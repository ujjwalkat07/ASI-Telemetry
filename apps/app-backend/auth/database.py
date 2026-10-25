import logging
import secrets
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from config.database import db_connection

logger = logging.getLogger("backend.auth.database")

# Thread-safe lock for in-memory fallbacks
_db_lock = threading.Lock()

# In-memory fallback if ClickHouse is temporarily offline
_memory_users: Dict[str, Dict[str, Any]] = {}
_memory_refresh_tokens: Dict[str, Dict[str, Any]] = {}
_memory_oauth_sessions: Dict[str, Dict[str, Any]] = {}
_memory_github_integrations: Dict[str, Dict[str, Any]] = {}


def initialize_auth_database() -> None:
    """Initializes the users, refresh_tokens, oauth_sessions, and user_github_integrations tables in ClickHouse."""
    if not db_connection.is_connected or not db_connection.client:
        logger.warning("ClickHouse not connected during auth init; in-memory auth fallback active.")
        return

    create_table_sql = """
    CREATE TABLE IF NOT EXISTS users (
        id String,
        name String,
        email String,
        password_hash String,
        created_at DateTime64(3, 'UTC')
    ) ENGINE = MergeTree()
    ORDER BY (email, id);
    """
    create_tokens_sql = """
    CREATE TABLE IF NOT EXISTS refresh_tokens (
        id String,
        user_id String,
        token_hash String,
        family_id String,
        created_at DateTime64(3, 'UTC'),
        expires_at DateTime64(3, 'UTC'),
        revoked_at Nullable(DateTime64(3, 'UTC')),
        replaced_by_hash Nullable(String)
    ) ENGINE = MergeTree()
    ORDER BY (token_hash, user_id);
    """
    create_oauth_sessions_sql = """
    CREATE TABLE IF NOT EXISTS oauth_sessions (
        session_id String,
        sender_address String,
        state_hash String,
        code_verifier String,
        redirect_uri String,
        created_at DateTime64(3, 'UTC'),
        expires_at DateTime64(3, 'UTC'),
        status String,
        handoff_code String,
        handoff_code_hash String,
        user_id String,
        access_token String,
        refresh_token String,
        updated_at DateTime64(3, 'UTC')
    ) ENGINE = ReplacingMergeTree(updated_at)
    ORDER BY (session_id);
    """
    create_github_integrations_sql = """
    CREATE TABLE IF NOT EXISTS user_github_integrations (
        user_id String,
        github_username String,
        access_token String,
        default_repository String,
        created_at DateTime64(3, 'UTC'),
        updated_at DateTime64(3, 'UTC')
    ) ENGINE = ReplacingMergeTree(updated_at)
    ORDER BY (user_id);
    """
    try:
        db_connection.safe_command(create_table_sql)
        db_connection.safe_command(create_tokens_sql)
        db_connection.safe_command(create_oauth_sessions_sql)
        db_connection.safe_command(create_github_integrations_sql)
        logger.info("ClickHouse auth and user_github_integrations tables initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize ClickHouse auth tables: {e}")



def email_exists(email: str) -> bool:
    """Checks whether an account with the given email already exists."""
    clean_email = email.strip().lower()
    if db_connection.is_connected and db_connection.client:
        try:
            res = db_connection.safe_query(
                "SELECT count(*) FROM users WHERE lower(email) = %(email)s",
                parameters={"email": clean_email},
            )
            return bool(res.result_rows and res.result_rows[0][0] > 0)
        except Exception as e:
            logger.warning(f"ClickHouse query error in email_exists: {e}")

    # Fallback to in-memory store
    return any(u["email"].lower() == clean_email for u in _memory_users.values())


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Retrieves a user record by email address."""
    clean_email = email.strip().lower()
    if db_connection.is_connected and db_connection.client:
        try:
            res = db_connection.safe_query(
                "SELECT id, name, email, password_hash, created_at FROM users WHERE lower(email) = %(email)s LIMIT 1",
                parameters={"email": clean_email},
            )
            if res.result_rows:
                row = res.result_rows[0]
                created_at = row[4].isoformat() if hasattr(row[4], "isoformat") else str(row[4])
                return {
                    "id": str(row[0]),
                    "name": str(row[1]),
                    "email": str(row[2]),
                    "password_hash": str(row[3]),
                    "created_at": created_at,
                }
        except Exception as e:
            logger.warning(f"ClickHouse query error in get_user_by_email: {e}")

    # Fallback to in-memory store
    for u in _memory_users.values():
        if u["email"].lower() == clean_email:
            return dict(u)
    return None


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves a user record by ID."""
    clean_id = str(user_id)
    if db_connection.is_connected and db_connection.client:
        try:
            res = db_connection.safe_query(
                "SELECT id, name, email, password_hash, created_at FROM users WHERE id = %(id)s LIMIT 1",
                parameters={"id": clean_id},
            )
            if res.result_rows:
                row = res.result_rows[0]
                created_at = row[4].isoformat() if hasattr(row[4], "isoformat") else str(row[4])
                return {
                    "id": str(row[0]),
                    "name": str(row[1]),
                    "email": str(row[2]),
                    "password_hash": str(row[3]),
                    "created_at": created_at,
                }
        except Exception as e:
            logger.warning(f"ClickHouse query error in get_user_by_id: {e}")

    # Fallback to in-memory store
    if clean_id in _memory_users:
        return dict(_memory_users[clean_id])
    return None


def insert_user(user_id: str, name: str, email: str, password_hash: str, created_at: Optional[datetime] = None) -> None:
    """Inserts a new user record into ClickHouse or memory fallback."""
    clean_id = str(user_id)
    clean_email = email.strip().lower()
    dt = created_at if isinstance(created_at, datetime) else datetime.now(timezone.utc)

    if db_connection.is_connected and db_connection.client:
        try:
            db_connection.safe_insert(
                "users",
                [[clean_id, name, clean_email, password_hash, dt]],
                column_names=["id", "name", "email", "password_hash", "created_at"],
            )
            return
        except Exception as e:
            logger.warning(f"ClickHouse insert error in insert_user: {e}")

    # Fallback to in-memory store
    _memory_users[clean_id] = {
        "id": clean_id,
        "name": name,
        "email": clean_email,
        "password_hash": password_hash,
        "created_at": dt.isoformat(),
        "google_id": None,
    }


def update_user(
    user_id: str,
    name: Optional[str] = None,
    password_hash: Optional[str] = None,
) -> bool:
    """Updates user name and/or password hash in ClickHouse and memory store."""
    clean_id = str(user_id)
    updated = False

    # 1. Update in-memory store
    with _db_lock:
        if clean_id in _memory_users:
            if name is not None:
                _memory_users[clean_id]["name"] = name
            if password_hash is not None:
                _memory_users[clean_id]["password_hash"] = password_hash
            updated = True

    # 2. Update ClickHouse if connected
    if db_connection.is_connected and db_connection.client:
        try:
            assignments = []
            params: Dict[str, Any] = {"id": clean_id}
            if name is not None:
                assignments.append("name = %(name)s")
                params["name"] = name
            if password_hash is not None:
                assignments.append("password_hash = %(password_hash)s")
                params["password_hash"] = password_hash

            if assignments:
                set_clause = ", ".join(assignments)
                db_connection.safe_command(
                    f"ALTER TABLE users UPDATE {set_clause} WHERE id = %(id)s",
                    parameters=params,
                )
                updated = True
        except Exception as e:
            logger.warning(f"ClickHouse update error in update_user: {e}")

    return updated


# In-memory storage for refresh tokens: token_hash -> record
_tokens_lock = _db_lock


def insert_refresh_token(
    token_id: str,
    user_id: str,
    token_hash: str,
    family_id: str,
    expires_at: datetime,
) -> None:
    """Stores a hashed refresh token in ClickHouse or memory fallback."""
    now = datetime.now(timezone.utc)
    record = {
        "id": str(token_id),
        "user_id": str(user_id),
        "token_hash": str(token_hash),
        "family_id": str(family_id),
        "created_at": now,
        "expires_at": expires_at,
        "revoked_at": None,
        "replaced_by_hash": None,
    }

    with _tokens_lock:
        _memory_refresh_tokens[str(token_hash)] = dict(record)

    if db_connection.is_connected and db_connection.client:
        try:
            db_connection.safe_insert(
                "refresh_tokens",
                [[
                    record["id"],
                    record["user_id"],
                    record["token_hash"],
                    record["family_id"],
                    record["created_at"],
                    record["expires_at"],
                    None,
                    None,
                ]],
                column_names=[
                    "id", "user_id", "token_hash", "family_id",
                    "created_at", "expires_at", "revoked_at", "replaced_by_hash",
                ],
            )
        except Exception as e:
            logger.warning(f"ClickHouse insert error in insert_refresh_token: {e}")


def get_refresh_token_record(token_hash: str) -> Optional[Dict[str, Any]]:
    """Retrieves a refresh token record by its SHA-256 hash."""
    clean_hash = str(token_hash).strip()
    with _tokens_lock:
        if clean_hash in _memory_refresh_tokens:
            return dict(_memory_refresh_tokens[clean_hash])

    if db_connection.is_connected and db_connection.client:
        try:
            res = db_connection.safe_query(
                "SELECT id, user_id, token_hash, family_id, created_at, expires_at, revoked_at, replaced_by_hash "
                "FROM refresh_tokens WHERE token_hash = %(hash)s LIMIT 1",
                parameters={"hash": clean_hash},
            )
            if res.result_rows:
                row = res.result_rows[0]
                rec = {
                    "id": str(row[0]),
                    "user_id": str(row[1]),
                    "token_hash": str(row[2]),
                    "family_id": str(row[3]),
                    "created_at": row[4],
                    "expires_at": row[5],
                    "revoked_at": row[6],
                    "replaced_by_hash": str(row[7]) if row[7] else None,
                }
                with _tokens_lock:
                    _memory_refresh_tokens[clean_hash] = rec
                return rec
        except Exception as e:
            logger.warning(f"ClickHouse query error in get_refresh_token_record: {e}")

    return None


def revoke_refresh_token(token_hash: str, replaced_by_hash: Optional[str] = None) -> bool:
    """Marks an individual refresh token as revoked."""
    clean_hash = str(token_hash).strip()
    now = datetime.now(timezone.utc)
    found = False

    with _tokens_lock:
        if clean_hash in _memory_refresh_tokens:
            _memory_refresh_tokens[clean_hash]["revoked_at"] = now
            if replaced_by_hash:
                _memory_refresh_tokens[clean_hash]["replaced_by_hash"] = str(replaced_by_hash)
            found = True

    return found


def revoke_token_family(family_id: str) -> int:
    """Revokes all refresh tokens belonging to a family (triggered upon token reuse detection)."""
    clean_fam = str(family_id).strip()
    now = datetime.now(timezone.utc)
    count = 0

    with _tokens_lock:
        for rec in _memory_refresh_tokens.values():
            if rec.get("family_id") == clean_fam and not rec.get("revoked_at"):
                rec["revoked_at"] = now
                count += 1

    logger.warning("Revoked %d tokens in family %s due to reuse detection or session revocation", count, clean_fam)
    return count


def revoke_all_user_tokens(user_id: str) -> int:
    """Revokes all active refresh tokens for a user upon global logout."""
    clean_uid = str(user_id).strip()
    now = datetime.now(timezone.utc)
    count = 0

    with _tokens_lock:
        for rec in _memory_refresh_tokens.values():
            if str(rec.get("user_id")) == clean_uid and not rec.get("revoked_at"):
                rec["revoked_at"] = now
                count += 1

    return count


def get_or_create_google_user(google_id: str, email: str, name: str) -> Dict[str, Any]:
    """
    Finds or creates a user account securely verified by Google OpenID Connect.
    Prevents account collision while honoring existing user records.
    """
    clean_email = email.strip().lower()
    existing_user = get_user_by_email(clean_email)
    now = datetime.now(timezone.utc)

    if existing_user:
        # User already exists; update google_id linkage in memory
        existing_user["google_id"] = google_id
        if clean_email in _memory_users:
            _memory_users[clean_email]["google_id"] = google_id
        return existing_user

    # Create new OAuth user with unguessable random password hash
    import secrets
    from auth.security import hash_password
    import uuid

    new_id = str(uuid.uuid4())
    random_pw = secrets.token_hex(32)
    pw_hash = hash_password(random_pw)

    insert_user(
        user_id=new_id,
        name=name or clean_email.split("@")[0],
        email=clean_email,
        password_hash=pw_hash,
        created_at=now,
    )

    created = {
        "id": new_id,
        "name": name or clean_email.split("@")[0],
        "email": clean_email,
        "password_hash": pw_hash,
        "created_at": now.isoformat(),
        "google_id": google_id,
    }
    with _tokens_lock:
        _memory_users[new_id] = created
    return created


def insert_or_update_oauth_session(
    session_id: str,
    sender_address: str,
    state_hash: str,
    code_verifier: str,
    redirect_uri: str,
    expires_at_timestamp: float,
    status: str,
    handoff_code: Optional[str] = None,
    handoff_code_hash: Optional[str] = None,
    user_id: Optional[str] = None,
    access_token: Optional[str] = None,
    refresh_token: Optional[str] = None,
) -> None:
    """Persists or updates an agent OAuth session in ClickHouse and memory."""
    now = datetime.now(timezone.utc)
    expires_dt = datetime.fromtimestamp(expires_at_timestamp, tz=timezone.utc)

    rec = {
        "session_id": str(session_id),
        "sender_address": str(sender_address or ""),
        "state_hash": str(state_hash or ""),
        "code_verifier": str(code_verifier or ""),
        "redirect_uri": str(redirect_uri or ""),
        "created_at": now,
        "expires_at": expires_at_timestamp,
        "status": str(status),
        "handoff_code": str(handoff_code or "") if handoff_code else None,
        "handoff_code_hash": str(handoff_code_hash or "") if handoff_code_hash else None,
        "user_id": str(user_id or "") if user_id else None,
        "access_token": str(access_token or "") if access_token else None,
        "refresh_token": str(refresh_token or "") if refresh_token else None,
        "updated_at": now,
    }

    with _db_lock:
        _memory_oauth_sessions[str(session_id)] = rec

    if db_connection.is_connected and db_connection.client:
        try:
            db_connection.safe_insert(
                "oauth_sessions",
                [[
                    str(session_id),
                    str(sender_address or ""),
                    str(state_hash or ""),
                    str(code_verifier or ""),
                    str(redirect_uri or ""),
                    now,
                    expires_dt,
                    str(status),
                    str(handoff_code or ""),
                    str(handoff_code_hash or ""),
                    str(user_id or ""),
                    str(access_token or ""),
                    str(refresh_token or ""),
                    now,
                ]],
                column_names=[
                    "session_id", "sender_address", "state_hash", "code_verifier",
                    "redirect_uri", "created_at", "expires_at", "status",
                    "handoff_code", "handoff_code_hash", "user_id", "access_token",
                    "refresh_token", "updated_at",
                ],
            )
        except Exception as e:
            logger.warning(f"ClickHouse insert error in insert_or_update_oauth_session: {e}")


def _parse_oauth_session_row(row: list) -> Dict[str, Any]:
    expires_at = row[6]
    if hasattr(expires_at, "timestamp"):
        expires_timestamp = expires_at.timestamp()
    elif isinstance(expires_at, (int, float)):
        expires_timestamp = float(expires_at)
    else:
        expires_timestamp = time.time() + 600

    rec = {
        "session_id": str(row[0]),
        "sender_address": str(row[1]),
        "state_hash": str(row[2]),
        "code_verifier": str(row[3]),
        "redirect_uri": str(row[4]),
        "created_at": row[5],
        "expires_at": expires_timestamp,
        "status": str(row[7]),
        "handoff_code": str(row[8]) if row[8] else None,
        "handoff_code_hash": str(row[9]) if row[9] else None,
        "user_id": str(row[10]) if row[10] else None,
        "access_token": str(row[11]) if row[11] else None,
        "refresh_token": str(row[12]) if row[12] else None,
    }
    with _db_lock:
        _memory_oauth_sessions[rec["session_id"]] = rec
    return rec


def get_oauth_session(
    session_id: Optional[str] = None,
    state_hash: Optional[str] = None,
    handoff_code_hash: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Retrieves an active OAuth session by session_id, state_hash, or handoff_code_hash."""
    # 1. In-memory check first
    with _db_lock:
        if session_id and session_id in _memory_oauth_sessions:
            return dict(_memory_oauth_sessions[session_id])
        if state_hash:
            for s in _memory_oauth_sessions.values():
                if secrets.compare_digest(s.get("state_hash", ""), state_hash):
                    return dict(s)
        if handoff_code_hash:
            for s in _memory_oauth_sessions.values():
                if secrets.compare_digest(s.get("handoff_code_hash") or "", handoff_code_hash):
                    return dict(s)

    # 2. ClickHouse check
    if db_connection.is_connected and db_connection.client:
        query = ""
        params = {}
        if session_id:
            query = (
                "SELECT session_id, sender_address, state_hash, code_verifier, redirect_uri, "
                "created_at, expires_at, status, handoff_code, handoff_code_hash, user_id, "
                "access_token, refresh_token, updated_at FROM oauth_sessions "
                "WHERE session_id = %(val)s ORDER BY updated_at DESC LIMIT 1"
            )
            params = {"val": str(session_id)}
        elif handoff_code_hash:
            query = (
                "SELECT session_id, sender_address, state_hash, code_verifier, redirect_uri, "
                "created_at, expires_at, status, handoff_code, handoff_code_hash, user_id, "
                "access_token, refresh_token, updated_at FROM oauth_sessions "
                "WHERE handoff_code_hash = %(val)s ORDER BY updated_at DESC LIMIT 1"
            )
            params = {"val": str(handoff_code_hash)}
        elif state_hash:
            query = (
                "SELECT session_id, sender_address, state_hash, code_verifier, redirect_uri, "
                "created_at, expires_at, status, handoff_code, handoff_code_hash, user_id, "
                "access_token, refresh_token, updated_at FROM oauth_sessions "
                "WHERE state_hash = %(val)s ORDER BY updated_at DESC LIMIT 1"
            )
            params = {"val": str(state_hash)}

        if query:
            try:
                res = db_connection.safe_query(query, parameters=params)
                if res.result_rows:
                    return _parse_oauth_session_row(res.result_rows[0])
            except Exception as e:
                logger.warning(f"ClickHouse query error in get_oauth_session: {e}")

    return None


def save_user_github_integration(
    user_id: str,
    access_token: str,
    default_repository: str,
    github_username: str = "",
) -> Dict[str, Any]:
    """Saves or updates a user's GitHub integration (token and default repo)."""
    clean_uid = str(user_id).strip()
    clean_repo = default_repository.strip()
    clean_token = access_token.strip()
    clean_user = github_username.strip()
    now = datetime.now(timezone.utc)

    record = {
        "user_id": clean_uid,
        "github_username": clean_user,
        "access_token": clean_token,
        "default_repository": clean_repo,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }

    if db_connection.is_connected and db_connection.client:
        try:
            db_connection.safe_command(
                "INSERT INTO user_github_integrations (user_id, github_username, access_token, default_repository, created_at, updated_at) "
                "VALUES (%(uid)s, %(user)s, %(token)s, %(repo)s, %(created)s, %(updated)s)",
                parameters={
                    "uid": clean_uid,
                    "user": clean_user,
                    "token": clean_token,
                    "repo": clean_repo,
                    "created": now,
                    "updated": now,
                },
            )
        except Exception as e:
            logger.warning(f"ClickHouse insert error in save_user_github_integration: {e}")

    with _db_lock:
        _memory_github_integrations[clean_uid] = record

    return record


def get_user_github_integration(user_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves a user's GitHub integration details."""
    clean_uid = str(user_id).strip()

    with _db_lock:
        if clean_uid in _memory_github_integrations:
            return dict(_memory_github_integrations[clean_uid])

    if db_connection.is_connected and db_connection.client:
        try:
            res = db_connection.safe_query(
                "SELECT user_id, github_username, access_token, default_repository, created_at, updated_at "
                "FROM user_github_integrations WHERE user_id = %(uid)s ORDER BY updated_at DESC LIMIT 1",
                parameters={"uid": clean_uid},
            )
            if res.result_rows:
                row = res.result_rows[0]
                rec = {
                    "user_id": str(row[0]),
                    "github_username": str(row[1]),
                    "access_token": str(row[2]),
                    "default_repository": str(row[3]),
                    "created_at": row[4].isoformat() if hasattr(row[4], "isoformat") else str(row[4]),
                    "updated_at": row[5].isoformat() if hasattr(row[5], "isoformat") else str(row[5]),
                }
                with _db_lock:
                    _memory_github_integrations[clean_uid] = rec
                return rec
        except Exception as e:
            logger.warning(f"ClickHouse query error in get_user_github_integration: {e}")

    return None


def delete_user_github_integration(user_id: str) -> bool:
    """Removes a user's GitHub integration."""
    clean_uid = str(user_id).strip()
    with _db_lock:
        existed = clean_uid in _memory_github_integrations
        _memory_github_integrations.pop(clean_uid, None)

    if db_connection.is_connected and db_connection.client:
        try:
            db_connection.safe_command(
                "ALTER TABLE user_github_integrations DELETE WHERE user_id = %(uid)s",
                parameters={"uid": clean_uid},
            )
        except Exception as e:
            logger.warning(f"ClickHouse delete error in delete_user_github_integration: {e}")

    return existed

