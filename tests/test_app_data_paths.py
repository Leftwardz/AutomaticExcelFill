from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.models.schema import AppConfig
from app.utils.app_data_paths import (
  app_data_dir,
  migrate_legacy_app_data,
  shared_config_path,
)


class AppDataPathsTests(unittest.TestCase):
  def test_shared_config_lives_in_app_data_subfolder(self):
    self.assertEqual(
      shared_config_path('/rede/pasta'),
      Path('/rede/pasta/_AutomaticExcelFill/config.json'),
    )

  def test_migrate_legacy_config_from_watch_root(self):
    with tempfile.TemporaryDirectory() as tmp:
      watch = Path(tmp) / 'monitor'
      watch.mkdir()
      legacy = watch / 'config.json'
      legacy.write_text(json.dumps({'watch_folder': str(watch), 'flows': []}), encoding='utf-8')

      migrate_legacy_app_data(watch)

      self.assertFalse(legacy.is_file())
      self.assertTrue(shared_config_path(watch).is_file())


if __name__ == '__main__':
  unittest.main()
