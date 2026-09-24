#!/usr/bin/env python3
"""Render the built DOCX files to PDF and page images, then record what came out.

문서는 눈으로 봐야 알 수 있는 것이 많다. 쪽이 몇 장인지, 마지막 쪽에 몇 줄만 남았는지,
글자가 잘리지 않았는지는 실제로 렌더링해야 확인할 수 있다. 이 스크립트는 LibreOffice로
DOCX를 PDF와 페이지 이미지로 만들고, 쪽마다 글자 수를 세어 `manifest.json`에 적는다.

LibreOffice가 PATH에 있으면 그대로 쓰고, 없으면 Docker 이미지 안에서 실행한다.
Docker를 쓸 때는 한글 글꼴을 컨테이너에 연결해야 문서와 같은 모습으로 렌더링된다.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


DOCUMENTS = (
    "resume-kim-myeongjun",
    "personal-statement-kim-myeongjun",
    "career-description-kim-myeongjun",
    "resume-kim-myeongjun-en",
)

DEFAULT_IMAGE = "t12-doc-render"
DOCKERFILE = """FROM ubuntu:24.04
RUN apt-get update \\
 && apt-get install -y --no-install-recommends libreoffice-writer poppler-utils fontconfig \\
 && rm -rf /var/lib/apt/lists/*
"""


def run(command: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(command, check=True, capture_output=True, text=True, **kwargs)


def local_soffice() -> str | None:
    for name in ("soffice", "libreoffice"):
        found = shutil.which(name)
        if found:
            return found
    return None


def font_mount() -> tuple[Path, str] | None:
    """컨테이너에 연결할 글꼴 폴더. 문서가 쓰는 맑은 고딕이 있어야 한다."""
    candidates = [Path(os.environ.get("T12_FONT_DIR", ""))] if os.environ.get("T12_FONT_DIR") else []
    if platform.system() == "Windows":
        candidates.append(Path(os.environ.get("SystemRoot", "C:/Windows")) / "Fonts")
    candidates += [Path("/usr/share/fonts"), Path.home() / ".fonts"]
    for path in candidates:
        if path and path.is_dir():
            return path, "/usr/share/fonts/host"
    return None


def ensure_image(image: str) -> None:
    probe = subprocess.run(
        ["docker", "image", "inspect", image], capture_output=True, text=True
    )
    if probe.returncode == 0:
        return
    print(f"렌더 이미지 {image}를 만듭니다. 처음 한 번만 걸립니다.")
    subprocess.run(
        ["docker", "build", "-t", image, "-"],
        input=DOCKERFILE,
        text=True,
        check=True,
    )


def convert(input_dir: Path, work: Path, image: str) -> None:
    """DOCX를 PDF로 바꾸고 쪽 이미지와 쪽별 글자 수를 만든다."""
    script = """set -e
cd /work
mkdir -p out/pdf
for f in in/*.docx; do
  soffice --headless --convert-to pdf --outdir out/pdf "$f" >/dev/null 2>&1
done
for f in out/pdf/*.pdf; do
  name=$(basename "$f" .pdf)
  mkdir -p "out/$name"
  pdftoppm -png -r 110 "$f" "out/$name/page"
  pages=$(pdfinfo "$f" | awk '/^Pages:/ {print $2}')
  echo "$name pages $pages" >> out/report.txt
  for p in $(seq 1 "$pages"); do
    chars=$(pdftotext -f "$p" -l "$p" "$f" - | tr -d '[:space:]' | wc -c)
    echo "$name page $p $chars" >> out/report.txt
  done
done
"""
    soffice = local_soffice()
    if soffice:
        print("로컬 LibreOffice로 렌더링합니다.")
        run(["bash", "-lc", script.replace("soffice", soffice)], cwd=work)
        return

    if not shutil.which("docker"):
        raise SystemExit(
            "LibreOffice도 Docker도 찾지 못했습니다. 둘 중 하나가 있어야 렌더링할 수 있습니다."
        )
    ensure_image(image)
    mount = font_mount()
    command = ["docker", "run", "--rm", "-v", f"{work.resolve()}:/work"]
    if mount:
        host, guest = mount
        command += ["-v", f"{host.resolve()}:{guest}:ro"]
        script = "fc-cache -f >/dev/null 2>&1 || true\n" + script
    command += [image, "bash", "-lc", script]
    run(command)


def content_digest(path: Path) -> str:
    """DOCX 본문의 지문. 다시 저장할 때마다 바뀌는 압축 시간은 빼고 본문만 센다."""
    with zipfile.ZipFile(path) as archive:
        return hashlib.sha256(archive.read("word/document.xml")).hexdigest()[:16]


def read_report(report: Path) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for line in report.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) == 3 and parts[1] == "pages":
            result.setdefault(parts[0], {"pages": 0, "charsPerPage": []})["pages"] = int(parts[2])
        elif len(parts) == 4 and parts[1] == "page":
            result.setdefault(parts[0], {"pages": 0, "charsPerPage": []})["charsPerPage"].append(
                int(parts[3])
            )
    return result


def main() -> int:
    base = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser()
    published = base.parent / "docs" / "files"
    parser.add_argument("--input-dir", type=Path, default=published)
    parser.add_argument("--output-dir", type=Path, default=base / "qa" / "latest")
    parser.add_argument("--pdf-dir", type=Path, default=None, help="PDF를 따로 복사할 위치")
    parser.add_argument("--image", default=DEFAULT_IMAGE)
    args = parser.parse_args()

    sources = [args.input_dir / f"{name}.docx" for name in DOCUMENTS]
    missing = [str(path) for path in sources if not path.exists()]
    if missing:
        print(f"ERROR: 문서를 찾지 못했습니다: {', '.join(missing)}", file=sys.stderr)
        return 1

    work = args.output_dir.resolve()
    if work.exists():
        shutil.rmtree(work)
    (work / "in").mkdir(parents=True)
    for path in sources:
        shutil.copy2(path, work / "in" / path.name)

    convert(args.input_dir, work, args.image)

    report = work / "out" / "report.txt"
    if not report.exists():
        print("ERROR: 렌더 결과를 읽지 못했습니다.", file=sys.stderr)
        return 1

    data = read_report(report)
    manifest = {}
    for name in DOCUMENTS:
        entry = data.get(name)
        if not entry:
            print(f"ERROR: {name} 렌더 결과가 없습니다.", file=sys.stderr)
            return 1
        chars = entry["charsPerPage"]
        manifest[name] = {
            "pages": entry["pages"],
            "charsPerPage": chars,
            # 마지막 쪽이 앞쪽들에 비해 얼마나 찼는지. 낮으면 몇 줄만 남은 것이다.
            "lastPageFill": round(chars[-1] / (max(chars[:-1]) or 1), 3) if len(chars) > 1 else 1.0,
            # 이 결과가 어느 본문에서 나왔는지. 문서를 고치고 다시 렌더링하지 않으면 어긋난다.
            "sourceDigest": content_digest(args.input_dir / f"{name}.docx"),
        }

    for path in (work / "out" / "pdf").glob("*.pdf"):
        shutil.copy2(path, work / path.name)
    if args.pdf_dir:
        args.pdf_dir.mkdir(parents=True, exist_ok=True)
        for path in (work / "out" / "pdf").glob("*.pdf"):
            shutil.copy2(path, args.pdf_dir / path.name)

    payload = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    (work / "manifest.json").write_text(payload, encoding="utf-8")
    # 저장소 기록은 공개 문서를 렌더링했을 때만 덮는다. 초안을 한 번 재 보고 나면
    # 기록이 초안 지문으로 바뀌어, 고치지도 않은 문서가 테스트에서 어긋난다.
    if args.input_dir.resolve() == published.resolve():
        (base / "render-manifest.json").write_text(payload, encoding="utf-8", newline="\n")
    else:
        print(f"초안이라 저장소 기록은 그대로 둔다: {args.input_dir}")
    for name, info in manifest.items():
        print(f"{name}: {info['pages']}쪽, 마지막 쪽 채움 {info['lastPageFill']}")
    print(f"PASS: {work}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
