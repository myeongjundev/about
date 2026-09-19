from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


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
            self.assertNotIn("clovlabcalss.store", content)

    def test_final_site_rejects_draft_content(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                site_module.build(
                    REPO / "content" / "approved.json",
                    Path(temp) / "index.html",
                    BASE / "templates" / "page.html.tpl",
                    False,
                )


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
    def test_current_draft_passes_structural_validation(self) -> None:
        self.assertEqual(validation_module.validate(REPO, True, False), [])

    def test_current_draft_cannot_be_released(self) -> None:
        problems = validation_module.validate(REPO, False, False)
        self.assertTrue(any("profile.tagline" in problem for problem in problems))
        self.assertTrue(any("third-project" in problem for problem in problems))


if __name__ == "__main__":
    unittest.main()
