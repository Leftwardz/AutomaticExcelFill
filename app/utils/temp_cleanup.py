from __future__ import annotations

import time
from pathlib import Path

EXCEL_PART_SUFFIX = '.xlsx.part'
LEGACY_EXCEL_TEMP_SUFFIX = '.xlsx.tmp'
CONFIG_TEMP_SUFFIX = '.json.tmp'
DEFAULT_MAX_AGE_SECONDS = 3600.0


def _is_stale(path: Path, max_age_seconds: float) -> bool:
  try:
    return (time.time() - path.stat().st_mtime) > max_age_seconds
  except OSError:
    return False


def _remove_if_stale(path: Path, max_age_seconds: float) -> bool:
  if not path.is_file() or not _is_stale(path, max_age_seconds):
    return False
  try:
    path.unlink()
    return True
  except OSError:
    return False


def cleanup_directory_temp_files(
  directory: Path,
  *,
  max_age_seconds: float = DEFAULT_MAX_AGE_SECONDS,
) -> list[Path]:
  """Remove arquivos temporários órfãos de gravações interrompidas."""
  removed: list[Path] = []
  if not directory.is_dir():
    return removed

  patterns = (
    f'*{EXCEL_PART_SUFFIX}',
    f'*{LEGACY_EXCEL_TEMP_SUFFIX}',
    'tmp*.xlsx.tmp',
    f'*{CONFIG_TEMP_SUFFIX}',
  )
  seen: set[Path] = set()
  for pattern in patterns:
    for path in directory.glob(pattern):
      if path in seen:
        continue
      seen.add(path)
      if _remove_if_stale(path, max_age_seconds):
        removed.append(path)
  return removed


def cleanup_excel_directories(
  directories: list[str | Path],
  *,
  max_age_seconds: float = DEFAULT_MAX_AGE_SECONDS,
) -> list[Path]:
  """Varre pastas de Excel (e subpastas de ano) em busca de temporários antigos."""
  removed: list[Path] = []
  seen_dirs: set[Path] = set()

  for raw_directory in directories:
    directory = Path(raw_directory)
    if not directory.is_dir():
      continue

    targets = [directory]
    try:
      for child in directory.iterdir():
        if child.is_dir() and child.name.isdigit() and len(child.name) == 4:
          targets.append(child)
    except OSError:
      pass

    for target in targets:
      resolved = target.resolve()
      if resolved in seen_dirs:
        continue
      seen_dirs.add(resolved)
      removed.extend(
        cleanup_directory_temp_files(target, max_age_seconds=max_age_seconds),
      )
  return removed
