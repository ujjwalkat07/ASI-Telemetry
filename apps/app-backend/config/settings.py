import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from the backend folder
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")


class Settings:
    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8080"))

    # ClickHouse database settings
    CLICKHOUSE_HOST: str = os.getenv("CLICKHOUSE_HOST", "localhost")
    CLICKHOUSE_PORT: int = int(os.getenv("CLICKHOUSE_PORT", "8123"))
    CLICKHOUSE_USER: str = os.getenv("CLICKHOUSE_USER", "default")
    CLICKHOUSE_PASSWORD: str = os.getenv("CLICKHOUSE_PASSWORD", "")
    CLICKHOUSE_DATABASE: str = os.getenv("CLICKHOUSE_DATABASE", "default")
    CLICKHOUSE_SECURE: bool = os.getenv("CLICKHOUSE_SECURE", "false").lower() in ("true", "1")


    # Authentication settings
    AUTH_DATABASE_PATH: str = os.getenv("AUTH_DATABASE_PATH", "./data/auth.db")
    AUTH_SECRET_KEY: str = os.getenv(
        "AUTH_SECRET_KEY",
        "development-only-change-this-secret-before-deploying",
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "43200"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))
    TOKEN_ISSUER: str = os.getenv("TOKEN_ISSUER", "asi-telemetry")
    TOKEN_AUDIENCE: str = os.getenv("TOKEN_AUDIENCE", "asi-telemetry-api")

    # Google OAuth settings
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = os.getenv(
        "GOOGLE_REDIRECT_URI",
        "https://asi-telemetry-backend.vercel.app/api/auth/oauth/callback",
    )
    ALLOWED_REDIRECT_URIS: list[str] = list(
        set(
            [
                uri.strip().rstrip("/")
                for uri in os.getenv(
                    "ALLOWED_REDIRECT_URIS",
                    "https://asi-telemetry-backend.vercel.app/api/auth/oauth/callback,http://localhost:8080/api/auth/oauth/callback,http://127.0.0.1:8080/api/auth/oauth/callback",
                ).split(",")
                if uri.strip()
            ]
            + [
                os.getenv(
                    "GOOGLE_REDIRECT_URI",
                    "https://asi-telemetry-backend.vercel.app/api/auth/oauth/callback",
                ).strip().rstrip("/")
            ]
        )
    )
    FRONTEND_BASE_URL: str = os.getenv("FRONTEND_BASE_URL", "https://asi-telemetry.vercel.app")



settings = Settings()

