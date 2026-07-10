from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional, Tuple

from app.services.excel_crypto import ExcelPasswordError, is_encrypted_excel
from app.services.excel_service import current_month_sheet_name, read_tab_csv

XL_FILE_FORMAT_XLSB = 50


def _require_windows_excel() -> None:
  if sys.platform != 'win32':
    raise RuntimeError(
      'Arquivos .xlsb exigem Windows com Microsoft Excel instalado para gravação.',
    )
  try:
    import win32com.client  # type: ignore  # noqa: F401
  except ImportError as exc:
    raise RuntimeError(
      'Arquivos .xlsb exigem pywin32 e Microsoft Excel no Windows.',
    ) from exc


def _append_via_win32com(
  excel_path: Path,
  sheet_name: str,
  headers: List[str],
  data_rows: List[List[str]],
  password: Optional[str] = None,
) -> None:
  import win32com.client  # type: ignore

  excel = win32com.client.DispatchEx('Excel.Application')
  excel.Visible = False
  excel.DisplayAlerts = False
  workbook = None
  created_new = False
  try:
    if excel_path.is_file():
      workbook = excel.Workbooks.Open(
        str(excel_path.resolve()),
        UpdateLinks=0,
        ReadOnly=False,
        Password=password or '',
      )
    else:
      workbook = excel.Workbooks.Add()
      workbook.SaveAs(str(excel_path.resolve()), FileFormat=XL_FILE_FORMAT_XLSB)
      created_new = True

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
      workbook.Close(SaveChanges=not created_new)
    excel.Quit()


def append_csv_to_xlsb(
  csv_path: Path,
  excel_path: Path,
  headers: List[str],
  *,
  sheet_name: str | None = None,
  excel_password: Optional[str] = None,
) -> Tuple[str, int]:
  _require_windows_excel()

  sheet_name = sheet_name or current_month_sheet_name()
  data_rows = read_tab_csv(csv_path)
  if not data_rows:
    raise ValueError('Arquivo CSV vazio ou sem linhas válidas.')

  excel_path.parent.mkdir(parents=True, exist_ok=True)

  if excel_path.is_file() and is_encrypted_excel(excel_path) and not excel_password:
    raise ExcelPasswordError(
      'O arquivo Excel está protegido por senha. Informe a senha no cadastro do fluxo.',
    )

  _append_via_win32com(excel_path, sheet_name, headers, data_rows, excel_password)
  return sheet_name, len(data_rows)
