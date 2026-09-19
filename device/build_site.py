#!/usr/bin/env python3
"""Build the static T12 site from approved public content."""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path
from urllib.parse import urlparse


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def missing(value: object) -> bool:
    return value is None or value == "" or value == [] or value == {}


def value_or_todo(value: object, draft: bool, label: str = "확정 필요") -> str:
    if not missing(value):
        return esc(value)
    if not draft:
        raise ValueError(label)
    return f'<span class="todo" data-draft="true">{esc(label)}</span>'


def safe_href(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme and parsed.scheme not in {"https", "mailto"}:
        raise ValueError(f"허용되지 않은 링크 형식: {value}")
    return esc(value)


def section_head(title: str, note: str | None = None) -> str:
    note_html = f"\n          <p>{esc(note)}</p>" if note else ""
    return f"""        <div class="section-head">
          <h2>{esc(title)}</h2>{note_html}
        </div>"""


def render_sidebar(data: dict[str, object], draft: bool) -> str:
    profile = data["profile"]
    technologies = profile.get("technologies") or {}
    stack = []
    for category, items in technologies.items():
        stack.append(
            f'<span><span class="mono muted">{esc(category)}</span><span>{esc(" · ".join(items))}</span></span>'
        )

    education = "<br>".join(
        f"{esc(item['name'])} <span class=\"mono muted\">{esc(item['period'])}</span>"
        for item in profile.get("education") or []
    )
    contact = profile.get("contact")
    if contact:
        contact_html = f'<a href="{safe_href(contact["href"])}">{esc(contact["label"])}</a>'
    else:
        contact_html = value_or_todo(None, draft, "공개 연락 수단 확정 필요")

    return f"""    <aside class="side">
      <header class="intro">
        <span class="mono muted">myeongjundev.github.io/about</span>
        <h1>{esc(profile['name'])}</h1>
        <p class="role">{esc(profile['role'])}</p>
        <p class="tagline">{value_or_todo(profile.get('tagline'), draft, '본인이 쓸 한 줄 소개')} </p>
      </header>

      <nav class="entrances" aria-label="바로 가기">
        <a href="#story"><span>이야기</span><span class="arrow" aria-hidden="true">→</span></a>
        <a href="#numbers"><span>숫자</span><span class="arrow" aria-hidden="true">→</span></a>
        <a href="#work"><span>대표작</span><span class="arrow" aria-hidden="true">→</span></a>
        <a href="#experience"><span>경력</span><span class="arrow" aria-hidden="true">→</span></a>
        <a href="#documents"><span>문서</span><span class="arrow" aria-hidden="true">→</span></a>
      </nav>

      <dl class="facts">
        <div><dt>방향</dt><dd>{esc(profile['direction'])}</dd></div>
        <div><dt>기술</dt><dd class="stack">{''.join(stack)}</dd></div>
        <div><dt>교육</dt><dd>{education}</dd></div>
        <div><dt>연락</dt><dd>{contact_html}</dd></div>
      </dl>
    </aside>"""


def render_story(data: dict[str, object], draft: bool) -> str:
    story = data["story"]
    segments = []
    for segment in story["segments"]:
        pair = ""
        paired = [
            item for item in data["numbers"] if item.get("linkedSegment") == segment["id"]
        ]
        if paired:
            pair = f'<p class="pair">↔ 숫자 「{esc(paired[0]["label"])}」와 연결</p>'
        segments.append(
            f"""        <article class="stage" id="story-{esc(segment['id'])}">
          <div class="stage-meta">
            <time class="mono date" datetime="{esc(segment['date'])}">{esc(segment['period'])}</time>
            <span class="stage-name">{esc(segment['stage'])}</span>
            <span class="spacer"></span>
            <span class="ability">드러난 능력 · {esc(segment['ability'])}</span>
          </div>
          <p class="summary">{esc(segment['summary'])}</p>
          <p class="body">{esc(segment['body'])}</p>
          {pair}
        </article>"""
        )
    return f"""      <section id="story">
{section_head('이야기', '고난에서 다시 시작한 날을 거쳐 지금의 학습 방식으로 이어집니다.')}
        <p class="lead">{value_or_todo(story.get('firstSentence'), draft, '본인이 쓸 첫 문장')}</p>
{chr(10).join(segments)}
        <p class="lead closing">{value_or_todo(story.get('lastSentence'), draft, '본인이 쓸 마지막 문장')}</p>
      </section>"""


def render_numbers(data: dict[str, object], draft: bool) -> str:
    cards = []
    for item in data["numbers"]:
        detail = f'<span class="label-detail">{esc(item["detail"])}</span>' if item.get("detail") else ""
        linked = f'<span class="pair">↔ 이야기 {esc(item["linkedSegment"])}</span>' if item.get("linkedSegment") else ""
        cards.append(
            f"""          <div class="metric">
            <span class="value">{value_or_todo(item.get('value'), draft, '집계 필요')}</span>
            <span class="label">{esc(item['label'])}</span>
            {detail}
            <span class="source">출처 · {esc(item['source'])}<br>기준 · {value_or_todo(item.get('asOf'), draft, '기준일 필요')}<br>분모 · {value_or_todo(item.get('denominator'), draft, '분모 정의 필요')}</span>
            {linked}
          </div>"""
        )
    return f"""      <section id="numbers">
{section_head('숫자', '13주 과정 기록에서 옮겼으며 값마다 출처와 기준일을 표시했습니다.')}
        <div class="metrics">
{chr(10).join(cards)}
        </div>
      </section>"""


def render_works(data: dict[str, object], draft: bool) -> str:
    cards = []
    for item in data["works"]:
        links = "".join(
            f'<a href="{safe_href(link["href"])}">{esc(link["label"])}</a>'
            for link in item.get("links") or []
        )
        period = item.get("period")
        if item.get("status") == "planned":
            period = f"예정 · {value_or_todo(item.get('plannedDate'), draft, '예정일 확정 필요')}"
        pending = " pending" if item.get("status") == "planned" else ""
        cards.append(
            f"""          <article class="work{pending}">
            <span class="mono muted">{esc(item['kind'])} · {period if '<span' in str(period) else esc(period)}</span>
            <h3 class="work-title">{esc(item['title'])}</h3>
            <p class="work-desc">{esc(item['summary'])}</p>
            <p class="links">{links}</p>
          </article>"""
        )
    return f"""      <section id="work">
{section_head('대표작')}
        <div class="works">
{chr(10).join(cards)}
        </div>
      </section>"""


def render_experience(data: dict[str, object], draft: bool) -> str:
    entries = []
    for item in data["experience"]:
        links = "".join(
            f'<a href="{safe_href(link["href"])}">{esc(link["label"])}</a>'
            for link in item.get("links") or []
        )
        tech = " · ".join(item.get("technologies") or [])
        entries.append(
            f"""        <article class="exp">
          <div class="exp-meta">
            <span class="mono muted">{value_or_todo(item.get('period'), draft, '기간 확정 필요')}</span>
            <span class="spacer"></span>
            <span class="ability">{esc(item['ability'])}</span>
          </div>
          <h3 class="exp-title">{value_or_todo(item.get('title'), draft, '세 번째 경력 항목 선택 필요')}</h3>
          <p class="exp-role">{value_or_todo(item.get('role'), draft, '역할 확정 필요')}</p>
          <dl class="star">
            <dt>상황</dt><dd>{value_or_todo(item.get('situation'), draft, '상황 확정 필요')}</dd>
            <dt>행동</dt><dd>{value_or_todo(item.get('action'), draft, '행동 확정 필요')}</dd>
            <dt>결과</dt><dd>{value_or_todo(item.get('result'), draft, '결과 확정 필요')}</dd>
          </dl>
          <p class="exp-foot"><span class="mono muted">{value_or_todo(tech, draft, '기술 확정 필요')}</span><span class="links">{links}</span></p>
        </article>"""
        )
    return f"""      <section id="experience">
{section_head('경력과 과제', '과제마다 능력과 상황, 행동, 결과를 같은 순서로 적었습니다.')}
{chr(10).join(entries)}
      </section>"""


def render_documents(data: dict[str, object], output: Path, draft: bool) -> str:
    links = []
    for item in data["documents"]:
        target = output.parent / item["href"]
        if target.exists():
            link = f'<a href="{safe_href(item["href"])}"><span>{esc(item["label"])}</span><span class="fmt">{esc(item["format"])} 내려받기</span></a>'
        elif draft:
            link = f'<div class="document-pending"><span>{esc(item["label"])}</span><span class="fmt todo" data-draft="true">파일 생성 전</span></div>'
        else:
            raise ValueError(f"문서 파일이 없습니다: {item['href']}")
        links.append(link)

    contact = data["profile"].get("contact")
    if contact:
        contact_html = f'<a href="{safe_href(contact["href"])}">{esc(contact["label"])}</a>'
    else:
        contact_html = value_or_todo(None, draft, "공개 연락 수단 확정 필요")

    return f"""      <section id="documents">
{section_head('문서', '로그인과 비밀번호 없이 내려받을 수 있습니다.')}
        <div class="doc-list">{''.join(links)}</div>
      </section>

      <footer id="contact" class="contact">
        <p class="name">{esc(data['profile']['name'])}</p>
        <p>{contact_html}</p>
        <p class="note">새 기록을 넣으면 숫자와 문장 후보를 다시 만들 수 있습니다 · 마지막 갱신 {esc(data['updatedAt'])}</p>
      </footer>"""


def build(data_path: Path, output: Path, template_path: Path, draft: bool) -> None:
    data = json.loads(data_path.read_text(encoding="utf-8"))
    if data.get("draft") and not draft:
        raise ValueError("approved.json이 draft 상태입니다. 최종 빌드를 중단합니다.")
    template = template_path.read_text(encoding="utf-8")
    banner = ""
    if draft:
        banner = '  <p class="draft-banner" role="status">작업 중인 미리보기입니다. 노란 표시는 본인 확인이 필요합니다.</p>'
    main = "\n\n".join(
        (
            render_story(data, draft),
            render_numbers(data, draft),
            render_works(data, draft),
            render_experience(data, draft),
            render_documents(data, output, draft),
        )
    )
    replacements = {
        "{{TITLE}}": esc(f"{data['profile']['name']} 자기소개"),
        "{{DESCRIPTION}}": esc(f"{data['profile']['name']}의 이야기와 기록, 대표작, 경력, 문서"),
        "{{DRAFT_BANNER}}": banner,
        "{{SIDEBAR}}": render_sidebar(data, draft),
        "{{MAIN}}": main,
    }
    for token, replacement in replacements.items():
        template = template.replace(token, replacement)
    output.parent.mkdir(parents=True, exist_ok=True)
    clean = "\n".join(line.rstrip() for line in template.splitlines()).rstrip() + "\n"
    output.write_text(clean, encoding="utf-8", newline="\n")


def main() -> int:
    base = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser()
    parser.add_argument("--content", type=Path, default=base.parent / "content" / "approved.json")
    parser.add_argument("--output", type=Path, default=base.parent / "docs" / "index.html")
    parser.add_argument("--template", type=Path, default=base / "templates" / "page.html.tpl")
    parser.add_argument("--draft", action="store_true")
    args = parser.parse_args()
    try:
        build(args.content.resolve(), args.output.resolve(), args.template.resolve(), args.draft)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"PASS: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
