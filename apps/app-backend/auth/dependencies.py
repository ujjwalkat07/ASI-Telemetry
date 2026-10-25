from typing import Optional
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from auth.security import decode_access_token
from auth.service import find_user_by_id
from auth.api_keys import resolve_api_key

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired access token. Please log in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise credentials_error

    token = credentials.credentials.strip()

    # If an API key is passed as the Bearer token (asi_live_...)
    if token.startswith("asi_"):
        user_id = resolve_api_key(token)
        if not user_id:
            raise credentials_error
        user = find_user_by_id(user_id)
        if not user:
            raise credentials_error
        return user

    try:
        payload = decode_access_token(token)
        if payload.get("type") != "access":
            raise credentials_error
        subject = payload.get("sub")
        if not subject or not str(subject).strip():
            raise credentials_error
        user = find_user_by_id(str(subject))
        if user is None:
            raise credentials_error
        return user
    except HTTPException:
        raise
    except Exception:
        raise credentials_error


def resolve_request_user_id(request: Request, body_dict: Optional[dict] = None) -> Optional[str]:
    """
    Extracts the user_id associated with a request by inspecting:
    1. 'x-api-key' or 'asi-api-key' headers
    2. 'Authorization: Bearer <jwt_or_api_key>'
    3. Query parameter ?api_key=... or ?user_id=...
    4. Optional body dictionary 'api_key' or 'user_id'
    Returns None if unauthenticated.
    """
    # 1. Custom API Key headers
    raw_api_key = (
        request.headers.get("x-api-key")
        or request.headers.get("asi-api-key")
        or request.headers.get("api-key")
    )
    if raw_api_key:
        uid = resolve_api_key(raw_api_key)
        if uid:
            return uid

    # 2. Authorization header
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header[7:].strip()
        if token.startswith("asi_"):
            uid = resolve_api_key(token)
            if uid:
                return uid
        else:
            payload = decode_access_token(token)
            if not payload:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Session expired or invalid access token. Please log in again.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            sub = payload.get("sub")
            if sub:
                return str(sub)

    # 3. Query parameters
    param_key = request.query_params.get("api_key")
    if param_key:
        uid = resolve_api_key(param_key)
        if uid:
            return uid

    param_uid = request.query_params.get("user_id")
    if param_uid:
        return str(param_uid).strip()

    # 4. Body dictionary fallback
    if body_dict and isinstance(body_dict, dict):
        if body_dict.get("api_key"):
            uid = resolve_api_key(body_dict["api_key"])
            if uid:
                return uid
        if body_dict.get("user_id"):
            return str(body_dict["user_id"]).strip()

    return None
