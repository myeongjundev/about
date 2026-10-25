# about — 김명준 자기소개 사이트

> 처음 온 사람이 3분 안에 읽고 함께 일하고 싶어지는 공개 사이트와,
> 새 기록을 넣으면 사이트의 숫자와 문단 후보를 다시 만드는 장치.

SKT ALEPH 마지막 과제 A(12번)의 작업 저장소입니다.

## 현재 상태

**제출 완료 (2026-09-21, 제출한 저장소 상태 `a413189`)** — 승인 데이터에서 반응형 포트폴리오와
DOCX 문서 3종을 생성했고, 기록 집계·반복 실행·접근성·외부 링크·릴리스 검사를 통과했습니다.
`docs/`에는 GitHub Pages용 사이트와 내려받을 문서가 있으며, 제출용 ZIP은 로컬에서 재현할 수 있습니다.
제출한 것과 양식 문안은 [`planning/SUBMISSION-2026-09-21.md`](planning/SUBMISSION-2026-09-21.md)에 있습니다.

제출 뒤에도 공개 프로젝트의 화면과 검증 근거를 갱신합니다. 대표작은 NetProof, ExplainSOC,
10번 연구, CLOV, 7번 다이어리 인증입니다. 2026-10-25에 사용자의 요청으로
[NetProof](https://netproof-vert.vercel.app/)를 추가했습니다. 합성 구성에서 닿는 서비스 15개가
1개로 줄고 수복 기록에 막힘 14·아직 닿음 1이 남는 흐름을 소개하며, 실제 장비 대조와
다른 사용자 확인은 아직 없다고 구분합니다. 근거는 [NetProof 검토 기록](https://github.com/myeongjundev/netproof/blob/main/docs/final-review-2026-10-25.md)입니다.

- 공개 사이트: https://myeongjundev.github.io/about/

- 요구사항·통과 기준 정리: [`planning/REQUIREMENTS.md`](planning/REQUIREMENTS.md)
- 새 단일 기준 설계: [`planning/T12-MASTER-PLAN.md`](planning/T12-MASTER-PLAN.md)
- 제출 후 독립 리뷰: [`planning/T12-POST-SUBMISSION-REVIEW.md`](planning/T12-POST-SUBMISSION-REVIEW.md)
- 이전 설계 초안: [`planning/DESIGN.md`](planning/DESIGN.md)
- 진행 기록: [`planning/STATUS.md`](planning/STATUS.md)

## 개발 검사

```text
python -m unittest device/test_device.py -v
python device/check_repeat.py
python documents/build.py
python device/build_site.py
python device/validate_release.py --check-urls
python release/build_release.py
```

승인 데이터가 다시 초안 상태가 되거나 문서가 누락되면 최종 빌드와 릴리스 생성이 실패합니다.

## 저장소 구조

```text
docs/              공개 사이트 (GitHub Pages: main 브랜치 /docs)
documents/         이력서·자기소개서·경력기술서 원고와 빌드 결과
device/            계속 새로 쓰는 장치 (실행 소스·README·예시 입력)
planning/          요구사항·설계·진행 기록
private/inputs/    실제 입력 기록 (Git에 올리지 않음)
```

## 개인정보 경계

이 저장소는 사이트 공개를 위해 **public**입니다.

- 실제 리추얼 JSON·출석·제출 현황 원본은 `private/inputs/`에 두고 Git에 올리지 않습니다.
- 사이트·문서·장치 결과에는 본인 이름과 공개하기로 정한 연락 수단 하나만 남기고,
  다른 사람의 실명·연락처와 비밀번호·토큰·API 키는 넣지 않습니다.
- 과제 원문 파일과 11번 소설 원고는 이 저장소에 넣지 않습니다.
