import re
import json
import os
import asyncio
import aiohttp

# CC Pattern
CC_PATTERN = re.compile(
    r"(\d{13,19})[|/](\d{1,2})[|/](\d{2,4})[|/](\d{3,4})"
)


def parse_proxy_format(text: str) -> dict | None:
    """Parse various proxy formats into dict."""
    text = text.strip()
    if not text:
        return None

    # Format: host:port:user:pass
    if text.count(":") >= 3:
        parts = text.split(":")
        if len(parts) >= 4:
            return {
                "ip": parts[0],
                "port": parts[1],
                "username": parts[2],
                "password": ":".join(parts[3:]),
                "type": "http",
                "proxy_url": f"http://{parts[2]}:{':'.join(parts[3:])}@{parts[0]}:{parts[1]}"
            }

    # Format: user:pass@host:port
    if "@" in text:
        auth, hostport = text.split("@", 1)
        if ":" in hostport:
            host, port = hostport.split(":", 1)
            return {
                "ip": host,
                "port": port,
                "username": auth.split(":")[0] if ":" in auth else "",
                "password": auth.split(":", 1)[1] if ":" in auth else "",
                "type": "http",
                "proxy_url": f"http://{text}"
            }

    # Format: host:port
    if ":" in text:
        host, port = text.split(":", 1)
        return {
            "ip": host,
            "port": port,
            "username": "",
            "password": "",
            "type": "http",
            "proxy_url": f"http://{host}:{port}"
        }

    return None


def proxy_dict_to_url(proxy_data: dict) -> str | None:
    """Convert proxy dict to URL string."""
    if not proxy_data:
        return None
    url = proxy_data.get("proxy_url")
    if url:
        return url
    ip = proxy_data.get("ip", "")
    port = proxy_data.get("port", "")
    user = proxy_data.get("username", "")
    pw = proxy_data.get("password", "")
    if user and pw:
        return f"http://{user}:{pw}@{ip}:{port}"
    return f"http://{ip}:{port}"


async def test_proxy(proxy_url: str, timeout: int = 15) -> tuple[bool, float, str]:
    """Test if proxy is working. Returns (success, latency_ms, error)."""
    try:
        start = asyncio.get_event_loop().time()
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "http://httpbin.org/ip",
                proxy=proxy_url,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as resp:
                latency = (asyncio.get_event_loop().time() - start) * 1000
                if resp.status == 200:
                    return True, latency, ""
                return False, 0, f"HTTP {resp.status}"
    except Exception as e:
        return False, 0, str(e)[:80]


async def bin_lookup(bin_num: str) -> dict:
    """Lookup BIN info. Returns dict with brand, type, level, bank, country, flag."""
    default = {
        "brand": "-",
        "type": "-",
        "level": "-",
        "bank": "-",
        "country": "-",
        "flag": "🏳️"
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://lookup.binlist.net/{bin_num}",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "brand": data.get("scheme", "-").upper(),
                        "type": data.get("type", "-").upper(),
                        "level": data.get("brand", "-").upper(),
                        "bank": data.get("bank", {}).get("name", "-"),
                        "country": data.get("country", {}).get("name", "-"),
                        "flag": data.get("country", {}).get("emoji", "🏳️")
                    }
    except Exception:
        pass
    return default


def extract_cc(text: str) -> str | None:
    """Extract first CC from text."""
    m = CC_PATTERN.search(text)
    if m:
        return f"{m.group(1)}|{m.group(2)}|{m.group(3)}|{m.group(4)}"
    return None


def close_session():
    """Placeholder for session cleanup."""
    pass
