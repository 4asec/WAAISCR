import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Base project path
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load .env if present
load_dotenv(PROJECT_ROOT / ".env")

class AppConfig(BaseModel):
    name: str = "Link Curator"
    version: str = "0.1.0"
    env: str = "development"
    host: str = "127.0.0.1"
    port: int = 8000

class WhitelistConfig(BaseModel):
    phone_numbers: List[str] = Field(default_factory=list)

    def is_allowed(self, phone: str) -> bool:
        """Check if phone number is in whitelist (after cleaning formatting and handling country prefixes)."""
        clean_target = "".join(filter(str.isdigit, phone))
        # Normalize local Indonesian prefix '0' to '62' if applicable
        if clean_target.startswith("08"):
            clean_target = "62" + clean_target[1:]

        for allowed in self.phone_numbers:
            clean_allowed = "".join(filter(str.isdigit, allowed))
            if clean_allowed.startswith("08"):
                clean_allowed = "62" + clean_allowed[1:]

            if clean_target and clean_allowed:
                if clean_target == clean_allowed or clean_target.endswith(clean_allowed) or clean_allowed.endswith(clean_target):
                    return True
        return False

class WhatsAppConfig(BaseModel):
    auth_method: str = "qr"             # "qr" or "pairing"
    phone_number: str = ""              # Secondary phone number for pairing
    gateway_url: str = "http://127.0.0.1:3001"
    reconnect_max_attempts: int = 10
    send_delay_min_ms: int = 1000
    send_delay_max_ms: int = 3000

class RateLimitConfig(BaseModel):
    requests_per_minute: int = 15
    tokens_per_minute: int = 1000000

class LLMConfig(BaseModel):
    provider: str = "gemini"            # "gemini" or "ollama"
    model: str = "gemini-2.5-flash"
    api_key: Optional[str] = None
    timeout_seconds: int = 45
    max_retries: int = 3
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)

class FormattingConfig(BaseModel):
    term_badge: str = "🔹"
    bold_terms: bool = True
    meta_ai_style: bool = True

class GroupsConfig(BaseModel):
    default_role: str = "ignore"        # links | tugas | pdf | ignore
    default_reply_mode: str = "quiet"   # quiet (DM) | group_reply
    group_rules: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

class StorageConfig(BaseModel):
    database_url: str = f"sqlite+aiosqlite:///{PROJECT_ROOT / 'data' / 'link_curator.db'}"

class Config(BaseModel):
    app: AppConfig = Field(default_factory=AppConfig)
    whitelist: WhitelistConfig = Field(default_factory=WhitelistConfig)
    whatsapp: WhatsAppConfig = Field(default_factory=WhatsAppConfig)
    groups: GroupsConfig = Field(default_factory=GroupsConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    formatting: FormattingConfig = Field(default_factory=FormattingConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)

def load_config(config_path: Optional[Path] = None) -> Config:
    """Load configuration from config.yaml and environment variables."""
    target_path = config_path or (PROJECT_ROOT / "config.yaml")
    data: Dict[str, Any] = {}

    if target_path.exists():
        with open(target_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

    # Override / inject from environment variables
    whitelist_env = os.getenv("WHITELIST_PHONE_NUMBERS")
    if whitelist_env:
        data["whitelist"] = {
            "phone_numbers": [p.strip() for p in whitelist_env.split(",") if p.strip()]
        }

    llm_dict = data.get("llm", {})
    env_gemini_key = os.getenv("GEMINI_API_KEY")
    if env_gemini_key:
        llm_dict["api_key"] = env_gemini_key
    data["llm"] = llm_dict

    wa_dict = data.get("whatsapp", {})
    if os.getenv("WA_AUTH_METHOD"):
        wa_dict["auth_method"] = os.getenv("WA_AUTH_METHOD")
    if os.getenv("WA_PHONE_NUMBER"):
        wa_dict["phone_number"] = os.getenv("WA_PHONE_NUMBER")
    if os.getenv("GATEWAY_PORT"):
        wa_dict["gateway_url"] = f"http://127.0.0.1:{os.getenv('GATEWAY_PORT')}"
    data["whatsapp"] = wa_dict

    storage_dict = data.get("storage", {})
    if os.getenv("DATABASE_URL"):
        storage_dict["database_url"] = os.getenv("DATABASE_URL")
    data["storage"] = storage_dict

    return Config(**data)

# Global settings instance
settings = load_config()
