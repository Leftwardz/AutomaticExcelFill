"""Gera screenshot do diálogo de cadastro de fluxo (scrot)."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

import customtkinter as ctk

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
  dialog.title('Cadastro de fluxo')
  dialog.update_idletasks()
  dialog.deiconify()
  dialog.lift()
  dialog.attributes('-topmost', True)
  dialog.focus_force()
  dialog.update()

  time.sleep(1.5)
  dialog.update()

  window_id = dialog.winfo_id()
  subprocess.run(
    ['import', '-window', str(window_id), str(OUTPUT)],
    check=True,
    capture_output=True,
  )
  print(f'Screenshot salvo em: {OUTPUT} (window id {window_id})')

  dialog.destroy()
  root.destroy()
  return 0


if __name__ == '__main__':
  sys.exit(main())
