from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path

from g4f.providers.any_provider import wants_image_generation


class TestTomGPTIntent(unittest.TestCase):
    def test_backend_image_intent_matrix(self):
        cases = {
            "帮我生成美国国旗": True,
            "生成美国国旗": True,
            "generate american flag": True,
            "生成一张小猫图片": True,
            "帮我识别这张照片": False,
            "帮我分析这张图片": False,
            "写一份会议纪要": False,
        }
        for prompt, expected in cases.items():
            with self.subTest(prompt=prompt):
                self.assertEqual(expected, wants_image_generation(prompt))

    @unittest.skipUnless(shutil.which("node"), "Node.js is not installed")
    def test_frontend_intent_matrix(self):
        root = Path(__file__).resolve().parents[2]
        result = subprocess.run(
            ["node", str(root / "g4f.dev/dist/js/tomgpt-intents.test.js")],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=15,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
