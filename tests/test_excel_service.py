from __future__ import annotations

import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from openpyxl import load_workbook

from app.models.schema import Flow
from app.services.excel_service import append_csv_to_excel, current_month_sheet_name, read_tab_csv


class ExcelServiceTests(unittest.TestCase):
  def test_current_month_sheet_name(self):
    when = datetime(2026, 7, 10)
    self.assertEqual(current_month_sheet_name(when), 'Julho 2026')

  def test_append_creates_sheet_and_headers(self):
    with tempfile.TemporaryDirectory() as tmp:
      csv_path = Path(tmp) / 'dados.csv'
      csv_path.write_text('A\tB\tC\n1\t2\t3\n4\t5\t6\n', encoding='utf-8')
      excel_path = Path(tmp) / 'saida.xlsx'
      headers = ['Col1', 'Col2', 'Col3']
      sheet_name, count = append_csv_to_excel(csv_path, excel_path, headers, sheet_name='Julho 2026')
      self.assertEqual(sheet_name, 'Julho 2026')
      self.assertEqual(count, 3)
      workbook = load_workbook(excel_path)
      sheet = workbook['Julho 2026']
      self.assertEqual(sheet.cell(row=1, column=1).value, 'Col1')
      self.assertEqual(sheet.cell(row=2, column=1).value, 'A')
      self.assertEqual(sheet.cell(row=4, column=3).value, '6')

  def test_append_to_existing_sheet(self):
    with tempfile.TemporaryDirectory() as tmp:
      csv_path = Path(tmp) / 'dados.csv'
      csv_path.write_text('X\tY\n', encoding='utf-8')
      excel_path = Path(tmp) / 'saida.xlsx'
      append_csv_to_excel(csv_path, excel_path, ['Col1', 'Col2'], sheet_name='Julho 2026')
      csv_path.write_text('N\tM\n', encoding='utf-8')
      append_csv_to_excel(csv_path, excel_path, ['Col1', 'Col2'], sheet_name='Julho 2026')
      workbook = load_workbook(excel_path)
      sheet = workbook['Julho 2026']
      self.assertEqual(sheet.max_row, 3)
      self.assertEqual(sheet.cell(row=3, column=1).value, 'N')


class FlowTests(unittest.TestCase):
  def test_roundtrip(self):
    flow = Flow(
      name='Teste',
      source_filename='a.csv',
      excel_directory='/tmp',
      excel_filename='out.xlsx',
      headers=['A', 'B'],
    )
    restored = Flow.from_dict(flow.to_dict())
    self.assertEqual(restored.name, flow.name)
    self.assertEqual(restored.headers, flow.headers)


if __name__ == '__main__':
  unittest.main()
