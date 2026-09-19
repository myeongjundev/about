# about — 김명준 자기소개 사이트

> 처음 온 사람이 3분 안에 읽고 함께 일하고 싶어지는 공개 사이트와,
> 새 기록을 넣으면 사이트의 숫자와 문단 후보를 다시 만드는 장치.

SKT ALEPH 마지막 과제 A(12번)의 작업 저장소입니다.

## 현재 상태

**전체 재설계와 공통 기반 구현 완료, 본인 확인 대기 (2026-09-19)** — 승인 데이터에서 사이트와
문서 3종을 만들고, 기록 집계·반복 실행·릴리스 검사를 수행하는 구조를 구현했습니다. 실제 T12
원문과 학원 PC의 최신 비공개 입력, 본인이 직접 쓸 문장을 확보한 뒤 최종 공개합니다.

- 요구사항·통과 기준 정리: [`planning/REQUIREMENTS.md`](planning/REQUIREMENTS.md)
- 새 단일 기준 설계: [`planning/T12-MASTER-PLAN.md`](planning/T12-MASTER-PLAN.md)
- 이전 설계 초안: [`planning/DESIGN.md`](planning/DESIGN.md)
- 진행 기록: [`planning/STATUS.md`](planning/STATUS.md)

## 개발 검사

```text
python -m unittest device/test_device.py -v
python device/check_repeat.py
python device/build_site.py --draft
python device/validate_release.py --allow-draft
```

최종 승인 전에는 `--draft`와 `--allow-draft`를 제거한 빌드가 실패하는 것이 정상입니다.

## 예정 구조

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
