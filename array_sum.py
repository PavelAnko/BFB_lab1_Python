"""Parallel and sequential array sum implementations."""

from __future__ import annotations

import threading
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from multiprocessing import shared_memory

import numpy as np

# Module-level state for ProcessPoolExecutor workers (Windows spawn).
_shm_name: str | None = None
_array_size: int = 0


def _init_process_worker(shm_name: str, size: int) -> None:
    global _shm_name, _array_size
    _shm_name = shm_name
    _array_size = size


def _sum_range_process(part: int, parts: int) -> int:
    assert _shm_name is not None
    shm = shared_memory.SharedMemory(name=_shm_name)
    try:
        arr = np.ndarray((_array_size,), dtype=np.int32, buffer=shm.buf)
        return sum_range(arr, part, parts)
    finally:
        shm.close()


def sum_range(array: np.ndarray, part: int, parts: int) -> int:
    n = array.size
    from_ = part * n // parts
    to = (part + 1) * n // parts
    return int(array[from_:to].sum())


def sum_sequential(array: np.ndarray) -> int:
    return int(array.sum())


def sum_with_threads(array: np.ndarray, parts: int) -> int:
    partials = [0] * parts

    def worker(i: int) -> None:
        partials[i] = sum_range(array, i, parts)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(parts)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return sum(partials)


def sum_with_executor(array: np.ndarray, parts: int) -> int:
    with ThreadPoolExecutor(max_workers=parts) as executor:
        futures = [executor.submit(sum_range, array, i, parts) for i in range(parts)]
        return sum(f.result() for f in futures)


def sum_with_processes(shm_name: str, size: int, parts: int) -> int:
    """Sum via ProcessPoolExecutor over an existing SharedMemory buffer."""
    with ProcessPoolExecutor(
        max_workers=parts,
        initializer=_init_process_worker,
        initargs=(shm_name, size),
    ) as executor:
        futures = [executor.submit(_sum_range_process, i, parts) for i in range(parts)]
        return sum(f.result() for f in futures)
