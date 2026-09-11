"""
checker_bridge.py — يستخدم API مباشرة بدل الـ nodes القديمة
API: https://api-production-49ca.up.railway.app/check
"""

import asyncio
import aiohttp
import logging
from urllib.parse import quote as _q

log = logging.getLogger("checker_bridge")

API_BASE = "https://api-production-49ca.up.railway.app"
_REQUEST_TIMEOUT = 60
_CONNECT_TIMEOUT = 10

# ── Session singleton ─────────────────────────────────────────────────────────
_session: aiohttp.ClientSession | None = None
_session_lock = asyncio.Lock()

async def _get_session() -> aiohttp.ClientSession:
    global _session
    async with _session_lock:
        if _session is None or _session.closed:
            timeout = aiohttp.ClientTimeout(
                total=_REQUEST_TIMEOUT,
                connect=_CONNECT_TIMEOUT,
            )
            _session = aiohttp.ClientSession(timeout=timeout)
    return _session

# ── proxy dict → url string ───────────────────────────────────────────────────
def _proxy_data_to_proxy_str(proxy_data: dict | None) -> str | None:
    if not proxy_data:
        return None
    host = proxy_data.get("host", "")
    port = proxy_data.get("port", "")
    user = proxy_data.get("username") or proxy_data.get("user", "")
    pwd  = proxy_data.get("password") or proxy_data.get("pass", "")
    if not host or not port:
        return None
    if user and pwd:
        return f"http://{user}:{pwd}@{host}:{port}"
    return f"http://{host}:{port}"

# ── Main check function ───────────────────────────────────────────────────────
async def check_card_site(
    cc_str: str,
    site_url: str,
    proxy_data: dict | None,
) -> dict:
    """
    يرسل الكرت للـ API ويرجع dict فيه:
    Response, Price, Gate, Site, Charged, status_code, error
    """
    proxy_str = _proxy_data_to_proxy_str(proxy_data)
    if not proxy_str:
        return {
            "Response": "No proxy – add one with /proxy",
            "Price": "-",
            "Gate": "-",
            "Site": site_url,
            "Charged": "False",
            "status_code": "NO_PROXY",
            "error": "no proxy configured",
        }

    params = {
        "card": cc_str,
        "url": site_url,
        "proxy": proxy_str,
    }

    session = await _get_session()
    try:
        async with session.get(
            f"{API_BASE}/check",
            params=params,
            ssl=False,
        ) as resp:
            if resp.status != 200:
                text = await resp.text()
                return {
                    "Response": "ERROR",
                    "Price": "-",
                    "Gate": "-",
                    "Site": site_url,
                    "Charged": "False",
                    "status_code": f"HTTP_{resp.status}",
                    "error": text[:120],
                }
            data = await resp.json(content_type=None)
            # نضمن وجود كل الـ keys اللي يحتاجها bot.py
            return {
                "Response":    data.get("Response", "ERROR"),
                "Price":       data.get("Price", "-"),
                "Gate":        data.get("Gate", "-"),
                "Site":        data.get("Site", site_url),
                "Charged":     data.get("Charged", "False"),
                "status_code": data.get("status_code", ""),
                "error":       data.get("error", ""),
                "receipt_url": data.get("receipt_url", ""),
            }
    except asyncio.TimeoutError:
        return {
            "Response": "ERROR",
            "Price": "-",
            "Gate": "-",
            "Site": site_url,
            "Charged": "False",
            "status_code": "TIMEOUT",
            "error": "request timed out",
        }
    except Exception as exc:
        return {
            "Response": "ERROR",
            "Price": "-",
            "Gate": "-",
            "Site": site_url,
            "Charged": "False",
            "status_code": "EXCEPTION",
            "error": str(exc)[:120],
        }

# ── test_site ─────────────────────────────────────────────────────────────────
async def test_site(site_url: str, proxy_data: dict | None) -> dict:
    dummy_cc = "4111111111111111|12|2030|123"
    return await check_card_site(dummy_cc, site_url, proxy_data)

# ── Node management stubs (bot.py يستدعيها) ──────────────────────────────────
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
