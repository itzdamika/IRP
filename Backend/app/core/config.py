from __future__ import annotations

import os
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]

class Settings:
    database_url: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{_REPO_ROOT / 'data' / 'arkon.db'}",
    )
    jwt_secret: str = os.getenv("JWT_SECRET", "be674940d90d3e480b07ec61bcf421d9ea810a1640c26a4c8fec0ef6cba886fa")
    jwt_algorithm: str = "HS256"
    jwt_exp_hours: int = int(os.getenv("JWT_EXP_HOURS", "168"))
    cors_origins: list[str] = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,https://arkon-three.vercel.app/",
    ).split(",")
    artifacts_dir: str | None = os.getenv("ARKON_ARTIFACTS_DIR")


settings = Settings()
