from __future__ import annotations

import os
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]


class Settings:
    database_url: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{_REPO_ROOT / 'data' / 'arkon.db'}",
    )
    jwt_secret: str = os.getenv("JWT_SECRET", "change-me-in-production-use-long-random")
    jwt_algorithm: str = "HS256"
    jwt_exp_hours: int = int(os.getenv("JWT_EXP_HOURS", "168"))
    cors_origins: list[str] = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    artifacts_dir: str | None = os.getenv("ARKON_ARTIFACTS_DIR")


settings = Settings()
