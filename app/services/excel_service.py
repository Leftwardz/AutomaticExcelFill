from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from openpyxl.worksheet.worksheet import Worksheet

from app.services.excel_crypto import create_empty_workbook, load_workbook_from_path, save_workbook_to_path

MONTHS_PT = [
  'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
  'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro',
]


def current_month_sheet_name(when: datetime | None = None) -> str:
  when = when or datetime.now()
  return f'{MONTHS_PT[when.month - 1]} {when.year}'


def excel_full_path(directory: str, filename: str) -> Path:
  name = filename if filename.lower().endswith('.xlsx') else f'{filename}.xlsx'
  return Path(directory) / name


def read_tab_csv(path: Path) -> List[List[str]]:
  rows: List[List[str]] = []
  with open(path, encoding='utf-8-sig', newline='') as f:
    reader = csv.reader(f, delimiter='\t')
    for row in reader:
      if not row or all(not cell.strip() for cell in row):
        continue
      rows.append([cell.strip() for cell in row])
  return rows


def _sheet_is_empty(sheet: Worksheet) -> bool:
  if sheet.max_row == 1 and sheet.max_column == 1:
    value = sheet.cell(row=1, column=1).value
    return value is None or str(value).strip() == ''
  return sheet.max_row == 0


def _ensure_headers(sheet: Worksheet, headers: List[str]) -> None:
  if not headers:
    return
  if _sheet_is_empty(sheet):
    for col_index, header in enumerate(headers, start=1):
      sheet.cell(row=1, column=col_index, value=header)
    return
  existing = [str(sheet.cell(row=1, column=col).value or '').strip() for col in range(1, sheet.max_column + 1)]
  if not any(existing):
    for col_index, header in enumerate(headers, start=1):
      sheet.cell(row=1, column=col_index, value=header)


def _next_data_row(sheet: Worksheet) -> int:
  if _sheet_is_empty(sheet):
    return 2 if sheet.max_row >= 1 and sheet.cell(row=1, column=1).value else 1
  return sheet.max_row + 1


def append_csv_to_excel(
  csv_path: Path,
  excel_path: Path,
  headers: List[str],
  *,
  sheet_name: str | None = None,
  excel_password: Optional[str] = None,
) -> Tuple[str, int]:
  sheet_name = sheet_name or current_month_sheet_name()
  rows = read_tab_csv(csv_path)
  if not rows:
    raise ValueError('Arquivo CSV vazio ou sem linhas válidas.')

  excel_path.parent.mkdir(parents=True, exist_ok=True)
  if excel_path.is_file():
    workbook = load_workbook_from_path(excel_path, password=excel_password or None)
  else:
    workbook = create_empty_workbook()

  if sheet_name in workbook.sheetnames:
    sheet = workbook[sheet_name]
  else:
    sheet = workbook.create_sheet(title=sheet_name)

  _ensure_headers(sheet, headers)
  start_row = _next_data_row(sheet)
  if start_row == 1 and headers:
    start_row = 2

  for offset, row in enumerate(rows):
    target_row = start_row + offset
    for col_index, value in enumerate(row, start=1):
      sheet.cell(row=target_row, column=col_index, value=value)

  save_workbook_to_path(workbook, excel_path, password=excel_password or None)
  return sheet_name, len(rows)
