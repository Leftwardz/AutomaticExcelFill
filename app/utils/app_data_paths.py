from __future__ import annotations

import shutil
from pathlib import Path

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
  if not folder.is_dir():
    return

  target_dir = app_data_dir(folder)
  target_dir.mkdir(parents=True, exist_ok=True)

  legacy_config = legacy_shared_config_path(folder)
  shared_config = shared_config_path(folder)
  if legacy_config.is_file() and not shared_config.is_file():
    shutil.move(str(legacy_config), str(shared_config))

  legacy_log = legacy_shared_log_path(folder)
  shared_log = default_shared_log_path(folder)
  if legacy_log.is_file() and not shared_log.is_file():
    shutil.move(str(legacy_log), str(shared_log))

  legacy_locks = legacy_locks_root(folder)
  shared_locks = locks_root(folder)
  if legacy_locks.is_dir() and not shared_locks.exists():
    shutil.move(str(legacy_locks), str(shared_locks))
