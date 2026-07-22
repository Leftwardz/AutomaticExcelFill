from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import List, Literal
from uuid import uuid4

ColumnType = Literal['text', 'number', 'date']

COLUMN_TYPE_LABELS = {
  'text': 'Texto',
  'number': 'Número',
  'date': 'Data',
}
COLUMN_TYPE_BY_LABEL = {label: key for key, label in COLUMN_TYPE_LABELS.items()}


def normalize_column_type(value: str) -> ColumnType:
  item = str(value).strip().lower()
  if item == 'number':
    return 'number'
  if item == 'date':
    return 'date'
  return 'text'


def normalize_cutoff_hour(value: object, default: int = 19) -> int:
  try:
    hour = int(value)  # type: ignore[arg-type]
  except (TypeError, ValueError):
    return default
  return max(0, min(23, hour))


@dataclass
class Flow:
  name: str
  source_filename: str
  excel_directory: str
  excel_filename: str
  headers: List[str] = field(default_factory=list)
  column_types: List[str] = field(default_factory=list)
  column_duplicate_checks: List[bool] = field(default_factory=list)
  skip_duplicate_row_check: bool = False
  excel_password: str = ''
  header_source_path: str = ''
  header_source_sheet: str = ''
  enabled: bool = True
  id: str = field(default_factory=lambda: str(uuid4()))

  def normalized_column_types(self) -> List[str]:
    types = [normalize_column_type(item) for item in (self.column_types or [])]
    while len(types) < len(self.headers):
      types.append('text')
    return types[:len(self.headers)]

  def normalized_column_duplicate_checks(self) -> List[bool]:
    checks: List[bool] = []
    for item in (self.column_duplicate_checks or []):
      if isinstance(item, bool):
        checks.append(item)
      else:
        checks.append(str(item).strip().lower() in {'1', 'true', 'sim', 'yes'})
    while len(checks) < len(self.headers):
      checks.append(False)
    return checks[:len(self.headers)]

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
      column_types=list(data.get('column_types') or []),
      column_duplicate_checks=list(data.get('column_duplicate_checks') or []),
      skip_duplicate_row_check=bool(data.get('skip_duplicate_row_check', False)),
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
  move_failed_files: bool = True
  failed_subfolder: str = 'falhas'
  shared_log_path: str = ''
  row_color_cutoff_hour: int = 19
  flows: List[Flow] = field(default_factory=list)

  def to_dict(self) -> dict:
    return {
      'watch_folder': self.watch_folder,
      'ui_theme': self.ui_theme,
      'auto_start_watcher': self.auto_start_watcher,
      'move_processed_files': self.move_processed_files,
      'processed_subfolder': self.processed_subfolder,
      'move_failed_files': self.move_failed_files,
      'failed_subfolder': self.failed_subfolder,
      'shared_log_path': self.shared_log_path,
      'row_color_cutoff_hour': self.row_color_cutoff_hour,
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
      move_failed_files=bool(data.get('move_failed_files', True)),
      failed_subfolder=data.get('failed_subfolder', 'falhas'),
      shared_log_path=data.get('shared_log_path', ''),
      row_color_cutoff_hour=normalize_cutoff_hour(data.get('row_color_cutoff_hour', 19)),
      flows=flows,
    )
