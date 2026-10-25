from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator



class SignupRequest(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Name must contain at least 2 non-space characters")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=80)
    current_password: Optional[str] = Field(default=None, min_length=1, max_length=128)
    new_password: Optional[str] = Field(default=None, min_length=8, max_length=128)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Name must contain at least 2 non-space characters")
        return value


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: EmailStr
    created_at: Optional[str] = None


class AuthResponse(BaseModel):
    status: str = "success"
    message: str
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user: UserResponse


class CreateApiKeyRequest(BaseModel):
    name: Optional[str] = "Default Key"
    environment: str = Field(default="production")
    permissions: List[str] = Field(default_factory=lambda: ["telemetry:write", "telemetry:read"])
    expires_at: Optional[str] = "90 days"
    rate_limit: Optional[str] = "25,000 req/min"


class ApiKeyResponse(BaseModel):
    id: str
    user_id: str
    name: str
    key_prefix: str
    full_key: Optional[str] = None
    environment: str
    permissions: List[str] = Field(default_factory=list)
    rate_limit: str = "25,000 req/min"
    status: str = "active"
    created_at: str
    last_used_at: Optional[str] = None
    expires_at: Optional[str] = None


class OAuthInitRequest(BaseModel):
    sender_address: str
    redirect_uri: Optional[str] = None


class OAuthInitResponse(BaseModel):
    session_id: str
    state: str
    authorization_url: str
    connect_url: Optional[str] = None
    expires_in_seconds: int
    sender_address: str


class OAuthHandoffExchangeRequest(BaseModel):
    session_id: Optional[str] = None
    handoff_code: Optional[str] = None
    sender_address: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Optional[UserResponse] = None


class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None

