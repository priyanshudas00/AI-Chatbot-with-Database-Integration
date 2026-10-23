import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=PROJECT_ROOT / ".env", override=True)


@dataclass(frozen=True)
class Settings:
    openrouter_api_key: str
    openrouter_base_url: str
    openrouter_chat_model: str
    openrouter_embedding_model: str
    mysql_host: str
    mysql_port: int
    mysql_user: str
    mysql_password: str
    mysql_database: str
    mysql_ssl_mode: str
    mysql_ssl_ca: str

    @staticmethod
    def from_env() -> "Settings":
        return Settings(
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY", ""),
            openrouter_base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            openrouter_chat_model=os.getenv("OPENROUTER_CHAT_MODEL", "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"),
            openrouter_embedding_model=os.getenv("OPENROUTER_EMBEDDING_MODEL", "nvidia/nemotron-3.5-embed-8b:free"),
            mysql_host=os.getenv("MYSQL_HOST", "localhost"),
            mysql_port=int(os.getenv("MYSQL_PORT", "3306")),
            mysql_user=os.getenv("MYSQL_USER", "root"),
            mysql_password=os.getenv("MYSQL_PASSWORD", ""),
            mysql_database=os.getenv("MYSQL_DATABASE", "ai_chatbot"),
            mysql_ssl_mode=os.getenv("MYSQL_SSL_MODE", "DISABLED"),
            mysql_ssl_ca=os.getenv("MYSQL_SSL_CA", ""),
        )
