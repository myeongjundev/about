#!/usr/bin/env python3
"""Validate the T12 site and release inputs before publication."""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


SECRET_PATTERNS = {
    "private key": re.compile(r"BEGIN [A-Z ]*PRIVATE KEY"),
    "token": re.compile(r"(?i)(api[_-]?key|secret|password|passwd)\s*[:=]\s*[^\s]+"),
}


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.assets: list[str] = []
        self.ids: list[str] = []
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.append(str(values["id"]))
        if tag == "a" and values.get("href"):
            self.links.append(str(values["href"]))
        if tag == "link" and values.get("href"):
            self.assets.append(str(values["href"]))
        if tag in {"img", "script"} and values.get("src"):
            self.assets.append(str(values["src"]))


def empty(value: object) -> bool:
    return value is None or value == "" or value == [] or value == {}


def required_content(data: dict[str, object]) -> list[str]:
    missing: list[str] = []
    profile = data["profile"]
    story = data["story"]
    checks = {
        "profile.tagline": profile.get("tagline"),
        "profile.contact": profile.get("contact"),
        "story.firstSentence": story.get("firstSentence"),
        "story.lastSentence": story.get("lastSentence"),
    }
    for name, value in checks.items():
        if empty(value):
            missing.append(name)

    for item in data["numbers"]:
        for field in ("value", "label", "source", "asOf", "denominator"):
            if empty(item.get(field)):
                missing.append(f"numbers.{item['id']}.{field}")

    for item in data["works"]:
        if item.get("status") == "planned" and empty(item.get("plannedDate")):
            missing.append(f"works.{item['id']}.plannedDate")

    for item in data["experience"]:
        for field in ("period", "title", "role", "ability", "situation", "action", "result", "technologies"):
            if empty(item.get(field)):
                missing.append(f"experience.{item['id']}.{field}")
    return missing


def content_quality(data: dict[str, object]) -> list[str]:
    problems: list[str] = []
    profile = data["profile"]
    story = data["story"]
    tagline = str(profile.get("tagline") or "")
    if tagline and not tagline.endswith("사람"):
        problems.append("profile.tagline은 '사람'으로 끝나야 합니다.")

    story_parts = [story.get("firstSentence") or "", story.get("lastSentence") or ""]
    for segment in story.get("segments") or []:
        story_parts.extend((segment.get("summary") or "", segment.get("body") or ""))
    story_length = sum(len(str(part)) for part in story_parts)
    if story_length < 1400 or story_length > 1700:
        problems.append(f"이야기 분량은 1,400~1,700자여야 합니다: 현재 {story_length}자")
    return problems


def check_url(url: str) -> str | None:
    # A HEAD response can be healthy even when the page body fails at runtime.
    # Read one byte with GET so this check matches what an anonymous visitor opens
    # without downloading large linked files such as PDFs.
    request = urllib.request.Request(
        url,
        method="GET",
        headers={"User-Agent": "T12-release-check/1.0", "Accept": "*/*"},
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            if response.status >= 400:
                return f"HTTP {response.status}: {url}"
            response.read(1)
    except urllib.error.HTTPError as exc:
        return f"HTTP {exc.code}: {url}"
    except urllib.error.URLError as exc:
        return f"URL 오류: {url}: {exc.reason}"
    return None


def validate(repo: Path, allow_draft: bool, check_urls: bool) -> list[str]:
    problems: list[str] = []
    content_path = repo / "content" / "approved.json"
    site_path = repo / "docs" / "index.html"
    data = json.loads(content_path.read_text(encoding="utf-8"))
    site = site_path.read_text(encoding="utf-8")
    problems.extend(content_quality(data))

    if not allow_draft:
        if data.get("draft"):
            problems.append("approved.json이 draft 상태입니다.")
        problems.extend(f"미확정 값: {name}" for name in required_content(data))
        for marker in ('class="todo"', "data-draft=", "확정 필요", "파일 생성 전"):
            if marker in site:
                problems.append(f"사이트에 작업 표시가 남았습니다: {marker}")

    parser = LinkParser()
    parser.feed(site)
    duplicate_ids = sorted({value for value in parser.ids if parser.ids.count(value) > 1})
    problems.extend(f"중복 ID: {value}" for value in duplicate_ids)

    external: list[str] = []
    for href in parser.links:
        if href.startswith("#"):
            if href[1:] not in parser.ids:
                problems.append(f"없는 내부 링크 대상: {href}")
            continue
        parsed = urlparse(href)
        if parsed.scheme in {"https", "mailto"}:
            if "clovlabcalss.store" in parsed.netloc:
                problems.append(f"로그인이 필요한 URL: {href}")
            if parsed.scheme == "https":
                external.append(href)
            continue
        target = (site_path.parent / href).resolve()
        if not target.exists() and not allow_draft:
            problems.append(f"없는 파일 링크: {href}")

    for href in parser.assets:
        parsed = urlparse(href)
        if parsed.scheme in {"http", "https", "data"}:
            continue
        target = (site_path.parent / parsed.path).resolve()
        if not target.is_file():
            problems.append(f"없는 사이트 자산: {href}")

    for path in (repo / "docs", repo / "content", repo / "device", repo / "submission"):
        for file in path.rglob("*"):
            if not file.is_file() or file.suffix.lower() not in {".html", ".css", ".json", ".md", ".py", ".txt", ".csv", ".tpl"}:
                continue
            text = file.read_text(encoding="utf-8", errors="ignore")
            for label, pattern in SECRET_PATTERNS.items():
                if pattern.search(text):
                    problems.append(f"비밀값 의심 문자열 {label}: {file.relative_to(repo)}")

    if not allow_draft:
        for file in (repo / "submission").glob("*.md"):
            if "[확정 필요]" in file.read_text(encoding="utf-8"):
                problems.append(f"제출문에 확정 표시가 남았습니다: {file.relative_to(repo)}")

    if check_urls:
        for url in sorted(set(external)):
            problem = check_url(url)
            if problem:
                problems.append(problem)
    return problems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--allow-draft", action="store_true")
    parser.add_argument("--check-urls", action="store_true")
    args = parser.parse_args()
    try:
        problems = validate(args.repo.resolve(), args.allow_draft, args.check_urls)
    except (OSError, KeyError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    if problems:
        for problem in problems:
            print(f"FAIL: {problem}")
        return 1
    print("PASS: release validation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
