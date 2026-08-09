import gzip
import json

from flask import Flask, Response, request

from ...config import AppConfig
from ...tomgpt_security import (
    RateLimiter,
    check_access_secret,
    client_ip,
    is_chat_heavy_path,
    is_static_asset_path,
    parse_rate_limit,
)


def _json_error(message: str, status: int, headers: dict | None = None) -> Response:
    body = json.dumps(
        {"error": {"message": message}},
        ensure_ascii=False,
    )
    response = Response(body, status=status, mimetype="application/json")
    if headers:
        for key, value in headers.items():
            response.headers[key] = value
    return response


def _build_limiters() -> tuple[RateLimiter | None, RateLimiter | None]:
    chat_spec = parse_rate_limit(AppConfig.rate_limit)
    global_spec = parse_rate_limit(AppConfig.rate_limit_global)
    chat_limiter = RateLimiter(*chat_spec) if chat_spec else None
    global_limiter = RateLimiter(*global_spec) if global_spec else None
    return chat_limiter, global_limiter


def create_app(compress: bool = True) -> Flask:
    app = Flask(__name__)
    chat_limiter, global_limiter = _build_limiters()

    @app.before_request
    def tomgpt_security_gate():
        if request.method == "OPTIONS":
            return None

        password = AppConfig.resolved_access_password()
        if password and not check_access_secret(
            request.headers.get("Authorization"),
            password,
            api_key_header=request.headers.get("g4f-api-key"),
        ):
            return Response(
                "Authentication required / 需要访问密码",
                401,
                {
                    "WWW-Authenticate": 'Basic realm="TomGPT"',
                    "Cache-Control": "no-store",
                },
            )

        if is_static_asset_path(request.path):
            return None

        ip = client_ip(
            request.remote_addr,
            request.headers.get("X-Forwarded-For"),
            trust_proxy=AppConfig.trust_proxy,
        )

        if global_limiter and not global_limiter.allow(ip):
            retry = global_limiter.retry_after(ip)
            return _json_error(
                "Rate limit exceeded / 请求过于频繁，请稍后再试",
                429,
                {"Retry-After": str(retry), "Cache-Control": "no-store"},
            )

        if (
            chat_limiter
            and is_chat_heavy_path(request.path)
            and request.method in ("POST", "PUT", "PATCH", "DELETE")
            and not chat_limiter.allow(f"chat:{ip}")
        ):
            retry = chat_limiter.retry_after(f"chat:{ip}")
            return _json_error(
                "Chat rate limit exceeded / 对话请求过于频繁，请稍后再试",
                429,
                {"Retry-After": str(retry), "Cache-Control": "no-store"},
            )

        return None

    @app.after_request
    def compress_response(response):
        if not compress:
            return response
        accept_encoding = request.headers.get("Accept-Encoding", "")
        if "gzip" not in accept_encoding.lower():
            return response
        if response.status_code < 200 or response.status_code >= 300:
            return response
        if "Content-Encoding" in response.headers:
            return response
        content_type = response.headers.get("Content-Type", "")
        if not content_type.startswith(
            ("text/", "application/javascript", "application/json")
        ):
            return response

        response.direct_passthrough = False
        response.data = gzip.compress(response.data)
        response.headers["Content-Encoding"] = "gzip"
        response.headers["Vary"] = "Accept-Encoding"
        response.headers["Content-Length"] = len(response.data)
        return response

    return app
