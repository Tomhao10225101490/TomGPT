from __future__ import annotations

import unittest
from unittest.mock import patch

from g4f.providers.base_provider import AsyncGeneratorProvider
from g4f.providers.retry_provider import RotatedProvider
from g4f.providers.tomgpt_failover import PreferredThenAny
from g4f.providers.any_provider import AnyProvider
from g4f.providers.response import ProviderInfo


MESSAGES = [{"role": "user", "content": "hello"}]


class EmptyProvider(AsyncGeneratorProvider):
    working = True
    live = 0
    default_model = ""
    model_aliases = {}

    @classmethod
    async def create_async_generator(cls, model, messages, stream=True, **kwargs):
        if False:
            yield None


class GoodProvider(AsyncGeneratorProvider):
    working = True
    live = 0
    default_model = ""
    model_aliases = {}

    @classmethod
    async def create_async_generator(cls, model, messages, stream=True, **kwargs):
        yield "ok"


class FailingProvider(AsyncGeneratorProvider):
    working = True
    live = 0
    default_model = ""
    model_aliases = {}

    @classmethod
    async def create_async_generator(cls, model, messages, stream=True, **kwargs):
        raise RuntimeError("provider down")
        yield None


class MidStreamFailProvider(AsyncGeneratorProvider):
    working = True
    live = 0
    default_model = ""
    model_aliases = {}

    @classmethod
    async def create_async_generator(cls, model, messages, stream=True, **kwargs):
        yield "partial"
        raise RuntimeError("connection lost")


class TestTomGPTFailover(unittest.IsolatedAsyncioTestCase):
    async def test_rotated_skips_empty_response(self):
        chunks = [
            chunk
            async for chunk in RotatedProvider(
                [EmptyProvider, GoodProvider], False
            ).create_async_generator("", MESSAGES)
            if not isinstance(chunk, ProviderInfo)
        ]
        self.assertEqual(["ok"], chunks)

    async def test_midstream_failure_returns_clear_partial_marker(self):
        chunks = [
            chunk
            async for chunk in RotatedProvider(
                [MidStreamFailProvider, GoodProvider], False
            ).create_async_generator("", MESSAGES)
            if not isinstance(chunk, ProviderInfo)
        ]
        self.assertEqual("partial", chunks[0])
        self.assertIn("回复可能不完整", chunks[-1])
        self.assertNotIn("ok", chunks)

    async def test_preferred_failure_falls_back_to_any(self):
        async def fake_any(cls, model, messages, **kwargs):
            yield "fallback"

        with patch.object(
            AnyProvider,
            "create_async_generator",
            new=classmethod(fake_any),
        ):
            chunks = [
                chunk
                async for chunk in PreferredThenAny(
                    FailingProvider
                ).create_async_generator("", MESSAGES)
                if not isinstance(chunk, (ProviderInfo, Exception))
            ]
        self.assertEqual(["fallback"], chunks)
