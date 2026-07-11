"""Gera screenshot do diálogo de cadastro de fluxo."""

from __future__ import annotations

import sys
from pathlib import Path

import customtkinter as ctk
from PIL import ImageGrab

from app.models.storage import load_config
from app.ui.flow_dialog import FlowDialog
from app.ui.theme import init_theme_from_config

OUTPUT = Path(__file__).resolve().parents[1] / 'flow_dialog_screenshot.png'


def main() -> int:
  config = load_config()
  init_theme_from_config(config.to_dict())
  ctk.set_default_color_theme('dark-blue')
  ctk.set_appearance_mode('dark')

  root = ctk.CTk()
  root.withdraw()

  dialog = FlowDialog(root)
  dialog.update_idletasks()
  dialog.update()

  def capture_and_exit() -> None:
    dialog.update_idletasks()
    x = dialog.winfo_rootx()
    y = dialog.winfo_rooty()
    width = dialog.winfo_width()
    height = dialog.winfo_height()
    image = ImageGrab.grab(bbox=(x, y, x + width, y + height))
    image.save(OUTPUT)
    print(f'Screenshot salvo em: {OUTPUT}')
    dialog.destroy()
    root.destroy()

  dialog.after(600, capture_and_exit)
  root.mainloop()
  return 0


if __name__ == '__main__':
  sys.exit(main())
