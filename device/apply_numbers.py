#!/usr/bin/env python3
"""Apply reviewed metric output to a copy of approved.json."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


METRIC_IDS = ("attendance", "ritual", "submissions")
FIELDS = ("value", "label", "detail", "source", "asOf", "denominator")


def load_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"파일이 없습니다: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON 형식이 올바르지 않습니다: {path}: {exc}") from exc


def apply_numbers(content: dict[str, object], numbers: dict[str, object]) -> dict[str, object]:
    items = content.get("numbers")
    if not isinstance(items, list):
        raise ValueError("approved.json에 numbers 배열이 필요합니다.")
    by_id = {str(item.get("id")): item for item in items if isinstance(item, dict)}
    missing = [metric_id for metric_id in METRIC_IDS if metric_id not in numbers or metric_id not in by_id]
    if missing:
        raise ValueError("필수 숫자 ID가 없습니다: " + ", ".join(missing))

    as_of_values: list[str] = []
    for metric_id in METRIC_IDS:
        derived = numbers[metric_id]
        if not isinstance(derived, dict):
            raise ValueError(f"numbers.json의 {metric_id} 값은 객체여야 합니다.")
        target = by_id[metric_id]
        for field in FIELDS:
            if field not in derived:
                raise ValueError(f"numbers.json에 {metric_id}.{field} 값이 없습니다.")
            target[field] = derived[field]
        as_of_values.append(str(derived["asOf"]))
    content["updatedAt"] = max(as_of_values)
    return content


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> int:
    base = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser()
    parser.add_argument("--numbers", type=Path, default=base / "out" / "numbers.json")
    parser.add_argument("--content", type=Path, default=base.parent / "content" / "approved.json")
    parser.add_argument("--output", type=Path, default=base / "out" / "approved.preview.json")
    parser.add_argument("--in-place", action="store_true")
    args = parser.parse_args()
    try:
        content = load_json(args.content.resolve())
        numbers = load_json(args.numbers.resolve())
        if not isinstance(content, dict) or not isinstance(numbers, dict):
            raise ValueError("입력 JSON의 최상위 값은 객체여야 합니다.")
        result = apply_numbers(content, numbers)
        output = args.content.resolve() if args.in_place else args.output.resolve()
        write_json(output, result)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"PASS: {output}")
    if not args.in_place:
        print("검토 뒤 --in-place 옵션으로 승인 데이터에 반영할 수 있습니다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
