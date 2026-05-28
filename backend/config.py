import os
from pathlib import Path
from dataclasses import dataclass

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR.parent / ".env", override=False)


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "NetPulse")
    app_port: int = int(os.getenv("APP_PORT", "5001"))
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret-change-me")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///netpulse.db")
    monitor_tick_seconds: int = int(os.getenv("MONITOR_TICK_SECONDS", "5"))
    degraded_alert_persist_seconds: int = int(
        os.getenv("DEGRADED_ALERT_PERSIST_SECONDS", "60")
    )
    ping_count: int = int(os.getenv("PING_COUNT", "5"))
    ping_timeout_seconds: float = float(os.getenv("PING_TIMEOUT_SECONDS", "1.5"))
    incident_alert_cooldown_seconds: int = int(
        os.getenv("INCIDENT_ALERT_COOLDOWN_SECONDS", "300")
    )
    telegram_bot_token: str = os.getenv("BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("CHAT_ID", "")


settings = Settings()
