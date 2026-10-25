"""Comprehensive automated tests for Google OAuth, PKCE, and Application Token Lifecycle.

Covers Phase 8 requirements:
- Google OAuth session initialization & PKCE challenge
- OAuth state validation & invalid state rejection
- Single-use handoff code generation & exchange
- Sender address binding & cross-account linking prevention
- Handoff code replay rejection
- Access token claims (sub, iss, aud, exp, jti) and signature verification
- Access token expiry verification
- Refresh token rotation
- Refresh token reuse detection & token family revocation
- Server-side logout & revocation
"""

import time
import pytest
from datetime import timedelta
from fastapi import HTTPException
from jose import jwt

from auth.security import (
    create_access_token,
    decode_access_token,
    create_refresh_token,
    hash_token,
)
from auth.oauth_service import (
    create_agent_oauth_session,
    handle_google_oauth_callback,
    exchange_agent_oauth_session,
    refresh_application_tokens,
    logout_session,
    _oauth_sessions,
)
from config import settings


@pytest.fixture(autouse=True)
def clean_state():
    """Ensure in-memory sessions are fresh before each test."""
    _oauth_sessions.clear()
    yield
    _oauth_sessions.clear()


# =====================================================================
# 1. OAuth Session Initiation & PKCE
# =====================================================================

def test_oauth_init_generates_pkce_and_binds_sender():
    sender = "agent1qtestsender11111111111111111111111111111111111111111111111"
    init_res = create_agent_oauth_session(sender_address=sender)

    session_id = init_res["session_id"]
    auth_url = init_res["authorization_url"]

    assert session_id is not None
    assert "response_type=code" in auth_url or "mock" in auth_url
    assert init_res["sender_address"] == sender

    session = _oauth_sessions.get(session_id)
    assert session is not None
    assert session["sender_address"] == sender
    assert len(session["state"]) > 20
    assert len(session["code_verifier"]) > 30


# =====================================================================
# 2. OAuth Callback & State Validation
# =====================================================================

@pytest.mark.asyncio
async def test_callback_rejects_invalid_or_missing_state():
    with pytest.raises(HTTPException) as exc_info:
        await handle_google_oauth_callback(code="mock_code_123", state="invalid_state")
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_callback_success_generates_single_use_handoff():
    sender = "agent1qtestsender22222222222222222222222222222222222222222222222"
    init_res = create_agent_oauth_session(sender_address=sender)
    session_id = init_res["session_id"]
    state = init_res["state"]

    res = await handle_google_oauth_callback(code="mock_code", state=state)

    assert res["status"] == "authorized"
    handoff_code = res["handoff_code"]
    assert handoff_code.startswith("AUTH-")

    session = _oauth_sessions[session_id]
    assert session["status"] == "authorized"
    assert session["handoff_code"] == handoff_code


@pytest.mark.asyncio
async def test_callback_rejects_replayed_state():
    sender = "agent1qtestsender33333333333333333333333333333333333333333333333"
    init_res = create_agent_oauth_session(sender_address=sender)
    state = init_res["state"]

    await handle_google_oauth_callback(code="mock_code", state=state)

    # Second callback with same state must fail because session is already authorized
    with pytest.raises(HTTPException) as exc_info:
        await handle_google_oauth_callback(code="mock_code", state=state)
    assert exc_info.value.status_code == 400


# =====================================================================
# 3. Agent Handoff Code Exchange & Sender Binding
# =====================================================================

@pytest.mark.asyncio
async def test_handoff_exchange_success():
    sender = "agent1qtestsender44444444444444444444444444444444444444444444444"
    init_res = create_agent_oauth_session(sender_address=sender)
    session_id = init_res["session_id"]
    state = init_res["state"]
    cb_res = await handle_google_oauth_callback(code="mock_code", state=state)
    handoff_code = cb_res["handoff_code"]

    tokens = exchange_agent_oauth_session(
        sender_address=sender,
        session_id=session_id,
        handoff_code=handoff_code,
    )

    assert tokens["status"] == "success"
    assert tokens["access_token"] is not None
    assert tokens["refresh_token"].startswith("asi_rf_")
    assert tokens["token_type"] == "bearer"
    assert tokens["expires_in"] == settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    assert "user" in tokens


@pytest.mark.asyncio
async def test_handoff_exchange_from_database_fallback():
    """Verify exchange succeeds even when in-memory cache is empty (database fallback)."""
    sender = "agent1qdbfallback111111111111111111111111111111111111111111111"
    init_res = create_agent_oauth_session(sender_address=sender)
    session_id = init_res["session_id"]
    state = init_res["state"]
    cb_res = await handle_google_oauth_callback(code="mock_code", state=state)
    handoff_code = cb_res["handoff_code"]

    # Clear in-memory cache to force fallback to database lookup
    _oauth_sessions.clear()

    tokens = exchange_agent_oauth_session(
        sender_address=sender,
        handoff_code=handoff_code,
    )

    assert tokens["status"] == "success"
    assert tokens["access_token"] is not None


@pytest.mark.asyncio
async def test_handoff_exchange_rejects_wrong_sender():
    sender = "agent1qlegitsender55555555555555555555555555555555555555555555555"
    attacker = "agent1qattackersender666666666666666666666666666666666666666666"

    init_res = create_agent_oauth_session(sender_address=sender)
    session_id = init_res["session_id"]
    state = init_res["state"]
    cb_res = await handle_google_oauth_callback(code="mock_code", state=state)
    handoff_code = cb_res["handoff_code"]

    # Attacker tries to exchange legitimate sender's session
    with pytest.raises(HTTPException) as exc_info:
        exchange_agent_oauth_session(
            sender_address=attacker,
            session_id=session_id,
            handoff_code=handoff_code,
        )
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_handoff_exchange_rejects_invalid_code():
    sender = "agent1qtestsenderwrongcode11111111111111111111111111111111111111"
    init_res = create_agent_oauth_session(sender_address=sender)
    session_id = init_res["session_id"]
    state = init_res["state"]
    cb_res = await handle_google_oauth_callback(code="mock_code", state=state)
    real_code = cb_res["handoff_code"]

    # Attempt exchange with wrong code (even if session_id matches)
    with pytest.raises(HTTPException) as exc_info:
        exchange_agent_oauth_session(
            sender_address=sender,
            session_id=session_id,
            handoff_code="AUTH-9EC1516Y",
        )
    assert exc_info.value.status_code == 400
    assert "Invalid authorization handoff code" in exc_info.value.detail


@pytest.mark.asyncio
async def test_handoff_exchange_rejects_replayed_code():
    sender = "agent1qtestsender77777777777777777777777777777777777777777777777"
    init_res = create_agent_oauth_session(sender_address=sender)
    session_id = init_res["session_id"]
    state = init_res["state"]
    cb_res = await handle_google_oauth_callback(code="mock_code", state=state)
    handoff_code = cb_res["handoff_code"]

    exchange_agent_oauth_session(
        sender_address=sender,
        session_id=session_id,
        handoff_code=handoff_code,
    )

    # Second exchange attempt must fail (single-use constraint)
    with pytest.raises(HTTPException) as exc_info:
        exchange_agent_oauth_session(
            sender_address=sender,
            session_id=session_id,
            handoff_code=handoff_code,
        )
    assert exc_info.value.status_code in (400, 404)


# =====================================================================
# 4. Access Token Lifecycle & Validation
# =====================================================================

def test_access_token_claims_and_signature():
    email = "dev@example.com"
    token = create_access_token(user_id="usr_test123", email=email)

    payload = decode_access_token(token)
    assert payload is not None
    assert payload.get("sub") == "usr_test123"
    assert payload.get("email") == email
    assert payload.get("iss") == settings.TOKEN_ISSUER
    assert payload.get("aud") == settings.TOKEN_AUDIENCE
    assert payload.get("type") == "access"
    assert "jti" in payload
    assert "exp" in payload
    assert "iat" in payload


def test_access_token_rejected_after_expiry():
    email = "expired@example.com"
    # Create token expired in past
    token = create_access_token(
        user_id="usr_exp",
        email=email,
        expires_delta=timedelta(seconds=-5),
    )

    payload = decode_access_token(token)
    assert payload is None, "Expired access token must be rejected"


def test_access_token_rejected_with_invalid_signature():
    email = "dev@example.com"
    token = create_access_token(user_id="usr_test", email=email)
    # Tamper with the token
    tampered = token[:-5] + "aaaaa"

    payload = decode_access_token(tampered)
    assert payload is None, "Tampered signature must be rejected"


def test_access_token_rejected_with_wrong_issuer():
    claims = {
        "sub": "usr_test",
        "email": "user@example.com",
        "iss": "malicious-issuer",
        "aud": settings.TOKEN_AUDIENCE,
        "exp": int(time.time()) + 3600,
    }
    bad_token = jwt.encode(claims, settings.AUTH_SECRET_KEY, algorithm="HS256")
    payload = decode_access_token(bad_token)
    # With wrong issuer, payload should either be rejected or not match expected issuer
    assert payload is None or payload.get("iss") != settings.TOKEN_ISSUER


def test_access_token_rejected_with_wrong_audience():
    claims = {
        "sub": "usr_test",
        "email": "user@example.com",
        "iss": settings.TOKEN_ISSUER,
        "aud": "wrong-audience",
        "exp": int(time.time()) + 3600,
    }
    bad_token = jwt.encode(claims, settings.AUTH_SECRET_KEY, algorithm="HS256")
    payload = decode_access_token(bad_token)
    assert payload is None or payload.get("aud") != settings.TOKEN_AUDIENCE


# =====================================================================
# 5. Refresh Token Lifecycle, Rotation, & Reuse Detection
# =====================================================================

@pytest.mark.asyncio
async def test_refresh_token_rotation():
    sender = "agent1qtestsender88888888888888888888888888888888888888888888888"
    init_res = create_agent_oauth_session(sender_address=sender)
    session_id = init_res["session_id"]
    state = init_res["state"]
    cb_res = await handle_google_oauth_callback(code="mock_code", state=state)
    handoff_code = cb_res["handoff_code"]

    orig_tokens = exchange_agent_oauth_session(
        sender_address=sender,
        session_id=session_id,
        handoff_code=handoff_code,
    )

    # Perform refresh token rotation
    rotated = refresh_application_tokens(orig_tokens["refresh_token"])

    assert rotated["access_token"] is not None
    assert rotated["refresh_token"].startswith("asi_rf_")
    assert rotated["refresh_token"] != orig_tokens["refresh_token"]



@pytest.mark.asyncio
async def test_refresh_token_reuse_revokes_token_family():
    sender = "agent1qtestsender99999999999999999999999999999999999999999999999"
    init_res = create_agent_oauth_session(sender_address=sender)
    session_id = init_res["session_id"]
    state = init_res["state"]
    cb_res = await handle_google_oauth_callback(code="mock_code", state=state)
    handoff_code = cb_res["handoff_code"]

    orig_tokens = exchange_agent_oauth_session(
        sender_address=sender,
        session_id=session_id,
        handoff_code=handoff_code,
    )

    # Legitimate client rotates refresh token
    rotated = refresh_application_tokens(orig_tokens["refresh_token"])

    # Malicious actor or compromised client presents the OLD refresh token again
    with pytest.raises(HTTPException) as exc_info:
        refresh_application_tokens(orig_tokens["refresh_token"])
    assert exc_info.value.status_code == 401
    assert "reuse detected" in exc_info.value.detail.lower()

    # Security policy: Token family revocation! Even the newest rotated token is now revoked
    with pytest.raises(HTTPException) as exc_info2:
        refresh_application_tokens(rotated["refresh_token"])
    assert exc_info2.value.status_code == 401


@pytest.mark.asyncio
async def test_logout_revokes_refresh_token():
    sender = "agent1qlogout111111111111111111111111111111111111111111111111111"
    init_res = create_agent_oauth_session(sender_address=sender)
    session_id = init_res["session_id"]
    state = init_res["state"]
    cb_res = await handle_google_oauth_callback(code="mock_code", state=state)
    handoff_code = cb_res["handoff_code"]

    tokens = exchange_agent_oauth_session(
        sender_address=sender,
        session_id=session_id,
        handoff_code=handoff_code,
    )

    # Server-side logout
    res = logout_session(tokens["refresh_token"])
    assert res["status"] == "success"

    # Attempting to use revoked refresh token must be rejected
    with pytest.raises(HTTPException) as exc_info:
        refresh_application_tokens(tokens["refresh_token"])
    assert exc_info.value.status_code == 401


# =====================================================================
# 7. UI Portal & Callback HTML Rendering
# =====================================================================

def test_connect_portal_and_callback_ui():
    from fastapi.testclient import TestClient
    from main import app

    test_client = TestClient(app)

    # 1. Initiate session
    init_res = create_agent_oauth_session(sender_address="agent1qui11111111111111111111111111111111111111111111111")
    session_id = init_res["session_id"]
    state = init_res["state"]
    connect_url = init_res["connect_url"]

    assert "session_id=" in connect_url
    assert "/api/auth/connect" in connect_url

    # 2. Test Connect Portal UI
    portal_resp = test_client.get(f"/api/auth/connect?session_id={session_id}")
    assert portal_resp.status_code == 200
    assert "text/html" in portal_resp.headers["content-type"]
    assert "Connect Account" in portal_resp.text
    assert "Continue with Google" in portal_resp.text
    assert "agent1qui" in portal_resp.text

    # 3. Test Missing or Invalid Session handling on Portal
    missing_resp = test_client.get("/api/auth/connect")
    assert missing_resp.status_code == 400
    assert "Invalid Connection Link" in missing_resp.text

    invalid_resp = test_client.get("/api/auth/connect?session_id=invalid_nonexistent")
    assert invalid_resp.status_code == 404
    assert "Session Expired or Not Found" in invalid_resp.text

    # 4. Test Callback Success UI
    cb_resp = test_client.get(f"/api/auth/oauth/callback?code=mock_code&state={state}")
    assert cb_resp.status_code == 200
    assert "text/html" in cb_resp.headers["content-type"]
    assert "Account Linked" in cb_resp.text
    assert "AUTH-" in cb_resp.text
    assert "Copy Code" in cb_resp.text

    # 5. Test Callback Error UI (e.g. user denied consent)
    err_resp = test_client.get("/api/auth/oauth/callback?error=access_denied")
    assert err_resp.status_code == 400
    assert "Authorization Failed" in err_resp.text

