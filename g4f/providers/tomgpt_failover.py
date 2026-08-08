"""TomGPT automatic provider failover.

When a user selects a specific provider that fails, transparently fall back to
AnyProvider (multi-provider rotation) so chat stays smooth.
"""

from __future__ import annotations

from typing import Type, Union

from ..typing import Messages, AsyncResult, MediaListType
from .. import debug
from .types import BaseProvider, BaseRetryProvider
from .response import ProviderInfo, JsonConversation, is_content
from .base_provider import get_async_provider_method
from .retry_provider import _resolve_model, _prepare_provider_kwargs
from .any_provider import AnyProvider


class PreferredThenAny(BaseRetryProvider):
    """Try the user's preferred provider first; on failure switch to AnyProvider."""

    __name__ = "TomGPTAuto"
    label = "TomGPT 自动"
    working = True
    supports_stream = True

    def __init__(self, preferred: Type[BaseProvider]) -> None:
        self.preferred = preferred
        self.providers = [preferred]
        self.last_provider: Type[BaseProvider] = None

    def get_dict(self):
        preferred = self.preferred
        data = preferred.get_dict() if hasattr(preferred, "get_dict") else {}
        data = dict(data or {})
        data["name"] = getattr(preferred, "__name__", "TomGPTAuto")
        data["label"] = getattr(preferred, "label", None) or data.get("name")
        return data

    async def create_async_generator(
        self,
        model: str,
        messages: Messages,
        ignored: list[str] = None,
        api_key: str = None,
        conversation: JsonConversation = None,
        media: MediaListType = None,
        **kwargs,
    ) -> AsyncResult:
        ignored = list(ignored or [])
        preferred = self.preferred
        self.last_provider = preferred
        alias = _resolve_model(preferred, model)

        debug.log(
            f"TomGPT: trying preferred provider {preferred.__name__} with model {alias}"
        )
        yield ProviderInfo(**preferred.get_dict(), model=alias)

        started = False
        preferred_failed = False
        fail_reason = None
        extra_body = _prepare_provider_kwargs(preferred, api_key, conversation, kwargs)

        try:
            method = get_async_provider_method(preferred)
            response = method(
                model=alias,
                messages=messages,
                media=media,
                **extra_body,
            )
            async for chunk in response:
                if isinstance(chunk, JsonConversation):
                    if conversation is None:
                        conversation = JsonConversation()
                    setattr(conversation, preferred.__name__, chunk.get_dict())
                    yield conversation
                elif chunk:
                    yield chunk
                    if is_content(chunk):
                        started = True
            if started:
                preferred.live = getattr(preferred, "live", 0) + 1
                return
            preferred_failed = True
            fail_reason = "empty response"
        except Exception as e:
            preferred.live = getattr(preferred, "live", 0) - 1
            preferred_failed = True
            fail_reason = e
            debug.error(f"TomGPT: {preferred.__name__} failed:", e)
            if started:
                raise

        if not preferred_failed:
            return

        parent = preferred.get_parent()
        fallback_ignored = list({*ignored, parent, preferred.__name__})
        debug.log(
            f"TomGPT: auto-switching after {preferred.__name__} ({fail_reason}); "
            f"ignored={fallback_ignored}"
        )
        # Soft status for the UI (type: message — shown as subtle notice)
        yield Exception("TomGPT 正在自动切换可用通道…")

        # Start a fresh session so stale chat IDs from other backends can't poison failover
        async for chunk in AnyProvider.create_async_generator(
            model,
            messages,
            ignored=fallback_ignored,
            api_key=api_key,
            conversation=None,
            media=media,
            **kwargs,
        ):
            if isinstance(chunk, ProviderInfo):
                self.last_provider = None
            yield chunk


def wrap_with_auto_failover(
    provider_handler: Union[Type[BaseProvider], BaseRetryProvider, None],
):
    """Ensure chat requests always have transparent multi-provider failover."""
    if provider_handler is None:
        return AnyProvider
    if isinstance(provider_handler, BaseRetryProvider):
        return provider_handler
    if provider_handler is AnyProvider or getattr(provider_handler, "__name__", "") == "AnyProvider":
        return AnyProvider
    # Custom / PA / single providers: prefer them, then auto-rotate
    return PreferredThenAny(provider_handler)
