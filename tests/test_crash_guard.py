from __future__ import annotations

import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from app.utils import crash_guard


class CrashGuardTests(unittest.TestCase):
  def setUp(self):
    crash_guard._main_window = None
    crash_guard.install_crash_guard._installed = False

  def test_thread_exception_is_logged_without_dialog(self):
    with tempfile.TemporaryDirectory() as tmp:
      log_path = Path(tmp) / 'crash.log'
      crash_guard.install_crash_guard(crash_log_path=log_path)

      with mock.patch.object(crash_guard, '_show_crash_dialog') as dialog:
        def boom():
          raise RuntimeError('falha em background')

        thread = threading.Thread(target=boom)
        thread.start()
        thread.join()

      dialog.assert_not_called()
      self.assertTrue(log_path.is_file())
      self.assertIn('falha em background', log_path.read_text(encoding='utf-8'))


if __name__ == '__main__':
  unittest.main()
