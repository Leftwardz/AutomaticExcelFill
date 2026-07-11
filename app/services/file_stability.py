from __future__ import annotations

import time
from pathlib import Path


def wait_for_file_stable(
  path: Path,
  *,
  stable_seconds: float = 2.0,
  timeout: float = 60.0,
  poll_interval: float = 0.5,
) -> bool:
  if not path.is_file():
    return False

  deadline = time.time() + timeout
  last_size = -1
  stable_since: float | None = None

  while time.time() < deadline:
    try:
      stat = path.stat()
    except OSError:
      time.sleep(poll_interval)
      continue

    size = stat.st_size
    if size == last_size:
      if stable_since is None:
        stable_since = time.time()
      elif time.time() - stable_since >= stable_seconds:
        return True
    else:
      last_size = size
      stable_since = None

    time.sleep(poll_interval)

  return False
