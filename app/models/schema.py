from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import List
from uuid import uuid4


@dataclass
class Flow:
  name: str
  source_filename: str
  excel_directory: str
  excel_filename: str
  headers: List[str] = field(default_factory=list)
  excel_password: str = ''
  header_source_path: str = ''
  header_source_sheet: str = ''
  enabled: bool = True
  id: str = field(default_factory=lambda: str(uuid4()))

  def to_dict(self) -> dict:
    return asdict(self)

  @classmethod
  def from_dict(cls, data: dict) -> 'Flow':
    return cls(
      id=data.get('id') or str(uuid4()),
      name=data.get('name', ''),
      source_filename=data.get('source_filename', ''),
      excel_directory=data.get('excel_directory', ''),
      excel_filename=data.get('excel_filename', ''),
      headers=list(data.get('headers') or []),
      excel_password=data.get('excel_password', ''),
      header_source_path=data.get('header_source_path', ''),
      header_source_sheet=data.get('header_source_sheet', ''),
      enabled=bool(data.get('enabled', True)),
    )


@dataclass
class AppConfig:
  watch_folder: str = ''
  ui_theme: str = 'slate'
  auto_start_watcher: bool = True
  move_processed_files: bool = True
  processed_subfolder: str = 'processados'
  flows: List[Flow] = field(default_factory=list)

  def to_dict(self) -> dict:
    return {
      'watch_folder': self.watch_folder,
      'ui_theme': self.ui_theme,
      'auto_start_watcher': self.auto_start_watcher,
      'move_processed_files': self.move_processed_files,
      'processed_subfolder': self.processed_subfolder,
      'flows': [flow.to_dict() for flow in self.flows],
    }

  @classmethod
  def from_dict(cls, data: dict) -> 'AppConfig':
    flows = [Flow.from_dict(item) for item in data.get('flows') or []]
    return cls(
      watch_folder=data.get('watch_folder', ''),
      ui_theme=data.get('ui_theme', 'slate'),
      auto_start_watcher=bool(data.get('auto_start_watcher', True)),
      move_processed_files=bool(data.get('move_processed_files', True)),
      processed_subfolder=data.get('processed_subfolder', 'processados'),
      flows=flows,
    )
