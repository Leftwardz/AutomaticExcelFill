from __future__ import annotations

import unittest

from app.ui.log_view import (
  format_shared_log_entry,
  level_entry_tag,
  parse_job_log_line,
  session_log_group_key,
  shared_log_entry_tag,
)


class LogViewTests(unittest.TestCase):
  def test_parse_job_log_line(self):
    line = '2026-07-12 10:00:00\tPC1\tSUCCESS\tVendas\tplanilha.csv\tok'
    entry = parse_job_log_line(line)
    assert entry is not None
    self.assertEqual(entry.flow_name, 'Vendas')
    self.assertEqual(entry.source_file, 'planilha.csv')
    self.assertFalse(entry.is_error)

  def test_parse_job_log_line_error(self):
    line = '2026-07-12 10:00:00\tPC1\tERROR\tVendas\tplanilha.csv\tfalhou'
    entry = parse_job_log_line(line)
    assert entry is not None
    self.assertTrue(entry.is_error)

  def test_format_shared_log_entry(self):
    entry = parse_job_log_line('2026-07-12 10:00:00\tPC1\tSUCCESS\tVendas\tplanilha.csv\tok')
    assert entry is not None
    rendered = format_shared_log_entry(entry)
    self.assertIn('Vendas', rendered)
    self.assertIn('planilha.csv', rendered)
    self.assertIn('ok', rendered)

  def test_session_log_group_key_extracts_flow(self):
    key = session_log_group_key('success', '[Vendas] planilha.csv: ok')
    self.assertEqual(key, ('success', 'Vendas', 'planilha.csv'))

  def test_level_entry_tag_colors_by_level(self):
    self.assertEqual(level_entry_tag('info'), 'entry_info')
    self.assertEqual(level_entry_tag('success'), 'entry_success')
    self.assertEqual(level_entry_tag('error'), 'entry_error')

  def test_shared_log_entry_tag(self):
    success = parse_job_log_line('2026-07-12 10:00:00\tPC1\tSUCCESS\tVendas\tplanilha.csv\tok')
    info = parse_job_log_line('2026-07-12 10:00:00\tPC1\tINFO\tVendas\t-\tprocessando')
    error = parse_job_log_line('2026-07-12 10:00:00\tPC1\tERROR\tVendas\tplanilha.csv\tfalhou')
    assert success and info and error
    self.assertEqual(shared_log_entry_tag(success), 'entry_success')
    self.assertEqual(shared_log_entry_tag(info), 'entry_info')
    self.assertEqual(shared_log_entry_tag(error), 'entry_error')


if __name__ == '__main__':
  unittest.main()
