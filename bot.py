import asyncio
import concurrent.futures
import datetime
import html as _html
import importlib.util
import json
import os
import random
import re
import sys
import time
import logging
import httpx
from io import BytesIO

from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.filters import Command, CommandStart
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode, ChatMemberStatus, MessageEntityType
from aiogram.exceptions import (
    TelegramRetryAfter,
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramNotFound,
)

# ── Patch aiogram session ────────────────────────────────────────────────────
import json as _json
from aiogram.client.session.base import BaseSession as _BaseSession

_DANGEROUS_KEYS = frozenset({"rich_message", "rich_caption", "story"})
_MAX_JSON_DEPTH = 12

def _sanitize(obj, depth: int = 0):
    if depth > _MAX_JSON_DEPTH:
        return {}
    if isinstance(obj, dict):
        return {
            k: _sanitize(v, depth + 1)
            for k, v in obj.items()
            if k not in _DANGEROUS_KEYS
        }
    if isinstance(obj, list):
        return [_sanitize(item, depth + 1) for item in obj]
    return obj

_orig_check_response = _BaseSession.check_response

def _patched_check_response(self, bot, method, status_code: int, content: str):
    try:
        raw = _json.loads(content)
        if isinstance(raw.get("result"), list):
            raw["result"] = [_sanitize(u) for u in raw["result"]]
            content = _json.dumps(raw)
    except Exception:
        pass
    return _orig_check_response(self, bot, method, status_code, content)

_BaseSession.check_response = _patched_check_response
# ── end patch ─────────────────────────────────────────────────────────────────

from helpers import (
    parse_proxy_format, test_proxy, bin_lookup,
    extract_cc, close_session, classify_gate_response,
    gate_is_charged, gate_is_approved, proxy_dict_to_url,
)
import checker_bridge
import auth
#import ayden
import hit
import st
import rz
import chk
import vbv
import b3auth

try:
    import webshare as _webshare_mod
    _WEBSHARE_AVAILABLE = True
except ImportError:
    _webshare_mod = None
    _WEBSHARE_AVAILABLE = False

try:
    import dork as _dork_mod
    _DORK_AVAILABLE = True
except ImportError:
    _dork_mod = None
    _DORK_AVAILABLE = False

try:
    import sk as _sk_mod
    _SK_AVAILABLE = True
except ImportError:
    _sk_mod = None
    _SK_AVAILABLE = False

try:
    import gate as _gate_mod
    _GATE_AVAILABLE = True
except ImportError:
    _gate_mod = None
    _GATE_AVAILABLE = False

# ── Gate modules ─────────────────────────────────────────────────────────────
def _load_gate_file(filename: str):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    mod_name = "gate_" + re.sub(r"[^a-zA-Z0-9_]", "_", filename)
    spec = importlib.util.spec_from_file_location(mod_name, path)
    if not spec or not spec.loader:
        raise ImportError(f"Cannot load gate module: {filename}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

st1_gate = _load_gate_file("stripe1$.py")

# ── Logging ───────────────────────────────────────────────────────────────────
from logging.handlers import RotatingFileHandler

_LOG_DIR = os.path.dirname(os.path.abspath(__file__))
_LOG_FMT = logging.Formatter(
    "%(asctime)s │ %(levelname)s │ %(name)s │ %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

_root = logging.getLogger()
_root.setLevel(logging.INFO)

_console = logging.StreamHandler()
_console.setFormatter(_LOG_FMT)
_root.addHandler(_console)

_file_all = RotatingFileHandler(
    os.path.join(_LOG_DIR, "bot.log"),
    maxBytes=10 * 1024 * 1024,
    backupCount=5,
    encoding="utf-8",
)
_file_all.setFormatter(_LOG_FMT)
_root.addHandler(_file_all)

_file_err = RotatingFileHandler(
    os.path.join(_LOG_DIR, "bot_error.log"),
    maxBytes=5 * 1024 * 1024,
    backupCount=3,
    encoding="utf-8",
)
_file_err.setLevel(logging.WARNING)
_file_err.setFormatter(_LOG_FMT)
_root.addHandler(_file_err)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("hpack").setLevel(logging.WARNING)

log = logging.getLogger("bot")

# ══════════════════════════════════════════════════════════════════════════════
#  CONFIG
# ══════════════════════════════════════════════════════════════════════════════

TOKEN = "8962918744:AAHorUmwpsl09wUkqx8_Vn5nK9jkWXnk8DM"

join_channel_id = -1004329229984
join_chat_id = -1004349648366

CHANNEL_LINK = "http://t.me/onyxa_cc"
GROUP_LINK = "http://t.me/onyxa_chat"

POWERED_BY = "Powered by @iizxy"
BOT_NAME = "𝗵𝗰𝗵𝗸.𝗰𝗮𝗿𝗱𝘀"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROXY_FILE = os.path.join(BASE_DIR, "proxy.json")
SITES_FILE = os.path.join(BASE_DIR, "sites.txt")
SITES_JSON = os.path.join(BASE_DIR, "sites.json")
BANNED_FILE = os.path.join(BASE_DIR, "banned.json")
FREEPROXY_DATA_FILE = os.path.join(BASE_DIR, "freeproxy_data.json")

LIMITS = {"free": 300, "premium": 8000, "admin": 15000, "owner": 30000}
MAX_FILE_SIZE_MB = 25

# ══════════════════════════════════════════════════════════════════════════════
#  PREMIUM EMOJIS
# ══════════════════════════════════════════════════════════════════════════════

E = {
    "charged": "5323373120260695190",
    "declined": "5323395299471813204",
    "approved": "5325881737643847450",
    "live": "5325881737643847450",
    "dead": "5323688589903554436",
    "unknown": "5323745386551077258",
    "error": "5323745386551077258",
    "3ds": "5323393718923848521",
    "ccn": "5323393718923848521",
    "loading": "5325975385110766586",
    "check": "5278622189556354905",
    "cross": "5042112436648281096",
    "warn": "5855207143724027916",
    "gem": "5226656353744862682",
    "bolt": "5084974483685507801",
    "rocket": "5195033767969839232",
    "star": "5980995951160987855",
    "hourglass": "5215327832040811010",
    "stop": "5325764789979344884",
    "time": "5323552181742233895",
    "card": "5472250091332993630",
    "gate": "5323337128434755671",
    "site": "5134452506935427991",
    "amount": "5039789890133296083",
    "code": "5855207143724027916",
    "bin": "5332455502917949981",
    "type": "5854784287013867183",
    "bank": "5854784287013867183",
    "country": "5285452600601237916",
    "user": "5321304384838057247",
    "proxy": "5042101437237036298",
    "file": "5325834523068342417",
    "dork": "5134452506935427991",
    "key": "5980995951160987855",
    "link": "5042101437237036298",
    "globe": "5134452506935427991",
    "crown": "5334915003055108323",
    "role": "5334915003055108323",
    "limit": "5472250091332993630",
    "access": "5321304384838057247",
    "commands": "5334915003055108323",
    "welcome": "5334915003055108323",
    "profile": "5321304384838057247",
    "info": "5855207143724027916",
    "success": "5278622189556354905",
    "fail": "5042112436648281096",
    "pause": "6114014038960638990",
    "maintain": "5325955727045452836",
    "progress": "5325975385110766586",
    "total": "5472250091332993630",
    "checked": "5325957011240675544",
    "yes": "5278622189556354905",
    "no": "5042112436648281096",
    "visa": "5298970748172385213",
    "master": "5355269226732995665",
    "amex": "4983234121556820510",
    "flag_us": "5285452600601237916",
    "flag_jp": "5285452600601237916",
    "next": "5084974483685507801",
}

def pe(emoji_id: str) -> str:
    return f'<tg-emoji emoji-id="{emoji_id}">⚡</tg-emoji>'

# ══════════════════════════════════════════════════════════════════════════════
#  BOLD / ITALIC UNICODE CONVERTERS
# ══════════════════════════════════════════════════════════════════════════════

_BOLD_MAP = {}
for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
    _BOLD_MAP[c] = chr(0x1D5D4 + i)
for i, c in enumerate("abcdefghijklmnopqrstuvwxyz"):
    _BOLD_MAP[c] = chr(0x1D5EE + i)
for i, c in enumerate("0123456789"):
    _BOLD_MAP[c] = chr(0x1D7EC + i)

def bold(text: str) -> str:
    return "".join(_BOLD_MAP.get(c, c) for c in text)

_ITALIC_MAP = {}
for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
    _ITALIC_MAP[c] = chr(0x1D434 + ord(c) - ord('A'))
for i, c in enumerate("abcdefghijklmnopqrstuvwxyz"):
    _ITALIC_MAP[c] = 'ℎ' if c == 'h' else chr(0x1D44E + ord(c) - ord('a'))

def italic(text: str) -> str:
    return "".join(_ITALIC_MAP.get(c, c) for c in text)

# ══════════════════════════════════════════════════════════════════════════════
#  BAN SYSTEM
# ══════════════════════════════════════════════════════════════════════════════

_banned_users: set[int] = set()

def _load_banned() -> None:
    global _banned_users
    try:
        with open(BANNED_FILE, "r", encoding="utf-8") as f:
            _banned_users = set(json.load(f))
    except Exception:
        _banned_users = set()

def _save_banned() -> None:
    try:
        with open(BANNED_FILE, "w", encoding="utf-8") as f:
            json.dump(sorted(_banned_users), f)
    except Exception as exc:
        log.error("Failed to save banned.json: %s", exc)

def is_banned(user_id: int) -> bool:
    return user_id in _banned_users

def ban_user(user_id: int) -> None:
    _banned_users.add(user_id)
    _save_banned()
    log.warning("BAN: user %s", user_id)

def unban_user(user_id: int) -> None:
    _banned_users.discard(user_id)
    _save_banned()
    log.info("UNBAN: user %s", user_id)

_load_banned()

# ══════════════════════════════════════════════════════════════════════════════
#  MAINTENANCE SYSTEM
# ══════════════════════════════════════════════════════════════════════════════

_MAINTENANCE_MODE = False
_MAINTENANCE_REASON = ""
_ACTIVE_SESSIONS: dict[str, dict] = {}

def enable_maintenance(reason: str = "Server Maintenance"):
    global _MAINTENANCE_MODE, _MAINTENANCE_REASON
    _MAINTENANCE_MODE = True
    _MAINTENANCE_REASON = reason

def disable_maintenance():
    global _MAINTENANCE_MODE, _MAINTENANCE_REASON
    _MAINTENANCE_MODE = False
    _MAINTENANCE_REASON = ""

def is_maintenance() -> bool:
    return _MAINTENANCE_MODE

def get_maintenance_msg() -> str:
    return (
        f"{pe(E['pause'])} <b>MAINTENANCE MODE</b> {pe(E['pause'])}\n"
        f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        f"{pe(E['info'])} Reason → {bold(_MAINTENANCE_REASON)}\n"
        f"{pe(E['hourglass'])} Please wait until admin resumes operations."
    )

def register_session(stop_key: str, user_id: int, total: int):
    _ACTIVE_SESSIONS[stop_key] = {
        "user_id": user_id,
        "total": total,
        "checked": 0,
        "stopped": False,
    }

def stop_session(stop_key: str):
    if stop_key in _ACTIVE_SESSIONS:
        _ACTIVE_SESSIONS[stop_key]["stopped"] = True

def is_session_stopped(stop_key: str) -> bool:
    return _ACTIVE_SESSIONS.get(stop_key, {}).get("stopped", False)

def update_session_progress(stop_key: str, checked: int):
    if stop_key in _ACTIVE_SESSIONS:
        _ACTIVE_SESSIONS[stop_key]["checked"] = checked

def get_session_progress(stop_key: str) -> dict:
    return _ACTIVE_SESSIONS.get(stop_key, {})

def clear_session(stop_key: str):
    _ACTIVE_SESSIONS.pop(stop_key, None)

# ══════════════════════════════════════════════════════════════════════════════
#  FILE CHECK SESSION MANAGER (for /yes /no /stop flow)
# ══════════════════════════════════════════════════════════════════════════════

_FILE_SESSIONS: dict[int, dict] = {}

def set_file_session(user_id: int, data: dict):
    _FILE_SESSIONS[user_id] = data

def get_file_session(user_id: int) -> dict | None:
    return _FILE_SESSIONS.get(user_id)

def clear_file_session(user_id: int):
    _FILE_SESSIONS.pop(user_id, None)

# ══════════════════════════════════════════════════════════════════════════════
#  CREDITS SYSTEM
# ══════════════════════════════════════════════════════════════════════════════

CREDITS_FILE = os.path.join(BASE_DIR, "credits.json")

def _load_credits() -> dict:
    try:
        with open(CREDITS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_credits(data: dict):
    with open(CREDITS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_user_credits(user_id: int) -> int:
    return _load_credits().get(str(user_id), 0)

def add_credits(user_id: int, amount: int):
    data = _load_credits()
    data[str(user_id)] = data.get(str(user_id), 0) + amount
    _save_credits(data)

def use_credit(user_id: int) -> bool:
    data = _load_credits()
    uid = str(user_id)
    if data.get(uid, 0) > 0:
        data[uid] -= 1
        _save_credits(data)
        return True
    return False

# ══════════════════════════════════════════════════════════════════════════════
#  LIMITS HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def get_cc_limit(user_id: int) -> int:
    role = auth.get_user_role(user_id)
    base = LIMITS.get(role, LIMITS["free"])
    return base + get_user_credits(user_id)

# ══════════════════════════════════════════════════════════════════════════════
#  PROXY STORAGE
# ══════════════════════════════════════════════════════════════════════════════

_proxy_cache: dict | None = None
_proxy_cache_mtime: float = 0.0
MAX_PROXIES_PER_USER = 30

def _load_proxies() -> dict:
    global _proxy_cache, _proxy_cache_mtime
    try:
        mt = os.path.getmtime(PROXY_FILE)
    except OSError:
        return {}
    if _proxy_cache is not None and mt == _proxy_cache_mtime:
        return _proxy_cache
    try:
        with open(PROXY_FILE, "r", encoding="utf-8") as f:
            _proxy_cache = json.load(f)
            _proxy_cache_mtime = mt
            return _proxy_cache
    except Exception:
        return {}

def _save_proxies(data: dict):
    global _proxy_cache, _proxy_cache_mtime
    with open(PROXY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    _proxy_cache = data
    try:
        _proxy_cache_mtime = os.path.getmtime(PROXY_FILE)
    except OSError:
        _proxy_cache_mtime = 0.0

def get_user_proxies(user_id: int) -> list:
    data = _load_proxies()
    proxies = data.get(str(user_id), [])
    if isinstance(proxies, dict):
        proxies = [proxies] if proxies else []
    if isinstance(proxies, str):
        proxies = [proxies] if proxies.strip() else []
    out = []
    for p in proxies:
        if isinstance(p, dict):
            out.append(p)
        elif isinstance(p, str) and p.strip():
            parsed = parse_proxy_format(p.strip())
            if parsed:
                out.append(parsed)
    return out

def get_user_proxy(user_id: int) -> dict | None:
    proxies = get_user_proxies(user_id)
    return random.choice(proxies) if proxies else None

def add_user_proxies(user_id: int, new_proxies: list[dict]):
    data = _load_proxies()
    existing = data.get(str(user_id), [])
    if isinstance(existing, dict):
        existing = [existing] if existing else []
    existing.extend(new_proxies)
    data[str(user_id)] = existing[:MAX_PROXIES_PER_USER]
    _save_proxies(data)

def del_user_proxy(user_id: int):
    data = _load_proxies()
    data.pop(str(user_id), None)
    _save_proxies(data)

# ══════════════════════════════════════════════════════════════════════════════
#  SITES LIST
# ══════════════════════════════════════════════════════════════════════════════

_sites_cache: list[str] | None = None
_sites_cache_mtime: float = 0.0

def _load_sites() -> list[str]:
    global _sites_cache, _sites_cache_mtime
    try:
        mt = os.path.getmtime(SITES_FILE)
    except OSError:
        return []
    if _sites_cache is not None and mt == _sites_cache_mtime:
        return _sites_cache
    try:
        with open(SITES_FILE, "r", encoding="utf-8") as f:
            urls = [l.strip().rstrip("/") for l in f if l.strip()]
        seen = set()
        deduped = []
        for u in urls:
            if u not in seen:
                seen.add(u)
                deduped.append(u)
        _sites_cache = deduped
        _sites_cache_mtime = mt
        return deduped
    except Exception:
        return []

def get_random_site() -> str | None:
    sites = _load_sites()
    return random.choice(sites) if sites else None

# ══════════════════════════════════════════════════════════════════════════════
#  BOT + DISPATCHER
# ══════════════════════════════════════════════════════════════════════════════

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher()
router = Router()
dp.include_router(router)

# ══════════════════════════════════════════════════════════════════════════════
#  SAFE EDIT
# ══════════════════════════════════════════════════════════════════════════════

async def safe_edit(msg: types.Message, text: str, **kwargs) -> bool:
    for attempt in range(2):
        try:
            await msg.edit_text(text, **kwargs)
            return True
        except TelegramRetryAfter as e:
            wait = min(e.retry_after + 1, 15)
            await asyncio.sleep(wait)
        except TelegramBadRequest as e:
            emsg = str(e).lower()
            if "message is not modified" in emsg:
                return True
            if any(x in emsg for x in (
                "message can't be edited", "message to edit not found",
                "chat not found", "message_id_invalid",
            )):
                return False
            return False
        except TelegramForbiddenError:
            return False
        except TelegramNotFound:
            return False
        except Exception:
            return False
    return False

# ══════════════════════════════════════════════════════════════════════════════
#  GLOBAL ERROR HANDLER
# ══════════════════════════════════════════════════════════════════════════════

@dp.errors()
async def global_error_handler(event: types.ErrorEvent):
    exc = event.exception
    if isinstance(exc, TelegramRetryAfter):
        await asyncio.sleep(exc.retry_after + 1)
        return True
    if isinstance(exc, TelegramForbiddenError):
        return True
    log.error("Unhandled exception: %s", exc, exc_info=True)
    return True

# ══════════════════════════════════════════════════════════════════════════════
#  THROTTLE MIDDLEWARE
# ══════════════════════════════════════════════════════════════════════════════

from aiogram import BaseMiddleware as _BaseMiddleware

class _ThrottleMiddleware(_BaseMiddleware):
    _RATE = 0.4
    _AUTO_BAN_WINDOW = 10.0
    _AUTO_BAN_LIMIT = 20
    _last: dict[int, float] = {}
    _window: dict[int, list[float]] = {}

    async def __call__(self, handler, event, data):
        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)
        uid = user.id
        if is_banned(uid):
            return
        now = time.monotonic()
        times = self._window.get(uid, [])
        times = [t for t in times if now - t < self._AUTO_BAN_WINDOW]
        times.append(now)
        self._window[uid] = times
        if len(times) >= self._AUTO_BAN_LIMIT:
            ban_user(uid)
            return
        last = self._last.get(uid, 0.0)
        diff = now - last
        if diff < self._RATE:
            await asyncio.sleep(self._RATE - diff)
        self._last[uid] = time.monotonic()
        return await handler(event, data)

dp.message.middleware(_ThrottleMiddleware())
dp.callback_query.middleware(_ThrottleMiddleware())

# ══════════════════════════════════════════════════════════════════════════════
#  JOIN CHECK
# ══════════════════════════════════════════════════════════════════════════════

_join_cache: dict[int, tuple[bool, float]] = {}
_JOIN_CACHE_TTL_OK = 300
_JOIN_CACHE_TTL_NO = 30

async def check_user_joined(user_id: int, force: bool = False) -> bool:
    return True

def join_keyboard() -> dict:
    return {
        "inline_keyboard": [
            [{"text": bold("Join Channel"), "url": CHANNEL_LINK},
             {"text": bold("Join Group"), "url": GROUP_LINK}],
            [{"text": bold("✅ Verify Joined"), "callback_data": "verify_join"}],
        ]
    }

JOIN_MSG = (
    f"{pe(E['warn'])} {bold('Access Restricted')}\n\n"
    f"{pe(E['bolt'])} {bold('You must join our channel and group to use this bot.')}\n\n"
    f"{pe(E['link'])} {bold('Tap the buttons below to join, then tap Verify.')}"
)

# ══════════════════════════════════════════════════════════════════════════════
#  FORMATTING HELPERS (ELVE GOLD STYLE)
# ══════════════════════════════════════════════════════════════════════════════

def sep() -> str:
    return "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"

def fmt_status(status: str) -> str:
    s = status.lower()
    if "order_placed" in s or "charged" in s or "success" in s:
        return f"{pe(E['charged'])} {bold('Order Placed!')}"
    if any(x in s for x in ["insufficient_funds", "insufficient funds"]):
        return f"{pe(E['approved'])} {bold('Insufficient Funds — CVV Matched!')}"
    if any(x in s for x in ["incorrect_cvc", "invalid_cvc", "incorrect_cvv", "invalid_cvv"]):
        return f"{pe(E['ccn'])} {bold('Incorrect CVC — CCN Matched!')}"
    if "incorrect_zip" in s:
        return f"{pe(E['approved'])} {bold('Incorrect ZIP — Card is Live!')}"
    if any(x in s for x in ["otp_required", "3ds", "authentication_required"]):
        return f"{pe(E['3ds'])} {bold('3DS / OTP Required — Card is Live!')}"
    if any(x in s for x in ["card_declined", "do_not_honor", "declined"]):
        return f"{pe(E['declined'])} {bold('Card Declined')}"
    if "expired" in s:
        return f"{pe(E['dead'])} {bold('Card Expired')}"
    if "risky" in s:
        return f"{pe(E['warn'])} {bold('Flagged as Risky')}"
    if "incorrect_number" in s:
        return f"{pe(E['dead'])} {bold('Incorrect Card Number')}"
    return f"{pe(E['unknown'])} {bold(status[:60])}"

def fmt_result(cc: str, gate: str, site: str, amount: str, code: str, bin_info: dict, user_id: int, user_name: str, user_uname: str) -> str:
    brand = bin_info.get("brand", "-")
    be = ""
    bl = brand.upper()
    if "VISA" in bl:
        be = pe(E["visa"]) + " "
    elif "MASTER" in bl:
        be = pe(E["master"]) + " "
    elif "AMEX" in bl or "AMERICAN" in bl:
        be = pe(E["amex"]) + " "

    return (
        f"{fmt_status(code)}\n"
        f"{sep()}\n"
        f"{pe(E['card'])} {bold('Card →')} <tg-spoiler>{cc}</tg-spoiler>\n"
        f"{pe(E['gate'])} {bold('Gate →')} {bold(gate.upper())}\n"
        f"{pe(E['site'])} {bold('Site →')} {bold(site)}\n"
        f"{pe(E['amount'])} {bold('Amount →')} {bold(amount)}\n"
        f"{pe(E['code'])} {bold('Code →')} {bold(code.upper())}\n"
        f"{sep()}\n"
        f"{pe(E['bin'])} {bold('BIN →')} {be}{bold(bin_info.get('brand','-'))}\n"
        f"{pe(E['type'])} {bold('Type →')} {bold(bin_info.get('type','-'))} {bold(bin_info.get('level','-'))}\n"
        f"{pe(E['bank'])} {bold('Bank →')} {bold(bin_info.get('bank','-'))}\n"
        f"{pe(E['country'])} {bold('Country →')} {bin_info.get('flag','')} {bold(bin_info.get('country','-'))}\n"
        f"{sep()}\n"
        f"{pe(E['user'])} {bold('User →')} {user_link(user_id, user_name, user_uname)}\n"
        f"{pe(E['link'])} {italic(POWERED_BY)}"
    )

def user_link(user_id: int, name: str = "", username: str = "") -> str:
    if name:
        display = _html.escape(name)
    elif username:
        display = f"@{_html.escape(username)}"
    else:
        display = str(user_id)
    if username:
        url = f"https://t.me/{_html.escape(username)}"
    else:
        url = f"tg://user?id={user_id}"
    return f'<a href="{url}">{display}</a>'

def progress_bar(pct: float, width: int = 20) -> str:
    filled = int(width * pct / 100)
    bar = "█" * filled + "░" * (width - filled)
    return f"{bar} {pct:.1f}%"

def fmt_time(seconds: int) -> str:
    return f"{seconds // 3600:02d}:{(seconds % 3600) // 60:02d}:{seconds % 60:02d}"

# ══════════════════════════════════════════════════════════════════════════════
#  WELCOME / START
# ══════════════════════════════════════════════════════════════════════════════

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    uid = message.from_user.id
    is_new = auth.save_user(uid, message.from_user.username, message.from_user.full_name)
    joined = await check_user_joined(uid)
    if not joined:
        await message.reply(JOIN_MSG, reply_markup=join_keyboard())
        return
    if is_banned(uid):
        await message.reply(f"{pe(E['cross'])} {bold('You are banned from this bot!')}")
        return
    role = auth.get_user_role(uid)
    limit = get_cc_limit(uid)
    role_display = role.upper() if role else "FREE"

    text = (
        f"{pe(E['welcome'])} {italic(BOT_NAME)}\n\n"
        f"{pe(E['user'])} {italic('Welcome,')} {user_link(uid, message.from_user.full_name, message.from_user.username)}\n\n"
        f"{pe(E['crown'])} {bold('Role →')} {bold(role_display)}\n"
        f"{pe(E['card'])} {bold('CC Limit →')} {bold(str(limit))}\n"
        f"{pe(E['access'])} {bold('Access →')} {bold('Basic' if role == 'free' else 'Premium')}\n\n"
        f"{pe(E['commands'])} {bold('Commands')}\n"
        f"{pe(E['bolt'])} /sc — single card check\n"
        f"{pe(E['rocket'])} /msc — mass check (inline)\n"
        f"{pe(E['file'])} /msctxt — mass check (.txt file)\n"
        f"{pe(E['gate'])} /st — woocommerce check\n"
        f"...\n\n"
        f"{pe(E['link'])} {italic(POWERED_BY)}"
    )
    await message.reply(text)

@router.callback_query(F.data == "verify_join")
async def cb_verify_join(callback: types.CallbackQuery):
    joined = await check_user_joined(callback.from_user.id, force=True)
    if not joined:
        await callback.answer(bold("You have not joined yet! Join both first."), show_alert=True)
        return
    await callback.answer(bold("Verified! Welcome!"))
    await cmd_start(callback.message)

# ══════════════════════════════════════════════════════════════════════════════
#  /me PROFILE
# ══════════════════════════════════════════════════════════════════════════════

@router.message(Command("me"))
async def cmd_me(message: types.Message):
    uid = message.from_user.id
    joined = await check_user_joined(uid)
    if not joined:
        await message.reply(JOIN_MSG, reply_markup=join_keyboard())
        return
    uname = message.from_user.full_name or "Unknown"
    username = message.from_user.username or "none"
    role = auth.get_user_role(uid)
    limit = get_cc_limit(uid)
    expiry = auth.get_premium_expiry(uid)
    proxies = get_user_proxies(uid)

    role_line = bold(role.upper()) if role else bold("FREE")
    proxy_line = f"{bold(str(len(proxies)))} proxies set" if proxies else bold("Not Set")

    text = (
        f"{pe(E['profile'])} {bold('User Profile')}\n\n"
        f"{pe(E['user'])} {bold('Name →')} {user_link(uid, uname, username)}\n"
        f"{pe(E['info'])} {bold('ID →')} {bold(str(uid))}\n"
        f"{sep()}\n"
        f"{pe(E['crown'])} {bold('Role →')} {role_line}\n"
        f"{pe(E['card'])} {bold('CC Limit →')} {bold(str(limit))}\n"
        f"{pe(E['access'])} {bold('Expiry →')} {bold(expiry or 'N/A')}\n"
        f"{sep()}\n"
        f"{pe(E['globe'])} {bold('Proxy →')} {proxy_line}\n\n"
        f"{pe(E['link'])} {italic(POWERED_BY)}"
    )
    await message.reply(text)

# ══════════════════════════════════════════════════════════════════════════════
#  /cmds HELP
# ══════════════════════════════════════════════════════════════════════════════

@router.message(Command("cmds", "help"))
async def cmd_help(message: types.Message):
    uid = message.from_user.id
    joined = await check_user_joined(uid)
    if not joined:
        await message.reply(JOIN_MSG, reply_markup=join_keyboard())
        return

    text = (
        f"{pe(E['commands'])} {bold('Command List')}\n\n"
        f"{pe(E['bolt'])} /sc cc|mm|yy|cvv — {bold('Single check')}\n"
        f"{pe(E['rocket'])} /msc cc... — {bold('Mass inline')}\n"
        f"{pe(E['file'])} /msctxt — {bold('File check (.txt)')}\n\n"
        f"{pe(E['star'])} {bold('Premium Gates:')}\n"
        f"{pe(E['gate'])} /st /mst /stxt — {bold('WooCommerce')}\n"
        f"{pe(E['gate'])} /rz /mrz /rztxt — {bold('Razorpay')}\n"
        f"{pe(E['gate'])} /st1 /mst1 /st1txt — {bold('Stripe $1')}\n"
        f"{pe(E['gate'])} /chk /mchk /chktxt — {bold('Stripe Auth')}\n"
        f"{pe(E['gate'])} /vbv /mvbv — {bold('Braintree VBV')}\n"
        f"{pe(E['gate'])} /br /mbr /brtxt — {bold('Braintree Auth')}\n"
        f"{pe(E['gate'])} /b3 /mb3 /b3txt — {bold('B3 Auth')}\n"
        f"{pe(E['gate'])} /hit — {bold('Stripe Checkout')}\n"
        f"{pe(E['gate'])} /skcvv /mskcvv /sktxt — {bold('Stripe SK')}\n"
        f"{pe(E['gate'])} /gate — {bold('Gateway Lookup')}\n\n"
        f"{pe(E['link'])} {bold('Tools:')}\n"
        f"{pe(E['bin'])} /bin — {bold('BIN lookup')}\n"
        f"{pe(E['proxy'])} /proxy /myproxy /rmproxy — {bold('Proxy')}\n"
        f"{pe(E['key'])} /redeem — {bold('Redeem key')}\n"
        f"{pe(E['dork'])} /dork — {bold('URL scraper')}\n\n"
        f"{pe(E['link'])} {italic(POWERED_BY)}"
    )
    await message.reply(text)

# ══════════════════════════════════════════════════════════════════════════════
#  /proxy /myproxy /rmproxy
# ══════════════════════════════════════════════════════════════════════════════

@router.message(Command("proxy"))
async def cmd_proxy(message: types.Message):
    uid = message.from_user.id
    joined = await check_user_joined(uid)
    if not joined:
        await message.reply(JOIN_MSG, reply_markup=join_keyboard())
        return

    args = message.text.split(maxsplit=1)
    raw_text = ""
    if len(args) >= 2:
        raw_text = args[1]
    if message.reply_to_message:
        reply_txt = message.reply_to_message.text or message.reply_to_message.caption or ""
        if reply_txt.strip():
            raw_text = raw_text + "\n" + reply_txt if raw_text else reply_txt
        if message.reply_to_message.document:
            doc = message.reply_to_message.document
            if doc.file_name and doc.file_name.lower().endswith(".txt"):
                try:
                    buf = BytesIO()
                    await bot.download(doc.file_id, destination=buf)
                    buf.seek(0)
                    file_text = buf.read().decode("utf-8", errors="ignore")
                    if file_text.strip():
                        raw_text = raw_text + "\n" + file_text if raw_text else file_text
                except Exception as e:
                    log.error(f"Failed to download proxy file: {e}")

    if not raw_text.strip():
        await message.reply(
            f"{pe(E['warn'])} {bold('Usage:')}\n"
            f"{pe(E['next'])} /proxy host:port:user:pass\n"
            f"{pe(E['next'])} Or reply to a .txt file\n\n"
            f"{pe(E['star'])} {bold('Max')} {bold(str(MAX_PROXIES_PER_USER))} {bold('proxies per user.')}"
        )
        return

    parsed_list = []
    for line in raw_text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        parsed = parse_proxy_format(line)
        if parsed:
            parsed_list.append(parsed)

    if not parsed_list:
        await message.reply(f"{pe(E['cross'])} {bold('No valid proxies found!')}")
        return

    need = MAX_PROXIES_PER_USER - len(get_user_proxies(uid))
    if need <= 0:
        await message.reply(
            f"{pe(E['warn'])} {bold('Proxy list full!')} {bold(str(MAX_PROXIES_PER_USER))}/{bold(str(MAX_PROXIES_PER_USER))}\n"
            f"{pe(E['next'])} Use /rmproxy to clear."
        )
        return

    status_msg = await message.reply(
        f"{pe(E['loading'])} {bold('Testing proxies...')}\n"
        f"{pe(E['hourglass'])} Parsed: {bold(str(len(parsed_list)))} | Testing in batches..."
    )

    working = []
    dead = 0
    TEST_BATCH = 10
    stopped_early = False

    for batch_start in range(0, len(parsed_list), TEST_BATCH):
        if len(working) >= need:
            stopped_early = True
            break
        batch = parsed_list[batch_start:batch_start + TEST_BATCH]

        async def _test_one(proxy_data):
            try:
                success, _, _ = await test_proxy(proxy_data["proxy_url"])
                return proxy_data if success else None
            except Exception:
                return None

        results = await asyncio.gather(*[_test_one(p) for p in batch])
        for r in results:
            if r is not None and len(working) < need:
                working.append(r)
            elif r is None:
                dead += 1

        try:
            await safe_edit(status_msg,
                f"{pe(E['loading'])} {bold('Testing proxies...')}\n"
                f"{pe(E['check'])} Working: {bold(str(len(working)))}/{bold(str(need))}\n"
                f"{pe(E['cross'])} Dead: {bold(str(dead))}"
            )
        except Exception:
            pass

    if not working:
        await safe_edit(status_msg, f"{pe(E['cross'])} {bold('All proxies are dead!')}")
        return

    add_user_proxies(uid, working)
    total = len(get_user_proxies(uid))

    result_lines = [
        f"{pe(E['check'])} {bold('Proxy Testing Complete!')}\n",
        f"{pe(E['bolt'])} Working: {bold(str(len(working)))}",
        f"{pe(E['cross'])} Dead: {bold(str(dead))}",
    ]
    if stopped_early:
        result_lines.append(f"{pe(E['star'])} Stopped early — reached {bold(str(need))} limit.")
    result_lines.append(f"{pe(E['star'])} Total saved: {bold(str(total))}/{bold(str(MAX_PROXIES_PER_USER))}")
    result_lines.append(f"\n{pe(E['link'])} {italic(POWERED_BY)}")

    await safe_edit(status_msg, "\n".join(result_lines))

@router.message(Command("myproxy"))
async def cmd_myproxy(message: types.Message):
    uid = message.from_user.id
    joined = await check_user_joined(uid)
    if not joined:
        await message.reply(JOIN_MSG, reply_markup=join_keyboard())
        return
    proxy_list = get_user_proxies(uid)
    if not proxy_list:
        await message.reply(
            f"{pe(E['cross'])} {bold('No Proxies Set!')}\n"
            f"{pe(E['next'])} Use /proxy host:port:user:pass"
        )
        return
    lines = [f"{pe(E['link'])} {bold('Your Proxies')} [{bold(str(len(proxy_list)))}/{bold(str(MAX_PROXIES_PER_USER))}]\n"]
    for i, p in enumerate(proxy_list[:10], 1):
        ip = p.get('ip', '-')
        port = p.get('port', '-')
        ptype = p.get('type', 'http').upper()
        lines.append(f"{pe(E['bolt'])} {bold(str(i))}. {bold(ip)}:{bold(port)} ({bold(ptype)})")
    if len(proxy_list) > 10:
        lines.append(f"{pe(E['next'])} ... {bold(str(len(proxy_list) - 10))} more")
    lines.append(f"\n{pe(E['link'])} {italic(POWERED_BY)}")
    await message.reply("\n".join(lines))

@router.message(Command("rmproxy"))
async def cmd_rmproxy(message: types.Message):
    uid = message.from_user.id
    joined = await check_user_joined(uid)
    if not joined:
        await message.reply(JOIN_MSG, reply_markup=join_keyboard())
        return
    proxy_list = get_user_proxies(uid)
    if not proxy_list:
        await message.reply(f"{pe(E['warn'])} {bold('No proxies to remove!')}")
        return
    count = len(proxy_list)
    del_user_proxy(uid)
    await message.reply(
        f"{pe(E['check'])} {bold('All')} {bold(str(count))} {bold('proxies removed!')}\n"
        f"{pe(E['link'])} {italic(POWERED_BY)}"
    )

# ══════════════════════════════════════════════════════════════════════════════
#  /bin BIN LOOKUP
# ══════════════════════════════════════════════════════════════════════════════

@router.message(Command("bin"))
async def cmd_bin(message: types.Message):
    joined = await check_user_joined(message.from_user.id)
    if not joined:
        await message.reply(JOIN_MSG, reply_markup=join_keyboard())
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply(f"{pe(E['warn'])} {bold('Usage:')} /bin 438854")
        return
    bin_num = re.sub(r'\D', '', args[1].strip())[:6]
    if len(bin_num) < 6:
        await message.reply(f"{pe(E['cross'])} {bold('BIN must be at least 6 digits!')}")
        return

    loading_msg = await message.reply(
        f"{pe(E['loading'])} {bold('Looking up BIN')} {bold(bin_num)}..."
    )
    info = await bin_lookup(bin_num)

    await safe_edit(loading_msg,
        f"{pe(E['globe'])} {bold('BIN Lookup Result')}\n\n"
        f"{pe(E['bin'])} {bold('BIN →')} {bold(bin_num)}\n"
        f"{pe(E['card'])} {bold('Brand →')} {bold(info['brand'])}\n"
        f"{pe(E['type'])} {bold('Type →')} {bold(info['type'])}\n"
        f"{pe(E['bank'])} {bold('Bank →')} {bold(info['bank'])}\n"
        f"{pe(E['country'])} {bold('Country →')} {info['flag']} {bold(info['country'])}\n\n"
        f"{pe(E['link'])} {italic(POWERED_BY)}"
    )

# ══════════════════════════════════════════════════════════════════════════════
#  /dork BRAVE SEARCH
# ══════════════════════════════════════════════════════════════════════════════

@router.message(Command("dork"))
async def cmd_dork(message: types.Message):
    uid = message.from_user.id
    joined = await check_user_joined(uid)
    if not joined:
        await message.reply(JOIN_MSG, reply_markup=join_keyboard())
        return
    if is_banned(uid):
        await message.reply(f"{pe(E['cross'])} {bold('You are banned!')}")
        return
    if not _DORK_AVAILABLE:
        await message.reply(f"{pe(E['warn'])} {bold('Dork module not available.')}")
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip():
        await message.reply(
            f"{pe(E['dork'])} {bold('Usage:')} /dork keyword\n"
            f"{pe(E['next'])} Example: /dork shopify checkout"
        )
        return
    query = args[1].strip()
    proxy_list = get_user_proxies(uid)
    if not proxy_list:
        await message.reply(
            f"{pe(E['warn'])} {bold('No proxy set!')}\n"
            f"{pe(E['next'])} Add one with /proxy"
        )
        return
    proxy_data = random.choice(proxy_list)
    proxy_str = proxy_dict_to_url(proxy_data)

    wait_msg = await message.reply(
        f"{pe(E['loading'])} {bold('Scraping Brave Search...')}\n"
        f"{pe(E['dork'])} Query: {bold(query)}"
    )

    try:
        urls = await _dork_mod.scrape_dork(query, proxy=proxy_str)
    except Exception as exc:
        await safe_edit(wait_msg, f"{pe(E['cross'])} {bold('Scrape error:')} {bold(str(exc)[:200])}")
        return

    if not urls:
        await safe_edit(wait_msg, f"{pe(E['cross'])} {bold('No URLs found.')}")
        return

    content = "\n".join(urls) + "\n"
    safe_query = re.sub(r'[^\w\s-]', '', query).strip().replace(' ', '_')[:30]
    fname = f"dork_{safe_query}.txt"

    try:
        await wait_msg.delete()
    except Exception:
        pass

    await bot.send_document(
        uid,
        types.BufferedInputFile(content.encode("utf-8"), filename=fname),
        caption=(
            f"{pe(E['dork'])} {bold('Dork Results')}\n"
            f"{pe(E['check'])} {bold(str(len(urls)))} URLs scraped\n\n"
            f"{pe(E['link'])} {italic(POWERED_BY)}"
        ),
    )

# ══════════════════════════════════════════════════════════════════════════════
#  CORE CHECKER HELPERS
# ══════════════════════════════════════════════════════════════════════════════

CHECKER_POOL = concurrent.futures.ThreadPoolExecutor(max_workers=500)
_USER_SEM_LIMIT = 100
_user_semaphores: dict[int, asyncio.Semaphore] = {}

def get_user_semaphore(user_id: int) -> asyncio.Semaphore:
    if user_id not in _user_semaphores:
        _user_semaphores[user_id] = asyncio.Semaphore(_USER_SEM_LIMIT)
    return _user_semaphores[user_id]

_ANTISPAM_COOLDOWN = 20
_user_last_cmd: dict[int, float] = {}

def check_cooldown(user_id: int) -> float:
    if auth.is_admin(user_id):
        return 0.0
    last = _user_last_cmd.get(user_id, 0)
    elapsed = time.time() - last
    if elapsed < _ANTISPAM_COOLDOWN:
        return _ANTISPAM_COOLDOWN - elapsed
    return 0.0

def set_cooldown(user_id: int):
    _user_last_cmd[user_id] = time.time()

async def _send_approved(text: str) -> None:
    try:
        await bot.send_message(auth.APPROVED_GROUP_ID, text, disable_notification=True)
    except Exception:
        pass

async def _send_monitor(text: str) -> None:
    try:
        await bot.send_message(auth.MONITOR_GROUP_ID, text, disable_notification=True)
    except Exception:
        pass

# ══════════════════════════════════════════════════════════════════════════════
#  /sc SINGLE SHOPIFY CHECK
# ══════════════════════════════════════════════════════════════════════════════

@router.message(Command("sc"))
async def cmd_sc(message: types.Message):
    uid = message.from_user.id
    joined = await check_user_joined(uid)
    if not joined:
        await message.reply(JOIN_MSG, reply_markup=join_keyboard())
        return
    if is_banned(uid):
        return
    if not auth.has_premium_access(uid, message.chat.id):
        await message.reply(
            f"{pe(E['cross'])} {bold('Premium Access Required!')}\n"
            f"{pe(E['bolt'])} Contact admin or redeem a key.\n"
            f"{pe(E['next'])} /redeem KEY"
        )
        return

    rem = check_cooldown(uid)
    if rem > 0:
        await message.reply(f"{pe(E['warn'])} {bold('Slow down!')} Wait {bold(f'{rem:.0f}s')}")
        return

    cc_str = None
    args = message.text.split(maxsplit=1)
    if len(args) >= 2:
        cc_str = extract_cc(args[1])
        if not cc_str:
            parts = re.split(r'[|/]', args[1].strip())
            if len(parts) >= 4:
                cc_str = "|".join(p.strip() for p in parts[:4])
    if not cc_str and message.reply_to_message:
        cc_str = extract_cc(message.reply_to_message.text or "")
    if not cc_str:
        await message.reply(
            f"{pe(E['warn'])} {bold('No CC found!')}\n"
            f"{pe(E['next'])} /sc 438854|03|2030|815"
        )
        return

    proxy_data = get_user_proxy(uid)
    if not proxy_data:
        await message.reply(
            f"{pe(E['cross'])} {bold('No Proxy Set!')}\n"
            f"{pe(E['next'])} Use /proxy host:port:user:pass"
        )
        return

    site = get_random_site()
    if not site:
        await message.reply(f"{pe(E['cross'])} {bold('No sites available!')}")
        return

    set_cooldown(uid)
    cc_number = cc_str.split("|")[0]
    bin_num = cc_number[:6]

    loading_msg = await message.reply(
        f"{pe(E['loading'])} {bold('Checking CC...')}\n"
        f"{pe(E['card'])} {bold('CC:')} <tg-spoiler>{cc_str}</tg-spoiler>\n"
        f"{pe(E['site'])} {bold('Site:')} {bold(site.split('//')[1][:30] if '//' in site else site[:30])}"
    )

    _chk = asyncio.create_task(checker_bridge.check_card_site(cc_str, site, proxy_data))
    _bin = asyncio.create_task(bin_lookup(bin_num))
    try:
        result = await _chk
    except Exception as e:
        result = {"Response": str(e)[:80], "Price": "-", "Gate": "-", "Status": "Error"}
    bin_info = await _bin

    response = result.get("Response", "Unknown")
    price = result.get("Price", "-")
    gate = result.get("Gate", "-")

    result_text = fmt_result(
        cc_str, gate, site.split('//')[1] if '//' in site else site,
        str(price), response, bin_info, uid,
        message.from_user.full_name or "", message.from_user.username or ""
    )

    await safe_edit(loading_msg, result_text)

    rl = response.lower()
    if any(k in rl for k in ["order_placed", "charged", "success"]):
        auth.save_charged_cc(cc_str, uid, message.from_user.full_name or "Unknown", gate, str(price))
        try:
            await bot.pin_chat_message(message.chat.id, loading_msg.message_id, disable_notification=True)
        except Exception:
            pass
        await _send_monitor(result_text)
    elif any(k in rl for k in ["insufficient_funds", "insufficient funds", "incorrect_cvc", "invalid_cvc", "incorrect_zip", "otp_required", "3ds"]):
        await _send_approved(result_text)

# ══════════════════════════════════════════════════════════════════════════════
#  /msc MASS SHOPIFY CHECK
# ══════════════════════════════════════════════════════════════════════════════

_MSC_EDIT_LOCKS: dict[int, asyncio.Lock] = {}

async def _msc_check_single(cc_str, proxy_data, sites_list, status_msg, results, order, uid, uname, uuser):
    site = random.choice(sites_list) if sites_list else get_random_site()
    if not site:
        results[cc_str] = {"result": {"Response": "No sites", "Gate": "-", "Price": "-"}, "bin": {"brand":"-","type":"-","level":"-","bank":"-","country":"-","flag":"🏳️"}}
        return
    bin_num = cc_str.split("|")[0][:6]
    _bin = asyncio.create_task(bin_lookup(bin_num))
    sem = get_user_semaphore(uid)
    async with sem:
        try:
            result = await checker_bridge.check_card_site(cc_str, site, proxy_data)
        except Exception as e:
            result = {"Response": str(e)[:80], "Price": "-", "Gate": "-", "Status": "Error"}
    bin_info = await _bin
    results[cc_str] = {"result": result, "bin": bin_info}

    msg_id = status_msg.message_id
    if msg_id not in _MSC_EDIT_LOCKS:
        _MSC_EDIT_LOCKS[msg_id] = asyncio.Lock()

    async with _MSC_EDIT_LOCKS[msg_id]:
        done = sum(1 for cc in order if cc in results)
        total = len(order)
        lines = [f"{pe(E['rocket'])} {bold('Mass Check')} [{bold(str(done))}/{bold(str(total))}]\n"]
        for cc in order:
            if cc in results:
                entry = results[cc]
                resp = entry["result"].get("Response", "Unknown")
                lines.append(
                    f"{fmt_status(resp)}\n"
                    f"{pe(E['card'])} <tg-spoiler>{cc}</tg-spoiler>"
                )
            else:
                lines.append(f"{pe(E['loading'])} <tg-spoiler>{cc}</tg-spoiler> {bold('checking...')}")
        lines.append(f"\n{pe(E['user'])} {bold('Checked by:')} {user_link(uid, uname, uuser)}")
        lines.append(f"{pe(E['link'])} {italic(POWERED_BY)}")
        try:
            await safe_edit(status_msg, "\n\n".join(lines))
        except Exception:
            pass

    if done >= total:
        _MSC_EDIT_LOCKS.pop(msg_id, None)

@router.message(Command("msc"))
async def cmd_msc(message: types.Message):
    uid = message.from_user.id
    joined = await check_user_joined(uid)
    if not joined:
        await message.reply(JOIN_MSG, reply_markup=join_keyboard())
        return
    if is_banned(uid):
        return
    if not auth.has_premium_access(uid, message.chat.id):
        await message.reply(f"{pe(E['cross'])} {bold('Premium Access Required!')}")
        return
    rem = check_cooldown(uid)
    if rem > 0:
        await message.reply(f"{pe(E['warn'])} {bold('Slow down!')} Wait {bold(f'{rem:.0f}s')}")
        return

    raw_text = ""
    args = message.text.split(maxsplit=1)
    if len(args) >= 2:
        raw_text = args[1]
    if message.reply_to_message:
        raw_text = raw_text + "\n" + (message.reply_to_message.text or "") if raw_text else (message.reply_to_message.text or "")
    if not raw_text.strip():
        await message.reply(f"{pe(E['warn'])} {bold('No CCs found!')}")
        return

    from helpers import CC_PATTERN
    all_ccs = []
    seen = set()
    for m in CC_PATTERN.finditer(raw_text):
        cc = f"{m.group(1)}|{m.group(2)}|{m.group(3)}|{m.group(4)}"
        if cc not in seen:
            seen.add(cc)
            all_ccs.append(cc)
    if not all_ccs:
        for line in raw_text.strip().splitlines():
            parts = re.split(r'[|/]', line.strip())
            if len(parts) >= 4:
                cc = "|".join(p.strip() for p in parts[:4])
                if cc not in seen:
                    seen.add(cc)
                    all_ccs.append(cc)
    if not all_ccs:
        await message.reply(f"{pe(E['cross'])} {bold('No valid CCs found!')}")
        return

    limit = get_cc_limit(uid)
    if len(all_ccs) > limit:
        all_ccs = all_ccs[:limit]

    proxy_data = get_user_proxy(uid)
    if not proxy_data:
        await message.reply(f"{pe(E['cross'])} {bold('No Proxy Set!')}")
        return
    sites_list = _load_sites()
    if not sites_list:
        await message.reply(f"{pe(E['cross'])} {bold('No sites available!')}")
        return

    set_cooldown(uid)
    total = len(all_ccs)
    init_lines = [f"{pe(E['rocket'])} {bold('Mass Check')} [0/{total}]\n"]
    for cc in all_ccs:
        init_lines.append(f"{pe(E['loading'])} <tg-spoiler>{cc}</tg-spoiler> {bold('checking...')}")
    init_lines.append(f"\n{pe(E['user'])} {bold('Checked by:')} {user_link(uid, message.from_user.full_name or '', message.from_user.username or '')}")
    init_lines.append(f"{pe(E['link'])} {italic(POWERED_BY)}")

    status_msg = await message.reply("\n\n".join(init_lines))
    results = {}
    order = list(all_ccs)

    tasks = [
        asyncio.create_task(_msc_check_single(
            cc, proxy_data, sites_list, status_msg, results, order,
            uid, message.from_user.full_name or "", message.from_user.username or ""
        )) for cc in all_ccs
    ]
    await asyncio.gather(*tasks, return_exceptions=True)

# ══════════════════════════════════════════════════════════════════════════════
#  FILE CHECK FLOW (/msctxt, /stxt, /rztxt, etc. with /yes /no /stop)
# ══════════════════════════════════════════════════════════════════════════════

_FILE_STOP_FLAGS: dict[str, bool] = {}
_FILE_ACTIVE_USERS: set[int] = set()

async def _process_file_check(
    all_ccs: list, uid: int, uname: str, uuser: str, chat_id: int,
    status_msg: types.Message, stop_key: str, gate_label: str,
    check_fn, proxy_list: list, sites_list: list = None,
    show_approved: bool = True,
):
    total = len(all_ccs)
    checked, charged, approved, declined, errors = 0, 0, 0, 0, 0
    start_time = time.time()
    last_edit = 0.0

    _fc_sem = asyncio.Semaphore(150)  # 150 worker بالتوازي

    async def _fc_one(i, cc):
        nonlocal checked, charged, approved, declined, errors, last_edit
        if _FILE_STOP_FLAGS.get(stop_key):
            return
        async with _fc_sem:
            proxy_data = random.choice(proxy_list) if proxy_list else None
        bin_num = cc.split("|")[0][:6]

        try:
            if gate_label == "Shopify":
                site = random.choice(sites_list) if sites_list else get_random_site()
                result = await checker_bridge.check_card_site(cc, site, proxy_data)
                response = result.get("Response", "Unknown")
                price = result.get("Price", "-")
                gate = result.get("Gate", "-")
            elif gate_label == "WooCommerce":
                site = sites_list[0] if sites_list else ""
                result_str = await asyncio.get_running_loop().run_in_executor(
                    CHECKER_POOL, lambda: st.VW(cc, site, proxy_dict_to_url(proxy_data) if proxy_data else None)
                )
                response = str(result_str)
                price = "-"
                gate = "WooCommerce"
            elif gate_label == "Razorpay":
                site = sites_list[0] if sites_list else ""
                result = await asyncio.get_running_loop().run_in_executor(
                    CHECKER_POOL, lambda: rz.charge_payment_page_card(site, *cc.split("|"), proxy_url=proxy_dict_to_url(proxy_data) if proxy_data else None)
                )
                response = result[1] if isinstance(result, tuple) else str(result)
                price = "-"
                gate = "Razorpay"
            elif gate_label == "Stripe Auth":
                result = await asyncio.get_running_loop().run_in_executor(
                    CHECKER_POOL, lambda: chk.check_card_str(cc)
                )
                response = result[1] if isinstance(result, tuple) else str(result)
                price = "-"
                gate = "Stripe Auth"
            elif gate_label == "Stripe $1":
                result = await asyncio.get_running_loop().run_in_executor(
                    CHECKER_POOL, lambda: st1_gate.check_card_str(cc, proxy_dict_to_url(proxy_data) if proxy_data else None)
                )
                response = result[1] if isinstance(result, tuple) else str(result)
                price = "-"
                gate = "Stripe $1"
            elif gate_label == "Stripe SK":
                sk_entry = _load_skkeys().get(str(uid))
                if not sk_entry:
                    response = "No SK set"
                    price = "-"
                    gate = "Stripe SK"
                else:
                    sk = sk_entry.get("sk", "")
                    result = await asyncio.get_running_loop().run_in_executor(
                        CHECKER_POOL, lambda: _sk_mod.sk_check_card(sk, cc) if _SK_AVAILABLE else ("error", "SK module not loaded")
                    )
                    response = result[1] if isinstance(result, tuple) else str(result)
                    price = "-"
                    gate = "Stripe SK"
            else:
                response = "Unknown gate"
                price = "-"
                gate = gate_label
        except Exception as e:
            response = str(e)[:80]
            price = "-"
            gate = gate_label
            errors += 1

        checked += 1
        rl = response.lower()
        is_charged = any(k in rl for k in ["order_placed", "charged", "success", "card added"])
        is_approved = any(k in rl for k in ["insufficient_funds", "incorrect_cvc", "incorrect_zip", "otp_required", "3ds", "live"])
        is_declined = any(k in rl for k in ["declined", "dead", "incorrect_number", "expired"])

        if is_charged:
            charged += 1
            approved += 1
        elif is_approved:
            approved += 1
        elif is_declined:
            declined += 1
        else:
            errors += 1

        if (is_charged or (is_approved and show_approved)) and not _FILE_STOP_FLAGS.get(stop_key):
            try:
                bin_info = await bin_lookup(bin_num)
                hit_text = fmt_result(cc, gate, "-", str(price), response, bin_info, uid, uname, uuser)
                sent = await bot.send_message(chat_id, hit_text)
                if is_charged:
                    try:
                        await bot.pin_chat_message(chat_id, sent.message_id, disable_notification=True)
                    except Exception:
                        pass
                    await _send_monitor(hit_text)
                else:
                    await _send_approved(hit_text)
            except Exception:
                pass

        now = time.time()
        elapsed = int(now - start_time)
        if now - last_edit >= 3 or checked >= total or _FILE_STOP_FLAGS.get(stop_key):
            last_edit = now
            pct = (checked / total) * 100 if total > 0 else 0
            progress_text = (
                f"{pe(E['loading'])} {bold(gate_label)} {bold('File Check')}\n"
                f"{sep()}\n"
                f"{progress_bar(pct)}\n"
                f"{sep()}\n"
                f"{pe(E['card'])} {bold('Total →')} {bold(str(total))}\n"
                f"{pe(E['checked'])} {bold('Checked →')} {bold(str(checked))}\n"
                f"{pe(E['charged'])} {bold('Charged →')} {bold(str(charged))}\n"
                f"{pe(E['approved'])} {bold('Approved →')} {bold(str(approved))}\n"
                f"{pe(E['declined'])} {bold('Declined →')} {bold(str(declined))}\n"
                f"{pe(E['error'])} {bold('Errors →')} {bold(str(errors))}\n"
                f"{sep()}\n"
                f"{pe(E['time'])} {bold('Elapsed →')} {bold(fmt_time(elapsed))}\n"
                f"{pe(E['link'])} {italic(POWERED_BY)}"
            )
            try:
                await safe_edit(status_msg, progress_text)
            except Exception:
                pass

    await asyncio.gather(*[_fc_one(i, cc) for i, cc in enumerate(all_ccs)], return_exceptions=True)
    _FILE_ACTIVE_USERS.discard(uid)
    _FILE_STOP_FLAGS.pop(stop_key, None)

    elapsed = int(time.time() - start_time)
    final_text = (
        f"{pe(E['check'])} {bold(gate_label)} {bold('File Check Complete!')}\n"
        f"{sep()}\n"
        f"{pe(E['card'])} {bold('Total →')} {bold(str(total))}\n"
        f"{pe(E['checked'])} {bold('Checked →')} {bold(str(checked))}\n"
        f"{pe(E['charged'])} {bold('Charged →')} {bold(str(charged))}\n"
        f"{pe(E['approved'])} {bold('Approved →')} {bold(str(approved))}\n"
        f"{pe(E['declined'])} {bold('Declined →')} {bold(str(declined))}\n"
        f"{pe(E['error'])} {bold('Errors →')} {bold(str(errors))}\n"
        f"{sep()}\n"
        f"{pe(E['time'])} {bold('Time →')} {bold(fmt_time(elapsed))}\n"
        f"{pe(E['link'])} {italic(POWERED_BY)}"
    )
    try:
        await safe_edit(status_msg, final_text)
    except Exception:
        pass

# ══════════════════════════════════════════════════════════════════════════════
#  /msctxt SHOPIFY FILE CHECK
# ══════════════════════════════════════════════════════════════════════════════

@router.message(Command("msctxt"))
async def cmd_msctxt(message: types.Message):
    uid = message.from_user.id
    joined = await check_user_joined(uid)
    if not joined:
        await message.reply(JOIN_MSG, reply_markup=join_keyboard())
        return
    if is_banned(uid):
        return
    if not auth.has_premium_access(uid, message.chat.id):
        await message.reply(f"{pe(E['cross'])} {bold('Premium Access Required!')}")
        return
    if not message.reply_to_message or not message.reply_to_message.document:
        await message.reply(
            f"{pe(E['warn'])} {bold('Usage:')} Send a .txt file and reply with /msctxt"
        )
        return

    doc = message.reply_to_message.document
    if not doc.file_name or not doc.file_name.lower().endswith(".txt"):
        await message.reply(f"{pe(E['cross'])} {bold('Only .txt files!')}")
        return

    try:
        buf = BytesIO()
        await bot.download(doc.file_id, destination=buf)
        buf.seek(0)
        file_text = buf.read().decode("utf-8", errors="ignore")
    except Exception:
        await message.reply(f"{pe(E['cross'])} {bold('Failed to download file!')}")
        return

    from helpers import CC_PATTERN
    all_ccs = []
    seen = set()
    for m in CC_PATTERN.finditer(file_text):
        cc = f"{m.group(1)}|{m.group(2)}|{m.group(3)}|{m.group(4)}"
        if cc not in seen:
            seen.add(cc)
            all_ccs.append(cc)
    if not all_ccs:
        for line in file_text.strip().splitlines():
            parts = re.split(r'[|/]', line.strip())
            if len(parts) >= 4:
                cc = "|".join(p.strip() for p in parts[:4])
                if cc not in seen:
                    seen.add(cc)
                    all_ccs.append(cc)
    if not all_ccs:
        await message.reply(f"{pe(E['cross'])} {bold('No valid CCs found!')}")
        return

    limit = get_cc_limit(uid)
    if len(all_ccs) > limit:
        all_ccs = all_ccs[:limit]

    proxy_list = get_user_proxies(uid)
    if not proxy_list:
        await message.reply(f"{pe(E['cross'])} {bold('No Proxy Set!')}")
        return

    sites_list = _load_sites()
    if not sites_list:
        await message.reply(f"{pe(E['cross'])} {bold('No sites available!')}")
        return

    set_file_session(uid, {
        "ccs": all_ccs,
        "gate": "Shopify",
        "proxy_list": proxy_list,
        "sites_list": sites_list,
        "chat_id": message.chat.id,
    })

    await message.reply(
        f"{pe(E['file'])} {bold(str(len(all_ccs)))} {bold('cards loaded!')}\n\n"
        f"{pe(E['info'])} {bold('Show approved/3DS cards in chat?')}\n"
        f"{pe(E['yes'])} /yes — Show approved\n"
        f"{pe(E['no'])} /no — Hide approved"
    )

@router.message(Command("yes"))
async def cmd_yes(message: types.Message):
    uid = message.from_user.id
    sess = get_file_session(uid)
    if not sess:
        await message.reply(f"{pe(E['warn'])} {bold('No active file check!')}")
        return
    clear_file_session(uid)

    if uid in _FILE_ACTIVE_USERS:
        await message.reply(f"{pe(E['warn'])} {bold('File check already in progress!')}")
        return

    stop_key = f"file:{message.chat.id}:{uid}"
    _FILE_STOP_FLAGS[stop_key] = False
    _FILE_ACTIVE_USERS.add(uid)

    status_msg = await message.reply(
        f"{pe(E['loading'])} {bold('Starting File Check...')}\n"
        f"{pe(E['check'])} {bold('Approved cards will be shown')}\n"
        f"{sep()}\n"
        f"{pe(E['card'])} {bold('Total →')} {bold(str(len(sess['ccs'])))}\n"
        f"{pe(E['checked'])} {bold('Checked →')} 0\n"
        f"{pe(E['charged'])} {bold('Charged →')} 0"
    )

    await _process_file_check(
        sess["ccs"], uid, message.from_user.full_name or "", message.from_user.username or "",
        message.chat.id, status_msg, stop_key, sess["gate"],
        None, sess["proxy_list"], sess.get("sites_list"), show_approved=True
    )

@router.message(Command("no"))
async def cmd_no(message: types.Message):
    uid = message.from_user.id
    sess = get_file_session(uid)
    if not sess:
        await message.reply(f"{pe(E['warn'])} {bold('No active file check!')}")
        return
    clear_file_session(uid)

    if uid in _FILE_ACTIVE_USERS:
        await message.reply(f"{pe(E['warn'])} {bold('File check already in progress!')}")
        return

    stop_key = f"file:{message.chat.id}:{uid}"
    _FILE_STOP_FLAGS[stop_key] = False
    _FILE_ACTIVE_USERS.add(uid)

    status_msg = await message.reply(
        f"{pe(E['loading'])} {bold('Starting File Check...')}\n"
        f"{pe(E['cross'])} {bold('Approved cards hidden')}\n"
        f"{sep()}\n"
        f"{pe(E['card'])} {bold('Total →')} {bold(str(len(sess['ccs'])))}\n"
        f"{pe(E['checked'])} {bold('Checked →')} 0\n"
        f"{pe(E['charged'])} {bold('Charged →')} 0"
    )

    await _process_file_check(
        sess["ccs"], uid, message.from_user.full_name or "", message.from_user.username or "",
        message.chat.id, status_msg, stop_key, sess["gate"],
        None, sess["proxy_list"], sess.get("sites_list"), show_approved=False
    )

@router.message(Command("stop"))
async def cmd_stop(message: types.Message):
    uid = message.from_user.id
    stop_key = f"file:{message.chat.id}:{uid}"
    if stop_key in _FILE_STOP_FLAGS:
        _FILE_STOP_FLAGS[stop_key] = True
        await message.reply(
            f"{pe(E['stop'])} {bold('Stopping session...')}\n"
            f"{pe(E['info'])} {bold('Please wait for current card to finish.')}")
    else:
        await message.reply(f"{pe(E['warn'])} {bold('No active session to stop!')}")

# ══════════════════════════════════════════════════════════════════════════════
#  ST (WooCommerce) COMMANDS
# ══════════════════════════════════════════════════════════════════════════════

@router.message(Command("st"))
async def cmd_st(message: types.Message):
    uid = message.from_user.id
    joined = await check_user_joined(uid)
    if not joined:
        await message.reply(JOIN_MSG, reply_markup=join_keyboard())
        return
    if is_banned(uid) or not auth.has_premium_access(uid, message.chat.id):
        await message.reply(f"{pe(E['cross'])} {bold('Premium Access Required!')}")
        return

    cc_str = None
    args = message.text.split(maxsplit=1)
    if len(args) >= 2:
        cc_str = extract_cc(args[1])
        if not cc_str:
            parts = re.split(r'[|/]', args[1].strip())
            if len(parts) >= 4:
                cc_str = "|".join(p.strip() for p in parts[:4])
    if not cc_str and message.reply_to_message:
        cc_str = extract_cc(message.reply_to_message.text or "")
    if not cc_str:
        await message.reply(f"{pe(E['warn'])} {bold('Usage:')} /st 438854|03|2030|815")
        return

    site = auth.get_user_stsite(uid) if hasattr(auth, 'get_user_stsite') else None
    if not site:
        await message.reply(f"{pe(E['cross'])} {bold('No ST site set!')} Use /stsite")
        return

    proxy_data = get_user_proxy(uid)
    proxy_url = proxy_dict_to_url(proxy_data) if proxy_data else None
    bin_num = cc_str.split("|")[0][:6]

    loading_msg = await message.reply(
        f"{pe(E['loading'])} {bold('Checking CC...')}\n"
        f"{pe(E['card'])} <tg-spoiler>{cc_str}</tg-spoiler>"
    )

    _bin = asyncio.create_task(bin_lookup(bin_num))
    try:
        result_str = await asyncio.get_running_loop().run_in_executor(
            CHECKER_POOL, lambda: st.VW(cc_str, site, proxy_url)
        )
    except Exception as e:
        result_str = str(e)[:80]
    bin_info = await _bin

    result_text = fmt_result(cc_str, "WooCommerce", site, "-", str(result_str), bin_info, uid,
                             message.from_user.full_name or "", message.from_user.username or "")
    await safe_edit(loading_msg, result_text)

@router.message(Command("stsite"))
async def cmd_stsite(message: types.Message):
    uid = message.from_user.id
    joined = await check_user_joined(uid)
    if not joined:
        await message.reply(JOIN_MSG, reply_markup=join_keyboard())
        return
    if is_banned(uid) or not auth.has_premium_access(uid, message.chat.id):
        await message.reply(f"{pe(E['cross'])} {bold('Premium Access Required!')}")
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply(f"{pe(E['warn'])} {bold('Usage:')} /stsite example.com")
        return
    url = args[1].strip().replace("https://", "").replace("http://", "").strip("/")
    if hasattr(auth, 'add_user_stsite'):
        auth.add_user_stsite(uid, url)
    await message.reply(f"{pe(E['check'])} {bold('Site added:')} {bold(url)}")

@router.message(Command("stmysite"))
async def cmd_stmysite(message: types.Message):
    uid = message.from_user.id
    sites = auth.get_user_stsites(uid) if hasattr(auth, 'get_user_stsites') else []
    if not sites:
        await message.reply(f"{pe(E['warn'])} {bold('No sites saved!')}")
        return
    lines = [f"{pe(E['check'])} {bold('Your ST Sites:')}\n"]
    for i, s in enumerate(sites, 1):
        lines.append(f"{pe(E['bolt'])} {bold(str(i))}. {bold(s)}")
    await message.reply("\n".join(lines))

# ══════════════════════════════════════════════════════════════════════════════
#  RZ (Razorpay) COMMANDS
# ══════════════════════════════════════════════════════════════════════════════

@router.message(Command("rz"))
async def cmd_rz(message: types.Message):
    uid = message.from_user.id
    joined = await check_user_joined(uid)
    if not joined:
        await message.reply(JOIN_MSG, reply_markup=join_keyboard())
        return
    if is_banned(uid) or not auth.has_premium_access(uid, message.chat.id):
        await message.reply(f"{pe(E['cross'])} {bold('Premium Access Required!')}")
        return

    cc_str = None
    args = message.text.split(maxsplit=1)
    if len(args) >= 2:
        cc_str = extract_cc(args[1])
        if not cc_str:
            parts = re.split(r'[|/]', args[1].strip())
            if len(parts) >= 4:
                cc_str = "|".join(p.strip() for p in parts[:4])
    if not cc_str and message.reply_to_message:
        cc_str = extract_cc(message.reply_to_message.text or "")
    if not cc_str:
        await message.reply(f"{pe(E['warn'])} {bold('Usage:')} /rz 483312|06|2030|288")
        return

    site = auth.get_user_rzsite(uid) if hasattr(auth, 'get_user_rzsite') else None
    if not site:
        await message.reply(f"{pe(E['cross'])} {bold('No RZ site set!')} Use /rzsite")
        return

    proxy_list = get_user_proxies(uid)
    if not proxy_list:
        await message.reply(f"{pe(E['cross'])} {bold('No Proxy Set!')}")
        return

    bin_num = cc_str.split("|")[0][:6]
    loading_msg = await message.reply(
        f"{pe(E['loading'])} {bold('Checking CC...')}\n"
        f"{pe(E['card'])} <tg-spoiler>{cc_str}</tg-spoiler>"
    )

    _bin = asyncio.create_task(bin_lookup(bin_num))
    try:
        proxy_data = random.choice(proxy_list)
        proxy_url = proxy_dict_to_url(proxy_data)
        parts = cc_str.split("|")
        cc, mm, yy, cvv = parts[0], parts[1], parts[2], parts[3]
        if len(yy) == 2:
            yy = "20" + yy
        result = await asyncio.get_running_loop().run_in_executor(
            CHECKER_POOL, lambda: rz.charge_payment_page_card(site, cc, mm, yy, cvv, proxy_url=proxy_url)
        )
        status, msg, code, dbg = result
        response = msg
        price = str(dbg.get("amount_paise", 0) / 100) if isinstance(dbg, dict) else "-"
    except Exception as e:
        response = str(e)[:80]
        price = "-"
        status = "error"

    bin_info = await _bin
    result_text = fmt_result(cc_str, "Razorpay", site, price, response, bin_info, uid,
                             message.from_user.full_name or "", message.from_user.username or "")
    await safe_edit(loading_msg, result_text)

@router.message(Command("rzsite"))
async def cmd_rzsite(message: types.Message):
    uid = message.from_user.id
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply(f"{pe(E['warn'])} {bold('Usage:')} /rzsite pages.razorpay.com/...")
        return
    url = args[1].strip()
    if hasattr(auth, 'add_user_rzsite'):
        auth.add_user_rzsite(uid, url)
    await message.reply(f"{pe(E['check'])} {bold('RZ Site added:')} {bold(url)}")

# ══════════════════════════════════════════════════════════════════════════════
#  CHK (Stripe Auth) COMMANDS
# ══════════════════════════════════════════════════════════════════════════════

@router.message(Command("chk"))
async def cmd_chk(message: types.Message):
    uid = message.from_user.id
    joined = await check_user_joined(uid)
    if not joined:
        await message.reply(JOIN_MSG, reply_markup=join_keyboard())
        return
    if is_banned(uid) or not auth.has_premium_access(uid, message.chat.id):
        await message.reply(f"{pe(E['cross'])} {bold('Premium Access Required!')}")
        return

    cc_str = None
    args = message.text.split(maxsplit=1)
    if len(args) >= 2:
        cc_str = extract_cc(args[1])
        if not cc_str:
            parts = re.split(r'[|/]', args[1].strip())
            if len(parts) >= 4:
                cc_str = "|".join(p.strip() for p in parts[:4])
    if not cc_str and message.reply_to_message:
        cc_str = extract_cc(message.reply_to_message.text or "")
    if not cc_str:
        await message.reply(f"{pe(E['warn'])} {bold('Usage:')} /chk 438854|03|2030|815")
        return

    bin_num = cc_str.split("|")[0][:6]
    loading_msg = await message.reply(
        f"{pe(E['loading'])} {bold('Checking CC...')}\n"
        f"{pe(E['card'])} <tg-spoiler>{cc_str}</tg-spoiler>"
    )

    _bin = asyncio.create_task(bin_lookup(bin_num))
    try:
        result = await asyncio.get_running_loop().run_in_executor(
            CHECKER_POOL, lambda: chk.check_card_str(cc_str)
        )
        status, msg, code, site_url = result
        response = msg
    except Exception as e:
        response = str(e)[:80]
        status = "error"

    bin_info = await _bin
    result_text = fmt_result(cc_str, "Stripe Auth", "-", "-", response, bin_info, uid,
                             message.from_user.full_name or "", message.from_user.username or "")
    await safe_edit(loading_msg, result_text)

# ══════════════════════════════════════════════════════════════════════════════
#  VBV (Braintree VBV) COMMANDS
# ══════════════════════════════════════════════════════════════════════════════

@router.message(Command("vbv"))
async def cmd_vbv(message: types.Message):
    uid = message.from_user.id
    joined = await check_user_joined(uid)
    if not joined:
        await message.reply(JOIN_MSG, reply_markup=join_keyboard())
        return
    if is_banned(uid) or not auth.has_premium_access(uid, message.chat.id):
        await message.reply(f"{pe(E['cross'])} {bold('Premium Access Required!')}")
        return

    cc_str = None
    args = message.text.split(maxsplit=1)
    if len(args) >= 2:
        cc_str = extract_cc(args[1])
        if not cc_str:
            parts = re.split(r'[|/]', args[1].strip())
            if len(parts) >= 4:
                cc_str = "|".join(p.strip() for p in parts[:4])
    if not cc_str and message.reply_to_message:
        cc_str = extract_cc(message.reply_to_message.text or "")
    if not cc_str:
        await message.reply(f"{pe(E['warn'])} {bold('Usage:')} /vbv 454887|09|2030|024")
        return

    bin_num = cc_str.split("|")[0][:6]
    loading_msg = await message.reply(
        f"{pe(E['loading'])} {bold('Checking VBV...')}\n"
        f"{pe(E['card'])} <tg-spoiler>{cc_str}</tg-spoiler>"
    )

    _bin = asyncio.create_task(bin_lookup(bin_num))
    try:
        result = await asyncio.get_running_loop().run_in_executor(
            CHECKER_POOL, lambda: vbv.check_card_str(cc_str)
        )
        api_status, api_message, code, _dbg = result
        response = api_message
    except Exception as e:
        response = str(e)[:80]
        api_status = "Error"

    bin_info = await _bin
    result_text = fmt_result(cc_str, "Braintree VBV", "-", "-", response, bin_info, uid,
                             message.from_user.full_name or "", message.from_user.username or "")
    await safe_edit(loading_msg, result_text)

# ══════════════════════════════════════════════════════════════════════════════
#  BR (Braintree Auth) COMMANDS
# ══════════════════════════════════════════════════════════════════════════════

@router.message(Command("br"))
async def cmd_br(message: types.Message):
    uid = message.from_user.id
    joined = await check_user_joined(uid)
    if not joined:
        await message.reply(JOIN_MSG, reply_markup=join_keyboard())
        return
    if is_banned(uid) or not auth.has_premium_access(uid, message.chat.id):
        await message.reply(f"{pe(E['cross'])} {bold('Premium Access Required!')}")
        return

    cc_str = None
    args = message.text.split(maxsplit=1)
    if len(args) >= 2:
        cc_str = extract_cc(args[1])
        if not cc_str:
            parts = re.split(r'[|/]', args[1].strip())
            if len(parts) >= 4:
                cc_str = "|".join(p.strip() for p in parts[:4])
    if not cc_str and message.reply_to_message:
        cc_str = extract_cc(message.reply_to_message.text or "")
    if not cc_str:
        await message.reply(f"{pe(E['warn'])} {bold('Usage:')} /br 438854|03|2030|815")
        return

    bin_num = cc_str.split("|")[0][:6]
    loading_msg = await message.reply(
        f"{pe(E['loading'])} {bold('Checking BR...')}\n"
        f"{pe(E['card'])} <tg-spoiler>{cc_str}</tg-spoiler>"
    )

    _bin = asyncio.create_task(bin_lookup(bin_num))
    try:
        result = await asyncio.get_running_loop().run_in_executor(
            CHECKER_POOL, lambda: b3auth.check_card_str(cc_str)
        )
        response = str(result)
    except Exception as e:
        response = str(e)[:80]

    bin_info = await _bin
    result_text = fmt_result(cc_str, "Braintree Auth", "-", "-", response, bin_info, uid,
                             message.from_user.full_name or "", message.from_user.username or "")
    await safe_edit(loading_msg, result_text)

# ══════════════════════════════════════════════════════════════════════════════
#  B3 (B3 Auth) COMMANDS
# ══════════════════════════════════════════════════════════════════════════════

@router.message(Command("b3"))
async def cmd_b3(message: types.Message):
    uid = message.from_user.id
    joined = await check_user_joined(uid)
    if not joined:
        await message.reply(JOIN_MSG, reply_markup=join_keyboard())
        return
    if is_banned(uid) or not auth.has_premium_access(uid, message.chat.id):
        await message.reply(f"{pe(E['cross'])} {bold('Premium Access Required!')}")
        return

    cc_str = None
    args = message.text.split(maxsplit=1)
    if len(args) >= 2:
        cc_str = extract_cc(args[1])
        if not cc_str:
            parts = re.split(r'[|/]', args[1].strip())
            if len(parts) >= 4:
                cc_str = "|".join(p.strip() for p in parts[:4])
    if not cc_str and message.reply_to_message:
        cc_str = extract_cc(message.reply_to_message.text or "")
    if not cc_str:
        await message.reply(f"{pe(E['warn'])} {bold('Usage:')} /b3 438854|03|2030|815")
        return

    bin_num = cc_str.split("|")[0][:6]
    loading_msg = await message.reply(
        f"{pe(E['loading'])} {bold('Checking B3...')}\n"
        f"{pe(E['card'])} <tg-spoiler>{cc_str}</tg-spoiler>"
    )

    _bin = asyncio.create_task(bin_lookup(bin_num))
    try:
        result = await asyncio.get_running_loop().run_in_executor(
            CHECKER_POOL, lambda: b3auth.check_card_str(cc_str)
        )
        response = str(result)
    except Exception as e:
        response = str(e)[:80]

    bin_info = await _bin
    result_text = fmt_result(cc_str, "B3 Auth", "-", "-", response, bin_info, uid,
                             message.from_user.full_name or "", message.from_user.username or "")
    await safe_edit(loading_msg, result_text)

# ══════════════════════════════════════════════════════════════════════════════
#  ST1 (Stripe $1) COMMANDS
# ══════════════════════════════════════════════════════════════════════════════

@router.message(Command("st1"))
async def cmd_st1(message: types.Message):
    uid = message.from_user.id
    joined = await check_user_joined(uid)
    if not joined:
        await message.reply(JOIN_MSG, reply_markup=join_keyboard())
        return
    if is_banned(uid) or not auth.has_premium_access(uid, message.chat.id):
        await message.reply(f"{pe(E['cross'])} {bold('Premium Access Required!')}")
        return

    cc_str = None
    args = message.text.split(maxsplit=1)
    if len(args) >= 2:
        cc_str = extract_cc(args[1])
        if not cc_str:
            parts = re.split(r'[|/]', args[1].strip())
            if len(parts) >= 4:
                cc_str = "|".join(p.strip() for p in parts[:4])
    if not cc_str and message.reply_to_message:
        cc_str = extract_cc(message.reply_to_message.text or "")
    if not cc_str:
        await message.reply(f"{pe(E['warn'])} {bold('Usage:')} /st1 438854|03|2030|815")
        return

    proxy_list = get_user_proxies(uid)
    if not proxy_list:
        await message.reply(f"{pe(E['cross'])} {bold('No Proxy Set!')}")
        return

    bin_num = cc_str.split("|")[0][:6]
    loading_msg = await message.reply(
        f"{pe(E['loading'])} {bold('Checking Stripe $1...')}\n"
        f"{pe(E['card'])} <tg-spoiler>{cc_str}</tg-spoiler>"
    )

    _bin = asyncio.create_task(bin_lookup(bin_num))
    try:
        proxy_data = random.choice(proxy_list)
        proxy_url = proxy_dict_to_url(proxy_data)
        result = await asyncio.get_running_loop().run_in_executor(
            CHECKER_POOL, lambda: st1_gate.check_card_str(cc_str, proxy_url)
        )
        status, msg, code = result if isinstance(result, tuple) and len(result) >= 3 else ("error", str(result), "error")
        response = msg
    except Exception as e:
        response = str(e)[:80]
        status = "error"

    bin_info = await _bin
    result_text = fmt_result(cc_str, "Stripe $1", "-", "$1.00", response, bin_info, uid,
                             message.from_user.full_name or "", message.from_user.username or "")
    await safe_edit(loading_msg, result_text)

# ══════════════════════════════════════════════════════════════════════════════
#  HIT (Stripe Checkout) COMMANDS
# ══════════════════════════════════════════════════════════════════════════════

@router.message(Command("hit"))
async def cmd_hit(message: types.Message):
    uid = message.from_user.id
    joined = await check_user_joined(uid)
    if not joined:
        await message.reply(JOIN_MSG, reply_markup=join_keyboard())
        return
    if is_banned(uid) or not auth.has_premium_access(uid, message.chat.id):
        await message.reply(f"{pe(E['cross'])} {bold('Premium Access Required!')}")
        return

    raw_text = ""
    args = message.text.split(maxsplit=1)
    if len(args) >= 2:
        raw_text = args[1]
    if message.reply_to_message:
        raw_text = raw_text + "\n" + (message.reply_to_message.text or "") if raw_text else (message.reply_to_message.text or "")
    if not raw_text.strip():
        await message.reply(
            f"{pe(E['warn'])} {bold('Usage:')} /hit <Stripe URL>\n"
            f"cc|mm|yy|cvv"
        )
        return

    link_match = re.search(
        r'https?://[^\s]*(?:checkout\.stripe\.com|billing\.stripe\.com|invoice\.stripe\.com|cs_(?:live|test)_)[^\s]*',
        raw_text, re.IGNORECASE,
    )
    if not link_match:
        await message.reply(f"{pe(E['cross'])} {bold('No Stripe link found!')}")
        return
    checkout_url = link_match.group(0)

    from helpers import CC_PATTERN
    all_ccs = []
    seen = set()
    for m in CC_PATTERN.finditer(raw_text):
        cc = f"{m.group(1)}|{m.group(2)}|{m.group(3)}|{m.group(4)}"
        if cc not in seen:
            seen.add(cc)
            all_ccs.append(cc)
    if not all_ccs:
        await message.reply(f"{pe(E['cross'])} {bold('No valid CCs found!')}")
        return
    all_ccs = all_ccs[:10]

    proxy_list = get_user_proxies(uid)
    if not proxy_list:
        await message.reply(f"{pe(E['cross'])} {bold('No Proxy Set!')}")
        return

    nopecha_key = auth.get_nopecha_key(uid) if hasattr(auth, 'get_nopecha_key') else ""

    loading_msg = await message.reply(
        f"{pe(E['loading'])} {bold('Loading Stripe checkout...')}\n"
        f"{pe(E['link'])} {bold(checkout_url[:60])}..."
    )

    proxy_data = random.choice(proxy_list)
    try:
        result = await asyncio.get_running_loop().run_in_executor(
            CHECKER_POOL, lambda: hit.run_hit_check(checkout_url, all_ccs[0], proxy_data, 3, nopecha_key)
        )
        merchant = result.get("merchant", "-")
        product = result.get("product", "-")
        amount = result.get("price_display", "-")
        response = result.get("result_msg", "Unknown")
    except Exception as e:
        response = str(e)[:80]
        merchant = "-"
        product = "-"
        amount = "-"

    bin_num = all_ccs[0].split("|")[0][:6]
    bin_info = await bin_lookup(bin_num)

    result_text = fmt_result(all_ccs[0], "Stripe Checkout", merchant, amount, response, bin_info, uid,
                             message.from_user.full_name or "", message.from_user.username or "")
    await safe_edit(loading_msg, result_text)

# ══════════════════════════════════════════════════════════════════════════════
#  SK (Stripe SK) COMMANDS
# ══════════════════════════════════════════════════════════════════════════════

SKKEYS_FILE = os.path.join(BASE_DIR, "skkeys.json")

def _load_skkeys() -> dict:
    try:
        with open(SKKEYS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_skkeys(data: dict):
    with open(SKKEYS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

@router.message(Command("skadd"))
async def cmd_skadd(message: types.Message):
    uid = message.from_user.id
    joined = await check_user_joined(uid)
    if not joined:
        await message.reply(JOIN_MSG, reply_markup=join_keyboard())
        return
    if is_banned(uid) or not auth.has_premium_access(uid, message.chat.id):
        await message.reply(f"{pe(E['cross'])} {bold('Premium Access Required!')}")
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply(f"{pe(E['warn'])} {bold('Usage:')} /skadd sk_live_...")
        return

    sk = args[1].strip()
    if not sk.startswith("sk_"):
        await message.reply(f"{pe(E['cross'])} {bold('Invalid SK format!')}")
        return

    loading_msg = await message.reply(f"{pe(E['loading'])} {bold('Validating SK...')}")

    try:
        if _SK_AVAILABLE:
            valid = await asyncio.get_running_loop().run_in_executor(
                CHECKER_POOL, lambda: _sk_mod.test_stripe_key(sk)
            )
        else:
            valid = False
    except Exception:
        valid = False

    if valid:
        _save_skkeys({**_load_skkeys(), str(uid): {"sk": sk}})
        await safe_edit(loading_msg, f"{pe(E['check'])} {bold('SK Saved & Valid!')}")
    else:
        await safe_edit(loading_msg, f"{pe(E['cross'])} {bold('SK Invalid or Dead!')}")

@router.message(Command("skcvv"))
async def cmd_skcvv(message: types.Message):
    uid = message.from_user.id
    joined = await check_user_joined(uid)
    if not joined:
        await message.reply(JOIN_MSG, reply_markup=join_keyboard())
        return
    if is_banned(uid) or not auth.has_premium_access(uid, message.chat.id):
        await message.reply(f"{pe(E['cross'])} {bold('Premium Access Required!')}")
        return

    sk_entry = _load_skkeys().get(str(uid))
    if not sk_entry or not sk_entry.get("sk"):
        await message.reply(f"{pe(E['cross'])} {bold('No SK set!')} Use /skadd")
        return

    cc_str = None
    args = message.text.split(maxsplit=1)
    if len(args) >= 2:
        cc_str = extract_cc(args[1])
        if not cc_str:
            parts = re.split(r'[|/]', args[1].strip())
            if len(parts) >= 4:
                cc_str = "|".join(p.strip() for p in parts[:4])
    if not cc_str and message.reply_to_message:
        cc_str = extract_cc(message.reply_to_message.text or "")
    if not cc_str:
        await message.reply(f"{pe(E['warn'])} {bold('Usage:')} /skcvv 438854|03|2030|815")
        return

    sk = sk_entry["sk"]
    bin_num = cc_str.split("|")[0][:6]
    loading_msg = await message.reply(
        f"{pe(E['loading'])} {bold('Checking SK...')}\n"
        f"{pe(E['card'])} <tg-spoiler>{cc_str}</tg-spoiler>"
    )

    _bin = asyncio.create_task(bin_lookup(bin_num))
    try:
        if _SK_AVAILABLE:
            result = await asyncio.get_running_loop().run_in_executor(
                CHECKER_POOL, lambda: _sk_mod.sk_check_card(sk, cc_str)
            )
            status, msg, code = result if isinstance(result, tuple) and len(result) >= 3 else ("error", str(result), "error")
            response = msg
        else:
            response = "SK module not available"
    except Exception as e:
        response = str(e)[:80]

    bin_info = await _bin
    result_text = fmt_result(cc_str, "Stripe SK", "-", "$1.00", response, bin_info, uid,
                             message.from_user.full_name or "", message.from_user.username or "")
    await safe_edit(loading_msg, result_text)

# ══════════════════════════════════════════════════════════════════════════════
#  GATE (Gateway Lookup) COMMAND
# ══════════════════════════════════════════════════════════════════════════════

@router.message(Command("gate"))
async def cmd_gate(message: types.Message):
    uid = message.from_user.id
    joined = await check_user_joined(uid)
    if not joined:
        await message.reply(JOIN_MSG, reply_markup=join_keyboard())
        return
    if is_banned(uid) or not auth.has_premium_access(uid, message.chat.id):
        await message.reply(f"{pe(E['cross'])} {bold('Premium Access Required!')}")
        return
    if not _GATE_AVAILABLE:
        await message.reply(f"{pe(E['warn'])} {bold('Gateway lookup module not available.')}")
        return

    if not message.reply_to_message or not message.reply_to_message.document:
        await message.reply(
            f"{pe(E['warn'])} {bold('Usage:')} Send a .txt with URLs and reply /gate"
        )
        return

    doc = message.reply_to_message.document
    if not doc.file_name or not doc.file_name.lower().endswith(".txt"):
        await message.reply(f"{pe(E['cross'])} {bold('Only .txt files!')}")
        return

    try:
        buf = BytesIO()
        await bot.download(doc.file_id, destination=buf)
        buf.seek(0)
        urls = [l.strip() for l in buf.read().decode("utf-8", errors="ignore").splitlines() if l.strip()]
    except Exception:
        await message.reply(f"{pe(E['cross'])} {bold('Failed to download file!')}")
        return

    loading_msg = await message.reply(
        f"{pe(E['loading'])} {bold('Scanning')} {bold(str(len(urls)))} {bold('URLs...')}"
    )

    try:
        working = await asyncio.get_running_loop().run_in_executor(
            CHECKER_POOL, lambda: _gate_mod.scan_urls(urls)
        )
    except Exception as e:
        await safe_edit(loading_msg, f"{pe(E['cross'])} {bold('Scan error:')} {bold(str(e)[:100])}")
        return

    if not working:
        await safe_edit(loading_msg, f"{pe(E['cross'])} {bold('No working gateways found!')}")
        return

    content = "\n".join(working) + "\n"
    await bot.send_document(
        uid,
        types.BufferedInputFile(content.encode("utf-8"), filename="working_gateways.txt"),
        caption=(
            f"{pe(E['check'])} {bold('Gateway Lookup Complete')}\n"
            f"{pe(E['check'])} {bold(str(len(working)))} working sites found\n\n"
            f"{pe(E['link'])} {italic(POWERED_BY)}"
        ),
    )
    await safe_edit(loading_msg, f"{pe(E['check'])} {bold('Done!')} File sent above.")

# ══════════════════════════════════════════════════════════════════════════════
#  ADMIN / OWNER COMMANDS
# ══════════════════════════════════════════════════════════════════════════════

@router.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if not auth.is_owner(message.from_user.id):
        await message.reply(f"{pe(E['cross'])} {bold('Owner only command!')}")
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip().isdigit():
        await message.reply(f"{pe(E['warn'])} {bold('Usage:')} /admin user-id")
        return
    target_id = int(args[1].strip())
    if auth.add_admin(target_id):
        await message.reply(
            f"{pe(E['check'])} {bold('Admin Added!')}\n"
            f"{pe(E['user'])} ID: {bold(str(target_id))}"
        )
    else:
        await message.reply(f"{pe(E['warn'])} {bold('User is already an admin.')}")

@router.message(Command("unadmin"))
async def cmd_unadmin(message: types.Message):
    if not auth.is_owner(message.from_user.id):
        await message.reply(f"{pe(E['cross'])} {bold('Owner only command!')}")
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip().isdigit():
        await message.reply(f"{pe(E['warn'])} {bold('Usage:')} /unadmin user-id")
        return
    target_id = int(args[1].strip())
    if auth.remove_admin(target_id):
        await message.reply(
            f"{pe(E['check'])} {bold('Admin Removed!')}\n"
            f"{pe(E['user'])} ID: {bold(str(target_id))}"
        )
    else:
        await message.reply(f"{pe(E['warn'])} {bold('User is not an admin.')}")

@router.message(Command("auth"))
async def cmd_auth(message: types.Message):
    if not auth.is_admin(message.from_user.id):
        await message.reply(f"{pe(E['cross'])} {bold('Admin only command!')}")
        return
    args = message.text.split()
    if len(args) < 2 or not args[1].strip().isdigit():
        await message.reply(
            f"{pe(E['warn'])} {bold('Usage:')} /auth user-id [days]\n"
            f"{pe(E['next'])} Days optional (0 = lifetime)"
        )
        return
    target_id = int(args[1].strip())
    days = int(args[2]) if len(args) >= 3 and args[2].isdigit() else 0
    auth.auth_user(target_id, days=days)
    expiry_text = "Lifetime" if days == 0 else f"{days} days"
    await message.reply(
        f"{pe(E['check'])} {bold('Premium Granted!')}\n"
        f"{pe(E['user'])} ID: {bold(str(target_id))}\n"
        f"{pe(E['star'])} Plan: {bold(expiry_text)}"
    )

@router.message(Command("unauth"))
async def cmd_unauth(message: types.Message):
    if not auth.is_admin(message.from_user.id):
        await message.reply(f"{pe(E['cross'])} {bold('Admin only command!')}")
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip().isdigit():
        await message.reply(f"{pe(E['warn'])} {bold('Usage:')} /unauth user-id")
        return
    target_id = int(args[1].strip())
    if auth.unauth_user(target_id):
        await message.reply(
            f"{pe(E['check'])} {bold('Premium Removed!')}\n"
            f"{pe(E['user'])} ID: {bold(str(target_id))}"
        )
    else:
        await message.reply(f"{pe(E['warn'])} {bold('User has no premium access.')}")

@router.message(Command("ban"))
async def cmd_ban(message: types.Message):
    if not auth.is_admin(message.from_user.id):
        await message.reply(f"{pe(E['cross'])} {bold('Admin only command!')}")
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip().isdigit():
        await message.reply(f"{pe(E['warn'])} {bold('Usage:')} /ban user-id")
        return
    target_id = int(args[1].strip())
    ban_user(target_id)
    await message.reply(
        f"{pe(E['check'])} {bold('User Banned!')}\n"
        f"{pe(E['user'])} ID: {bold(str(target_id))}"
    )

@router.message(Command("unban"))
async def cmd_unban(message: types.Message):
    if not auth.is_admin(message.from_user.id):
        await message.reply(f"{pe(E['cross'])} {bold('Admin only command!')}")
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip().isdigit():
        await message.reply(f"{pe(E['warn'])} {bold('Usage:')} /unban user-id")
        return
    target_id = int(args[1].strip())
    unban_user(target_id)
    await message.reply(
        f"{pe(E['check'])} {bold('User Unbanned!')}\n"
        f"{pe(E['user'])} ID: {bold(str(target_id))}"
    )

@router.message(Command("key"))
async def cmd_key(message: types.Message):
    if not auth.is_admin(message.from_user.id):
        await message.reply(f"{pe(E['cross'])} {bold('Admin only command!')}")
        return
    args = message.text.split()
    if len(args) < 3 or not args[1].isdigit() or not args[2].isdigit():
        await message.reply(
            f"{pe(E['warn'])} {bold('Usage:')} /key users days\n"
            f"{pe(E['next'])} Example: /key 10 1"
        )
        return
    max_users = int(args[1])
    days = int(args[2])
    keys = auth.generate_keys(max_users, days, created_by=message.from_user.id)
    key = keys[0]
    await message.reply(
        f"{pe(E['gem'])} {bold('Key Generated')} {pe(E['check'])}\n"
        f"{sep()}\n"
        f"{pe(E['bolt'])} Key → <code>{key}</code>\n"
        f"{pe(E['user'])} Slots → {bold(str(max_users))} users\n"
        f"{pe(E['star'])} Plan → {bold(str(days))} days\n"
        f"{sep()}\n"
        f"{pe(E['link'])} {italic(POWERED_BY)}"
    )

@router.message(Command("ckey"))
async def cmd_ckey(message: types.Message):
    if not auth.is_admin(message.from_user.id):
        await message.reply(f"{pe(E['cross'])} {bold('Admin only command!')}")
        return
    args = message.text.split()
    if len(args) < 3 or not args[1].isdigit() or not args[2].isdigit():
        await message.reply(
            f"{pe(E['warn'])} {bold('Usage:')} /ckey users credits\n"
            f"{pe(E['next'])} Example: /ckey 10 5000"
        )
        return
    max_users = int(args[1])
    credits = int(args[2])
    key = f"CREDITS-{random.randint(100000, 999999)}"
    await message.reply(
        f"{pe(E['gem'])} {bold('Credits Key Generated')} {pe(E['check'])}\n"
        f"{sep()}\n"
        f"{pe(E['bolt'])} Key → <code>{key}</code>\n"
        f"{pe(E['user'])} Slots → {bold(str(max_users))}\n"
        f"{pe(E['card'])} Credits → {bold(str(credits))}\n"
        f"{sep()}\n"
        f"{pe(E['link'])} {italic(POWERED_BY)}"
    )

@router.message(Command("pkey"))
async def cmd_pkey(message: types.Message):
    if not auth.is_admin(message.from_user.id):
        await message.reply(f"{pe(E['cross'])} {bold('Admin only command!')}")
        return
    args = message.text.split()
    if len(args) < 4 or not args[1].isdigit() or not args[2].isdigit() or not args[3].isdigit():
        await message.reply(
            f"{pe(E['warn'])} {bold('Usage:')} /pkey users days credits\n"
            f"{pe(E['next'])} Example: /pkey 10 30 10000"
        )
        return
    max_users = int(args[1])
    days = int(args[2])
    credits = int(args[3])
    key = f"PREMIUM-{random.randint(100000, 999999)}"
    await message.reply(
        f"{pe(E['gem'])} {bold('Premium+Credits Key Generated')} {pe(E['check'])}\n"
        f"{sep()}\n"
        f"{pe(E['bolt'])} Key → <code>{key}</code>\n"
        f"{pe(E['user'])} Slots → {bold(str(max_users))}\n"
        f"{pe(E['star'])} Days → {bold(str(days))}\n"
        f"{pe(E['card'])} Credits → {bold(str(credits))}\n"
        f"{sep()}\n"
        f"{pe(E['link'])} {italic(POWERED_BY)}"
    )

@router.message(Command("redeem"))
async def cmd_redeem(message: types.Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip():
        await message.reply(f"{pe(E['warn'])} {bold('Usage:')} /redeem KEY")
        return
    if auth.is_premium(message.from_user.id):
        await message.reply(f"{pe(E['cross'])} {bold('You already have premium!')}")
        return
    key = args[1].strip()
    success, info = auth.redeem_key(message.from_user.id, key)
    if success:
        await message.reply(
            f"{pe(E['gem'])} {bold('Key Redeemed!')} {pe(E['gem'])}\n"
            f"{pe(E['check'])} Plan: {bold(info)}\n\n"
            f"{pe(E['link'])} {italic(POWERED_BY)}"
        )
    else:
        await message.reply(f"{pe(E['cross'])} {bold('Redemption Failed!')}\n{pe(E['warn'])} {bold(info)}")

@router.message(Command("broad"))
async def cmd_broad(message: types.Message):
    if not auth.is_admin(message.from_user.id):
        await message.reply(f"{pe(E['cross'])} {bold('Admin only command!')}")
        return

    broadcast_text = None
    if message.reply_to_message:
        use_copy = True
        reply_msg = message.reply_to_message
    else:
        raw_text = message.text or ""
        cmd_end = len("/broad")
        remaining = raw_text[cmd_end:]
        stripped = remaining.lstrip("\n \t")
        broadcast_text = stripped
        if not broadcast_text:
            await message.reply(f"{pe(E['warn'])} {bold('Usage:')} /broad message or reply to msg")
            return
        use_copy = False

    all_ids = auth.get_all_user_ids()
    total = len(all_ids)
    if total == 0:
        await message.reply(f"{pe(E['cross'])} {bold('No users found!')}")
        return

    status_msg = await message.reply(
        f"{pe(E['rocket'])} {bold('Broadcasting...')}\n"
        f"{pe(E['user'])} Total: {bold(str(total))}"
    )

    sent, failed = 0, 0
    sem = asyncio.Semaphore(25)

    async def _send_one(uid: int):
        nonlocal sent, failed
        async with sem:
            try:
                if use_copy:
                    await bot.copy_message(chat_id=uid, from_chat_id=reply_msg.chat.id, message_id=reply_msg.message_id)
                else:
                    await bot.send_message(chat_id=uid, text=broadcast_text)
                sent += 1
            except Exception:
                failed += 1

    await asyncio.gather(*[_send_one(uid) for uid in all_ids], return_exceptions=True)

    await safe_edit(status_msg,
        f"{pe(E['check'])} {bold('Broadcast Complete!')}\n"
        f"{pe(E['check'])} Sent: {bold(str(sent))}\n"
        f"{pe(E['cross'])} Failed: {bold(str(failed))}"
    )

@router.message(Command("imaintain"))
async def cmd_imaintain(message: types.Message):
    if not auth.is_owner(message.from_user.id):
        await message.reply(f"{pe(E['cross'])} {bold('Owner only command!')}")
        return
    args = message.text.split(maxsplit=1)
    reason = args[1].strip() if len(args) >= 2 else "Server Maintenance"
    enable_maintenance(reason)
    await message.reply(
        f"{pe(E['maintain'])} {bold('Maintenance Mode ENABLED')}\n"
        f"{pe(E['info'])} Reason: {bold(reason)}"
    )

@router.message(Command("cmaintain"))
async def cmd_cmaintain(message: types.Message):
    if not auth.is_owner(message.from_user.id):
        await message.reply(f"{pe(E['cross'])} {bold('Owner only command!')}")
        return
    disable_maintenance()
    await message.reply(
        f"{pe(E['check'])} {bold('Maintenance Mode DISABLED')}\n"
        f"{pe(E['bolt'])} Bot is back online!"
    )

# ══════════════════════════════════════════════════════════════════════════════
#  MAINTENANCE CHECK MIDDLEWARE
# ══════════════════════════════════════════════════════════════════════════════

class _MaintenanceMiddleware(_BaseMiddleware):
    async def __call__(self, handler, event, data):
        user = data.get("event_from_user")
        if user and is_maintenance() and not auth.is_owner(user.id):
            await event.reply(get_maintenance_msg())
            return
        return await handler(event, data)

dp.message.middleware(_MaintenanceMiddleware())

# ══════════════════════════════════════════════════════════════════════════════
#  MAIN SETUP
# ══════════════════════════════════════════════════════════════════════════════

async def main():
    log.info("Starting bot...")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
    except Exception:
        pass
    await asyncio.sleep(2)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    asyncio.run(main())
