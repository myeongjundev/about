# 개발자 자기소개·이력서 사이트 조사

조사일: 2026-09-17 · 목적: 채용 담당자가 3분 안에 "누구인지, 무엇을 했는지, 왜 함께 일하고 싶은지"를
이해하는 사이트 구조를 찾는다.

## 1. 채용 담당자는 어떻게 보는가

| 자료 | 내용 |
|---|---|
| Ladders 시선 추적 연구(2018) | 첫 훑어보기는 평균 **7.4초**. 현재 직함·회사 → 이전 직함·회사 → 날짜(꾸준한 진행) → 학력 순으로 본다. 단순한 레이아웃, 분명한 섹션 제목, 굵은 제목, 성과 불릿이 잘 읽히고, 복잡한 배치·여백 부족·여러 단·긴 문장은 불리하다. F·E자 패턴으로 읽는다. |
| 한국 이력서 가이드(검색 요약) | 한 장당 짧은 시간(15초 안팎으로 소개됨) 안에 핵심 역량과 성과가 보여야 한다. 신입은 기술 스택·교육·프로젝트·GitHub·문제 해결이 중요하다. "무엇을 어떻게 개선했고 결과가 어땠는지"를 쓴다. |
| 주니어 포트폴리오 가이드(Codecademy 등) | 이름·이메일을 잘 보이게, 이력서 링크 또는 PDF 제공. 프로젝트는 3~5개를 깊게, 맡은 일·범위·결과·극복한 어려움과 "왜 그렇게 만들었는지"를 설명. 협업 프로젝트 1개 이상. 모바일에서 훑어보기 쉽게. 튜토리얼 클론은 빼기. |
| 한국어 이력서 모음(awesome-korean-resume) | 성과는 "A 과제 → B 방법 → C 결과"로. 1~2쪽. 신입은 실제 프로젝트·오픈소스·동아리 리더 경험. |

## 2. 유명 개발자 사이트 관찰

| 사이트 | 첫 화면 | 구성 순서 | 경력·작업 표기 | 눈여겨볼 점 |
|---|---|---|---|---|
| Brittany Chiang (brittanychiang.com) | 이름 · 직무("Frontend Engineer") · 한 문장("I build accessible, pixel-perfect experiences for the web.") · 섹션 이동 링크 · SNS 아이콘 | About → Experience → Projects → Writing | 기간 · 직함+회사 · 짧은 설명 · 기술 태그. "View Full Résumé"(PDF) 링크 | 한 페이지, 첫 화면에서 직무와 가치가 바로 보임 |
| Lee Robinson (leerob.com) | 이름 · 한두 문장 소개(무슨 일을 하는지) | 소개 → Notes → Blog | 경력을 소개 문장 속에 녹임, 글은 날짜와 함께 목록 | 매우 짧은 텍스트 중심, 이메일을 본문에 둠 |
| Josh W. Comeau (about 페이지) | 개인적·유쾌한 톤 | 시작 연도 → 경력 → 전환 → 지금 | "2007년부터" 같은 연도, 수강생 수 같은 숫자 | 고난 서사보다 "지금의 나"와 철학 중심 |
| Kent C. Dodds (about 페이지) | 사진 · "full time educator" | 출생·학업·경력 → 가치 3가지 → 발표 → 인정 → 개인 사실 | 연도와 자격(GDE, MVP), "100회 이상 발표" | 가치를 세 가지로 묶어 보여 줌 |
| swyx (about 페이지) | — | 금융 → 개발자 경험 → AI "돌아온 길" | 커뮤니티 규모 숫자 | 진로 전환을 "우회로"로 설명 |
| 이동욱 (jojoldu.github.io) | 이름 · 직무 · 요약 문단(연차·기술·서비스 규모 숫자) · 연락처 | About → Experience → Skills → Open Source → Education → 대외활동 | `YYYY.MM ~ YYYY.MM` · 서비스 규모 숫자 · 결정·개선·결과 불릿 | 첫 문단부터 숫자로 신뢰를 만든다 |
| 이현섭 (hyunseob.github.io/resume) | 이름 · "N년차 … 엔지니어" 소개 | Work → Other → Skills → Contact | 회사 → 역할 → 프로젝트 → 설명 → "무엇을 했나" 불릿 → 기술 스택 | 가로선으로 섹션을 분명히 나눔 |
| Jbee (jbee.io/about) | "Growth mindset Software Engineer" · 한/영 이력서 링크 | 커뮤니티 → 멘토링 → 발표 → 글 → 책 → 개인 관심 → 연락 | 이름+기간 `(18.06 - current)` | 이력서는 별도 링크, 소개 페이지는 활동 중심 |

## 3. 공통 패턴

1. **첫 화면 = 이름 + 직무 + 한 문장 + 연락/이력서 입구.** 스크롤 없이 "누구·무엇"이 보인다.
2. **한 페이지, 한 칼럼, 분명한 섹션 제목.** 이동 링크로 원하는 곳에 바로 간다.
3. **기간은 `YYYY.MM` 형식, 항목마다 문제·행동·결과와 숫자.** 한국 이력서는 숫자를 첫 문단부터 쓴다.
4. **이력서는 따로 받을 수 있게(PDF/문서 링크).**
5. **유명 개발자는 회사 이름이 신뢰를 대신한다.** 신입은 그 자리를 **날짜 있는 장면 + 출처 있는 숫자 + 대표작**으로 채워야 한다.
6. 고난 서사를 길게 쓰는 사례는 드물다. 쓰더라도 짧고, "지금"과 "배운 방식"으로 끝난다.

## 4. 우리 사이트에 적용할 것 (3분 시간표)

| 시간 | 채용 담당자가 보는 것 | 사이트 자리 |
|---|---|---|
| 0~10초 | 이름, 무엇을 하는 사람인지, 연락·이력서 | 첫 화면: 김명준 · 직무 표기 · "…한 사람" 한 줄 소개 · 입구 4개(이야기·숫자·대표작·이력서) · 연락 수단 1개 |
| 10~60초 | 이야기의 뼈대 | 세 토막마다 **날짜 + 굵은 한 줄 요약**을 먼저 두어, 본문을 다 읽지 않아도 고난 → 다시 일어난 날 → 지금이 보이게 |
| 1~2분 | 믿을 근거 | 숫자 카드 3~4개(숫자 · 무엇을 셌나 · 출처 · 기준일), 대표작 2칸(CLOV · 10번 논문) |
| 2~3분 | 깊이 | 이야기 본문 1,500자, 과제 타임라인(`YYYY.MM` · 능력 · 상황·행동·결과), 문서 받기 |

설계에 반영할 원칙:

- 한 칼럼, 모바일 우선, 섹션 제목과 굵은 요약줄, 긴 문장 쪼개기.
- 1,500자 본문은 끝까지 읽으면 몇 분이 걸리므로, **토막별 요약줄만 읽어도 이야기가 이해되게** 한다.
- 경력기술서·타임라인은 한국 관례대로 `YYYY.MM`과 "과제 → 방법 → 결과 + 숫자"로 쓴다(예: 39일, 리뷰 72건).
- 튜토리얼성 결과물보다 협업(CLOV)과 연구(10번 논문)처럼 **왜 그렇게 했는지** 설명할 수 있는 작업을 앞에 둔다.
- 이력서 문서는 첫 화면에서 한 번에 받을 수 있게 한다.

## 출처

- [HR Dive — Eye tracking study shows recruiters look at resumes for 7 seconds](https://www.hrdive.com/news/eye-tracking-study-shows-recruiters-look-at-resumes-for-7-seconds/541582/)
- [Ladders — Eye-Tracking Study 2018 (PDF)](https://www.theladders.com/static/images/basicSite/pdfs/TheLadders-EyeTracking-StudyC2.pdf)
- [Codecademy — Junior Developer Portfolio: Examples + Must-Haves](https://www.codecademy.com/resources/blog/what-to-include-in-a-junior-developer-portfolio)
- [점핏 — 개발자 이력서 항목별 작성팁 총 정리](https://jumpit.saramin.co.kr/contents/450)
- [9j/awesome-korean-resume](https://github.com/9j/awesome-korean-resume)
- [Brittany Chiang](https://brittanychiang.com) · [Lee Robinson](https://leerob.com) · [Josh W. Comeau — About](https://www.joshwcomeau.com/about-josh/) · [Kent C. Dodds — About](https://kentcdodds.com/about) · [swyx — About](https://www.swyx.io/about)
- [이동욱](https://jojoldu.github.io/) · [이현섭](https://hyunseob.github.io/resume/) · [Jbee — About](https://jbee.io/about)
