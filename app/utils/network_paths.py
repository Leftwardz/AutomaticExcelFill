from __future__ import annotations

import sys
from pathlib import Path


def is_unc_path(path: str | Path) -> bool:
  text = str(path).strip().replace('/', '\\')
  return text.startswith('\\\\')


def is_windows_mapped_network_drive(path: str | Path) -> bool:
  if sys.platform != 'win32':
    return False
  import ctypes

  text = str(path).strip().replace('/', '\\')
  if len(text) < 2 or text[1] != ':':
    return False
  drive = text[:2] + '\\'
  drive_remote = 4
  return ctypes.windll.kernel32.GetDriveTypeW(drive) == drive_remote


def is_likely_network_path(path: str | Path) -> bool:
  if is_unc_path(path):
    return True
  try:
    return is_windows_mapped_network_drive(path)
  except Exception:
    return False
