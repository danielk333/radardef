"""Wrappers to simplify the usage of MPI on individual functions"""

import logging
from functools import wraps
from typing import Any, Callable

logger = logging.getLogger(__name__)

logger.debug("Importing MPI")
try:
    from mpi4py import MPI

    comm = MPI.COMM_WORLD
except ImportError:
    logger.debug("MPI import failed: reverting to one process")

    class COMM_WORLD:
        rank = 0
        size = 1

    comm = COMM_WORLD()  # type: ignore[assignment]


def MPI_target_arg(arg_index: int, MPI: bool = False, MPI_root: int = 0) -> Any:
    """
    Decorates the target function to parallelize over a single input iterable
    positional argument identified by the given index.


    Args:
        arg_index: index of the argument to iterate over
        MPI (optional): if MPI should be enabled, default is false
        MPI_root (optional): Which process to gather the results in (tasks will be divided on the rest).
            If negative no results will be gathered.
    """

    def _mpi_wrapper(func: Callable) -> Any:
        """Wrapper"""

        @wraps(func)
        def _mpi_wrapped_func(*args: Any, **kwargs: Any) -> Any:
            """Parallelizes the function over the iterable arg."""
            input_list = args[arg_index]
            _args = list(args)
            rets = [None] * len(input_list)

            if MPI:
                iter_inds = range(comm.rank, len(input_list), comm.size)
            else:
                iter_inds = range(len(input_list))

            for ind in iter_inds:
                _args[arg_index] = input_list[ind]
                rets[ind] = func(*_args, **kwargs)

            if MPI and MPI_root is None:
                pass
            elif MPI and MPI_root >= 0:
                if comm.rank == MPI_root:
                    for thr_id in range(comm.size):
                        if thr_id == MPI_root:
                            continue

                        mpi_inds = range(thr_id, len(input_list), comm.size)
                        for ind in mpi_inds:
                            rets[ind] = comm.recv(source=thr_id, tag=ind)
                else:
                    for ind in iter_inds:
                        comm.send(rets[ind], dest=MPI_root, tag=ind)

                if comm.rank != MPI_root:
                    for ind in iter_inds:
                        rets[ind] = None
            elif MPI and MPI_root < 0:
                for ind in iter_inds:
                    rets[ind] = comm.bcast(rets[ind], root=comm.rank)

            return rets

        return _mpi_wrapped_func

    return _mpi_wrapper


def MPI_target_args(
    arg_indexes: range, loading_bar: bool = False, MPI: bool = False, MPI_root: int = 0
) -> Any:
    """
    Decorates the target function to parallelize over several iterable
    positional arguments identified by the index range.


    Args:
        arg_indexes: The indexes to iterate over, note that the length of the arguments to
            iterate over has to be the same size.
        MPI (optional): If MPI should be enabled, default is false
        MPI_root (optional): Which process to gather the results in (tasks will be divided on the rest).
            If negative no results will be gathered.
    """

    def _mpi_wrapper(func: Callable) -> Any:
        """Wrapper"""

        @wraps(func)
        def _mpi_wrapped_func(*args: Any, **kwargs: int) -> list[Any]:
            """Parallelizes the function over the iterable args."""
            iterable_arguments = [args[arg] for arg in arg_indexes]
            try:
                number_of_indexes = len(iterable_arguments[0])
            except TypeError:
                return func(*args, **kwargs)

            # Validate that the arguments are of the same length
            for argument_list in iterable_arguments:
                if len(argument_list) is not number_of_indexes:
                    raise ValueError("The arguments length are not of the same size")

            func_calls = [None] * number_of_indexes
            func_rets = [None] * number_of_indexes
            tmp_args = list(args)
            for i in range(number_of_indexes):
                for arg in arg_indexes:
                    tmp_args[arg] = iterable_arguments[arg - min(arg_indexes)][i]
                func_calls[i] = func(*tmp_args, **kwargs)

            if MPI:
                iter_inds = range(comm.rank, number_of_indexes, comm.size)
            else:
                iter_inds = range(number_of_indexes)

            if MPI and MPI_root >= 0:
                if comm.rank == MPI_root:
                    for thr_id in range(comm.size):
                        if thr_id == MPI_root:
                            continue

                        mpi_inds = range(thr_id, number_of_indexes, comm.size)
                        for ind in mpi_inds:
                            func_rets[ind] = comm.recv(source=thr_id, tag=ind)
                else:
                    for ind in iter_inds:
                        comm.send(func_calls[ind], dest=MPI_root, tag=ind)

                if comm.rank != MPI_root:
                    for ind in iter_inds:
                        func_rets[ind] = None
            elif MPI and MPI_root < 0:
                for ind in iter_inds:
                    comm.bcast(func_calls[ind], root=comm.rank)
            elif not MPI:
                for ind in iter_inds:
                    func_rets[ind] = func_calls[ind]
            return func_rets

        return _mpi_wrapped_func

    return _mpi_wrapper
