import sys
import time
from threading import Thread
from types import TracebackType
from typing import Any, Callable, Optional, Protocol

from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    ProgressColumn,
    Task,
    TaskID,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
    filesize,
)
from rich.text import Text

try:
    from typing import Self
except ImportError:
    from typing_extensions import Self


class CommObject(Protocol):
    rank: int
    size: int

    def bcast(self, obj: Any, root: int = 0) -> Any: ...
    def gather(self, sendobj: Any, root: int = 0) -> list[Any] | None: ...
    def Split(self, color: int, key: int) -> "CommObject": ...
    def barrier(self) -> None: ...
    def recv(self, buf: Any = None, source: int = 0, tag: int = 0) -> Any: ...  # TODO: Correct default values
    def isend(self, obj: Any, dest: int, tag: int = 0) -> Any: ...
    def iprobe(self, source: int = 0, tag: int = 0, status: Any = None) -> bool: ...
    def allreduce(self, sendobj: Any, op: Callable[[Any, Any], Any] = lambda x, y: x + y) -> Any: ...


class CommMock(CommObject):
    rank = 0
    size = 1

    message_que: list[Any] = []

    def bcast(self, obj: Any, root: int = 0) -> Any:
        return obj

    def gather(self, sendobj: Any, root: int = 0) -> list[Any]:
        return [sendobj]

    def Split(self, color: int, key: int) -> CommObject:
        return self

    def barrier(self) -> None:
        return None

    def recv(self, buf: Any = None, source: int = 0, tag: int = 0) -> Any:
        if len(self.message_que) >= 1:
            return self.message_que.pop(0)
        else:
            return 0

    def isend(self, obj: Any, dest: int, tag: int = 0) -> Any:
        self.message_que.append(obj)

    def iprobe(self, source: int = 0, tag: int = 0, status: Any = None) -> bool:
        return len(self.message_que) >= 1

    def allreduce(self, sendobj: Any, op: Callable[[Any, Any], Any] = lambda x, y: x + y) -> Any:
        return sendobj


_COMM: CommObject = CommMock()
_ANY_SOURCE = 0
_IMPORTED = False


def get_mpi() -> CommObject:
    """
    Get MPI, if mpi is not available a mock object will be returned.
    """

    global _COMM, _IMPORTED, _ANY_SOURCE
    if not _IMPORTED:
        try:
            from mpi4py import MPI

            _ANY_SOURCE = MPI.ANY_SOURCE
            _COMM = MPI.COMM_WORLD
        except ImportError:
            _COMM = CommMock()
            _ANY_SOURCE = 0
        _IMPORTED = True
    return _COMM


class CommBar:
    """
    If tot = none it will just be a bouncing bar
    TODO: Docs
    """

    def __init__(
        self,
        tot: int | None,
        desc: str,
        prog_rank: int = 0,
        parent_progress: Optional["CommBar"] = None,
        transient: bool = False,
        comm: CommObject = get_mpi(),
        multi_process_bar: bool = True,
    ) -> None:

        self.tot = tot
        self.desc = desc
        self.comm = comm
        self.prog_rank = prog_rank
        self.transient = transient
        self.parent_progress = parent_progress
        self.multi_process_bar = multi_process_bar and comm.size > 1
        self.buffer = 0
        self._last_line_count = 0

        if self.comm.rank == self.prog_rank:
            if not parent_progress:
                consol = Console(force_terminal=True, width=100)
                if self.tot:
                    self.prog = Progress(
                        TextColumn("[progress.description]{task.description}"),
                        MofNCompleteColumn(),
                        BarColumn(),
                        TaskProgressColumn(),
                        "|",
                        TimeElapsedColumn(),
                        "/",
                        TimeRemainingColumn(),
                        "|",
                        RateColumn(),
                        console=consol,
                        auto_refresh=False,
                    )
                    self.update_rate = 1.0
                else:
                    self.prog = Progress(
                        "[progress.description]{task.description}",
                        BarColumn(),
                        TimeElapsedColumn(),
                        console=consol,
                        auto_refresh=False,
                    )
                    self.update_rate = 0.05
            else:
                self.prog = parent_progress.prog

            task_id = self.prog.add_task(desc + ":", total=tot)
        else:
            task_id = None

        if self.multi_process_bar:
            task_id = self.comm.bcast(task_id, root=self.prog_rank)
        self.task_id = task_id

        # Only the top-level parent starts a rendering thread
        self.thread_id = 0
        if self.comm.rank == self.prog_rank and not self.parent_progress:
            self.thread: Thread | None = Thread(
                target=self.progress_thread,
                args=(self.prog, self.comm),
                daemon=True,
                name="CommBar_Render_Thread",
            )
            self.thread.start()
            thread_id = self.thread.native_id
        elif self.parent_progress:
            thread_id = self.parent_progress.thread_id
            self.thread = None
        else:
            thread_id = None
            self.thread = None
        if self.multi_process_bar:
            thread_id = self.comm.bcast(thread_id, root=self.prog_rank)
        self.thread_id = thread_id  # type: ignore[assignment]

    def add_sub_progress(self, tot: int, desc: str, transient: bool = False) -> "CommBar":

        return CommBar(
            tot=tot, desc=desc, prog_rank=self.prog_rank, transient=transient, parent_progress=self
        )

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()

    def progress_thread(self, prog: Progress, comm: CommObject) -> None:

        with prog._lock:
            last_percentages = {task.id: 0.0 for task in prog.tasks}

        # Track the last time the UI was printed
        last_print_time = time.time()

        # Visualize progress bar at start
        self.print_bar(prog=prog, clear_old_bar=False)

        while True:
            if self.thread_id:
                if comm.iprobe(source=_ANY_SOURCE, tag=self.thread_id):
                    msg = comm.recv(source=_ANY_SOURCE, tag=self.thread_id)

                    n_completed = msg[0]
                    task_tag = msg[1]

                    # If close requested
                    if n_completed == -1:
                        break

                    with prog._lock:
                        # If task has not been removed, updated it
                        if task_tag in prog._tasks:
                            prog.update(
                                TaskID(task_tag),
                                advance=n_completed,
                            )

                            task = prog._tasks[TaskID(task_tag)]
                            if task.total and task.total != 0:
                                new_pct = (task.completed / task.total) * 100
                            else:
                                new_pct = 100
                            old_pct = last_percentages.get(TaskID(task_tag), 0.0)

                            if ((new_pct - old_pct) >= 0.2) or task.finished:
                                last_percentages[TaskID(task_tag)] = new_pct
                                self.print_bar(prog)
                                last_print_time = time.time()

                            if task.finished:
                                del last_percentages[TaskID(task_tag)]
                else:
                    time.sleep(0.01)
            else:
                time.sleep(0.01)

            # Periodic Time Check: Force update if 1 second has passed
            current_time = time.time()
            if (current_time - last_print_time) >= self.update_rate:
                self.print_bar(prog)
                last_print_time = current_time

            with prog._lock:
                if all(task.finished for task in prog.tasks):
                    break

    def print_bar(self, prog: Progress, clear_old_bar: bool = True) -> None:
        """
        Print progress bar to terminal

        Args:
            prog: Progress bar
            clear_old_bar: If old text should be removed before printing progress bar

        """

        # Extract exisiting task table
        with prog._lock:
            table = prog.make_tasks_table(prog.tasks)

        with prog.console.capture() as capture:
            prog.console.print(table, end="")
        raw_bar_text = capture.get().strip()

        # Count how many lines the previous print took up
        lines_to_clear = (
            self.parent_progress._last_line_count if self.parent_progress else self._last_line_count
        )

        # Clear these lines if requested
        output = ""
        if clear_old_bar and lines_to_clear > 0:
            output += f"\x1b[{lines_to_clear}A\r\x1b[J"

        # Add formated task table
        output += f"{raw_bar_text}\n"

        # Save line count for the next iteration clear loop
        current_lines = raw_bar_text.count("\n") + 1
        if self.parent_progress:
            self.parent_progress._last_line_count = current_lines
        else:
            self._last_line_count = current_lines

        sys.stdout.write(output)
        sys.stdout.flush()

    def update(self, n: int = 1) -> None:
        """
        Update progress bar n steps

        """
        self.buffer += n

        if self.tot is None or (self.buffer / self.tot) >= 0.001:
            self.comm.isend([self.buffer, self.task_id], dest=self.prog_rank, tag=self.thread_id)
            self.buffer = 0

    def clear_sub_tasks(self) -> None:
        self.comm.barrier()
        if self.comm.rank == self.prog_rank:
            if not self.parent_progress:
                for task in list(self.prog.tasks):
                    if task.id != self.task_id:
                        self.prog.remove_task(task.id)

            self.print_bar(self.prog)
        self.comm.barrier()

    def close(self) -> None:
        """
        Close bar
        """

        self.comm.isend([self.buffer, self.task_id], dest=self.prog_rank, tag=self.thread_id)

        # If multiple processes dependent on this process, wait for them
        if self.multi_process_bar:
            try:
                self.comm.barrier()
            except Exception:
                pass
        else:
            time.sleep(0.01)

        if self.comm.rank == self.prog_rank:
            # If it is a hovering bar that is closed, print its total if available, then mark green
            if self.tot is None and self.prog:
                completed = self.prog._tasks.get(self.task_id).completed  # type: ignore[union-attr, arg-type]
                if completed > 0:
                    self.prog.update(
                        self.task_id,  # type: ignore[arg-type]
                        total=completed,
                        description=f"{self.desc}: [green]{completed}",
                    )
                else:
                    self.prog.update(self.task_id, total=completed)  # type: ignore[arg-type]

            self.print_bar(prog=self.prog)

            # request thread to close and join thread
            if self.thread and self.thread.is_alive():
                try:
                    self.comm.isend([-1, self.thread_id], dest=self.prog_rank, tag=self.thread_id)
                    self.thread.join(timeout=2)
                except Exception:
                    pass

            # Sub progress bars marked with transient needs to be removed from the prog and then clear the terminal
            if self.parent_progress and self.transient:
                with self.prog._lock:
                    self.prog.remove_task(self.task_id)  # type: ignore[arg-type]

                if self.parent_progress:
                    self.parent_progress.print_bar(self.prog)

            # For the main bar, if marked with transient clear all rows once finsihed
            elif not self.parent_progress and self.transient:
                # Remove all subtasks aswell if done and transient requested
                for task in list(self.prog.tasks):
                    if task.finished and task.id != self.task_id:
                        self.prog.remove_task(task.id)

                self.print_bar(self.prog)

                lines_to_clear = self._last_line_count
                if lines_to_clear > 0:
                    sys.stdout.write(f"\x1b[{lines_to_clear}A\r\x1b[J")
                    sys.stdout.flush()
                    self._last_line_count = 0


class RateColumn(ProgressColumn):
    """Renders human readable processing rate."""

    def render(self, task: "Task") -> Text:
        """Render the speed in iterations per second."""
        speed = task.finished_speed or task.speed
        if speed is None:
            return Text("", style="progress.percentage")
        unit, suffix = filesize.pick_unit_and_suffix(
            int(speed),
            ["", "×10³", "×10⁶", "×10⁹", "×10¹²"],
            1000,
        )
        data_speed = speed / unit
        return Text(f"{data_speed:.1f}{suffix} it/s", style="progress.percentage")
