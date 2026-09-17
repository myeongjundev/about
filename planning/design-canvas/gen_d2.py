import json, pathlib, sys

root = pathlib.Path(__file__).parent / "project"
preview = pathlib.Path(__file__).parent / "preview"
preview.mkdir(exist_ok=True)

INK = "#1C1917"
MUTED = "#57534E"
FAINT = "#A8A29E"
LINE = "#E7E5E4"
BAR = "#E7E5E4"
BG = "#FAFAF9"
MONO = "'Geist Mono', monospace"
ACC = "{{accent}}"

STAGES = [
    ("[2024.12.05]", "고난", "[요약줄 후보] 프로젝트가 끝난 뒤 남은 클라우드 비용을 청구 내역부터 읽었다", "자기조절력"),
    ("[2025.02.03]", "다시 일어난 날", "[요약줄 후보] 졸업을 기다리며 시작한 일을 1년 동안 이어 간 뒤 개발 과정에 들어갔다", "자기동기력"),
    ("[2026.08.04]", "더 나아진 지금", "[요약줄 후보] 팀 저장소의 리뷰로 동료의 작업을 합쳐 서비스를 완성했다", "대인관계력"),
]
METRICS = [
    ("출석일 / 전체 수업일", "내 출석 기록", True),
    ("리추얼 기록 일수 / 13주", "리추얼 기록", False),
    ("기한 안에 낸 과제 / 전체", "내 제출 현황", False),
]
EXPS = [
    ("[YYYY.MM – YYYY.MM]", "CLOV 팀 프로젝트", "[맡은 역할]", "대인관계력"),
    ("[YYYY.MM – YYYY.MM]", "10번 과제 · 논문", "[맡은 역할]", "자기동기력"),
    ("[YYYY.MM – YYYY.MM]", "[세 번째 과제]", "[맡은 역할]", "자기조절력"),
]
ENTRANCES = [("story", "이야기"), ("numbers", "숫자"), ("work", "대표작"), ("experience", "경력"), ("documents", "이력서")]
STACK = [("Frontend", "[예: React]"), ("Backend", "[예: Java · Spring]"), ("DB", "[예: MySQL]"),
         ("Infra", "[예: Ubuntu · Nginx · Docker]"), ("Learning", "[예: Network · Security]")]


def tag(text):
    return f'<span style="font-size: 12px; font-weight: 500; color: {ACC};">{text}</span>'


def bars(n, last=0.55):
    rows = "".join(
        f'<span style="display: block; height: 9px; margin: 9px 0; border-radius: 2px; background: {BAR}; width: {int(last * 100) if i == n - 1 else 100}%;"></span>'
        for i in range(n))
    return f'<div aria-hidden="true">{rows}</div>'


def h2(title, sub=None):
    s = f'<p style="margin: 4px 0 0; font-size: 14px; line-height: 1.5; color: {MUTED};">{sub}</p>' if sub else ""
    return f'<div style="margin-bottom: 16px;"><h2 style="margin: 0; font-size: 20px; font-weight: 600; letter-spacing: -0.01em; color: {INK};">{title}</h2>{s}</div>'


def kv(k, v, mobile):
    col = "72px" if mobile else "80px"
    return f"""
        <div style="display: grid; grid-template-columns: {col} minmax(0, 1fr); column-gap: 12px; padding: 10px 0; border-top: 1px solid {LINE};">
          <dt style="font-size: 13px; line-height: 22px; color: {MUTED};">{k}</dt>
          <dd style="margin: 0; font-size: 14px; line-height: 22px; color: {INK};">{v}</dd>
        </div>"""


def build(mobile):
    W = 390 if mobile else 1280
    pad = 20 if mobile else 48
    stack = "".join(
        f'<span style="display: grid; grid-template-columns: 68px 1fr; gap: 6px;"><span style="font-family: {MONO}; font-size: 12px; color: {MUTED};">{a}</span><span>{b}</span></span>'
        for a, b in STACK)
    facts = (kv("방향", "프론트엔드·백엔드·DB·배포를 경험했고, 네트워크·보안까지 관심 영역을 넓혀 가는 중", mobile)
             + kv("기술", f'<span style="display: flex; flex-direction: column; gap: 2px;">{stack}</span>', mobile)
             + kv("교육", "[학력 · 교육 과정 — 공개 범위 본인 결정]", mobile)
             + kv("연락", f'<a href="#contact" style="color: {ACC};">[공개 연락 수단 1개]</a>', mobile))

    if mobile:
        entr = "".join(
            f'<a href="#{h}" style="display: flex; align-items: center; justify-content: center; min-height: 44px; border: 1px solid {LINE}; border-radius: 8px; background: #FFFFFF; font-size: 14px; font-weight: 500; color: {INK}; text-decoration: none;">{t}</a>'
            for h, t in ENTRANCES)
        entrances = f'<nav aria-label="바로 가기" style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px;">{entr}</nav>'
    else:
        entr = "".join(
            f'<a href="#{h}" style="display: flex; align-items: center; justify-content: space-between; min-height: 40px; border-top: 1px solid {LINE}; font-size: 15px; font-weight: 500; color: {INK}; text-decoration: none;"><span>{t}</span><span style="color: {FAINT};">→</span></a>'
            for h, t in ENTRANCES)
        entrances = f'<nav aria-label="바로 가기" style="display: flex; flex-direction: column; border-bottom: 1px solid {LINE};">{entr}</nav>'

    intro = f"""
      <div style="display: flex; flex-direction: column; gap: 8px;">
        <span style="font-family: {MONO}; font-size: 12px; color: {MUTED};">myeongjundev.github.io/about</span>
        <h1 style="margin: 8px 0 0; font-size: {32 if mobile else 40}px; font-weight: 700; letter-spacing: -0.02em; line-height: 1.1; color: {INK};">김명준</h1>
        <p style="margin: 0; font-size: 15px; font-weight: 500; color: {MUTED};">신입 풀스택 개발자</p>
        <p style="margin: 12px 0 0; font-size: {19 if mobile else 21}px; font-weight: 600; line-height: 1.45; letter-spacing: -0.01em; color: {INK};">[한 줄 소개 — 본인 작성] …한 사람</p>
      </div>"""
    aside_inner = f"""{intro}
      {entrances}
      <dl style="margin: 0; display: flex; flex-direction: column;">{facts}
      </dl>"""

    # story
    date_w = "auto"
    stage_html = ""
    for i, (d, name, summ, abil) in enumerate(STAGES):
        link = ""
        if i == 0:
            link = f'<p style="margin: 0; font-size: 12px; color: {MUTED};">↔ 숫자 「출석일」과 짝지음</p>'
        stage_html += f"""
        <article style="display: flex; flex-direction: column; gap: 8px; padding: 24px 0; border-top: 1px solid {LINE};">
          <div style="display: flex; flex-wrap: wrap; align-items: baseline; gap: 4px 12px;">
            <span style="font-family: {MONO}; font-size: 13px; color: {INK};">{d}</span>
            <span style="font-size: 13px; font-weight: 600; color: {MUTED};">{i + 1} · {name}</span>
            <span style="flex-grow: 1;"></span>{tag('드러난 능력 · ' + abil)}
          </div>
          <p style="margin: 0; font-size: 17px; font-weight: 600; line-height: 1.5; color: {INK};">{summ}</p>
          <p style="margin: 4px 0 0; font-size: 12px; color: {FAINT};">본문 약 450자 · 날짜 있는 장면에서 시작 · 사실만</p>
          {bars(12 if mobile else 9)}{link}
        </article>"""
    story = f"""
      <section id="story">{h2('이야기', '요약줄만 읽어도 흐름이 보이도록 토막마다 날짜와 한 줄을 먼저 둡니다.')}
        <p style="margin: 0 0 8px; font-size: 17px; line-height: 1.65; color: {INK};">[첫 문장 — 본인 작성]</p>{stage_html}
        <p style="margin: 0; padding-top: 24px; border-top: 1px solid {LINE}; font-size: 17px; line-height: 1.65; color: {INK};">[마지막 문장 — 본인 작성]</p>
      </section>"""

    # numbers
    mcols = "1fr" if mobile else "repeat(3, minmax(0, 1fr))"
    mets = ""
    for label, src, paired in METRICS:
        pair = f'<span style="font-size: 12px; font-weight: 500; color: {ACC};">↔ 고난 토막과 짝</span>' if paired else ""
        mets += f"""
          <div style="display: flex; flex-direction: column; gap: 4px; padding: 16px 0 {12 if mobile else 0}px; border-top: 2px solid {INK};">
            <span style="font-size: 32px; font-weight: 600; letter-spacing: -0.02em; color: {INK};">[숫자]</span>
            <span style="font-size: 14px; color: {INK};">{label}</span>
            <span style="font-size: 12px; line-height: 1.5; color: {MUTED};">출처 · {src}<br>기준 · [YYYY.MM.DD] (13주 과정)</span>{pair}
          </div>"""
    numbers = f"""
      <section id="numbers">{h2('숫자', '13주 기록에서 옮긴 숫자입니다. 작은 숫자도 그대로 적습니다.')}
        <div style="display: grid; grid-template-columns: {mcols}; gap: {'8px' if mobile else '0 20px'};">{mets}
        </div>
      </section>"""

    # works
    wcols = "1fr" if mobile else "repeat(2, minmax(0, 1fr))"
    works = f"""
      <section id="work">{h2('대표작')}
        <div style="display: grid; grid-template-columns: {wcols}; gap: {'28px' if mobile else '20px'};">
          <div style="display: flex; flex-direction: column; gap: 8px; padding-top: 16px; border-top: 2px solid {INK};">
            <span style="font-family: {MONO}; font-size: 12px; color: {MUTED};">10번 과제 · 논문 · [YYYY.MM]</span>
            <p style="margin: 0; font-size: 17px; font-weight: 600; line-height: 1.45; color: {INK};">[논문 제목]</p>
            <p style="margin: 0; font-size: 14px; line-height: 1.65; color: {MUTED};">[문제] → [방법] → [결과] 한 줄 요약</p>
            <p style="margin: 4px 0 0; display: flex; flex-wrap: wrap; gap: 4px 16px; font-size: 14px;"><a href="#work" style="color: {ACC};">논문 읽기 (로그인 없이)</a><a href="#work" style="color: {ACC};">저장소</a></p>
          </div>
          <div style="display: flex; flex-direction: column; gap: 8px; padding-top: 16px; border-top: 2px dashed {FAINT};">
            <span style="font-family: {MONO}; font-size: 12px; color: {MUTED};">13번 과제 · 앱</span>
            <p style="margin: 0; font-size: 17px; font-weight: 600; color: {INK};">준비 중</p>
            <p style="margin: 0; font-size: 14px; line-height: 1.65; color: {MUTED};">13번 과제를 마친 뒤 채웁니다.<br>예정일 <span style="font-family: {MONO}; color: {INK};">[YYYY.MM.DD]</span></p>
          </div>
        </div>
      </section>"""

    # experience
    exp = ""
    for period, title, role, abil in EXPS:
        head = f"""
            <div style="display: flex; flex-wrap: wrap; align-items: baseline; gap: 4px 12px;">
              <span style="font-family: {MONO}; font-size: 12px; color: {MUTED};">{period}</span>
              <span style="flex-grow: 1;"></span>{tag(abil)}
            </div>"""
        exp += f"""
          <article style="display: flex; flex-direction: column; gap: 6px; padding: 20px 0; border-top: 1px solid {LINE};">{head}
            <p style="margin: 0; font-size: 17px; font-weight: 600; color: {INK};">{title}</p>
            <p style="margin: 0; font-size: 13px; color: {MUTED};">{role}</p>
            <dl style="margin: 6px 0 0; display: grid; grid-template-columns: 40px minmax(0, 1fr); gap: 6px 10px; font-size: 15px; line-height: 1.6;">
              <dt style="color: {MUTED}; font-size: 13px; line-height: 24px;">상황</dt><dd style="margin: 0; color: {INK};">[어떤 문제가 있었나]</dd>
              <dt style="color: {MUTED}; font-size: 13px; line-height: 24px;">행동</dt><dd style="margin: 0; color: {INK};">[내가 한 일]</dd>
              <dt style="color: {MUTED}; font-size: 13px; line-height: 24px;">결과</dt><dd style="margin: 0; color: {INK};">[결과 — 숫자로]</dd>
            </dl>
            <p style="margin: 4px 0 0; display: flex; flex-wrap: wrap; justify-content: space-between; gap: 4px 16px;">
              <span style="font-family: {MONO}; font-size: 12px; line-height: 22px; color: {MUTED};">[기술 스택]</span>
              <a href="#experience" style="font-size: 14px; color: {ACC};">확인 · 저장소</a>
            </p>
          </article>"""
    experience = f"""
      <section id="experience">{h2('경력·과제', '경력기술서와 같은 내용입니다. 과제마다 능력 · 상황 · 행동 · 결과.')}{exp}
      </section>"""

    docs = "".join(
        f'<a href="#documents" style="display: flex; justify-content: space-between; align-items: center; min-height: 52px; border-top: 1px solid {LINE}; font-size: 16px; color: {INK}; text-decoration: none;"><span>{name}</span><span style="font-size: 13px; color: {MUTED};">{fmt} ↓</span></a>'
        for name, fmt in [("이력서", "DOCX"), ("자기소개서", "DOCX"), ("경력기술서", "DOCX")])
    documents = f"""
      <section id="documents">{h2('이력서 · 문서', '로그인·비밀번호 없이 받습니다.')}
        <div style="display: flex; flex-direction: column; border-bottom: 1px solid {LINE};">{docs}</div>
      </section>
      <footer id="contact" style="display: flex; flex-direction: column; gap: 6px; padding-top: 24px; border-top: 2px solid {INK};">
        <p style="margin: 0; font-size: 16px; font-weight: 600; color: {INK};">김명준</p>
        <p style="margin: 0; font-size: 15px;"><a href="#contact" style="color: {ACC};">[공개 연락 수단 1개]</a></p>
        <p style="margin: 20px 0 0; font-size: 12px; line-height: 1.6; color: {MUTED};">새 기록을 넣으면 숫자와 문단 후보가 다시 만들어집니다 · 마지막 갱신 [YYYY.MM.DD]</p>
      </footer>"""

    main_inner = story + numbers + works + experience + documents

    if mobile:
        page = f"""<div id="page" style="width: {W}px; box-sizing: border-box; background: {BG}; color: {INK}; font-family: 'Geist', 'Noto Sans KR', sans-serif; padding: 40px {pad}px 56px; display: flex; flex-direction: column; gap: 56px;">
    <header style="display: flex; flex-direction: column; gap: 24px;">{aside_inner}
    </header>{main_inner}
  </div>"""
    else:
        page = f"""<div id="page" style="width: {W}px; box-sizing: border-box; background: {BG}; color: {INK}; font-family: 'Geist', 'Noto Sans KR', sans-serif; display: flex; justify-content: center;">
    <div style="width: 1120px; box-sizing: border-box; padding: 0 {pad}px; display: flex; gap: 72px;">
      <aside style="width: 360px; flex-shrink: 0; padding: 80px 0; display: flex; flex-direction: column; gap: 32px;">{aside_inner}
      </aside>
      <main style="flex-grow: 1; min-width: 0; padding: 80px 0; display: flex; flex-direction: column; gap: 72px;">{main_inner}
      </main>
    </div>
  </div>"""
    return W, page


FONTS = '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&amp;family=Geist+Mono:wght@400;500&amp;family=Noto+Sans+KR:wght@400;500;600;700&amp;display=swap">'
STYLE = """<style>
    body { margin: 0; word-break: keep-all; }
    a { text-decoration: underline; text-decoration-color: #D6D3D1; text-underline-offset: 3px; }
    a:hover { text-decoration-color: currentColor; }
    a:focus-visible { outline: 2px solid #1D4ED8; outline-offset: 3px; }
  </style>"""

heights = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}

for fname, mobile in [("TrustV2.dc.html", False), ("TrustV2Mobile.dc.html", True)]:
    W, page = build(mobile)
    H = heights.get(fname, 3600 if not mobile else 7000)
    # plain preview for measuring height
    (preview / fname.replace(".dc.html", ".html")).write_text(
        f"<!doctype html><html lang='ko'><head><meta charset='utf-8'>{FONTS}{STYLE}</head><body>{page.replace(ACC, '#1D4ED8')}</body></html>",
        encoding="utf-8")
    page_fixed = page.replace('id="page" style="', f'id="page" style="height: {H}px; ', 1)
    props = {
        "accent": {"editor": "color", "default": "#1D4ED8", "options": ["#1D4ED8", "#0F766E", "#1C1917"]},
        "$preview": {"width": W, "height": H},
    }
    props_attr = json.dumps(props, ensure_ascii=False).replace("&", "&amp;").replace("'", "&#39;")
    html = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
  {FONTS}
  {STYLE}
</helmet>
{page_fixed}
</x-dc>
<script data-dc-script data-props='{props_attr}'>
class Component extends DCLogic {{
  renderVals() {{
    return {{ accent: this.props.accent ?? '#1D4ED8' }};
  }}
}}
</script>
</body>
</html>
"""
    (root / fname).write_text(html, encoding="utf-8")
print("ok")
