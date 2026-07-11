from __future__ import annotations

import socket
from datetime import datetime
from pathlib import Path

from app.models.schema import AppConfig


def resolve_shared_log_path(config: AppConfig) -> Path:
  custom = (config.shared_log_path or '').strip()
  if custom:
    path = Path(custom)
    if path.is_dir():
      return path / 'automatic_fill.log'
    return path
  watch_folder = (config.watch_folder or '').strip()
  if watch_folder:
    return Path(watch_folder) / 'automatic_fill.log'
  return Path('automatic_fill.log')


def append_job_log(
  log_path: Path,
  level: str,
  message: str,
  *,
  flow_name: str = '',
  source_file: str = '',
) -> None:
  log_path.parent.mkdir(parents=True, exist_ok=True)
  timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
  host = socket.gethostname()
  flow = flow_name or '-'
  source = source_file or '-'
  line = f'{timestamp}\t{host}\t{level.upper()}\t{flow}\t{source}\t{message}\n'
  with open(log_path, 'a', encoding='utf-8') as handle:
    handle.write(line)
