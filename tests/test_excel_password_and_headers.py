from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook, load_workbook

from app.services.excel_crypto import (
  ExcelPasswordError,
  is_encrypted_excel,
  load_workbook_from_path,
  save_workbook_to_path,
)
from app.services.excel_service import append_csv_to_excel
from app.services.header_import import parse_headers_from_text, read_headers_from_excel


class HeaderImportTests(unittest.TestCase):
  def test_parse_tab_separated(self):
    headers = parse_headers_from_text('Col A\tCol B\tCol C')
    self.assertEqual(headers, ['Col A', 'Col B', 'Col C'])

  def test_parse_multiline_uses_longest(self):
    headers = parse_headers_from_text('A\tB\nCol1\tCol2\tCol3')
    self.assertEqual(headers, ['Col1', 'Col2', 'Col3'])

  def test_read_headers_from_excel_file(self):
    with tempfile.TemporaryDirectory() as tmp:
      path = Path(tmp) / 'modelo.xlsx'
      workbook = Workbook()
      sheet = workbook.active
      sheet.title = 'Julho 2026'
      sheet.cell(row=1, column=1, value='Data')
      sheet.cell(row=1, column=2, value='Valor')
      workbook.save(path)

      headers = read_headers_from_excel(path, sheet_name='Julho 2026')
      self.assertEqual(headers, ['Data', 'Valor'])


class ExcelCryptoTests(unittest.TestCase):
  def test_encrypt_decrypt_roundtrip(self):
    with tempfile.TemporaryDirectory() as tmp:
      path = Path(tmp) / 'segredo.xlsx'
      workbook = Workbook()
      sheet = workbook.active
      sheet.title = 'Julho 2026'
      sheet.cell(row=1, column=1, value='A')
      sheet.cell(row=2, column=1, value='1')
      save_workbook_to_path(workbook, path, password='teste123')

      self.assertTrue(is_encrypted_excel(path))
      loaded = load_workbook_from_path(path, password='teste123')
      self.assertEqual(loaded['Julho 2026'].cell(row=2, column=1).value, '1')

  def test_wrong_password_raises(self):
    with tempfile.TemporaryDirectory() as tmp:
      path = Path(tmp) / 'segredo.xlsx'
      workbook = Workbook()
      save_workbook_to_path(workbook, path, password='certa')
      with self.assertRaises(ExcelPasswordError):
        load_workbook_from_path(path, password='errada')

  def test_append_to_encrypted_excel(self):
    with tempfile.TemporaryDirectory() as tmp:
      folder = Path(tmp)
      excel_path = folder / 'dados.xlsx'
      csv_path = folder / 'entrada.csv'

      workbook = Workbook()
      sheet = workbook.active
      sheet.title = 'Julho 2026'
      sheet.cell(row=1, column=1, value='Nome')
      sheet.cell(row=1, column=2, value='Qtd')
      save_workbook_to_path(workbook, excel_path, password='abc')

      csv_path.write_text('Item\t10\n', encoding='utf-8')
      sheet_name, count = append_csv_to_excel(
        csv_path,
        excel_path,
        ['Nome', 'Qtd'],
        sheet_name='Julho 2026',
        excel_password='abc',
      )
      self.assertEqual(count, 1)
      self.assertEqual(sheet_name, 'Julho 2026')

      loaded = load_workbook_from_path(excel_path, password='abc')
      self.assertEqual(loaded['Julho 2026'].cell(row=2, column=1).value, 'Item')


if __name__ == '__main__':
  unittest.main()
