from __future__ import annotations

import os

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")

from multiprocessing import shared_memory
from pathlib import Path

import numpy as np

from array_sum import (
    sum_sequential,
    sum_with_executor,
    sum_with_processes,
    sum_with_threads,
)
from benchmark import measure_best, print_table, write_report

ARRAY_SIZE = 1_000_000_000
ELEMENT = 1
ITERATIONS = 3


def main() -> None:
    parts = os.cpu_count() or 4
    expected = ARRAY_SIZE * ELEMENT

    print(f"n={ARRAY_SIZE}, parts={parts}")

    shm: shared_memory.SharedMemory | None = None
    try:
        shm = shared_memory.SharedMemory(create=True, size=ARRAY_SIZE * 4)
        array = np.ndarray((ARRAY_SIZE,), dtype=np.int32, buffer=shm.buf)
        array.fill(ELEMENT)
    except MemoryError as e:
        if shm is not None:
            shm.close()
            shm.unlink()
        raise SystemExit(
            "OOM: need ~4 GB free RAM for int32 array of size 1_000_000_000"
        ) from e

    try:
        warm_shm = shared_memory.SharedMemory(create=True, size=1_000_000 * 4)
        try:
            warm = np.ndarray((1_000_000,), dtype=np.int32, buffer=warm_shm.buf)
            warm.fill(1)
            sum_sequential(warm)
            sum_with_threads(warm, 4)
            sum_with_executor(warm, 4)
            sum_with_processes(warm_shm.name, warm.size, 4)
        finally:
            warm_shm.close()
            warm_shm.unlink()

        results = [
            measure_best(
                "Single-threaded",
                expected,
                ITERATIONS,
                lambda: sum_sequential(array),
            ),
            measure_best(
                "Thread + join",
                expected,
                ITERATIONS,
                lambda: sum_with_threads(array, parts),
            ),
            measure_best(
                "ThreadPoolExecutor",
                expected,
                ITERATIONS,
                lambda: sum_with_executor(array, parts),
            ),
            measure_best(
                "ProcessPoolExecutor",
                expected,
                ITERATIONS,
                lambda: sum_with_processes(shm.name, array.size, parts),
            ),
        ]

        print_table(results)
        write_report(Path("RESULTS.md"), ARRAY_SIZE, parts, results)
        assert all(r.correct for r in results), "incorrect sum"
        print("Wrote RESULTS.md")
    finally:
        shm.close()
        shm.unlink()


if __name__ == "__main__":
    main()
