import unittest
from pathlib import Path
from unittest.mock import patch

from app.utils.bundle_paths import install_dir, resource_path


class BundlePathsTests(unittest.TestCase):
  def test_resource_path_finds_theme_in_project(self):
    path = resource_path('theme', 'presets.json')
    self.assertTrue(path.is_file())
    self.assertEqual(path.name, 'presets.json')

  def test_resource_path_uses_meipass_when_frozen(self):
    fake_meipass = Path('/tmp/fake_bundle')
    fake_file = fake_meipass / 'theme' / 'presets.json'
    with patch.object(Path, 'exists', lambda self: str(self) == str(fake_file)):
      with patch('app.utils.bundle_paths.sys') as mock_sys:
        mock_sys.frozen = True
        mock_sys.executable = r'C:\Apps\AutomaticExcelFill\AutomaticExcelFill.exe'
        mock_sys._MEIPASS = str(fake_meipass)
        path = resource_path('theme', 'presets.json')
    self.assertEqual(path, fake_file)

  def test_install_dir_points_to_project_in_dev(self):
    root = Path(__file__).resolve().parents[1]
    with patch('app.utils.bundle_paths.sys') as mock_sys:
      mock_sys.frozen = False
      self.assertEqual(install_dir(), root)


if __name__ == '__main__':
  unittest.main()
