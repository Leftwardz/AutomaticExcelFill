from __future__ import annotations

import sys
from pathlib import Path


def _project_root() -> Path:
  return Path(__file__).resolve().parents[2]


def install_dir() -> Path:
  """Pasta onde o executável (ou o projeto) está instalado — ex.: config.json ao lado do .exe."""
  if getattr(sys, 'frozen', False):
    return Path(sys.executable).resolve().parent
  return _project_root()


def resource_path(*parts: str) -> Path:
  """Arquivo ou pasta empacotado (PyInstaller) ou do projeto em desenvolvimento."""
  relative = Path(*parts)
  candidates: list[Path] = []
  if getattr(sys, 'frozen', False):
    meipass = getattr(sys, '_MEIPASS', None)
    if meipass:
      candidates.append(Path(meipass) / relative)
    candidates.append(install_dir() / relative)
  else:
    candidates.append(_project_root() / relative)

  for candidate in candidates:
    if candidate.exists():
      return candidate
  return candidates[0]
