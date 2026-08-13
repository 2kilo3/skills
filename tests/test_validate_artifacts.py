from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "project-learning-sop"
    / "scripts"
    / "validate_artifacts.py"
)


def load_validator():
    specification = importlib.util.spec_from_file_location("validate_artifacts", SCRIPT)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


class CourseResourceTests(unittest.TestCase):
    def test_course_parser_rejects_non_embedded_resource_references(self) -> None:
        validator = load_validator()
        parser = validator.CourseParser()
        parser.feed(
            """
            <link rel="stylesheet" href="styles.css">
            <script src="file:///private/course.js"></script>
            <iframe src="ftp://example.invalid/course"></iframe>
            <object data="//example.invalid/object"></object>
            <form action="https://example.invalid/submit"></form>
            <video poster="poster.png"></video>
            """
        )
        self.assertEqual(len(parser.external_resources), 6)

    def test_course_parser_accepts_inline_anchors_and_data_images(self) -> None:
        validator = load_validator()
        parser = validator.CourseParser()
        parser.feed(
            """
            <style>body { color: black; }</style>
            <script>document.body.dataset.ready = "true";</script>
            <a href="#module-1">Module</a>
            <img src="data:image/png;base64,AA==" alt="embedded">
            """
        )
        self.assertEqual(parser.external_resources, [])
        self.assertEqual(parser.invalid_images, [])

    def test_course_parser_reads_strict_offline_csp(self) -> None:
        validator = load_validator()
        parser = validator.CourseParser()
        parser.feed(
            """
            <meta http-equiv="Content-Security-Policy"
              content="default-src 'none'; base-uri 'none'; connect-src 'none';
              form-action 'none'; frame-src 'none'; img-src data:; object-src 'none';
              script-src 'unsafe-inline'; style-src 'unsafe-inline'">
            """
        )
        self.assertEqual(parser.content_security_policy, validator.REQUIRED_CSP)
        self.assertEqual(parser.content_security_policy_count, 1)

    def test_course_parser_counts_multiple_csp_policies(self) -> None:
        validator = load_validator()
        parser = validator.CourseParser()
        parser.feed(
            '<meta http-equiv="Content-Security-Policy" content="default-src *">'
            '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'">'
        )
        self.assertEqual(parser.content_security_policy_count, 2)

    def test_course_parser_reports_navigation_and_embedding_tags(self) -> None:
        validator = load_validator()
        parser = validator.CourseParser()
        parser.feed(
            '<meta http-equiv="refresh" content="0;url=file:///private">'
            '<iframe srcdoc="inline"></iframe><object></object><form></form>'
        )
        self.assertTrue(parser.meta_refresh)
        self.assertEqual(parser.forbidden_tags, ["iframe", "object", "form"])


if __name__ == "__main__":
    unittest.main()
