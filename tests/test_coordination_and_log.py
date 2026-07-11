from __future__ import annotations

import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from app.models.schema import AppConfig
from app.services.coordination import LockNotAcquired, exclusive_lock
from app.utils.app_data_paths import locks_root
from app.services.job_log import append_job_log, resolve_shared_log_path


class CoordinationTests(unittest.TestCase):
  def test_exclusive_lock_blocks_second_acquirer(self):
    with tempfile.TemporaryDirectory() as tmp:
      lock_dir = Path(tmp)
      with exclusive_lock(lock_dir, 'csv', 'dados.csv'):
        with self.assertRaises(LockNotAcquired):
          with exclusive_lock(lock_dir, 'csv', 'dados.csv'):
            pass

  def test_lock_released_after_context(self):
    with tempfile.TemporaryDirectory() as tmp:
      lock_dir = Path(tmp)
      with exclusive_lock(lock_dir, 'excel', 'planilha'):
        pass
      with exclusive_lock(lock_dir, 'excel', 'planilha'):
        pass


class JobLogTests(unittest.TestCase):
  def test_resolve_shared_log_path_defaults_to_watch_folder(self):
    config = AppConfig(watch_folder='/rede/pasta')
    self.assertEqual(
      resolve_shared_log_path(config),
      Path('/rede/pasta/_AutomaticExcelFill/automatic_fill.log'),
    )

  def test_resolve_shared_log_path_custom_file(self):
    config = AppConfig(shared_log_path='/rede/logs/jobs.log')
    self.assertEqual(resolve_shared_log_path(config), Path('/rede/logs/jobs.log'))

  def test_append_job_log_writes_tab_separated_line(self):
    with tempfile.TemporaryDirectory() as tmp:
      log_path = Path(tmp) / 'automatic_fill.log'
      append_job_log(log_path, 'error', 'Linha duplicada', flow_name='Fluxo A', source_file='a.csv')
      content = log_path.read_text(encoding='utf-8')
      self.assertIn('ERROR', content)
      self.assertIn('Fluxo A', content)
      self.assertIn('a.csv', content)
      self.assertIn('Linha duplicada', content)


if __name__ == '__main__':
  unittest.main()
