from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock
from urllib.parse import urlparse
from xml.etree import ElementTree


BASE = Path(__file__).resolve().parent
REPO = BASE.parent


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


refresh_module = load_module("t12_refresh", BASE / "refresh.py")
site_module = load_module("t12_build_site", BASE / "build_site.py")
validation_module = load_module("t12_validate_release", BASE / "validate_release.py")
apply_module = load_module("t12_apply_numbers", BASE / "apply_numbers.py")
release_module = load_module("t12_build_release", REPO / "release" / "build_release.py")


class RefreshTests(unittest.TestCase):
    def test_sample_matches_expected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            refresh_module.refresh(BASE / "sample-inputs", output)
            for name in ("numbers.json", "candidates.json", "candidates.md"):
                self.assertEqual(
                    (output / name).read_bytes(),
                    (BASE / "expected" / name).read_bytes(),
                    name,
                )

    def test_missing_input_fails(self) -> None:
        with tempfile.TemporaryDirectory() as input_temp, tempfile.TemporaryDirectory() as output_temp:
            with self.assertRaises(ValueError):
                refresh_module.refresh(Path(input_temp), Path(output_temp))


WEB_DOCUMENTS = (
        "resume.html",
        "personal-statement.html",
        "career-description.html",
        "resume-en.html",
        "personal-statement-en.html",
        "career-description-en.html",
    )


def copy_published_documents(output_dir: Path) -> None:
    """사이트는 문서 파일과 웹 문서가 실제로 있어야 만들어진다. 임시 폴더에 둘 다 옮긴다."""
    shutil.copytree(REPO / "docs" / "files", output_dir / "files")
    for page in WEB_DOCUMENTS:
        shutil.copy2(REPO / "docs" / page, output_dir / page)


class SiteTests(unittest.TestCase):
    def test_draft_site_contains_known_story_without_login_service(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "index.html"
            site_module.build(
                REPO / "content" / "approved.json",
                output,
                BASE / "templates" / "page.html.tpl",
                True,
            )
            content = output.read_text(encoding="utf-8")
            self.assertIn("2024년 12월 5일", content)
            self.assertIn("CLOV 팀 프로젝트", content)
            self.assertIn("2,830,743건", content)
            self.assertIn("CLOV 추억 피드 화면", content)
            self.assertIn("↔ 숫자 · 「제출한 과제 / 현재 제출 대상 과제」", content)
            self.assertIn("↔ 이야기 · 「더 나아진 지금」", content)
            self.assertNotIn("↔ 이야기 now", content)
            self.assertNotIn("↔ 이야기 setback", content)
            self.assertNotIn("clovlabcalss.store", content)

    def test_final_site_rejects_draft_content(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            content = json.loads(
                (REPO / "content" / "approved.json").read_text(encoding="utf-8")
            )
            content["draft"] = True
            content_path = Path(temp) / "draft.json"
            content_path.write_text(
                json.dumps(content, ensure_ascii=False), encoding="utf-8"
            )
            with self.assertRaises(ValueError):
                site_module.build(
                    content_path,
                    Path(temp) / "index.html",
                    BASE / "templates" / "page.html.tpl",
                    False,
                )

    def test_final_site_builds_without_draft_markers(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output_dir = Path(temp)
            copy_published_documents(output_dir)
            output = output_dir / "index.html"
            site_module.build(
                REPO / "content" / "approved.json",
                output,
                BASE / "templates" / "page.html.tpl",
                False,
            )
            content = output.read_text(encoding="utf-8")
            self.assertNotIn("data-draft=", content)
            self.assertNotIn("작업 중인 미리보기", content)
            self.assertIn('href="files/resume-kim-myeongjun.docx"', content)
            # 워드가 없는 사람을 위해 같은 문서를 PDF로도 둔다.
            # 한국어 문서 셋과 영문 문서 셋
            self.assertEqual(content.count('class="doc-card"'), 6)
            self.assertEqual(content.count('class="doc-card" lang="en"'), 3)
            # 문서는 웹 페이지로도 읽는다. 웹 페이지와 DOCX는 documents/build.py가 같은 순서로 만든다.
            for page in WEB_DOCUMENTS:
                self.assertIn(f'href="{page}"', content)
            for name in (
                "resume-kim-myeongjun",
                "personal-statement-kim-myeongjun",
                "career-description-kim-myeongjun",
            ):
                self.assertIn(f'href="files/{name}.pdf"', content)
            # 일하는 방식은 단추 위젯 대신 세 줄 목록이다. 각 줄에 근거 작업이 붙는다.
            self.assertNotIn("data-craft", content)
            self.assertEqual(content.count('class="how-step"'), 3)
            self.assertEqual(content.count('class="how-proof"'), 3)
            self.assertNotIn('aria-label="색상 테마 바꾸기"', content)
            self.assertNotIn("fonts.googleapis.com", content)
            self.assertNotIn("fonts.gstatic.com", content)
            self.assertNotIn("raw.githubusercontent.com", content)
            self.assertNotIn("myeongjundev.github.io/assets", content)
            self.assertIn('aria-label="섹션 바로가기"', content)
            self.assertGreater(
                content.index('class="entrances entrances-rail"'),
                content.index('</main>'),
            )

    def test_both_section_navigations_list_the_same_five_sections(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output_dir = Path(temp)
            copy_published_documents(output_dir)
            output = output_dir / "index.html"
            site_module.build(
                REPO / "content" / "approved.json",
                output,
                BASE / "templates" / "page.html.tpl",
                False,
            )
            content = output.read_text(encoding="utf-8")
            self.assertEqual(content.count('class="entrances-head"'), 2)
            self.assertEqual(content.count("<span>바로 가기</span>"), 2)
            self.assertEqual(content.count('class="entrance-indicator"'), 2)
            # ol 안에는 li만 올 수 있다. 표시 요소는 목록 밖에 둔다.
            import re as _re

            for block in _re.findall(r"<ol>.*?</ol>", content, _re.S):
                self.assertNotIn("<span", block.split("<li>")[0])
            self.assertEqual(content.count('class="nav-index mono"'), 10)
            self.assertEqual(content.count('class="entrance-copy"'), 10)
            for anchor in ("story", "numbers", "work", "experience", "documents"):
                self.assertEqual(content.count(f'href="#{anchor}"'), 2)

            styles = (REPO / "docs" / "styles.css").read_text(encoding="utf-8")
            mobile = styles[styles.index("@media (max-width: 880px)") :]
            side_rule = mobile[mobile.index("  .side {") : mobile.index("  .side {") + 420]
            self.assertIn("backdrop-filter: none", side_rule)
            # 레일도 .entrances라서, 하단 고정 바 규칙보다 뒤에서 접어야 한다.
            self.assertIn(".entrances.entrances-rail { display: none; }", mobile)
            self.assertGreater(
                mobile.index(".entrances.entrances-rail { display: none; }"),
                mobile.index("  .entrances {"),
            )

    def test_project_sections_exist_without_decorative_card_stack(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output_dir = Path(temp)
            copy_published_documents(output_dir)
            output = output_dir / "index.html"
            site_module.build(
                REPO / "content" / "approved.json",
                output,
                BASE / "templates" / "page.html.tpl",
                False,
            )
            content = output.read_text(encoding="utf-8")
            # 왼쪽에 쌓이던 SELECTED BUILDS 카드 더미와 영문 장식 문구는 뺐다(2026-09-25).
            for decoration in ("SELECTED BUILDS", "build-card", "LET'S BUILD", "CASE NOTES", "PORTFOLIO 2026", 'class="avatar"'):
                self.assertNotIn(decoration, content)
            # 공개된 대표작과 경력은 모두 제자리(id)가 있다.
            approved = json.loads((REPO / "content" / "approved.json").read_text(encoding="utf-8"))
            for item in approved["works"]:
                if item.get("status") == "published":
                    self.assertIn(f'id="work-{item["id"]}"', content)
            for item in approved["experience"]:
                self.assertIn(f'id="experience-{item["id"]}"', content)
            # 대표작은 ExplainSOC·10번·CLOV·7번 인증 넷이고, 5번 AI 인계는 경력으로 내려갔다.
            self.assertIn('id="work-t07-auth"', content)
            self.assertNotIn('id="work-t05-ai-handoff"', content)
            self.assertLess(content.index('id="work-t13-app"'), content.index('id="work-t10-paper"'))
            # 대표작마다 카드 겉면에 핵심 판단 한 줄이 있다.
            self.assertEqual(content.count('class="work-decision"'), 4)
            # 첫 화면과 맨 아래에 이력서 PDF(주)와 GitHub(보조)가 있다. 없는 연락처는 만들지 않는다.
            self.assertEqual(content.count('class="cta-primary" href="resume.html"'), 2)
            self.assertEqual(content.count('class="cta-text" href="resume-en.html" lang="en"'), 2)
            self.assertEqual(content.count('class="cta-secondary" href="https://github.com/myeongjundev"'), 2)
            self.assertNotIn("mailto:", content)
            self.assertIn('id="work-t13-app"', content)
            self.assertIn('id="experience-third-project"', content)
            self.assertEqual(content.count('class="work-case"'), 4)
            self.assertEqual(content.count('class="case-step"'), 16)
            self.assertIn("문제부터 검증까지 보기", content)


    def test_share_preview_image_exists_and_matches_declared_size(self) -> None:
        # 공유 미리보기는 링크를 붙여 보기 전에는 빠진 걸 모른다. 여기서 잡는다.
        import re as _re4

        page = (REPO / "docs" / "index.html").read_text(encoding="utf-8")
        found = _re4.search(r'property="og:image" content="([^"]+)"', page)
        self.assertIsNotNone(found, "og:image가 없다")
        url = found.group(1)
        self.assertTrue(url.startswith("https://"), "og:image는 절대 주소여야 한다")
        self.assertIn('content="summary_large_image"', page)

        name = url.rsplit("/", 1)[-1]
        card = REPO / "docs" / "assets" / name
        self.assertTrue(card.exists(), f"{name}이 없다")
        # 링크를 읽어 가는 쪽 가운데 WebP를 못 다루는 데가 있다.
        self.assertEqual(card.suffix, ".png")

        head = card.read_bytes()[:24]
        self.assertEqual(head[:8], bytes.fromhex("89504e470d0a1a0a"), "PNG가 아니다")
        width = int.from_bytes(head[16:20], "big")
        height = int.from_bytes(head[20:24], "big")
        self.assertEqual((width, height), (1200, 630))
        for axis, value in (("width", width), ("height", height)):
            self.assertIn(f'property="og:image:{axis}" content="{value}"', page)


class ApplyNumbersTests(unittest.TestCase):
    def test_applies_only_metric_fields_and_updated_date(self) -> None:
        content = json.loads((REPO / "content" / "approved.json").read_text(encoding="utf-8"))
        numbers = json.loads((BASE / "expected" / "numbers.json").read_text(encoding="utf-8"))
        story_before = json.dumps(content["story"], ensure_ascii=False, sort_keys=True)
        result = apply_module.apply_numbers(content, numbers)
        by_id = {item["id"]: item for item in result["numbers"]}
        self.assertEqual(by_id["attendance"]["value"], "3 / 3일")
        self.assertEqual(by_id["submissions"]["value"], "2 / 3건")
        self.assertEqual(result["updatedAt"], "2026-09-03")
        self.assertEqual(
            json.dumps(result["story"], ensure_ascii=False, sort_keys=True), story_before
        )


class ValidationTests(unittest.TestCase):
    def test_story_meets_length_and_tagline_rules(self) -> None:
        data = json.loads((REPO / "content" / "approved.json").read_text(encoding="utf-8"))
        self.assertEqual(validation_module.content_quality(data), [])

    def test_site_assets_are_declared_and_present(self) -> None:
        parser = validation_module.LinkParser()
        parser.feed((REPO / "docs" / "index.html").read_text(encoding="utf-8"))
        asset_paths = [urlparse(href).path for href in parser.assets]
        self.assertIn("styles.css", asset_paths)
        self.assertIn("favicon.svg", asset_paths)
        self.assertIn("app.js", asset_paths)
        self.assertEqual(parser.images_without_alt, [])
        for href in parser.assets:
            if not href.startswith(("http://", "https://", "data:")):
                self.assertTrue((REPO / "docs" / urlparse(href).path).is_file(), href)

    def test_external_url_check_uses_get_and_reads_body(self) -> None:
        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self, size: int) -> bytes:
                self.read_size = size
                return b"<"

        response = Response()
        with mock.patch.object(validation_module.urllib.request, "urlopen", return_value=response) as open_url:
            self.assertIsNone(validation_module.check_url("https://example.com"))
        request = open_url.call_args.args[0]
        self.assertEqual(request.get_method(), "GET")
        self.assertEqual(response.read_size, 1)

    def test_undersized_font_declarations_are_rejected(self) -> None:
        css = ".meta { font-size: 11px; }\n.badge { font: 600 9px monospace; }"
        problems = validation_module.undersized_font_declarations(css)
        self.assertEqual(len(problems), 2)
        self.assertTrue(all("12px 미만 글자" in problem for problem in problems))

    def test_visible_internal_story_id_is_rejected(self) -> None:
        data = json.loads((REPO / "content" / "approved.json").read_text(encoding="utf-8"))
        problems = validation_module.exposed_internal_story_ids(
            "<p>↔ 이야기 now</p>", data
        )
        self.assertEqual(problems, ["내부 id 노출: now"])

    def test_external_hosted_image_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            shutil.copytree(REPO / "content", repo / "content")
            shutil.copytree(REPO / "docs", repo / "docs")
            shutil.copytree(REPO / "device", repo / "device")
            shutil.copytree(REPO / "submission", repo / "submission")
            site = (repo / "docs" / "index.html").read_text(encoding="utf-8")
            # 파일 이름을 적어 두지 않는다. 그림 형식을 바꾸면 조용히 어긋난다.
            import re as _re3

            first = _re3.search(r'src="(assets/[^"]+)"', site)
            self.assertIsNotNone(first, "사이트에 그림이 하나도 없다")
            outside = f"https://example.com/{first.group(1).split('/')[-1]}"
            site = site.replace(f'src="{first.group(1)}"', f'src="{outside}"', 1)
            (repo / "docs" / "index.html").write_text(site, encoding="utf-8")
            problems = validation_module.validate(repo, False, False)
            self.assertIn(f"외부 호스트 이미지: {outside}", problems)

    def test_current_content_passes_structural_validation(self) -> None:
        self.assertEqual(validation_module.validate(REPO, True, False), [])

    def test_current_content_passes_release_validation(self) -> None:
        self.assertEqual(validation_module.validate(REPO, False, False), [])


class DocumentTests(unittest.TestCase):
    def test_generated_documents_use_a4_and_fit_tables_within_body(self) -> None:
        namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        width_key = f"{{{namespace['w']}}}w"
        for name in (
            "resume-kim-myeongjun.docx",
            "personal-statement-kim-myeongjun.docx",
            "career-description-kim-myeongjun.docx",
            "resume-kim-myeongjun-en.docx",
            "personal-statement-kim-myeongjun-en.docx",
            "career-description-kim-myeongjun-en.docx",
        ):
            with self.subTest(name=name), zipfile.ZipFile(REPO / "docs" / "files" / name) as archive:
                root = ElementTree.fromstring(archive.read("word/document.xml"))
                page_sizes = root.findall(".//w:sectPr/w:pgSz", namespace)
                self.assertTrue(page_sizes)
                for page_size in page_sizes:
                    self.assertAlmostEqual(int(page_size.attrib[width_key]), 11906, delta=1)
                    self.assertAlmostEqual(int(page_size.attrib[f"{{{namespace['w']}}}h"]), 16838, delta=1)
                for grid in root.findall(".//w:tblGrid", namespace):
                    table_width = sum(
                        int(column.attrib[width_key])
                        for column in grid.findall("w:gridCol", namespace)
                    )
                    self.assertLessEqual(table_width, 9360)

    def test_render_manifest_matches_documents_and_has_no_stray_page(self) -> None:
        """렌더 결과 기록을 검사한다. 쪽 수와 마지막 쪽 채움은 눈으로만 알 수 있던 값이다."""
        import hashlib

        manifest = json.loads(
            (REPO / "documents" / "render-manifest.json").read_text(encoding="utf-8")
        )
        # 경력기술서는 수업 실습까지 일곱 항목이 되면서 4쪽이 됐다. 판단 줄은 경력기술서에만
        # 나오므로 항목을 빼는 대신 한도를 올렸다(2026-09-21).
        limits = {
            "resume-kim-myeongjun": 2,
            "personal-statement-kim-myeongjun": 2,
            "career-description-kim-myeongjun": 4,
            # 영문 이력서도 한국어 이력서처럼 두 쪽을 넘기지 않는다.
            "resume-kim-myeongjun-en": 2,
            # 영문 자기소개서는 같은 내용이 한 쪽을 넘어 두 쪽까지 둔다. 영문 경력기술서는 7번 과제가
            # 들어가며 5쪽이 됐다. 판단 줄을 줄이는 대신 한도를 올렸다(2026-09-25).
            "personal-statement-kim-myeongjun-en": 2,
            "career-description-kim-myeongjun-en": 5,
        }
        for name, info in manifest.items():
            with self.subTest(name=name):
                source = REPO / "docs" / "files" / f"{name}.docx"
                with zipfile.ZipFile(source) as archive:
                    digest = hashlib.sha256(archive.read("word/document.xml")).hexdigest()[:16]
                # 문서를 고치고 다시 렌더링하지 않으면 여기서 걸린다.
                self.assertEqual(info["sourceDigest"], digest, "문서를 다시 렌더링해야 합니다")
                self.assertLessEqual(info["pages"], limits.get(name, 3))
                # 마지막 쪽에 몇 줄만 남으면 덜 만든 문서로 보인다.
                self.assertGreater(info["lastPageFill"], 0.25)


class ReleaseTests(unittest.TestCase):
    def test_release_allowlist_contains_full_device_and_root_readme(self) -> None:
        targets = {str(target) for _, target in release_module.required_files(REPO)}
        self.assertIn("T12-KimMyeongjun/README-FIRST.md", targets)
        # 장치 스크립트는 하나도 빠지면 안 된다. README가 가리키는 명령이 없어진다.
        bundled_scripts = {
            target.removeprefix("T12-KimMyeongjun/device/")
            for target in targets
            if target.startswith("T12-KimMyeongjun/device/") and target.endswith(".py")
        }
        device_scripts = {path.name for path in (REPO / "device").glob("*.py")}
        self.assertEqual(bundled_scripts, device_scripts)
        self.assertIn("test_device.py", device_scripts)
        bundled_assets = {
            target.removeprefix("T12-KimMyeongjun/docs/assets/")
            for target in targets
            if target.startswith("T12-KimMyeongjun/docs/assets/")
        }
        site_assets = {path.name for path in (REPO / "docs" / "assets").iterdir() if path.is_file()}
        self.assertEqual(bundled_assets, site_assets)
        self.assertTrue(site_assets)
        self.assertFalse(
            any(
                target.startswith("T12-KimMyeongjun/private/")
                or target.startswith("T12-KimMyeongjun/inputs/")
                for target in targets
            )
        )


if __name__ == "__main__":
    unittest.main()
