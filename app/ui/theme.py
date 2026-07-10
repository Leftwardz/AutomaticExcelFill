"""UI color presets loaded from theme/presets.json."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from app.ui import constants


@dataclass(frozen=True)
class ThemePreset:
    id: str
    sidebar: str
    bg: str
    card: str
    card_border: str
    accent: str
    accent_hover: str
    accent_secondary: str
    nav_active: str
    text_secondary: str
    progress_bg: str
    destructive: str
    destructive_hover: str
    icon: str
    nav_text_accent: str
    gradient_hover: str
    table_row_a: str
    table_row_b: str
    canvas_bg: str
    error_text: str


_current_theme_id: str = 'slate'


def app_dir() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def presets_path() -> Path:
    return app_dir() / 'theme' / 'presets.json'


@lru_cache(maxsize=1)
def _load_catalog() -> Tuple[str, Dict[str, ThemePreset]]:
    path = presets_path()
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    default_id = data.get('default', 'slate')
    presets: Dict[str, ThemePreset] = {}
    for preset_id, colors in data.get('presets', {}).items():
        presets[preset_id] = ThemePreset(id=preset_id, **colors)
    return default_id, presets


def get_theme() -> ThemePreset:
    default_id, presets = _load_catalog()
    return presets.get(_current_theme_id) or presets.get(default_id) or next(iter(presets.values()))


def init_theme_from_config(config: Optional[dict] = None) -> ThemePreset:
    config = config or {}
    default_id, presets = _load_catalog()
    theme_id = (config.get('ui_theme') or default_id).strip()
    if theme_id not in presets:
        theme_id = default_id if default_id in presets else next(iter(presets))
    preset = presets[theme_id]
    constants.apply_theme_colors(
        sidebar=preset.sidebar,
        bg=preset.bg,
        card=preset.card,
        card_border=preset.card_border,
        accent=preset.accent,
        accent_hover=preset.accent_hover,
        accent_secondary=preset.accent_secondary,
        nav_active=preset.nav_active,
        text_secondary=preset.text_secondary,
        progress_bg=preset.progress_bg,
        destructive=preset.destructive,
        destructive_hover=preset.destructive_hover,
        icon=preset.icon,
        nav_text_accent=preset.nav_text_accent,
        gradient_hover=preset.gradient_hover,
        table_row_a=preset.table_row_a,
        table_row_b=preset.table_row_b,
        canvas_bg=preset.canvas_bg,
        error_text=preset.error_text,
    )
    return preset
