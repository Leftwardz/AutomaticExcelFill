from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path
from typing import Optional

from app.models.schema import AppConfig, Flow
from app.utils.filename_matching import filename_matches_pattern, has_wildcards

CONFIG_FILENAME = 'config.json'
CONFIG_ENV_VAR = 'AUTOMATIC_EXCEL_FILL_CONFIG'


def app_dir() -> Path:
  if getattr(sys, 'frozen', False):
    return Path(sys.executable).resolve().parent
  return Path(__file__).resolve().parents[2]


def bootstrap_config_path() -> Path:
  return app_dir() / CONFIG_FILENAME


def shared_config_path(watch_folder: str) -> Path:
  return Path(watch_folder) / CONFIG_FILENAME


def resolve_config_path(watch_folder: str = '') -> Path:
  override = os.environ.get(CONFIG_ENV_VAR, '').strip()
  if override:
    return Path(override)
  folder = (watch_folder or '').strip()
  if folder:
    return shared_config_path(folder)
  return bootstrap_config_path()


def _atomic_write_json(path: Path, data: dict) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  tmp_path = path.with_suffix(path.suffix + '.tmp')
  with open(tmp_path, 'w', encoding='utf-8') as handle:
    json.dump(data, handle, ensure_ascii=False, indent=2)
  backup_path = path.with_suffix(path.suffix + '.bak')
  if path.is_file():
    shutil.copy2(path, backup_path)
  os.replace(tmp_path, path)


def load_config() -> AppConfig:
  bootstrap = bootstrap_config_path()
  config = AppConfig()

  if bootstrap.is_file():
    with open(bootstrap, encoding='utf-8') as handle:
      config = AppConfig.from_dict(json.load(handle))

  watch_folder = (config.watch_folder or '').strip()
  if watch_folder:
    shared = shared_config_path(watch_folder)
    if shared.is_file() and shared.resolve() != bootstrap.resolve():
      with open(shared, encoding='utf-8') as handle:
        config = AppConfig.from_dict(json.load(handle))
    return config

  override = os.environ.get(CONFIG_ENV_VAR, '').strip()
  if override and Path(override).is_file():
    with open(override, encoding='utf-8') as handle:
      config = AppConfig.from_dict(json.load(handle))
  return config


def save_config(config: AppConfig) -> None:
  target = resolve_config_path(config.watch_folder)
  _atomic_write_json(target, config.to_dict())

  bootstrap = bootstrap_config_path()
  if (config.watch_folder or '').strip() and target.resolve() != bootstrap.resolve():
    _atomic_write_json(bootstrap, {'watch_folder': config.watch_folder})


def upsert_flow(config: AppConfig, flow: Flow) -> AppConfig:
  for index, existing in enumerate(config.flows):
    if existing.id == flow.id:
      config.flows[index] = flow
      return config
  config.flows.append(flow)
  return config


def remove_flow(config: AppConfig, flow_id: str) -> AppConfig:
  config.flows = [flow for flow in config.flows if flow.id != flow_id]
  return config


def find_flow_by_filename(config: AppConfig, filename: str) -> Optional[Flow]:
  for flow in config.flows:
    if not flow.enabled:
      continue
    if filename_matches_pattern(filename, flow.source_filename):
      return flow
  return None


def iter_matching_files(folder: Path, pattern: str):
  """Lista arquivos na pasta que correspondem ao padrão do fluxo."""
  if not folder.is_dir():
    return
  if has_wildcards(pattern):
    for path in sorted(folder.iterdir()):
      if path.is_file() and filename_matches_pattern(path.name, pattern):
        yield path
    return
  candidate = folder / pattern
  if candidate.is_file():
    yield candidate
