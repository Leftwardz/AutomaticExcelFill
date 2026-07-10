from __future__ import annotations

import re
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, List, Optional

from app.services.excel_crypto import is_encrypted_excel
from app.services.excel_service import current_month_sheet_name


def parse_headers_from_text(text: str) -> List[str]:
  """Interpreta linha(s) colada(s) do Excel ou texto separado por tab/;/|."""
  if not text or not str(text).strip():
    return []

  lines = [line.strip() for line in str(text).splitlines() if line.strip()]
  if not lines:
    return []

  candidate = max(lines, key=len)
  if '\t' in candidate:
    parts = candidate.split('\t')
  elif ';' in candidate:
    parts = candidate.split(';')
  elif '|' in candidate:
    parts = candidate.split('|')
  else:
    parts = re.split(r'\s{2,}', candidate)

  return [part.strip() for part in parts if part and str(part).strip()]


def _require_calamine():
  try:
    from python_calamine import CalamineWorkbook
  except ImportError as exc:
    raise RuntimeError('Dependência python-calamine não instalada.') from exc
  return CalamineWorkbook


@contextmanager
def _open_excel_path(path: Path, password: Optional[str] = None) -> Iterator[Path]:
  if not path.is_file():
    raise FileNotFoundError(str(path))

  if not password or not is_encrypted_excel(path):
    yield path
    return

  from app.services.excel_crypto import decrypt_office_file_to_path

  with tempfile.TemporaryDirectory() as tmp:
    decrypted = Path(tmp) / f'decrypted{path.suffix}'
    decrypt_office_file_to_path(path, decrypted, password)
    yield decrypted


def list_excel_sheets(path: Path, password: Optional[str] = None) -> List[str]:
  CalamineWorkbook = _require_calamine()
  with _open_excel_path(path, password) as work_path:
    workbook = CalamineWorkbook.from_path(str(work_path))
    return list(workbook.sheet_names)


def read_headers_from_excel(
  excel_path: Path,
  *,
  password: Optional[str] = None,
  sheet_name: Optional[str] = None,
) -> List[str]:
  CalamineWorkbook = _require_calamine()
  with _open_excel_path(excel_path, password) as work_path:
    workbook = CalamineWorkbook.from_path(str(work_path))
    sheet_names = list(workbook.sheet_names)
    if not sheet_names:
      return []

    target_sheet = (sheet_name or '').strip() or current_month_sheet_name()
    if target_sheet not in sheet_names:
      target_sheet = sheet_names[0]

    rows = workbook.get_sheet_by_name(target_sheet).to_python()
    if not rows:
      return []
    return [str(cell).strip() for cell in rows[0] if cell is not None and str(cell).strip()]


def resolve_header_source_path(flow) -> Optional[Path]:
  path_value = (getattr(flow, 'header_source_path', '') or '').strip()
  if not path_value:
    return None
  path = Path(path_value)
  return path if path.is_file() else None
