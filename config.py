import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    token: str = os.getenv("DISCORD_TOKEN", "")
    guild_id: int | None = int(os.environ["GUILD_ID"]) if os.getenv("GUILD_ID") else None
    snapshot_hour: int = int(os.getenv("SNAPSHOT_HOUR", "6"))
    snapshot_minute: int = int(os.getenv("SNAPSHOT_MINUTE", "0"))
    timezone: str = os.getenv("TIMEZONE", "Europe/Warsaw")
    report_channel_id: int | None = int(os.environ["REPORT_CHANNEL_ID"]) if os.getenv("REPORT_CHANNEL_ID") else None

settings = Settings()
