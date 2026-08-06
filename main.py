from __future__ import annotations

import sys

import customtkinter as ctk

from app.models.storage import load_config
from app.ui.main_app import App
from app.ui.theme import init_theme_from_config
from app.utils.crash_guard import install_crash_guard
from app.utils.temp_cleanup import cleanup_excel_directories

MIN_PYTHON = (3, 9)


def _check_python_version() -> None:
  if sys.version_info < MIN_PYTHON:
    version = '.'.join(str(part) for part in sys.version_info[:3])
    required = '.'.join(str(part) for part in MIN_PYTHON)
    raise SystemExit(f'Python {required}+ é necessário (detectado: {version}).')


def _cleanup_stale_temp_files(config) -> None:
  directories = [
    flow.excel_directory
    for flow in config.flows
    if (flow.excel_directory or '').strip()
  ]
  if not directories:
    return
  cleanup_excel_directories(directories)


def main() -> None:
  install_crash_guard()
  _check_python_version()
  config = load_config()
  _cleanup_stale_temp_files(config)
  init_theme_from_config(config.to_dict())
  ctk.set_default_color_theme('dark-blue')
  ctk.set_appearance_mode('dark')
  app = App(config)
  app.mainloop()


if __name__ == '__main__':
  main()
