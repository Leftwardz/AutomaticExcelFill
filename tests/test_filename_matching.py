from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.models.schema import AppConfig, Flow
from app.models.storage import find_flow_by_filename, iter_matching_files
from app.utils.filename_matching import filename_matches_pattern, has_wildcards


class FilenameMatchingTests(unittest.TestCase):
  def test_exact_match_case_insensitive(self):
    self.assertTrue(filename_matches_pattern('Relatorio.CSV', 'relatorio.csv'))
    self.assertFalse(filename_matches_pattern('outro.csv', 'relatorio.csv'))

  def test_wildcard_prefix(self):
    self.assertTrue(filename_matches_pattern('planilha_alc_01.csv', 'planilha_alc_*'))
    self.assertTrue(filename_matches_pattern('PLANILHA_ALC_JULHO.txt', 'planilha_alc_*'))
    self.assertFalse(filename_matches_pattern('planilha_xyz_01.csv', 'planilha_alc_*'))

  def test_wildcard_with_extension(self):
    self.assertTrue(filename_matches_pattern('planilha_alc_01.csv', 'planilha_alc_*.csv'))
    self.assertFalse(filename_matches_pattern('planilha_alc_01.txt', 'planilha_alc_*.csv'))

  def test_has_wildcards(self):
    self.assertTrue(has_wildcards('planilha_*'))
    self.assertFalse(has_wildcards('planilha.csv'))


class FlowMatchingTests(unittest.TestCase):
  def test_find_flow_by_wildcard(self):
    config = AppConfig(flows=[
      Flow(name='ALC', source_filename='planilha_alc_*', excel_directory='/tmp', excel_filename='out.xlsx', headers=['A']),
      Flow(name='Outro', source_filename='vendas.csv', excel_directory='/tmp', excel_filename='v.xlsx', headers=['B']),
    ])
    flow = find_flow_by_filename(config, 'planilha_alc_20260710.csv')
    self.assertIsNotNone(flow)
    self.assertEqual(flow.name, 'ALC')

  def test_iter_matching_files_with_wildcard(self):
    with tempfile.TemporaryDirectory() as tmp:
      folder = Path(tmp)
      (folder / 'planilha_alc_01.csv').write_text('a\tb\n', encoding='utf-8')
      (folder / 'planilha_alc_02.csv').write_text('a\tb\n', encoding='utf-8')
      (folder / 'outro.csv').write_text('a\tb\n', encoding='utf-8')

      matches = list(iter_matching_files(folder, 'planilha_alc_*'))
      self.assertEqual(len(matches), 2)
      self.assertEqual({path.name for path in matches}, {'planilha_alc_01.csv', 'planilha_alc_02.csv'})

  def test_iter_matching_files_exact(self):
    with tempfile.TemporaryDirectory() as tmp:
      folder = Path(tmp)
      (folder / 'fixo.csv').write_text('a\tb\n', encoding='utf-8')
      matches = list(iter_matching_files(folder, 'fixo.csv'))
      self.assertEqual(len(matches), 1)
      self.assertEqual(matches[0].name, 'fixo.csv')


if __name__ == '__main__':
  unittest.main()
