#!/usr/bin/env python3
"""Build a deterministic T12 submission ZIP from an explicit allowlist."""

from __future__ import annotations

import argparse
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath


FIXED_DATE = (2026, 9, 19, 0, 0, 0)
DOCUMENTS = (
    "resume-kim-myeongjun.docx",
    "resume-kim-myeongjun.pdf",
    "personal-statement-kim-myeongjun.docx",
    "personal-statement-kim-myeongjun.pdf",
    "career-description-kim-myeongjun.docx",
    "career-description-kim-myeongjun.pdf",
)


def add_file(archive: zipfile.ZipFile, source: Path, target: PurePosixPath) -> None:
    info = zipfile.ZipInfo(str(target), date_time=FIXED_DATE)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    archive.writestr(info, source.read_bytes())


def required_files(repo: Path) -> list[tuple[Path, PurePosixPath]]:
    root = PurePosixPath("T12-KimMyeongjun")
    files: list[tuple[Path, PurePosixPath]] = []
    files.append((repo / "submission" / "README-FIRST.md", root / "README-FIRST.md"))
    for name in ("CHECK-HOWTO.md", "AI-JUDGMENT.md"):
        files.append((repo / "submission" / name, root / "submission" / name))
    for name in DOCUMENTS:
        files.append((repo / "docs" / "files" / name, root / "documents" / name))
    files.append((repo / "content" / "approved.json", root / "device" / "approved.json"))

    for relative in (
        "README.md",
        "refresh.py",
        "apply_numbers.py",
        "build_site.py",
        "check_repeat.py",
        "test_device.py",
        "validate_release.py",
        "templates/page.html.tpl",
    ):
        files.append((repo / "device" / relative, root / "device" / relative))
    for folder in ("sample-inputs", "expected", "last-result"):
        base = repo / "device" / folder
        if base.exists():
            for source in sorted(path for path in base.rglob("*") if path.is_file()):
                relative = PurePosixPath(*source.relative_to(repo / "device").parts)
                files.append((source, root / "device" / relative))
    assets = repo / "docs" / "assets"
    for source in sorted(path for path in assets.rglob("*") if path.is_file()):
        relative = PurePosixPath(*source.relative_to(repo / "docs").parts)
        files.append((source, root / "docs" / relative))
    return files


def main() -> int:
    repo = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=repo / "release" / "out" / "T12-KimMyeongjun.zip",
    )
    args = parser.parse_args()

    validation = subprocess.run(
        [sys.executable, str(repo / "device" / "validate_release.py"), "--repo", str(repo)],
        check=False,
    )
    if validation.returncode:
        print("ERROR: 릴리스 검사를 먼저 통과해야 합니다.", file=sys.stderr)
        return 1

    files = required_files(repo)
    missing = [str(source.relative_to(repo)) for source, _ in files if not source.is_file()]
    if not (repo / "device" / "last-result").is_dir():
        missing.append("device/last-result/")
    if missing:
        for item in missing:
            print(f"ERROR: 필수 릴리스 파일이 없습니다: {item}", file=sys.stderr)
        return 1

    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w") as archive:
        for source, target in sorted(files, key=lambda item: str(item[1])):
            add_file(archive, source, target)
    print(f"PASS: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
