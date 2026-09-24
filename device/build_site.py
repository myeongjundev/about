#!/usr/bin/env python3
"""Build the static T12 site from approved public content."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
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


def render_project_rail(data: dict[str, object]) -> str:
    projects = []
    work_ids = set()

    for item in data.get("works") or []:
        if item.get("status") != "published":
            continue
        work_ids.add(item["id"])
        projects.append(
            {
                "target": f"work-{item['id']}",
                "period": item.get("period") or "",
                "kind": item.get("kind") or "",
                "title": item["title"],
                "visual": item.get("visual"),
            }
        )

    for item in data.get("experience") or []:
        if item.get("status") != "published" or item["id"] in work_ids:
            continue
        gallery = item.get("gallery") or []
        projects.append(
            {
                "target": f"experience-{item['id']}",
                "period": item.get("period") or "",
                "kind": item.get("role") or "",
                "title": item["title"],
                "visual": gallery[0] if gallery else None,
            }
        )

    cards = []
    for index, item in enumerate(projects, start=1):
        visual = item.get("visual")
        image = ""
        image_class = ""
        if visual:
            image_class = " has-image"
            image = (
                f'<img src="{safe_href(visual["src"])}" alt="" '
                f'width="{esc(visual["width"])}" height="{esc(visual["height"])}" '
                'loading="lazy" decoding="async">'
            )
        cards.append(
            f'''        <a class="build-card" href="#{esc(item['target'])}" style="--stack-order: {index - 1}; --stack-top: {28 + (index - 1) * 26}px">
          <span class="build-card-visual{image_class}" aria-hidden="true">
            {image}
            <span class="build-card-number">{index:02d}</span>
            <span class="build-card-mark">VIEW ↗</span>
          </span>
          <span class="build-card-meta mono"><span>{esc(item['period'])}</span><span>{esc(item['kind'])}</span></span>
          <strong>{esc(item['title'])}</strong>
        </a>'''
        )

    if not cards:
        return ""

    return f'''    <section class="build-reel" aria-labelledby="build-reel-title">
      <div class="build-reel-head">
        <p class="mono">SELECTED BUILDS</p>
        <span class="mono">01—{len(cards):02d}</span>
      </div>
      <h2 id="build-reel-title">만들고 끝까지 확인한 작업</h2>
      <p class="build-reel-intro">실제 화면과 결과가 남아 있는 작업을 골랐습니다.</p>
      <div class="build-stack">
{chr(10).join(cards)}
      </div>
    </section>'''


# 처음 온 사람이 결과물부터 보도록 대표작을 맨 앞에 둔다. 이야기·숫자는 그 뒤에서 근거를 채운다.
SECTION_ENTRANCES = (
    ("work", "대표작"),
    ("story", "이야기"),
    ("numbers", "숫자"),
    ("experience", "경력"),
    ("documents", "문서"),
)


def render_entrances(variant: str = "side") -> str:
    rail = variant == "rail"
    indent = "    " if rail else "      "
    items = []
    for index, (anchor, label) in enumerate(SECTION_ENTRANCES, start=1):
        items.append(
            f'''{indent}    <li>
{indent}      <a href="#{anchor}">
{indent}        <span class="nav-index mono" aria-hidden="true">{index:02d}</span>
{indent}        <span class="entrance-copy">{esc(label)}</span>
{indent}        <span class="arrow" aria-hidden="true">↗</span>
{indent}      </a>
{indent}    </li>'''
        )

    last = f"{len(SECTION_ENTRANCES):02d}"
    classes = "entrances entrances-rail" if rail else "entrances"
    label_text = "섹션 바로가기" if rail else "바로 가기"
    return f'''{indent}<nav class="{classes}" aria-label="{label_text}">
{indent}  <div class="entrances-head">
{indent}    <span class="mono">SECTIONS</span>
{indent}    <span class="mono">01 — {last}</span>
{indent}  </div>
{indent}  <span class="entrance-indicator" aria-hidden="true"></span>
{indent}  <ol>
{chr(10).join(items)}
{indent}  </ol>
{indent}</nav>'''


def render_sidebar(data: dict[str, object], draft: bool) -> str:
    profile = data["profile"]
    technologies = profile.get("technologies") or {}
    stack = []
    for category, items in technologies.items():
        stack.append(
            f'<span><span class="mono muted">{esc(category)}</span><span>{esc(" · ".join(items))}</span></span>'
        )

    education = "<br>".join(
        f"{esc(item['name'])}"
        + (f" · {esc(item['org'])}" if item.get("org") else "")
        + f" <span class=\"mono muted\">{esc(item['period'])}</span>"
        for item in profile.get("education") or []
    )
    contact = profile.get("contact")
    if contact:
        contact_html = f'<a href="{safe_href(contact["href"])}">{esc(contact["label"])}</a>'
    else:
        contact_html = value_or_todo(None, draft, "공개 연락 수단 확정 필요")

    return f"""    <div class="side-column">
    <aside class="side">
      <header class="intro">
        <div class="profile-topline">
          <span class="avatar" aria-hidden="true">MJ</span>
          <span class="profile-actions">
            <span class="availability"><span aria-hidden="true"></span> Portfolio 2026</span>
            <button class="theme-toggle" type="button" aria-pressed="false">
              <span class="theme-icon" aria-hidden="true">◐</span><span class="theme-label">Dark mode</span>
            </button>
          </span>
        </div>
        <span class="mono muted site-id">myeongjundev / portfolio</span>
        <h1>{esc(profile['name'])}</h1>
        <p class="role">{esc(profile['role'])}</p>
        <p class="tagline">{value_or_todo(profile.get('tagline'), draft, '본인이 쓸 한 줄 소개')}</p>
        <div class="craft-console" aria-label="작업 방식">
          <div class="craft-console-head">
            <span class="mono">HOW I WORK</span>
            <output class="craft-output mono" aria-live="polite">01 / DESIGN</output>
          </div>
          <div class="craft-path" role="group" aria-label="작업 단계">
            <button type="button" data-craft="design" data-index="01" data-copy="문제와 사용 흐름을 먼저 정리합니다." aria-pressed="true"><span>01</span>DESIGN</button>
            <button type="button" data-craft="build" data-index="02" data-copy="화면과 서버를 하나의 서비스로 연결합니다." aria-pressed="false"><span>02</span>BUILD</button>
            <button type="button" data-craft="ship" data-index="03" data-copy="배포하고 실제 결과까지 확인합니다." aria-pressed="false"><span>03</span>SHIP</button>
          </div>
          <p class="craft-caption">문제와 사용 흐름을 먼저 정리합니다.</p>
        </div>
      </header>

{render_entrances()}

      <dl class="facts">
        <div><dt>방향</dt><dd>{esc(profile['direction'])}</dd></div>
        <div><dt>기술</dt><dd class="stack">{''.join(stack)}</dd></div>
        <div><dt>교육</dt><dd>{education}</dd></div>
        <div><dt>연락</dt><dd>{contact_html}</dd></div>
      </dl>
    </aside>
{render_project_rail(data)}
    </div>"""


def render_story(data: dict[str, object], draft: bool) -> str:
    story = data["story"]
    segments = []
    for index, segment in enumerate(story["segments"], start=1):
        pair = ""
        paired = [
            item for item in data["numbers"] if item.get("linkedSegment") == segment["id"]
        ]
        if paired:
            pair = f'<p class="pair">↔ 숫자 · 「{esc(paired[0]["label"])}」</p>'
        segments.append(
            f"""        <article class="stage reveal" id="story-{esc(segment['id'])}">
          <span class="stage-index" aria-hidden="true">0{index}</span>
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
        <p class="lead lead-opening">{value_or_todo(story.get('firstSentence'), draft, '본인이 쓸 첫 문장')}</p>
{chr(10).join(segments)}
        <p class="lead closing">{value_or_todo(story.get('lastSentence'), draft, '본인이 쓸 마지막 문장')}</p>
      </section>"""


def render_numbers(data: dict[str, object], draft: bool) -> str:
    cards = []
    story_titles = {
        str(segment["id"]): str(segment["stage"])
        for segment in data["story"]["segments"]
    }
    for index, item in enumerate(data["numbers"], start=1):
        detail = f'<span class="label-detail">{esc(item["detail"])}</span>' if item.get("detail") else ""
        linked_segment = item.get("linkedSegment")
        linked = ""
        if linked_segment:
            linked_title = story_titles[str(linked_segment)]
            linked = f'<span class="pair">↔ 이야기 · 「{esc(linked_title)}」</span>'
        progress = 0
        value = str(item.get("value") or "")
        match = re.search(r"(\d+)\s*/\s*(\d+)", value)
        if match and int(match.group(2)):
            progress = round(int(match.group(1)) / int(match.group(2)) * 100)
        cards.append(
            f"""          <article class="metric reveal">
            <span class="metric-index mono">0{index}</span>
            <span class="value">{value_or_todo(item.get('value'), draft, '집계 필요')}</span>
            <span class="label">{esc(item['label'])}</span>
            {detail}
            <span class="metric-bar" aria-hidden="true"><span style="--progress: {progress}%"></span></span>
            <span class="source">근거 · {value_or_todo(item.get('supports'), draft, '근거 능력 필요')}<br>출처 · {esc(item['source'])}<br>기준 · {value_or_todo(item.get('asOf'), draft, '기준일 필요')}<br>분모 · {value_or_todo(item.get('denominator'), draft, '분모 정의 필요')}</span>
            {linked}
          </article>"""
        )
    return f"""      <section id="numbers">
{section_head('숫자', '회복탄력성과 과제지속력을 13주 과정 기록의 숫자로 보여 줍니다. 값마다 근거 능력과 출처, 기준일을 표시했습니다.')}
        <div class="metrics">
{chr(10).join(cards)}
        </div>
      </section>"""


def render_works(data: dict[str, object], draft: bool) -> str:
    cards = []
    for index, item in enumerate(data["works"], start=1):
        links = "".join(
            f'<a href="{safe_href(link["href"])}">{esc(link["label"])}</a>'
            for link in item.get("links") or []
        )
        visual = item.get("visual")
        if visual:
            visual_class = " has-image"
            visual_accessibility = ""
            # 좁은 칸에서 잘릴 때 글자가 시작하는 쪽을 남기도록 그림마다 초점을 정할 수 있다.
            focus = f' style="object-position: {esc(visual["focus"])}"' if visual.get("focus") else ""
            visual_media = (
                f'<img src="{safe_href(visual["src"])}" alt="{esc(visual["alt"])}" '
                f'width="{esc(visual["width"])}" height="{esc(visual["height"])}"{focus} '
                'loading="lazy" decoding="async">'
            )
            signal = ""
        else:
            visual_class = ""
            visual_accessibility = ' aria-hidden="true"'
            visual_media = ""
            signal = '<span class="work-signal"></span>'
        period = item.get("period")
        if item.get("status") == "planned":
            period = f"예정 · {value_or_todo(item.get('plannedDate'), draft, '예정일 확정 필요')}"
        pending = " pending" if item.get("status") == "planned" else " published"
        status_label = "NEXT" if item.get("status") == "planned" else "LIVE"
        case_study = item.get("caseStudy") or {}
        case_html = ""
        if case_study:
            steps = (
                ("01", "문제", "PROBLEM", case_study.get("problem")),
                ("02", "판단", "DECISION", case_study.get("decision")),
                ("03", "구현", "BUILD", case_study.get("implementation")),
                ("04", "검증", "VERIFY", case_study.get("validation")),
            )
            step_html = []
            for step_number, label, english, value in steps:
                step_html.append(
                    f'''                <section class="case-step">
                  <span class="case-step-index mono">{step_number} / {esc(english)}</span>
                  <h4>{esc(label)}</h4>
                  <p>{value_or_todo(value, draft, f'{label} 확정 필요')}</p>
                </section>'''
                )
            case_html = f'''            <details class="work-case">
              <summary>
                <span><span class="mono">CASE NOTES</span><span class="case-summary-open">문제부터 검증까지 보기</span><span class="case-summary-close">사례 노트 접기</span></span>
                <span class="case-icon" aria-hidden="true">＋</span>
              </summary>
              <div class="case-grid">
{chr(10).join(step_html)}
              </div>
            </details>'''
        cards.append(
            f"""          <article id="work-{esc(item['id'])}" class="work{pending} reveal">
            <div class="work-visual{visual_class}"{visual_accessibility}>
              {visual_media}
              <span class="work-number">0{index}</span>
              {signal}
              <span class="work-status">{status_label}</span>
            </div>
            <div class="work-copy">
              <span class="mono muted work-kind">CASE {index:02d} · {esc(item['kind'])} · {period if '<span' in str(period) else esc(period)}</span>
              <h3 class="work-title">{esc(item['title'])}</h3>
              <p class="work-desc">{esc(item['summary'])}</p>
              <p class="links">{links}</p>
            </div>
{case_html}
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
    work_ids = {str(work["id"]) for work in data.get("works") or [] if work.get("status") == "published"}
    for index, item in enumerate(data["experience"], start=1):
        links = "".join(
            f'<a href="{safe_href(link["href"])}">{esc(link["label"])}</a>'
            for link in item.get("links") or []
        )

        gallery_items = []
        for image in item.get("gallery") or []:
            gallery_items.append(
                f'''            <figure class="gallery-item">
              <img src="{safe_href(image['src'])}" alt="{esc(image['alt'])}" width="{esc(image['width'])}" height="{esc(image['height'])}" loading="lazy" decoding="async">
              <figcaption>{esc(image['label'])}</figcaption>
            </figure>'''
            )
        gallery = ""
        if gallery_items:
            gallery = f'''          <div class="project-gallery" aria-label="{esc(item['title'])} 화면">
{chr(10).join(gallery_items)}
          </div>'''
        tech = " · ".join(item.get("technologies") or [])
        work_id = item.get("workId")
        if work_id and str(work_id) in work_ids:
            # 대표작에 사례 노트가 이미 있으므로, 경력에는 화면과 결과 한 줄, 대표작 링크만 둔다.
            # 상황·행동·결과 전체는 경력기술서 문서에 그대로 있다.
            entries.append(
                f"""        <article id="experience-{esc(item['id'])}" class="exp exp-compact reveal">
          <span class="exp-index mono" aria-hidden="true">0{index}</span>
          <div class="exp-meta">
            <span class="mono muted">{value_or_todo(item.get('period'), draft, '기간 확정 필요')}</span>
            <span class="spacer"></span>
            <span class="ability">{esc(item['ability'])}</span>
          </div>
          <h3 class="exp-title">{esc(item['title'])}</h3>
          <p class="exp-role">{esc(item.get('role') or '')}</p>
{gallery}
          <p class="exp-result">{esc(item.get('result') or '')}</p>
          <p class="exp-foot"><span class="mono muted">{esc(tech)}</span><span class="links"><a href="#work-{esc(work_id)}">대표작에서 자세히 보기 ↑</a>{links}</span></p>
        </article>"""
            )
            continue
        entries.append(
            f"""        <article id="experience-{esc(item['id'])}" class="exp reveal">
          <span class="exp-index mono" aria-hidden="true">0{index}</span>
          <div class="exp-meta">
            <span class="mono muted">{value_or_todo(item.get('period'), draft, '기간 확정 필요')}</span>
            <span class="spacer"></span>
            <span class="ability">{esc(item['ability'])}</span>
          </div>
          <h3 class="exp-title">{value_or_todo(item.get('title'), draft, '세 번째 경력 항목 선택 필요')}</h3>
          <p class="exp-role">{value_or_todo(item.get('role'), draft, '역할 확정 필요')}</p>
{gallery}
          <dl class="star">
            <dt>상황</dt><dd>{value_or_todo(item.get('situation'), draft, '상황 확정 필요')}</dd>
            <dt>행동</dt><dd>{value_or_todo(item.get('action'), draft, '행동 확정 필요')}</dd>
            <dt>결과</dt><dd>{value_or_todo(item.get('result'), draft, '결과 확정 필요')}</dd>
          </dl>
          <p class="exp-foot"><span class="mono muted">{value_or_todo(tech, draft, '기술 확정 필요')}</span><span class="links">{links}</span></p>
        </article>"""
        )
    return f"""      <section id="experience">
{section_head('경력과 과제', '과제마다 능력과 상황, 행동, 결과를 같은 순서로 적었습니다. 대표작에 있는 작업은 화면과 결과 한 줄만 두었습니다.')}
{chr(10).join(entries)}
      </section>"""


def render_documents(data: dict[str, object], output: Path, draft: bool) -> str:
    links = []
    for item in data["documents"]:
        # 워드가 없는 사람도 볼 수 있도록 같은 문서를 DOCX와 PDF로 함께 둔다.
        formats = [(item["format"], item["href"])]
        if item.get("pdfHref"):
            formats.append(("PDF", item["pdfHref"]))
        missing = [href for _, href in formats if not (output.parent / href).exists()]
        if not missing:
            buttons = "".join(
                f'<a href="{safe_href(href)}">{esc(label)}</a>' for label, href in formats
            )
            link = (
                f'<div class="doc-card"><span class="doc-name">{esc(item["label"])}</span>'
                f'<span class="doc-formats">{buttons}</span></div>'
            )
        elif draft:
            link = f'<div class="document-pending"><span>{esc(item["label"])}</span><span class="fmt todo" data-draft="true">파일 생성 전</span></div>'
        else:
            raise ValueError(f"문서 파일이 없습니다: {', '.join(missing)}")
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
        <p class="contact-kicker mono">LET'S BUILD SOMETHING RELIABLE.</p>
        <p class="name">{esc(data['profile']['name'])}</p>
        <p class="contact-link">{contact_html}</p>
        <p class="note">새 기록을 넣으면 숫자와 문장 후보를 다시 만들 수 있습니다 · 숫자 기준일 {esc(data['updatedAt'])}</p>
      </footer>"""


def build(data_path: Path, output: Path, template_path: Path, draft: bool) -> None:
    data = json.loads(data_path.read_text(encoding="utf-8"))
    if data.get("draft") and not draft:
        raise ValueError("approved.json이 draft 상태입니다. 최종 빌드를 중단합니다.")
    template = template_path.read_text(encoding="utf-8")
    repo = template_path.parents[2]
    asset_hash = hashlib.sha256()
    for asset in (repo / "docs" / "styles.css", repo / "docs" / "app.js"):
        asset_hash.update(asset.read_bytes())
    asset_version = asset_hash.hexdigest()[:12]
    banner = ""
    if draft:
        banner = '  <p class="draft-banner" role="status">작업 중인 미리보기입니다. 노란 표시는 본인 확인이 필요합니다.</p>'
    main = "\n\n".join(
        (
            render_works(data, draft),
            render_story(data, draft),
            render_numbers(data, draft),
            render_experience(data, draft),
            render_documents(data, output, draft),
        )
    )
    replacements = {
        "{{TITLE}}": esc(f"{data['profile']['name']} 자기소개"),
        "{{DESCRIPTION}}": esc(f"{data['profile']['name']}의 이야기와 기록, 대표작, 경력, 문서"),
        "{{ASSET_VERSION}}": asset_version,
        "{{DRAFT_BANNER}}": banner,
        "{{SIDEBAR}}": render_sidebar(data, draft),
        "{{MAIN}}": main,
        "{{SECTION_RAIL}}": render_entrances("rail"),
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
