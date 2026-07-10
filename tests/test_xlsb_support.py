from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from xlspy import XlsbWriter

from app.services.excel_service import append_csv_to_excel
from app.services.header_import import read_headers_from_excel
from app.utils.excel_paths import excel_full_path, normalize_excel_filename


class XlsbSupportTests(unittest.TestCase):
  def test_normalize_xlsb_filename(self):
    self.assertEqual(normalize_excel_filename('planilha'), 'planilha.xlsx')
    self.assertEqual(normalize_excel_filename('planilha.xlsb'), 'planilha.xlsb')

  def test_excel_full_path_keeps_xlsb(self):
    path = excel_full_path('/tmp', 'dados.xlsb')
    self.assertEqual(path.name, 'dados.xlsb')

  def test_read_headers_from_xlsb(self):
    with tempfile.TemporaryDirectory() as tmp:
      path = Path(tmp) / 'modelo.xlsb'
      with XlsbWriter(str(path)) as writer:
        writer.add_sheet('Julho 2026')
        writer.write_sheet([['Data', 'Produto', 'Qtd'], ['1', 'A', '2']])
      headers = read_headers_from_excel(path, sheet_name='Julho 2026')
      self.assertEqual(headers, ['Data', 'Produto', 'Qtd'])

  def test_append_csv_to_xlsb(self):
    with tempfile.TemporaryDirectory() as tmp:
      folder = Path(tmp)
      excel_path = folder / 'saida.xlsb'
      csv_path = folder / 'entrada.csv'

      with XlsbWriter(str(excel_path)) as writer:
        writer.add_sheet('Julho 2026')
        writer.write_sheet([['Nome', 'Qtd'], ['A', '1']])

      csv_path.write_text('B\t2\n', encoding='utf-8')
      sheet_name, count = append_csv_to_excel(
        csv_path,
        excel_path,
        ['Nome', 'Qtd'],
        sheet_name='Julho 2026',
      )
      self.assertEqual(sheet_name, 'Julho 2026')
      self.assertEqual(count, 1)
      headers = read_headers_from_excel(excel_path, sheet_name='Julho 2026')
      self.assertEqual(headers, ['Nome', 'Qtd'])


if __name__ == '__main__':
  unittest.main()
