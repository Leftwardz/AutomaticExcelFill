from __future__ import annotations

import sys

import customtkinter as ctk

from app.models.storage import load_config
from app.ui.main_app import App
from app.ui.theme import init_theme_from_config

MIN_PYTHON = (3, 9)


def _check_python_version() -> None:
  if sys.version_info < MIN_PYTHON:
    version = '.'.join(str(part) for part in sys.version_info[:3])
    required = '.'.join(str(part) for part in MIN_PYTHON)
    raise SystemExit(f'Python {required}+ é necessário (detectado: {version}).')


def main() -> None:
  _check_python_version()
  config = load_config()
  init_theme_from_config(config.to_dict())
  ctk.set_default_color_theme('dark-blue')
  ctk.set_appearance_mode('dark')
  app = App(config)
  app.mainloop()


if __name__ == '__main__':
  main()
