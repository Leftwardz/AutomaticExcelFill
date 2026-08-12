from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from app.models.storage import load_config
from app.utils.app_data_paths import migrate_legacy_app_data
from app.utils.network_paths import safe_is_dir


class SafeNetworkPathTests(unittest.TestCase):
  def test_safe_is_dir_returns_false_when_stat_fails(self):
    path = Path('\\\\servidor\\pasta')
    with mock.patch.object(Path, 'is_dir', side_effect=OSError(1920, 'inacessível')):
      self.assertFalse(safe_is_dir(path))

  def test_migrate_legacy_app_data_ignores_unreachable_folder(self):
    with mock.patch('app.utils.app_data_paths.safe_is_dir', return_value=False):
      migrate_legacy_app_data('\\\\servidor\\pasta')

  def test_load_config_survives_unreachable_watch_folder(self):
    with tempfile.TemporaryDirectory() as tmp:
      bootstrap = Path(tmp) / 'config.json'
      watch = '\\\\10.30.40.79\\payment perso\\ABASTECIMENTO PLANILHAS'
      bootstrap.write_text(
        json.dumps({'watch_folder': watch, 'flows': []}),
        encoding='utf-8',
      )

      with mock.patch('app.models.storage.bootstrap_config_path', return_value=bootstrap):
        with mock.patch('app.utils.app_data_paths.safe_is_dir', return_value=False):
          config = load_config()

      self.assertEqual(config.watch_folder, watch)
      self.assertEqual(config.flows, [])


if __name__ == '__main__':
  unittest.main()
