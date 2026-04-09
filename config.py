# config.py
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict


CONFIG_DIR = Path(os.path.expandvars(r"%USERPROFILE%")) / ".gmcli"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "api_key": "HIER_DEIN_API_KEY",
    "default_load_chunks": False,
    "presets": {
        "quelle": {"x": 100, "y": 64, "z": 200},
        "ziel": {"x": 105, "y": 64, "z": 200}
    },
    "ui": {
        "appearance_mode": "dark",
        "window_width": 1200,
        "window_height": 760
    }
}


class ConfigError(Exception):
    """Fehler in der lokalen Konfiguration."""


def ensure_config_exists() -> Path:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        with CONFIG_FILE.open("w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)
    return CONFIG_FILE


def load_config() -> Dict[str, Any]:
    ensure_config_exists()
    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Ungültige config.json: {exc}") from exc

    if not isinstance(data, dict):
        raise ConfigError("config.json muss ein JSON-Objekt sein.")

    data.setdefault("api_key", "HIER_DEIN_API_KEY")
    data.setdefault("default_load_chunks", False)
    data.setdefault("presets", {})
    data.setdefault("ui", {})
    data["ui"].setdefault("appearance_mode", "dark")
    data["ui"].setdefault("window_width", 1200)
    data["ui"].setdefault("window_height", 760)
    return data


def save_config(data: Dict[str, Any]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with CONFIG_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_api_key() -> str:
    data = load_config()
    key = str(data.get("api_key", "")).strip()
    if not key or key == "HIER_DEIN_API_KEY":
        raise ConfigError(
            f"Bitte trage deinen API-Key in {CONFIG_FILE} ein oder nutze das Einstellungsfenster."
        )
    return key


def get_presets() -> Dict[str, Dict[str, int]]:
    data = load_config()
    presets = data.get("presets", {})
    if not isinstance(presets, dict):
        raise ConfigError("'presets' muss ein Objekt sein.")
    return presets


def set_preset(name: str, x: int, y: int, z: int) -> None:
    data = load_config()
    data.setdefault("presets", {})
    data["presets"][name] = {"x": int(x), "y": int(y), "z": int(z)}
    save_config(data)


def delete_preset(name: str) -> bool:
    data = load_config()
    presets = data.setdefault("presets", {})
    if name in presets:
        del presets[name]
        save_config(data)
        return True
    return False


def update_api_key(api_key: str) -> None:
    data = load_config()
    data["api_key"] = api_key.strip()
    save_config(data)


def update_default_load_chunks(value: bool) -> None:
    data = load_config()
    data["default_load_chunks"] = bool(value)
    save_config(data)


def get_default_load_chunks() -> bool:
    return bool(load_config().get("default_load_chunks", False))


def get_ui_settings() -> Dict[str, Any]:
    return load_config().get("ui", {})


def update_ui_settings(**kwargs: Any) -> None:
    data = load_config()
    ui = data.setdefault("ui", {})
    for key, value in kwargs.items():
        ui[key] = value
    save_config(data)


def parse_coordinates(text: str) -> tuple[int, int, int]:
    try:
        parts = [p.strip() for p in text.split(",")]
        if len(parts) != 3:
            raise ValueError
        return int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError as exc:
        raise ConfigError("Koordinaten müssen im Format x,y,z angegeben werden.") from exc