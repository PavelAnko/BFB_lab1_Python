"""Benchmark helpers and RESULTS.md report writer."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


@dataclass
class BenchmarkResult:
    method: str
    time_ms: float
    sum: int
    expected_sum: int

    @property
    def correct(self) -> bool:
        return self.sum == self.expected_sum

    def speedup(self, base_ms: float) -> float:
        if self.time_ms <= 0:
            return float("inf")
        return base_ms / self.time_ms


def measure_best(
    method: str,
    expected: int,
    iterations: int,
    block: Callable[[], int],
) -> BenchmarkResult:
    best: BenchmarkResult | None = None
    for _ in range(iterations):
        t0 = time.perf_counter_ns()
        total = block()
        ms = (time.perf_counter_ns() - t0) / 1_000_000.0
        result = BenchmarkResult(method, ms, total, expected)
        if not result.correct:
            raise AssertionError(f"{method}: got {result.sum}, expected {expected}")
        if best is None or result.time_ms < best.time_ms:
            best = result
    assert best is not None
    return best


def print_table(results: list[BenchmarkResult]) -> None:
    base = results[0].time_ms
    print(f"{'Method':<20} {'ms':>10} {'Speedup':>8}")
    for r in results:
        print(f"{r.method:<20} {r.time_ms:10.2f} {r.speedup(base):7.2f}x")


def _fmt(v: float) -> str:
    return f"{v:.2f}"


def write_report(
    path: Path,
    size: int,
    parts: int,
    results: list[BenchmarkResult],
) -> None:
    base = results[0]
    mt = results[1:]
    fastest = min(mt, key=lambda r: r.time_ms)

    lines: list[str] = [
        "# Results",
        f"n={size}, parts={parts}",
        "",
        "| Method | ms | Speedup |",
        "|--------|----|---------|",
    ]
    for r in results:
        lines.append(f"| {r.method} | {_fmt(r.time_ms)} | {_fmt(r.speedup(base.time_ms))}x |")

    lines.append("")
    lines.append("## Conclusions")
    for r in mt:
        notes: list[str] = []
        for other in mt:
            if other is r:
                continue
            if other.time_ms > r.time_ms * 1.05:
                notes.append(f"> {other.method}")
            elif r.time_ms > other.time_ms * 1.05:
                notes.append(f"< {other.method}")
        note_str = f" ({', '.join(notes)})" if notes else ""
        lines.append(f"- {r.method}: {_fmt(r.speedup(base.time_ms))}x{note_str}")

    lines.append("")
    lines.append(f"Fastest: {fastest.method} ({_fmt(fastest.time_ms)} ms).")
    lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
