# 문서 3종 빌드

`build.py`는 `content/approved.json`에서 이력서, 자기소개서, 경력기술서 DOCX를 만든다.

최종 문서는 승인 데이터의 `draft`가 `false`이고 필수 값이 모두 채워져야 생성한다.

```text
python documents/build.py
```

내용과 레이아웃을 확인하기 위한 내부 초안은 공개 폴더가 아닌 `documents/out/`에 만든다.

```text
python documents/build.py --draft --output-dir documents/out
```

최종 문서는 생성 뒤 `render_docx.py`로 모든 페이지를 이미지로 렌더링하고 글자 잘림, 표 겹침,
페이지 나눔을 확인한다. 내부 초안은 제출하거나 `docs/files/`에 복사하지 않는다.
