from __future__ import annotations

import io
import unittest
import zipfile

from g4f.tools.export_docx import (
    build_docx_bytes,
    has_docx,
    safe_docx_filename,
)


@unittest.skipUnless(has_docx, "python-docx is not installed")
class TestTomGPTDocxExport(unittest.TestCase):
    def test_build_docx_contains_expected_content(self):
        payload = build_docx_bytes(
            "# 测试标题\n\n- 第一项\n- 第二项\n\n**正文**",
            title="TomGPT 导出",
        )
        self.assertTrue(payload.startswith(b"PK"))
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            document_xml = archive.read("word/document.xml").decode("utf-8")
        self.assertIn("TomGPT 导出", document_xml)
        self.assertIn("测试标题", document_xml)
        self.assertIn("第一项", document_xml)
        self.assertIn("正文", document_xml)

    def test_empty_content_is_still_valid_docx(self):
        payload = build_docx_bytes("")
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            self.assertIn("word/document.xml", archive.namelist())

    def test_safe_filename(self):
        self.assertEqual("报告-最终版.docx", safe_docx_filename("报告/最终版"))
        self.assertEqual("TomGPT.docx", safe_docx_filename(None))
