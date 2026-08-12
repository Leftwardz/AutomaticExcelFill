from __future__ import annotations

import sys
import threading
import traceback
from datetime import datetime
from pathlib import Path
from typing import Callable

from app.models.storage import bootstrap_config_path

_main_window = None


def register_main_window(window) -> None:
  global _main_window
  _main_window = window


def _default_crash_log_path() -> Path:
  return bootstrap_config_path().parent / 'crash.log'


def _write_crash_log(path: Path, header: str, exc: BaseException) -> None:
  try:
    path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(path, 'a', encoding='utf-8') as handle:
      handle.write(f'\n=== {header} @ {timestamp} ===\n')
      handle.write(''.join(traceback.format_exception(type(exc), exc, exc.__traceback__)))
      handle.write('\n')
  except OSError:
    pass


def _show_crash_dialog(message: str) -> None:
  try:
    import tkinter as tk
    from tkinter import messagebox

    parent = _main_window
    if parent is not None:
      try:
        if not parent.winfo_exists():
          parent = None
      except Exception:
        parent = None

    if parent is None:
      root = tk.Tk()
      root.withdraw()
      messagebox.showerror(
        'AutomaticExcelFill — erro inesperado',
        message,
        parent=root,
      )
      root.destroy()
      return

    messagebox.showerror(
      'AutomaticExcelFill — erro inesperado',
      message,
      parent=parent,
    )
  except Exception:
    pass


def install_crash_guard(
  *,
  crash_log_path: Path | None = None,
  on_fatal: Callable[[BaseException, str], None] | None = None,
) -> None:
  log_path = crash_log_path or _default_crash_log_path()
  if getattr(install_crash_guard, '_installed', False):
    return
  install_crash_guard._installed = True

  def _handle_main_thread(exc: BaseException) -> None:
    tb = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    _write_crash_log(log_path, 'thread principal', exc)
    if on_fatal is not None:
      on_fatal(exc, tb)
      return
    _show_crash_dialog(
      'O programa encontrou um erro inesperado.\n\n'
      f'Detalhes foram salvos em:\n{log_path}\n\n'
      f'Erro: {exc}'
    )

  previous_hook = sys.excepthook

  def sys_hook(exc_type, exc, tb):
    if exc_type is KeyboardInterrupt:
      previous_hook(exc_type, exc, tb)
      return
    if exc is not None:
      _handle_main_thread(exc)
    previous_hook(exc_type, exc, tb)

  sys.excepthook = sys_hook

  if hasattr(threading, 'excepthook'):
    previous_thread_hook = threading.excepthook

    def thread_hook(args):
      if args.exc_value is not None:
        _write_crash_log(
          log_path,
          f'thread {args.thread.name}',
          args.exc_value,
        )
      if previous_thread_hook is not None:
        previous_thread_hook(args)

    threading.excepthook = thread_hook
