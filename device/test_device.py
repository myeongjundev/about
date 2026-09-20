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
            shutil.copytree(REPO / "docs" / "files", output_dir / "files")
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
            self.assertEqual(content.count('data-craft="'), 3)
            self.assertEqual(content.count('data-craft="design"'), 1)
            self.assertIn('data-craft="design" data-index="01"', content)
            self.assertIn('aria-pressed="true"', content)
            self.assertNotIn('aria-label="색상 테마 바꾸기"', content)
            self.assertNotIn("fonts.googleapis.com", content)
            self.assertNotIn("fonts.gstatic.com", content)
            self.assertNotIn("raw.githubusercontent.com", content)
            self.assertNotIn("myeongjundev.github.io/assets", content)
            self.assertEqual(content.count('class="story-step-link'), 3)
            self.assertIn('href="#story-setback"', content)
            self.assertIn('href="#story-recovery"', content)
            self.assertIn('href="#story-now"', content)
            self.assertIn('aria-label="이야기 단계 바로가기"', content)
            self.assertIn('aria-current="step"', content)

    def test_selected_builds_link_to_existing_project_sections(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output_dir = Path(temp)
            shutil.copytree(REPO / "docs" / "files", output_dir / "files")
            output = output_dir / "index.html"
            site_module.build(
                REPO / "content" / "approved.json",
                output,
                BASE / "templates" / "page.html.tpl",
                False,
            )
            content = output.read_text(encoding="utf-8")
            self.assertIn("SELECTED BUILDS", content)
            self.assertEqual(content.count('class="build-card"'), 4)
            self.assertIn('href="#work-clov"', content)
            self.assertIn('id="work-clov"', content)
            self.assertIn('href="#work-t03-card-studio"', content)
            self.assertIn('id="work-t03-card-studio"', content)
            self.assertIn('href="#experience-third-project"', content)
            self.assertIn('id="experience-third-project"', content)
            self.assertEqual(content.count('class="work-case"'), 3)
            self.assertEqual(content.count('class="case-step"'), 12)
            self.assertIn("문제부터 검증까지 보기", content)


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
            site = site.replace(
                'src="assets/clov-promise.jpg"',
                'src="https://example.com/clov-promise.jpg"',
                1,
            )
            (repo / "docs" / "index.html").write_text(site, encoding="utf-8")
            problems = validation_module.validate(repo, False, False)
            self.assertIn(
                "외부 호스트 이미지: https://example.com/clov-promise.jpg",
                problems,
            )

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


class ReleaseTests(unittest.TestCase):
    def test_release_allowlist_contains_full_device_and_root_readme(self) -> None:
        targets = {str(target) for _, target in release_module.required_files(REPO)}
        self.assertIn("T12-KimMyeongjun/README-FIRST.md", targets)
        self.assertIn("T12-KimMyeongjun/device/apply_numbers.py", targets)
        self.assertIn("T12-KimMyeongjun/device/test_device.py", targets)
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
