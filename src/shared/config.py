from enum import StrEnum

from pydantic_settings import BaseSettings, SettingsConfigDict


class BusinessSegment(StrEnum):
    T_SYSTEMS = "t_systems"
    TELEKOM_DEUTSCHLAND = "telekom_deutschland"
    T_MOBILE_US = "t_mobile_us"
    DEUTSCHE_TELEKOM_GROUP = "deutsche_telekom_group"


class DocumentType(StrEnum):
    FINANCIAL_REPORT = "financial_report"
    PRODUCT_LAUNCH = "product_launch"
    PARTNERSHIP = "partnership"
    AWARD = "award"
    GENERAL = "general"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    azure_openai_api_key: str = ""
    azure_openai_endpoint: str = ""
    azure_openai_deployment: str = "gpt-4o"
    azure_openai_api_version: str = "2024-12-01-preview"

    cohere_api_key: str = ""
    cohere_embed_model: str = "embed-english-v3.0"
    cohere_rerank_model: str = "rerank-english-v3.0"

    database_path: str = "data/rag.db"

    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    phoenix_host: str = "http://localhost:6006"

    reranker_threshold: float = 0.3
    max_tool_calls: int = 3


def get_settings() -> Settings:
    return Settings()
