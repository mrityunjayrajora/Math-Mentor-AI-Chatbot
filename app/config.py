"""
Configuration loader for the Math Mentor application.
Loads config.yaml and overlays environment variables.
"""

import os
from pathlib import Path
from functools import lru_cache
from typing import Any, Dict, List, Optional

import yaml
from dotenv import load_dotenv

load_dotenv()

# Project root is one level up from the app/ directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _deep_merge(base: dict, override: dict) -> dict:
    """Deep merge two dicts, with override taking precedence."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


class Settings:
    """Singleton settings object loaded from config.yaml + env vars."""

    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            config_path = os.getenv(
                "CONFIG_PATH",
                str(PROJECT_ROOT / "config" / "config.yaml")
            )

        with open(config_path, "r") as f:
            self._config: Dict[str, Any] = yaml.safe_load(f)

        self._apply_env_overrides()

    def _apply_env_overrides(self):
        """Override config values with environment variables."""
        env_mappings = {
            "GOOGLE_API_KEY": None,  # standalone, not in config
            "LLM_MODEL": ("llm", "model"),
            "LLM_TEMPERATURE": ("llm", "temperature"),
            "LLM_MAX_TOKENS": ("llm", "max_tokens"),
            "OCR_CONFIDENCE_THRESHOLD": ("ocr", "confidence_threshold"),
            "ASR_MODEL_SIZE": ("asr", "model_size"),
            "ASR_CONFIDENCE_THRESHOLD": ("asr", "confidence_threshold"),
            "RAG_TOP_K": ("rag", "top_k"),
            "RAG_CHUNK_SIZE": ("rag", "chunk_size"),
            "MEMORY_DB_PATH": ("memory", "db_path"),
            "SERVER_HOST": ("server", "host"),
            "SERVER_PORT": ("server", "port"),
            "SERVER_DEBUG": ("server", "debug"),
            "LOG_LEVEL": ("logging", "level"),
        }

        type_casts = {
            "LLM_TEMPERATURE": float,
            "LLM_MAX_TOKENS": int,
            "OCR_CONFIDENCE_THRESHOLD": float,
            "ASR_CONFIDENCE_THRESHOLD": float,
            "RAG_TOP_K": int,
            "RAG_CHUNK_SIZE": int,
            "SERVER_PORT": int,
            "SERVER_DEBUG": lambda x: x.lower() in ("true", "1", "yes"),
        }

        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None and config_path is not None:
                if env_var in type_casts:
                    value = type_casts[env_var](value)
                # Navigate to the nested config key
                section = self._config
                for key in config_path[:-1]:
                    section = section.setdefault(key, {})
                section[config_path[-1]] = value

    # --- Accessors ---

    @property
    def google_api_key(self) -> str:
        key = os.getenv("GOOGLE_API_KEY", "")
        if not key:
            raise ValueError("GOOGLE_API_KEY environment variable is required")
        return key

    @property
    def llm(self) -> Dict[str, Any]:
        return self._config.get("llm", {})

    @property
    def ocr(self) -> Dict[str, Any]:
        return self._config.get("ocr", {})

    @property
    def asr(self) -> Dict[str, Any]:
        return self._config.get("asr", {})

    @property
    def rag(self) -> Dict[str, Any]:
        return self._config.get("rag", {})

    @property
    def memory(self) -> Dict[str, Any]:
        return self._config.get("memory", {})

    @property
    def hitl(self) -> Dict[str, Any]:
        return self._config.get("hitl", {})

    @property
    def agents(self) -> Dict[str, Any]:
        return self._config.get("agents", {})

    @property
    def server(self) -> Dict[str, Any]:
        return self._config.get("server", {})

    @property
    def logging_config(self) -> Dict[str, Any]:
        return self._config.get("logging", {})

    def get(self, *keys: str, default: Any = None) -> Any:
        """Get a nested config value by key path."""
        section = self._config
        for key in keys:
            if isinstance(section, dict):
                section = section.get(key)
                if section is None:
                    return default
            else:
                return default
        return section


_settings_instance: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create the singleton Settings instance."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance


def reset_settings():
    """Reset settings (useful for testing)."""
    global _settings_instance
    _settings_instance = None
