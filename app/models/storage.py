from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Callable, Optional

from app.models.schema import AppConfig, Flow


def app_dir() -> Path:
  if getattr(sys, 'frozen', False):
    return Path(sys.executable).resolve().parent
  return Path(__file__).resolve().parents[2]


def config_path() -> Path:
  return app_dir() / 'config.json'


def load_config() -> AppConfig:
  path = config_path()
  if not path.is_file():
    return AppConfig()
  with open(path, encoding='utf-8') as f:
    return AppConfig.from_dict(json.load(f))


def save_config(config: AppConfig) -> None:
  path = config_path()
  with open(path, 'w', encoding='utf-8') as f:
    json.dump(config.to_dict(), f, ensure_ascii=False, indent=2)


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
  filename_lower = filename.lower()
  for flow in config.flows:
    if not flow.enabled:
      continue
    if flow.source_filename.lower() == filename_lower:
      return flow
  return None
