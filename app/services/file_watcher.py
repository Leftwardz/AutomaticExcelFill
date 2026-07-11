from __future__ import annotations

import hashlib
import shutil
import time
from pathlib import Path
from threading import Event, Thread
from typing import Callable, Optional

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from watchdog.observers.polling import PollingObserver

from app.models.schema import AppConfig, Flow
from app.models.storage import find_flow_by_filename, iter_matching_files, load_config
from app.services.coordination import (
  CSV_STALE_SECONDS,
  EXCEL_STALE_SECONDS,
  LockNotAcquired,
  exclusive_lock,
)
from app.utils.app_data_paths import locks_root, migrate_legacy_app_data
from app.services.excel_service import DuplicateRowError, append_csv_to_excel, excel_full_path
from app.services.file_stability import wait_for_file_stable
from app.services.job_log import append_job_log, resolve_shared_log_path
from app.utils.network_paths import is_likely_network_path


LogCallback = Callable[[str, str], None]


class _CsvHandler(FileSystemEventHandler):
  def __init__(
    self,
    config_provider: Callable[[], AppConfig],
    on_log: LogCallback,
    on_processed: Optional[Callable[[Flow, Path, str, int], None]] = None,
  ):
    self._config_provider = config_provider
    self._on_log = on_log
    self._on_processed = on_processed
    self._recent: dict[str, float] = {}
    self._debounce_seconds = 1.0

  def on_created(self, event):
    if event.is_directory:
      return
    self._handle_file(event.src_path)

  def on_modified(self, event):
    if event.is_directory:
      return
    self._handle_file(event.src_path)

  def _handle_file(self, src_path: str) -> None:
    path = Path(src_path)
    if path.suffix.lower() not in {'.csv', '.txt', '.tsv'}:
      return

    key = str(path.resolve())
    now = time.time()
    last = self._recent.get(key, 0)
    if now - last < self._debounce_seconds:
      return
    self._recent[key] = now
    self._process_file(path)

  def process_pending(self, path: Path, *, skip_stability_wait: bool = False) -> None:
    key = str(path.resolve())
    now = time.time()
    last = self._recent.get(key, 0)
    if now - last < self._debounce_seconds:
      return
    self._recent[key] = now
    self._process_file(path, skip_stability_wait=skip_stability_wait)

  def _process_file(self, path: Path, *, skip_stability_wait: bool = False) -> None:
    if not path.is_file():
      return

    config = self._config_provider()
    flow = find_flow_by_filename(config, path.name)
    if flow is None:
      return

    watch_folder = (config.watch_folder or '').strip()
    if not watch_folder:
      self._on_log('error', f'[{flow.name}] Pasta de monitoramento não configurada.')
      return

    migrate_legacy_app_data(watch_folder)

    if not skip_stability_wait and not wait_for_file_stable(path):
      self._on_log('info', f'[{flow.name}] {path.name} ainda sendo copiado — será tentado novamente.')
      return

    lock_dir = locks_root(watch_folder)
    csv_lock_name = path.name
    excel_path = excel_full_path(flow.excel_directory, flow.excel_filename)
    excel_lock_name = hashlib.sha256(str(excel_path.resolve()).encode('utf-8')).hexdigest()
    log_path = resolve_shared_log_path(config)

    try:
      with exclusive_lock(lock_dir, 'csv', csv_lock_name, stale_seconds=CSV_STALE_SECONDS):
        if not path.is_file():
          return
        with exclusive_lock(lock_dir, 'excel', excel_lock_name, stale_seconds=EXCEL_STALE_SECONDS):
          sheet_name, row_count = append_csv_to_excel(
            path,
            excel_path,
            flow.headers,
            excel_password=flow.excel_password or None,
          )
    except LockNotAcquired as exc:
      owner = exc.owner or 'outro computador'
      self._on_log('info', f'[{flow.name}] {path.name} ignorado — {owner} está processando.')
      return
    except DuplicateRowError as exc:
      self._handle_failure(path, config, log_path, flow, str(exc))
      return
    except Exception as exc:
      self._handle_failure(path, config, log_path, flow, f'Erro ao processar {path.name}: {exc}')
      return

    success_message = (
      f'{path.name} → {excel_path.name} / aba "{sheet_name}" (+{row_count} linhas)'
    )
    self._on_log('success', f'[{flow.name}] {success_message}')
    append_job_log(
      log_path,
      'success',
      success_message,
      flow_name=flow.name,
      source_file=path.name,
    )
    self._archive_source(path, config)
    if self._on_processed:
      self._on_processed(flow, path, sheet_name, row_count)

  def _handle_failure(
    self,
    path: Path,
    config: AppConfig,
    log_path: Path,
    flow: Flow,
    message: str,
  ) -> None:
    self._on_log('error', f'[{flow.name}] {path.name}: {message}')
    append_job_log(
      log_path,
      'error',
      message,
      flow_name=flow.name,
      source_file=path.name,
    )
    self._archive_failed(path, config)

  def _archive_source(self, path: Path, config: AppConfig) -> None:
    if not config.move_processed_files:
      return
    target_dir = path.parent / config.processed_subfolder
    target_dir.mkdir(parents=True, exist_ok=True)
    destination = target_dir / path.name
    if destination.exists():
      stamp = time.strftime('%Y%m%d_%H%M%S')
      destination = target_dir / f'{path.stem}_{stamp}{path.suffix}'
    shutil.move(str(path), str(destination))

  def _archive_failed(self, path: Path, config: AppConfig) -> None:
    if not config.move_failed_files or not path.is_file():
      return
    target_dir = path.parent / config.failed_subfolder
    target_dir.mkdir(parents=True, exist_ok=True)
    destination = target_dir / path.name
    if destination.exists():
      stamp = time.strftime('%Y%m%d_%H%M%S')
      destination = target_dir / f'{path.stem}_{stamp}{path.suffix}'
    shutil.move(str(path), str(destination))


class FolderWatcher:
  def __init__(self, on_log: LogCallback):
    self._on_log = on_log
    self._observer: Optional[Observer] = None
    self._handler: Optional[_CsvHandler] = None
    self._stop_event = Event()
    self._scan_thread: Optional[Thread] = None
    self._watch_folder = ''

  @property
  def is_running(self) -> bool:
    return self._observer is not None and self._observer.is_alive()

  @property
  def watch_folder(self) -> str:
    return self._watch_folder

  def start(self, watch_folder: str) -> None:
    self.stop()
    folder = Path(watch_folder)
    if not folder.is_dir():
      raise FileNotFoundError(f'Pasta de monitoramento inválida: {watch_folder}')

    self._watch_folder = str(folder)
    self._handler = _CsvHandler(load_config, self._on_log)
    if is_likely_network_path(folder):
      self._observer = PollingObserver(timeout=2)
      observer_mode = 'polling (rede)'
    else:
      self._observer = Observer()
      observer_mode = 'eventos do sistema'
    self._observer.schedule(self._handler, str(folder), recursive=False)
    self._observer.start()
    self._stop_event.clear()
    self._scan_thread = Thread(target=self._initial_scan, args=(folder,), daemon=True)
    self._scan_thread.start()
    self._on_log('info', f'Monitorando pasta: {folder} [{observer_mode}]')

  def stop(self) -> None:
    self._stop_event.set()
    if self._observer is not None:
      self._observer.stop()
      self._observer.join(timeout=3)
      self._observer = None
    self._handler = None
    self._watch_folder = ''
    if self._scan_thread and self._scan_thread.is_alive():
      self._scan_thread.join(timeout=2)
    self._scan_thread = None

  def process_file_now(self, path: Path) -> None:
    if self._handler is None:
      config = load_config()
      handler = _CsvHandler(lambda: config, self._on_log)
      handler.process_pending(path, skip_stability_wait=True)
      return
    self._handler.process_pending(path, skip_stability_wait=True)

  def _initial_scan(self, folder: Path) -> None:
    time.sleep(0.5)
    config = load_config()
    for flow in config.flows:
      if not flow.enabled:
        continue
      for candidate in iter_matching_files(folder, flow.source_filename):
        if self._handler is not None:
          self._handler._process_file(candidate)
      if self._stop_event.is_set():
        return
