from __future__ import annotations

import unittest

from g4f import Provider, models
from g4f.providers.any_provider import AnyProvider, FREE_MODEL_ROUTES


class TestTomGPTFreeModels(unittest.TestCase):
    def test_capability_routes_are_discoverable_and_ordered(self):
        expected = {
            "free-advanced": ["Qwen", "CopilotApp", "Pollinations"],
            "free-reasoning": ["CopilotApp", "Qwen", "Pollinations"],
            "free-coding": ["Qwen", "Pollinations"],
            "free-multimodal": ["Qwen", "OperaAria"],
        }
        for model_name, provider_names in expected.items():
            self.assertIn(model_name, AnyProvider.models)
            self.assertEqual(
                provider_names,
                list(AnyProvider.model_map[model_name]),
                model_name,
            )
            self.assertEqual(
                provider_names,
                list(FREE_MODEL_ROUTES[model_name]),
                model_name,
            )

    def test_capability_routes_never_use_auth_or_browser_providers(self):
        for model_name, routes in FREE_MODEL_ROUTES.items():
            for provider_name in routes:
                provider = Provider.__map__[provider_name]
                self.assertTrue(provider.working, f"{model_name}: {provider_name}")
                self.assertFalse(provider.needs_auth, f"{model_name}: {provider_name}")
                self.assertFalse(
                    getattr(provider, "use_nodriver", False),
                    f"{model_name}: {provider_name}",
                )

    def test_provider_aliases_match_supported_models(self):
        qwen_models = set(Provider.Qwen.get_models())
        self.assertIn("qwen3.7-plus", qwen_models)
        self.assertIn("qwen3-coder-plus", qwen_models)
        self.assertIn("qwen3.5-omni-plus", qwen_models)
        self.assertEqual("smart", Provider.CopilotApp.model_aliases["gpt-5"])
        self.assertIn("reasoning", Provider.CopilotApp.get_models())
        self.assertIn("aria", Provider.OperaAria.get_models())

    def test_single_provider_models_are_not_presented_as_high_availability(self):
        expected = {
            "qwen-3.7-plus": ["Qwen"],
            "qwen-3.7-max": ["Qwen"],
            "qwen-3-coder-plus": ["Qwen"],
            "qwen-3.5-omni-plus": ["Qwen"],
            "gpt-oss-20b": ["Pollinations"],
            "llama-3.3-70b": ["Pollinations"],
            "kimi-k2.7-code": ["Pollinations"],
            "glm-5.2": ["Pollinations"],
        }
        for model_name, provider_names in expected.items():
            self.assertIn(model_name, models.__models__)
            self.assertEqual(
                provider_names,
                [
                    provider
                    if isinstance(provider, str)
                    else provider.__name__
                    for provider in models.__models__[model_name][1]
                ],
                model_name,
            )

    def test_free_models_are_grouped_for_the_ui(self):
        groups = {
            group["group"]: group["models"]
            for group in AnyProvider.get_grouped_models()
        }
        self.assertEqual(
            [
                "free-advanced",
                "free-reasoning",
                "free-coding",
                "free-multimodal",
            ],
            groups["Free Advanced"],
        )
