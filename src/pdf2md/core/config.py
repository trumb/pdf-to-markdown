"""Configuration management using Pydantic settings."""

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="PDF2MD_",
        case_sensitive=False,
    )

    # Extraction settings
    extractor: Literal["pdfplumber", "pymupdf", "auto"] = Field(
        default="auto",
        description="PDF extraction engine (auto=try pdfplumber, fallback to pymupdf)",
    )

    # Security sandbox settings
    sandbox_enabled: bool = Field(
        default=True, description="Enable process isolation sandbox"
    )
    sandbox_timeout: int = Field(
        default=60, description="Sandbox timeout in seconds", ge=1, le=600
    )
    sandbox_memory_limit_mb: int = Field(
        default=512, description="Memory limit in MB", ge=128, le=4096
    )

    # Output settings
    output_format: Literal["markdown", "json", "yaml", "text"] = Field(
        default="markdown", description="Default output format"
    )
    include_frontmatter: bool = Field(
        default=True, description="Include YAML frontmatter in markdown"
    )
    include_tokens: bool = Field(
        default=True, description="Include token counts in output"
    )

    # Image handling
    image_mode: Literal["skip", "extract", "base64", "reference"] = Field(
        default="skip", description="How to handle images"
    )

    # Table handling
    table_format: Literal["markdown", "html", "code", "csv"] = Field(
        default="markdown", description="Table output format"
    )

    # Token counting
    token_encodings: list[str] = Field(
        default=["cl100k_base", "p50k_base", "claude"],
        description="Token encoding methods to use",
    )

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Logging level"
    )

    # Version
    version: str = Field(default="1.0.0", description="Application version")


# Global settings instance
settings = Settings()
