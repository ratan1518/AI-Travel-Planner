from dataclasses import dataclass
import os

import streamlit as st


@dataclass(frozen=True)
class AppConfig:
    openrouter_api_key: str
    pexels_api_key: str
    app_url: str
    app_title: str
    model_name: str


def _read_setting(name: str, default: str = "") -> str:
    if name in st.secrets:
        value = st.secrets[name]
        return str(value).strip()
    return os.getenv(name, default).strip()


def load_config() -> AppConfig:
    return AppConfig(
        openrouter_api_key=_read_setting("OPENROUTER_API_KEY"),
        pexels_api_key=_read_setting("PEXELS_API_KEY"),
        app_url=_read_setting("APP_URL", "https://your-app-name.streamlit.app"),
        app_title=_read_setting("APP_TITLE", "AI Travel Planner"),
        model_name=_read_setting("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
    )
