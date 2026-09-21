# 승인 콘텐츠 필드

`approved.json`은 공개 사이트와 문서 3종이 함께 사용하는 공개 정보 원본이다. 비공개 입력의
전체 문장과 다른 사람의 이름은 넣지 않는다.

## 값의 상태

- 문자열이나 객체: 본인이 공개를 승인한 값
- `null`: 본인 확인이 필요해 아직 공개할 수 없는 값
- `draft: true`: 최종 공개 검사를 통과할 수 없는 작업 상태

`build_site.py --draft`는 `null`을 “확정 필요”로 표시한다. `--draft` 없이 실행하면 필수 값이
비어 있을 때 실패한다.

## 사람이 직접 확정할 필드

- `profile.tagline`
- `profile.contact`
- `story.firstSentence`
- `story.lastSentence`
- `story.segments[*].statementTitle`
- `numbers[submissions]`
- `experience[third-project]`

대표작에는 공개가 끝난 결과물과, 과제가 요구하는 13번 앱의 예정 자리(`status: planned`)를
둔다. 예정 자리에는 `plannedDate`가 있어야 하고, 13번을 마치면 `published`로 바꾸고 공개
링크와 검증 가능한 결과를 채운다(BRA-C06).

## 문서에만 쓰는 필드

사이트에는 보이지 않고 문서 3종에서만 쓰는 값이다.

- `profile.site`: 공개 사이트 주소. 문서 머리글의 확인 링크에 들어간다
- `profile.highlights`: 이력서 맨 앞 핵심 역량. 다른 필드에 이미 있는 확인된 수치만 다시 쓴다
- `profile.education[*]`: 교육과 학력. 최근 항목을 먼저 둔다
- `experience[*].scope`: 그 프로젝트에서 본인이 직접 맡은 범위. 역할보다 구체적으로 적는다
- `experience[*].rationale`: 그 상황에서 왜 그렇게 하기로 했는지. 경력기술서의 `판단` 줄이 된다.
  대표작 카드가 있는 항목은 `works[*].caseStudy.decision`과 같은 문장을 쓴다
- `documents[*].pdfHref`: 같은 문서의 PDF 경로. `render_docx.py`가 만든다

## 숫자 필드

모든 숫자는 다음 필드를 가진다.

- `value`: 화면에 보일 값과 단위
- `label`: 무엇을 셌는지
- `source`: 출석 기록, 리추얼 기록, 제출 현황 중 하나
- `asOf`: 집계 기준일
- `denominator`: 분모에 포함한 범위
- `linkedSegment`: 이야기와 연결할 때 해당 장면 ID

## 링크 필드

최종 사이트의 모든 외부 링크는 로그인하지 않은 새 브라우저에서 열려야 한다. 로그인 화면으로
이어지는 서비스 링크는 승인 데이터에 넣지 않는다.
