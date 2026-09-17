# 진행 기록

## 2026-09-17 — 저장소 생성과 설계 준비

- `myeongjundev/about`을 public으로 만들었다. 사이트는 GitHub Pages(`https://myeongjundev.github.io/about/`)로 공개할 예정이다.
  기존 포트폴리오 `myeongjundev.github.io`는 그대로 둔다.
- 동기에게 받은 과제 안내 텍스트로 요구사항과 통과 기준을 정리했다(`planning/REQUIREMENTS.md`).
  원문 파일은 저장소에 넣지 않는다.
- **원문 텍스트에 붙어 있던 리추얼 기록(27일, 동료 칭찬·감사)은 동기의 기록이다. 쓰지 않는다.**
  본인 과제 화면이 열리면 본인 리추얼 JSON을 받는다.
- 설계 초안 작성(`planning/DESIGN.md`): 사이트 구조, 이야기 뼈대 후보, 되돌릴 각색 목록, 숫자 칸 후보, 장치·문서 설계.
- 재사용할 자료: 9번 서사 문서(`t09-self-introduction/drafts/T09-13-서사문서-본문.md`), 공개 도구
  `ritual-strength-agent`, 11번 사실 원장(`t11-autobiographical-novel/planning/FACT-LEDGER.md`), 10번 공개 저장소
  `explainsoc-research`.

## 2026-09-17 — 사이트 조사와 디자인 방향

- 개발자 자기소개·이력서 사이트 조사(`planning/RESEARCH.md`).
- Claude Design 프롬프트 정리(`planning/DESIGN-PROMPT.md`). 첫 시안(카드형)은 "AI가 만든 결과물 같다"는 이유로 채택하지 않았다.
- 해외 개발자 사이트 6곳의 색·글꼴·구조를 브라우저에서 실측했다. 이를 바탕으로 A·B·C 세 방향과 국내·해외 겸용 신뢰형 D를 만들었다.
- D를 T12 채점 조건에 맞춰 고친 **D2**(데스크톱·모바일)를 채택했다. 결정 내용과 미정 사항은 `planning/DESIGN-DECISION.md`에 적었다.
  - 시안 캔버스: https://claude.ai/artifact/CbHUdWUnN9yoNSuhcTfwPD
  - 시안 생성 스크립트 사본: `planning/design-canvas/gen_d2.py`

## 다음 작업 (집에서 이어서)

1. `docs/`에 D2 구조로 정적 사이트 뼈대(`index.html`, `styles.css`, `script.js`, `data/site.json`)를 만든다. 자리표시로 둔다.
2. 카드 1: 이야기 본편 초안(1,500자 안팎, 사실만)과 세 능력 장면 표시 → 본인 확인.
   - 요약줄 후보와 능력 짝짓기는 `DESIGN-DECISION.md` 6절.
3. GitHub Pages 켜기(main `/docs`) → 시크릿 창 확인.
4. 본인 과제 화면이 열리면 원문을 다시 대조한다. 리추얼 JSON·출석·제출 현황을 받는다(`DESIGN.md` 8절).
