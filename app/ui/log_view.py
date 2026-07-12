from __future__ import annotations

import re
from dataclasses import dataclass

import customtkinter as ctk

from app.ui.constants import (
  THEME_ERROR_TEXT,
  THEME_TABLE_ROW_A,
  THEME_TABLE_ROW_B,
  THEME_TEXT_SECONDARY,
)

LOG_SEPARATOR = '─' * 52
LOG_INFO_BG = '#1e3a5f'
LOG_INFO_FG = '#e0f2fe'
LOG_SUCCESS_BG = '#14532d'
LOG_SUCCESS_FG = '#dcfce7'


@dataclass(frozen=True)
class ParsedLogEntry:
  timestamp: str
  host: str
  level: str
  flow_name: str
  source_file: str
  message: str

  @property
  def group_key(self) -> tuple[str, str, str]:
    return (self.level.upper(), self.flow_name, self.source_file)

  @property
  def is_error(self) -> bool:
    return self.level.upper() in {'ERROR', 'ERR', 'FALHA', 'FAIL'}


def parse_job_log_line(line: str) -> ParsedLogEntry | None:
  text = line.strip()
  if not text:
    return None
  parts = text.split('\t')
  if len(parts) < 6:
    return None
  timestamp, host, level, flow_name, source_file, message = parts[:6]
  return ParsedLogEntry(
    timestamp=timestamp.strip(),
    host=host.strip(),
    level=level.strip(),
    flow_name=flow_name.strip() if flow_name.strip() != '-' else '',
    source_file=source_file.strip() if source_file.strip() != '-' else '',
    message=message.strip(),
  )


def format_shared_log_entry(entry: ParsedLogEntry) -> str:
  prefix = {'SUCCESS': '✓', 'ERROR': '✗', 'INFO': 'ℹ'}.get(entry.level.upper(), '•')
  meta_parts = [entry.timestamp]
  if entry.flow_name:
    meta_parts.append(entry.flow_name)
  if entry.source_file:
    meta_parts.append(entry.source_file)
  meta = '  •  '.join(meta_parts)
  return f'{meta}\n{prefix}  {entry.message}\n'


def level_entry_tag(level: str) -> str:
  normalized = level.lower()
  if normalized == 'error':
    return 'entry_error'
  if normalized == 'success':
    return 'entry_success'
  if normalized == 'info':
    return 'entry_info'
  return 'entry_neutral'


def shared_log_entry_tag(entry: ParsedLogEntry) -> str:
  level = entry.level.upper()
  if entry.is_error:
    return 'entry_error'
  if level == 'SUCCESS':
    return 'entry_success'
  if level == 'INFO':
    return 'entry_info'
  return 'entry_neutral'


def session_log_group_key(level: str, message: str) -> tuple[str, str, str]:
  flow_match = re.search(r'\[(.+?)\]', message)
  flow_name = flow_match.group(1).strip() if flow_match else ''
  source_match = re.search(r'\]\s*([^:\n]+?):', message)
  source_file = source_match.group(1).strip() if source_match else ''
  return (level.lower(), flow_name, source_file)


class ColoredLogView:
  def __init__(self, textbox: ctk.CTkTextbox):
    self._textbox = textbox
    self._inner = textbox._textbox
    self._last_group_key: tuple[str, ...] | None = None
    self._stripe_index = 0
    self._configure_tags()

  def _configure_tags(self) -> None:
    inner = self._inner
    inner.configure(
      spacing1=2,
      spacing3=4,
      selectbackground='#4338ca',
      inactiveselectbackground='#4338ca',
    )
    inner.tag_configure('header', foreground=THEME_TEXT_SECONDARY, spacing3=8)
    inner.tag_configure('separator', foreground='#52525b', spacing1=6, spacing3=6)
    inner.tag_configure('entry_neutral', background=THEME_TABLE_ROW_A, foreground='white')
    inner.tag_configure('entry_info', background=LOG_INFO_BG, foreground=LOG_INFO_FG)
    inner.tag_configure('entry_success', background=LOG_SUCCESS_BG, foreground=LOG_SUCCESS_FG)
    inner.tag_configure('entry_error', background='#3f1515', foreground=THEME_ERROR_TEXT)
    # Legado: faixas alternadas para entradas neutras sem nível explícito
    inner.tag_configure('entry_a', background=THEME_TABLE_ROW_A, foreground='white')
    inner.tag_configure('entry_b', background=THEME_TABLE_ROW_B, foreground='white')
    inner.tag_configure('entry_a_error', background='#3f1515', foreground=THEME_ERROR_TEXT)
    inner.tag_configure('entry_b_error', background='#4a1818', foreground=THEME_ERROR_TEXT)

  def clear(self) -> None:
    self._textbox.configure(state='normal')
    self._inner.delete('1.0', 'end')
    self._textbox.configure(state='disabled')
    self._last_group_key = None
    self._stripe_index = 0

  def _prepare_entry(
    self,
    group_key: tuple[str, ...],
    *,
    level: str,
  ) -> tuple[list[tuple[str, str]], str]:
    tag = level_entry_tag(level)
    prefix_lines: list[tuple[str, str]] = []
    if self._last_group_key is not None and group_key != self._last_group_key:
      self._stripe_index += 1
      prefix_lines.extend([
        ('', 'separator'),
        (LOG_SEPARATOR, 'separator'),
        ('', 'separator'),
      ])
    elif self._last_group_key is not None:
      prefix_lines.append(('', tag))
    self._last_group_key = group_key
    return prefix_lines, tag

  def _insert_line(self, text: str, tag: str) -> None:
    self._insert_lines([(text, tag)])

  def _insert_lines(self, lines: list[tuple[str, str]]) -> None:
    if not lines:
      return
    self._textbox.configure(state='normal')
    for text, tag in lines:
      self._inner.insert('end', f'{text}\n', tag)
    self._textbox.configure(state='disabled')

  def append_session_entry(self, level: str, message: str) -> None:
    prefix = {'info': 'ℹ', 'success': '✓', 'error': '✗'}.get(level.lower(), '•')
    group_key = session_log_group_key(level, message)
    prefix_lines, tag = self._prepare_entry(group_key, level=level)
    self._insert_lines(prefix_lines + [(f'{prefix}  {message}', tag)])
    self._inner.see('end')

  def render_shared_log(self, header: str, lines: list[str]) -> None:
    self.clear()
    rendered: list[tuple[str, str]] = [
      (header.strip(), 'header'),
      ('', 'header'),
    ]

    for line in lines:
      entry = parse_job_log_line(line)
      if entry is None:
        if line.strip():
          prefix_lines, tag = self._prepare_entry(('raw', line.strip()), level='neutral')
          rendered.extend(prefix_lines)
          rendered.append((line.strip(), tag))
        continue

      entry_tag = shared_log_entry_tag(entry)
      prefix_lines, tag = self._prepare_entry(entry.group_key, level=entry.level)
      rendered.extend(prefix_lines)
      for rendered_line in format_shared_log_entry(entry).splitlines():
        rendered.append((rendered_line, entry_tag))

    self._insert_lines(rendered)
    self._inner.see('end')

  def render_plain(self, text: str, *, tag: str = 'header') -> None:
    self.clear()
    self._insert_lines([(line, tag) for line in text.splitlines()])
    self._inner.see('end')
