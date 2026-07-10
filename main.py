from __future__ import annotations

import customtkinter as ctk

from app.models.storage import load_config
from app.ui.main_app import App
from app.ui.theme import init_theme_from_config


def main() -> None:
  config = load_config()
  init_theme_from_config(config.to_dict())
  ctk.set_default_color_theme('dark-blue')
  ctk.set_appearance_mode('dark')
  app = App(config)
  app.mainloop()


if __name__ == '__main__':
  main()
