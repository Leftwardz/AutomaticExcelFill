from __future__ import annotations

from pathlib import Path

SUPPORTED_EXCEL_EXTENSIONS = ('.xlsx', '.xlsm', '.xlsb')
DEFAULT_EXCEL_EXTENSION = '.xlsx'

EXCEL_FILETYPES = [
  ('Excel', '*.xlsx;*.xlsm;*.xlsb'),
  ('Excel binário', '*.xlsb'),
  ('Excel XML', '*.xlsx;*.xlsm'),
  ('Todos', '*.*'),
]


def normalize_excel_filename(filename: str, default_ext: str = DEFAULT_EXCEL_EXTENSION) -> str:
  name = (filename or '').strip()
  if not name:
    return f'planilha{default_ext}'
  lower = name.lower()
  for ext in SUPPORTED_EXCEL_EXTENSIONS:
    if lower.endswith(ext):
      return name
  return f'{name}{default_ext}'


def excel_full_path(directory: str, filename: str) -> Path:
  return Path(directory) / normalize_excel_filename(filename)


def excel_format(path: Path) -> str:
  suffix = path.suffix.lower()
  if suffix == '.xlsb':
    return 'xlsb'
  return 'xlsx'
