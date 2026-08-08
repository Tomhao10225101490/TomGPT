from __future__ import annotations

import unittest

from g4f import models
from g4f import Provider


def provider_names(retry_provider):
    return [
        provider if isinstance(provider, str) else provider.__name__
        for provider in retry_provider.providers
    ]


class TestTomGPTDefaultPool(unittest.TestCase):
    def test_text_pool_is_stable_and_quality_first(self):
        pool = models.default.best_provider
        self.assertFalse(pool.shuffle)
        self.assertEqual(
            ["Qwen", "CopilotApp", "OperaAria", "Pollinations", "TeachAnything"],
            provider_names(pool),
        )
        for name in provider_names(pool):
            provider = Provider.__map__[name]
            self.assertFalse(provider.needs_auth, name)
            self.assertFalse(getattr(provider, "use_nodriver", False), name)

    def test_vision_pool_is_stable_and_multimodal_first(self):
        pool = models.default_vision.best_provider
        names = provider_names(pool)
        self.assertFalse(pool.shuffle)
        self.assertEqual(
            ["Qwen", "OperaAria", "Pollinations"],
            names,
        )
        self.assertNotIn("Ollama", names)
        self.assertNotIn("DeepInfra", names)
        for name in names:
            provider = Provider.__map__[name]
            self.assertFalse(provider.needs_auth, name)
            self.assertFalse(getattr(provider, "use_nodriver", False), name)
