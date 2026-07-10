"""Smoke test: inicia a janela principal e encerra sem bloquear."""

from __future__ import annotations

import sys

import customtkinter as ctk

from app.models.storage import load_config
from app.ui.main_app import App
from app.ui.theme import init_theme_from_config


def main() -> int:
  config = load_config()
  init_theme_from_config(config.to_dict())
  ctk.set_default_color_theme('dark-blue')
  ctk.set_appearance_mode('dark')

  app = App(config)
  app.update_idletasks()
  title = app.title()
  app.after(300, app.destroy)
  app.mainloop()
  print(f'OK: janela iniciada ({title!r})')
  return 0


if __name__ == '__main__':
  sys.exit(main())
