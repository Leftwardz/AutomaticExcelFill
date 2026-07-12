from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import customtkinter as ctk

if TYPE_CHECKING:
  from tkinter import Misc

_SCROLL_FRAMES_BY_ROOT: dict[Misc, list[ctk.CTkScrollableFrame]] = {}
_SHIFT_PRESSED = False


def _is_ctk_window(window) -> bool:
  return isinstance(window, (ctk.CTk, ctk.CTkToplevel))


def _logical_size(window) -> tuple[int, int]:
  window.update_idletasks()

  if _is_ctk_window(window):
    geometry = window.geometry()
    if geometry:
      width, height, _, _ = window._parse_geometry_string(geometry)
      if width and height:
        return width, height
    return window._current_width, window._current_height

  width = window.winfo_width()
  height = window.winfo_height()
  if width <= 1 or height <= 1:
    geometry = window.geometry().split('+', 1)[0]
    if 'x' in geometry:
      width_str, height_str = geometry.split('x', 1)
      return int(width_str), int(height_str)
  return width, height


def _physical_size(window, logical_width: int, logical_height: int) -> tuple[int, int]:
  if _is_ctk_window(window):
    scaling = window._get_window_scaling()
    return round(logical_width * scaling), round(logical_height * scaling)
  return logical_width, logical_height


def _screen_bounds(window, parent=None) -> tuple[int, int, int, int]:
  if parent is not None:
    parent.update_idletasks()
    return (
      parent.winfo_rootx(),
      parent.winfo_rooty(),
      parent.winfo_width(),
      parent.winfo_height(),
    )

  if sys.platform == 'win32':
    work_area = _windows_work_area(window)
    if work_area is not None:
      left, top, right, bottom = work_area
      return left, top, right - left, bottom - top

  window.update_idletasks()
  return 0, 0, window.winfo_screenwidth(), window.winfo_screenheight()


def _windows_work_area(window) -> tuple[int, int, int, int] | None:
  try:
    import ctypes
    from ctypes import wintypes
  except ImportError:
    return None

  user32 = ctypes.windll.user32
  MONITOR_DEFAULTTONEAREST = 2

  class POINT(ctypes.Structure):
    _fields_ = [('x', wintypes.LONG), ('y', wintypes.LONG)]

  class RECT(ctypes.Structure):
    _fields_ = [
      ('left', wintypes.LONG),
      ('top', wintypes.LONG),
      ('right', wintypes.LONG),
      ('bottom', wintypes.LONG),
    ]

  class MONITORINFO(ctypes.Structure):
    _fields_ = [
      ('cbSize', wintypes.DWORD),
      ('rcMonitor', RECT),
      ('rcWork', RECT),
      ('dwFlags', wintypes.DWORD),
    ]

  monitor = None
  try:
    window.update_idletasks()
    monitor = user32.MonitorFromWindow(window.winfo_id(), MONITOR_DEFAULTTONEAREST)
  except Exception:
    monitor = None

  if not monitor:
    point = POINT(window.winfo_pointerx(), window.winfo_pointery())
    monitor = user32.MonitorFromPoint(point, MONITOR_DEFAULTTONEAREST)
  if not monitor:
    return None

  info = MONITORINFO()
  info.cbSize = ctypes.sizeof(MONITORINFO)
  if not user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
    return None

  work = info.rcWork
  return work.left, work.top, work.right, work.bottom


def _is_window_ready(window) -> bool:
  window.update_idletasks()
  if _is_ctk_window(window):
    expected_width = round(window._current_width * window._get_window_scaling())
    expected_height = round(window._current_height * window._get_window_scaling())
    return (
      window.winfo_width() >= max(120, expected_width - 4)
      and window.winfo_height() >= max(120, expected_height - 4)
    )
  return window.winfo_width() > 1 and window.winfo_height() > 1


def center_window(window, parent=None) -> None:
  """Center a window on its parent or on the active monitor."""
  if _is_ctk_window(window):
    logical_width = window._current_width
    logical_height = window._current_height
    physical_width, physical_height = _physical_size(window, logical_width, logical_height)
  else:
    logical_width, logical_height = _logical_size(window)
    physical_width, physical_height = logical_width, logical_height

  origin_x, origin_y, area_width, area_height = _screen_bounds(window, parent)
  x = origin_x + max(0, (area_width - physical_width) // 2)
  y = origin_y + max(0, (area_height - physical_height) // 2)

  if _is_ctk_window(window):
    window.geometry(f'+{x}+{y}')
  else:
    window.geometry(f'{logical_width}x{logical_height}+{x}+{y}')


def schedule_center_window(window, parent=None) -> None:
  """Center after CTk applied the real window size (not the initial 200x200 placeholder)."""
  def try_center(attempt: int = 0) -> None:
    if not window.winfo_exists():
      return
    if _is_window_ready(window):
      center_window(window, parent)
      return
    if attempt < 15:
      window.after(50, lambda: try_center(attempt + 1))

  window.bind('<Map>', lambda _event: try_center(), add='+')
  try_center()


def create_scrollable_frame(master, **kwargs) -> ctk.CTkScrollableFrame:
  """Create a CTkScrollableFrame with nested mouse-wheel routing."""
  frame = ctk.CTkScrollableFrame(master, **kwargs)
  register_scrollable_frame(frame)
  return frame


def register_scrollable_frame(frame: ctk.CTkScrollableFrame) -> None:
  """Route mouse-wheel scrolling to the innermost scroll frame under the cursor."""
  root = frame.winfo_toplevel()
  frames = _SCROLL_FRAMES_BY_ROOT.setdefault(root, [])
  if frame not in frames:
    frames.append(frame)

  _install_scroll_router(root)
  frame.bind('<Destroy>', lambda _event: _unregister_scrollable_frame(frame), add='+')


def _unregister_scrollable_frame(frame: ctk.CTkScrollableFrame) -> None:
  root = frame.winfo_toplevel()
  frames = _SCROLL_FRAMES_BY_ROOT.get(root, [])
  if frame in frames:
    frames.remove(frame)
  if not frames:
    _SCROLL_FRAMES_BY_ROOT.pop(root, None)


def _install_scroll_router(root: Misc) -> None:
  if getattr(root, '_aef_scroll_router_installed', False):
    _rebind_scroll_router(root)
    return

  root._aef_scroll_router_installed = True
  _rebind_scroll_router(root)


def _rebind_scroll_router(root: Misc) -> None:
  for sequence in (
    '<MouseWheel>',
    '<Button-4>',
    '<Button-5>',
    '<KeyPress-Shift_L>',
    '<KeyPress-Shift_R>',
    '<KeyRelease-Shift_L>',
    '<KeyRelease-Shift_R>',
  ):
    root.unbind_all(sequence)

  root.bind_all('<MouseWheel>', lambda event: _route_scroll_event(root, event), add='+')
  root.bind_all('<Button-4>', lambda event: _route_scroll_event(root, event), add='+')
  root.bind_all('<Button-5>', lambda event: _route_scroll_event(root, event), add='+')
  root.bind_all('<KeyPress-Shift_L>', _on_shift_press, add='+')
  root.bind_all('<KeyPress-Shift_R>', _on_shift_press, add='+')
  root.bind_all('<KeyRelease-Shift_L>', _on_shift_release, add='+')
  root.bind_all('<KeyRelease-Shift_R>', _on_shift_release, add='+')


def _on_shift_press(_event) -> None:
  global _SHIFT_PRESSED
  _SHIFT_PRESSED = True


def _on_shift_release(_event) -> None:
  global _SHIFT_PRESSED
  _SHIFT_PRESSED = False


def _canvas_depth(frame: ctk.CTkScrollableFrame, widget) -> int:
  depth = 0
  current = widget
  while current is not None:
    if current == frame._parent_canvas:
      return depth
    current = current.master
    depth += 1
  return -1


def _route_scroll_event(root: Misc, event) -> None:
  frames = [
    frame
    for frame in _SCROLL_FRAMES_BY_ROOT.get(root, [])
    if frame.winfo_exists() and frame.check_if_master_is_canvas(event.widget)
  ]
  if not frames:
    return

  target = max(frames, key=lambda frame: _canvas_depth(frame, event.widget))
  target._shift_pressed = _SHIFT_PRESSED

  canvas = target._parent_canvas
  if event.num == 4:
    if target._shift_pressed:
      if canvas.xview() != (0.0, 1.0):
        canvas.xview('scroll', -1, 'units')
    elif canvas.yview() != (0.0, 1.0):
      canvas.yview('scroll', -1, 'units')
    return
  if event.num == 5:
    if target._shift_pressed:
      if canvas.xview() != (0.0, 1.0):
        canvas.xview('scroll', 1, 'units')
    elif canvas.yview() != (0.0, 1.0):
      canvas.yview('scroll', 1, 'units')
    return

  if sys.platform.startswith('win'):
    delta = -int(event.delta / 6)
  elif sys.platform == 'darwin':
    delta = -event.delta
  else:
    delta = -event.delta

  if target._shift_pressed:
    if canvas.xview() != (0.0, 1.0):
      canvas.xview('scroll', delta, 'units')
  elif canvas.yview() != (0.0, 1.0):
    canvas.yview('scroll', delta, 'units')
