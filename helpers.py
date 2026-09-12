import re
import json
import os
import asyncio
import aiohttp
import time
from functools import lru_cache

# CC Pattern — يقبل | و / كفاصل
CC_PATTERN = re.compile(
    r"(\d{13,19})[|/](\d{1,2})[|/](\d{2,4})[|/](\d{3,4})"
)

# BIN cache — نتجنب طلبات متكررة لنفس الـ BIN
_bin_cache: dict = {}
_bin_cache_time: dict = {}
_BIN_CACHE_TTL = 3600  # ساعة


def parse_proxy_format(text: str) -> dict | None:
    text = text.strip()
    if not text:
        return None

    # إزالة http:// أو socks5:// prefix
    scheme = "http"
    for s in ("socks5://", "socks4://", "http://", "https://"):
        if text.lower().startswith(s):
            scheme = s.rstrip("://")
            text = text[len(s):]
            break

    # Format: user:pass@host:port
    if "@" in text:
        auth, hostport = text.rsplit("@", 1)
        host, port = (hostport.rsplit(":", 1) + ["80"])[:2]
        user, pwd = (auth.split(":", 1) + [""])[:2]
        return {
            "ip": host, "port": port,
            "username": user, "password": pwd,
            "type": scheme,
            "proxy_url": f"http://{user}:{pwd}@{host}:{port}"
        }

    # Format: host:port:user:pass
    parts = text.split(":")
    if len(parts) >= 4:
        host, port, user = parts[0], parts[1], parts[2]
        pwd = ":".join(parts[3:])
        return {
            "ip": host, "port": port,
            "username": user, "password": pwd,
            "type": scheme,
            "proxy_url": f"http://{user}:{pwd}@{host}:{port}"
        }

    # Format: host:port
    if ":" in text:
        host, port = text.rsplit(":", 1)
        return {
            "ip": host, "port": port,
            "username": "", "password": "",
            "type": scheme,
            "proxy_url": f"http://{host}:{port}"
        }

    return None


def proxy_dict_to_url(proxy_data: dict) -> str | None:
    if not proxy_data:
        return None
    url = proxy_data.get("proxy_url")
    if url:
        return url
    ip   = proxy_data.get("ip", "") or proxy_data.get("host", "")
    port = proxy_data.get("port", "")
    user = proxy_data.get("username", "") or proxy_data.get("user", "")
    pw   = proxy_data.get("password", "") or proxy_data.get("pass", "")
    if user and pw:
        return f"http://{user}:{pw}@{ip}:{port}"
    return f"http://{ip}:{port}"


async def test_proxy(proxy_url: str, timeout: int = 10) -> tuple[bool, float, str]:
    try:
        start = time.monotonic()
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.ipify.org?format=json",
                proxy=proxy_url,
                timeout=aiohttp.ClientTimeout(total=timeout),
                ssl=False,
            ) as resp:
                latency = (time.monotonic() - start) * 1000
                if resp.status == 200:
                    return True, latency, ""
                return False, 0, f"HTTP {resp.status}"
    except Exception as e:
        return False, 0, str(e)[:80]


async def bin_lookup(bin_num: str) -> dict:
    default = {
        "brand": "-", "type": "-", "level": "-",
        "bank": "-", "country": "-", "flag": "🏳️"
    }
    # تحقق من الكاش
    now = time.time()
    if bin_num in _bin_cache and now - _bin_cache_time.get(bin_num, 0) < _BIN_CACHE_TTL:
        return _bin_cache[bin_num]

    # نجرب مصادر متعددة
    sources = [
        f"https://lookup.binlist.net/{bin_num}",
        f"https://api.bincodes.com/bin/?format=json&api_key=free&bin={bin_num}",
    ]
    for url in sources:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=8),
                    headers={"Accept-Version": "3"},
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json(content_type=None)
                        result = {
                            "brand":   data.get("scheme", data.get("brand", "-")).upper(),
                            "type":    data.get("type", "-").upper(),
                            "level":   data.get("brand", data.get("subtype", "-")).upper(),
                            "bank":    (data.get("bank", {}) or {}).get("name", data.get("bank_name", "-")),
                            "country": (data.get("country", {}) or {}).get("name", data.get("country_name", "-")),
                            "flag":    (data.get("country", {}) or {}).get("emoji", "🏳️"),
                        }
                        _bin_cache[bin_num] = result
                        _bin_cache_time[bin_num] = now
                        return result
        except Exception:
            continue
    return default


def extract_cc(text: str) -> str | None:
    m = CC_PATTERN.search(text)
    if m:
        return f"{m.group(1)}|{m.group(2)}|{m.group(3)}|{m.group(4)}"
    return None


def extract_all_cc(text: str) -> list[str]:
    return [f"{m.group(1)}|{m.group(2)}|{m.group(3)}|{m.group(4)}"
            for m in CC_PATTERN.finditer(text)]


def close_session():
    pass


def classify_gate_response(response_text: str) -> str:
    if not response_text:
        return "unknown"
    r = str(response_text).lower()

    if any(k in r for k in [
        "order_placed", "charged", "success", "thank_you", "thank-you",
        "order confirmed", "payment complete", "payment successful",
        "/orders/", "processedreceipt", "order placed"
    ]):
        return "charged"

    if any(k in r for k in ["insufficient_funds", "insufficient funds", "do_not_honor", "do not honor"]):
        return "insufficient_funds"

    if any(k in r for k in [
        "incorrect_cvc", "incorrect_cvv", "invalid_cvc", "invalid_cvv",
        "cvv_failed", "cvc_failed", "security code", "cvc does not match"
    ]):
        return "incorrect_cvc"

    if any(k in r for k in ["incorrect_zip", "incorrect zip", "zip failed", "postal"]):
        return "incorrect_zip"

    if any(k in r for k in [
        "otp_required", "otp required", "3ds", "3d secure",
        "authentication_required", "action_required", "actionrequiredreceipt",
        "authenticate", "challenge"
    ]):
        return "otp_required"

    if any(k in r for k in ["risky", "fraud", "suspected fraud", "risk_rejected", "risk"]):
        return "risky"

    if any(k in r for k in ["expired", "card_expired", "card expired", "expiry"]):
        return "expired"

    if any(k in r for k in [
        "declined", "card_declined", "do_not_honor", "transaction not permitted",
        "invalid card", "lost card", "stolen card", "restricted", "blocked",
        "payment_failed", "incorrect_number", "invalid_number", "call_issuer",
        "pick_up_card", "generic_decline", "transaction declined"
    ]):
        return "declined"

    return "unknown"


def gate_is_charged(response_text: str) -> bool:
    return classify_gate_response(response_text) == "charged"


def gate_is_approved(response_text: str) -> bool:
    return classify_gate_response(response_text) in (
        "otp_required", "incorrect_cvc", "incorrect_zip", "insufficient_funds",
    )
