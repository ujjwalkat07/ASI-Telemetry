import logging
import time
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse

from auth.dependencies import get_current_user
from auth.oauth_service import (
    create_agent_oauth_session,
    exchange_agent_oauth_session,
    get_oauth_session,
    handle_google_oauth_callback,
    logout_session,
    refresh_application_tokens,
)
from auth.templates import (
    render_callback_page,
    render_connect_page,
    render_error_page,
)
from auth.schemas import (
    AuthResponse,
    LoginRequest,
    LogoutRequest,
    OAuthHandoffExchangeRequest,
    OAuthInitRequest,
    OAuthInitResponse,
    RefreshTokenRequest,
    SignupRequest,
    TokenResponse,
    UpdateProfileRequest,
    UserResponse,
)
from auth.service import login, signup, update_profile

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# ---------------------------------------------------------------------------
# Traditional Email / Password Endpoints
# ---------------------------------------------------------------------------

@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup_endpoint(payload: SignupRequest):
    """Create a user account and return an access token."""
    return signup(payload)


@router.post("/login", response_model=AuthResponse)
def login_endpoint(payload: LoginRequest):
    """Verify credentials and return an access token."""
    return login(payload)


@router.get("/me", response_model=UserResponse)
def current_user_endpoint(current_user: UserResponse = Depends(get_current_user)):
    """Return the account associated with the supplied Bearer token."""
    return current_user


@router.put("/profile", response_model=UserResponse)
@router.patch("/profile", response_model=UserResponse)
@router.put("/me", response_model=UserResponse)
def update_profile_endpoint(
    payload: UpdateProfileRequest,
    current_user: UserResponse = Depends(get_current_user),
):
    """Updates the authenticated user's display name and/or password."""
    return update_profile(current_user.id, payload)


# ---------------------------------------------------------------------------
# Google OAuth 2.0 & Agent Handoff Endpoints
# ---------------------------------------------------------------------------

@router.post("/oauth/agent-init", response_model=OAuthInitResponse)
def oauth_agent_init_endpoint(payload: OAuthInitRequest):
    """
    Starts Google OAuth flow for an agent conversation.
    Generates a secure PKCE code verifier, challenge, state, and browser authorization URL.
    """
    return create_agent_oauth_session(
        sender_address=payload.sender_address,
        redirect_uri=payload.redirect_uri,
    )


logger = logging.getLogger("backend.routes.auth")


@router.get("/connect", response_class=HTMLResponse)
def connect_portal_endpoint(session_id: Optional[str] = Query(None)):
    """
    Renders the modern ASI-Telemetry Account Connection Portal.
    Validates the agent session and provides a seamless 1-click Google sign-in UI.
    """
    if not session_id:
        return HTMLResponse(
            content=render_error_page(
                title="Invalid Connection Link",
                detail="No session ID was provided. Please use the connection link provided in your agent chat.",
                error_code="ERR_MISSING_SESSION",
            ),
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    session = get_oauth_session(session_id)
    if not session:
        return HTMLResponse(
            content=render_error_page(
                title="Session Expired or Not Found",
                detail="This authorization session has expired or is invalid. Please request a new link by typing 'connect my account' in chat.",
                error_code="ERR_SESSION_EXPIRED",
            ),
            status_code=status.HTTP_404_NOT_FOUND,
        )

    if session.get("status") != "pending":
        return HTMLResponse(
            content=render_error_page(
                title="Session Already Completed",
                detail="This authorization session has already been completed or exchanged. Please start a new session if you wish to reconnect.",
                error_code="ERR_SESSION_USED",
            ),
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    now = time.time()
    remaining = max(0, int(session.get("expires_at", now) - now))

    return HTMLResponse(
        content=render_connect_page(
            session_id=session_id,
            sender_address=session.get("sender_address", ""),
            auth_url=session.get("auth_url", ""),
            expires_in=remaining,
        ),
        status_code=status.HTTP_200_OK,
    )


@router.get("/oauth/callback", response_class=HTMLResponse)
async def oauth_callback_endpoint(
    request: Request,
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
):
    """
    Handles Google OAuth callback.
    Validates state, exchanges code for Google tokens, verifies OpenID Connect identity,
    and renders a beautiful confirmation page with 1-click code copying.
    """
    try:
        result = await handle_google_oauth_callback(code=code or "", state=state or "", error=error)
    except HTTPException as exc:
        logger.warning("OAuth callback rejected: %s", exc.detail)
        return HTMLResponse(
            content=render_error_page(
                title="Authorization Failed",
                detail=str(exc.detail),
                error_code=f"HTTP_{exc.status_code}",
            ),
            status_code=exc.status_code,
        )
    except Exception as exc:
        logger.error("Unhandled error during OAuth callback: %s", exc)
        return HTMLResponse(
            content=render_error_page(
                title="Authorization Error",
                detail="An unexpected error occurred while completing authentication with Google. Please try again.",
                error_code="ERR_INTERNAL_AUTH",
            ),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    user = result.get("user", {})
    handoff_code = result.get("handoff_code", "")
    email = user.get("email", "")
    name = user.get("name", "")

    return HTMLResponse(
        content=render_callback_page(
            handoff_code=handoff_code,
            email=email,
            name=name,
        ),
        status_code=status.HTTP_200_OK,
    )


@router.post("/oauth/agent-exchange", response_model=TokenResponse)
def oauth_agent_exchange_endpoint(payload: OAuthHandoffExchangeRequest):
    """
    Completes agent session handoff.
    Exchanges session_id or single-use handoff code for ASI-Telemetry access & refresh tokens.
    """
    return exchange_agent_oauth_session(
        session_id=payload.session_id,
        handoff_code=payload.handoff_code,
        sender_address=payload.sender_address,
    )


# ---------------------------------------------------------------------------
# Token Lifecycle & Session Management
# ---------------------------------------------------------------------------

@router.post("/refresh", response_model=TokenResponse)
def refresh_tokens_endpoint(payload: RefreshTokenRequest):
    """
    Refreshes the application access token (15-min lifetime) with Refresh Token Rotation.
    Detects reuse and revokes token families accordingly.
    """
    return refresh_application_tokens(refresh_token=payload.refresh_token)


@router.post("/logout")
def logout_endpoint(
    payload: Optional[LogoutRequest] = None,
    current_user: Optional[UserResponse] = Depends(get_current_user),
):
    """Revokes the active refresh token session or user sessions."""
    rf_token = payload.refresh_token if payload else None
    user_id = current_user.id if current_user else None
    return logout_session(refresh_token=rf_token, user_id=user_id)


# ---------------------------------------------------------------------------
# Sandbox / Local Testing Helper
# ---------------------------------------------------------------------------

@router.get("/oauth/mock")
async def oauth_mock_endpoint(session_id: str, state: str):
    """Sandbox endpoint for testing Google OAuth redirect when client credentials are in mock mode."""
    return await oauth_callback_endpoint(
        request=None,
        code=f"test_code_{session_id[:8]}",
        state=state,
    )
