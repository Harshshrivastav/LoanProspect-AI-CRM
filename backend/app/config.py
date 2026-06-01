"""
Application configuration via environment variables.
"""

import os
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    app_name: str = "LoanProspect AI CRM"
    app_version: str = "1.0.0"
    app_env: str = "development"
    debug: bool = True

    # LLM
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    max_agent_iterations: int = 15
    agent_verbose: bool = True
    agent_timeout: int = 120

    # Database
    database_url: str = "sqlite:///./data/banking_crm.db"

    # Security
    app_secret_key: str = "change_me_in_production"

    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def db_path(self) -> Path:
        url = self.database_url.replace("sqlite:///", "")
        p = Path(url)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
