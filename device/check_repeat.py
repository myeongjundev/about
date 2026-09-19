#!/usr/bin/env python3
"""Run refresh.py twice in fresh folders and compare deterministic outputs."""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path


OUTPUTS = ("numbers.json", "candidates.json", "candidates.md")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_refresh(script: Path, input_dir: Path, output_dir: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(script), str(input_dir), str(output_dir)],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())


def compare(left: Path, right: Path) -> list[str]:
    problems: list[str] = []
    for name in OUTPUTS:
        left_file = left / name
        right_file = right / name
        if not left_file.exists() or not right_file.exists():
            problems.append(f"missing: {name}")
        elif digest(left_file) != digest(right_file):
            problems.append(f"different: {name}")
    return problems


def main() -> int:
    base = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=base / "sample-inputs")
    parser.add_argument("--expected", type=Path, default=base / "expected")
    args = parser.parse_args()

    try:
        with tempfile.TemporaryDirectory(prefix="t12-repeat-a-") as first, tempfile.TemporaryDirectory(
            prefix="t12-repeat-b-"
        ) as second:
            first_path = Path(first)
            second_path = Path(second)
            run_refresh(base / "refresh.py", args.input.resolve(), first_path)
            run_refresh(base / "refresh.py", args.input.resolve(), second_path)
            problems = compare(first_path, second_path)
            if args.expected.exists():
                problems.extend(
                    f"expected {problem}" for problem in compare(first_path, args.expected.resolve())
                )
            if problems:
                for problem in problems:
                    print(f"FAIL: {problem}")
                return 1
            for name in OUTPUTS:
                print(f"{name} {digest(first_path / name)}")
    except (OSError, RuntimeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print("PASS: repeated outputs and expected outputs are identical")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
