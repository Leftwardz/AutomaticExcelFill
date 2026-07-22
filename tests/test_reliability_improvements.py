from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from openpyxl import Workbook

from app.models.schema import AppConfig, normalize_cutoff_hour
from app.services.coordination import LockNotAcquired, exclusive_lock
from app.services.excel_crypto import save_workbook_to_path
from app.services.excel_service import read_tab_csv
from app.services.file_stability import wait_for_file_stable
from app.services.file_watcher import _CsvHandler
from app.services.job_log import append_job_log, read_job_log_tail
from app.models.storage import load_config, read_shared_config, save_config
from app.utils.app_data_paths import (
  APP_DATA_DIR_NAME,
  app_data_dir,
  locks_root,
  shared_config_path,
)
from app.utils.network_paths import is_likely_network_path, is_unc_path


class FileStabilityTests(unittest.TestCase):
  def test_wait_for_file_stable_when_size_is_constant(self):
    with tempfile.TemporaryDirectory() as tmp:
      path = Path(tmp) / 'dados.csv'
      path.write_text('a\tb\n', encoding='utf-8')
      self.assertTrue(wait_for_file_stable(path, stable_seconds=0.2, timeout=2))


class CutoffHourConfigTests(unittest.TestCase):
  def test_normalize_cutoff_hour_clamps_values(self):
    self.assertEqual(normalize_cutoff_hour(19), 19)
    self.assertEqual(normalize_cutoff_hour(-1), 0)
    self.assertEqual(normalize_cutoff_hour(30), 23)
    self.assertEqual(normalize_cutoff_hour('abc'), 19)

  def test_app_config_persists_cutoff_hour(self):
    config = AppConfig.from_dict({'row_color_cutoff_hour': 20})
    self.assertEqual(config.row_color_cutoff_hour, 20)
    self.assertEqual(config.to_dict()['row_color_cutoff_hour'], 20)


class NetworkPathTests(unittest.TestCase):
  def test_unc_path_is_network(self):
    self.assertTrue(is_unc_path('\\\\servidor\\pasta'))
    self.assertTrue(is_likely_network_path('\\\\servidor\\pasta'))

  def test_local_path_is_not_network(self):
    self.assertFalse(is_likely_network_path('/tmp/pasta'))
    self.assertFalse(is_likely_network_path('C:\\dados'))


class RescanCandidateTests(unittest.TestCase):
  def test_should_process_new_file(self):
    with tempfile.TemporaryDirectory() as tmp:
      path = Path(tmp) / 'dados.csv'
      path.write_text('a\tb\n', encoding='utf-8')
      handler = _CsvHandler(lambda: AppConfig(), lambda *_: None)
      self.assertTrue(handler.should_process_rescan_candidate(path))

  def test_should_skip_after_marked_processed(self):
    with tempfile.TemporaryDirectory() as tmp:
      path = Path(tmp) / 'dados.csv'
      path.write_text('a\tb\n', encoding='utf-8')
      handler = _CsvHandler(lambda: AppConfig(), lambda *_: None)
      handler._mark_batch_processed([path])
      self.assertFalse(handler.should_process_rescan_candidate(path))

  def test_should_reprocess_when_file_changes(self):
    with tempfile.TemporaryDirectory() as tmp:
      path = Path(tmp) / 'dados.csv'
      path.write_text('a\tb\n', encoding='utf-8')
      handler = _CsvHandler(lambda: AppConfig(), lambda *_: None)
      handler._mark_batch_processed([path])
      path.write_text('a\tb\nc\td\n', encoding='utf-8')
      self.assertTrue(handler.should_process_rescan_candidate(path))


class CoordinationTests(unittest.TestCase):
  def test_exclusive_lock_includes_owner_on_conflict(self):
    with tempfile.TemporaryDirectory() as tmp:
      lock_dir = Path(tmp)
      with exclusive_lock(lock_dir, 'csv', 'dados.csv'):
        with self.assertRaises(LockNotAcquired) as ctx:
          with exclusive_lock(lock_dir, 'csv', 'dados.csv'):
            pass
        self.assertTrue(ctx.exception.owner)

  def test_stale_lock_removed_when_pid_is_dead(self):
    with tempfile.TemporaryDirectory() as tmp:
      lock_dir = Path(tmp)
      lock_path = lock_dir / 'csv' / 'dados.csv.lock'
      lock_path.parent.mkdir(parents=True)
      lock_path.write_text('host=test\npid=999999999\n', encoding='utf-8')
      with exclusive_lock(lock_dir, 'csv', 'dados.csv', stale_seconds=3600):
        pass


class JobLogTests(unittest.TestCase):
  def test_read_job_log_tail_returns_last_lines(self):
    with tempfile.TemporaryDirectory() as tmp:
      log_path = Path(tmp) / 'automatic_fill.log'
      for index in range(5):
        append_job_log(log_path, 'info', f'linha {index}')
      content = read_job_log_tail(log_path, max_lines=2)
      self.assertIn('linha 3', content)
      self.assertIn('linha 4', content)
      self.assertNotIn('linha 0', content)


class StorageTests(unittest.TestCase):
  def test_read_shared_config_returns_none_when_missing(self):
    self.assertIsNone(read_shared_config('/tmp/inexistente'))

  def test_read_shared_config_loads_file(self):
    with tempfile.TemporaryDirectory() as tmp:
      watch = Path(tmp) / 'monitor'
      watch.mkdir()
      shared = app_data_dir(watch) / 'config.json'
      shared.parent.mkdir(parents=True, exist_ok=True)
      shared.write_text(json.dumps({
        'watch_folder': str(watch),
        'flows': [{'name': 'A', 'source_filename': 'x.csv', 'excel_directory': '/a', 'excel_filename': 'b.xlsx'}],
      }), encoding='utf-8')
      loaded = read_shared_config(str(watch))
      self.assertIsNotNone(loaded)
      self.assertEqual(loaded.flows[0].name, 'A')

  def test_save_config_writes_shared_and_bootstrap(self):
    with tempfile.TemporaryDirectory() as tmp:
      tmp_path = Path(tmp)
      watch = tmp_path / 'monitor'
      watch.mkdir()
      bootstrap = tmp_path / 'local' / 'config.json'

      with mock.patch('app.models.storage.bootstrap_config_path', return_value=bootstrap):
        config = AppConfig(watch_folder=str(watch))
        save_config(config)
        self.assertTrue(shared_config_path(watch).is_file())
        self.assertTrue(bootstrap.is_file())
        bootstrap_data = json.loads(bootstrap.read_text(encoding='utf-8'))
        self.assertEqual(bootstrap_data['watch_folder'], str(watch))

  def test_load_config_prefers_shared_file(self):
    with tempfile.TemporaryDirectory() as tmp:
      tmp_path = Path(tmp)
      watch = tmp_path / 'monitor'
      watch.mkdir()
      bootstrap = tmp_path / 'bootstrap.json'
      bootstrap.write_text(json.dumps({'watch_folder': str(watch), 'flows': []}), encoding='utf-8')
      shared = app_data_dir(watch) / 'config.json'
      shared.parent.mkdir(parents=True, exist_ok=True)
      shared.write_text(json.dumps({
        'watch_folder': str(watch),
        'flows': [{
          'name': 'Remoto',
          'source_filename': 'a.csv',
          'excel_directory': '/x',
          'excel_filename': 'b.xlsx',
        }],
      }), encoding='utf-8')

      with mock.patch('app.models.storage.bootstrap_config_path', return_value=bootstrap):
        config = load_config()
        self.assertEqual(config.flows[0].name, 'Remoto')


class EncodingTests(unittest.TestCase):
  def test_read_tab_csv_supports_cp1252(self):
    with tempfile.TemporaryDirectory() as tmp:
      path = Path(tmp) / 'dados.csv'
      path.write_bytes('ação\t10\n'.encode('cp1252'))
      rows = read_tab_csv(path)
      self.assertEqual(rows[0][0], 'ação')


class AtomicSaveTests(unittest.TestCase):
  def test_save_workbook_writes_final_file(self):
    with tempfile.TemporaryDirectory() as tmp:
      target = Path(tmp) / 'saida.xlsx'
      workbook = Workbook()
      workbook.active['A1'] = 'ok'
      save_workbook_to_path(workbook, target)
      self.assertTrue(target.is_file())


if __name__ == '__main__':
  unittest.main()
