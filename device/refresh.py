#!/usr/bin/env python3
"""Create deterministic T12 metrics and private writing candidates."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path


SELF_LABELS = {
    "내 강점",
    "강점이 드러난 일화",
    "그 결과·알게 된 점",
    "오늘 지킬 강점·가치",
    "오늘의 첫 행동",
    "강점 행동",
    "강점을 위해 노력하고 생각한 것",
    "나에게 남기는 말",
}

ABILITY_KEYWORDS = {
    "자기조절력": ("확인", "정리", "차례", "삭제", "기록", "조절", "원인", "해결"),
    "대인관계력": ("팀원", "동료", "설명", "리뷰", "함께", "도움", "소개", "대화"),
    "자기동기력": ("배우", "공부", "시작", "과제", "실천", "완주", "도전", "계속"),
}

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?<!\d)01[016789][ -]?\d{3,4}[ -]?\d{4}(?!\d)")


def _load_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"필수 입력 파일이 없습니다: {path.name}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON 형식이 올바르지 않습니다: {path.name}: {exc}") from exc


def _write_json(path: Path, value: object) -> None:
    text = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")


def _parse_iso(value: str, field: str) -> datetime:
    if not value:
        raise ValueError(f"{field} 값이 비어 있습니다.")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field}는 ISO 날짜 형식이어야 합니다: {value}") from exc


def _record_id(day_value: str, phase: str, index: int) -> str:
    compact = date.fromisoformat(day_value).strftime("%Y%m%d")
    phase_code = "O" if phase == "open" else "C"
    return f"R-{compact}-{phase_code}-{index:02d}"


def _split_item(raw: object) -> tuple[str, str]:
    text = str(raw).strip()
    match = re.match(r"^([^:]+):\s*(.*)$", text, flags=re.DOTALL)
    if not match:
        return "라벨 없음", text
    return match.group(1).strip(), match.group(2).strip()


def _redact(text: str, student: str) -> str:
    value = EMAIL_RE.sub("[이메일 가림]", text)
    value = PHONE_RE.sub("[전화번호 가림]", value)
    if student:
        value = value.replace(student, "본인")
    return value


def _ability(text: str) -> str:
    scores = {
        ability: sum(text.count(keyword) for keyword in keywords)
        for ability, keywords in ABILITY_KEYWORDS.items()
    }
    best = max(scores.values(), default=0)
    if best == 0:
        return "미분류"
    return sorted(ability for ability, score in scores.items() if score == best)[0]


def _ritual_metrics(data: object) -> tuple[dict[str, object], list[dict[str, str]]]:
    if not isinstance(data, dict) or not isinstance(data.get("days"), list):
        raise ValueError("ritual.json에는 days 배열이 필요합니다.")

    student = str(data.get("student") or "")
    days = sorted(data["days"], key=lambda item: str(item.get("date", "")))
    if not days:
        raise ValueError("ritual.json의 days 배열이 비어 있습니다.")

    open_days = 0
    close_days = 0
    candidates: list[dict[str, str]] = []

    for day in days:
        day_value = str(day.get("date") or "")
        date.fromisoformat(day_value)
        open_items = day.get("open") or []
        close_items = day.get("close") or []
        if not isinstance(open_items, list) or not isinstance(close_items, list):
            raise ValueError(f"ritual.json {day_value}: open과 close는 배열이어야 합니다.")
        open_days += int(bool(open_items))
        close_days += int(bool(close_items))

        for phase, items in (("open", open_items), ("close", close_items)):
            for index, raw in enumerate(items, start=1):
                label, content = _split_item(raw)
                if label not in SELF_LABELS or not content:
                    continue
                safe_content = _redact(content, student)
                candidates.append(
                    {
                        "ability": _ability(safe_content),
                        "content": safe_content,
                        "date": day_value,
                        "evidenceId": _record_id(day_value, phase, index),
                        "label": label,
                        "phase": "아침" if phase == "open" else "마무리",
                    }
                )

    candidates.sort(key=lambda item: (item["date"], item["evidenceId"]))
    return (
        {
            "asOf": str(days[-1]["date"]),
            "closeDays": close_days,
            "morningDays": open_days,
            "recordedDays": len(days),
        },
        candidates,
    )


def _attendance_metrics(data: object) -> dict[str, object]:
    if not isinstance(data, dict) or not isinstance(data.get("sessions"), list):
        raise ValueError("attendance.json에는 sessions 배열이 필요합니다.")
    sessions = sorted(data["sessions"], key=lambda item: str(item.get("date", "")))
    if not sessions:
        raise ValueError("attendance.json의 sessions 배열이 비어 있습니다.")

    allowed = {"present", "late", "absent"}
    for item in sessions:
        date.fromisoformat(str(item.get("date") or ""))
        if item.get("status") not in allowed:
            raise ValueError(f"알 수 없는 출석 상태입니다: {item.get('status')}")

    return {
        "absent": sum(item["status"] == "absent" for item in sessions),
        "asOf": str(sessions[-1]["date"]),
        "attended": sum(item["status"] in {"present", "late"} for item in sessions),
        "late": sum(item["status"] == "late" for item in sessions),
        "sessions": len(sessions),
    }


def _submission_metrics(path: Path) -> dict[str, object]:
    try:
        handle = path.open("r", encoding="utf-8-sig", newline="")
    except FileNotFoundError as exc:
        raise ValueError(f"필수 입력 파일이 없습니다: {path.name}") from exc

    with handle:
        reader = csv.DictReader(handle)
        required = {"id", "due_at", "submitted_at", "status"}
        if set(reader.fieldnames or []) != required:
            raise ValueError("submissions.csv 열은 id,due_at,submitted_at,status 순서여야 합니다.")
        rows = [row for row in reader if row["status"] != "not_required"]

    if not rows:
        raise ValueError("submissions.csv에 제출 대상 과제가 없습니다.")

    submitted = 0
    on_time = 0
    dates: list[datetime] = []
    for row in rows:
        due = _parse_iso(row["due_at"], f"{row['id']}.due_at")
        dates.append(due)
        if row["submitted_at"]:
            submitted_at = _parse_iso(row["submitted_at"], f"{row['id']}.submitted_at")
            dates.append(submitted_at)
            submitted += 1
            on_time += int(submitted_at <= due)

    return {
        "asOf": max(dates).date().isoformat(),
        "onTime": on_time,
        "submitted": submitted,
        "total": len(rows),
    }


def _candidate_markdown(candidates: list[dict[str, str]]) -> str:
    lines = [
        "# 문장 후보",
        "",
        "비공개 검토용 자동 생성 결과입니다. 사이트에는 사람이 승인한 문장만 옮깁니다.",
        "",
    ]
    for ability in ("자기조절력", "대인관계력", "자기동기력", "미분류"):
        items = [item for item in candidates if item["ability"] == ability]
        if not items:
            continue
        lines.extend((f"## {ability}", ""))
        for item in items:
            clean = item["content"].replace("\n", " ").replace("\r", " ")
            lines.append(
                f"- {item['date']} · {item['evidenceId']} · {item['label']}: {clean}"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def refresh(input_dir: Path, output_dir: Path) -> None:
    ritual, candidates = _ritual_metrics(_load_json(input_dir / "ritual.json"))
    attendance = _attendance_metrics(_load_json(input_dir / "attendance.json"))
    submissions = _submission_metrics(input_dir / "submissions.csv")

    numbers = {
        "attendance": {
            "asOf": attendance["asOf"],
            "denominator": "attendance.json의 확정 수업일",
            "detail": f"지각 {attendance['late']} · 결석 {attendance['absent']}",
            "label": "출석일 / 확정 수업일",
            "source": "내 출석 기록",
            "value": f"{attendance['attended']} / {attendance['sessions']}일",
        },
        "ritual": {
            "asOf": ritual["asOf"],
            "denominator": "ritual.json에 포함된 기록일",
            "detail": f"마무리 리추얼 {ritual['closeDays']}일",
            "label": "아침 리추얼 작성일 / 기록일",
            "source": "내 리추얼 기록",
            "value": f"{ritual['morningDays']} / {ritual['recordedDays']}일",
        },
        "submissions": {
            "asOf": submissions["asOf"],
            "denominator": "submissions.csv의 제출 대상 과제",
            "detail": f"제출 완료 {submissions['submitted']}건",
            "label": "기한 안에 낸 과제 / 제출 대상 과제",
            "source": "내 제출 현황",
            "value": f"{submissions['onTime']} / {submissions['total']}건",
        },
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / "numbers.json", numbers)
    _write_json(output_dir / "candidates.json", candidates)
    (output_dir / "candidates.md").write_text(
        _candidate_markdown(candidates), encoding="utf-8", newline="\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    try:
        refresh(args.input_dir.resolve(), args.output_dir.resolve())
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print("PASS: numbers.json, candidates.json, candidates.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
