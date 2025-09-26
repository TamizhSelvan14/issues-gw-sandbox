### Coded by - Soham Jain - SJSUID- 019139796 ###
# src/config.py
import os
from pydantic import BaseModel, ValidationError
from dotenv import load_dotenv

# Load .env automatically in development
load_dotenv()

class Settings(BaseModel):
    GITHUB_TOKEN: str
    GITHUB_OWNER: str
    GITHUB_REPO: str
    WEBHOOK_SECRET: str
    PORT: int = 8080

def get_settings() -> Settings:
    try:
        return Settings(
            GITHUB_TOKEN=os.environ["GITHUB_TOKEN"],
            GITHUB_OWNER=os.environ["GITHUB_OWNER"],
            GITHUB_REPO=os.environ["GITHUB_REPO"],
            WEBHOOK_SECRET=os.environ["WEBHOOK_SECRET"],
            PORT=int(os.environ.get("PORT", "8080")),
        )
    except KeyError as e:
        missing = e.args[0]
        raise RuntimeError(
            f"Missing required env var: {missing}. "
            "Open your .env and fill it in (GITHUB_TOKEN/OWNER/REPO/WEBHOOK_SECRET/PORT)."
        ) from e
    except ValidationError as e:
        raise RuntimeError(f"Invalid configuration: {e}") from e
