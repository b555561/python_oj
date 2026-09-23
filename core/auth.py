"""认证：标准库实现的密码哈希 + 签名 Cookie 会话（零额外依赖）。"""
import base64
import hashlib
import hmac
import json
import secrets
import time
from pathlib import Path
from typing import Optional

from fastapi import Request

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_FILE = BASE_DIR / ".secret_key"

# 会话有效期：30 天
SESSION_TTL = 30 * 24 * 3600


def _get_secret() -> bytes:
    if SECRET_FILE.exists():
        return SECRET_FILE.read_text(encoding="utf-8").strip().encode()
    key = secrets.token_hex(32)
    SECRET_FILE.write_text(key, encoding="utf-8")
    return key.encode()


SECRET = _get_secret()


# ============ 密码 ============
def hash_password(pwd: str) -> (str, str):
    salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", pwd.encode("utf-8"), salt.encode(), 100_000)
    return h.hex(), salt


def verify_password(pwd: str, pwd_hash: str, salt: str) -> bool:
    h = hashlib.pbkdf2_hmac("sha256", pwd.encode("utf-8"), salt.encode(), 100_000)
    return hmac.compare_digest(h.hex(), pwd_hash)


# ============ 会话 Cookie ============
def _b64e(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _b64d(text: str) -> bytes:
    pad = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + pad)


def _sign(payload: str) -> str:
    return hmac.new(SECRET, payload.encode("utf-8"), hashlib.sha256).hexdigest()[:32]


def create_session_token(user_id: int) -> str:
    payload = _b64e(json.dumps({"uid": user_id, "exp": int(time.time()) + SESSION_TTL}).encode())
    return f"{payload}.{_sign(payload)}"


def read_session_token(token: str) -> Optional[int]:
    if not token or "." not in token:
        return None
    payload, sig = token.rsplit(".", 1)
    if not hmac.compare_digest(_sign(payload), sig):
        return None
    try:
        data = json.loads(_b64d(payload))
    except Exception:
        return None
    if int(data.get("exp", 0)) < time.time():
        return None
    return int(data.get("uid", 0)) or None


def get_current_user(request: Request) -> Optional[dict]:
    """从请求中解析出当前用户（未登录返回 None）。"""
    from core import db
    token = request.cookies.get("session")
    uid = read_session_token(token or "")
    if not uid:
        return None
    return db.query_one("SELECT * FROM users WHERE id = ?", (uid,))
