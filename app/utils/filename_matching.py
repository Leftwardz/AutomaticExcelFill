from __future__ import annotations

import fnmatch


def has_wildcards(pattern: str) -> bool:
  return any(char in pattern for char in ('*', '?', '['))


def filename_matches_pattern(filename: str, pattern: str) -> bool:
  """Compara nome de arquivo com padrão exato ou wildcard (*, ?, [])."""
  filename = filename.strip()
  pattern = pattern.strip()
  if not filename or not pattern:
    return False
  if has_wildcards(pattern):
    return fnmatch.fnmatch(filename.lower(), pattern.lower())
  return filename.lower() == pattern.lower()
