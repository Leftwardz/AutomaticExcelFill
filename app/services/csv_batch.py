from __future__ import annotations

from pathlib import Path

from app.models.schema import AppConfig, Flow
from app.models.storage import iter_matching_files
from app.services.file_stability import wait_for_file_stable

WATCHABLE_SUFFIXES = {'.csv', '.txt', '.tsv'}


def is_active_watch_file(path: Path, watch_folder: Path, config: AppConfig) -> bool:
  if not path.is_file():
    return False
  if path.suffix.lower() not in WATCHABLE_SUFFIXES:
    return False
  try:
    watch_folder.resolve()
    path.resolve().relative_to(watch_folder.resolve())
  except ValueError:
    return False
  if path.parent.resolve() != watch_folder.resolve():
    return False
  excluded = {config.processed_subfolder, config.failed_subfolder}
  return path.parent.name not in excluded


def collect_ready_csv_batch(
  watch_folder: Path,
  flow: Flow,
  config: AppConfig,
  *,
  skip_stability_wait: bool = False,
  sibling_stable_seconds: float = 1.0,
  sibling_timeout: float = 45.0,
) -> list[Path]:
  """Collect all stable CSV files in the watch folder that match the same flow."""
  candidates = [
    path
    for path in iter_matching_files(watch_folder, flow.source_filename)
    if is_active_watch_file(path, watch_folder, config)
  ]
  ready: list[Path] = []
  for candidate in candidates:
    if skip_stability_wait:
      ready.append(candidate)
      continue
    if wait_for_file_stable(
      candidate,
      stable_seconds=sibling_stable_seconds,
      timeout=sibling_timeout,
    ):
      ready.append(candidate)
  ready.sort(key=lambda path: path.name.lower())
  return ready
