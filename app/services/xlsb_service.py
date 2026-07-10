from __future__ import annotations

import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, List, Optional, Tuple

from app.services.excel_crypto import ExcelPasswordError, decrypt_office_file_to_path, is_encrypted_excel
from app.services.excel_service import current_month_sheet_name, read_tab_csv


def _require_xlspy():
  try:
    from xlspy import ExcelReader, XlsbWriter
  except ImportError as exc:
    raise RuntimeError('Dependência xlspy não instalada.') from exc
  return ExcelReader, XlsbWriter


@contextmanager
def _readable_xlsb_path(path: Path, password: Optional[str] = None) -> Iterator[Path]:
  if not path.is_file():
    raise FileNotFoundError(str(path))
  if password and is_encrypted_excel(path):
    with tempfile.TemporaryDirectory() as tmp:
      decrypted = Path(tmp) / f'work{path.suffix}'
      decrypt_office_file_to_path(path, decrypted, password)
      yield decrypted
    return
  yield path


def _sheet_rows_empty(rows: List[List]) -> bool:
  if not rows:
    return True
  return not any(
    any(str(cell).strip() for cell in row if cell is not None)
    for row in rows
  )


def _ensure_headers_rows(rows: List[List], headers: List[str]) -> None:
  if not headers:
    return
  if _sheet_rows_empty(rows):
    rows.clear()
    rows.append(list(headers))
    return
  first = rows[0]
  if not any(str(cell).strip() for cell in first if cell is not None):
    rows[0] = list(headers)


def _append_via_win32com(
  excel_path: Path,
  sheet_name: str,
  headers: List[str],
  data_rows: List[List[str]],
  password: Optional[str] = None,
) -> None:
  if sys.platform != 'win32':
    raise RuntimeError(
      'Arquivo .xlsb protegido por senha requer Windows com Microsoft Excel instalado.',
    )
  try:
    import win32com.client  # type: ignore
  except ImportError as exc:
    raise RuntimeError(
      'Arquivo .xlsb protegido por senha requer pywin32 e Microsoft Excel no Windows.',
    ) from exc

  excel = win32com.client.DispatchEx('Excel.Application')
  excel.Visible = False
  excel.DisplayAlerts = False
  workbook = None
  try:
    workbook = excel.Workbooks.Open(
      str(excel_path.resolve()),
      UpdateLinks=0,
      ReadOnly=False,
      Password=password or '',
    )
    try:
      worksheet = workbook.Worksheets(sheet_name)
    except Exception:
      worksheet = workbook.Worksheets.Add(After=workbook.Worksheets(workbook.Worksheets.Count))
      worksheet.Name = sheet_name

    used_last_row = worksheet.Cells(worksheet.Rows.Count, 1).End(-4162).Row
    first_cell = str(worksheet.Cells(1, 1).Value or '').strip()
    if used_last_row < 1 or (used_last_row == 1 and not first_cell):
      start_row = 1
      if headers:
        for col_index, header in enumerate(headers, start=1):
          worksheet.Cells(1, col_index).Value = header
        start_row = 2
    else:
      if headers and not first_cell:
        for col_index, header in enumerate(headers, start=1):
          worksheet.Cells(1, col_index).Value = header
      start_row = max(used_last_row, 1) + 1
      if start_row == 2 and not first_cell and not headers:
        start_row = 1

    if data_rows:
      col_count = max(len(row) for row in data_rows)
      target_range = worksheet.Range(
        worksheet.Cells(start_row, 1),
        worksheet.Cells(start_row + len(data_rows) - 1, col_count),
      )
      target_range.Value = data_rows

    workbook.Save()
  finally:
    if workbook is not None:
      workbook.Close(SaveChanges=True)
    excel.Quit()


def _rewrite_xlsb(path: Path, sheets_data: dict[str, List[List]]) -> None:
  ExcelReader, XlsbWriter = _require_xlspy()
  with XlsbWriter(str(path)) as writer:
    for name, rows in sheets_data.items():
      writer.add_sheet(name)
      writer.write_sheet(rows)


def append_csv_to_xlsb(
  csv_path: Path,
  excel_path: Path,
  headers: List[str],
  *,
  sheet_name: str | None = None,
  excel_password: Optional[str] = None,
) -> Tuple[str, int]:
  sheet_name = sheet_name or current_month_sheet_name()
  data_rows = read_tab_csv(csv_path)
  if not data_rows:
    raise ValueError('Arquivo CSV vazio ou sem linhas válidas.')

  excel_path.parent.mkdir(parents=True, exist_ok=True)

  if excel_path.is_file() and is_encrypted_excel(excel_path):
    if not excel_password:
      raise ExcelPasswordError(
        'O arquivo Excel está protegido por senha. Informe a senha no cadastro do fluxo.',
      )
    _append_via_win32com(excel_path, sheet_name, headers, data_rows, excel_password)
    return sheet_name, len(data_rows)

  ExcelReader, _XlsbWriter = _require_xlspy()
  sheets_data: dict[str, List[List]] = {}

  if excel_path.is_file():
    with _readable_xlsb_path(excel_path, excel_password) as work_path:
      with ExcelReader(str(work_path)) as reader:
        for name in reader.get_sheet_names():
          sheets_data[name] = [list(row) for row in reader.read_all(name)]

  if sheet_name not in sheets_data:
    sheets_data[sheet_name] = []

  sheet_rows = sheets_data[sheet_name]
  _ensure_headers_rows(sheet_rows, headers)
  sheet_rows.extend(data_rows)
  _rewrite_xlsb(excel_path, sheets_data)
  return sheet_name, len(data_rows)
