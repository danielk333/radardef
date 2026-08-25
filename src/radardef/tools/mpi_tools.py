import sys
import time
from threading import Event, Lock, Thread
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
from rich.table import Column
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
    def allgather(self, sendobj: Any) -> list[Any]: ...


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

    def allgather(self, sendobj: Any) -> list[Any]:
        return [sendobj]


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
    A shared multi process progress bar compatible with MPI.

    Args:
        tot: Size of bar, if None the bar will be a bouncing bar.
        desc: Desicription of bar.
        prog_rank (optional): What rank should the progress bar thread be running on.
        parent_progress (optional): If this bar should inherit from another bar.
        transient (optional): Should the progress bar be removed once done.
        comm (optional): MPI communication object
        multi_process_bar (optional): If this progress bar is running on multiple processes, if not it needs to be marked so it does not try to sync.
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

        self.input_active = False
        self.input_thread: Thread | None = None
        self.input_result: str | None = None
        self.input_done = Event()
        self.input_prompt = ""

        self.terminal_lock = Lock()

        if self.comm.rank == self.prog_rank:
            if not parent_progress:
                consol = Console(force_terminal=True, width=105)

                self.prog = Progress(
                    *self.get_columns(self.tot),
                    console=consol,
                    auto_refresh=False,
                )
                self.update_rate = 1.0 if self.tot else 0.05

            else:
                self.prog = parent_progress.prog

            task_id = self.prog.add_task(desc + ":", total=tot)
        else:
            task_id = None

        if self.multi_process_bar:
            task_id = self.comm.bcast(task_id, root=self.prog_rank)
        self.task_id = task_id

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

    def get_columns(self, tot: int | None) -> tuple[ProgressColumn | str, ...]:
        """Get columns design based on the size of the bar."""

        desc_col = Column(width=27, no_wrap=True)
        mofn_col = Column(width=12, justify="right", no_wrap=True)
        bar_col = Column(width=20, no_wrap=True)
        prog_col = Column(width=4, no_wrap=True)

        if tot:
            return (
                TextColumn("[progress.description]{task.description}", table_column=desc_col),
                MofNCompleteColumn(table_column=mofn_col),
                BarColumn(table_column=bar_col),
                TaskProgressColumn(table_column=prog_col),
                "|",
                TimeElapsedColumn(),
                "/",
                TimeRemainingColumn(),
                "|",
                RateColumn(),
            )
        else:
            return (
                TextColumn("[progress.description]{task.description}", table_column=desc_col),
                StatusOrEmptyColumn(table_column=mofn_col),
                BarColumn(table_column=bar_col),
                TextColumn("", table_column=prog_col),
                "|",
                TimeElapsedColumn(),
            )

    def add_sub_progress(self, tot: int, desc: str, transient: bool = False) -> "CommBar":
        """
        Add a progress bar below this progress bar.

        """
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

            # Periodic Time Check: Force update if more time than the expected updated rate has passed
            current_time = time.time()
            if (current_time - last_print_time) >= self.update_rate:
                self.print_bar(prog)
                last_print_time = current_time

            with prog._lock:
                if all(task.finished for task in prog.tasks):
                    break

    def print_bar(self, prog: Progress, clear_old_bar: bool = True) -> None:
        """
        Print progress bar to terminal.
        """
        with prog._lock:
            table = prog.make_tasks_table(prog.tasks)

        with prog.console.capture() as capture:
            prog.console.print(table, end="")

        raw_bar_text = capture.get().strip()
        old_lines = self.parent_progress._last_line_count if self.parent_progress else self._last_line_count
        new_lines = raw_bar_text.count("\n") + 1

        if self.input_active:
            # Save the exact cursor position, including the column.
            output = "\x1b[s"

            # Move from the input line to the old progress bar.
            if old_lines > 0:
                output += f"\x1b[{old_lines}A"

            output += "\r"

            # Clear the old progress bar.
            for i in range(old_lines):
                output += "\x1b[2K"
                if i < old_lines - 1:
                    output += "\x1b[1B"

            # Return to the first progress-bar line.
            if old_lines > 1:
                output += f"\x1b[{old_lines - 1}A"

            output += "\r"

            # Draw new updated bar
            output += "\x1b[0m" + raw_bar_text + "\n"
            output += "\n"

            # If getpass is running run hide code again.
            if getattr(self, "_is_getpass", False):
                output += "\x1b[8m"

            # Restore the exact input cursor position.
            output += "\x1b[u"

        else:
            output = ""
            if clear_old_bar and old_lines > 0:
                output += f"\x1b[{old_lines}A\r\x1b[J"

            output += "\x1b[0m" + raw_bar_text
            output += "\n"

        with self.terminal_lock:
            sys.stdout.write(output)
            sys.stdout.flush()

        if self.parent_progress:
            self.parent_progress._last_line_count = new_lines
        else:
            self._last_line_count = new_lines

    def update(self, n: int = 1) -> None:
        """
        Update progress bar by n steps.
        """
        self.buffer += n

        if self.tot is None or (self.buffer / self.tot) >= 0.001:
            self.comm.isend([self.buffer, self.task_id], dest=self.prog_rank, tag=self.thread_id)
            self.buffer = 0

    def clear_sub_tasks(self) -> None:
        """
        Clear all sub tasks of current progress bar.
        """

        self.comm.barrier()
        if self.comm.rank == self.prog_rank:
            lines_to_clear = (
                self.parent_progress._last_line_count if self.parent_progress else self._last_line_count
            )

            # Clear all lines
            if lines_to_clear > 0:
                with self.terminal_lock:
                    sys.stdout.write(f"\x1b[{lines_to_clear}A\r\x1b[J")
                    sys.stdout.flush()

                # reset line counter
                if self.parent_progress:
                    self.parent_progress._last_line_count = 0
                else:
                    self._last_line_count = 0

            # Remove tasks from prog
            if not self.parent_progress:
                for task in list(self.prog.tasks):
                    if task.id != self.task_id:
                        self.prog.remove_task(task.id)

            # Reprint bar
            self.print_bar(self.prog)

        self.comm.barrier()

    def getpass(self, prompt: str = "") -> str:
        """
        Alternative solution to getpass compatible with the rich.progress,
        only works on single process.

        Args:
            prompt: String to show when asking for password
        """

        if self.comm.rank != self.prog_rank:
            raise RuntimeError("CommBar.getpass() must be called on prog_rank.")

        self.input_active = True
        self._is_getpass = True
        self.input_prompt = prompt
        self.input_done.clear()
        self.input_result = None

        def read_getpass() -> None:
            try:
                # Hidden mode after prompt
                full_prompt = f"\x1b[0m{prompt}\x1b[8m"
                self.input_result = input(full_prompt)
            finally:
                with self.terminal_lock:
                    sys.stdout.write("\x1b[0m")  # remove hidden mode
                    sys.stdout.flush()
                self.input_done.set()

        self.input_thread = Thread(target=read_getpass, daemon=True, name="CommBar_GetPass_Thread")
        self.input_thread.start()
        self.input_done.wait()
        self.input_thread.join()

        # Clear prompt and password
        with self.terminal_lock:
            sys.stdout.write("\x1b[1A\r\x1b[2K")
            sys.stdout.flush()

        self.input_active = False
        self._is_getpass = False
        self.print_bar(self.prog)
        return self.input_result or ""

    def input(self, prompt: str = "") -> str:
        """
        Wrapper around input to make it compatible with the rich.progress bar,
        only works on single process.

        Args:
            prompt: String to show when asking for input

        """
        if self.comm.rank != self.prog_rank:
            raise RuntimeError("CommBar.input() must be called on prog_rank.")

        self.input_active = True
        self.input_prompt = prompt
        self.input_done.clear()
        self.input_result = None

        def read_input() -> None:
            try:
                self.input_result = input(prompt)
            finally:
                self.input_done.set()

        self.input_thread = Thread(target=read_input, daemon=True, name="CommBar_Input_Thread")
        self.input_thread.start()
        self.input_done.wait()
        self.input_thread.join()

        # Clear prompt and input
        with self.terminal_lock:
            sys.stdout.write("\x1b[1A\r\x1b[2K")
            sys.stdout.flush()

        self.input_active = False
        self.print_bar(self.prog)
        return self.input_result or ""

    def clear_input_line(self) -> None:
        """Clear the terminal line currently used for input."""
        sys.stdout.write("\r\x1b[2K")
        sys.stdout.flush()

    def set_tot(self, tot: int | None) -> None:
        """
        Update total value and refresh progress bar

        Args:
            tot: size of items to iterate through.
        """
        self.tot = tot

        # If not a single process bar, sync tot over all bars.
        if self.multi_process_bar:
            self.tot = self.comm.bcast(self.tot, root=self.prog_rank)

        if self.comm.rank == self.prog_rank:
            with self.prog._lock:
                if self.task_id in self.prog._tasks:
                    self.prog._tasks[self.task_id].total = tot

                # Regenerate columns based on the new tot
                if not self.parent_progress:
                    self.prog.columns = self.get_columns(self.tot)
                    self.update_rate = 1.0 if self.tot else 0.05

            # Force terminal to write the new columns
            self.print_bar(self.prog)

    def close(self, desc: str | None = None) -> None:
        """
        Close bar.

        Args:
            desc (optional): Possibility to update the description once the bar is marked done.
        """

        self.comm.isend([self.buffer, self.task_id], dest=self.prog_rank, tag=self.thread_id)
        time.sleep(0.4)
        # If multiple processes dependent on this process, wait for them
        if self.multi_process_bar:
            try:
                self.comm.barrier()
            except Exception:
                pass
        else:
            time.sleep(0.01)

        if desc:
            self.desc = desc

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
                    self.prog.update(
                        self.task_id,  # type: ignore[arg-type]
                        description=self.desc,
                        total=completed,
                        show_checkmark=True,
                    )
            elif self.tot is not None and self.prog:
                self.prog.update(
                    self.task_id,  # type: ignore[arg-type]
                    description=f"{self.desc}:",
                )

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

            # For the main bar, if marked with transient clear all rows once finished
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

        if self.multi_process_bar:
            try:
                self.comm.barrier()
            except Exception:
                pass


class StatusOrEmptyColumn(ProgressColumn):
    """Column that generates a green bock if show_checkmark is set."""

    def render(self, task: Task) -> Text:
        if task.fields.get("show_checkmark"):
            return Text("✓", style="bold green", justify="right")

        return Text(" " * 12)


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
