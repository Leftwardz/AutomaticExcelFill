from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.utils.protection import hash_password

from app.services.excel_crypto import (
  ExcelPasswordError,
  is_encrypted_excel,
  load_workbook_from_path,
  read_file_sharing_password_hash,
  save_workbook_to_path,
)
from app.services.excel_service import append_csv_to_excel


class ExcelPasswordTests(unittest.TestCase):
  def test_windows_modify_password_in_workbook_xml(self):
    with tempfile.TemporaryDirectory() as tmp:
      path = Path(tmp) / 'mod.xlsx'
      workbook = Workbook()
      workbook.active['A1'] = 'x'
      save_workbook_to_path(workbook, path, password='mod123')

      self.assertFalse(is_encrypted_excel(path))
      self.assertEqual(read_file_sharing_password_hash(path), hash_password('mod123'))
      loaded = load_workbook_from_path(path)
      self.assertEqual(loaded.active['A1'].value, 'x')

  def test_append_new_file_with_modify_password(self):
    with tempfile.TemporaryDirectory() as tmp:
      folder = Path(tmp)
      excel_path = folder / 'saida.xlsx'
      csv_path = folder / 'entrada.csv'
      csv_path.write_text('Item\t10\n', encoding='utf-8')

      sheet_name, count = append_csv_to_excel(
        csv_path,
        excel_path,
        ['Nome', 'Qtd'],
        excel_password='gravar123',
      )
      self.assertEqual(count, 1)
      self.assertEqual(sheet_name, 'Julho 2026')
      self.assertEqual(read_file_sharing_password_hash(excel_path), hash_password('gravar123'))

      loaded = load_workbook(excel_path)
      self.assertEqual(loaded['Julho 2026'].cell(row=2, column=1).value, 'Item')

  def test_append_again_with_modify_password(self):
    with tempfile.TemporaryDirectory() as tmp:
      folder = Path(tmp)
      excel_path = folder / 'saida.xlsx'
      csv_path = folder / 'entrada.csv'
      csv_path.write_text('A\t1\n', encoding='utf-8')
      append_csv_to_excel(csv_path, excel_path, ['Nome', 'Qtd'], excel_password='gravar123')

      csv_path.write_text('B\t2\n', encoding='utf-8')
      append_csv_to_excel(csv_path, excel_path, ['Nome', 'Qtd'], excel_password='gravar123')

      loaded = load_workbook(excel_path)
      self.assertEqual(loaded['Julho 2026'].cell(row=3, column=1).value, 'B')
      self.assertEqual(read_file_sharing_password_hash(excel_path), hash_password('gravar123'))

  def test_legacy_encrypted_file_still_needs_open_password(self):
    with tempfile.TemporaryDirectory() as tmp:
      path = Path(tmp) / 'legado.xlsx'
      workbook = Workbook()
      workbook.active['A1'] = 'x'

      import io
      from msoffcrypto.format.ooxml import OOXMLFile

      plain = io.BytesIO()
      workbook.save(plain)
      plain.seek(0)
      encrypted = io.BytesIO()
      OOXMLFile(plain).encrypt('abrir123', encrypted)
      path.write_bytes(encrypted.getvalue())

      self.assertTrue(is_encrypted_excel(path))
      with self.assertRaises(ExcelPasswordError):
        load_workbook_from_path(path)
      loaded = load_workbook_from_path(path, password='abrir123')
      self.assertEqual(loaded.active['A1'].value, 'x')


if __name__ == '__main__':
  unittest.main()
