from __future__ import annotations

import base64
import unittest

from g4f.tomgpt_security import (
    RateLimiter,
    check_access_secret,
    client_ip,
    is_chat_heavy_path,
    is_loopback_host,
    parse_rate_limit,
    resolve_access_password,
)


class TestTomGPTSecurity(unittest.TestCase):
    def test_parse_rate_limit(self):
        self.assertEqual((20, 60), parse_rate_limit("20/60"))
        self.assertIsNone(parse_rate_limit("off"))
        self.assertIsNone(parse_rate_limit(""))
        with self.assertRaises(ValueError):
            parse_rate_limit("abc")

    def test_rate_limiter_blocks_after_budget(self):
        limiter = RateLimiter(2, 60)
        now = 1000.0
        self.assertTrue(limiter.allow("1.1.1.1", now=now))
        self.assertTrue(limiter.allow("1.1.1.1", now=now + 1))
        self.assertFalse(limiter.allow("1.1.1.1", now=now + 2))
        self.assertTrue(limiter.allow("2.2.2.2", now=now + 2))
        self.assertTrue(limiter.allow("1.1.1.1", now=now + 61))

    def test_check_access_secret_basic_and_bearer(self):
        password = "s3cret"
        token = base64.b64encode(b"user:s3cret").decode()
        self.assertTrue(check_access_secret(f"Basic {token}", password))
        self.assertTrue(check_access_secret("Bearer s3cret", password))
        self.assertTrue(
            check_access_secret(None, password, api_key_header="s3cret")
        )
        bad = base64.b64encode(b"user:wrong").decode()
        self.assertFalse(check_access_secret(f"Basic {bad}", password))
        self.assertFalse(check_access_secret("Bearer wrong", password))

    def test_client_ip_respects_trust_proxy(self):
        self.assertEqual(
            "9.9.9.9",
            client_ip("10.0.0.1", "9.9.9.9, 8.8.8.8", trust_proxy=True),
        )
        self.assertEqual(
            "10.0.0.1",
            client_ip("10.0.0.1", "9.9.9.9, 8.8.8.8", trust_proxy=False),
        )

    def test_resolve_password_priority(self):
        self.assertEqual(
            "a",
            resolve_access_password(
                "a", tomgpt_password="b", g4f_api_key="c"
            ),
        )
        self.assertEqual(
            "b",
            resolve_access_password(
                None, tomgpt_password="b", g4f_api_key="c"
            ),
        )
        self.assertEqual(
            "c",
            resolve_access_password(
                None, tomgpt_password=None, g4f_api_key="c"
            ),
        )

    def test_loopback_and_chat_paths(self):
        self.assertTrue(is_loopback_host("127.0.0.1"))
        self.assertFalse(is_loopback_host("0.0.0.0"))
        self.assertTrue(is_chat_heavy_path("/backend-api/v2/conversation"))
        self.assertFalse(is_chat_heavy_path("/chat/"))

    def test_flask_gate_requires_password_and_rate_limits_chat(self):
        from g4f.config import AppConfig
        from g4f.gui.server.app import create_app

        previous = {
            "access_password": AppConfig.access_password,
            "g4f_api_key": AppConfig.g4f_api_key,
            "rate_limit": AppConfig.rate_limit,
            "rate_limit_global": AppConfig.rate_limit_global,
            "trust_proxy": AppConfig.trust_proxy,
        }
        try:
            AppConfig.access_password = "gate-pass"
            AppConfig.g4f_api_key = "gate-pass"
            AppConfig.rate_limit = "2/60"
            AppConfig.rate_limit_global = "off"
            AppConfig.trust_proxy = False
            app = create_app(compress=False)
            client = app.test_client()

            denied = client.get("/chat/")
            self.assertEqual(401, denied.status_code)

            headers = {
                "Authorization": "Basic "
                + base64.b64encode(b"u:gate-pass").decode()
            }
            allowed = client.get("/chat/", headers=headers)
            self.assertNotEqual(401, allowed.status_code)

            first = client.post(
                "/backend-api/v2/conversation", headers=headers, json={}
            )
            second = client.post(
                "/backend-api/v2/conversation", headers=headers, json={}
            )
            third = client.post(
                "/backend-api/v2/conversation", headers=headers, json={}
            )
            self.assertNotEqual(429, first.status_code)
            self.assertNotEqual(429, second.status_code)
            self.assertEqual(429, third.status_code)
        finally:
            for key, value in previous.items():
                setattr(AppConfig, key, value)
