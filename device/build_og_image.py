#!/usr/bin/env python3
"""공유 미리보기 그림을 만든다.

카카오톡·슬랙·링크드인에 링크를 붙이면 이 그림이 뜬다. 글자는 지어내지 않고
`approved.json`의 이름·직무·한 줄 소개를 그대로 쓴다. 사이트가 바뀌면 이 그림도
같은 값에서 다시 만들어진다.

WebP가 아니라 PNG로 낸다. 링크를 읽어 가는 쪽 가운데 WebP를 못 다루는 데가 있다.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

WIDTH = 1200
HEIGHT = 630
MARGIN = 84

# 어두운 테마 토큰을 그대로 쓴다. 작게 줄여도 글자가 바탕에서 떨어져 보인다.
BG = (11, 16, 32)
INK = (245, 247, 255)
MUTED = (180, 190, 208)
FAINT = (127, 139, 163)
ACCENT = (125, 156, 255)

FONT_DIR = Path("C:/Windows/Fonts")
BOLD = FONT_DIR / "malgunbd.ttf"
BODY = FONT_DIR / "malgun.ttf"
MONO = FONT_DIR / "consola.ttf"


def font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    if not path.exists():
        raise SystemExit(f"글꼴을 찾지 못했다: {path}")
    return ImageFont.truetype(str(path), size)


def glow(image: Image.Image) -> None:
    """사이트 바탕에 있는 원형 번짐을 작게 그려 키운다. 한 번에 그리면 느리다."""
    small = Image.new("RGB", (120, 63), BG)
    pixels = small.load()
    cx, cy, radius = 12, 6, 62
    for y in range(small.height):
        for x in range(small.width):
            distance = ((x - cx) ** 2 + ((y - cy) * 1.9) ** 2) ** 0.5
            if distance >= radius:
                continue
            strength = (1 - distance / radius) * 0.22
            pixels[x, y] = tuple(
                round(BG[i] + (ACCENT[i] - BG[i]) * strength) for i in range(3)
            )
    image.paste(small.resize((WIDTH, HEIGHT), Image.BICUBIC), (0, 0))


def wrap(draw: ImageDraw.ImageDraw, text: str, face: ImageFont.FreeTypeFont, limit: int) -> list[str]:
    lines: list[str] = []
    line = ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if draw.textlength(trial, font=face) <= limit or not line:
            line = trial
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def wrap_balanced(
    draw: ImageDraw.ImageDraw, text: str, face: ImageFont.FreeTypeFont, limit: int
) -> list[str]:
    """줄 수는 그대로 두고 폭만 좁혀 본다. 마지막 줄에 한 낱말만 남는 모양을 피한다."""
    lines = wrap(draw, text, face, limit)
    if len(lines) < 2:
        return lines
    low, high = 1, limit
    while low < high:
        mid = (low + high) // 2
        if len(wrap(draw, text, face, mid)) <= len(lines):
            high = mid
        else:
            low = mid + 1
    return wrap(draw, text, face, low)


def build(data: dict, output: Path) -> None:
    profile = data["profile"]
    name = profile["name"]
    role = profile["role"]
    tagline = profile["tagline"]
    site = profile["site"]["href"].replace("https://", "").rstrip("/")

    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    glow(image)
    draw = ImageDraw.Draw(image)

    draw.text((MARGIN, 76), "myeongjundev / portfolio", font=font(MONO, 26), fill=FAINT)
    draw.text((MARGIN, 136), name, font=font(BOLD, 116), fill=INK)
    draw.text((MARGIN, 286), role, font=font(BODY, 34), fill=ACCENT)

    draw.line([(MARGIN, 356), (MARGIN + 92, 356)], fill=ACCENT, width=4)

    face = font(BOLD, 46)
    top = 396
    for line in wrap_balanced(draw, tagline, face, WIDTH - MARGIN * 2):
        draw.text((MARGIN, top), line, font=face, fill=INK)
        top += 62

    draw.text((MARGIN, HEIGHT - 84), site, font=font(MONO, 27), fill=MUTED)

    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, "PNG", optimize=True)


def main() -> int:
    base = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser()
    parser.add_argument("--content", type=Path, default=base.parent / "content" / "approved.json")
    parser.add_argument("--output", type=Path, default=base.parent / "docs" / "assets" / "og-card.png")
    args = parser.parse_args()

    data = json.loads(args.content.read_text(encoding="utf-8"))
    build(data, args.output)
    size = args.output.stat().st_size
    print(f"PASS: {args.output} ({WIDTH}x{HEIGHT}, {size // 1024}KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
