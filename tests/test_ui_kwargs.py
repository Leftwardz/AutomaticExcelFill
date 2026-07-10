import unittest

from app.ui.main_app import _entry_kwargs, _secondary_btn_kwargs


class WidgetKwargsTests(unittest.TestCase):
  def test_secondary_btn_kwargs_allows_height_override(self):
    kwargs = _secondary_btn_kwargs(height=36)
    self.assertEqual(kwargs['height'], 36)

  def test_entry_kwargs_allows_height_override(self):
    kwargs = _entry_kwargs(height=40)
    self.assertEqual(kwargs['height'], 40)


if __name__ == '__main__':
  unittest.main()
