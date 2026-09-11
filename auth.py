import json
import os
import time
import logging

log = logging.getLogger("auth")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(BASE_DIR, "users.json")
KEYS_FILE = os.path.join(BASE_DIR, "keys.json")
CREDITS_FILE = os.path.join(BASE_DIR, "credits.json")
ADMINS_FILE = os.path.join(BASE_DIR, "admins.json")
OWNER_FILE = os.path.join(BASE_DIR, "owner.json")
BANNED_FILE = os.path.join(BASE_DIR, "banned.json")
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

LIMITS = {
    "free": 300,
    "premium": 8000,
    "admin": 15000,
    "owner": 30000,
}


class UserAuth:
    def __init__(self):
        self.users = self._load_json(USERS_FILE, {})
        self.keys = self._load_json(KEYS_FILE, {})
        self.credits = self._load_json(CREDITS_FILE, {})
        self.admins = self._load_json(ADMINS_FILE, [])
        self.owner_id = 8563232385
        self.banned = self._load_json(BANNED_FILE, [])
        config = self._load_json(CONFIG_FILE, {})
        self.approved_group_id = config.get("approved_group_id")
        self.monitor_group_id = config.get("monitor_group_id")

    def _load_json(self, path, default):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default

    def _save_json(self, path, data):
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            log.error("Failed to save %s: %s", path, e)

    def get_role(self, user_id: int) -> str:
        if user_id == self.owner_id:
            return "owner"
        if user_id in self.admins:
            return "admin"
        user = self.users.get(str(user_id), {})
        if user.get("premium"):
            expiry = user.get("premium_expiry", 0)
            if expiry == 0 or expiry > time.time():
                return "premium"
        return "free"

    def get_limit(self, user_id: int) -> int:
        role = self.get_role(user_id)
        base = LIMITS.get(role, 300)
        extra = self.credits.get(str(user_id), 0)
        return base + extra

    def has_premium_access(self, user_id: int, chat_id: int = None) -> bool:
        role = self.get_role(user_id)
        return role in ("premium", "admin", "owner")

    def is_owner(self, user_id: int) -> bool:
        return user_id == self.owner_id

    def is_admin(self, user_id: int) -> bool:
        return user_id in self.admins or user_id == self.owner_id

    def is_banned(self, user_id: int) -> bool:
        return user_id in self.banned

    def ban_user(self, user_id: int):
        if user_id not in self.banned:
            self.banned.append(user_id)
            self._save_json(BANNED_FILE, self.banned)

    def unban_user(self, user_id: int):
        if user_id in self.banned:
            self.banned.remove(user_id)
            self._save_json(BANNED_FILE, self.banned)

    def add_admin(self, user_id: int) -> bool:
        if user_id not in self.admins:
            self.admins.append(user_id)
            self._save_json(ADMINS_FILE, self.admins)
            return True
        return False

    def remove_admin(self, user_id: int) -> bool:
        if user_id in self.admins:
            self.admins.remove(user_id)
            self._save_json(ADMINS_FILE, self.admins)
            return True
        return False

    def auth_user(self, user_id: int, days: int = 0):
        user = self.users.setdefault(str(user_id), {})
        user["premium"] = True
        if days == 0:
            user["premium_expiry"] = 0
        else:
            user["premium_expiry"] = int(time.time()) + (days * 86400)
        self._save_json(USERS_FILE, self.users)

    def unauth_user(self, user_id: int) -> bool:
        user = self.users.get(str(user_id))
        if user and user.get("premium"):
            user["premium"] = False
            user["premium_expiry"] = 0
            self._save_json(USERS_FILE, self.users)
            return True
        return False

    def add_credits(self, user_id: int, amount: int):
        current = self.credits.get(str(user_id), 0)
        self.credits[str(user_id)] = current + amount
        self._save_json(CREDITS_FILE, self.credits)

    def get_credits(self, user_id: int) -> int:
        return self.credits.get(str(user_id), 0)

    def generate_key(self, key_type: str, max_users: int, days: int = 0, credits: int = 0) -> str:
        key = "Kamal-" + "".join(__import__("random").choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=8))
        self.keys[key] = {
            "type": key_type,
            "max_users": max_users,
            "used_by": [],
            "days": days,
            "credits": credits,
            "created_at": int(time.time()),
        }
        self._save_json(KEYS_FILE, self.keys)
        return key

    def redeem_key(self, user_id: int, key: str) -> tuple[bool, str]:
        data = self.keys.get(key)
        if not data:
            return False, "Invalid key"
        if user_id in data["used_by"]:
            return False, "Already redeemed"
        if len(data["used_by"]) >= data["max_users"]:
            return False, "Key exhausted"
        data["used_by"].append(user_id)
        if data["type"] == "pkey":
            self.auth_user(user_id, data["days"])
        if data["credits"] > 0:
            self.add_credits(user_id, data["credits"])
        self._save_json(KEYS_FILE, self.keys)
        if data["type"] == "pkey":
            return True, f"Premium + {data['credits']} credits"
        return True, f"{data['credits']} credits added"

    def get_all_user_ids(self) -> list[int]:
        return [int(k) for k in self.users.keys()]

    def save_user(self, user_id: int, username: str = "", full_name: str = "") -> bool:
        uid = str(user_id)
        if uid not in self.users:
            self.users[uid] = {
                "username": username,
                "full_name": full_name,
                "joined_at": int(time.time()),
                "premium": False,
                "premium_expiry": 0,
            }
            self._save_json(USERS_FILE, self.users)
            return True
        return False


# Global instance
user_auth = UserAuth()
OWNER_ID = user_auth.owner_id or 0
APPROVED_GROUP_ID = user_auth.approved_group_id
MONITOR_GROUP_ID = user_auth.monitor_group_id


# ══ دوال ناقصة مطلوبة من bot.py ══

def get_user_role(user_id: int) -> str:
    return user_auth.get_role(user_id)

def get_premium_expiry(user_id: int) -> str:
    import datetime
    u = user_auth.users.get(str(user_id), {})
    expiry = u.get("premium_expiry", 0)
    if expiry == 0:
        return "Lifetime"
    if expiry < time.time():
        return "Expired"
    return datetime.datetime.fromtimestamp(expiry).strftime("%Y-%m-%d")

def is_premium(user_id: int) -> bool:
    return user_auth.get_role(user_id) in ("premium", "admin", "owner")

def generate_keys(max_users: int, days: int, created_by: int = None) -> list:
    key = user_auth.generate_key("pkey", max_users, days)
    return [key]

def save_charged_cc(cc: str, user_id: int, name: str, gate: str, price: str):
    pass

def get_nopecha_key(user_id: int) -> str:
    return ""

def check_card_str(cc: str):
    return ("error", "use checker_bridge", "error")

_ST_SITES_FILE = os.path.join(BASE_DIR, "st_sites.json")
_RZ_SITES_FILE = os.path.join(BASE_DIR, "rz_sites.json")

def _load_st_sites() -> dict:
    try:
        with open(_ST_SITES_FILE) as f:
            return json.load(f)
    except Exception:
        return {}

def _save_st_sites(data: dict):
    with open(_ST_SITES_FILE, "w") as f:
        json.dump(data, f, indent=2)

def add_user_stsite(user_id: int, url: str):
    data = _load_st_sites()
    sites = data.get(str(user_id), [])
    if url not in sites:
        sites.append(url)
    data[str(user_id)] = sites
    _save_st_sites(data)

def get_user_stsite(user_id: int):
    data = _load_st_sites()
    sites = data.get(str(user_id), [])
    return sites[-1] if sites else None

def get_user_stsites(user_id: int) -> list:
    return _load_st_sites().get(str(user_id), [])

def _load_rz_sites() -> dict:
    try:
        with open(_RZ_SITES_FILE) as f:
            return json.load(f)
    except Exception:
        return {}

def _save_rz_sites(data: dict):
    with open(_RZ_SITES_FILE, "w") as f:
        json.dump(data, f, indent=2)

def add_user_rzsite(user_id: int, url: str):
    data = _load_rz_sites()
    data[str(user_id)] = url
    _save_rz_sites(data)

def get_user_rzsite(user_id: int):
    return _load_rz_sites().get(str(user_id))

def save_user(user_id: int, username: str = "", full_name: str = "") -> bool:
    return user_auth.save_user(user_id, username, full_name)

def get_user_role(user_id: int) -> str:
    return user_auth.get_role(user_id)

def unauth_user(user_id: int) -> bool:
    return user_auth.unauth_user(user_id)

def auth_user(user_id: int, days: int = 0) -> None:
    user_auth.auth_user(user_id, days)

def add_admin(user_id: int) -> bool:
    return user_auth.add_admin(user_id)

def is_admin(user_id: int) -> bool:
    return user_auth.is_admin(user_id)

def get_all_user_ids() -> list:
    return user_auth.get_all_user_ids()

def redeem_key(user_id: int, key: str) -> tuple:
    return user_auth.redeem_key(user_id, key)

def remove_admin(user_id: int) -> bool:
    return user_auth.remove_admin(user_id)

def is_owner(user_id: int) -> bool:
    return user_auth.is_owner(user_id)

def has_premium_access(user_id: int, chat_id: int = None) -> bool:
    return user_auth.has_premium_access(user_id)
