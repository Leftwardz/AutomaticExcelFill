from __future__ import annotations

import customtkinter as ctk
from pathlib import Path
from tkinter import filedialog, ttk

from app.models.schema import AppConfig, Flow
from app.models.storage import (
  active_config_path,
  load_config,
  read_shared_config,
  remove_flow,
  save_config,
  shared_config_path,
  upsert_flow,
)
from app.services.file_watcher import FolderWatcher
from app.services.job_log import read_job_log_tail, resolve_shared_log_path
from app.ui.constants import (
  APP_NAME,
  BTN_HOVER_RED,
  BTN_RED,
  DEFAULT_HEIGHT,
  DEFAULT_WIDTH,
  FONT,
  SIDEBAR_WIDTH,
  THEME_ACCENT,
  THEME_ACCENT_HOVER,
  THEME_ACCENT_SECONDARY,
  THEME_BG,
  THEME_CARD,
  THEME_CARD_BORDER,
  THEME_NAV_ACTIVE,
  THEME_SIDEBAR,
  THEME_TEXT_SECONDARY,
)
from app.ui.flow_dialog import FlowDialog
from app.ui.theme_assets import gradient_ctk_image
from app.ui.ttk_theme import ARTEMIS_SCROLLBAR_V_STYLE, ARTEMIS_TREEVIEW_STYLE, apply_artemis_ttk_theme


def _entry_kwargs(**extra):
  kwargs = dict(
    fg_color=THEME_BG,
    border_color=THEME_CARD_BORDER,
    border_width=2,
    corner_radius=8,
    height=34,
    text_color='white',
    placeholder_text_color=THEME_TEXT_SECONDARY,
  )
  kwargs.update(extra)
  return kwargs


def _secondary_btn_kwargs(**extra):
  kwargs = dict(
    fg_color=THEME_NAV_ACTIVE,
    hover_color=THEME_CARD_BORDER,
    border_width=1,
    border_color=THEME_CARD_BORDER,
    corner_radius=8,
    height=32,
  )
  kwargs.update(extra)
  return kwargs


def _section_card(parent, title: str):
  card = ctk.CTkFrame(
    parent,
    fg_color=THEME_CARD,
    corner_radius=12,
    border_width=1,
    border_color=THEME_CARD_BORDER,
  )
  ctk.CTkLabel(card, text=title, font=(FONT, 13, 'bold'), text_color='white', anchor='w').pack(fill='x', padx=12, pady=(10, 6))
  body = ctk.CTkFrame(card, fg_color='transparent')
  body.pack(fill='both', expand=True, padx=12, pady=(0, 12))
  return card, body


class App(ctk.CTk):
  def __init__(self, config: AppConfig):
    super().__init__()
    self.title(APP_NAME)
    ctk.set_default_color_theme('dark-blue')
    ctk.set_appearance_mode('dark')
    apply_artemis_ttk_theme(self)
    self.option_add('*Font', (FONT, 13))
    self.configure(fg_color=THEME_BG)
    self.geometry(f'{DEFAULT_WIDTH}x{DEFAULT_HEIGHT}')
    self.minsize(900, 600)

    self.config_data = config
    self.watcher = FolderWatcher(self._add_log)
    self._active_view = 'monitor'
    self._nav_buttons: dict[str, ctk.CTkButton] = {}

    self.grid_columnconfigure(1, weight=1)
    self.grid_rowconfigure(0, weight=1)

    self._build_sidebar()
    self._build_views()
    self._show_view('monitor')

    if config.auto_start_watcher and config.watch_folder:
      self.after(500, self._start_watcher)

    self.protocol('WM_DELETE_WINDOW', self._on_close)

  def _build_sidebar(self):
    sidebar = ctk.CTkFrame(self, width=SIDEBAR_WIDTH, corner_radius=0, fg_color=THEME_SIDEBAR)
    sidebar.grid(row=0, column=0, sticky='nswe')
    sidebar.grid_propagate(False)
    sidebar.grid_rowconfigure(2, weight=1)

    logo_frame = ctk.CTkFrame(sidebar, fg_color='transparent')
    logo_frame.grid(row=0, column=0, sticky='ew', padx=12, pady=(16, 20))
    logo_img = gradient_ctk_image(36, 36, THEME_ACCENT, THEME_ACCENT_SECONDARY, radius=18)
    logo_mark = ctk.CTkLabel(
      logo_frame,
      image=logo_img,
      text='A',
      font=(FONT, 18, 'bold'),
      text_color='white',
      width=36,
      height=36,
      fg_color='transparent',
    )
    logo_mark.pack(side='left')
    logo_mark.image = logo_img
    ctk.CTkLabel(logo_frame, text=APP_NAME, font=(FONT, 16, 'bold'), text_color='white').pack(side='left', padx=(10, 0))

    nav = ctk.CTkFrame(sidebar, fg_color='transparent')
    nav.grid(row=1, column=0, sticky='new', padx=8)
    self._nav_buttons['monitor'] = self._nav_item(nav, 'Monitoramento', True, lambda: self._show_view('monitor'))
    self._nav_buttons['flows'] = self._nav_item(nav, 'Fluxos', False, lambda: self._show_view('flows'))
    self._nav_buttons['settings'] = self._nav_item(nav, 'Configurações', False, lambda: self._show_view('settings'))

    status_card = ctk.CTkFrame(sidebar, fg_color=THEME_NAV_ACTIVE, corner_radius=10)
    status_card.grid(row=3, column=0, sticky='ew', padx=12, pady=12)
    self.lbl_status = ctk.CTkLabel(status_card, text='Parado', font=(FONT, 12, 'bold'), text_color='white')
    self.lbl_status.pack(padx=12, pady=(10, 2))
    self.lbl_watch_folder = ctk.CTkLabel(
      status_card,
      text='Nenhuma pasta configurada',
      font=(FONT, 10),
      text_color=THEME_TEXT_SECONDARY,
      wraplength=SIDEBAR_WIDTH - 40,
    )
    self.lbl_watch_folder.pack(padx=12, pady=(0, 10))

  def _nav_item(self, parent, text: str, active: bool, command):
    btn = ctk.CTkButton(
      parent,
      text=text,
      anchor='w',
      height=36,
      corner_radius=8,
      fg_color=THEME_NAV_ACTIVE if active else 'transparent',
      hover_color=THEME_CARD_BORDER,
      text_color='white',
      command=command,
    )
    btn.pack(fill='x', pady=2)
    return btn

  def _build_views(self):
    self.views = ctk.CTkFrame(self, fg_color='transparent')
    self.views.grid(row=0, column=1, sticky='nswe', padx=16, pady=16)
    self.views.grid_columnconfigure(0, weight=1)
    self.views.grid_rowconfigure(0, weight=1)

    self.monitor_view = ctk.CTkFrame(self.views, fg_color='transparent')
    self.flows_view = ctk.CTkFrame(self.views, fg_color='transparent')
    self.settings_view = ctk.CTkFrame(self.views, fg_color='transparent')

    for view in (self.monitor_view, self.flows_view, self.settings_view):
      view.grid(row=0, column=0, sticky='nswe')
      view.grid_columnconfigure(0, weight=1)
      view.grid_rowconfigure(0, weight=1)

    self._build_monitor_view()
    self._build_flows_view()
    self._build_settings_view()
    self._refresh_status()

  def _build_monitor_view(self):
    card, body = _section_card(self.monitor_view, 'Monitoramento da pasta')
    card.grid(row=0, column=0, sticky='nsew')
    self.monitor_view.grid_rowconfigure(0, weight=1)

    controls = ctk.CTkFrame(body, fg_color='transparent')
    controls.pack(fill='x', pady=(0, 12))
    self.btn_start = ctk.CTkButton(
      controls,
      text='Iniciar monitoramento',
      command=self._start_watcher,
      fg_color=THEME_ACCENT,
      hover_color=THEME_ACCENT_HOVER,
      corner_radius=8,
      height=36,
    )
    self.btn_start.pack(side='left')
    self.btn_stop = ctk.CTkButton(
      controls,
      text='Parar',
      command=self._stop_watcher,
      **_secondary_btn_kwargs(height=36),
    )
    self.btn_stop.pack(side='left', padx=(8, 0))
    ctk.CTkButton(
      controls,
      text='Processar arquivo...',
      command=self._process_file_manual,
      **_secondary_btn_kwargs(height=36),
    ).pack(side='left', padx=(8, 0))
    ctk.CTkButton(
      controls,
      text='Atualizar log compartilhado',
      command=self._refresh_shared_log,
      **_secondary_btn_kwargs(height=36),
    ).pack(side='left', padx=(8, 0))

    log_card, log_body = _section_card(self.monitor_view, 'Log desta sessão')
    log_card.grid(row=1, column=0, sticky='nsew', pady=(12, 0))
    self.monitor_view.grid_rowconfigure(1, weight=1)

    self.log_box = ctk.CTkTextbox(
      log_body,
      fg_color=THEME_BG,
      border_color=THEME_CARD_BORDER,
      border_width=1,
      corner_radius=8,
      text_color='white',
      font=(FONT, 11),
    )
    self.log_box.pack(fill='both', expand=True)
    self.log_box.configure(state='disabled')

    shared_card, shared_body = _section_card(self.monitor_view, 'Log compartilhado (rede)')
    shared_card.grid(row=2, column=0, sticky='nsew', pady=(12, 0))
    self.monitor_view.grid_rowconfigure(2, weight=1)

    self.shared_log_box = ctk.CTkTextbox(
      shared_body,
      fg_color=THEME_BG,
      border_color=THEME_CARD_BORDER,
      border_width=1,
      corner_radius=8,
      text_color='white',
      font=(FONT, 11),
    )
    self.shared_log_box.pack(fill='both', expand=True)
    self.shared_log_box.configure(state='disabled')

  def _build_flows_view(self):
    top = ctk.CTkFrame(self.flows_view, fg_color='transparent')
    top.grid(row=0, column=0, sticky='ew', pady=(0, 8))
    ctk.CTkLabel(top, text='Fluxos cadastrados', font=(FONT, 18, 'bold'), text_color='white').pack(side='left')
    ctk.CTkButton(
      top,
      text='+ Novo fluxo',
      command=self._new_flow,
      fg_color=THEME_ACCENT,
      hover_color=THEME_ACCENT_HOVER,
      corner_radius=8,
      height=34,
    ).pack(side='right')

    table_host = ctk.CTkFrame(
      self.flows_view,
      fg_color=THEME_BG,
      corner_radius=8,
      border_width=1,
      border_color=THEME_CARD_BORDER,
    )
    table_host.grid(row=1, column=0, sticky='nsew')
    self.flows_view.grid_rowconfigure(1, weight=1)

    columns = ('name', 'source', 'excel', 'headers', 'password', 'enabled')
    self.flows_tree = ttk.Treeview(
      table_host,
      columns=columns,
      show='headings',
      style=ARTEMIS_TREEVIEW_STYLE,
    )
    self.flows_tree.heading('name', text='Nome')
    self.flows_tree.heading('source', text='Arquivo esperado')
    self.flows_tree.heading('excel', text='Excel')
    self.flows_tree.heading('headers', text='Colunas')
    self.flows_tree.heading('password', text='Modificar')
    self.flows_tree.heading('enabled', text='Ativo')
    self.flows_tree.column('name', width=140)
    self.flows_tree.column('source', width=140)
    self.flows_tree.column('excel', width=180)
    self.flows_tree.column('headers', width=70, anchor='center')
    self.flows_tree.column('password', width=60, anchor='center')
    self.flows_tree.column('enabled', width=60, anchor='center')

    scrollbar = ttk.Scrollbar(table_host, orient='vertical', command=self.flows_tree.yview, style=ARTEMIS_SCROLLBAR_V_STYLE)
    self.flows_tree.configure(yscrollcommand=scrollbar.set)
    self.flows_tree.pack(side='left', fill='both', expand=True, padx=8, pady=8)
    scrollbar.pack(side='right', fill='y', pady=8)

    actions = ctk.CTkFrame(self.flows_view, fg_color='transparent')
    actions.grid(row=2, column=0, sticky='ew', pady=(8, 0))
    ctk.CTkButton(actions, text='Editar', command=self._edit_flow, **_secondary_btn_kwargs()).pack(side='left')
    ctk.CTkButton(
      actions,
      text='Ativar/Desativar',
      command=self._toggle_flow_enabled,
      **_secondary_btn_kwargs(),
    ).pack(side='left', padx=(8, 0))
    ctk.CTkButton(
      actions,
      text='Recarregar da rede',
      command=self._reload_shared_config,
      **_secondary_btn_kwargs(),
    ).pack(side='left', padx=(8, 0))
    ctk.CTkButton(
      actions,
      text='Excluir',
      command=self._delete_flow,
      fg_color=BTN_RED,
      hover_color=BTN_HOVER_RED,
      corner_radius=8,
      height=32,
    ).pack(side='left', padx=(8, 0))

    self._reload_flows_table()

  def _build_settings_view(self):
    scroll = ctk.CTkScrollableFrame(self.settings_view, fg_color='transparent')
    scroll.grid(row=0, column=0, sticky='nsew')

    card, body = _section_card(scroll, 'Pasta principal')
    card.pack(fill='x', pady=(0, 12))

    row = ctk.CTkFrame(body, fg_color='transparent')
    row.pack(fill='x')
    self.entry_watch_folder = ctk.CTkEntry(row, **_entry_kwargs())
    self.entry_watch_folder.pack(side='left', fill='x', expand=True)
    self.entry_watch_folder.insert(0, self.config_data.watch_folder)
    ctk.CTkButton(row, text='...', width=40, command=self._browse_watch_folder, **_secondary_btn_kwargs()).pack(side='left', padx=(8, 0))

    self.lbl_config_path = ctk.CTkLabel(
      body,
      text='',
      font=(FONT, 10),
      text_color=THEME_TEXT_SECONDARY,
      wraplength=700,
      justify='left',
    )
    self.lbl_config_path.pack(fill='x', pady=(8, 0))

    ctk.CTkLabel(
      body,
      text='Use o mesmo caminho de rede nos dois PCs. Fluxos e configurações ficam em config.json dentro dessa pasta.',
      font=(FONT, 10),
      text_color=THEME_TEXT_SECONDARY,
      wraplength=700,
      justify='left',
    ).pack(fill='x', pady=(4, 0))

    options_card, options_body = _section_card(scroll, 'Comportamento')
    options_card.pack(fill='x', pady=(0, 12))

    self.chk_auto_start = ctk.CTkCheckBox(
      options_body,
      text='Iniciar monitoramento ao abrir o aplicativo',
      text_color='white',
      fg_color=THEME_ACCENT,
      hover_color=THEME_ACCENT_HOVER,
    )
    self.chk_auto_start.pack(anchor='w', pady=4)
    if self.config_data.auto_start_watcher:
      self.chk_auto_start.select()

    self.chk_move_processed = ctk.CTkCheckBox(
      options_body,
      text='Mover arquivos processados para subpasta',
      text_color='white',
      fg_color=THEME_ACCENT,
      hover_color=THEME_ACCENT_HOVER,
    )
    self.chk_move_processed.pack(anchor='w', pady=4)
    if self.config_data.move_processed_files:
      self.chk_move_processed.select()

    sub_row = ctk.CTkFrame(options_body, fg_color='transparent')
    sub_row.pack(fill='x', pady=(4, 0))
    ctk.CTkLabel(sub_row, text='Nome da subpasta:', text_color=THEME_TEXT_SECONDARY).pack(side='left')
    self.entry_processed_subfolder = ctk.CTkEntry(sub_row, width=180, **_entry_kwargs())
    self.entry_processed_subfolder.pack(side='left', padx=(8, 0))
    self.entry_processed_subfolder.insert(0, self.config_data.processed_subfolder)

    self.chk_move_failed = ctk.CTkCheckBox(
      options_body,
      text='Mover arquivos com falha para subpasta',
      text_color='white',
      fg_color=THEME_ACCENT,
      hover_color=THEME_ACCENT_HOVER,
    )
    self.chk_move_failed.pack(anchor='w', pady=4)
    if self.config_data.move_failed_files:
      self.chk_move_failed.select()

    failed_row = ctk.CTkFrame(options_body, fg_color='transparent')
    failed_row.pack(fill='x', pady=(4, 0))
    ctk.CTkLabel(failed_row, text='Subpasta de falhas:', text_color=THEME_TEXT_SECONDARY).pack(side='left')
    self.entry_failed_subfolder = ctk.CTkEntry(failed_row, width=180, **_entry_kwargs())
    self.entry_failed_subfolder.pack(side='left', padx=(8, 0))
    self.entry_failed_subfolder.insert(0, self.config_data.failed_subfolder)

    log_row = ctk.CTkFrame(options_body, fg_color='transparent')
    log_row.pack(fill='x', pady=(8, 0))
    ctk.CTkLabel(log_row, text='Log compartilhado:', text_color=THEME_TEXT_SECONDARY).pack(side='left')
    self.entry_shared_log_path = ctk.CTkEntry(log_row, **_entry_kwargs())
    self.entry_shared_log_path.pack(side='left', fill='x', expand=True, padx=(8, 0))
    placeholder = 'Padrão: pasta monitorada / automatic_fill.log'
    if self.config_data.shared_log_path:
      self.entry_shared_log_path.insert(0, self.config_data.shared_log_path)
    else:
      self.entry_shared_log_path.insert(0, placeholder)
      self.entry_shared_log_path.configure(text_color=THEME_TEXT_SECONDARY)
      self.entry_shared_log_path.bind('<FocusIn>', self._clear_shared_log_placeholder)
      self.entry_shared_log_path.bind('<FocusOut>', self._restore_shared_log_placeholder)

    ctk.CTkButton(
      scroll,
      text='Salvar configurações',
      command=self._save_settings,
      fg_color=THEME_ACCENT,
      hover_color=THEME_ACCENT_HOVER,
      corner_radius=8,
      height=36,
    ).pack(anchor='w', pady=(4, 0))

    ctk.CTkButton(
      scroll,
      text='Recarregar configuração da rede',
      command=self._reload_shared_config,
      **_secondary_btn_kwargs(),
    ).pack(anchor='w', pady=(8, 0))

  def _show_view(self, name: str):
    self._active_view = name
    for key, btn in self._nav_buttons.items():
      btn.configure(fg_color=THEME_NAV_ACTIVE if key == name else 'transparent')
    self.monitor_view.grid_remove()
    self.flows_view.grid_remove()
    self.settings_view.grid_remove()
    if name == 'monitor':
      self.monitor_view.grid()
      self._refresh_shared_log()
    elif name == 'flows':
      self.flows_view.grid()
      self._reload_shared_config(quiet=True)
      self._reload_flows_table()
    else:
      self.settings_view.grid()

  def _browse_watch_folder(self):
    path = filedialog.askdirectory(parent=self)
    if path:
      self.entry_watch_folder.delete(0, 'end')
      self.entry_watch_folder.insert(0, path)

  def _clear_shared_log_placeholder(self, _event=None):
    if self.entry_shared_log_path.get().startswith('Padrão:'):
      self.entry_shared_log_path.delete(0, 'end')
      self.entry_shared_log_path.configure(text_color='white')

  def _restore_shared_log_placeholder(self, _event=None):
    if not self.entry_shared_log_path.get().strip():
      self.entry_shared_log_path.insert(0, 'Padrão: pasta monitorada / automatic_fill.log')
      self.entry_shared_log_path.configure(text_color=THEME_TEXT_SECONDARY)

  def _reload_shared_config(self, *, quiet: bool = False) -> bool:
    folder = self.entry_watch_folder.get().strip() or (self.config_data.watch_folder or '').strip()
    loaded = read_shared_config(folder)
    if loaded is None:
      if not quiet:
        if folder:
          self._add_log('info', f'Nenhuma configuração compartilhada em {shared_config_path(folder)} ainda.')
        else:
          self._add_log('error', 'Configure a pasta principal antes de recarregar.')
      self._refresh_config_path_label()
      return False

    self.config_data = loaded
    self._sync_settings_form_from_config()
    self._reload_flows_table()
    self._refresh_status()
    self._refresh_config_path_label()
    if not quiet:
      self._add_log('info', f'Configuração recarregada ({len(self.config_data.flows)} fluxos).')
    return True

  def _sync_settings_form_from_config(self) -> None:
    self.entry_watch_folder.delete(0, 'end')
    self.entry_watch_folder.insert(0, self.config_data.watch_folder)

    if self.config_data.auto_start_watcher:
      self.chk_auto_start.select()
    else:
      self.chk_auto_start.deselect()

    if self.config_data.move_processed_files:
      self.chk_move_processed.select()
    else:
      self.chk_move_processed.deselect()

    self.entry_processed_subfolder.delete(0, 'end')
    self.entry_processed_subfolder.insert(0, self.config_data.processed_subfolder)

    if self.config_data.move_failed_files:
      self.chk_move_failed.select()
    else:
      self.chk_move_failed.deselect()

    self.entry_failed_subfolder.delete(0, 'end')
    self.entry_failed_subfolder.insert(0, self.config_data.failed_subfolder)

    self.entry_shared_log_path.delete(0, 'end')
    if self.config_data.shared_log_path:
      self.entry_shared_log_path.insert(0, self.config_data.shared_log_path)
      self.entry_shared_log_path.configure(text_color='white')
    else:
      self.entry_shared_log_path.insert(0, 'Padrão: pasta monitorada / automatic_fill.log')
      self.entry_shared_log_path.configure(text_color=THEME_TEXT_SECONDARY)

  def _refresh_config_path_label(self) -> None:
    folder = self.entry_watch_folder.get().strip() or (self.config_data.watch_folder or '').strip()
    if folder:
      path = shared_config_path(folder)
      self.lbl_config_path.configure(text=f'Configuração compartilhada: {path}')
    else:
      path = active_config_path(self.config_data)
      self.lbl_config_path.configure(text=f'Configuração local: {path}')

  def _ensure_latest_shared_config(self) -> None:
    folder = self.entry_watch_folder.get().strip() or (self.config_data.watch_folder or '').strip()
    loaded = read_shared_config(folder)
    if loaded is not None:
      self.config_data = loaded

  def _save_settings(self):
    was_running = self.watcher.is_running
    previous_folder = self.config_data.watch_folder
    watch_folder = self.entry_watch_folder.get().strip()

    loaded = read_shared_config(watch_folder)
    if loaded is not None:
      self.config_data = loaded

    self.config_data.watch_folder = watch_folder
    self.config_data.auto_start_watcher = bool(self.chk_auto_start.get())
    self.config_data.move_processed_files = bool(self.chk_move_processed.get())
    self.config_data.processed_subfolder = self.entry_processed_subfolder.get().strip() or 'processados'
    self.config_data.move_failed_files = bool(self.chk_move_failed.get())
    self.config_data.failed_subfolder = self.entry_failed_subfolder.get().strip() or 'falhas'
    shared_log = self.entry_shared_log_path.get().strip()
    if shared_log.startswith('Padrão:'):
      shared_log = ''
    self.config_data.shared_log_path = shared_log
    save_config(self.config_data)
    self.config_data = load_config()
    self._sync_settings_form_from_config()
    self._refresh_status()
    self._refresh_config_path_label()
    self._reload_flows_table()
    self._add_log('info', 'Configurações salvas.')
    if was_running:
      self.watcher.stop()
      if self.config_data.watch_folder:
        try:
          self.watcher.start(self.config_data.watch_folder)
          self.lbl_status.configure(text='Monitorando', text_color='#86efac')
          if previous_folder != self.config_data.watch_folder:
            self._add_log('info', 'Monitoramento reiniciado na nova pasta.')
        except Exception as exc:
          self._add_log('error', f'Não foi possível reiniciar o monitoramento: {exc}')
      else:
        self.lbl_status.configure(text='Parado', text_color='white')

  def _selected_flow(self) -> Flow | None:
    selected = self.flows_tree.selection()
    if not selected:
      return None
    flow_id = selected[0]
    for flow in self.config_data.flows:
      if flow.id == flow_id:
        return flow
    return None

  def _reload_flows_table(self):
    for item in self.flows_tree.get_children():
      self.flows_tree.delete(item)
    for flow in self.config_data.flows:
      excel_label = f'{flow.excel_directory}/{flow.excel_filename}'
      self.flows_tree.insert(
        '',
        'end',
        iid=flow.id,
        values=(
          flow.name,
          flow.source_filename,
          excel_label,
          len(flow.headers),
          'Sim' if flow.excel_password else '—',
          'Sim' if flow.enabled else 'Não',
        ),
      )

  def _new_flow(self):
    FlowDialog(self, on_save=self._persist_flow)

  def _edit_flow(self):
    flow = self._selected_flow()
    if flow is None:
      self._add_log('error', 'Selecione um fluxo para editar.')
      return
    FlowDialog(self, flow=Flow.from_dict(flow.to_dict()), on_save=self._persist_flow)

  def _toggle_flow_enabled(self):
    self._ensure_latest_shared_config()
    flow = self._selected_flow()
    if flow is None:
      self._add_log('error', 'Selecione um fluxo.')
      return
    flow.enabled = not flow.enabled
    self.config_data = upsert_flow(self.config_data, flow)
    save_config(self.config_data)
    self._reload_flows_table()
    state = 'ativado' if flow.enabled else 'desativado'
    self._add_log('info', f'Fluxo {state}: {flow.name}')

  def _delete_flow(self):
    self._ensure_latest_shared_config()
    flow = self._selected_flow()
    if flow is None:
      self._add_log('error', 'Selecione um fluxo para excluir.')
      return
    self.config_data = remove_flow(self.config_data, flow.id)
    save_config(self.config_data)
    self._reload_flows_table()
    self._add_log('info', f'Fluxo removido: {flow.name}')

  def _persist_flow(self, flow: Flow):
    self._ensure_latest_shared_config()
    self.config_data = upsert_flow(self.config_data, flow)
    save_config(self.config_data)
    self._reload_flows_table()
    self._add_log('info', f'Fluxo salvo: {flow.name}')

  def _start_watcher(self):
    folder = self.config_data.watch_folder or self.entry_watch_folder.get().strip()
    if not folder:
      self._add_log('error', 'Configure a pasta principal antes de iniciar.')
      return
    try:
      self.watcher.start(folder)
      self.lbl_status.configure(text='Monitorando', text_color='#86efac')
      self._add_log('info', 'Monitoramento iniciado.')
    except Exception as exc:
      self._add_log('error', str(exc))

  def _stop_watcher(self):
    self.watcher.stop()
    self.lbl_status.configure(text='Parado', text_color='white')
    self._add_log('info', 'Monitoramento parado.')

  def _refresh_status(self):
    folder = self.config_data.watch_folder or 'Nenhuma pasta configurada'
    self.lbl_watch_folder.configure(text=folder)
    self._refresh_config_path_label()

  def _process_file_manual(self):
    path = filedialog.askopenfilename(
      parent=self,
      title='Selecionar arquivo para processar',
      filetypes=[
        ('Arquivos de dados', '*.csv *.txt *.tsv'),
        ('Todos os arquivos', '*.*'),
      ],
    )
    if not path:
      return
    self._add_log('info', f'Processamento manual: {Path(path).name}')
    self.watcher.process_file_now(Path(path))
    self._refresh_shared_log()

  def _refresh_shared_log(self):
    log_path = resolve_shared_log_path(self.config_data)
    content = read_job_log_tail(log_path)
    header = f'Arquivo: {log_path}\n{"—" * 48}\n'

    def apply():
      self.shared_log_box.configure(state='normal')
      self.shared_log_box.delete('1.0', 'end')
      self.shared_log_box.insert('1.0', header + content)
      self.shared_log_box.see('end')
      self.shared_log_box.configure(state='disabled')

    self.after(0, apply)

  def _add_log(self, level: str, message: str):
    prefix = {'info': 'ℹ', 'success': '✓', 'error': '✗'}.get(level, '•')

    def append():
      self.log_box.configure(state='normal')
      self.log_box.insert('end', f'{prefix} {message}\n')
      self.log_box.see('end')
      self.log_box.configure(state='disabled')

    self.after(0, append)
    if level in ('success', 'error'):
      self.after(200, self._refresh_shared_log)

  def _on_close(self):
    self.watcher.stop()
    self.destroy()
