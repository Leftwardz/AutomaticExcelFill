from __future__ import annotations

import csv
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional, Tuple

from openpyxl.styles import PatternFill
from openpyxl.worksheet.worksheet import Worksheet

from app.services.excel_crypto import create_empty_workbook, load_workbook_from_path, save_workbook_to_path

META_SHEET_NAME = '__AEF__'
ROW_FILL_WHITE = PatternFill(fill_type='solid', fgColor='FFFFFF')
ROW_FILL_PURPLE = PatternFill(fill_type='solid', fgColor='E9D5FF')
ROW_FILLS = (ROW_FILL_WHITE, ROW_FILL_PURPLE)

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


def _ensure_meta_sheet(workbook) -> Worksheet:
  if META_SHEET_NAME in workbook.sheetnames:
    return workbook[META_SHEET_NAME]
  sheet = workbook.create_sheet(title=META_SHEET_NAME)
  sheet.sheet_state = 'hidden'
  sheet.cell(row=1, column=1, value='sheet_name')
  sheet.cell(row=1, column=2, value='last_date')
  sheet.cell(row=1, column=3, value='color_index')
  return sheet


def _parse_meta_date(value) -> date | None:
  if value is None:
    return None
  if isinstance(value, datetime):
    return value.date()
  if isinstance(value, date):
    return value
  text = str(value).strip()
  if not text:
    return None
  return date.fromisoformat(text)


def _read_day_color_state(meta_sheet: Worksheet, sheet_name: str) -> Tuple[date | None, int]:
  for row_index in range(2, meta_sheet.max_row + 1):
    if str(meta_sheet.cell(row=row_index, column=1).value or '').strip() != sheet_name:
      continue
    last_date = _parse_meta_date(meta_sheet.cell(row=row_index, column=2).value)
    color_index = int(meta_sheet.cell(row=row_index, column=3).value or 0)
    return last_date, 0 if color_index not in (0, 1) else color_index
  return None, 0


def _write_day_color_state(meta_sheet: Worksheet, sheet_name: str, process_date: date, color_index: int) -> None:
  for row_index in range(2, meta_sheet.max_row + 1):
    if str(meta_sheet.cell(row=row_index, column=1).value or '').strip() == sheet_name:
      meta_sheet.cell(row=row_index, column=2, value=process_date.isoformat())
      meta_sheet.cell(row=row_index, column=3, value=color_index)
      return
  next_row = max(meta_sheet.max_row, 1) + 1
  meta_sheet.cell(row=next_row, column=1, value=sheet_name)
  meta_sheet.cell(row=next_row, column=2, value=process_date.isoformat())
  meta_sheet.cell(row=next_row, column=3, value=color_index)


def _resolve_row_color_index(last_date: date | None, current_date: date, current_index: int) -> int:
  if last_date is None:
    return 0
  if last_date == current_date:
    return current_index
  return 1 - current_index


def _row_fill_column_count(sheet: Worksheet, headers: List[str], rows: List[List[str]]) -> int:
  max_cols = sheet.max_column
  if headers:
    max_cols = max(max_cols, len(headers))
  for row in rows:
    max_cols = max(max_cols, len(row))
  return max(max_cols, 1)


def _apply_row_fill(sheet: Worksheet, row_index: int, fill: PatternFill, column_count: int) -> None:
  for col_index in range(1, column_count + 1):
    sheet.cell(row=row_index, column=col_index).fill = fill


def append_csv_to_excel(
  csv_path: Path,
  excel_path: Path,
  headers: List[str],
  *,
  sheet_name: str | None = None,
  excel_password: Optional[str] = None,
  processed_on: datetime | None = None,
) -> Tuple[str, int]:
  sheet_name = sheet_name or current_month_sheet_name()
  process_date = (processed_on or datetime.now()).date()
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

  meta_sheet = _ensure_meta_sheet(workbook)
  last_date, color_index = _read_day_color_state(meta_sheet, sheet_name)
  color_index = _resolve_row_color_index(last_date, process_date, color_index)
  row_fill = ROW_FILLS[color_index]
  fill_column_count = _row_fill_column_count(sheet, headers, rows)

  for offset, row in enumerate(rows):
    target_row = start_row + offset
    for col_index, value in enumerate(row, start=1):
      sheet.cell(row=target_row, column=col_index, value=value)
    _apply_row_fill(sheet, target_row, row_fill, fill_column_count)

  _write_day_color_state(meta_sheet, sheet_name, process_date, color_index)

  save_workbook_to_path(workbook, excel_path, password=excel_password or None)
  return sheet_name, len(rows)
