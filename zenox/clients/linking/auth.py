"""HoYoLAB auth utilities – constants, RSA encryption, DS generation, cookie helpers.

This module mirrors genshin.py's ``genshin/utility/auth.py`` for the subset
of functionality needed by Zenox's linking flow.
"""
from __future__ import annotations

import base64
import hashlib
import json
import random
import string
import time

import rsa

from zenox.config import CONFIG

__all__ = (
    "WEB_LOGIN_HEADERS",
    "APP_LOGIN_HEADERS",
    "API_HEADERS",
    "WEB_LOGIN_URL",
    "APP_LOGIN_URL",
    "STOKEN_TO_LTOKEN_URL",
    "encrypt_credentials",
    "generate_app_login_ds",
    "make_aigis_header",
    "parse_cookie_string",
    "get_configured_cookies",
)

# ------------------------------------------------------------------ #
# RSA public key                                                       #
# ------------------------------------------------------------------ #

# Production key for OS web / app login.
# Source: HoYoLAB APK – getRSA_PUBLIC_KEY (use https://www.decompiler.com
# to decompile the APK; the key is the first of three environment keys).
LOGIN_RSA_KEY = b"""-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA4PMS2JVMwBsOIrYWRluY
wEiFZL7Aphtm9z5Eu/anzJ09nB00uhW+ScrDWFECPwpQto/GlOJYCUwVM/raQpAj
/xvcjK5tNVzzK94mhk+j9RiQ+aWHaTXmOgurhxSp3YbwlRDvOgcq5yPiTz0+kSeK
ZJcGeJ95bvJ+hJ/UMP0Zx2qB5PElZmiKvfiNqVUk8A8oxLJdBB5eCpqWV6CUqDKQ
KSQP4sM0mZvQ1Sr4UcACVcYgYnCbTZMWhJTWkrNXqI8TMomekgny3y+d6NX/cFa6
6jozFIF4HCX5aW8bp8C8vq2tFvFbleQ/Q3CU56EWWKMrOcpmFtRmC18s9biZBVR/
8QIDAQAB
-----END PUBLIC KEY-----
"""

# ------------------------------------------------------------------ #
# DS salt                                                              #
# ------------------------------------------------------------------ #

# Salt used by the official HoYoLAB app for its login endpoint.
# Source: decompiled HoYoLAB APK, RequestUtils.createSign().
_DS_SALT_APP_LOGIN = "IZPgfb0dRPtBeLuFkdDznSZ6f4wWt6y2"

# ------------------------------------------------------------------ #
# Endpoint URLs                                                        #
# ------------------------------------------------------------------ #

WEB_LOGIN_URL = "https://sg-public-api.hoyolab.com/account/ma-passport/api/webLoginByPassword"
APP_LOGIN_URL = "https://sg-public-api.hoyoverse.com/account/ma-passport/api/appLoginByPassword"

# Exchange an stoken (returned by app login) for an ltoken_v2 usable with HoYoLAB APIs.
STOKEN_TO_LTOKEN_URL = "https://sg-public-api.hoyoverse.com/account/ma-passport/token/getBySToken"

# ------------------------------------------------------------------ #
# Request headers                                                      #
# ------------------------------------------------------------------ #

# Used for the web password-login endpoint.
# NOTE: Origin/Referer must equal account.hoyolab.com or HoYoLAB returns 1200.
WEB_LOGIN_HEADERS: dict[str, str] = {
    "x-rpc-app_id": "c9oqaq3s3gu8",
    "x-rpc-client_type": "4",
    "Origin": "https://account.hoyolab.com",
    "Referer": "https://account.hoyolab.com/",
}

# Used for the app (Android) password-login endpoint.
APP_LOGIN_HEADERS: dict[str, str] = {
    "x-rpc-app_id": "c9oqaq3s3gu8",
    "x-rpc-client_type": "2",
    "x-rpc-aigis_v4": "true",
    "x-rpc-app_version": "4.8.0",
    "x-rpc-sdk_version": "2.2.0",
}

# Used for HoYoLAB profile/game-record API calls.
API_HEADERS: dict[str, str] = {
    "accept": "application/json, text/plain, */*",
    "content-type": "application/json",
    "origin": "https://www.hoyolab.com",
    "referer": "https://www.hoyolab.com/",
    "x-rpc-app_version": "3.10.0",
    "x-rpc-client_type": "4",
    "x-rpc-language": "en-us",
}

# ------------------------------------------------------------------ #
# Encryption                                                           #
# ------------------------------------------------------------------ #

def encrypt_credentials(text: str) -> str:
    """RSA-PKCS1v15-encrypt *text* for HoYoLAB login payloads."""
    pub = rsa.PublicKey.load_pkcs1_openssl_pem(LOGIN_RSA_KEY)
    return base64.b64encode(rsa.encrypt(text.encode(), pub)).decode()


# ------------------------------------------------------------------ #
# Dynamic-secret (DS) generation                                       #
# ------------------------------------------------------------------ #

def generate_app_login_ds(body: dict) -> str:
    """Generate the ``ds`` header required by the HoYoLAB app login endpoint.

    Mirrors ``RequestUtils.createSign()`` from the official HoYoLAB APK.
    """
    t = int(time.time())
    r = "".join(random.choices(string.ascii_letters + string.digits, k=6))
    b = json.dumps(body, separators=(",", ":"))
    h = hashlib.md5(f"salt={_DS_SALT_APP_LOGIN}&t={t}&r={r}&b={b}&q=".encode()).hexdigest()
    return f"{t},{r},{h}"


# ------------------------------------------------------------------ #
# AIGIS header                                                         #
# ------------------------------------------------------------------ #

def make_aigis_header(session_id: str, mmt_result: dict) -> str:
    """Build the ``x-rpc-aigis`` header used when retrying a captcha-blocked login.

    Format mirrors ``BaseSessionMMTResult.to_aigis_header()`` from genshin.py:
    ``{session_id};{base64(json(mmt_result))}``
    """
    return f"{session_id};{base64.b64encode(json.dumps(mmt_result).encode()).decode()}"


# ------------------------------------------------------------------ #
# Cookie helpers                                                       #
# ------------------------------------------------------------------ #

def parse_cookie_string(cookie_str: str) -> dict[str, str]:
    """Parse a raw ``Cookie:`` header string into a ``{key: value}`` dict."""
    result: dict[str, str] = {}
    for chunk in cookie_str.split(";"):
        part = chunk.strip()
        if not part or "=" not in part:
            continue
        key, _, value = part.partition("=")
        key = key.strip()
        if key:
            result[key] = value.strip()
    return result


def get_configured_cookies() -> dict[str, str]:
    """Return HoYoLAB auth cookies from environment config.

    Priority:
    1. ``HOYOLAB_COOKIE`` – full raw cookie header string.
    2. Discrete ``HOYOLAB_LTOKEN_V2`` / ``HOYOLAB_LTUID_V2`` / … fields.
    """
    if CONFIG.hoyolab_cookie:
        parsed = parse_cookie_string(CONFIG.hoyolab_cookie)
        if parsed:
            return parsed

    cookies: dict[str, str] = {}
    if CONFIG.hoyolab_cookie_token:
        cookies["cookie_token"] = CONFIG.hoyolab_cookie_token
    if CONFIG.hoyolab_ltoken_v2:
        cookies["ltoken_v2"] = CONFIG.hoyolab_ltoken_v2
    if CONFIG.hoyolab_ltuid_v2:
        cookies["ltuid_v2"] = CONFIG.hoyolab_ltuid_v2
    if CONFIG.hoyolab_account_id_v2:
        cookies["account_id_v2"] = CONFIG.hoyolab_account_id_v2
    return cookies
