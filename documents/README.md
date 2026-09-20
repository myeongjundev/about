# 문서 3종 빌드

`build.py`는 `content/approved.json`에서 이력서, 자기소개서, 경력기술서 DOCX를 만든다.
`render_docx.py`는 그 DOCX를 PDF와 페이지 이미지로 렌더링하고 쪽 수를 기록한다.

최종 문서는 승인 데이터의 `draft`가 `false`이고 필수 값이 모두 채워져야 생성한다.

```text
python documents/build.py
python documents/render_docx.py --output-dir documents/qa/latest --pdf-dir docs/files
```

내용과 레이아웃을 확인하기 위한 내부 초안은 공개 폴더가 아닌 `documents/out/`에 만든다.

```text
python documents/build.py --draft --output-dir documents/out
```

한 문서만 다시 만들 때는 `--only`를 사용한다.

```text
python documents/build.py --draft --only personal-statement --output-dir documents/out
```

## 문서를 고쳤으면 반드시 다시 렌더링한다

쪽이 몇 장인지, 마지막 쪽에 몇 줄만 남았는지는 실제로 렌더링해야 알 수 있다.
`render_docx.py`는 결과를 `documents/render-manifest.json`에 적고, 단위 테스트가 이 기록을
검사한다. 문서를 고치고 렌더링하지 않으면 본문 지문이 어긋나 테스트가 실패한다.

- 이력서와 자기소개서는 2쪽을 넘지 않는다
- 마지막 쪽은 앞쪽의 25%보다 많이 차 있어야 한다. 몇 줄만 남으면 덜 만든 문서로 보인다

렌더링에는 LibreOffice가 필요하다. PATH에 있으면 그대로 쓰고, 없으면 Docker 이미지를 만들어
그 안에서 실행한다. 이때 문서가 쓰는 맑은 고딕을 컨테이너에 연결해야 같은 모습이 나온다.
Windows에서는 자동으로 `C:\Windows\Fonts`를 연결하고, 다른 환경에서는 `T12_FONT_DIR`로
글꼴 폴더를 지정한다.

## 지면 설계

해외 이력서·경력기술서 관례를 따랐다.

- 한 열로만 짠다. 표로 본문을 배치하지 않는다. 채용 시스템이 표를 잘못 읽는 일이 있다
- 이름을 가장 크게 두고 문서 종류를 오른쪽에 작게 붙인다. 그 아래 한 줄에 직무와 확인 링크를 모은다
- 날짜는 줄 앞이 아니라 오른쪽 끝에 세운다
- 본문 10~10.5pt, 여백 0.7~0.75인치, A4
- 결과는 수치와 함께 적는다
