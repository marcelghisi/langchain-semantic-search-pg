from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from getpass import getpass
from pathlib import Path
from urllib.parse import quote_plus
from typing import TYPE_CHECKING

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv() -> bool:
        return False

if TYPE_CHECKING:
    from psycopg import Connection


load_dotenv()

CONFIG_DIR = Path.home() / ".ghisi"
CONFIG_PATH = CONFIG_DIR / "config.json"
SUPPORTED_PROVIDERS = ("openai", "gemini")
DEFAULT_TEMPERATURES = {
    "gpt-5-nano": 1,
    "text-embedding-004": 0.1,
}


@dataclass
class AppConfig:
    pg_host: str
    pg_port: int
    pg_database: str
    pg_user: str
    pg_password: str
    provider: str
    langchain_api_key: str
    openai_api_key: str
    openai_embedding_model: str = "text-embedding-3-small"
    openai_llm_model: str = "gpt-5-nano"
    openai_embedding_dimensions: int = 1536
    google_api_key: str = ""
    gemini_embedding_model: str = "gemini-embedding-001"
    gemini_llm_model: str = "gemini-2.5-flash-lite"
    gemini_embedding_dimensions: int = 768


def _env_or_default(name: str, default: str) -> str:
    return os.getenv(name, default)


def get_default_config() -> AppConfig:
    return AppConfig(
        pg_host=_env_or_default("PG_HOST", "localhost"),
        pg_port=int(_env_or_default("PG_PORT", "5432")),
        pg_database=_env_or_default("PG_DATABASE", "ghisi_rag"),
        pg_user=_env_or_default("PG_USER", "ghisi"),
        pg_password=_env_or_default("PG_PASSWORD", "ghisi"),
        provider=_env_or_default("MODEL_PROVIDER", "openai"),
        langchain_api_key=_env_or_default("LANGCHAIN_API_KEY", ""),
        openai_api_key=_env_or_default("OPENAI_API_KEY", ""),
        openai_embedding_model=_env_or_default(
            "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"
        ),
        openai_llm_model=_env_or_default("OPENAI_LLM_MODEL", "gpt-5-nano"),
        openai_embedding_dimensions=int(
            _env_or_default("OPENAI_EMBEDDING_DIMENSIONS", "1536")
        ),
        google_api_key=_env_or_default("GOOGLE_API_KEY", ""),
        gemini_embedding_model=_env_or_default(
            "GEMINI_EMBEDDING_MODEL", "gemini-embedding-001"
        ),
        gemini_llm_model=_env_or_default("GEMINI_LLM_MODEL", "gemini-2.5-flash-lite"),
        gemini_embedding_dimensions=int(
            _env_or_default("GEMINI_EMBEDDING_DIMENSIONS", "768")
        ),
    )


def save_config(config: AppConfig) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with CONFIG_PATH.open("w", encoding="utf-8") as file:
        json.dump(asdict(config), file, indent=2)


def load_config() -> AppConfig:
    if CONFIG_PATH.exists():
        with CONFIG_PATH.open("r", encoding="utf-8") as file:
            config = AppConfig(**json.load(file))
    else:
        config = get_default_config()
    config.provider = normalize_provider(config.provider)
    return config


def _ask_value(label: str, default: str | None = None, secret: bool = False) -> str:
    suffix = f" [{default}]" if default else ""
    prompt = f"{label}{suffix}: "
    raw = getpass(prompt) if secret else input(prompt)
    if raw.strip():
        return raw.strip()
    return default or ""


def configure_interactive() -> AppConfig:
    existing = load_config()
    config = AppConfig(
        pg_host=_ask_value("PG Host", existing.pg_host),
        pg_port=int(_ask_value("PG Port", str(existing.pg_port))),
        pg_database=_ask_value("PG Database", existing.pg_database),
        pg_user=_ask_value("PG User", existing.pg_user),
        pg_password=_ask_value("PG Password", existing.pg_password),
        provider=normalize_provider(
            _ask_value("Provider (openai|gemini)", existing.provider)
        ),
        langchain_api_key=_ask_value(
            "LangChain API Key", existing.langchain_api_key, secret=True
        ),
        openai_api_key=_ask_value("OpenAI API Key", existing.openai_api_key, secret=True),
        openai_embedding_model=_ask_value(
            "OpenAI Embedding model", existing.openai_embedding_model
        ),
        openai_llm_model=_ask_value("OpenAI LLM model", existing.openai_llm_model),
        openai_embedding_dimensions=int(
            _ask_value(
                "OpenAI Embedding dimensions",
                str(existing.openai_embedding_dimensions),
            )
        ),
        google_api_key=_ask_value("Google API Key", existing.google_api_key, secret=True),
        gemini_embedding_model=_ask_value(
            "Gemini Embedding model", existing.gemini_embedding_model
        ),
        gemini_llm_model=_ask_value("Gemini LLM model", existing.gemini_llm_model),
        gemini_embedding_dimensions=int(
            _ask_value(
                "Gemini Embedding dimensions",
                str(existing.gemini_embedding_dimensions),
            )
        ),
    )
    save_config(config)
    return config


def normalize_provider(provider: str) -> str:
    normalized = provider.strip().lower()
    if normalized not in SUPPORTED_PROVIDERS:
        accepted = ", ".join(SUPPORTED_PROVIDERS)
        raise ValueError(f"Provider invalido: {provider}. Use um de: {accepted}")
    return normalized


def resolve_provider(config: AppConfig, provider: str | None) -> str:
    if provider:
        return normalize_provider(provider)
    return normalize_provider(config.provider)


def embedding_dimensions_for_provider(config: AppConfig, provider: str) -> int:
    if provider == "openai":
        return config.openai_embedding_dimensions
    return config.gemini_embedding_dimensions


def table_name_for_provider(provider: str) -> str:
    if provider == "openai":
        return "documents_openai"
    if provider == "gemini":
        return "documents_gemini"
    raise ValueError(f"Provider invalido: {provider}")


def embed_text(config: AppConfig, provider: str, text: str) -> list[float]:
    embeddings = get_embeddings_provider(config, provider)
    return embeddings.embed_query(text)


def get_embeddings_provider(config: AppConfig, provider: str):
    if provider == "openai":
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(
            api_key=config.openai_api_key,
            model=config.openai_embedding_model,
        )

    from langchain_google_genai import GoogleGenerativeAIEmbeddings

    return GoogleGenerativeAIEmbeddings(
        model=config.gemini_embedding_model,
        google_api_key=config.google_api_key,
    )


def open_connection(config: AppConfig) -> "Connection":
    from pgvector.psycopg import register_vector
    from psycopg import connect

    connection = connect(
        host=config.pg_host,
        port=config.pg_port,
        dbname=config.pg_database,
        user=config.pg_user,
        password=config.pg_password,
    )
    register_vector(connection)
    return connection


def build_postgres_connection_string(config: AppConfig) -> str:
    user = quote_plus(config.pg_user)
    password = quote_plus(config.pg_password)
    host = config.pg_host
    port = config.pg_port
    database = quote_plus(config.pg_database)
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{database}"


def ensure_schema(connection: "Connection", table_name: str, dimensions: int) -> None:
    with connection.cursor() as cursor:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id BIGSERIAL PRIMARY KEY,
                source TEXT NOT NULL,
                content TEXT NOT NULL,
                embedding vector({dimensions}) NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
    connection.commit()

