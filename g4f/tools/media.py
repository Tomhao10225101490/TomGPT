from __future__ import annotations

import os
import base64
from typing import Iterator, Union
from urllib.parse import urlparse
from pathlib import Path

from ..typing import Messages
from ..image import (
    is_data_an_media,
    to_input_audio,
    is_valid_media,
    is_valid_audio,
    to_data_uri,
)
from .files import get_bucket_dir, read_bucket


def render_media(
    bucket_id: str,
    name: str,
    url: str,
    as_path: bool = False,
    as_base64: bool = False,
    **kwargs,
) -> Union[str, Path]:
    if as_base64 or as_path or url.startswith("/"):
        file = Path(get_bucket_dir(bucket_id, "thumbnail", name))
        if not file.exists():
            file = Path(get_bucket_dir(bucket_id, "media", name))
        if as_path:
            return file
        data = file.read_bytes()
        data_base64 = base64.b64encode(data).decode()
        if as_base64:
            return data_base64
        return f"data:{is_data_an_media(data, name)};base64,{data_base64}"
    return url


def _image_url_from_part(part: dict) -> str | None:
    image_url = part.get("image_url")
    if isinstance(image_url, dict):
        return image_url.get("url")
    if isinstance(image_url, str):
        return image_url
    url = part.get("url")
    return url if isinstance(url, str) else None


def _is_local_or_unreachable_media_url(url: str | None) -> bool:
    """True when remote vision models cannot fetch this URL (blob/local/loopback)."""
    if not url or not isinstance(url, str):
        return True
    if url.startswith("data:"):
        return False
    if url.startswith("blob:"):
        return True
    parsed = urlparse(url)
    path = parsed.path or ""
    if path.startswith("/files/"):
        return True
    host = (parsed.hostname or "").lower()
    if host in ("localhost", "127.0.0.1", "0.0.0.0", "::1"):
        return True
    if not parsed.scheme and path.startswith("/"):
        return True
    return False


def _data_uri_from_files_path(url: str) -> str | None:
    parsed = urlparse(url)
    path = parsed.path or url
    if not path.startswith("/files/"):
        return None
    segments = path.split("/")
    # /files/<bucket>/<type>/<filename>
    if len(segments) < 5:
        return None
    file_path = Path(get_bucket_dir(*segments[2:]))
    if not file_path.exists():
        return None
    data = file_path.read_bytes()
    data_base64 = base64.b64encode(data).decode()
    return f"data:{is_data_an_media(data, segments[-1])};base64,{data_base64}"


def _localize_image_part(part: dict) -> dict:
    """Convert local/blob image parts to data URIs so remote models can read them."""
    if not part:
        return part
    if part.get("type") == "image_url" or part.get("image_url"):
        url = _image_url_from_part(part)
        if not _is_local_or_unreachable_media_url(url):
            return {
                "type": "image_url",
                "image_url": {"url": url},
            }
        bucket_id = part.get("bucket_id")
        name = part.get("name")
        if bucket_id and name:
            try:
                # Pass "/" so render_media reads the local bucket file (not echo remote URL)
                return {
                    "type": "image_url",
                    "image_url": {"url": render_media(bucket_id, name, "/", as_base64=False)},
                }
            except Exception:
                pass
        if url:
            data_uri = _data_uri_from_files_path(url)
            if data_uri:
                return {"type": "image_url", "image_url": {"url": data_uri}}
        # Drop unusable local/blob URL so FormData media can be merged instead
        return None
    if "type" in part:
        return part
    text = part.get("text")
    if text:
        return {"type": "text", "text": text}
    filename = part.get("name")
    if filename is None:
        bucket_dir = Path(get_bucket_dir(part.get("bucket_id")))
        return {"type": "text", "text": "".join(read_bucket(bucket_dir))}
    if is_valid_audio(filename=filename):
        return {
            "type": "input_audio",
            "input_audio": {
                "data": render_media(**part, as_base64=True),
                "format": os.path.splitext(filename)[1][1:],
            },
        }
    if is_valid_media(filename=filename):
        return {"type": "image_url", "image_url": {"url": render_media(**part)}}


def render_part(part: dict) -> dict:
    return _localize_image_part(part)


def _media_as_content_parts(media: list) -> list:
    parts = []
    for media_data, filename in media or []:
        if not media_data or not is_valid_media(media_data, filename):
            continue
        if is_valid_audio(media_data, filename):
            parts.append(
                {
                    "type": "input_audio",
                    "input_audio": to_input_audio(media_data, filename),
                }
            )
        else:
            parts.append(
                {
                    "type": "image_url",
                    "image_url": {"url": to_data_uri(media_data)},
                }
            )
    return parts


def _content_has_usable_media(parts: list) -> bool:
    for part in parts or []:
        if not part:
            continue
        if part.get("type") == "input_audio":
            return True
        if part.get("type") == "image_url":
            url = _image_url_from_part(part)
            if url and not _is_local_or_unreachable_media_url(url):
                return True
    return False


def merge_media(media: list, messages: list) -> Iterator:
    buffer = []
    # Read media from the last user message
    for message in messages:
        if message.get("role") == "user":
            content = message.get("content")
            if isinstance(content, list):
                for part in content:
                    if "type" not in part and "name" in part and "text" not in part:
                        path = render_media(**part, as_path=True)
                        buffer.append((path, os.path.basename(path)))
                    elif part.get("type") == "image_url":
                        image_url = part.get("image_url")
                        if isinstance(image_url, dict):
                            image_url = image_url.get("url")
                        path: str = urlparse(image_url).path
                        if path.startswith("/files/"):
                            path = get_bucket_dir(*path.split("/")[2:])
                            if os.path.exists(path):
                                buffer.append((Path(path), os.path.basename(path)))
                            else:
                                buffer.append((image_url, None))
                        else:
                            buffer.append((image_url, None))
        else:
            buffer = []
    yield from buffer
    if media is not None:
        yield from media


def render_messages(messages: Messages, media: list = None) -> Iterator:
    last_is_assistant = False
    for idx, message in enumerate(messages):
        # Remove duplicate assistant messages
        if message.get("role") == "assistant":
            if last_is_assistant:
                continue
            last_is_assistant = True
        else:
            last_is_assistant = False
        # Render content parts
        if isinstance(message.get("content"), list):
            parts = [render_part(part) for part in message["content"] if part]
            parts = [part for part in parts if part]
            # List content previously ignored FormData media; merge when images are still unusable
            if (
                media is not None
                and idx == len(messages) - 1
                and not _content_has_usable_media(parts)
            ):
                parts = _media_as_content_parts(media) + parts
            if parts:
                yield {**message, "content": parts}
        else:
            # Append media to the last message
            if media is not None and idx == len(messages) - 1:
                yield {
                    **message,
                    "content": _media_as_content_parts(media)
                    + (
                        [{"type": "text", "text": message["content"]}]
                        if isinstance(message["content"], str)
                        else message["content"]
                    ),
                }
            else:
                yield message
