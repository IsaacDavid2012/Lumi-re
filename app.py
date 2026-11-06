#!/usr/bin/env python3
"""
Lumière — cinematic streaming front end powered by TMDB.

Provides fast search and browsing across 1.26M+ TMDB titles, a clean
VidFast player, multi-user accounts, autosaved Continue Watching history,
and hardened session authentication.
"""

import base64
import hashlib
import hmac
import ipaddress
import json
import logging
import os
import re
import secrets
import sqlite3
import struct
import threading
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from functools import wraps
from flask import (
    Flask,
    Response,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    stream_with_context,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

try:
    import nacl.secret
    from curl_cffi import requests as curl_requests
    HAVE_NATIVE_EXTRACTOR = True
except ImportError:
    HAVE_NATIVE_EXTRACTOR = False

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "movies.db")
SECRET_KEY_FILE = os.path.join(BASE_DIR, "data", ".flask_secret_key")
ENV_FILE = os.path.join(BASE_DIR, ".env")


def _load_dotenv(path: str):
    if not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k and k not in os.environ:
                    os.environ[k] = v
    except Exception:
        pass


_load_dotenv(ENV_FILE)

SITE_NAME = os.environ.get("LUMIERE_SITE_NAME", "Lumière")
SITE_TAGLINE = "Cinema, beautifully streamed."
MAX_SESSION_AGE_SECONDS = 12 * 3600

STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "").strip()
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "").strip()
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "").strip()
try:
    STRIPE_PRICE_CENTS = max(100, int(os.environ.get("STRIPE_PRICE_CENTS", "3000")))
except ValueError:
    STRIPE_PRICE_CENTS = 3000
STRIPE_CURRENCY = os.environ.get("STRIPE_CURRENCY", "myr").strip().lower() or "myr"


def format_price_display(cents: int = None, currency: str = None) -> str:
    c = STRIPE_PRICE_CENTS if cents is None else cents
    curr = (STRIPE_CURRENCY if currency is None else currency).upper()
    symbols = {"USD": "$", "EUR": "€", "GBP": "£", "MYR": "RM"}
    sym = symbols.get(curr, f"{curr} ")
    if c % 100 == 0:
        return f"{sym}{c // 100}"
    return f"{sym}{c / 100:.2f}"


TRUSTED_PROXY_NETS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("172.16.0.0/12"),
]
for _cidr in os.environ.get("LUMIERE_TRUSTED_PROXIES", "").split(","):
    _cidr = _cidr.strip()
    if _cidr:
        try:
            TRUSTED_PROXY_NETS.append(ipaddress.ip_network(_cidr, strict=False))
        except ValueError:
            pass


def load_or_create_secret_key() -> bytes:
    env_key = os.environ.get("FLASK_SECRET_KEY")
    if env_key:
        return env_key.encode("utf-8")
    os.makedirs(os.path.dirname(SECRET_KEY_FILE), exist_ok=True)
    if os.path.exists(SECRET_KEY_FILE):
        try:
            with open(SECRET_KEY_FILE, "rb") as f:
                key = f.read().strip()
                if len(key) >= 32:
                    return key
        except Exception:
            pass
    key = secrets.token_hex(32).encode("utf-8")
    try:
        with open(SECRET_KEY_FILE, "wb") as f:
            f.write(key)
        os.chmod(SECRET_KEY_FILE, 0o600)
    except Exception:
        pass
    return key


app.config.update(
    SECRET_KEY=load_or_create_secret_key(),
    SESSION_COOKIE_NAME=os.environ.get("LUMIERE_SESSION_COOKIE", "lumiere_session"),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("LUMIERE_COOKIE_SECURE", "0").lower()
    in ("1", "true", "yes", "on"),
    SESSION_REFRESH_EACH_REQUEST=False,
    PERMANENT_SESSION_LIFETIME=timedelta(hours=12),
    MAX_CONTENT_LENGTH=64 * 1024,
)

TRUSTED_HOSTS = [
    host.strip()
    for host in os.environ.get("LUMIERE_TRUSTED_HOSTS", "").split(",")
    if host.strip()
]
if TRUSTED_HOSTS:
    app.config["TRUSTED_HOSTS"] = TRUSTED_HOSTS

app.jinja_env.globals["site_name"] = SITE_NAME
app.jinja_env.globals["site_name_upper"] = SITE_NAME.upper()
app.jinja_env.globals["site_tagline"] = SITE_TAGLINE
app.jinja_env.globals["subscription_price"] = format_price_display()
app.jinja_env.globals["stripe_enabled"] = bool(STRIPE_SECRET_KEY)

# Pre-computed scrypt hash for default admin password ("IDC-201Two")
DEFAULT_ADMIN_USER = (
    os.environ.get("LUMIERE_ADMIN_USER")
    or os.environ.get("GMOVIES_ADMIN_USER")
    or "Isaac"
)
DEFAULT_ADMIN_HASH = (
    "scrypt:32768:8:1$OvPqfDWnVB6QlH9e$"
    "9f07249d16017996d27e5b6ccf4e8d73a8700c958b1bed481767fad7047e58d6"
    "3ccb4291c481fbf399d4438b52744a3982e19f2efd755ab41856c39fc04f0194"
)
# Dummy hash used when username does not match to prevent user-enumeration timing side-channels
DUMMY_SCRYPT_HASH = generate_password_hash("dummy_constant_time_pad_value", method="scrypt")

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_WINDOW_SECONDS = 900  # 15 minutes
MAX_SIGNUPS_PER_HOUR = 5
SIGNUP_WINDOW_SECONDS = 3600
MIN_PASSWORD_LENGTH = 10
USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{3,24}$")
COMMON_PASSWORDS = {
    "password",
    "password1",
    "password123",
    "1234567890",
    "123456789",
    "qwerty1234",
    "letmein123",
    "iloveyou",
    "admin12345",
    "welcome123",
    "changeme123",
    "gmovies123",
    "lumiere123",
}

TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "28fccf9ae9688fdaf7f990dc6307260c")
TMDB_READ_TOKEN = os.environ.get(
    "TMDB_READ_TOKEN",
    "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIyOGZjY2Y5YWU5Njg4ZmRhZjdmOTkwZGM2MzA3MjYwYyIsIm5iZiI6MTc5MzI5NzE5Ny42MDksInN1YiI6IjZhZTM4YjJkYjVhOTYwOTI5ZWQwYWI1NiIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.Po2wDlwZYWasGV-oZqV6Ep0ocF7ZEYBkBIfsumwJwME",
)


def get_db():
    conn = sqlite3.connect(DB_FILE, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.execute("PRAGMA busy_timeout=5000;")
    except Exception:
        pass
    return conn


def init_tables():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS movie_posters (
            id INTEGER PRIMARY KEY,
            poster_path TEXT,
            backdrop_path TEXT,
            release_date TEXT,
            vote_average REAL,
            updated_at REAL
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS movie_details_cache (
            id INTEGER PRIMARY KEY,
            details_json TEXT NOT NULL,
            created_at REAL NOT NULL
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS auth_users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'admin',
            created_at REAL NOT NULL,
            auth_version INTEGER DEFAULT 0
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS auth_rate_limits (
            ip TEXT PRIMARY KEY,
            attempts INTEGER DEFAULT 0,
            first_attempt_at REAL NOT NULL,
            locked_until REAL DEFAULT 0
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS auth_audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT NOT NULL,
            username TEXT NOT NULL,
            event TEXT NOT NULL,
            user_agent TEXT,
            created_at REAL NOT NULL
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            name TEXT NOT NULL,
            avatar_color TEXT DEFAULT '#e50914',
            is_kids INTEGER DEFAULT 0,
            created_at REAL NOT NULL
        );
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_user_profiles_username ON user_profiles(username)")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_watchlist (
            username TEXT NOT NULL,
            profile_id INTEGER DEFAULT 0,
            media_type TEXT NOT NULL,
            tmdb_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            poster_url TEXT,
            backdrop_url TEXT,
            year TEXT,
            vote_average REAL,
            overview TEXT,
            created_at REAL NOT NULL,
            PRIMARY KEY (username, profile_id, media_type, tmdb_id)
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS custom_streams (
            media_type TEXT NOT NULL,
            tmdb_id INTEGER NOT NULL,
            season INTEGER DEFAULT 1,
            episode INTEGER DEFAULT 1,
            stream_url TEXT NOT NULL,
            stream_type TEXT DEFAULT 'mp4',
            quality_label TEXT DEFAULT '1080p Full HD',
            added_by TEXT,
            updated_at REAL NOT NULL,
            PRIMARY KEY (media_type, tmdb_id, season, episode)
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS active_streams (
            stream_token TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            profile_id INTEGER DEFAULT 0,
            profile_name TEXT,
            media_type TEXT,
            tmdb_id INTEGER,
            title TEXT,
            client_ip TEXT,
            user_agent TEXT,
            started_at REAL NOT NULL,
            last_heartbeat REAL NOT NULL
        );
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_active_streams_username ON active_streams(username)")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS dash_stream_sessions (
            session_id TEXT PRIMARY KEY,
            base_url TEXT NOT NULL,
            manifest_url TEXT NOT NULL,
            headers_json TEXT NOT NULL,
            expires_at REAL NOT NULL
        );
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_dash_stream_expires ON dash_stream_sessions(expires_at)")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS watch_history (
            username TEXT NOT NULL,
            profile_id INTEGER DEFAULT 0,
            media_type TEXT NOT NULL,
            tmdb_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            poster_url TEXT,
            backdrop_url TEXT,
            year TEXT,
            vote_average REAL,
            overview TEXT,
            season INTEGER DEFAULT 1,
            episode INTEGER DEFAULT 1,
            episode_name TEXT,
            progress_seconds REAL DEFAULT 0,
            duration_seconds REAL DEFAULT 0,
            updated_at REAL NOT NULL,
            PRIMARY KEY (username, profile_id, media_type, tmdb_id)
        );
    """)
    history_columns = {
        row["name"] for row in cur.execute("PRAGMA table_info(watch_history)").fetchall()
    }
    if "progress_seconds" not in history_columns:
        cur.execute(
            "ALTER TABLE watch_history ADD COLUMN progress_seconds REAL DEFAULT 0"
        )
    if "duration_seconds" not in history_columns:
        cur.execute(
            "ALTER TABLE watch_history ADD COLUMN duration_seconds REAL DEFAULT 0"
        )
    if "profile_id" not in history_columns:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS watch_history_v2 (
                username TEXT NOT NULL,
                profile_id INTEGER DEFAULT 0,
                media_type TEXT NOT NULL,
                tmdb_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                poster_url TEXT,
                backdrop_url TEXT,
                year TEXT,
                vote_average REAL,
                overview TEXT,
                season INTEGER DEFAULT 1,
                episode INTEGER DEFAULT 1,
                episode_name TEXT,
                progress_seconds REAL DEFAULT 0,
                duration_seconds REAL DEFAULT 0,
                updated_at REAL NOT NULL,
                PRIMARY KEY (username, profile_id, media_type, tmdb_id)
            );
        """)
        cur.execute("""
            INSERT OR REPLACE INTO watch_history_v2 (
                username, profile_id, media_type, tmdb_id, title, poster_url, backdrop_url,
                year, vote_average, overview, season, episode, episode_name,
                progress_seconds, duration_seconds, updated_at
            )
            SELECT username, 0, media_type, tmdb_id, title, poster_url, backdrop_url,
                   year, vote_average, overview, season, episode, episode_name,
                   COALESCE(progress_seconds, 0), COALESCE(duration_seconds, 0), updated_at
            FROM watch_history
        """)
        cur.execute("DROP TABLE watch_history")
        cur.execute("ALTER TABLE watch_history_v2 RENAME TO watch_history")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS signup_rate_limits (
            ip TEXT PRIMARY KEY,
            attempts INTEGER DEFAULT 0,
            first_attempt_at REAL NOT NULL
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS stripe_webhook_events (
            event_id TEXT PRIMARY KEY,
            created_at REAL NOT NULL
        );
    """)
    auth_columns = {
        row["name"] for row in cur.execute("PRAGMA table_info(auth_users)").fetchall()
    }
    if "auth_version" not in auth_columns:
        cur.execute("ALTER TABLE auth_users ADD COLUMN auth_version INTEGER DEFAULT 0")
    if "subscription_status" not in auth_columns:
        cur.execute("ALTER TABLE auth_users ADD COLUMN subscription_status TEXT DEFAULT 'none'")
    if "stripe_customer_id" not in auth_columns:
        cur.execute("ALTER TABLE auth_users ADD COLUMN stripe_customer_id TEXT")
    if "stripe_subscription_id" not in auth_columns:
        cur.execute("ALTER TABLE auth_users ADD COLUMN stripe_subscription_id TEXT")
    if "stripe_checkout_session_id" not in auth_columns:
        cur.execute("ALTER TABLE auth_users ADD COLUMN stripe_checkout_session_id TEXT")
    if "subscription_end" not in auth_columns:
        cur.execute("ALTER TABLE auth_users ADD COLUMN subscription_end REAL DEFAULT 0")
    # Migrate legacy 'admin' account to DEFAULT_ADMIN_USER ('Isaac') if applicable
    if DEFAULT_ADMIN_USER.lower() != "admin":
        old_admin = cur.execute(
            "SELECT username, created_at FROM auth_users WHERE username = 'admin' COLLATE NOCASE"
        ).fetchone()
        new_admin = cur.execute(
            "SELECT username FROM auth_users WHERE username = ? COLLATE NOCASE",
            (DEFAULT_ADMIN_USER,),
        ).fetchone()
        if old_admin and not new_admin:
            cur.execute(
                """
                UPDATE auth_users
                SET username = ?, password_hash = ?, role = 'admin', subscription_status = 'comped', auth_version = COALESCE(auth_version, 0) + 1
                WHERE username = ?
                """,
                (DEFAULT_ADMIN_USER, DEFAULT_ADMIN_HASH, old_admin["username"]),
            )
            cur.execute(
                "UPDATE OR IGNORE watch_history SET username = ? WHERE username = ?",
                (DEFAULT_ADMIN_USER, old_admin["username"]),
            )
        elif old_admin and new_admin:
            cur.execute(
                "UPDATE OR IGNORE watch_history SET username = ? WHERE username = ?",
                (DEFAULT_ADMIN_USER, old_admin["username"]),
            )
            cur.execute("DELETE FROM auth_users WHERE username = ?", (old_admin["username"],))
            cur.execute(
                "UPDATE auth_users SET password_hash = ?, role = 'admin', subscription_status = 'comped' WHERE username = ? COLLATE NOCASE",
                (DEFAULT_ADMIN_HASH, DEFAULT_ADMIN_USER),
            )
    # Ensure default admin user is seeded with scrypt hash
    cur.execute(
        "INSERT OR IGNORE INTO auth_users (username, password_hash, role, created_at, subscription_status) VALUES (?, ?, 'admin', ?, 'comped')",
        (DEFAULT_ADMIN_USER, DEFAULT_ADMIN_HASH, time.time()),
    )
    cur.execute(
        "UPDATE auth_users SET subscription_status = 'comped' WHERE role = 'admin' AND COALESCE(subscription_status, 'none') = 'none'"
    )
    conn.commit()
    conn.close()
    try:
        os.chmod(DB_FILE, 0o600)
    except Exception:
        pass


init_tables()


def _is_trusted_proxy(addr: str) -> bool:
    try:
        ip_obj = ipaddress.ip_address(addr)
        return any(ip_obj in net for net in TRUSTED_PROXY_NETS)
    except ValueError:
        return False


def get_client_ip() -> str:
    """Return verified client IP; only trust X-Forwarded-For when direct peer is a trusted proxy."""
    peer = (request.environ.get("REMOTE_ADDR") or request.remote_addr or "127.0.0.1").strip()
    if _is_trusted_proxy(peer):
        forwarded = request.headers.get("X-Forwarded-For", "")
        if forwarded:
            hops = [h.strip() for h in forwarded.split(",") if h.strip()]
            for hop in reversed(hops):
                try:
                    ipaddress.ip_address(hop)
                    if not _is_trusted_proxy(hop) or hop == hops[0]:
                        return hop
                except ValueError:
                    continue
    return peer


def _ua_fingerprint() -> str:
    ua = (request.headers.get("User-Agent") or "")[:300]
    return hashlib.sha256(ua.encode("utf-8", errors="ignore")).hexdigest()[:24]


def validate_password(password: str, username: str = ""):
    if len(password or "") < MIN_PASSWORD_LENGTH:
        return f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
    if len(password) > 200:
        return "Password is too long."
    lowered = password.lower()
    if lowered in COMMON_PASSWORDS:
        return "That password is too common. Choose something more unique."
    if username and username.lower() in lowered:
        return "Password must not contain your username."
    return None


def validate_new_user(username: str, password: str):
    if not USERNAME_RE.fullmatch(username or ""):
        return "Username must be 3–24 characters using letters, numbers, dots, dashes, or underscores."
    return validate_password(password, username)


def create_auth_user(
    username: str, password: str, role: str = "user", subscription_status: str = "none"
):
    error = validate_new_user(username, password)
    if error:
        return error
    if role not in ("user", "admin"):
        role = "user"
    if role == "admin":
        subscription_status = "comped"
    elif subscription_status not in ("none", "comped", "active"):
        subscription_status = "none"
    conn = get_db()
    try:
        existing = conn.execute(
            "SELECT 1 FROM auth_users WHERE username = ? COLLATE NOCASE", (username,)
        ).fetchone()
        if existing:
            return "That username is already taken."
        conn.execute(
            "INSERT INTO auth_users (username, password_hash, role, created_at, subscription_status) VALUES (?, ?, ?, ?, ?)",
            (
                username,
                generate_password_hash(password, method="scrypt"),
                role,
                time.time(),
                subscription_status,
            ),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        return "That username is already taken."
    finally:
        conn.close()
    return None


def check_signup_rate_limit(ip: str):
    now = time.time()
    conn = get_db()
    row = conn.execute(
        "SELECT attempts, first_attempt_at FROM signup_rate_limits WHERE ip = ?", (ip,)
    ).fetchone()
    conn.close()
    if not row or now - (row["first_attempt_at"] or 0) > SIGNUP_WINDOW_SECONDS:
        return True, 0
    if (row["attempts"] or 0) >= MAX_SIGNUPS_PER_HOUR:
        return False, int(SIGNUP_WINDOW_SECONDS - (now - row["first_attempt_at"])) + 1
    return True, 0


def record_signup_attempt(ip: str):
    now = time.time()
    conn = get_db()
    row = conn.execute(
        "SELECT attempts, first_attempt_at FROM signup_rate_limits WHERE ip = ?", (ip,)
    ).fetchone()
    if not row or now - (row["first_attempt_at"] or 0) > SIGNUP_WINDOW_SECONDS:
        attempts, first_at = 1, now
    else:
        attempts, first_at = (row["attempts"] or 0) + 1, row["first_attempt_at"]
    conn.execute(
        "INSERT OR REPLACE INTO signup_rate_limits (ip, attempts, first_attempt_at) VALUES (?, ?, ?)",
        (ip, attempts, first_at),
    )
    conn.commit()
    conn.close()


def start_user_session(
    username: str, role: str, remember: bool = True, auth_version: int = 0
):
    session.clear()
    session.permanent = remember
    session["authenticated"] = True
    session["user"] = username
    session["role"] = role
    session["auth_version"] = int(auth_version or 0)
    session["login_at"] = int(time.time())
    session["ua_hash"] = _ua_fingerprint()
    session["csrf_token"] = secrets.token_hex(32)
    session["profile_selected"] = False


def get_csrf_token() -> str:
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)
    return session["csrf_token"]


app.jinja_env.globals["csrf_token"] = get_csrf_token
app.jinja_env.filters["datefmt"] = lambda ts: time.strftime(
    "%b %d, %Y", time.localtime(ts or 0)
)
app.jinja_env.filters["datetimefmt"] = lambda ts: time.strftime(
    "%b %d, %Y · %H:%M", time.localtime(ts or 0)
)


def _same_origin_request() -> bool:
    """Defense-in-depth check that Origin/Referer (when sent) matches request.host."""
    req_host = (request.host or "").split(",")[0].strip().lower()
    if not req_host:
        return True
    origin = request.headers.get("Origin")
    if origin and origin != "null":
        parsed = urllib.parse.urlparse(origin)
        if parsed.netloc and parsed.netloc.lower() != req_host:
            return False
    elif not origin:
        referer = request.headers.get("Referer")
        if referer:
            parsed = urllib.parse.urlparse(referer)
            if parsed.netloc and parsed.netloc.lower() != req_host:
                return False
    return True


def verify_csrf() -> bool:
    if not _same_origin_request():
        return False
    token = (
        request.headers.get("X-CSRF-Token")
        or request.form.get("csrf_token")
        or (request.get_json(silent=True) or {}).get("csrf_token")
        or ""
    )
    expected = session.get("csrf_token", "")
    if not token or not expected:
        return False
    return hmac.compare_digest(str(token), str(expected))


def _check_bucket_rate_limit(cur, key: str, now: float):
    cur.execute(
        "SELECT attempts, first_attempt_at, locked_until FROM auth_rate_limits WHERE ip = ?",
        (key,),
    )
    row = cur.fetchone()
    if not row:
        return False, 0, MAX_FAILED_ATTEMPTS

    locked_until = row["locked_until"] or 0
    if locked_until > now:
        return True, int(locked_until - now) + 1, 0

    if now - (row["first_attempt_at"] or 0) > LOCKOUT_WINDOW_SECONDS:
        cur.execute("DELETE FROM auth_rate_limits WHERE ip = ?", (key,))
        return False, 0, MAX_FAILED_ATTEMPTS

    attempts = row["attempts"] or 0
    return False, 0, max(0, MAX_FAILED_ATTEMPTS - attempts)


def check_rate_limit(ip: str, username: str = ""):
    """Returns (is_locked: bool, retry_after_seconds: int, remaining_attempts: int)."""
    now = time.time()
    conn = get_db()
    cur = conn.cursor()
    ip_locked, ip_retry, ip_rem = _check_bucket_rate_limit(cur, ip, now)
    user_locked, user_retry, user_rem = (False, 0, MAX_FAILED_ATTEMPTS)
    if username:
        user_key = f"user:{username.strip().lower()[:64]}"
        user_locked, user_retry, user_rem = _check_bucket_rate_limit(cur, user_key, now)
    conn.commit()
    conn.close()
    if ip_locked or user_locked:
        return True, max(ip_retry, user_retry), 0
    return False, 0, min(ip_rem, user_rem)


def _record_bucket_attempt(cur, key: str, now: float, success: bool):
    if success:
        cur.execute("DELETE FROM auth_rate_limits WHERE ip = ?", (key,))
        return
    cur.execute(
        "SELECT attempts, first_attempt_at FROM auth_rate_limits WHERE ip = ?",
        (key,),
    )
    row = cur.fetchone()
    if not row or (now - (row["first_attempt_at"] or 0) > LOCKOUT_WINDOW_SECONDS):
        attempts = 1
        first_at = now
    else:
        attempts = (row["attempts"] or 0) + 1
        first_at = row["first_attempt_at"]

    locked_until = (
        (now + LOCKOUT_WINDOW_SECONDS) if attempts >= MAX_FAILED_ATTEMPTS else 0
    )
    cur.execute(
        """
        INSERT OR REPLACE INTO auth_rate_limits (ip, attempts, first_attempt_at, locked_until)
        VALUES (?, ?, ?, ?)
        """,
        (key, attempts, first_at, locked_until),
    )


def record_login_attempt(ip: str, username: str, success: bool, event_override: str = None):
    now = time.time()
    ua = (request.headers.get("User-Agent") or "")[:250]
    conn = get_db()
    cur = conn.cursor()

    event_name = event_override or ("login_success" if success else "login_failed")
    cur.execute(
        "INSERT INTO auth_audit_log (ip, username, event, user_agent, created_at) VALUES (?, ?, ?, ?, ?)",
        (ip, (username or "unknown")[:64], event_name, ua, now),
    )

    _record_bucket_attempt(cur, ip, now, success)
    if username and username != "unknown":
        user_key = f"user:{username.strip().lower()[:64]}"
        _record_bucket_attempt(cur, user_key, now, success)

    # Periodic cleanup of expired rate limits & bounded audit log size
    cur.execute(
        "DELETE FROM auth_rate_limits WHERE first_attempt_at < ? AND locked_until < ?",
        (now - LOCKOUT_WINDOW_SECONDS, now),
    )
    cur.execute(
        "DELETE FROM signup_rate_limits WHERE first_attempt_at < ?",
        (now - SIGNUP_WINDOW_SECONDS,),
    )
    cur.execute(
        """
        DELETE FROM auth_audit_log
        WHERE id NOT IN (
            SELECT id FROM auth_audit_log ORDER BY id DESC LIMIT 5000
        )
        """
    )

    conn.commit()
    conn.close()


SAFE_STRIPE_PATH_RE = re.compile(r"^[A-Za-z0-9_/?=&\[\]-]+$")
SAFE_HOST_RE = re.compile(r"^[A-Za-z0-9.-]+(?::[0-9]{1,5})?$")
PUBLIC_BASE_URL = os.environ.get("LUMIERE_PUBLIC_URL", "").strip().rstrip("/")

_sliding_windows = {}
_sliding_lock = threading.Lock()


def check_sliding_rate_limit(key: str, max_hits: int, window_sec: float) -> bool:
    """Thread-safe sliding window rate limiter; returns True if allowed, False if rate-limited."""
    now = time.time()
    cutoff = now - window_sec
    with _sliding_lock:
        if len(_sliding_windows) > 4000:
            for k in list(_sliding_windows.keys())[:1000]:
                _sliding_windows.pop(k, None)
        hits = [t for t in _sliding_windows.get(key, []) if t > cutoff]
        if len(hits) >= max_hits:
            _sliding_windows[key] = hits
            return False
        hits.append(now)
        _sliding_windows[key] = hits
        return True


def stripe_api_request(endpoint: str, data: dict = None, method: str = "GET") -> dict:
    """Perform an authenticated HTTPS request to the Stripe v1 REST API."""
    if not STRIPE_SECRET_KEY:
        raise RuntimeError("Stripe secret key is not configured.")
    clean_ep = (endpoint or "").lstrip("/")
    if not clean_ep or ".." in clean_ep or not SAFE_STRIPE_PATH_RE.fullmatch(clean_ep):
        raise ValueError("Invalid Stripe API endpoint")
    url = f"https://api.stripe.com/v1/{clean_ep}"
    headers = {
        "Authorization": f"Bearer {STRIPE_SECRET_KEY}",
        "User-Agent": "Lumiere/1.0",
    }
    body = None
    if data is not None:
        encoded = urllib.parse.urlencode(data)
        if method.upper() == "GET":
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}{encoded}"
        else:
            body = encoded.encode("utf-8")
            headers["Content-Type"] = "application/x-www-form-urlencoded"
    elif method.upper() == "POST":
        body = b""

    req = urllib.request.Request(url, data=body, headers=headers, method=method.upper())
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="ignore")
        try:
            err_json = json.loads(err_body)
            msg = (err_json.get("error") or {}).get("message") or f"Stripe HTTP {exc.code}"
        except Exception:
            msg = f"Stripe HTTP {exc.code}"
        raise RuntimeError(msg) from exc


def _external_base_url() -> str:
    if PUBLIC_BASE_URL and PUBLIC_BASE_URL.startswith(("http://", "https://")):
        return PUBLIC_BASE_URL
    peer = (request.environ.get("REMOTE_ADDR") or request.remote_addr or "").strip()
    proto = "https" if request.is_secure else "http"
    if _is_trusted_proxy(peer):
        fwd_proto = request.headers.get("X-Forwarded-Proto", "").split(",")[0].strip().lower()
        if fwd_proto in ("http", "https"):
            proto = fwd_proto
    host = (request.host or "localhost:5000").split(",")[0].strip()
    if not SAFE_HOST_RE.fullmatch(host):
        host = "localhost:5000"
    return f"{proto}://{host}"


def is_user_subscribed(user_row) -> bool:
    if not STRIPE_SECRET_KEY:
        return True
    if not user_row:
        return False
    if user_row["role"] == "admin":
        return True
    status = (user_row["subscription_status"] or "none").lower()
    if status == "comped":
        return True
    if status in ("active", "trialing"):
        sub_end = float(user_row["subscription_end"] or 0)
        if sub_end <= 0 or sub_end > time.time():
            return True
    return False


def sync_user_subscription(username: str) -> dict:
    """Query Stripe for the latest subscription/checkout status of username and update SQLite."""
    conn = get_db()
    row = conn.execute(
        """
        SELECT username, role, subscription_status, stripe_customer_id,
               stripe_subscription_id, stripe_checkout_session_id, subscription_end
        FROM auth_users WHERE username = ?
        """,
        (username,),
    ).fetchone()
    conn.close()
    if not row or not STRIPE_SECRET_KEY:
        return dict(row) if row else {}
    if row["role"] == "admin" or row["subscription_status"] == "comped":
        return dict(row)

    sub_id = row["stripe_subscription_id"]
    cs_id = row["stripe_checkout_session_id"]
    cust_id = row["stripe_customer_id"]
    new_status = row["subscription_status"] or "none"
    new_end = float(row["subscription_end"] or 0)

    try:
        if not sub_id and cs_id:
            cs = stripe_api_request(
                f"checkout/sessions/{cs_id}", {"expand[]": "subscription"}, method="GET"
            )
            cust_id = cs.get("customer") or cust_id
            sub_obj = cs.get("subscription")
            if isinstance(sub_obj, dict):
                sub_id = sub_obj.get("id")
                new_status = sub_obj.get("status") or new_status
                new_end = float(sub_obj.get("current_period_end") or new_end)
            elif isinstance(sub_obj, str):
                sub_id = sub_obj
            elif cs.get("payment_status") == "paid":
                new_status = "active"
                new_end = max(new_end, time.time() + 31 * 86400)

        if sub_id:
            sub = stripe_api_request(f"subscriptions/{sub_id}", method="GET")
            cust_id = sub.get("customer") or cust_id
            new_status = sub.get("status") or new_status
            new_end = float(sub.get("current_period_end") or new_end)
    except Exception:
        pass

    conn = get_db()
    conn.execute(
        """
        UPDATE auth_users
        SET subscription_status = ?, stripe_customer_id = ?, stripe_subscription_id = ?, subscription_end = ?
        WHERE username = ?
        """,
        (new_status, cust_id, sub_id, new_end, username),
    )
    updated = conn.execute(
        """
        SELECT username, role, subscription_status, stripe_customer_id,
               stripe_subscription_id, stripe_checkout_session_id, subscription_end
        FROM auth_users WHERE username = ?
        """,
        (username,),
    ).fetchone()
    conn.commit()
    conn.close()
    return dict(updated) if updated else {}


SUBSCRIPTION_EXEMPT_PREFIXES = (
    "/subscribe",
    "/account",
    "/admin",
    "/logout",
    "/download",
    "/apps",
    "/landing",
    "/welcome",
)


def is_authenticated_user() -> bool:
    username = session.get("user")
    if not session.get("authenticated") or not username:
        return False
    login_at = int(session.get("login_at") or 0)
    if login_at <= 0 or (time.time() - login_at) > MAX_SESSION_AGE_SECONDS:
        return False
    expected_ua = session.get("ua_hash")
    if expected_ua and not hmac.compare_digest(str(expected_ua), _ua_fingerprint()):
        return False
    try:
        conn = get_db()
        row = conn.execute(
            "SELECT COALESCE(auth_version, 0) AS auth_version FROM auth_users WHERE username = ?",
            (username,),
        ).fetchone()
        conn.close()
        if not row or int(row["auth_version"] or 0) != int(session.get("auth_version", 0)):
            return False
    except Exception:
        return False
    return True


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        username = session.get("user")
        if not session.get("authenticated") or not username:
            if request.path.startswith("/api/"):
                return jsonify({"error": "Authentication required", "login_url": "/login"}), 401
            if request.path.startswith("/admin"):
                return "Not Found", 404
            return redirect(url_for("login"))

        login_at = int(session.get("login_at") or 0)
        if login_at <= 0 or (time.time() - login_at) > MAX_SESSION_AGE_SECONDS:
            session.clear()
            if request.path.startswith("/api/"):
                return jsonify({"error": "Session expired", "login_url": "/login"}), 401
            return redirect(url_for("login", revoked=1))

        expected_ua = session.get("ua_hash")
        if expected_ua and not hmac.compare_digest(str(expected_ua), _ua_fingerprint()):
            session.clear()
            if request.path.startswith("/api/"):
                return jsonify({"error": "Session device mismatch", "login_url": "/login"}), 401
            return redirect(url_for("login", revoked=1))

        conn = get_db()
        row = conn.execute(
            """
            SELECT username, role, COALESCE(auth_version, 0) AS auth_version,
                   COALESCE(subscription_status, 'none') AS subscription_status,
                   COALESCE(subscription_end, 0) AS subscription_end,
                   stripe_subscription_id, stripe_checkout_session_id
            FROM auth_users WHERE username = ?
            """,
            (username,),
        ).fetchone()
        conn.close()
        if not row:
            session.clear()
            if request.path.startswith("/api/"):
                return jsonify({"error": "Account no longer exists", "login_url": "/login"}), 401
            return redirect(url_for("login"))

        if int(row["auth_version"] or 0) != int(session.get("auth_version", 0)):
            session.clear()
            if request.path.startswith("/api/"):
                return jsonify({"error": "Session expired or revoked", "login_url": "/login"}), 401
            return redirect(url_for("login", revoked=1))

        session["role"] = row["role"]

        # Per-IP API flood / scraper rate limit (120 requests per 60s)
        if request.path.startswith("/api/"):
            ip = get_client_ip()
            if not check_sliding_rate_limit(f"api:{ip}", 120, 60.0):
                return jsonify({"error": "Rate limit exceeded. Please slow down."}), 429

        # Enforce active $30/mo subscription on catalog and streaming endpoints
        if not any(request.path.startswith(p) for p in SUBSCRIPTION_EXEMPT_PREFIXES):
            if not is_user_subscribed(row):
                # If user previously had a subscription or pending checkout, sync once with Stripe
                if row["stripe_subscription_id"] or row["stripe_checkout_session_id"]:
                    synced = sync_user_subscription(username)
                    if is_user_subscribed(synced):
                        return f(*args, **kwargs)
                if request.path.startswith("/api/"):
                    return (
                        jsonify(
                            {
                                "error": f"Active {format_price_display()}/month subscription required",
                                "subscribe_url": "/subscribe",
                            }
                        ),
                        402,
                    )
                return redirect(url_for("subscribe"))

        return f(*args, **kwargs)

    return decorated


@app.after_request
def apply_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
    response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
    csp = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com data:; "
        "img-src 'self' https://image.tmdb.org https://upload.wikimedia.org data: blob:; "
        "media-src 'self' https: blob:; "
        "connect-src 'self' https://api.themoviedb.org https:; "
        "frame-src 'self' https://www.youtube-nocookie.com https://www.youtube.com https://vidfast.vc https://*.vidfast.vc https://vidfast.pro https://vidfast.in https://vidfast.io https://vidfast.me https://vidfast.net https://vidfast.pm https://vidfast.xyz https://vidfast.bz https://vidlink.pro https://*.vidlink.pro https://vidsrc.cc https://*.vidsrc.cc https://vidsrc.xyz https://*.vidsrc.xyz https://multiembed.mov https://*.multiembed.mov; "
        "frame-ancestors 'self'; "
        "base-uri 'self'; "
        "form-action 'self' https://checkout.stripe.com https://billing.stripe.com; "
        "object-src 'none';"
    )
    response.headers["Content-Security-Policy"] = csp
    peer = (request.environ.get("REMOTE_ADDR") or request.remote_addr or "").strip()
    is_https = request.is_secure or (
        _is_trusted_proxy(peer) and request.headers.get("X-Forwarded-Proto", "").lower() == "https"
    )
    if is_https:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    if (
        request.path.startswith("/api/")
        or request.path.startswith("/account")
        or request.path.startswith("/admin")
        or request.path.startswith("/subscribe")
        or request.path in ("/login", "/logout", "/signup")
    ):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
    return response


@app.route("/favicon.ico")
def favicon_ico():
    return send_from_directory(
        os.path.join(BASE_DIR, "static"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )


@app.route("/favicon.svg")
def favicon_svg():
    return send_from_directory(
        os.path.join(BASE_DIR, "static"),
        "favicon.svg",
        mimetype="image/svg+xml",
    )


@app.route("/apple-touch-icon.png")
def apple_touch_icon():
    return send_from_directory(
        os.path.join(BASE_DIR, "static"),
        "apple-touch-icon.png",
        mimetype="image/png",
    )


@app.route("/site.webmanifest")
def site_webmanifest():
    return send_from_directory(
        os.path.join(BASE_DIR, "static"),
        "site.webmanifest",
        mimetype="application/manifest+json",
    )


@app.route("/robots.txt")
def robots_txt():
    return "User-agent: *\nDisallow: /\n", 200, {"Content-Type": "text/plain; charset=utf-8"}


@app.route("/healthz")
def healthz():
    return jsonify({"status": "ok", "site": SITE_NAME})


@app.route("/terms")
def terms_of_service():
    return render_template("terms.html", active_tab="terms")


@app.route("/privacy")
def privacy_policy():
    return render_template("terms.html", active_tab="privacy")


@app.route("/rules")
def site_rules():
    return redirect(url_for("terms_of_service"))


ALLOWED_DOWNLOAD_FILES = {
    "Lumiere.apk": ("application/vnd.android.package-archive", "Lumiere.apk"),
    "Lumiere-Setup.exe": ("application/vnd.microsoft.portable-executable", "Lumiere-Setup.exe"),
    "Lumiere.dmg": ("application/x-apple-diskimage", "Lumiere.dmg"),
    "Lumiere-mac.zip": ("application/zip", "Lumiere-mac.zip"),
}


@app.route("/apps")
def apps_page():
    return render_template("apps.html")


@app.route("/download/<path:filename>")
def download_app_file(filename):
    clean = os.path.basename(filename)
    if clean not in ALLOWED_DOWNLOAD_FILES:
        return "File not found", 404
    mimetype, download_name = ALLOWED_DOWNLOAD_FILES[clean]
    dl_dir = os.path.join(BASE_DIR, "data", "downloads")
    if not os.path.exists(os.path.join(dl_dir, clean)):
        return "File not found on server", 404
    return send_from_directory(
        dl_dir, clean, mimetype=mimetype, as_attachment=True, download_name=download_name
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if is_authenticated_user():
        return redirect(url_for("index"))

    # If the user has a stale, expired, or invalid session, clear it now
    # to prevent a redirect loop between /login and /
    if session.get("authenticated") or session.get("user"):
        session.clear()

    if request.method == "GET":
        warm_home_catalog_async()

    ip = get_client_ip()
    is_locked, retry_after, remaining = check_rate_limit(ip)
    error = None
    notice = None
    if request.args.get("deleted"):
        notice = "Your account was deleted. Thanks for watching."
    elif request.args.get("revoked"):
        notice = "Your session was signed out for security. Please sign in again."

    if request.method == "POST":
        is_json = request.is_json
        if is_json:
            payload = request.get_json(silent=True) or {}
            username = (payload.get("username") or "").strip()
            password = payload.get("password") or ""
            remember = bool(payload.get("remember", True))
        else:
            username = (request.form.get("username") or "").strip()
            password = request.form.get("password") or ""
            remember = bool(request.form.get("remember"))

        is_locked, retry_after, remaining = check_rate_limit(ip, username)
        if is_locked:
            mins = max(1, (retry_after + 59) // 60)
            msg = f"Too many failed sign-in attempts. Locked for {mins} minute(s)."
            if is_json:
                return jsonify({"error": msg, "retry_after": retry_after}), 429
            return render_template("login.html", error=msg, locked=True, notice=notice), 429

        if not verify_csrf():
            msg = "Security token expired or invalid. Please reload and try again."
            if is_json:
                return jsonify({"error": msg}), 400
            return render_template("login.html", error=msg, notice=notice), 400

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT username, password_hash, role, COALESCE(auth_version, 0) AS auth_version FROM auth_users WHERE username = ? COLLATE NOCASE",
            (username,),
        )
        user_row = cur.fetchone()
        conn.close()

        # Constant-time credential verification
        target_hash = user_row["password_hash"] if user_row else DUMMY_SCRYPT_HASH
        password_ok = check_password_hash(target_hash, password)
        username_ok = bool(user_row) and hmac.compare_digest(
            user_row["username"].casefold(), username.casefold()
        )

        if username_ok and password_ok:
            record_login_attempt(ip, user_row["username"], True)
            start_user_session(
                user_row["username"],
                user_row["role"],
                remember,
                user_row["auth_version"],
            )
            if is_json:
                return jsonify({"ok": True, "redirect": url_for("index")})
            return redirect(url_for("index"))

        record_login_attempt(ip, username or "unknown", False)
        is_locked, retry_after, remaining = check_rate_limit(ip, username)
        if is_locked:
            error = "Maximum failed attempts reached. Account access temporarily locked for 15 minutes."
            status_code = 429
        else:
            error = f"Invalid username or password. ({remaining} attempt{'s' if remaining != 1 else ''} remaining)"
            status_code = 401

        if is_json:
            return jsonify({"error": error, "remaining_attempts": remaining}), status_code
        return render_template("login.html", error=error, username=username, notice=notice), status_code

    return render_template("login.html", error=error, locked=is_locked, notice=notice)


@app.route("/logout", methods=["POST"])
def logout():
    if not verify_csrf():
        return jsonify({"error": "Invalid CSRF token"}), 400
    session.clear()
    if request.is_json or request.headers.get("Accept") == "application/json":
        return jsonify({"ok": True, "redirect": url_for("index")})
    return redirect(url_for("index"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if is_authenticated_user():
        return redirect(url_for("index"))

    if session.get("authenticated") or session.get("user"):
        session.clear()

    ip = get_client_ip()
    error = None
    username = (request.args.get("username") or request.args.get("email") or "").strip()[:24]

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        confirm = request.form.get("confirm_password") or ""
        accept_terms = request.form.get("accept_terms")

        if not verify_csrf():
            return render_template(
                "signup.html",
                error="Security token expired or invalid. Please reload and try again.",
                username=username,
            ), 400

        if not accept_terms:
            return render_template(
                "signup.html",
                error="You must agree to the Terms of Service, Site Rules, and Privacy Policy to create an account.",
                username=username,
            ), 400

        allowed, retry_after = check_signup_rate_limit(ip)
        if not allowed:
            mins = max(1, (retry_after + 59) // 60)
            return render_template(
                "signup.html",
                error=f"Too many accounts created from this network. Try again in {mins} minute(s).",
                username=username,
            ), 429

        if password != confirm:
            error = "Passwords do not match."
        else:
            error = create_auth_user(username, password, "user")

        if not error:
            record_signup_attempt(ip)
            record_login_attempt(ip, username, True, event_override="signup_success")
            start_user_session(username, "user", True, 0)
            if STRIPE_SECRET_KEY:
                return redirect(url_for("subscribe"))
            return redirect(url_for("index"))

    return render_template("signup.html", error=error, username=username)


def _get_user_billing_row(username: str):
    conn = get_db()
    row = conn.execute(
        """
        SELECT username, role, created_at, COALESCE(auth_version, 0) AS auth_version,
               COALESCE(subscription_status, 'none') AS subscription_status,
               stripe_customer_id, stripe_subscription_id,
               stripe_checkout_session_id, COALESCE(subscription_end, 0) AS subscription_end
        FROM auth_users WHERE username = ?
        """,
        (username,),
    ).fetchone()
    conn.close()
    return row


@app.route("/subscribe")
@login_required
def subscribe():
    username = session.get("user")
    user = _get_user_billing_row(username)
    if not user:
        session.clear()
        return redirect(url_for("login"))

    notice = None
    error = None
    if request.args.get("canceled"):
        notice = "Checkout was canceled. You have not been charged."
    elif request.args.get("synced"):
        if is_user_subscribed(user):
            return redirect(url_for("index"))
        error = "No active subscription was found yet. Click Subscribe below to complete checkout."
    elif request.args.get("error"):
        error = "Unable to verify payment status. Please try again or contact support."

    return render_template(
        "subscribe.html",
        user=user,
        is_subscribed=is_user_subscribed(user),
        price_display=format_price_display(),
        stripe_publishable_key=STRIPE_PUBLISHABLE_KEY,
        notice=notice,
        error=error,
    )


@app.route("/subscribe/checkout", methods=["POST"])
@login_required
def subscribe_checkout():
    if not verify_csrf():
        return render_template(
            "subscribe.html",
            user=_get_user_billing_row(session.get("user")),
            is_subscribed=False,
            price_display=format_price_display(),
            error="Security token expired or invalid. Please reload and try again.",
        ), 400

    username = session.get("user")
    user = _get_user_billing_row(username)
    if not user:
        session.clear()
        return redirect(url_for("login"))

    if is_user_subscribed(user):
        return redirect(url_for("index"))

    if not check_sliding_rate_limit(f"billing:{username}:{get_client_ip()}", 8, 900.0):
        return render_template(
            "subscribe.html",
            user=user,
            is_subscribed=False,
            price_display=format_price_display(),
            error="Too many checkout requests. Please wait a few minutes and try again.",
        ), 429

    base_url = _external_base_url()
    payload = {
        "mode": "subscription",
        "success_url": f"{base_url}/subscribe/success?session_id={{CHECKOUT_SESSION_ID}}",
        "cancel_url": f"{base_url}/subscribe?canceled=1",
        "client_reference_id": username,
        "metadata[username]": username,
        "subscription_data[metadata][username]": username,
        "line_items[0][quantity]": "1",
        "line_items[0][price_data][currency]": STRIPE_CURRENCY,
        "line_items[0][price_data][unit_amount]": str(STRIPE_PRICE_CENTS),
        "line_items[0][price_data][recurring][interval]": "month",
        "line_items[0][price_data][product_data][name]": f"{SITE_NAME} Monthly Membership",
        "line_items[0][price_data][product_data][description]": (
            f"Unlimited HD streaming across movies and series ({format_price_display()}/month)"
        ),
    }
    if user["stripe_customer_id"]:
        payload["customer"] = user["stripe_customer_id"]

    try:
        checkout_session = stripe_api_request("checkout/sessions", payload, method="POST")
    except Exception:
        return render_template(
            "subscribe.html",
            user=user,
            is_subscribed=False,
            price_display=format_price_display(),
            error="Unable to start Stripe Checkout right now. Please try again in a moment.",
        ), 502

    cs_id = checkout_session.get("id")
    cs_url = checkout_session.get("url") or ""
    if not cs_id or not cs_url.startswith("https://checkout.stripe.com/"):
        return render_template(
            "subscribe.html",
            user=user,
            is_subscribed=False,
            price_display=format_price_display(),
            error="Stripe did not return a valid checkout URL.",
        ), 502

    conn = get_db()
    conn.execute(
        "UPDATE auth_users SET stripe_checkout_session_id = ? WHERE username = ?",
        (cs_id, username),
    )
    conn.execute(
        "INSERT INTO auth_audit_log (ip, username, event, user_agent, created_at) VALUES (?, ?, ?, ?, ?)",
        (
            get_client_ip(),
            username[:64],
            "stripe_checkout_started",
            (request.headers.get("User-Agent") or "")[:250],
            time.time(),
        ),
    )
    conn.commit()
    conn.close()
    return redirect(cs_url, code=303)


@app.route("/subscribe/success")
@login_required
def subscribe_success():
    username = session.get("user")
    user = _get_user_billing_row(username)
    if not user:
        session.clear()
        return redirect(url_for("login"))

    session_id = (request.args.get("session_id") or "").strip()
    if not session_id or not re.fullmatch(r"^cs_[A-Za-z0-9_]+$", session_id):
        return redirect(url_for("subscribe", error=1))

    try:
        cs = stripe_api_request(
            f"checkout/sessions/{session_id}", {"expand[]": "subscription"}, method="GET"
        )
    except Exception:
        return redirect(url_for("subscribe", error=1))

    ref_user = (
        (cs.get("metadata") or {}).get("username")
        or cs.get("client_reference_id")
        or ""
    )
    if (
        ref_user.casefold() != username.casefold()
        and session_id != (user["stripe_checkout_session_id"] or "")
    ):
        return redirect(url_for("subscribe", error=1))

    sub_obj = cs.get("subscription")
    sub_id = None
    sub_status = "none"
    sub_end = 0.0
    if isinstance(sub_obj, dict):
        sub_id = sub_obj.get("id")
        sub_status = sub_obj.get("status") or "none"
        sub_end = float(sub_obj.get("current_period_end") or 0)
    elif isinstance(sub_obj, str):
        sub_id = sub_obj

    if cs.get("payment_status") == "paid" and sub_status not in ("active", "trialing"):
        sub_status = "active"
        if sub_end <= 0:
            sub_end = time.time() + 31 * 86400

    cust_id = cs.get("customer") or user["stripe_customer_id"]

    if sub_status in ("active", "trialing"):
        conn = get_db()
        conn.execute(
            """
            UPDATE auth_users
            SET subscription_status = ?, stripe_customer_id = ?,
                stripe_subscription_id = ?, stripe_checkout_session_id = ?,
                subscription_end = ?
            WHERE username = ?
            """,
            (sub_status, cust_id, sub_id, session_id, sub_end, username),
        )
        conn.execute(
            "INSERT INTO auth_audit_log (ip, username, event, user_agent, created_at) VALUES (?, ?, ?, ?, ?)",
            (
                get_client_ip(),
                username[:64],
                "subscription_activated",
                (request.headers.get("User-Agent") or "")[:250],
                time.time(),
            ),
        )
        conn.commit()
        conn.close()
        return redirect(url_for("index"))

    return redirect(url_for("subscribe", synced=1))


@app.route("/subscribe/sync", methods=["POST"])
@login_required
def subscribe_sync():
    if not verify_csrf():
        return redirect(url_for("subscribe", error=1))
    username = session.get("user")
    if not check_sliding_rate_limit(f"billing:{username}:{get_client_ip()}", 8, 900.0):
        return redirect(url_for("subscribe", error=1))
    synced = sync_user_subscription(username)
    if is_user_subscribed(synced):
        return redirect(url_for("index"))
    return redirect(url_for("subscribe", synced=1))


def _verify_stripe_signature(payload_bytes: bytes, sig_header: str, secret: str) -> bool:
    if not sig_header or not secret:
        return False
    timestamp = None
    signatures = []
    for part in sig_header.split(","):
        if "=" not in part:
            continue
        k, v = part.strip().split("=", 1)
        if k == "t":
            timestamp = v
        elif k == "v1":
            signatures.append(v)
    if not timestamp or not signatures:
        return False
    try:
        ts_int = int(timestamp)
    except ValueError:
        return False
    if abs(time.time() - ts_int) > 300:
        return False
    signed_payload = f"{timestamp}.".encode("utf-8") + payload_bytes
    expected = hmac.new(
        secret.encode("utf-8"), signed_payload, hashlib.sha256
    ).hexdigest()
    return any(hmac.compare_digest(expected, sig) for sig in signatures)


@app.route("/api/stripe/webhook", methods=["POST"])
def stripe_webhook():
    payload_bytes = request.get_data(cache=False)
    if not STRIPE_WEBHOOK_SECRET:
        return jsonify({"error": "Webhook secret not configured"}), 400
    sig_header = request.headers.get("Stripe-Signature", "")
    if not _verify_stripe_signature(payload_bytes, sig_header, STRIPE_WEBHOOK_SECRET):
        return jsonify({"error": "Invalid signature"}), 400

    try:
        event = json.loads(payload_bytes.decode("utf-8"))
    except Exception:
        return jsonify({"error": "Invalid JSON"}), 400

    event_id = str(event.get("id") or "").strip()[:120]
    event_type = event.get("type") or ""
    obj = (event.get("data") or {}).get("object") or {}

    conn = get_db()
    try:
        if event_id:
            already = conn.execute(
                "SELECT 1 FROM stripe_webhook_events WHERE event_id = ?", (event_id,)
            ).fetchone()
            if already:
                return jsonify({"received": True, "duplicate": True})
            conn.execute(
                "INSERT INTO stripe_webhook_events (event_id, created_at) VALUES (?, ?)",
                (event_id, time.time()),
            )
            conn.execute(
                "DELETE FROM stripe_webhook_events WHERE created_at < ?",
                (time.time() - 7 * 86400,),
            )
            conn.commit()
        if event_type == "checkout.session.completed":
            username = (
                (obj.get("metadata") or {}).get("username")
                or obj.get("client_reference_id")
            )
            cust_id = obj.get("customer")
            sub_id = obj.get("subscription")
            cs_id = obj.get("id")
            if username and obj.get("payment_status") == "paid":
                conn.execute(
                    """
                    UPDATE auth_users
                    SET subscription_status = 'active',
                        stripe_customer_id = COALESCE(?, stripe_customer_id),
                        stripe_subscription_id = COALESCE(?, stripe_subscription_id),
                        stripe_checkout_session_id = COALESCE(?, stripe_checkout_session_id),
                        subscription_end = CASE WHEN subscription_end > ? THEN subscription_end ELSE ? END
                    WHERE username = ? COLLATE NOCASE AND subscription_status != 'comped'
                    """,
                    (cust_id, sub_id, cs_id, time.time(), time.time() + 31 * 86400, username),
                )
                conn.commit()
        elif event_type in ("customer.subscription.updated", "customer.subscription.deleted"):
            sub_id = obj.get("id")
            cust_id = obj.get("customer")
            status = obj.get("status") or ("canceled" if event_type.endswith("deleted") else "none")
            period_end = float(obj.get("current_period_end") or 0)
            username = (obj.get("metadata") or {}).get("username")
            if sub_id:
                conn.execute(
                    """
                    UPDATE auth_users
                    SET subscription_status = ?, subscription_end = ?, stripe_customer_id = COALESCE(?, stripe_customer_id)
                    WHERE (stripe_subscription_id = ? OR (? IS NOT NULL AND username = ? COLLATE NOCASE))
                      AND subscription_status != 'comped'
                    """,
                    (status, period_end, cust_id, sub_id, username, username),
                )
                conn.commit()
        elif event_type == "invoice.payment_failed":
            sub_id = obj.get("subscription")
            if sub_id:
                conn.execute(
                    """
                    UPDATE auth_users
                    SET subscription_status = 'past_due'
                    WHERE stripe_subscription_id = ? AND subscription_status != 'comped'
                    """,
                    (sub_id,),
                )
                conn.commit()
    finally:
        conn.close()

    return jsonify({"received": True})



def render_account_page(error=None, notice=None, status_code=200):
    username = session.get("user")
    conn = get_db()
    user = conn.execute(
        """
        SELECT username, role, created_at, COALESCE(auth_version, 0) AS auth_version,
               COALESCE(subscription_status, 'none') AS subscription_status,
               stripe_customer_id, stripe_subscription_id,
               COALESCE(subscription_end, 0) AS subscription_end
        FROM auth_users WHERE username = ?
        """,
        (username,),
    ).fetchone()
    history_count = conn.execute(
        "SELECT COUNT(*) AS count FROM watch_history WHERE username = ?", (username,)
    ).fetchone()["count"]
    recent = conn.execute(
        """
        SELECT media_type, tmdb_id, title, year, season, episode, updated_at
        FROM watch_history WHERE username = ? ORDER BY updated_at DESC LIMIT 6
        """,
        (username,),
    ).fetchall()
    security_events = conn.execute(
        """
        SELECT event, ip, created_at
        FROM auth_audit_log
        WHERE username = ? COLLATE NOCASE
        ORDER BY created_at DESC LIMIT 6
        """,
        (username,),
    ).fetchall()
    conn.close()
    return (
        render_template(
            "account.html",
            user=user,
            is_subscribed=is_user_subscribed(user),
            history_count=history_count,
            recent=recent,
            security_events=security_events,
            error=error,
            notice=notice,
            is_admin=session.get("role") == "admin",
        ),
        status_code,
    )


@app.route("/account")
@login_required
def account():
    notice = None
    if request.args.get("pw_changed"):
        notice = "Password updated and all other sessions have been signed out."
    elif request.args.get("sessions_revoked"):
        notice = "All other active sessions for your account have been signed out."
    elif request.args.get("history_cleared"):
        notice = "Your watch history has been cleared."
    elif request.args.get("sub_canceled"):
        notice = "Your subscription has been set to cancel at the end of your current billing period."
    elif request.args.get("sub_synced"):
        notice = "Subscription status synced with Stripe."
    return render_account_page(notice=notice)


@app.route("/account/billing-portal", methods=["POST"])
@login_required
def account_billing_portal():
    if not verify_csrf():
        return render_account_page(
            "Security token expired or invalid. Please reload and try again.",
            status_code=400,
        )
    username = session.get("user")
    if not check_sliding_rate_limit(f"billing:{username}:{get_client_ip()}", 8, 900.0):
        return render_account_page(
            "Too many billing requests. Please wait a few minutes and try again.",
            status_code=429,
        )
    user = _get_user_billing_row(username)
    if not user or not user["stripe_customer_id"]:
        return redirect(url_for("subscribe"))
    try:
        portal = stripe_api_request(
            "billing_portal/sessions",
            {
                "customer": user["stripe_customer_id"],
                "return_url": f"{_external_base_url()}/account",
            },
            method="POST",
        )
        portal_url = portal.get("url") or ""
        if portal_url.startswith("https://billing.stripe.com/"):
            return redirect(portal_url, code=303)
    except Exception:
        return render_account_page(
            "Could not open Stripe Billing Portal. You can also cancel your subscription directly below.",
            status_code=400,
        )
    return redirect(url_for("account"))


@app.route("/account/subscription/cancel", methods=["POST"])
@login_required
def account_cancel_subscription():
    if not verify_csrf():
        return render_account_page(
            "Security token expired or invalid. Please reload and try again.",
            status_code=400,
        )
    username = session.get("user")
    if not check_sliding_rate_limit(f"billing:{username}:{get_client_ip()}", 8, 900.0):
        return render_account_page(
            "Too many billing requests. Please wait a few minutes and try again.",
            status_code=429,
        )
    user = _get_user_billing_row(username)
    if not user or not user["stripe_subscription_id"]:
        return render_account_page("No active Stripe subscription found to cancel.", status_code=400)

    try:
        sub = stripe_api_request(
            f"subscriptions/{user['stripe_subscription_id']}",
            {"cancel_at_period_end": "true"},
            method="POST",
        )
        period_end = float(sub.get("current_period_end") or user["subscription_end"] or 0)
        conn = get_db()
        conn.execute(
            "UPDATE auth_users SET subscription_end = ? WHERE username = ?",
            (period_end, username),
        )
        conn.execute(
            "INSERT INTO auth_audit_log (ip, username, event, user_agent, created_at) VALUES (?, ?, ?, ?, ?)",
            (
                get_client_ip(),
                username[:64],
                "subscription_cancel_scheduled",
                (request.headers.get("User-Agent") or "")[:250],
                time.time(),
            ),
        )
        conn.commit()
        conn.close()
        return redirect(url_for("account", sub_canceled=1))
    except Exception:
        return render_account_page("Unable to cancel subscription right now. Please try again shortly.", status_code=502)


@app.route("/account/password", methods=["POST"])
@login_required
def change_password():
    if not verify_csrf():
        return render_account_page(
            "Security token expired or invalid. Please reload and try again.",
            status_code=400,
        )

    username = session.get("user")
    ip = get_client_ip()
    is_locked, retry_after, _ = check_rate_limit(ip, f"reauth:{username}")
    if is_locked:
        mins = max(1, (retry_after + 59) // 60)
        return render_account_page(
            f"Too many failed password attempts. Please wait {mins} minute(s).",
            status_code=429,
        )

    current_password = request.form.get("current_password") or ""
    new_password = request.form.get("new_password") or ""
    confirm_password = request.form.get("confirm_password") or ""

    conn = get_db()
    user = conn.execute(
        "SELECT username, password_hash, role, COALESCE(auth_version, 0) AS auth_version FROM auth_users WHERE username = ?",
        (username,),
    ).fetchone()
    conn.close()

    if not user or not check_password_hash(user["password_hash"], current_password):
        record_login_attempt(ip, f"reauth:{username}", False, event_override="password_change_failed")
        return render_account_page(
            "Current password is incorrect.",
            status_code=400,
        )

    if new_password != confirm_password:
        return render_account_page("New passwords do not match.", status_code=400)

    if current_password == new_password:
        return render_account_page(
            "New password must be different from your current password.",
            status_code=400,
        )

    pw_error = validate_password(new_password, username)
    if pw_error:
        return render_account_page(pw_error, status_code=400)

    new_version = int(user["auth_version"] or 0) + 1
    new_hash = generate_password_hash(new_password, method="scrypt")

    conn = get_db()
    conn.execute(
        "UPDATE auth_users SET password_hash = ?, auth_version = ? WHERE username = ?",
        (new_hash, new_version, username),
    )
    conn.execute(
        "DELETE FROM auth_rate_limits WHERE ip IN (?, ?)",
        (ip, f"user:reauth:{username.lower()}"),
    )
    conn.execute(
        "INSERT INTO auth_audit_log (ip, username, event, user_agent, created_at) VALUES (?, ?, ?, ?, ?)",
        (
            ip,
            username[:64],
            "password_changed",
            (request.headers.get("User-Agent") or "")[:250],
            time.time(),
        ),
    )
    conn.commit()
    conn.close()

    start_user_session(username, user["role"], True, new_version)
    return redirect(url_for("account", pw_changed=1))


@app.route("/account/revoke-sessions", methods=["POST"])
@login_required
def revoke_sessions():
    if not verify_csrf():
        return render_account_page(
            "Security token expired or invalid. Please reload and try again.",
            status_code=400,
        )
    username = session.get("user")
    conn = get_db()
    user = conn.execute(
        "SELECT role, COALESCE(auth_version, 0) AS auth_version FROM auth_users WHERE username = ?",
        (username,),
    ).fetchone()
    if not user:
        conn.close()
        session.clear()
        return redirect(url_for("login"))

    new_version = int(user["auth_version"] or 0) + 1
    conn.execute(
        "UPDATE auth_users SET auth_version = ? WHERE username = ?",
        (new_version, username),
    )
    conn.execute(
        "INSERT INTO auth_audit_log (ip, username, event, user_agent, created_at) VALUES (?, ?, ?, ?, ?)",
        (
            get_client_ip(),
            username[:64],
            "sessions_revoked",
            (request.headers.get("User-Agent") or "")[:250],
            time.time(),
        ),
    )
    conn.commit()
    conn.close()

    start_user_session(username, user["role"], True, new_version)
    return redirect(url_for("account", sessions_revoked=1))


@app.route("/account/history/clear", methods=["POST"])
@login_required
def clear_account_history():
    if not verify_csrf():
        return render_account_page(
            "Security token expired or invalid. Please reload and try again.",
            status_code=400,
        )
    username = session.get("user")
    conn = get_db()
    conn.execute("DELETE FROM watch_history WHERE username = ?", (username,))
    conn.commit()
    conn.close()
    return redirect(url_for("account", history_cleared=1))


@app.route("/account/delete", methods=["POST"])
@login_required
def delete_account():
    if not verify_csrf():
        return render_account_page(
            "Security token expired or invalid. Please reload and try again.",
            status_code=400,
        )

    username = session.get("user")
    ip = get_client_ip()
    is_locked, retry_after, _ = check_rate_limit(ip, f"reauth:{username}")
    if is_locked:
        mins = max(1, (retry_after + 59) // 60)
        return render_account_page(
            f"Too many failed password attempts. Please wait {mins} minute(s).",
            status_code=429,
        )

    password = request.form.get("password") or ""
    conn = get_db()
    user = conn.execute(
        "SELECT username, password_hash, role FROM auth_users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()

    if not user or not check_password_hash(user["password_hash"], password):
        record_login_attempt(ip, f"reauth:{username}", False, event_override="account_delete_failed")
        return render_account_page(
            "Incorrect password. Your account was not deleted.", status_code=400
        )

    if user["role"] == "admin":
        conn = get_db()
        admin_count = conn.execute(
            "SELECT COUNT(*) AS count FROM auth_users WHERE role = 'admin'"
        ).fetchone()["count"]
        conn.close()
        if admin_count <= 1:
            return render_account_page(
                "This is the last admin account. Create or promote another admin before deleting it.",
                status_code=400,
            )

    conn = get_db()
    conn.execute("DELETE FROM watch_history WHERE username = ?", (username,))
    conn.execute("DELETE FROM user_watchlist WHERE username = ?", (username,))
    conn.execute("DELETE FROM user_profiles WHERE username = ?", (username,))
    conn.execute("DELETE FROM auth_users WHERE username = ?", (username,))
    conn.execute(
        "INSERT INTO auth_audit_log (ip, username, event, user_agent, created_at) VALUES (?, ?, ?, ?, ?)",
        (
            ip,
            username[:64],
            "account_deleted",
            (request.headers.get("User-Agent") or "")[:250],
            time.time(),
        ),
    )
    conn.commit()
    conn.close()
    session.clear()
    return redirect(url_for("login", deleted=1))


ADMIN_SUDO_TTL_SECONDS = 900  # 15 minutes


def is_admin_unlocked() -> bool:
    if session.get("role") != "admin":
        return False
    unlocked_at = float(session.get("admin_unlocked_at") or 0)
    return (time.time() - unlocked_at) < ADMIN_SUDO_TTL_SECONDS


def render_admin_users_page(error=None, notice=None, status_code=200):
    if session.get("role") != "admin":
        return "Not Found", 404
    if not is_admin_unlocked():
        return (
            render_template(
                "admin_users.html",
                sudo_required=True,
                error=error,
                notice=notice,
                is_admin=True,
                current_user=session.get("user"),
            ),
            status_code,
        )
    conn = get_db()
    users = conn.execute(
        """
        SELECT u.username, u.role, u.created_at,
               COALESCE(u.subscription_status, 'none') AS subscription_status,
               COALESCE(u.subscription_end, 0) AS subscription_end,
               COUNT(h.username) AS watch_count
        FROM auth_users u
        LEFT JOIN watch_history h ON h.username = u.username
        GROUP BY u.username, u.role, u.created_at, u.subscription_status, u.subscription_end
        ORDER BY CASE u.role WHEN 'admin' THEN 0 ELSE 1 END, u.username COLLATE NOCASE
        """
    ).fetchall()
    audit_logs = conn.execute(
        """
        SELECT ip, username, event, created_at
        FROM auth_audit_log
        ORDER BY created_at DESC LIMIT 12
        """
    ).fetchall()
    conn.close()
    return (
        render_template(
            "admin_users.html",
            sudo_required=False,
            users=users,
            audit_logs=audit_logs,
            error=error,
            notice=notice,
            is_admin=True,
            current_user=session.get("user"),
        ),
        status_code,
    )


@app.route("/admin/unlock", methods=["POST"])
@login_required
def admin_unlock():
    if session.get("role") != "admin":
        return "Not Found", 404
    if not verify_csrf():
        return render_admin_users_page(
            "Security token expired or invalid. Please reload and try again.", status_code=400
        )
    username = session.get("user")
    ip = get_client_ip()
    is_locked, retry_after, _ = check_rate_limit(ip, f"sudo:{username}")
    if is_locked:
        mins = max(1, (retry_after + 59) // 60)
        return render_admin_users_page(
            f"Too many failed admin verification attempts. Please wait {mins} minute(s).",
            status_code=429,
        )

    password = request.form.get("password") or ""
    conn = get_db()
    user = conn.execute(
        "SELECT username, password_hash, role FROM auth_users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()

    if not user or user["role"] != "admin" or not check_password_hash(user["password_hash"], password):
        record_login_attempt(ip, f"sudo:{username}", False, event_override="admin_sudo_failed")
        return render_admin_users_page("Incorrect admin password.", status_code=401)

    record_login_attempt(ip, f"sudo:{username}", True, event_override="admin_sudo_unlocked")
    session["admin_unlocked_at"] = time.time()
    return redirect(url_for("admin_users"))


@app.route("/admin/lock", methods=["POST"])
@login_required
def admin_lock():
    if session.get("role") != "admin":
        return "Not Found", 404
    if verify_csrf():
        session.pop("admin_unlocked_at", None)
    return redirect(url_for("index"))


@app.route("/admin")
@login_required
def admin_users():
    if session.get("role") != "admin":
        return "Not Found", 404
    notice = None
    if request.args.get("created"):
        notice = "Account created."
    elif request.args.get("revoked"):
        notice = "User sessions revoked."
    elif request.args.get("deleted"):
        notice = "Account deleted."
    elif request.args.get("comped"):
        notice = "Account billing access updated."
    return render_admin_users_page(notice=notice)


@app.route("/admin/users")
@login_required
def admin_users_legacy():
    if session.get("role") != "admin":
        return "Not Found", 404
    return redirect(url_for("admin_users"))


@app.route("/admin/create", methods=["POST"])
@app.route("/admin/users/create", methods=["POST"])
@login_required
def admin_create_user():
    if session.get("role") != "admin":
        return "Not Found", 404
    if not is_admin_unlocked():
        return render_admin_users_page("Please confirm your admin password to continue.", status_code=401)
    if not verify_csrf():
        return render_admin_users_page(
            "Security token expired or invalid. Please reload and try again.", status_code=400
        )
    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""
    comp_access = bool(request.form.get("comp_access"))
    sub_status = "comped" if comp_access else "none"
    error = create_auth_user(username, password, "user", subscription_status=sub_status)
    if error:
        return render_admin_users_page(error, status_code=400)
    conn = get_db()
    conn.execute(
        "INSERT INTO auth_audit_log (ip, username, event, user_agent, created_at) VALUES (?, ?, ?, ?, ?)",
        (
            get_client_ip(),
            username[:64],
            "admin_created_comped_account" if comp_access else "admin_created_account",
            (request.headers.get("User-Agent") or "")[:250],
            time.time(),
        ),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("admin_users", created=1))


@app.route("/admin/<path:username>/comp", methods=["POST"])
@login_required
def admin_toggle_comp_user(username):
    if session.get("role") != "admin":
        return "Not Found", 404
    if not is_admin_unlocked():
        return render_admin_users_page("Please confirm your admin password to continue.", status_code=401)
    if not verify_csrf():
        return render_admin_users_page(
            "Security token expired or invalid. Please reload and try again.", status_code=400
        )
    conn = get_db()
    target = conn.execute(
        "SELECT username, role, COALESCE(subscription_status, 'none') AS subscription_status FROM auth_users WHERE username = ?",
        (username,),
    ).fetchone()
    if not target:
        conn.close()
        return render_admin_users_page("That account no longer exists.", status_code=404)
    if target["role"] == "admin":
        conn.close()
        return redirect(url_for("admin_users"))

    new_status = "none" if target["subscription_status"] == "comped" else "comped"
    conn.execute(
        "UPDATE auth_users SET subscription_status = ? WHERE username = ?",
        (new_status, username),
    )
    conn.execute(
        "INSERT INTO auth_audit_log (ip, username, event, user_agent, created_at) VALUES (?, ?, ?, ?, ?)",
        (
            get_client_ip(),
            username[:64],
            f"admin_set_billing_{new_status}",
            (request.headers.get("User-Agent") or "")[:250],
            time.time(),
        ),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("admin_users", comped=1))


@app.route("/admin/<path:username>/revoke", methods=["POST"])
@app.route("/admin/users/<path:username>/revoke", methods=["POST"])
@login_required
def admin_revoke_user_sessions(username):
    if session.get("role") != "admin":
        return "Not Found", 404
    if not is_admin_unlocked():
        return render_admin_users_page("Please confirm your admin password to continue.", status_code=401)
    if not verify_csrf():
        return render_admin_users_page(
            "Security token expired or invalid. Please reload and try again.", status_code=400
        )
    conn = get_db()
    target = conn.execute(
        "SELECT username, role, COALESCE(auth_version, 0) AS auth_version FROM auth_users WHERE username = ?",
        (username,),
    ).fetchone()
    if not target:
        conn.close()
        return render_admin_users_page("That account no longer exists.", status_code=404)

    new_version = int(target["auth_version"] or 0) + 1
    conn.execute(
        "UPDATE auth_users SET auth_version = ? WHERE username = ?",
        (new_version, username),
    )
    conn.execute(
        "INSERT INTO auth_audit_log (ip, username, event, user_agent, created_at) VALUES (?, ?, ?, ?, ?)",
        (
            get_client_ip(),
            username[:64],
            "admin_revoked_sessions",
            (request.headers.get("User-Agent") or "")[:250],
            time.time(),
        ),
    )
    conn.commit()
    conn.close()
    if username == session.get("user"):
        start_user_session(username, target["role"], True, new_version)
        session["admin_unlocked_at"] = time.time()
    return redirect(url_for("admin_users", revoked=1))


@app.route("/admin/<path:username>/delete", methods=["POST"])
@app.route("/admin/users/<path:username>/delete", methods=["POST"])
@login_required
def admin_delete_user(username):
    if session.get("role") != "admin":
        return "Not Found", 404
    if not is_admin_unlocked():
        return render_admin_users_page("Please confirm your admin password to continue.", status_code=401)
    if not verify_csrf():
        return render_admin_users_page(
            "Security token expired or invalid. Please reload and try again.", status_code=400
        )
    if username == session.get("user"):
        return render_admin_users_page(
            "Use Account Settings to delete your own account.", status_code=400
        )
    conn = get_db()
    target = conn.execute(
        "SELECT username FROM auth_users WHERE username = ?", (username,)
    ).fetchone()
    if not target:
        conn.close()
        return render_admin_users_page("That account no longer exists.", status_code=404)
    conn.execute("DELETE FROM watch_history WHERE username = ?", (username,))
    conn.execute("DELETE FROM user_watchlist WHERE username = ?", (username,))
    conn.execute("DELETE FROM user_profiles WHERE username = ?", (username,))
    conn.execute("DELETE FROM auth_users WHERE username = ?", (username,))
    conn.execute(
        "INSERT INTO auth_audit_log (ip, username, event, user_agent, created_at) VALUES (?, ?, ?, ?, ?)",
        (
            get_client_ip(),
            username[:64],
            "admin_deleted_account",
            (request.headers.get("User-Agent") or "")[:250],
            time.time(),
        ),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("admin_users", deleted=1))


SAFE_TMDB_ENDPOINT_RE = re.compile(r"^[A-Za-z0-9_/-]+$")
SAFE_MEDIA_URL_RE = re.compile(
    r"^https://(?:image\.tmdb\.org/t/p/|upload\.wikimedia\.org/)[A-Za-z0-9_./%-]+$"
)


def sanitize_media_url(value) -> str:
    if not value:
        return None
    url = str(value).strip()[:500]
    if SAFE_MEDIA_URL_RE.fullmatch(url):
        return url
    return None


def tmdb_request(endpoint: str, query_params: dict = None) -> dict:
    """Helper to query TMDB API using v3 API key or v4 bearer token."""
    clean_ep = (endpoint or "").lstrip("/")
    if not clean_ep or ".." in clean_ep or not SAFE_TMDB_ENDPOINT_RE.fullmatch(clean_ep):
        raise ValueError("Invalid TMDB endpoint")
    base_url = f"https://api.themoviedb.org/3/{clean_ep}"
    params = query_params.copy() if query_params else {}
    if TMDB_API_KEY:
        params["api_key"] = TMDB_API_KEY

    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    headers = {"User-Agent": "TMDBExplorer/2.0"}
    if TMDB_READ_TOKEN:
        headers["Authorization"] = f"Bearer {TMDB_READ_TOKEN}"

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=4) as resp:
        if resp.status == 200:
            return json.loads(resp.read().decode())
    return {}


PROFILE_COLOR_PALETTE = [
    "#e50914",
    "#2563eb",
    "#10b981",
    "#f59e0b",
    "#8b5cf6",
    "#ec4899",
    "#06b6d4",
]


def _serialize_profile(row):
    return {
        "id": int(row["id"]),
        "name": row["name"],
        "avatar_color": row["avatar_color"] or "#e50914",
        "is_kids": bool(row["is_kids"]),
    }


def _ensure_user_profiles(username):
    conn = get_db()
    rows = conn.execute(
        "SELECT id, username, name, avatar_color, is_kids, created_at FROM user_profiles WHERE username = ? ORDER BY id ASC",
        (username,),
    ).fetchall()
    if not rows:
        now = time.time()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO user_profiles (username, name, avatar_color, is_kids, created_at) VALUES (?, ?, ?, 0, ?)",
            (username, username[:24], "#e50914", now),
        )
        default_id = cur.lastrowid
        # Migrate any legacy profile_id=0 rows to this default profile
        cur.execute(
            "UPDATE OR IGNORE watch_history SET profile_id = ? WHERE username = ? AND profile_id = 0",
            (default_id, username),
        )
        cur.execute(
            "UPDATE OR IGNORE user_watchlist SET profile_id = ? WHERE username = ? AND profile_id = 0",
            (default_id, username),
        )
        conn.commit()
        rows = conn.execute(
            "SELECT id, username, name, avatar_color, is_kids, created_at FROM user_profiles WHERE username = ? ORDER BY id ASC",
            (username,),
        ).fetchall()
    conn.close()
    return [_serialize_profile(r) for r in rows]


def _get_active_profile(username):
    profiles = _ensure_user_profiles(username)
    active_id = session.get("profile_id")
    for p in profiles:
        if p["id"] == active_id:
            session["is_kids"] = p["is_kids"]
            return p, profiles
    first = profiles[0]
    session["profile_id"] = first["id"]
    session["is_kids"] = first["is_kids"]
    return first, profiles


def _get_landing_posters():
    try:
        conn = get_db()
        rows = conn.execute(
            """
            SELECT m.id, m.title, p.poster_path, p.backdrop_path, COALESCE(p.vote_average, 7.5) AS vote_average
            FROM movies m
            JOIN movie_posters p ON m.id = p.id
            WHERE p.poster_path IS NOT NULL AND p.poster_path != ''
            ORDER BY m.popularity DESC
            LIMIT 16
            """
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


def render_landing():
    posters = _get_landing_posters()
    return render_template(
        "landing.html",
        site_name=SITE_NAME,
        site_name_upper=SITE_NAME.upper(),
        site_tagline=SITE_TAGLINE,
        subscription_price=format_price_display(),
        featured_posters=posters,
    )


@app.route("/")
def index():
    if not is_authenticated_user():
        if session.get("authenticated") or session.get("user"):
            session.clear()
        return render_landing()
    return show_catalog()


@app.route("/browse")
@login_required
def browse():
    return show_catalog()


@app.route("/landing")
@app.route("/welcome")
def landing():
    if not is_authenticated_user():
        if session.get("authenticated") or session.get("user"):
            session.clear()
    return render_landing()


@login_required
def show_catalog():
    username = session.get("user", "admin")
    initial_home = build_home_payload(username)
    initial_hero = initial_home["hero"][0] if initial_home.get("hero") else None
    return render_template(
        "index.html",
        current_user=username,
        is_admin=session.get("role") == "admin",
        active_profile=initial_home["active_profile"],
        profiles=initial_home["profiles"],
        initial_home=initial_home,
        initial_hero=initial_hero,
    )


@app.route("/api/profiles", methods=["GET", "POST"])
@login_required
def api_profiles():
    username = session.get("user")
    if request.method == "GET":
        active_profile, profiles = _get_active_profile(username)
        return jsonify({"active_profile": active_profile, "profiles": profiles})

    if not verify_csrf():
        return jsonify({"error": "Invalid CSRF token"}), 400

    payload = request.get_json(silent=True) or {}
    name = re.sub(r"[\x00-\x1f\x7f]", "", str(payload.get("name") or "").strip())[:24]
    if not name:
        return jsonify({"error": "Profile name is required"}), 400

    avatar_color = str(payload.get("avatar_color") or "#2563eb").strip()
    if avatar_color not in PROFILE_COLOR_PALETTE:
        avatar_color = "#2563eb"
    is_kids = 1 if bool(payload.get("is_kids")) else 0

    profiles = _ensure_user_profiles(username)
    if len(profiles) >= 4:
        return jsonify({"error": "Maximum of 4 household profiles per account"}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO user_profiles (username, name, avatar_color, is_kids, created_at) VALUES (?, ?, ?, ?, ?)",
        (username, name, avatar_color, is_kids, time.time()),
    )
    new_id = cur.lastrowid
    conn.commit()
    conn.close()

    session["profile_id"] = int(new_id)
    session["is_kids"] = bool(is_kids)
    session["profile_selected"] = True
    active_profile, profiles = _get_active_profile(username)
    return jsonify({"ok": True, "active_profile": active_profile, "profiles": profiles, "needs_profile_selection": False})


@app.route("/api/profiles/select", methods=["POST"])
@login_required
def api_select_profile():
    if not verify_csrf():
        return jsonify({"error": "Invalid CSRF token"}), 400
    username = session.get("user")
    payload = request.get_json(silent=True) or {}
    try:
        profile_id = int(payload.get("profile_id") or 0)
    except (TypeError, ValueError):
        profile_id = 0

    profiles = _ensure_user_profiles(username)
    chosen = next((p for p in profiles if p["id"] == profile_id), None)
    if not chosen:
        return jsonify({"error": "Profile not found"}), 404

    session["profile_id"] = chosen["id"]
    session["is_kids"] = chosen["is_kids"]
    session["profile_selected"] = True
    return jsonify({"ok": True, "active_profile": chosen, "profiles": profiles, "needs_profile_selection": False})


@app.route("/api/profiles/<int:profile_id>", methods=["PUT", "DELETE"])
@login_required
def api_modify_profile(profile_id):
    if not verify_csrf():
        return jsonify({"error": "Invalid CSRF token"}), 400
    username = session.get("user")
    profiles = _ensure_user_profiles(username)
    target = next((p for p in profiles if p["id"] == profile_id), None)
    if not target:
        return jsonify({"error": "Profile not found"}), 404

    if request.method == "PUT":
        payload = request.get_json(silent=True) or {}
        name = re.sub(r"[\x00-\x1f\x7f]", "", str(payload.get("name") or target["name"]).strip())[:24]
        if not name:
            return jsonify({"error": "Profile name is required"}), 400
        avatar_color = str(payload.get("avatar_color") or target["avatar_color"] or "#e50914").strip()
        if avatar_color not in PROFILE_COLOR_PALETTE:
            avatar_color = target["avatar_color"] or "#e50914"
        is_kids = 1 if bool(payload.get("is_kids", target["is_kids"])) else 0

        conn = get_db()
        conn.execute(
            "UPDATE user_profiles SET name = ?, avatar_color = ?, is_kids = ? WHERE username = ? AND id = ?",
            (name, avatar_color, is_kids, username, profile_id),
        )
        conn.commit()
        conn.close()

        if session.get("profile_id") == profile_id:
            session["is_kids"] = bool(is_kids)
        active_profile, updated_profiles = _get_active_profile(username)
        return jsonify({"ok": True, "active_profile": active_profile, "profiles": updated_profiles})

    if len(profiles) <= 1:
        return jsonify({"error": "Cannot delete your primary household profile"}), 400

    conn = get_db()
    conn.execute("DELETE FROM watch_history WHERE username = ? AND profile_id = ?", (username, profile_id))
    conn.execute("DELETE FROM user_watchlist WHERE username = ? AND profile_id = ?", (username, profile_id))
    conn.execute("DELETE FROM user_profiles WHERE username = ? AND id = ?", (username, profile_id))
    conn.commit()
    conn.close()

    if session.get("profile_id") == profile_id:
        session.pop("profile_id", None)
    active_profile, remaining = _get_active_profile(username)
    return jsonify({"ok": True, "active_profile": active_profile, "profiles": remaining})


def normalize_watchlist_row(row):
    return {
        "id": row["tmdb_id"],
        "tmdb_id": row["tmdb_id"],
        "media_type": row["media_type"],
        "title": row["title"],
        "poster_url": sanitize_media_url(row["poster_url"]),
        "poster_path": None,
        "backdrop_url": sanitize_media_url(row["backdrop_url"]),
        "backdrop_path": None,
        "year": row["year"] or "",
        "release_date": "",
        "vote_average": row["vote_average"],
        "overview": row["overview"] or "",
        "in_watchlist": True,
        "created_at": row["created_at"],
    }


@app.route("/api/watchlist", methods=["GET", "POST"])
@login_required
def api_watchlist():
    username = session.get("user")
    active_profile, _ = _get_active_profile(username)
    profile_id = active_profile["id"]

    if request.method == "GET":
        conn = get_db()
        rows = conn.execute(
            """
            SELECT * FROM user_watchlist
            WHERE username = ? AND profile_id IN (?, 0)
            ORDER BY created_at DESC LIMIT 100
            """,
            (username, profile_id),
        ).fetchall()
        conn.close()
        return jsonify({"items": [normalize_watchlist_row(r) for r in rows]})

    if not verify_csrf():
        return jsonify({"error": "Invalid CSRF token"}), 400

    payload = request.get_json(silent=True) or {}
    media_type = str(payload.get("media_type") or "").lower()
    if media_type not in ("movie", "tv"):
        return jsonify({"error": "media_type must be movie or tv"}), 400

    try:
        tmdb_id = int(payload.get("id") or payload.get("tmdb_id") or 0)
    except (TypeError, ValueError):
        tmdb_id = 0
    if tmdb_id <= 0 or tmdb_id > 50_000_000:
        return jsonify({"error": "A valid TMDB id is required"}), 400

    title = str(payload.get("title") or "").strip()[:300]
    if not title:
        return jsonify({"error": "title is required"}), 400

    try:
        vote_average = float(payload.get("vote_average") or 0)
    except (TypeError, ValueError):
        vote_average = 0
    vote_average = max(0, min(10, vote_average))

    poster_url = sanitize_media_url(payload.get("poster_url"))
    backdrop_url = sanitize_media_url(payload.get("backdrop_url"))
    year = re.sub(r"[^0-9-]", "", str(payload.get("year") or ""))[:12]
    overview = str(payload.get("overview") or "")[:2000]

    conn = get_db()
    conn.execute(
        """
        INSERT OR REPLACE INTO user_watchlist (
            username, profile_id, media_type, tmdb_id, title, poster_url,
            backdrop_url, year, vote_average, overview, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            username,
            profile_id,
            media_type,
            tmdb_id,
            title,
            poster_url,
            backdrop_url,
            year,
            vote_average,
            overview,
            time.time(),
        ),
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True, "in_watchlist": True})


@app.route("/api/watchlist/<media_type>/<int:tmdb_id>", methods=["DELETE"])
@login_required
def api_delete_watchlist(media_type, tmdb_id):
    if not verify_csrf():
        return jsonify({"error": "Invalid CSRF token"}), 400
    if media_type not in ("movie", "tv"):
        return jsonify({"error": "media_type must be movie or tv"}), 400
    username = session.get("user")
    active_profile, _ = _get_active_profile(username)
    conn = get_db()
    conn.execute(
        "DELETE FROM user_watchlist WHERE username = ? AND profile_id IN (?, 0) AND media_type = ? AND tmdb_id = ?",
        (username, active_profile["id"], media_type, tmdb_id),
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True, "in_watchlist": False})


def normalize_history_row(row):
    return {
        "id": row["tmdb_id"],
        "tmdb_id": row["tmdb_id"],
        "media_type": row["media_type"],
        "title": row["title"],
        "poster_url": sanitize_media_url(row["poster_url"]),
        "poster_path": None,
        "backdrop_url": sanitize_media_url(row["backdrop_url"]),
        "backdrop_path": None,
        "year": row["year"] or "",
        "release_date": "",
        "vote_average": row["vote_average"],
        "overview": row["overview"] or "",
        "season": row["season"] or 1,
        "episode": row["episode"] or 1,
        "episode_name": row["episode_name"] or "",
        "progress_seconds": row["progress_seconds"] or 0,
        "duration_seconds": row["duration_seconds"] or 0,
        "updated_at": row["updated_at"],
    }


@app.route("/api/history", methods=["GET", "POST"])
@login_required
def api_history():
    username = session.get("user")
    active_profile, _ = _get_active_profile(username)
    profile_id = active_profile["id"]

    if request.method == "GET":
        try:
            limit = max(1, min(50, int(request.args.get("limit", 20))))
        except (TypeError, ValueError):
            limit = 20
        conn = get_db()
        rows = conn.execute(
            """
            SELECT * FROM watch_history
            WHERE username = ? AND profile_id IN (?, 0)
              AND NOT (duration_seconds > 0 AND progress_seconds >= duration_seconds * 0.95)
            ORDER BY updated_at DESC LIMIT ?
            """,
            (username, profile_id, limit),
        ).fetchall()
        conn.close()
        return jsonify({"items": [normalize_history_row(row) for row in rows]})

    if not verify_csrf():
        return jsonify({"error": "Invalid CSRF token"}), 400

    payload = request.get_json(silent=True) or {}
    media_type = str(payload.get("media_type") or "").lower()
    if media_type not in ("movie", "tv"):
        return jsonify({"error": "media_type must be movie or tv"}), 400

    try:
        tmdb_id = int(payload.get("id") or payload.get("tmdb_id") or 0)
    except (TypeError, ValueError):
        tmdb_id = 0
    if tmdb_id <= 0:
        return jsonify({"error": "A valid TMDB id is required"}), 400

    title = str(payload.get("title") or "").strip()[:300]
    if not title:
        return jsonify({"error": "title is required"}), 400

    try:
        season = max(1, min(10000, int(payload.get("season") or 1)))
        episode = max(1, min(10000, int(payload.get("episode") or 1)))
    except (TypeError, ValueError):
        season, episode = 1, 1

    try:
        vote_average = float(payload.get("vote_average") or 0)
    except (TypeError, ValueError):
        vote_average = 0
    vote_average = max(0, min(10, vote_average))

    try:
        progress_seconds = max(0, float(payload.get("progress_seconds") or 0))
        duration_seconds = max(0, float(payload.get("duration_seconds") or 0))
    except (TypeError, ValueError):
        progress_seconds, duration_seconds = 0, 0
    if duration_seconds and progress_seconds > duration_seconds:
        progress_seconds = duration_seconds

    is_ended = bool(payload.get("is_ended"))
    # When watching TV series, advance to next episode if current episode ended or completed (>=90%)
    if media_type == "tv" and (is_ended or (duration_seconds > 0 and progress_seconds >= duration_seconds * 0.90)):
        if payload.get("next_season") and payload.get("next_episode"):
            season = max(1, int(payload.get("next_season")))
            episode = max(1, int(payload.get("next_episode")))
            episode_name = str(payload.get("next_episode_name") or f"Episode {episode}")[:200]
            progress_seconds = 0
            duration_seconds = 0
        elif payload.get("is_series_end"):
            # Whole series completed, drop off continue watching
            progress_seconds = max(100.0, duration_seconds or 100.0)
            duration_seconds = progress_seconds
        elif not payload.get("next_episode"):
            # Auto-advance to next episode in season
            episode += 1
            episode_name = f"Episode {episode}"
            progress_seconds = 0
            duration_seconds = 0

    poster_url = sanitize_media_url(payload.get("poster_url"))
    backdrop_url = sanitize_media_url(payload.get("backdrop_url"))
    year = re.sub(r"[^0-9-]", "", str(payload.get("year") or ""))[:12]
    overview = str(payload.get("overview") or "")[:2000]
    episode_name = str(payload.get("episode_name") or "")[:200]

    conn = get_db()
    conn.execute(
        """
        INSERT OR REPLACE INTO watch_history (
            username, profile_id, media_type, tmdb_id, title, poster_url, backdrop_url, year,
            vote_average, overview, season, episode, episode_name,
            progress_seconds, duration_seconds, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            username,
            profile_id,
            media_type,
            tmdb_id,
            title,
            poster_url,
            backdrop_url,
            year,
            vote_average,
            overview,
            season,
            episode,
            episode_name,
            progress_seconds,
            duration_seconds,
            time.time(),
        ),
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/api/history/<media_type>/<int:tmdb_id>", methods=["DELETE"])
@login_required
def api_delete_history(media_type, tmdb_id):
    if not verify_csrf():
        return jsonify({"error": "Invalid CSRF token"}), 400
    if media_type not in ("movie", "tv"):
        return jsonify({"error": "media_type must be movie or tv"}), 400
    username = session.get("user")
    active_profile, _ = _get_active_profile(username)
    conn = get_db()
    conn.execute(
        "DELETE FROM watch_history WHERE username = ? AND profile_id IN (?, 0) AND media_type = ? AND tmdb_id = ?",
        (username, active_profile["id"], media_type, tmdb_id),
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/api/movies")
@login_required
def search_movies():
    query = request.args.get("q", "").strip()[:200]
    media_type = request.args.get("type", "all").strip().lower()
    sort_by = request.args.get("sort", "popular").strip().lower()
    try:
        page = max(1, min(1000, int(request.args.get("page", 1))))
    except (TypeError, ValueError):
        page = 1
    try:
        limit = min(60, max(1, int(request.args.get("limit", 24))))
    except (TypeError, ValueError):
        limit = 24
    offset = (page - 1) * limit

    if media_type == "tv":
        tv_results = (
            search_tv_series(query or "Breaking Bad", limit=limit)
            if not query
            else search_tv_series(query, limit=limit)
        )
        if not query and len(tv_results) < 8:
            tv_results = get_popular_tv_defaults()
        return jsonify(
            {
                "results": tv_results,
                "total": len(tv_results),
                "page": 1,
                "limit": limit,
            }
        )

    conn = get_db()
    cur = conn.cursor()

    # Direct numeric search (by TMDB ID)
    if query.isdigit():
        movie_id = int(query)
        cur.execute(
            """
            SELECT m.id, m.title, m.popularity, m.adult, p.poster_path, p.backdrop_path, p.release_date, p.vote_average
            FROM movies m
            LEFT JOIN movie_posters p ON m.id = p.id
            WHERE m.id = ? AND m.adult = 0
        """,
            (movie_id,),
        )
        direct_match = cur.fetchall()
        if direct_match:
            cur.execute(
                """
                SELECT m.id, m.title, m.popularity, m.adult, p.poster_path, p.backdrop_path, p.release_date, p.vote_average
                FROM movies m
                LEFT JOIN movie_posters p ON m.id = p.id
                WHERE m.title LIKE ? AND m.id != ? AND m.adult = 0
                ORDER BY m.popularity DESC
                LIMIT ?
            """,
                (f"%{query}%", movie_id, limit - 1),
            )
            other_matches = cur.fetchall()
            results = format_movie_rows(direct_match + other_matches)
            conn.close()
            return jsonify(
                {
                    "results": results,
                    "total": len(results),
                    "page": 1,
                    "limit": limit,
                }
            )

    if not query:
        cur.execute("SELECT COUNT(*) as cnt FROM movies WHERE adult = 0;")
        total = cur.fetchone()["cnt"]

        order_clause = (
            "COALESCE(p.vote_average, 0) DESC, m.popularity DESC"
            if sort_by == "rating"
            else "m.popularity DESC"
        )
        cur.execute(
            f"""
            SELECT m.id, m.title, m.popularity, m.adult, p.poster_path, p.backdrop_path, p.release_date, p.vote_average
            FROM movies m
            LEFT JOIN movie_posters p ON m.id = p.id
            WHERE m.adult = 0
            ORDER BY {order_clause}
            LIMIT ? OFFSET ?
        """,
            (limit, offset),
        )
        rows = cur.fetchall()
        conn.close()
        movie_results = format_movie_rows(rows)
        if media_type == "all" and page == 1:
            tv_defaults = get_popular_tv_defaults()[:8]
            return jsonify(
                {
                    "results": movie_results[:limit],
                    "tv_row": tv_defaults,
                    "total": total,
                    "page": page,
                    "limit": limit,
                }
            )
        return jsonify(
            {
                "results": movie_results,
                "total": total,
                "page": page,
                "limit": limit,
            }
        )

    # Search with title/keywords using FTS5
    sanitized = re.sub(r"[^\w\s]", "", query).strip()
    rows = []
    total = 0

    if sanitized:
        fts_query = f'"{sanitized}"*'
        try:
            cur.execute(
                """
                SELECT COUNT(*) as cnt
                FROM movies_fts f
                JOIN movies m ON m.id = f.rowid
                WHERE movies_fts MATCH ? AND m.adult = 0
                """,
                (fts_query,),
            )
            total = cur.fetchone()["cnt"]

            cur.execute(
                """
                SELECT m.id, m.title, m.popularity, m.adult, p.poster_path, p.backdrop_path, p.release_date, p.vote_average
                FROM movies_fts f
                JOIN movies m ON m.id = f.rowid
                LEFT JOIN movie_posters p ON m.id = p.id
                WHERE movies_fts MATCH ? AND m.adult = 0
                ORDER BY m.popularity DESC
                LIMIT ? OFFSET ?
            """,
                (fts_query, limit, offset),
            )
            rows = cur.fetchall()
        except sqlite3.OperationalError:
            cur.execute(
                "SELECT COUNT(*) as cnt FROM movies WHERE title LIKE ? AND adult = 0",
                (f"%{query}%",),
            )
            total = cur.fetchone()["cnt"]

            cur.execute(
                """
                SELECT m.id, m.title, m.popularity, m.adult, p.poster_path, p.backdrop_path, p.release_date, p.vote_average
                FROM movies m
                LEFT JOIN movie_posters p ON m.id = p.id
                WHERE m.title LIKE ? AND m.adult = 0
                ORDER BY m.popularity DESC
                LIMIT ? OFFSET ?
            """,
                (f"%{query}%", limit, offset),
            )
            rows = cur.fetchall()

    conn.close()
    movie_results = format_movie_rows(rows)

    if media_type == "all" and query:
        tv_results = search_tv_series(query, limit=8)
        combined = tv_results + movie_results
        return jsonify(
            {
                "results": combined[:limit],
                "total": total + len(tv_results),
                "page": page,
                "limit": limit,
            }
        )

    return jsonify(
        {
            "results": movie_results,
            "total": total,
            "page": page,
            "limit": limit,
        }
    )


def format_poster_url(poster_path: str, size: str = "w342"):
    if not poster_path:
        return None
    if poster_path.startswith("http://") or poster_path.startswith("https://"):
        return poster_path
    return f"https://image.tmdb.org/t/p/{size}{poster_path}"


def format_movie_rows(rows):
    items = []
    for r in rows:
        d = dict(r)
        poster_path = d.get("poster_path")
        d["media_type"] = "movie"
        d["poster_url"] = format_poster_url(poster_path, "w342")
        d["backdrop_url"] = format_poster_url(d.get("backdrop_path"), "w1280")
        d["year"] = d["release_date"][:4] if d.get("release_date") else None
        items.append(d)
    return items


def get_popular_tv_defaults():
    """Curated popular TV series with official TMDB TV IDs for instant browsing."""
    return [
        {
            "id": 1396,
            "title": "Breaking Bad",
            "media_type": "tv",
            "year": "2008",
            "release_date": "2008-01-20",
            "vote_average": 8.9,
            "poster_url": "https://image.tmdb.org/t/p/w342/ztkUQFLlC19CCMYHW9o1zWhJRNq.jpg",
            "backdrop_url": "https://image.tmdb.org/t/p/w1280/tsRy63Mu5cu8etL1X7ZLyf7UP1M.jpg",
            "overview": "A chemistry teacher diagnosed with inoperable lung cancer turns to manufacturing and selling methamphetamine with a former student in order to secure his family's future.",
        },
        {
            "id": 1399,
            "title": "Game of Thrones",
            "media_type": "tv",
            "year": "2011",
            "release_date": "2011-04-17",
            "vote_average": 8.4,
            "poster_url": "https://image.tmdb.org/t/p/w342/1XS1oqL89opfnbLl8WnZY1O1uJx.jpg",
            "backdrop_url": "https://image.tmdb.org/t/p/w1280/2OMB0ynKlyIenMJWI2Dy9IWT4c.jpg",
            "overview": "Seven noble families fight for control of the mythical land of Westeros. Friction between the houses leads to full-scale war.",
        },
        {
            "id": 66732,
            "title": "Stranger Things",
            "media_type": "tv",
            "year": "2016",
            "release_date": "2016-07-15",
            "vote_average": 8.6,
            "poster_url": "https://image.tmdb.org/t/p/w342/uOOtwVbSr4QDjAGIifLDwpb2Pdl.jpg",
            "backdrop_url": "https://image.tmdb.org/t/p/w1280/56v2KjBlU4XaOv9rVYEQypROD7P.jpg",
            "overview": "When a young boy vanishes, a small town uncovers a mystery involving secret experiments, terrifying supernatural forces, and one strange little girl.",
        },
        {
            "id": 94997,
            "title": "House of the Dragon",
            "media_type": "tv",
            "year": "2022",
            "release_date": "2022-08-21",
            "vote_average": 8.4,
            "poster_url": "https://image.tmdb.org/t/p/w342/z2yahl2uefxDCl0nogcRBstwruJ.jpg",
            "overview": "The Targaryen dynasty is at the absolute apex of its power, with more than 15 dragons under their yoke.",
        },
        {
            "id": 100088,
            "title": "The Last of Us",
            "media_type": "tv",
            "year": "2023",
            "release_date": "2023-01-15",
            "vote_average": 8.6,
            "poster_url": "https://image.tmdb.org/t/p/w342/uKvVjHNqB5VmOrdxqAt2F7J78ED.jpg",
            "overview": "Twenty years after modern civilization has been destroyed, Joel, a hardened survivor, is hired to smuggle Ellie, a 14-year-old girl, out of an oppressive quarantine zone.",
        },
        {
            "id": 84958,
            "title": "Loki",
            "media_type": "tv",
            "year": "2021",
            "release_date": "2021-06-09",
            "vote_average": 8.2,
            "poster_url": "https://image.tmdb.org/t/p/w342/voHUmluYmKyleFkTu3lOXQG702u.jpg",
            "overview": "After stealing the Tesseract during the events of Avengers: Endgame, an alternate version of Loki is brought to the mysterious Time Variance Authority.",
        },
        {
            "id": 93405,
            "title": "Squid Game",
            "media_type": "tv",
            "year": "2021",
            "release_date": "2021-09-17",
            "vote_average": 7.8,
            "poster_url": "https://image.tmdb.org/t/p/w342/dDlEmu3EZ0Pgg93K2SVNLCjCSvE.jpg",
            "overview": "Hundreds of cash-strapped players accept a strange invitation to compete in children's games. Inside, a tempting prize awaits — with deadly high stakes.",
        },
        {
            "id": 60625,
            "title": "Rick and Morty",
            "media_type": "tv",
            "year": "2013",
            "release_date": "2013-12-02",
            "vote_average": 8.7,
            "poster_url": "https://image.tmdb.org/t/p/w342/gdIrmf2DdY5mgN6ycVP0XlzKzbE.jpg",
            "overview": "Rick is a mentally-unbalanced but scientifically gifted old man who has recently reconnected with his family. He spends most of his time involving his young grandson Morty in dangerous, outlandish adventures.",
        },
        {
            "id": 136315,
            "title": "The Bear",
            "media_type": "tv",
            "year": "2022",
            "release_date": "2022-06-23",
            "vote_average": 8.6,
            "poster_url": "https://image.tmdb.org/t/p/w342/sHFlbKS3WLqMnp9t2ghADIJFnuQ.jpg",
            "overview": "Carmy, a young fine-dining chef, comes home to Chicago to run his family sandwich shop. As he fights to transform the shop and himself, he works alongside a rough-around-the-edges crew.",
        },
        {
            "id": 95396,
            "title": "Severance",
            "media_type": "tv",
            "year": "2022",
            "release_date": "2022-02-17",
            "vote_average": 8.4,
            "poster_url": "https://image.tmdb.org/t/p/w342/lFf6LLrQjYldcZItzOkGmMMigP7.jpg",
            "overview": "Mark leads a team of office workers whose memories have been surgically divided between their work and personal lives.",
        },
        {
            "id": 76479,
            "title": "The Boys",
            "media_type": "tv",
            "year": "2019",
            "release_date": "2019-07-25",
            "vote_average": 8.5,
            "poster_url": "https://image.tmdb.org/t/p/w342/2zmTngn1tYC1AvfnrFLhxeD82hz.jpg",
            "overview": "A group of vigilantes known informally as 'The Boys' set out to take down corrupt superheroes with no more than blue-collar grit and a willingness to fight dirty.",
        },
        {
            "id": 94605,
            "title": "Arcane",
            "media_type": "tv",
            "year": "2021",
            "release_date": "2021-11-06",
            "vote_average": 8.8,
            "poster_url": "https://image.tmdb.org/t/p/w342/fqldf2t8ztc9aiwn3k6mlX3tvRT.jpg",
            "overview": "Amid the stark discord of twin cities Piltover and Zaun, two sisters fight on rival sides of a war between magic technologies and clashing convictions.",
        },
    ]


def search_tv_series(query: str, limit: int = 12):
    """Searches TV series via TMDB API with a Wikidata/Wikipedia fallback for TMDB TV IDs."""
    if not query:
        return []

    results = []
    # 1. Try official TMDB search/tv
    try:
        data = tmdb_request("search/tv", {"query": query, "include_adult": "false"})
        if data and data.get("results"):
            for item in data["results"][:limit]:
                first_air = item.get("first_air_date") or ""
                poster_path = item.get("poster_path")
                backdrop_path = item.get("backdrop_path")
                results.append(
                    {
                        "id": item["id"],
                        "title": item.get("name") or item.get("original_name") or "Untitled",
                        "media_type": "tv",
                        "poster_path": poster_path,
                        "poster_url": format_poster_url(poster_path, "w342"),
                        "backdrop_url": format_poster_url(backdrop_path, "w1280"),
                        "release_date": first_air,
                        "year": first_air[:4] if first_air else None,
                        "vote_average": item.get("vote_average"),
                        "overview": item.get("overview", ""),
                        "popularity": item.get("popularity", 0.0),
                    }
                )
            if results:
                return results
    except Exception:
        pass

    # 2. Fallback: Query Wikidata for TV series matching query with P4983 (TMDB TV series ID)
    try:
        headers = {"User-Agent": "MovieBrowserApp/1.0 (contact@local)"}
        wd_search_url = "https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(
            {
                "action": "wbsearchentities",
                "search": query,
                "language": "en",
                "limit": 10,
                "format": "json",
            }
        )
        req = urllib.request.Request(wd_search_url, headers=headers)
        with urllib.request.urlopen(req, timeout=4) as resp:
            search_data = json.loads(resp.read().decode())

        entity_ids = [item["id"] for item in search_data.get("search", []) if "id" in item]
        if entity_ids:
            wd_entities_url = "https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(
                {
                    "action": "wbgetentities",
                    "ids": "|".join(entity_ids),
                    "props": "claims|labels|descriptions|sitelinks",
                    "languages": "en",
                    "format": "json",
                }
            )
            req2 = urllib.request.Request(wd_entities_url, headers=headers)
            with urllib.request.urlopen(req2, timeout=4) as resp2:
                entities_data = json.loads(resp2.read().decode()).get("entities", {})

            for eid in entity_ids:
                ent = entities_data.get(eid, {})
                claims = ent.get("claims", {})
                tmdb_tv_claims = claims.get("P4983", [])
                if not tmdb_tv_claims:
                    continue
                try:
                    tmdb_tv_id = int(tmdb_tv_claims[0]["mainsnak"]["datavalue"]["value"])
                except (KeyError, ValueError, TypeError):
                    continue

                label = ent.get("labels", {}).get("en", {}).get("value") or query
                desc = ent.get("descriptions", {}).get("en", {}).get("value", "")
                enwiki_title = ent.get("sitelinks", {}).get("enwiki", {}).get("title")

                thumb, r_date, extract = fetch_wiki_poster_and_info(
                    enwiki_title or label, is_tv=True
                )
                results.append(
                    {
                        "id": tmdb_tv_id,
                        "title": label,
                        "media_type": "tv",
                        "poster_path": thumb,
                        "poster_url": thumb,
                        "release_date": r_date,
                        "year": r_date[:4] if r_date else None,
                        "overview": extract or desc,
                        "popularity": 50.0,
                    }
                )
                if len(results) >= limit:
                    break
    except Exception:
        pass

    return results


def fetch_wiki_poster_and_info(title: str, is_tv: bool = False):
    """Fallback to Wikipedia REST API for poster thumbnail and overview."""
    headers = {"User-Agent": "MovieBrowserApp/1.0 (contact@local)"}
    candidates = [f"{title} (TV series)", title] if is_tv else [f"{title} (film)", title]
    for candidate in candidates:
        try:
            candidate_encoded = urllib.parse.quote(candidate)
            wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{candidate_encoded}"
            req = urllib.request.Request(wiki_url, headers=headers)
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status == 200:
                    wdata = json.loads(resp.read().decode())
                    extract = wdata.get("extract", "")
                    if (
                        extract
                        and "may refer to" not in extract.lower()
                        and "disambiguation" not in extract.lower()
                    ):
                        thumb = wdata.get("thumbnail", {}).get("source")
                        year_match = re.search(r"\b(19\d\d|20\d\d)\b", extract[:300])
                        r_date = year_match.group(1) if year_match else None
                        return thumb, r_date, extract
        except Exception:
            continue
    return None, None, None


@app.route("/api/posters", methods=["POST", "GET"])
@login_required
def fetch_batch_posters():
    """Fetches posters for a list of movie IDs if not yet cached."""
    if request.method == "POST":
        if not verify_csrf():
            return jsonify({"error": "Invalid CSRF token"}), 403
        data = request.get_json(silent=True) or {}
        ids = data.get("ids", [])
    else:
        ids_str = request.args.get("ids", "")
        ids = [int(x) for x in ids_str.split(",") if x.strip().isdigit()]

    if not ids:
        return jsonify({})

    ids = [int(x) for x in ids[:30] if str(x).isdigit()]
    if not ids:
        return jsonify({})

    conn = get_db()
    cur = conn.cursor()

    placeholders = ",".join("?" for _ in ids)
    cur.execute(
        f"SELECT id, poster_path, backdrop_path, release_date, vote_average FROM movie_posters WHERE id IN ({placeholders})",
        ids,
    )
    cached_map = {row["id"]: dict(row) for row in cur.fetchall()}

    missing_ids = [
        mid for mid in ids if mid not in cached_map or not cached_map[mid].get("poster_path")
    ]

    if missing_ids:
        m_placeholders = ",".join("?" for _ in missing_ids)
        cur.execute(
            f"SELECT id, title FROM movies WHERE id IN ({m_placeholders})",
            missing_ids,
        )
        titles_map = {row["id"]: row["title"] for row in cur.fetchall()}

        def fetch_single(mid):
            try:
                data = tmdb_request(f"movie/{mid}")
                if data and data.get("poster_path"):
                    poster = data.get("poster_path")
                    backdrop = data.get("backdrop_path")
                    r_date = data.get("release_date")
                    vote = data.get("vote_average")
                    return mid, poster, backdrop, r_date, vote
            except Exception:
                pass
            title = titles_map.get(mid)
            if title:
                thumb, r_date, _ = fetch_wiki_poster_and_info(title)
                if thumb or r_date:
                    return mid, thumb, None, r_date, None
            return mid, None, None, None, None

        with ThreadPoolExecutor(max_workers=8) as executor:
            fetched_results = list(executor.map(fetch_single, missing_ids))

        to_insert = []
        now = time.time()
        for mid, poster, backdrop, r_date, vote in fetched_results:
            to_insert.append((mid, poster, backdrop, r_date, vote, now))
            cached_map[mid] = {
                "id": mid,
                "poster_path": poster,
                "backdrop_path": backdrop,
                "release_date": r_date,
                "vote_average": vote,
            }

        if to_insert:
            cur.executemany(
                """
                INSERT OR REPLACE INTO movie_posters (id, poster_path, backdrop_path, release_date, vote_average, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                to_insert,
            )
            conn.commit()

    conn.close()

    result = {}
    for mid, info in cached_map.items():
        poster_path = info.get("poster_path")
        result[str(mid)] = {
            "poster_url": format_poster_url(poster_path, "w342"),
            "backdrop_url": format_poster_url(info.get("backdrop_path"), "w1280"),
            "year": info.get("release_date")[:4] if info.get("release_date") else None,
            "vote_average": info.get("vote_average"),
        }

    return jsonify(result)


@app.route("/api/movies/<int:movie_id>")
@login_required
def get_movie_detail(movie_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT id, title, popularity, adult FROM movies WHERE id = ? AND adult = 0",
        (movie_id,),
    )
    row = cur.fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Movie not found"}), 404

    base_data = dict(row)
    base_data["tmdb_url"] = f"https://www.themoviedb.org/movie/{movie_id}"

    cur.execute("SELECT details_json FROM movie_details_cache WHERE id = ?", (movie_id,))
    cached = cur.fetchone()
    if cached:
        conn.close()
        merged = json.loads(cached["details_json"])
        merged.update(base_data)
        return jsonify(merged)

    details = {
        "overview": "",
        "poster_url": None,
        "backdrop_url": None,
        "release_date": None,
        "genres": [],
        "vote_average": None,
        "vote_count": None,
        "runtime": None,
        "tagline": "",
        "source": "database",
    }

    try:
        data = tmdb_request(f"movie/{movie_id}")
        if data:
            details["overview"] = data.get("overview", "")
            if data.get("poster_path"):
                details["poster_url"] = f"https://image.tmdb.org/t/p/w500{data.get('poster_path')}"
            if data.get("backdrop_path"):
                details["backdrop_url"] = f"https://image.tmdb.org/t/p/w1280{data.get('backdrop_path')}"
            details["release_date"] = data.get("release_date")
            details["genres"] = [g.get("name") for g in data.get("genres", [])]
            details["vote_average"] = data.get("vote_average")
            details["vote_count"] = data.get("vote_count")
            details["runtime"] = data.get("runtime")
            details["tagline"] = data.get("tagline")
            details["source"] = "tmdb_api"

            cur.execute(
                """
                INSERT OR REPLACE INTO movie_posters (id, poster_path, backdrop_path, release_date, vote_average, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    movie_id,
                    data.get("poster_path"),
                    data.get("backdrop_path"),
                    data.get("release_date"),
                    data.get("vote_average"),
                    time.time(),
                ),
            )
    except Exception as e:
        print(f"Error fetching from TMDB API: {e}")

    if not details.get("overview"):
        headers = {"User-Agent": "MovieBrowserApp/1.0 (contact@local)"}
        for candidate in [f"{base_data['title']} (film)", base_data["title"]]:
            try:
                candidate_encoded = urllib.parse.quote(candidate)
                wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{candidate_encoded}"
                req = urllib.request.Request(wiki_url, headers=headers)
                with urllib.request.urlopen(req, timeout=3) as resp:
                    if resp.status == 200:
                        wdata = json.loads(resp.read().decode())
                        extract = wdata.get("extract", "")
                        if (
                            extract
                            and "may refer to" not in extract.lower()
                            and "disambiguation" not in extract.lower()
                        ):
                            details["overview"] = extract
                            if not details.get("poster_url") and wdata.get("thumbnail"):
                                details["poster_url"] = wdata["thumbnail"].get("source")
                            details["source"] = "wikipedia_enriched"
                            break
            except Exception:
                continue

    try:
        cur.execute(
            "INSERT OR REPLACE INTO movie_details_cache (id, details_json, created_at) VALUES (?, ?, ?)",
            (movie_id, json.dumps(details), time.time()),
        )
        conn.commit()
    except Exception:
        pass

    conn.close()
    merged = {**base_data, **details}
    return jsonify(merged)


@app.route("/api/stats")
@login_required
def get_stats():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as total_movies FROM movies;")
    total = cur.fetchone()["total_movies"]
    cur.execute("SELECT COUNT(*) as cached_posters FROM movie_posters WHERE poster_path IS NOT NULL;")
    cached = cur.fetchone()["cached_posters"]
    conn.close()
    return jsonify(
        {
            "total_movies": total,
            "cached_posters": cached,
            "tmdb_api_configured": bool(TMDB_API_KEY),
            "user": session.get("user"),
        }
    )


# ==========================================================================
# TMDB-powered streaming catalog (server-side proxy + short-lived cache)
# ==========================================================================

TMDB_IMG_BASE = "https://image.tmdb.org/t/p"
TMDB_LANGUAGE = os.environ.get("TMDB_LANGUAGE", "en-US")

_tmdb_cache = {}
_tmdb_cache_lock = threading.Lock()


def tmdb_image(path, size="w500"):
    if not path:
        return None
    if str(path).startswith("http://") or str(path).startswith("https://"):
        return path
    return f"{TMDB_IMG_BASE}/{size}{path}"


def tmdb_api(endpoint, params=None, ttl=600):
    """Fetch TMDB data with an in-process TTL cache and graceful failure."""
    query = dict(params or {})
    query.setdefault("language", TMDB_LANGUAGE)
    cache_key = f"{endpoint}?{urllib.parse.urlencode(sorted(query.items()))}"
    now = time.time()

    with _tmdb_cache_lock:
        cached = _tmdb_cache.get(cache_key)
        if cached and cached[1] > now:
            return cached[0]

    try:
        data = tmdb_request(endpoint, query)
    except Exception as exc:
        print(f"[tmdb] {endpoint} failed: {exc}")
        data = {}

    if data:
        with _tmdb_cache_lock:
            if len(_tmdb_cache) > 500:
                for stale_key in list(_tmdb_cache.keys())[:100]:
                    _tmdb_cache.pop(stale_key, None)
            _tmdb_cache[cache_key] = (data, now + ttl)
    return data


def normalize_tmdb_item(item, default_type=None):
    """Convert a raw TMDB movie/tv object into the shape the UI expects."""
    if not item:
        return None
    media_type = item.get("media_type") or default_type
    if media_type == "person":
        return None
    if media_type not in ("movie", "tv"):
        # Trending/all sometimes omits media_type; infer from the payload keys.
        media_type = "tv" if ("first_air_date" in item or "name" in item) else "movie"

    title = (
        item.get("title")
        or item.get("name")
        or item.get("original_title")
        or item.get("original_name")
        or "Untitled"
    )
    date = item.get("release_date") or item.get("first_air_date") or ""
    vote = item.get("vote_average")
    try:
        vote = float(vote) if vote is not None else None
    except (TypeError, ValueError):
        vote = None

    return {
        "id": item.get("id"),
        "media_type": media_type,
        "title": title,
        "original_title": item.get("original_title") or item.get("original_name"),
        "overview": item.get("overview") or "",
        "release_date": date,
        "year": date[:4] if date else None,
        "vote_average": vote,
        "vote_count": item.get("vote_count"),
        "popularity": item.get("popularity"),
        "poster_path": item.get("poster_path"),
        "backdrop_path": item.get("backdrop_path"),
        "poster_url": tmdb_image(item.get("poster_path"), "w342"),
        "backdrop_url": tmdb_image(item.get("backdrop_path"), "w1280"),
        "genre_ids": item.get("genre_ids") or [],
        "original_language": item.get("original_language"),
    }


HOME_ROW_SPECS = [
    {
        "key": "trending",
        "title": "Trending Now",
        "endpoint": "trending/all/day",
        "media_type": "multi",
    },
    {
        "key": "top10",
        "title": "Top 10 Movies Today",
        "endpoint": "trending/movie/day",
        "media_type": "movie",
        "rank": True,
    },
    {
        "key": "popular",
        "title": "Popular Movies",
        "endpoint": "movie/popular",
        "media_type": "movie",
    },
    {
        "key": "top_rated",
        "title": "Top Rated Movies",
        "endpoint": "movie/top_rated",
        "media_type": "movie",
    },
    {
        "key": "now_playing",
        "title": "In Theaters Now",
        "endpoint": "movie/now_playing",
        "media_type": "movie",
    },
    {
        "key": "upcoming",
        "title": "Coming Soon",
        "endpoint": "movie/upcoming",
        "media_type": "movie",
    },
    {
        "key": "tv_popular",
        "title": "Popular Series",
        "endpoint": "tv/popular",
        "media_type": "tv",
    },
    {
        "key": "tv_top_rated",
        "title": "Critically Acclaimed Series",
        "endpoint": "tv/top_rated",
        "media_type": "tv",
    },
    {
        "key": "tv_airing",
        "title": "Airing Today",
        "endpoint": "tv/airing_today",
        "media_type": "tv",
    },
]

KIDS_HOME_ROW_SPECS = [
    {
        "key": "kids_popular",
        "title": "Popular With Kids & Family",
        "endpoint": "discover/movie",
        "params": {
            "with_genres": "10751,16",
            "certification_country": "US",
            "certification.lte": "PG",
            "sort_by": "popularity.desc",
            "include_adult": "false",
        },
        "media_type": "movie",
    },
    {
        "key": "kids_top10",
        "title": "Top 10 Animated Adventures",
        "endpoint": "discover/movie",
        "params": {
            "with_genres": "16",
            "certification_country": "US",
            "certification.lte": "PG",
            "sort_by": "popularity.desc",
            "include_adult": "false",
        },
        "media_type": "movie",
        "rank": True,
    },
    {
        "key": "kids_tv",
        "title": "Kids & Animated Series",
        "endpoint": "discover/tv",
        "params": {
            "with_genres": "10762,16",
            "sort_by": "popularity.desc",
            "include_adult": "false",
        },
        "media_type": "tv",
    },
    {
        "key": "kids_family_top",
        "title": "Critically Acclaimed Family Movies",
        "endpoint": "discover/movie",
        "params": {
            "with_genres": "10751",
            "certification_country": "US",
            "certification.lte": "PG",
            "sort_by": "vote_average.desc",
            "vote_count.gte": "300",
            "include_adult": "false",
        },
        "media_type": "movie",
    },
]

CATALOG_SPECS = {
    "movie": {
        "popular": ("movie/popular", "Popular Movies"),
        "top_rated": ("movie/top_rated", "Top Rated Movies"),
        "now_playing": ("movie/now_playing", "In Theaters Now"),
        "upcoming": ("movie/upcoming", "Coming Soon"),
        "trending": ("trending/movie/week", "Trending Movies"),
    },
    "tv": {
        "popular": ("tv/popular", "Popular Series"),
        "top_rated": ("tv/top_rated", "Top Rated Series"),
        "airing_today": ("tv/airing_today", "Airing Today"),
        "on_the_air": ("tv/on_the_air", "Currently On Air"),
        "trending": ("trending/tv/week", "Trending Series"),
    },
}

GENRE_SPECS = {
    "movie": {
        "genre_28": ("28", "Action Movies"),
        "genre_878": ("878", "Sci-Fi Movies"),
        "genre_27": ("27", "Horror Movies"),
        "genre_53": ("53", "Thrillers"),
        "genre_35": ("35", "Comedy Movies"),
        "genre_18": ("18", "Drama Movies"),
        "genre_16": ("16", "Animation & Anime"),
        "genre_80": ("80", "Crime Movies"),
        "genre_10749": ("10749", "Romance Movies"),
        "genre_99": ("99", "Documentaries"),
        "genre_10751": ("10751", "Family Movies"),
    },
    "tv": {
        "genre_10759": ("10759", "Action & Adventure Series"),
        "genre_10765": ("10765", "Sci-Fi & Fantasy Series"),
        "genre_35": ("35", "Comedy Series"),
        "genre_18": ("18", "Drama Series"),
        "genre_16": ("16", "Animation & Anime Series"),
        "genre_80": ("80", "Crime & Mystery Series"),
        "genre_99": ("99", "Docuseries"),
        "genre_10762": ("10762", "Kids Series"),
    },
}


def _fetch_home_row(spec):
    params = dict(spec.get("params") or {})
    params.setdefault("page", 1)
    data = tmdb_api(spec["endpoint"], params, ttl=600)
    items = []
    for raw in data.get("results", []):
        item = normalize_tmdb_item(raw, spec.get("media_type"))
        if item and item.get("id"):
            items.append(item)
    if spec.get("rank"):
        items = items[:10]
    return {
        "key": spec["key"],
        "title": spec["title"],
        "rank": bool(spec.get("rank")),
        "items": items,
    }


_catalog_warm_lock = threading.Lock()
_last_catalog_warm = 0.0


def _warm_catalog_worker():
    try:
        with ThreadPoolExecutor(max_workers=9) as executor:
            list(executor.map(_fetch_home_row, HOME_ROW_SPECS))
    except Exception as exc:
        print(f"[warm] catalog warmup error: {exc}")


def warm_home_catalog_async():
    """Pre-warm the server-side TMDB home catalog cache in a background thread."""
    global _last_catalog_warm
    now = time.time()
    with _catalog_warm_lock:
        if now - _last_catalog_warm < 240:
            return
        _last_catalog_warm = now
    threading.Thread(target=_warm_catalog_worker, daemon=True).start()


def build_home_payload(username):
    active_profile, profiles = _get_active_profile(username)
    profile_id = active_profile["id"]
    is_kids = bool(active_profile.get("is_kids"))

    row_specs = KIDS_HOME_ROW_SPECS if is_kids else HOME_ROW_SPECS
    with ThreadPoolExecutor(max_workers=9) as executor:
        rows = list(executor.map(_fetch_home_row, row_specs))

    rows = [row for row in rows if row["items"]]

    conn = get_db()
    watchlist_rows = conn.execute(
        """
        SELECT * FROM user_watchlist
        WHERE username = ? AND profile_id IN (?, 0)
        ORDER BY created_at DESC LIMIT 40
        """,
        (username, profile_id),
    ).fetchall()
    continue_rows = conn.execute(
        """
        SELECT * FROM watch_history
        WHERE username = ? AND profile_id IN (?, 0)
          AND NOT (duration_seconds > 0 AND progress_seconds >= duration_seconds * 0.95)
        ORDER BY updated_at DESC LIMIT 20
        """,
        (username, profile_id),
    ).fetchall()
    last_watched = conn.execute(
        """
        SELECT media_type, tmdb_id, title FROM watch_history
        WHERE username = ? AND profile_id IN (?, 0)
        ORDER BY updated_at DESC LIMIT 1
        """,
        (username, profile_id),
    ).fetchone()
    conn.close()

    watchlist_items = [normalize_watchlist_row(r) for r in watchlist_rows]
    continue_items = [normalize_history_row(r) for r in continue_rows]

    # Dynamic "Because you watched <Title>" row from TMDB recommendations
    if last_watched and not is_kids:
        lw_type = last_watched["media_type"]
        lw_id = last_watched["tmdb_id"]
        lw_title = last_watched["title"]
        rec_data = tmdb_api(f"{lw_type}/{lw_id}/recommendations", {"page": 1}, ttl=900)
        rec_items = []
        for raw in (rec_data.get("results") or [])[:16]:
            item = normalize_tmdb_item(raw, lw_type)
            if item and item.get("id") and item.get("poster_url"):
                rec_items.append(item)
        if rec_items:
            because_row = {
                "key": f"because_{lw_type}_{lw_id}",
                "title": f"Because you watched {lw_title}",
                "rank": False,
                "items": rec_items,
            }
            insert_idx = 1 if len(rows) >= 1 else 0
            rows.insert(insert_idx, because_row)

    hero_pool = rows[0]["items"] if rows else []
    if not hero_pool:
        hero_pool = rows[1]["items"] if len(rows) > 1 else []
    hero = [item for item in hero_pool if item.get("backdrop_url") or item.get("poster_url")][:6]
    return {
        "hero": hero,
        "rows": rows,
        "watchlist": watchlist_items,
        "continue_watching": continue_items,
        "active_profile": active_profile,
        "profiles": profiles,
        "needs_profile_selection": not bool(session.get("profile_selected")),
        "max_concurrent_streams": MAX_CONCURRENT_STREAMS,
    }


@app.route("/api/home")
@login_required
def api_home():
    username = session.get("user")
    return jsonify(build_home_payload(username))


# Trigger background warmup on server import/boot so even the first login is instant
warm_home_catalog_async()


@app.route("/api/catalog")
@login_required
def api_catalog():
    username = session.get("user")
    active_profile, _ = _get_active_profile(username)
    is_kids = bool(active_profile.get("is_kids"))

    media_type = (request.args.get("type") or "movie").lower()
    category = (request.args.get("category") or "popular").lower()
    try:
        page = max(1, min(500, int(request.args.get("page", 1))))
    except (TypeError, ValueError):
        page = 1

    if media_type not in CATALOG_SPECS:
        media_type = "movie"
    specs = CATALOG_SPECS[media_type]
    genre_map = GENRE_SPECS.get(media_type, {})

    params = {"page": page}
    if category in genre_map:
        genre_id, title = genre_map[category]
        endpoint = f"discover/{media_type}"
        params.update(
            {
                "with_genres": genre_id,
                "sort_by": "popularity.desc",
                "include_adult": "false",
            }
        )
        if is_kids and media_type == "movie":
            params["certification_country"] = "US"
            params["certification.lte"] = "PG"
    elif is_kids:
        endpoint = f"discover/{media_type}"
        title = "Kids & Family Movies" if media_type == "movie" else "Kids & Animated Series"
        params.update(
            {
                "with_genres": "10751,16" if media_type == "movie" else "10762,16",
                "sort_by": "popularity.desc",
                "include_adult": "false",
            }
        )
        if media_type == "movie":
            params["certification_country"] = "US"
            params["certification.lte"] = "PG"
    else:
        endpoint, title = specs.get(category, specs["popular"])

    data = tmdb_api(endpoint, params, ttl=300)
    items = []
    for raw in data.get("results", []):
        item = normalize_tmdb_item(raw, media_type)
        if item and item.get("id"):
            items.append(item)

    return jsonify(
        {
            "items": items,
            "page": page,
            "total_pages": min(int(data.get("total_pages") or 1), 500),
            "total_results": int(data.get("total_results") or len(items)),
            "title": title,
            "type": media_type,
            "category": category,
        }
    )


def local_catalog_search(query, limit=24):
    """Offline FTS fallback for when the TMDB API is unreachable."""
    sanitized = re.sub(r"[^\w\s]", "", query).strip()
    if not sanitized:
        return []
    conn = get_db()
    cur = conn.cursor()
    rows = []
    try:
        cur.execute(
            """
            SELECT m.id, m.title, m.popularity, m.adult,
                   p.poster_path, p.backdrop_path, p.release_date, p.vote_average
            FROM movies_fts f
            JOIN movies m ON m.id = f.rowid
            LEFT JOIN movie_posters p ON m.id = p.id
            WHERE movies_fts MATCH ? AND m.adult = 0
            ORDER BY m.popularity DESC
            LIMIT ?
            """,
            (f'"{sanitized}"*', limit),
        )
        rows = cur.fetchall()
    except sqlite3.OperationalError:
        cur.execute(
            """
            SELECT m.id, m.title, m.popularity, m.adult,
                   p.poster_path, p.backdrop_path, p.release_date, p.vote_average
            FROM movies m
            LEFT JOIN movie_posters p ON m.id = p.id
            WHERE m.title LIKE ? AND m.adult = 0
            ORDER BY m.popularity DESC
            LIMIT ?
            """,
            (f"%{query}%", limit),
        )
        rows = cur.fetchall()
    finally:
        conn.close()

    results = []
    for row in rows:
        item = normalize_tmdb_item(
            {
                "id": row["id"],
                "title": row["title"],
                "media_type": "movie",
                "poster_path": row["poster_path"],
                "backdrop_path": row["backdrop_path"],
                "release_date": row["release_date"],
                "vote_average": row["vote_average"],
                "popularity": row["popularity"],
            },
            "movie",
        )
        if item:
            results.append(item)
    return results


@app.route("/api/search")
@login_required
def api_search():
    query = (request.args.get("q") or "").strip()[:200]
    media_type = (request.args.get("type") or "multi").lower()
    try:
        page = max(1, min(500, int(request.args.get("page", 1))))
    except (TypeError, ValueError):
        page = 1

    if not query:
        return jsonify({"items": [], "page": 1, "total_pages": 0, "total_results": 0})

    if media_type not in ("multi", "movie", "tv"):
        media_type = "multi"

    items = []

    # A bare number is almost always a TMDB ID — resolve it directly first.
    if query.isdigit() and page == 1:
        candidates = ["tv", "movie"] if media_type == "multi" else [media_type]
        for candidate in candidates:
            detail = tmdb_api(f"{candidate}/{int(query)}", ttl=3600)
            item = normalize_tmdb_item(detail, candidate)
            if item and item.get("id"):
                items.append(item)

    if media_type == "multi":
        endpoint = "search/multi"
    else:
        endpoint = f"search/{media_type}"

    data = tmdb_api(
        endpoint,
        {"query": query, "page": page, "include_adult": "false"},
        ttl=300,
    )
    seen = {(item["media_type"], item["id"]) for item in items}
    for raw in data.get("results", []):
        item = normalize_tmdb_item(raw, None if media_type == "multi" else media_type)
        if not item or not item.get("id"):
            continue
        key = (item["media_type"], item["id"])
        if key in seen:
            continue
        seen.add(key)
        items.append(item)

    if not items and page == 1:
        items = local_catalog_search(query)

    return jsonify(
        {
            "items": items,
            "page": page,
            "total_pages": min(int(data.get("total_pages") or 1), 500),
            "total_results": int(data.get("total_results") or len(items)),
            "query": query,
            "type": media_type,
        }
    )


@app.route("/api/title/<media_type>/<int:tmdb_id>")
@login_required
def api_title_detail(media_type, tmdb_id):
    if media_type not in ("movie", "tv"):
        return jsonify({"error": "Unsupported media type"}), 400

    data = tmdb_api(
        f"{media_type}/{tmdb_id}",
        {"append_to_response": "credits,videos,recommendations,external_ids"},
        ttl=3600,
    )
    if not data or not data.get("id"):
        return jsonify({"error": "Title not found"}), 404

    item = normalize_tmdb_item(data, media_type)
    if not item:
        return jsonify({"error": "Title not found"}), 404

    credits = data.get("credits") or {}
    crew = credits.get("crew") or []
    cast = []
    for member in (credits.get("cast") or [])[:12]:
        cast.append(
            {
                "id": member.get("id"),
                "name": member.get("name"),
                "character": member.get("character"),
                "profile_url": tmdb_image(member.get("profile_path"), "w185"),
            }
        )

    directors = []
    director_items = []
    for member in crew:
        if member.get("job") in ("Director", "Creator"):
            name = member.get("name")
            if name and name not in directors:
                directors.append(name)
                director_items.append({"id": member.get("id"), "name": name})

    videos = (data.get("videos") or {}).get("results") or []
    trailer_key = None
    for video in videos:
        if video.get("site") == "YouTube" and video.get("type") in ("Trailer", "Teaser"):
            trailer_key = video.get("key")
            break

    seasons = []
    for season in data.get("seasons") or []:
        season_number = season.get("season_number")
        if season_number is None:
            continue
        seasons.append(
            {
                "season_number": season_number,
                "name": season.get("name") or f"Season {season_number}",
                "episode_count": season.get("episode_count") or 0,
                "air_date": season.get("air_date"),
                "year": (season.get("air_date") or "")[:4] or None,
                "poster_url": tmdb_image(season.get("poster_path"), "w342"),
            }
        )

    recommendations = []
    for raw in (data.get("recommendations") or {}).get("results", [])[:14]:
        rec = normalize_tmdb_item(raw, media_type)
        if rec and rec.get("id") and rec.get("poster_url"):
            recommendations.append(rec)

    runtimes = data.get("episode_run_time") or []
    runtime = data.get("runtime")
    if media_type == "tv" and not runtime and runtimes:
        runtime = round(sum(runtimes) / len(runtimes))

    username = session.get("user")
    active_profile, _ = _get_active_profile(username)
    conn = get_db()
    in_wl = conn.execute(
        "SELECT 1 FROM user_watchlist WHERE username = ? AND profile_id IN (?, 0) AND media_type = ? AND tmdb_id = ?",
        (username, active_profile["id"], media_type, tmdb_id),
    ).fetchone()
    conn.close()

    item.update(
        {
            "tagline": data.get("tagline") or "",
            "status": data.get("status"),
            "genres": [g.get("name") for g in data.get("genres") or [] if g.get("name")],
            "runtime": runtime,
            "number_of_seasons": data.get("number_of_seasons"),
            "number_of_episodes": data.get("number_of_episodes"),
            "directors": directors,
            "director_items": director_items,
            "cast": cast,
            "trailer_key": trailer_key,
            "seasons": seasons,
            "recommendations": recommendations,
            "in_watchlist": bool(in_wl),
            "imdb_id": data.get("imdb_id") or (data.get("external_ids") or {}).get("imdb_id"),
            "tmdb_url": f"https://www.themoviedb.org/{media_type}/{tmdb_id}",
            "source": "tmdb",
        }
    )
    return jsonify(item)


@app.route("/api/person/<int:person_id>")
@login_required
def api_person(person_id):
    if person_id <= 0 or person_id > 50_000_000:
        return jsonify({"error": "Person not found"}), 404
    data = tmdb_api(
        f"person/{person_id}",
        {"append_to_response": "combined_credits"},
        ttl=3600,
    )
    if not data or not data.get("id"):
        return jsonify({"error": "Person not found"}), 404

    combined = data.get("combined_credits") or {}
    raw_credits = list(combined.get("cast") or []) + [
        c for c in (combined.get("crew") or []) if c.get("job") in ("Director", "Creator", "Writer")
    ]
    seen = set()
    items = []
    for raw in sorted(raw_credits, key=lambda x: float(x.get("popularity") or 0), reverse=True):
        item = normalize_tmdb_item(raw)
        if not item or not item.get("id") or not item.get("poster_url"):
            continue
        key = (item["media_type"], item["id"])
        if key in seen:
            continue
        seen.add(key)
        items.append(item)
        if len(items) >= 48:
            break

    return jsonify(
        {
            "id": data.get("id"),
            "name": data.get("name") or "Unknown",
            "biography": (data.get("biography") or "")[:1200],
            "known_for_department": data.get("known_for_department") or "",
            "birthday": data.get("birthday") or "",
            "place_of_birth": data.get("place_of_birth") or "",
            "profile_url": tmdb_image(data.get("profile_path"), "w342"),
            "items": items,
        }
    )


@app.route("/api/tv/<int:tmdb_id>/season/<int:season_number>")
@login_required
def api_tv_season(tmdb_id, season_number):
    if tmdb_id <= 0 or tmdb_id > 50_000_000 or season_number < 0 or season_number > 500:
        return jsonify({"error": "Season not found"}), 404
    data = tmdb_api(f"tv/{tmdb_id}/season/{season_number}", ttl=3600)
    if not data:
        return jsonify({"error": "Season not found"}), 404

    episodes = []
    for episode in data.get("episodes") or []:
        episodes.append(
            {
                "episode_number": episode.get("episode_number"),
                "name": episode.get("name") or f"Episode {episode.get('episode_number')}",
                "overview": episode.get("overview") or "",
                "air_date": episode.get("air_date"),
                "runtime": episode.get("runtime"),
                "still_url": tmdb_image(episode.get("still_path"), "w300"),
                "vote_average": episode.get("vote_average"),
            }
        )

    return jsonify(
        {
            "season_number": data.get("season_number", season_number),
            "name": data.get("name") or f"Season {season_number}",
            "overview": data.get("overview") or "",
            "episodes": episodes,
        }
    )


# ==========================================================================
# Concurrent Stream Limiter (Max 3 Active Streams per Account)
# ==========================================================================

MAX_CONCURRENT_STREAMS = 3
STREAM_HEARTBEAT_TTL = 75.0


def _cleanup_expired_streams(conn):
    cutoff = time.time() - STREAM_HEARTBEAT_TTL
    conn.execute("DELETE FROM active_streams WHERE last_heartbeat < ?", (cutoff,))


def _serialize_active_stream(row):
    return {
        "stream_token": row["stream_token"][:8] + "…",
        "profile_name": row["profile_name"] or row["username"],
        "title": row["title"] or "Playing title",
        "media_type": row["media_type"] or "movie",
        "started_at": row["started_at"],
        "last_heartbeat": row["last_heartbeat"],
    }


@app.route("/api/stream/acquire", methods=["POST"])
@login_required
def api_stream_acquire():
    if not verify_csrf():
        return jsonify({"error": "Invalid CSRF token"}), 400

    username = session.get("user")
    active_profile, _ = _get_active_profile(username)
    payload = request.get_json(silent=True) or {}

    raw_token = str(payload.get("stream_token") or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{12,64}", raw_token):
        raw_token = secrets.token_urlsafe(24)

    media_type = str(payload.get("media_type") or "movie").lower()
    if media_type not in ("movie", "tv"):
        media_type = "movie"
    try:
        tmdb_id = int(payload.get("tmdb_id") or payload.get("id") or 0)
    except (TypeError, ValueError):
        tmdb_id = 0
    title = str(payload.get("title") or "Playing Title").strip()[:200]
    force_takeover = bool(payload.get("force_takeover"))

    now = time.time()
    conn = get_db()
    _cleanup_expired_streams(conn)

    # Check if this exact tab/token already holds an active slot for this user
    existing_self = conn.execute(
        "SELECT stream_token, started_at FROM active_streams WHERE stream_token = ? AND username = ?",
        (raw_token, username),
    ).fetchone()

    if existing_self:
        conn.execute(
            """
            UPDATE active_streams
            SET profile_id = ?, profile_name = ?, media_type = ?, tmdb_id = ?, title = ?, last_heartbeat = ?
            WHERE stream_token = ? AND username = ?
            """,
            (
                active_profile["id"],
                active_profile["name"],
                media_type,
                tmdb_id,
                title,
                now,
                raw_token,
                username,
            ),
        )
        conn.commit()
        active_rows = conn.execute(
            "SELECT * FROM active_streams WHERE username = ? ORDER BY started_at ASC",
            (username,),
        ).fetchall()
        conn.close()
        return jsonify(
            {
                "ok": True,
                "stream_token": raw_token,
                "active_count": len(active_rows),
                "max_streams": MAX_CONCURRENT_STREAMS,
            }
        )

    active_rows = conn.execute(
        "SELECT * FROM active_streams WHERE username = ? ORDER BY last_heartbeat ASC, started_at ASC",
        (username,),
    ).fetchall()

    if len(active_rows) >= MAX_CONCURRENT_STREAMS:
        if force_takeover and active_rows:
            oldest_token = active_rows[0]["stream_token"]
            conn.execute(
                "DELETE FROM active_streams WHERE stream_token = ? AND username = ?",
                (oldest_token, username),
            )
            active_rows = active_rows[1:]
        else:
            streams_info = [_serialize_active_stream(r) for r in active_rows]
            conn.commit()
            conn.close()
            return (
                jsonify(
                    {
                        "ok": False,
                        "stream_limit_reached": True,
                        "max_streams": MAX_CONCURRENT_STREAMS,
                        "active_count": len(streams_info),
                        "active_streams": streams_info,
                        "error": f"Your account is already streaming on {MAX_CONCURRENT_STREAMS} screens simultaneously.",
                    }
                ),
                429,
            )

    conn.execute(
        """
        INSERT OR REPLACE INTO active_streams (
            stream_token, username, profile_id, profile_name, media_type, tmdb_id,
            title, client_ip, user_agent, started_at, last_heartbeat
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            raw_token,
            username,
            active_profile["id"],
            active_profile["name"],
            media_type,
            tmdb_id,
            title,
            get_client_ip(),
            (request.headers.get("User-Agent") or "")[:200],
            now,
            now,
        ),
    )
    conn.commit()
    total_now = len(active_rows) + 1
    conn.close()
    return jsonify(
        {
            "ok": True,
            "stream_token": raw_token,
            "active_count": total_now,
            "max_streams": MAX_CONCURRENT_STREAMS,
        }
    )


@app.route("/api/stream/heartbeat", methods=["POST"])
@login_required
def api_stream_heartbeat():
    if not verify_csrf():
        return jsonify({"error": "Invalid CSRF token"}), 400

    username = session.get("user")
    payload = request.get_json(silent=True) or {}
    raw_token = str(payload.get("stream_token") or "").strip()
    if not raw_token:
        return jsonify({"ok": False, "terminated": True}), 400

    now = time.time()
    conn = get_db()
    _cleanup_expired_streams(conn)
    row = conn.execute(
        "SELECT stream_token FROM active_streams WHERE stream_token = ? AND username = ?",
        (raw_token, username),
    ).fetchone()
    if not row:
        conn.commit()
        conn.close()
        return jsonify(
            {
                "ok": False,
                "terminated": True,
                "reason": "Playback was transferred to another screen on your account (3-stream limit).",
            }
        )

    conn.execute(
        "UPDATE active_streams SET last_heartbeat = ? WHERE stream_token = ? AND username = ?",
        (now, raw_token, username),
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/api/stream/release", methods=["POST"])
@login_required
def api_stream_release():
    if not verify_csrf():
        return jsonify({"error": "Invalid CSRF token"}), 400
    username = session.get("user")
    payload = request.get_json(silent=True) or {}
    raw_token = str(payload.get("stream_token") or "").strip()
    if raw_token:
        conn = get_db()
        conn.execute(
            "DELETE FROM active_streams WHERE stream_token = ? AND username = ?",
            (raw_token, username),
        )
        conn.commit()
        conn.close()
    return jsonify({"ok": True})


# ==========================================================================
# Lumière Native Video Stream & Multi-Language Subtitle Engine
# ==========================================================================

_subtitle_cache = {}
_subtitle_cache_lock = threading.Lock()

PRIORITY_SUBTITLE_LANGS = {
    "en": (1, "English"),
    "eng": (1, "English"),
    "ms": (2, "Bahasa Melayu"),
    "may": (2, "Bahasa Melayu"),
    "msa": (2, "Bahasa Melayu"),
    "id": (3, "Bahasa Indonesia"),
    "ind": (3, "Bahasa Indonesia"),
    "zh": (4, "Chinese (中文)"),
    "zho": (4, "Chinese (中文)"),
    "chi": (4, "Chinese (中文)"),
    "zs": (4, "Chinese Simplified"),
    "zt": (5, "Chinese Traditional"),
    "ta": (6, "Tamil (தமிழ்)"),
    "tam": (6, "Tamil (தமிழ்)"),
    "hi": (7, "Hindi (हिन्दी)"),
    "hin": (7, "Hindi (हिन्दी)"),
    "ko": (8, "Korean (한국어)"),
    "kor": (8, "Korean (한국어)"),
    "ja": (9, "Japanese (日本語)"),
    "jpn": (9, "Japanese (日本語)"),
    "es": (10, "Español"),
    "spa": (10, "Español"),
    "ar": (11, "Arabic (العربية)"),
    "ara": (11, "Arabic (العربية)"),
    "fr": (12, "Français"),
    "fre": (12, "Français"),
    "fra": (12, "Français"),
    "de": (13, "Deutsch"),
    "ger": (13, "Deutsch"),
    "deu": (13, "Deutsch"),
    "pt": (14, "Português"),
    "por": (14, "Português"),
    "pob": (14, "Português (Brasil)"),
    "ru": (15, "Русский"),
    "rus": (15, "Русский"),
    "tr": (16, "Türkçe"),
    "tur": (16, "Türkçe"),
    "vi": (17, "Tiếng Việt"),
    "vie": (17, "Tiếng Việt"),
    "th": (18, "ไทย"),
    "tha": (18, "ไทย"),
    "it": (19, "Italiano"),
    "ita": (19, "Italiano"),
    "nl": (20, "Nederlands"),
    "dut": (20, "Nederlands"),
    "pol": (21, "Polski"),
}

SAFE_SUBTITLE_HOST_RE = re.compile(
    r"^(?:[a-z0-9-]+\.)*(?:strem\.io|wyzie\.ru|opensubtitles\.org|subdl\.com|subf2m\.co)$",
    re.IGNORECASE,
)


def _srt_to_webvtt(raw_text: str) -> str:
    """Convert .srt or .vtt subtitle text into normalized W3C WEBVTT."""
    text = (raw_text or "").replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff").strip()
    if not text:
        return "WEBVTT\n\n"
    if text.startswith("WEBVTT"):
        return text + "\n"
    # Convert SRT timestamps 00:01:20,500 --> 00:01:23,200 to 00:01:20.500 --> 00:01:23.200
    converted = re.sub(
        r"(\d{1,2}:\d{2}:\d{2}),(\d{3})\s*-->\s*(\d{1,2}:\d{2}:\d{2}),(\d{3})",
        r"\1.\2 --> \3.\4",
        text,
    )
    return "WEBVTT\n\n" + converted + "\n"


def _parse_vtt_cues(vtt_text: str) -> list:
    """Parse WebVTT/SRT text into [{start, end, text}] cues for universal overlay rendering."""
    cues = []
    blocks = re.split(r"\n\s*\n", (vtt_text or "").strip())
    time_re = re.compile(
        r"(?:(\d{1,2}):)?(\d{2}):(\d{2})[.,](\d{3})\s*-->\s*(?:(\d{1,2}):)?(\d{2}):(\d{2})[.,](\d{3})"
    )

    def _to_sec(h, m, s, ms):
        return (int(h or 0) * 3600) + (int(m) * 60) + int(s) + (int(ms) / 1000.0)

    for block in blocks:
        lines = [ln.strip() for ln in block.split("\n") if ln.strip()]
        if not lines or lines[0].startswith("WEBVTT") or lines[0].startswith("NOTE"):
            continue
        match = None
        text_start_idx = 0
        for idx, ln in enumerate(lines[:2]):
            m = time_re.search(ln)
            if m:
                match = m
                text_start_idx = idx + 1
                break
        if not match:
            continue
        start_s = _to_sec(match.group(1), match.group(2), match.group(3), match.group(4))
        end_s = _to_sec(match.group(5), match.group(6), match.group(7), match.group(8))
        raw_caption = "\n".join(lines[text_start_idx:])
        # Strip ASS/SSA override tags {\an8} and HTML tags except basic line breaks
        clean_caption = re.sub(r"\{[^}]*\}", "", raw_caption)
        clean_caption = re.sub(r"<[^>]+>", "", clean_caption).strip()
        if clean_caption and end_s > start_s:
            cues.append({"start": round(start_s, 3), "end": round(end_s, 3), "text": clean_caption})
        if len(cues) >= 3500:
            break
    return cues


# ==========================================================================
# Lumière Native Stream Extraction & DASH Proxy Engine (100% Ad-Free)
# ==========================================================================

VIDLINK_KEY_HEX = "c75136c5668bbfe65a7ecad431a745db68b5f381555b38d8f6c699449cf11fcd"
VIDLINK_KEY = bytes.fromhex(VIDLINK_KEY_HEX)
VIDLINK_NONCE = bytes(24)


def _encrypt_vidlink_token(media_id: str) -> str:
    if not HAVE_NATIVE_EXTRACTOR:
        return ""
    try:
        box = nacl.secret.SecretBox(VIDLINK_KEY)
        timestamp = int(time.time() + 480)
        message = str(media_id).encode("utf-8") + struct.pack(">Q", timestamp)
        encrypted = box.encrypt(message, VIDLINK_NONCE)
        full_payload = VIDLINK_NONCE + encrypted.ciphertext
        return base64.urlsafe_b64encode(full_payload).decode("utf-8").rstrip("=")
    except Exception as e:
        logging.warning("Failed to encrypt token: %s", e)
        return ""


def resolve_native_stream(media_type: str, tmdb_id: int, season: int = 1, episode: int = 1):
    """Extract direct DASH stream from VidLink API without showing any ads or popups."""
    if not HAVE_NATIVE_EXTRACTOR:
        return None
    try:
        token = _encrypt_vidlink_token(str(tmdb_id))
        if not token:
            return None
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
            "Origin": "https://vidlink.pro",
            "Referer": "https://vidlink.pro/",
            "x-playback-environment": "webkit",
        }
        if media_type == "tv":
            url = f"https://vidlink.pro/api/b/tv/{token}/{season}/{episode}?multiLang=1"
        else:
            url = f"https://vidlink.pro/api/b/movie/{token}?multiLang=1"

        res = curl_requests.get(url, headers=headers, impersonate="chrome110", timeout=12)
        if res.status_code != 200:
            return None
        data = res.json()
        if not isinstance(data, dict):
            return None
        stream = data.get("stream")
        if not isinstance(stream, dict):
            return None

        playlist_url = stream.get("playlist")
        playlist_headers = stream.get("playlistHeaders") or {}
        captions = stream.get("captions") or []

        if playlist_url and playlist_headers:
            session_id = secrets.token_urlsafe(18)
            base_url = playlist_url.rsplit("/", 1)[0] + "/"
            now = time.time()
            stream_headers = {
                "User-Agent": headers["User-Agent"],
                "Referer": "https://vidlink.pro/",
                "Origin": "https://vidlink.pro",
                **playlist_headers,
            }
            conn = get_db()
            conn.execute(
                """
                INSERT OR REPLACE INTO dash_stream_sessions (
                    session_id, base_url, manifest_url, headers_json, expires_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (session_id, base_url, playlist_url, json.dumps(stream_headers), now + 14400),
            )
            conn.commit()
            conn.close()

            return {
                "type": "dash",
                "url": f"/api/stream/dash/manifest/{session_id}",
                "session_id": session_id,
                "quality_label": "1080p FULL HD (Ad-Free)",
                "captions": captions,
            }
        return None
    except Exception as e:
        logging.warning("Error resolving native stream: %s", e)
        return None


@app.route("/api/stream/dash/manifest/<session_id>")
def api_stream_dash_manifest(session_id):
    session_id = str(session_id or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{12,64}", session_id):
        return jsonify({"error": "Invalid session token"}), 400

    conn = get_db()
    row = conn.execute(
        """
        SELECT base_url, manifest_url, headers_json, expires_at
        FROM dash_stream_sessions WHERE session_id = ?
        """,
        (session_id,),
    ).fetchone()
    conn.close()

    if not row or float(row["expires_at"] or 0) < time.time():
        return jsonify({"error": "Stream session expired or invalid"}), 404

    headers = json.loads(row["headers_json"] or "{}")
    try:
        res = curl_requests.get(row["manifest_url"], headers=headers, impersonate="chrome110", timeout=12)
        if res.status_code != 200:
            return jsonify({"error": "Upstream manifest error"}), 502

        mpd_text = res.text
        base_tag = f"<BaseURL>/api/stream/dash/segment/{session_id}/</BaseURL>"
        modified_mpd = re.sub(r"(<MPD\b[^>]*>)", r"\1\n  " + base_tag, mpd_text, count=1)

        response = Response(modified_mpd, mimetype="application/dash+xml")
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Cache-Control"] = "no-cache, no-store"
        return response
    except Exception as e:
        logging.warning("Manifest proxy error: %s", e)
        return jsonify({"error": "Manifest generation error"}), 500


@app.route("/api/stream/dash/segment/<session_id>/<path:filename>")
def api_stream_dash_segment(session_id, filename):
    session_id = str(session_id or "").strip()
    filename = str(filename or "").strip()

    if not re.fullmatch(r"[A-Za-z0-9_-]{12,64}", session_id):
        return jsonify({"error": "Invalid session token"}), 400

    if not re.fullmatch(r"[A-Za-z0-9_\-\.%]+\.(?:m4s|mp4|webm)", filename):
        return jsonify({"error": "Invalid segment path"}), 400

    conn = get_db()
    row = conn.execute(
        """
        SELECT base_url, headers_json, expires_at
        FROM dash_stream_sessions WHERE session_id = ?
        """,
        (session_id,),
    ).fetchone()
    conn.close()

    if not row or float(row["expires_at"] or 0) < time.time():
        return jsonify({"error": "Stream session expired or invalid"}), 404

    headers = json.loads(row["headers_json"] or "{}")
    target_url = row["base_url"] + filename

    try:
        upstream = curl_requests.get(target_url, headers=headers, stream=True, impersonate="chrome110", timeout=15)
        def generate():
            for chunk in upstream.iter_content(chunk_size=65536):
                if chunk:
                    yield chunk

        resp = Response(
            stream_with_context(generate()),
            status=upstream.status_code,
            content_type=upstream.headers.get("Content-Type", "video/iso.segment"),
        )
        cl = upstream.headers.get("Content-Length")
        if cl:
            resp.headers["Content-Length"] = cl
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Cache-Control"] = "public, max-age=86400"
        return resp
    except Exception as e:
        logging.warning("Segment proxy error: %s", e)
        return jsonify({"error": "Segment transfer error"}), 502
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Cache-Control"] = "public, max-age=86400"
        return resp
    except Exception as e:
        logging.warning("Segment proxy error: %s", e)
        return jsonify({"error": "Segment transfer error"}), 502


@app.route("/api/stream/<media_type>/<int:tmdb_id>", methods=["GET", "POST", "DELETE"])
@login_required
def api_custom_stream(media_type, tmdb_id):
    if media_type not in ("movie", "tv") or tmdb_id <= 0 or tmdb_id > 50_000_000:
        return jsonify({"error": "Invalid media target"}), 400

    try:
        season = max(1, min(500, int(request.args.get("season") or 1)))
        episode = max(1, min(5000, int(request.args.get("episode") or 1)))
    except (TypeError, ValueError):
        season, episode = 1, 1

    if media_type == "movie":
        season, episode = 1, 1

    if request.method == "GET":
        conn = get_db()
        row = conn.execute(
            """
            SELECT stream_url, stream_type, quality_label, updated_at
            FROM custom_streams
            WHERE media_type = ? AND tmdb_id = ? AND season = ? AND episode = ?
            """,
            (media_type, tmdb_id, season, episode),
        ).fetchone()
        conn.close()
        if row:
            return jsonify(
                {
                    "has_direct_stream": True,
                    "stream": {
                        "url": row["stream_url"],
                        "type": row["stream_type"] or "mp4",
                        "quality_label": row["quality_label"] or "1080p Full HD",
                    },
                }
            )

        # Auto-extract ad-free DASH stream via Lumière Cinema Engine
        resolved = resolve_native_stream(media_type, tmdb_id, season, episode)
        if resolved:
            return jsonify({"has_direct_stream": True, "stream": resolved})

        return jsonify({"has_direct_stream": False, "stream": None})

    if session.get("role") != "admin":
        return jsonify({"error": "Admin privileges required"}), 403
    if not verify_csrf():
        return jsonify({"error": "Invalid CSRF token"}), 400

    if request.method == "DELETE":
        conn = get_db()
        conn.execute(
            "DELETE FROM custom_streams WHERE media_type = ? AND tmdb_id = ? AND season = ? AND episode = ?",
            (media_type, tmdb_id, season, episode),
        )
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "has_direct_stream": False})

    payload = request.get_json(silent=True) or {}
    try:
        season = max(1, min(500, int(payload.get("season") or season)))
        episode = max(1, min(5000, int(payload.get("episode") or episode)))
    except (TypeError, ValueError):
        season, episode = 1, 1
    if media_type == "movie":
        season, episode = 1, 1

    stream_url = str(payload.get("stream_url") or "").strip()[:1000]
    if not stream_url or not re.match(r"^https?://[^\s\"'<>]+$", stream_url, re.IGNORECASE):
        return jsonify({"error": "A valid http(s) .m3u8 or .mp4 stream URL is required"}), 400

    stream_type = "hls" if ".m3u8" in stream_url.lower() else "mp4"
    quality_label = str(payload.get("quality_label") or "1080p Full HD").strip()[:40]

    conn = get_db()
    conn.execute(
        """
        INSERT OR REPLACE INTO custom_streams (
            media_type, tmdb_id, season, episode, stream_url, stream_type, quality_label, added_by, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            media_type,
            tmdb_id,
            season,
            episode,
            stream_url,
            stream_type,
            quality_label,
            session.get("user"),
            time.time(),
        ),
    )
    conn.commit()
    conn.close()
    return jsonify(
        {
            "ok": True,
            "has_direct_stream": True,
            "stream": {"url": stream_url, "type": stream_type, "quality_label": quality_label},
        }
    )


@app.route("/api/subtitles/<media_type>/<int:tmdb_id>")
@login_required
def api_subtitles(media_type, tmdb_id):
    if media_type not in ("movie", "tv") or tmdb_id <= 0 or tmdb_id > 50_000_000:
        return jsonify({"tracks": []})

    try:
        season = max(1, min(500, int(request.args.get("season") or 1)))
        episode = max(1, min(5000, int(request.args.get("episode") or 1)))
    except (TypeError, ValueError):
        season, episode = 1, 1

    cache_key = f"subs:{media_type}:{tmdb_id}:{season if media_type == 'tv' else 0}:{episode if media_type == 'tv' else 0}"
    now = time.time()
    with _subtitle_cache_lock:
        cached = _subtitle_cache.get(cache_key)
        if cached and cached[1] > now:
            return jsonify({"tracks": cached[0]})

    tracks = []
    try:
        ext_data = tmdb_api(f"{media_type}/{tmdb_id}/external_ids", ttl=86400)
        imdb_id = (ext_data or {}).get("imdb_id")
        if imdb_id and re.fullmatch(r"tt\d{5,12}", str(imdb_id)):
            if media_type == "tv":
                os_url = f"https://opensubtitles-v3.strem.io/subtitles/series/{imdb_id}:{season}:{episode}.json"
            else:
                os_url = f"https://opensubtitles-v3.strem.io/subtitles/movie/{imdb_id}.json"
            req = urllib.request.Request(
                os_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
                    "Accept": "application/json",
                },
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    payload = json.loads(resp.read().decode("utf-8", errors="replace"))
                    raw_list = payload.get("subtitles") if isinstance(payload, dict) else []
                    if isinstance(raw_list, list):
                        seen_langs = {}
                        for item in raw_list:
                            sub_url = str(item.get("url") or "").strip()
                            if not sub_url.startswith("https://"):
                                continue
                            lang_code = str(item.get("lang") or "eng").lower()[:5]
                            prio, friendly_name = PRIORITY_SUBTITLE_LANGS.get(
                                lang_code,
                                (50, lang_code.upper()),
                            )
                            count_for_lang = seen_langs.get(friendly_name, 0)
                            if count_for_lang >= 2:
                                continue
                            seen_langs[friendly_name] = count_for_lang + 1
                            label = friendly_name if count_for_lang == 0 else f"{friendly_name} (Track 2)"
                            tracks.append(
                                {
                                    "id": str(item.get("id") or f"{lang_code}_{count_for_lang}"),
                                    "lang": lang_code,
                                    "label": label,
                                    "hi": False,
                                    "priority": prio,
                                    "vtt_url": f"/api/subtitles/vtt?src={urllib.parse.quote(sub_url, safe='')}",
                                    "cues_url": f"/api/subtitles/vtt?src={urllib.parse.quote(sub_url, safe='')}&format=json",
                                }
                            )
    except Exception as exc:
        print(f"[subtitles] lookup for {media_type}/{tmdb_id} failed: {exc}")

    tracks.sort(key=lambda t: (t["priority"], t["label"]))
    for t in tracks:
        t.pop("priority", None)

    with _subtitle_cache_lock:
        if len(_subtitle_cache) > 400:
            for k in list(_subtitle_cache.keys())[:100]:
                _subtitle_cache.pop(k, None)
        _subtitle_cache[cache_key] = (tracks, now + 1800)

    return jsonify({"tracks": tracks})


@app.route("/api/subtitles/vtt")
@login_required
def api_subtitle_vtt():
    src = (request.args.get("src") or "").strip()
    out_format = (request.args.get("format") or "vtt").lower()
    if not src.startswith("https://") or len(src) > 1000:
        return jsonify({"error": "Invalid subtitle source"}), 400

    parsed = urllib.parse.urlparse(src)
    host = (parsed.hostname or "").lower()
    if not SAFE_SUBTITLE_HOST_RE.fullmatch(host):
        return jsonify({"error": "Untrusted subtitle host"}), 400

    cache_key = f"vtt:{src}"
    now = time.time()
    vtt_text = None
    with _subtitle_cache_lock:
        cached = _subtitle_cache.get(cache_key)
        if cached and cached[1] > now:
            vtt_text = cached[0]

    if vtt_text is None:
        try:
            req = urllib.request.Request(
                src,
                headers={"User-Agent": "LumiereCinema/2.0"},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                raw_bytes = resp.read(2_500_000)
            try:
                raw_text = raw_bytes.decode("utf-8")
            except UnicodeDecodeError:
                raw_text = raw_bytes.decode("latin-1", errors="replace")
            vtt_text = _srt_to_webvtt(raw_text)
            with _subtitle_cache_lock:
                _subtitle_cache[cache_key] = (vtt_text, now + 3600)
        except Exception as exc:
            print(f"[subtitles] vtt fetch failed: {exc}")
            vtt_text = "WEBVTT\n\n"

    if out_format == "json":
        cues = _parse_vtt_cues(vtt_text)
        return jsonify({"cues": cues, "count": len(cues)})

    resp = app.response_class(vtt_text, status=200, mimetype="text/vtt")
    resp.headers["Content-Type"] = "text/vtt; charset=utf-8"
    return resp


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"[*] Starting {SITE_NAME} at http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
