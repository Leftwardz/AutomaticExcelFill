from __future__ import annotations

import customtkinter as ctk
from tkinter import filedialog

from app.models.schema import COLUMN_TYPE_BY_LABEL, COLUMN_TYPE_LABELS, Flow
from app.services.header_import import parse_headers_from_text
from app.ui.constants import (
  FONT,
  THEME_ACCENT,
  THEME_ACCENT_HOVER,
  THEME_BG,
  THEME_CARD,
  THEME_CARD_BORDER,
  THEME_ERROR_TEXT,
  THEME_NAV_ACTIVE,
  THEME_TEXT_SECONDARY,
)
from app.ui.window_utils import center_window, create_scrollable_frame, schedule_center_window


def _entry_kwargs(**extra):
  kwargs = dict(
    fg_color=THEME_BG,
    border_color=THEME_CARD_BORDER,
    border_width=2,
    corner_radius=8,
    height=32,
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
    height=30,
  )
  kwargs.update(extra)
  return kwargs


class FlowDialog(ctk.CTkToplevel):
  def __init__(self, master, flow: Flow | None = None, on_save=None):
    super().__init__(master)
    self.title('Fluxo' if flow is None else f'Editar fluxo — {flow.name}')
    self.geometry('620x640')
    self.minsize(560, 560)
    self.resizable(True, True)
    self.configure(fg_color=THEME_BG)
    self.transient(master)
    self.grab_set()

    self._on_save = on_save
    self._flow = flow or Flow(name='', source_filename='', excel_directory='', excel_filename='')
    self._column_type_menus: dict[str, ctk.CTkOptionMenu] = {}
    self._duplicate_checks: dict[str, ctk.CTkCheckBox] = {}

    self._build()
    self._fill()
    self.after_idle(lambda: schedule_center_window(self, master))

  def _build(self):
    header = ctk.CTkFrame(self, fg_color=THEME_CARD, corner_radius=0, height=48)
    header.pack(fill='x')
    header.pack_propagate(False)
    ctk.CTkLabel(
      header,
      text='Cadastro de fluxo',
      font=(FONT, 15, 'bold'),
      text_color='white',
    ).pack(side='left', padx=16, pady=12)

    body = create_scrollable_frame(self, fg_color='transparent')
    body.pack(fill='both', expand=True, padx=16, pady=(12, 8))

    self._name = self._labeled_entry(body, 'Nome do fluxo', 'Ex.: Vendas diárias')
    self._source = self._labeled_entry(body, 'Arquivo esperado na pasta', 'Ex.: planilha_alc_* ou relatorio.csv')
    self._excel_dir = self._path_row(body, 'Pasta do Excel')
    self._excel_name = self._labeled_entry(body, 'Nome do arquivo Excel', 'Ex.: consolidado.xlsx')
    self._excel_password = self._labeled_entry(
      body,
      'Senha para modificar (opcional)',
      'Senha para modificar no Excel',
    )
    self._excel_password.configure(show='*')
    self._enabled = ctk.CTkCheckBox(
      body,
      text='Fluxo ativo (monitorar este arquivo)',
      text_color='white',
      fg_color=THEME_ACCENT,
      hover_color=THEME_ACCENT_HOVER,
    )
    self._enabled.pack(anchor='w', pady=(0, 4))
    self._skip_duplicate_row_check = ctk.CTkCheckBox(
      body,
      text='Ignorar verificação de linha duplicada (processamento mais rápido)',
      text_color=THEME_TEXT_SECONDARY,
      fg_color=THEME_ACCENT,
      hover_color=THEME_ACCENT_HOVER,
    )
    self._skip_duplicate_row_check.pack(anchor='w', pady=(0, 8))
    self._headers_block(body)

    footer = ctk.CTkFrame(self, fg_color='transparent')
    footer.pack(fill='x', padx=16, pady=(0, 12))

    ctk.CTkButton(
      footer,
      text='Cancelar',
      command=self.destroy,
      width=110,
      **_secondary_btn_kwargs(),
    ).pack(side='right', padx=(8, 0))

    ctk.CTkButton(
      footer,
      text='Salvar',
      command=self._save,
      width=110,
      fg_color=THEME_ACCENT,
      hover_color=THEME_ACCENT_HOVER,
      corner_radius=8,
      height=32,
    ).pack(side='right')

  def _labeled_entry(self, parent, label: str, placeholder: str):
    frame = ctk.CTkFrame(parent, fg_color='transparent')
    frame.pack(fill='x', pady=(0, 8))
    ctk.CTkLabel(frame, text=label, font=(FONT, 11), text_color='white', anchor='w').pack(fill='x')
    entry = ctk.CTkEntry(frame, placeholder_text=placeholder, **_entry_kwargs())
    entry.pack(fill='x', pady=(3, 0))
    return entry

  def _path_row(self, parent, label: str):
    frame = ctk.CTkFrame(parent, fg_color='transparent')
    frame.pack(fill='x', pady=(0, 8))
    ctk.CTkLabel(frame, text=label, font=(FONT, 11), text_color='white', anchor='w').pack(fill='x')
    row = ctk.CTkFrame(frame, fg_color='transparent')
    row.pack(fill='x', pady=(3, 0))
    entry = ctk.CTkEntry(row, **_entry_kwargs())
    entry.pack(side='left', fill='x', expand=True)

    def browse():
      path = filedialog.askdirectory(parent=self)
      if path:
        entry.delete(0, 'end')
        entry.insert(0, path)

    ctk.CTkButton(row, text='...', width=36, command=browse, **_secondary_btn_kwargs()).pack(side='left', padx=(8, 0))
    return entry

  def _headers_block(self, parent):
    frame = ctk.CTkFrame(parent, fg_color=THEME_CARD, corner_radius=12, border_width=1, border_color=THEME_CARD_BORDER)
    frame.pack(fill='x', pady=(4, 0))

    top = ctk.CTkFrame(frame, fg_color='transparent')
    top.pack(fill='x', padx=12, pady=(10, 4))
    ctk.CTkLabel(top, text='Colunas do Excel (cabeçalho)', font=(FONT, 11, 'bold'), text_color='white').pack(side='left')
    self._headers_count = ctk.CTkLabel(top, text='0 colunas', font=(FONT, 11), text_color=THEME_TEXT_SECONDARY)
    self._headers_count.pack(side='right')

    ctk.CTkLabel(
      frame,
      text='Cole a linha de cabeçalho copiada do Excel (colunas separadas por tab).',
      font=(FONT, 11),
      text_color=THEME_TEXT_SECONDARY,
      wraplength=540,
      justify='left',
    ).pack(fill='x', padx=12, pady=(0, 6))

    self._headers_text = ctk.CTkTextbox(
      frame,
      height=88,
      fg_color=THEME_BG,
      border_color=THEME_CARD_BORDER,
      border_width=1,
      corner_radius=8,
      text_color='white',
      font=(FONT, 11),
    )
    self._headers_text.pack(fill='x', padx=12, pady=(0, 8))
    self._headers_text.bind('<KeyRelease>', lambda _event: self._on_headers_changed())

    actions = ctk.CTkFrame(frame, fg_color='transparent')
    actions.pack(fill='x', padx=12, pady=(0, 10))
    ctk.CTkButton(
      actions,
      text='Colar da área de transferência',
      command=self._paste_headers_from_clipboard,
      fg_color=THEME_ACCENT,
      hover_color=THEME_ACCENT_HOVER,
      corner_radius=8,
      height=30,
    ).pack(side='left')

    types_frame = ctk.CTkFrame(frame, fg_color='transparent')
    types_frame.pack(fill='x', padx=12, pady=(0, 10))
    ctk.CTkLabel(
      types_frame,
      text='Tipo de cada coluna',
      font=(FONT, 11, 'bold'),
      text_color='white',
      anchor='w',
    ).pack(fill='x', pady=(0, 4))
    ctk.CTkLabel(
      types_frame,
      text='Escolha o tipo e marque "Repetido" para pintar valores duplicados em vermelho.',
      font=(FONT, 10),
      text_color=THEME_TEXT_SECONDARY,
      wraplength=540,
      justify='left',
    ).pack(fill='x', pady=(0, 6))
    self._column_types_frame = create_scrollable_frame(
      types_frame,
      height=160,
      fg_color=THEME_BG,
      border_color=THEME_CARD_BORDER,
      border_width=1,
      corner_radius=8,
    )
    self._column_types_frame.pack(fill='x')

  def _on_headers_changed(self) -> None:
    self._refresh_headers_count()
    self._rebuild_column_type_controls()

  def _current_column_types(self) -> dict[str, str]:
    selected: dict[str, str] = {}
    for header, menu in self._column_type_menus.items():
      selected[header] = COLUMN_TYPE_BY_LABEL.get(menu.get(), 'text')
    return selected

  def _current_duplicate_checks(self) -> dict[str, bool]:
    selected: dict[str, bool] = {}
    for header, checkbox in self._duplicate_checks.items():
      selected[header] = bool(checkbox.get())
    return selected

  def _rebuild_column_type_controls(
    self,
    *,
    selected_types: dict[str, str] | None = None,
    selected_duplicates: dict[str, bool] | None = None,
  ) -> None:
    headers = parse_headers_from_text(self._headers_text_value())
    if selected_types is None:
      selected_types = self._current_column_types()
      if not selected_types and self._flow.column_types:
        selected_types = {
          header: column_type
          for header, column_type in zip(self._flow.headers, self._flow.normalized_column_types())
        }
    if selected_duplicates is None:
      selected_duplicates = self._current_duplicate_checks()
      if not selected_duplicates and self._flow.column_duplicate_checks:
        selected_duplicates = {
          header: checked
          for header, checked in zip(
            self._flow.headers,
            self._flow.normalized_column_duplicate_checks(),
          )
        }

    for child in self._column_types_frame.winfo_children():
      child.destroy()
    self._column_type_menus.clear()
    self._duplicate_checks.clear()

    if not headers:
      ctk.CTkLabel(
        self._column_types_frame,
        text='Cole o cabeçalho acima para configurar as colunas.',
        font=(FONT, 10),
        text_color=THEME_TEXT_SECONDARY,
      ).pack(anchor='w', padx=8, pady=8)
      return

    for index, header in enumerate(headers, start=1):
      row = ctk.CTkFrame(self._column_types_frame, fg_color='transparent')
      row.pack(fill='x', padx=8, pady=2)
      ctk.CTkLabel(
        row,
        text=f'{index}. {header}',
        font=(FONT, 10),
        text_color='white',
        anchor='w',
      ).pack(side='left', fill='x', expand=True)
      column_type = selected_types.get(header, 'text')
      menu = ctk.CTkOptionMenu(
        row,
        values=list(COLUMN_TYPE_LABELS.values()),
        fg_color=THEME_NAV_ACTIVE,
        button_color=THEME_ACCENT,
        button_hover_color=THEME_ACCENT_HOVER,
        dropdown_fg_color=THEME_CARD,
        dropdown_hover_color=THEME_NAV_ACTIVE,
        width=110,
        height=28,
      )
      menu.set(COLUMN_TYPE_LABELS.get(column_type, 'Texto'))
      menu.pack(side='right', padx=(8, 0))
      self._column_type_menus[header] = menu

      duplicate_checkbox = ctk.CTkCheckBox(
        row,
        text='Repetido',
        text_color=THEME_TEXT_SECONDARY,
        fg_color=THEME_ACCENT,
        hover_color=THEME_ACCENT_HOVER,
        width=90,
      )
      if selected_duplicates.get(header, False):
        duplicate_checkbox.select()
      duplicate_checkbox.pack(side='right')
      self._duplicate_checks[header] = duplicate_checkbox

  def _column_types_from_ui(self, headers: list[str]) -> list[str]:
    selected = self._current_column_types()
    return [selected.get(header, 'text') for header in headers]

  def _column_duplicate_checks_from_ui(self, headers: list[str]) -> list[bool]:
    selected = self._current_duplicate_checks()
    return [selected.get(header, False) for header in headers]

  def _headers_text_value(self) -> str:
    return self._headers_text.get('1.0', 'end').strip()

  def _set_headers_text(self, headers: list[str]) -> None:
    self._headers_text.delete('1.0', 'end')
    if headers:
      self._headers_text.insert('1.0', '\t'.join(headers))
    self._on_headers_changed()

  def _refresh_headers_count(self) -> None:
    count = len(parse_headers_from_text(self._headers_text_value()))
    label = '1 coluna' if count == 1 else f'{count} colunas'
    self._headers_count.configure(text=label)

  def _paste_headers_from_clipboard(self) -> None:
    try:
      text = self.clipboard_get()
    except Exception:
      self._show_error('Não foi possível ler a área de transferência.')
      return
    if not text.strip():
      self._show_error('A área de transferência está vazia.')
      return
    self._headers_text.delete('1.0', 'end')
    self._headers_text.insert('1.0', text.strip())
    self._on_headers_changed()

  def _fill(self):
    self._name.insert(0, self._flow.name)
    self._source.insert(0, self._flow.source_filename)
    self._excel_dir.insert(0, self._flow.excel_directory)
    self._excel_name.insert(0, self._flow.excel_filename)
    self._excel_password.insert(0, self._flow.excel_password)
    if self._flow.enabled:
      self._enabled.select()
    if self._flow.skip_duplicate_row_check:
      self._skip_duplicate_row_check.select()
    if self._flow.headers:
      self._set_headers_text(self._flow.headers)
    else:
      self._on_headers_changed()

  def _save(self):
    name = self._name.get().strip()
    source = self._source.get().strip()
    excel_dir = self._excel_dir.get().strip()
    excel_name = self._excel_name.get().strip()
    excel_password = self._excel_password.get().strip()
    headers = parse_headers_from_text(self._headers_text_value())

    if not name or not source or not excel_dir or not excel_name:
      self._show_error('Preencha nome, arquivo de origem, pasta e nome do Excel.')
      return
    if not headers:
      self._show_error('Informe ao menos uma coluna (cole o cabeçalho do Excel).')
      return

    self._flow.name = name
    self._flow.source_filename = source
    self._flow.excel_directory = excel_dir
    self._flow.excel_filename = excel_name
    self._flow.excel_password = excel_password
    self._flow.enabled = bool(self._enabled.get())
    self._flow.skip_duplicate_row_check = bool(self._skip_duplicate_row_check.get())
    self._flow.header_source_path = ''
    self._flow.header_source_sheet = ''
    self._flow.headers = headers
    self._flow.column_types = self._column_types_from_ui(headers)
    self._flow.column_duplicate_checks = self._column_duplicate_checks_from_ui(headers)

    if self._on_save:
      self._on_save(self._flow)
    self.destroy()

  def _show_error(self, message: str):
    dialog = ctk.CTkToplevel(self)
    dialog.title('Validação')
    dialog.geometry('420x140')
    dialog.configure(fg_color=THEME_BG)
    dialog.transient(self)
    dialog.grab_set()
    ctk.CTkLabel(dialog, text=message, wraplength=380, text_color=THEME_ERROR_TEXT).pack(padx=16, pady=20)
    ctk.CTkButton(dialog, text='OK', command=dialog.destroy, fg_color=THEME_ACCENT, hover_color=THEME_ACCENT_HOVER).pack(pady=(0, 14))
    dialog.after_idle(lambda: schedule_center_window(dialog, self))
