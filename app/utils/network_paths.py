from __future__ import annotations

from pathlib import Path


def is_likely_network_path(path: str | Path) -> bool:
  text = str(path).strip().replace('/', '\\')
  return text.startswith('\\\\')
