from __future__ import annotations

import unittest

from app.services.excel_crypto import ExcelFileError, format_excel_error


class ExcelCryptoErrorTests(unittest.TestCase):
  def test_format_excel_error_windows_file_in_use(self):
    exc = OSError('in use')
    exc.winerror = 32
    self.assertIn('aberto', format_excel_error(exc))

  def test_format_excel_error_masks_low_level_message(self):
    exc = RuntimeError("<class 'OSError'> returned a result with an exception set")
    exc.__cause__ = OSError('Permission denied')
    getattr(exc.__cause__, 'winerror', None)
    message = format_excel_error(exc)
    self.assertNotIn('returned a result with an exception set', message)


if __name__ == '__main__':
  unittest.main()
