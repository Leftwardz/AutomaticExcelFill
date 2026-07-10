from __future__ import annotations

import sys
import unittest
from pathlib import Path

from app.services.excel_service import append_csv_to_excel
from app.services.header_import import read_headers_from_excel
from app.utils.excel_paths import excel_full_path, normalize_excel_filename

FIXTURE_XLSB = Path(__file__).resolve().parent / 'fixtures' / 'modelo.xlsb'


class XlsbSupportTests(unittest.TestCase):
  def test_normalize_xlsb_filename(self):
    self.assertEqual(normalize_excel_filename('planilha'), 'planilha.xlsx')
    self.assertEqual(normalize_excel_filename('planilha.xlsb'), 'planilha.xlsb')

  def test_excel_full_path_keeps_xlsb(self):
    path = excel_full_path('/tmp', 'dados.xlsb')
    self.assertEqual(path.name, 'dados.xlsb')

  @unittest.skipUnless(FIXTURE_XLSB.is_file(), 'fixture xlsb ausente')
  def test_read_headers_from_xlsb(self):
    headers = read_headers_from_excel(FIXTURE_XLSB, sheet_name='Julho 2026')
    self.assertEqual(headers, ['Data', 'Produto', 'Qtd'])

  @unittest.skipUnless(sys.platform == 'win32', 'gravação xlsb requer Windows')
  def test_append_csv_to_xlsb(self):
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
      folder = Path(tmp)
      excel_path = folder / 'saida.xlsb'
      csv_path = folder / 'entrada.csv'
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
