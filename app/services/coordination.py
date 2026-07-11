from __future__ import annotations

import os
import socket
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


class LockNotAcquired(Exception):
  def __init__(self, resource: str, owner: str = ''):
    self.resource = resource
    self.owner = owner
    message = f'Recurso já em uso por outro processo: {resource}'
    if owner:
      message = f'{message} — {owner}'
    super().__init__(message)


DEFAULT_STALE_SECONDS = 600
CSV_STALE_SECONDS = 300
EXCEL_STALE_SECONDS = 600


def _safe_lock_name(name: str) -> str:
  safe = ''.join(char if char.isalnum() or char in '._-' else '_' for char in name)
  return safe[:200] or 'lock'


def _lock_path(lock_dir: Path, category: str, name: str) -> Path:
  category_dir = lock_dir / category
  category_dir.mkdir(parents=True, exist_ok=True)
  return category_dir / f'{_safe_lock_name(name)}.lock'


def _parse_lock_file(lock_path: Path) -> dict[str, str]:
  try:
    content = lock_path.read_text(encoding='utf-8')
  except OSError:
    return {}
  data: dict[str, str] = {}
  for line in content.splitlines():
    if '=' not in line:
      continue
    key, value = line.split('=', 1)
    data[key.strip()] = value.strip()
  return data


def read_lock_owner(lock_path: Path) -> str:
  data = _parse_lock_file(lock_path)
  host = data.get('host', '')
  pid = data.get('pid', '')
  if host and pid:
    return f'{host} (pid {pid})'
  if host:
    return host
  return 'outro processo'


def _is_process_alive(pid: int) -> bool:
  if pid <= 0:
    return False
  try:
    os.kill(pid, 0)
  except OSError:
    return False
  return True


def _maybe_remove_stale(lock_path: Path, stale_seconds: float) -> None:
  if not lock_path.is_file():
    return

  data = _parse_lock_file(lock_path)
  pid_text = data.get('pid', '')
  if pid_text.isdigit():
    if not _is_process_alive(int(pid_text)):
      lock_path.unlink(missing_ok=True)
      return

  try:
    age = time.time() - lock_path.stat().st_mtime
    if age > stale_seconds:
      lock_path.unlink(missing_ok=True)
  except OSError:
    return


def _write_lock_file(lock_path: Path) -> None:
  fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
  with os.fdopen(fd, 'w', encoding='utf-8') as handle:
    handle.write(f'host={socket.gethostname()}\n')
    handle.write(f'pid={os.getpid()}\n')
    handle.write(f'time={time.time()}\n')


@contextmanager
def exclusive_lock(
  lock_dir: Path,
  category: str,
  name: str,
  *,
  stale_seconds: float = DEFAULT_STALE_SECONDS,
) -> Iterator[None]:
  lock_path = _lock_path(lock_dir, category, name)
  acquired = False
  try:
    _maybe_remove_stale(lock_path, stale_seconds)
    try:
      _write_lock_file(lock_path)
    except FileExistsError as exc:
      owner = read_lock_owner(lock_path)
      raise LockNotAcquired(name, owner) from exc
    acquired = True
    yield
  finally:
    if acquired:
      lock_path.unlink(missing_ok=True)
