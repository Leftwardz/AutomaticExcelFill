import unittest
from unittest.mock import MagicMock

from app.ui.window_utils import _canvas_depth, center_window


class CanvasDepthTests(unittest.TestCase):
  def test_deeper_nested_widget_prefers_inner_frame(self):
    outer = MagicMock()
    inner = MagicMock()
    outer_canvas = MagicMock()
    inner_canvas = MagicMock()
    widget = MagicMock()

    outer._parent_canvas = outer_canvas
    inner._parent_canvas = inner_canvas
    widget.master = inner
    inner.master = inner_canvas
    inner_canvas.master = outer
    outer.master = None

    self.assertGreater(_canvas_depth(inner, widget), _canvas_depth(outer, widget))

  def test_center_window_uses_parent_position(self):
    window = MagicMock()
    parent = MagicMock()
    window.update_idletasks = MagicMock()
    parent.update_idletasks = MagicMock()
    window.winfo_width.return_value = 620
    window.winfo_height.return_value = 640
    parent.winfo_rootx.return_value = 100
    parent.winfo_rooty.return_value = 80
    parent.winfo_width.return_value = 1200
    parent.winfo_height.return_value = 800

    center_window(window, parent)

    window.geometry.assert_called_once_with('620x640+390+160')

  def test_center_window_uses_ctk_position_only(self):
    window = MagicMock()
    window.update_idletasks = MagicMock()
    window._current_width = 1100
    window._current_height = 700
    window._get_window_scaling.return_value = 1.5
    window.winfo_pointerx.return_value = 960
    window.winfo_pointery.return_value = 540
    window.winfo_id.side_effect = RuntimeError('not mapped')

    with unittest.mock.patch('app.ui.window_utils._is_ctk_window', return_value=True), \
         unittest.mock.patch('app.ui.window_utils._windows_work_area', return_value=(0, 0, 1920, 1040)):
      center_window(window)

    window.geometry.assert_called_once_with('+135+0')


if __name__ == '__main__':
  unittest.main()
