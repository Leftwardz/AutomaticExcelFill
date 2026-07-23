from __future__ import annotations



import hashlib

import shutil

import time

from contextlib import ExitStack

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

from app.services.csv_batch import collect_ready_csv_batch

from app.services.excel_crypto import ExcelFileError, ExcelPasswordError, format_excel_error

from app.services.excel_service import DuplicateRowError, append_csv_to_excel, excel_full_path

from app.services.file_stability import wait_for_file_stable

from app.services.job_log import append_job_log, format_processing_duration, resolve_shared_log_path

from app.utils.network_paths import is_likely_network_path





LogCallback = Callable[[str, str], None]


def _file_signature(path: Path) -> tuple[int, float] | None:
  try:
    stat = path.stat()
    return stat.st_size, stat.st_mtime
  except OSError:
    return None


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

    self._processed_signatures: dict[str, tuple[int, float]] = {}

    self._on_debug: LogCallback | None = None

  def set_debug_logging(self, on_debug: LogCallback | None) -> None:
    self._on_debug = on_debug

  def _debug(self, message: str) -> None:
    if self._on_debug is not None:
      self._on_debug('info', message)

  def on_created(self, event):

    if event.is_directory:

      return

    self._handle_file(event.src_path, source='created')



  def on_modified(self, event):

    if event.is_directory:

      return

    self._handle_file(event.src_path, source='modified')

  def on_moved(self, event):
    if event.is_directory:
      return
    self._handle_file(event.dest_path, source='moved')

  def _handle_file(self, src_path: str, *, source: str = 'event') -> None:

    path = Path(src_path)

    if path.suffix.lower() not in {'.csv', '.txt', '.tsv'}:
      return

    key = str(path.resolve())
    self._debug(f'Evento {source}: {path.name}')

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



  def _mark_batch_recent(self, batch: list[Path]) -> None:

    now = time.time()

    for item in batch:

      self._recent[str(item.resolve())] = now

  def _mark_batch_processed(self, batch: list[Path]) -> None:
    for item in batch:
      signature = _file_signature(item)
      if signature is not None:
        self._processed_signatures[str(item.resolve())] = signature

  def should_process_rescan_candidate(self, path: Path) -> bool:
    key = str(path.resolve())
    signature = _file_signature(path)
    if signature is None:
      return False
    return self._processed_signatures.get(key) != signature

  def _process_file(self, path: Path, *, skip_stability_wait: bool = False) -> None:

    if not path.is_file():

      return



    config = self._config_provider()

    flow = find_flow_by_filename(config, path.name)

    if flow is None:
      self._debug(f'Ignorado (sem fluxo correspondente): {path.name}')
      return



    watch_folder = (config.watch_folder or '').strip()

    if not watch_folder:

      self._on_log('error', f'[{flow.name}] Pasta de monitoramento não configurada.')

      return



    migrate_legacy_app_data(watch_folder)

    watch_path = Path(watch_folder)

    network_mode = is_likely_network_path(watch_path)
    stability_poll_interval = (
      config.network_stability_poll_seconds if network_mode else 0.5
    )

    if not skip_stability_wait:

      self._on_log('info', f'[{flow.name}] Aguardando {path.name} finalizar a cópia...')

      if not wait_for_file_stable(path, poll_interval=stability_poll_interval):
        self._on_log(
          'info',
          f'[{flow.name}] {path.name} ainda sendo copiado — nova tentativa no próximo ciclo.',
        )
        return



    batch = collect_ready_csv_batch(

      watch_path,

      flow,

      config,

      skip_stability_wait=skip_stability_wait,

      stability_poll_interval=stability_poll_interval,

    )

    if not batch:

      return



    batch_keys = {str(item.resolve()) for item in batch}

    if str(path.resolve()) not in batch_keys:

      return



    if len(batch) > 1:

      names = ', '.join(item.name for item in batch)

      self._on_log(

        'info',

        f'[{flow.name}] {len(batch)} arquivos para o mesmo Excel ({names}) — processando em lote.',

      )

    else:

      self._on_log('info', f'[{flow.name}] Processando {path.name}...')



    lock_dir = locks_root(watch_folder)

    excel_path = excel_full_path(flow.excel_directory, flow.excel_filename)

    excel_lock_name = hashlib.sha256(str(excel_path.resolve()).encode('utf-8')).hexdigest()

    log_path = resolve_shared_log_path(config)

    processing_started_at = time.perf_counter()

    try:

      with exclusive_lock(lock_dir, 'excel', excel_lock_name, stale_seconds=EXCEL_STALE_SECONDS):

        with ExitStack() as stack:

          for item in batch:

            if not item.is_file():

              return

            stack.enter_context(

              exclusive_lock(lock_dir, 'csv', item.name, stale_seconds=CSV_STALE_SECONDS),

            )

          label = batch[0].name if len(batch) == 1 else f'{len(batch)} arquivos'

          self._on_log(

            'info',

            f'[{flow.name}] Gravando {label} em {excel_path.name}...',

          )

          sheet_name, row_count = append_csv_to_excel(

            batch[0],

            excel_path,

            flow.headers,

            column_types=flow.normalized_column_types(),

            column_duplicate_checks=flow.normalized_column_duplicate_checks(),

            excel_password=flow.excel_password or None,

            skip_duplicate_row_check=flow.skip_duplicate_row_check,

            extra_csv_paths=batch[1:] or None,

            row_color_cutoff_hour=config.row_color_cutoff_hour,

          )

    except LockNotAcquired as exc:

      owner = exc.owner or 'outro computador'

      self._on_log('info', f'[{flow.name}] {path.name} ignorado — {owner} está processando.')

      return

    except DuplicateRowError as exc:

      self._handle_failure(
        batch, config, log_path, flow, str(exc),
        duration_seconds=time.perf_counter() - processing_started_at,
      )

      return

    except (ExcelPasswordError, ExcelFileError, ValueError) as exc:

      self._handle_failure(
        batch, config, log_path, flow, str(exc),
        duration_seconds=time.perf_counter() - processing_started_at,
      )

      return

    except Exception as exc:

      self._handle_failure(

        batch,

        config,

        log_path,

        flow,

        f'Erro ao processar lote: {format_excel_error(exc)}',

        duration_seconds=time.perf_counter() - processing_started_at,

      )

      return



    elapsed = time.perf_counter() - processing_started_at

    duration_label = format_processing_duration(elapsed)

    names = ', '.join(item.name for item in batch)

    success_message = (

      f'{names} → {excel_path.name} / aba "{sheet_name}" (+{row_count} linhas) em {duration_label}'

    )

    self._on_log('success', f'[{flow.name}] {success_message}')

    for item in batch:

      append_job_log(

        log_path,

        'success',

        success_message,

        flow_name=flow.name,

        source_file=item.name,

      )

      self._archive_source(item, config)

    self._mark_batch_recent(batch)
    self._mark_batch_processed(batch)

    if self._on_processed:

      self._on_processed(flow, batch[0], sheet_name, row_count)



  def _handle_failure(

    self,

    paths: Path | list[Path],

    config: AppConfig,

    log_path: Path,

    flow: Flow,

    message: str,

    duration_seconds: float | None = None,

  ) -> None:

    batch = paths if isinstance(paths, list) else [paths]

    names = ', '.join(item.name for item in batch)

    if duration_seconds is not None:

      message = f'{message} (tempo: {format_processing_duration(duration_seconds)})'

    self._on_log('error', f'[{flow.name}] {names}: {message}')

    for item in batch:

      append_job_log(

        log_path,

        'error',

        message,

        flow_name=flow.name,

        source_file=item.name,

      )

      self._archive_failed(item, config)



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

    self._rescan_thread: Optional[Thread] = None

    self._watch_folder = ''

    self._use_network_rescan = False

    self._network_rescan_seconds = 30.0



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
    self._handler.set_debug_logging(self._on_log)

    config = load_config()
    use_network_mode = is_likely_network_path(folder)
    self._use_network_rescan = use_network_mode
    self._network_rescan_seconds = config.network_rescan_seconds

    if use_network_mode:
      self._observer = PollingObserver(timeout=config.network_polling_seconds)
      observer_mode = 'polling (rede)'
    else:
      self._observer = Observer()
      observer_mode = 'eventos do sistema'

    self._observer.schedule(self._handler, str(folder), recursive=False)

    self._observer.start()

    self._stop_event.clear()

    self._scan_thread = Thread(target=self._initial_scan, args=(folder,), daemon=True)

    self._scan_thread.start()

    if self._use_network_rescan:
      self._rescan_thread = Thread(target=self._periodic_rescan, args=(folder,), daemon=True)
      self._rescan_thread.start()
      self._on_log(
        'info',
        f'Monitorando pasta: {folder} [{observer_mode}; polling '
        f'{config.network_polling_seconds:g}s; varredura '
        f'{config.network_rescan_seconds:g}s]',
      )
    else:
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

    if self._rescan_thread and self._rescan_thread.is_alive():

      self._rescan_thread.join(timeout=2)

    self._rescan_thread = None

    self._use_network_rescan = False



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

    started_flows: set[str] = set()

    for flow in config.flows:

      if not flow.enabled:

        continue

      if flow.id in started_flows:

        continue

      candidates = list(iter_matching_files(folder, flow.source_filename))

      if not candidates:

        continue

      if self._handler is not None:

        self._handler._process_file(candidates[0])

      started_flows.add(flow.id)

      if self._stop_event.is_set():

        return

  def _periodic_rescan(self, folder: Path) -> None:
    while not self._stop_event.wait(self._network_rescan_seconds):
      if self._handler is None:
        continue

      config = load_config()
      started_flows: set[str] = set()

      for flow in config.flows:
        if not flow.enabled:
          continue
        if flow.id in started_flows:
          continue

        candidates = [
          path
          for path in iter_matching_files(folder, flow.source_filename)
          if self._handler.should_process_rescan_candidate(path)
        ]
        if not candidates:
          continue

        self._on_log(
          'info',
          f'[rede] Varredura encontrou {len(candidates)} arquivo(s) pendente(s) para '
          f'"{flow.name}": {", ".join(path.name for path in candidates)}',
        )
        self._handler._process_file(candidates[0])
        started_flows.add(flow.id)

        if self._stop_event.is_set():
          return

