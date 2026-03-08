import logging
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


# --------------------------------------------------
# Logging
# --------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("research_paper_assistant")


# --------------------------------------------------
# Configuration
# --------------------------------------------------

@dataclass(frozen=True)
class Settings:
    discord_token: str
    discord_guild_id: int

    @classmethod
    def from_env(cls) -> "Settings":
        token = os.getenv("DISCORD_TOKEN")
        guild_id_raw = os.getenv("DISCORD_GUILD_ID")

        if not token:
            raise ValueError("Missing required environment variable: DISCORD_TOKEN")

        if not guild_id_raw:
            raise ValueError("Missing required environment variable: DISCORD_GUILD_ID")

        try:
            guild_id = int(guild_id_raw)
        except ValueError as exc:
            raise ValueError("DISCORD_GUILD_ID must be an integer") from exc

        return cls(discord_token=token, discord_guild_id=guild_id)


settings = Settings.from_env()
