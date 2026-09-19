# T12 기록 갱신 장치

이 장치는 리추얼·출석·제출 기록을 읽어 공개할 숫자와 사람이 검토할 문장 후보를 만든다.
외부 API와 생성형 AI를 사용하지 않으며 Python 3.12 표준 라이브러리만 필요하다.

## 입력 파일

입력 폴더에는 다음 세 파일이 있어야 한다.

- `ritual.json`: `student`, `days[].date`, `days[].open`, `days[].close`
- `attendance.json`: `sessions[].date`, `sessions[].status`
- `submissions.csv`: `id,due_at,submitted_at,status`

출석 상태는 `present`, `late`, `absent` 중 하나다. 제출 상태가 `not_required`인 행은 분모에서
제외한다. 날짜와 시간은 ISO 8601 형식으로 적는다.

## 실행

저장소 루트에서 실행한다.

```text
python device/refresh.py device/sample-inputs device/out
```

결과 파일은 다음과 같다.

- `numbers.json`: 사이트에 옮길 집계값과 출처
- `candidates.json`: 능력별 문장 후보와 근거 ID
- `candidates.md`: 사람이 읽을 후보 보고서

문장 후보는 자동으로 사이트에 들어가지 않는다. 내용을 읽고 공개 범위를 확인한 뒤
`content/approved.json`에 직접 옮겨야 한다.

집계 숫자는 먼저 미리보기 파일에 반영해 확인한다.

```text
python device/apply_numbers.py
```

`device/out/approved.preview.json`의 값과 기준일을 확인한 뒤에만 다음 명령으로 승인 데이터에
반영한다.

```text
python device/apply_numbers.py --in-place
```

## 반복 실행 검사

```text
python device/check_repeat.py
```

새 임시 폴더 두 곳에서 같은 합성 입력을 실행하고 출력 SHA-256을 비교한다. `expected/`의 고정
기대 결과와도 같아야 성공한다.

## 사이트 빌드와 릴리스 검사

승인 전 미리보기는 다음 명령으로 만든다.

```text
python device/build_site.py --draft
python device/validate_release.py --allow-draft
```

최종 승인 뒤에는 `--draft`와 `--allow-draft`를 제거한다. 미확정 값, 없는 문서, 작업 표시가
하나라도 남아 있으면 실패한다.

## 실제 기록 사용

실제 파일은 `private/inputs/`에 두며 Git과 제출 ZIP에 포함하지 않는다.

```text
python device/refresh.py private/inputs device/out
```

오류가 발생하면 필수 파일, JSON 배열, 날짜 형식, CSV 열 이름을 먼저 확인한다. 알 수 없는
형식을 0건으로 처리하지 않고 오류로 중단하도록 만들었다.
