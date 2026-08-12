from __future__ import annotations

import shutil
from pathlib import Path

from app.utils.network_paths import safe_exists, safe_is_dir, safe_is_file

APP_DATA_DIR_NAME = '_AutomaticExcelFill'
CONFIG_FILENAME = 'config.json'
DEFAULT_LOG_FILENAME = 'automatic_fill.log'
LOCK_DIR_NAME = '.automatic_fill_locks'


def app_data_dir(watch_folder: str | Path) -> Path:
  return Path(watch_folder) / APP_DATA_DIR_NAME


def shared_config_path(watch_folder: str | Path) -> Path:
  return app_data_dir(watch_folder) / CONFIG_FILENAME


def default_shared_log_path(watch_folder: str | Path) -> Path:
  return app_data_dir(watch_folder) / DEFAULT_LOG_FILENAME


def locks_root(watch_folder: str | Path) -> Path:
  return app_data_dir(watch_folder) / LOCK_DIR_NAME


def legacy_shared_config_path(watch_folder: str | Path) -> Path:
  return Path(watch_folder) / CONFIG_FILENAME


def legacy_shared_log_path(watch_folder: str | Path) -> Path:
  return Path(watch_folder) / DEFAULT_LOG_FILENAME


def legacy_locks_root(watch_folder: str | Path) -> Path:
  return Path(watch_folder) / LOCK_DIR_NAME


def migrate_legacy_app_data(watch_folder: str | Path) -> None:
  folder = Path(watch_folder)
  if not safe_is_dir(folder):
    return

  target_dir = app_data_dir(folder)
  try:
    target_dir.mkdir(parents=True, exist_ok=True)
  except OSError:
    return

  legacy_config = legacy_shared_config_path(folder)
  shared_config = shared_config_path(folder)
  if safe_is_file(legacy_config) and not safe_is_file(shared_config):
    try:
      shutil.move(str(legacy_config), str(shared_config))
    except OSError:
      pass

  legacy_log = legacy_shared_log_path(folder)
  shared_log = default_shared_log_path(folder)
  if safe_is_file(legacy_log) and not safe_is_file(shared_log):
    try:
      shutil.move(str(legacy_log), str(shared_log))
    except OSError:
      pass

  legacy_locks = legacy_locks_root(folder)
  shared_locks = locks_root(folder)
  if safe_is_dir(legacy_locks) and not safe_exists(shared_locks):
    try:
      shutil.move(str(legacy_locks), str(shared_locks))
    except OSError:
      pass
