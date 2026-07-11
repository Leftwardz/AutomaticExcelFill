from __future__ import annotations

import os
import socket
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


class LockNotAcquired(Exception):
  def __init__(self, resource: str):
    self.resource = resource
    super().__init__(f'Recurso já em uso por outro processo: {resource}')


LOCK_DIR_NAME = '.automatic_fill_locks'
DEFAULT_STALE_SECONDS = 1800


def locks_root(watch_folder: str | Path) -> Path:
  return Path(watch_folder) / LOCK_DIR_NAME


def _safe_lock_name(name: str) -> str:
  safe = ''.join(char if char.isalnum() or char in '._-' else '_' for char in name)
  return safe[:200] or 'lock'


def _lock_path(lock_dir: Path, category: str, name: str) -> Path:
  category_dir = lock_dir / category
  category_dir.mkdir(parents=True, exist_ok=True)
  return category_dir / f'{_safe_lock_name(name)}.lock'


def _maybe_remove_stale(lock_path: Path, stale_seconds: float) -> None:
  if not lock_path.is_file():
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
      raise LockNotAcquired(name) from exc
    acquired = True
    yield
  finally:
    if acquired:
      lock_path.unlink(missing_ok=True)
