from __future__ import annotations

import customtkinter as ctk
from tkinter import filedialog

from app.models.schema import Flow
from app.utils.excel_paths import EXCEL_FILETYPES
from app.services.header_import import list_excel_sheets, parse_headers_from_text, read_headers_from_excel
from app.services.excel_crypto import ExcelPasswordError
from app.ui.constants import (
  BTN_HOVER_RED,
  BTN_RED,
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


class FlowDialog(ctk.CTkToplevel):
  def __init__(self, master, flow: Flow | None = None, on_save=None):
    super().__init__(master)
    self.title('Fluxo' if flow is None else f'Editar fluxo — {flow.name}')
    self.geometry('700x820')
    self.resizable(False, False)
    self.configure(fg_color=THEME_BG)
    self.transient(master)
    self.grab_set()

    self._on_save = on_save
    self._flow = flow or Flow(name='', source_filename='', excel_directory='', excel_filename='')

    self._build()
    self._fill()

  def _build(self):
    header = ctk.CTkFrame(self, fg_color=THEME_CARD, corner_radius=0, height=56)
    header.pack(fill='x')
    header.pack_propagate(False)
    ctk.CTkLabel(
      header,
      text='Cadastro de fluxo',
      font=(FONT, 16, 'bold'),
      text_color='white',
    ).pack(side='left', padx=16, pady=14)

    body = ctk.CTkScrollableFrame(self, fg_color='transparent')
    body.pack(fill='both', expand=True, padx=16, pady=16)

    self._name = self._labeled_entry(body, 'Nome do fluxo', 'Ex.: Vendas diárias')
    self._source = self._labeled_entry(body, 'Arquivo esperado na pasta', 'Ex.: planilha_alc_* ou relatorio.csv')
    self._excel_dir = self._path_row(body, 'Pasta do Excel', is_directory=True)
    self._excel_name = self._labeled_entry(body, 'Nome do arquivo Excel', 'Ex.: consolidado.xlsb ou consolidado.xlsx')
    self._excel_password = self._labeled_entry(body, 'Senha do Excel (opcional)', 'Senha para abrir/salvar o arquivo')
    self._excel_password.configure(show='*')
    self._header_source = self._excel_file_row(body, 'Excel de referência (cabeçalho)', pick='file')
    self._header_sheet = self._labeled_entry(body, 'Aba do Excel de referência (opcional)', 'Ex.: Julho 2026 — vazio = mês atual')
    self._headers = self._headers_block(body)

    footer = ctk.CTkFrame(self, fg_color='transparent')
    footer.pack(fill='x', padx=16, pady=(0, 16))

    ctk.CTkButton(
      footer,
      text='Cancelar',
      command=self.destroy,
      width=120,
      **_secondary_btn_kwargs(),
    ).pack(side='right', padx=(8, 0))

    ctk.CTkButton(
      footer,
      text='Salvar',
      command=self._save,
      width=120,
      fg_color=THEME_ACCENT,
      hover_color=THEME_ACCENT_HOVER,
      corner_radius=8,
      height=34,
    ).pack(side='right')

  def _labeled_entry(self, parent, label: str, placeholder: str):
    frame = ctk.CTkFrame(parent, fg_color='transparent')
    frame.pack(fill='x', pady=(0, 12))
    ctk.CTkLabel(frame, text=label, font=(FONT, 12), text_color='white', anchor='w').pack(fill='x')
    entry = ctk.CTkEntry(frame, placeholder_text=placeholder, **_entry_kwargs())
    entry.pack(fill='x', pady=(4, 0))
    return entry

  def _excel_file_row(self, parent, label: str, *, pick: str):
    frame = ctk.CTkFrame(parent, fg_color='transparent')
    frame.pack(fill='x', pady=(0, 12))
    ctk.CTkLabel(frame, text=label, font=(FONT, 12), text_color='white', anchor='w').pack(fill='x')
    row = ctk.CTkFrame(frame, fg_color='transparent')
    row.pack(fill='x', pady=(4, 0))
    entry = ctk.CTkEntry(row, **_entry_kwargs())
    entry.pack(side='left', fill='x', expand=True)

    def browse():
      if pick == 'file':
        path = filedialog.askopenfilename(parent=self, filetypes=EXCEL_FILETYPES)
      else:
        path = filedialog.askdirectory(parent=self)
      if path:
        entry.delete(0, 'end')
        entry.insert(0, path)

    ctk.CTkButton(row, text='...', width=40, command=browse, **_secondary_btn_kwargs()).pack(side='left', padx=(8, 0))
    return entry

  def _path_row(self, parent, label: str, *, is_directory: bool):
    frame = ctk.CTkFrame(parent, fg_color='transparent')
    frame.pack(fill='x', pady=(0, 12))
    ctk.CTkLabel(frame, text=label, font=(FONT, 12), text_color='white', anchor='w').pack(fill='x')
    row = ctk.CTkFrame(frame, fg_color='transparent')
    row.pack(fill='x', pady=(4, 0))
    entry = ctk.CTkEntry(row, **_entry_kwargs())
    entry.pack(side='left', fill='x', expand=True)

    def browse():
      if is_directory:
        path = filedialog.askdirectory(parent=self)
      else:
        path = filedialog.askopenfilename(parent=self)
      if path:
        entry.delete(0, 'end')
        entry.insert(0, path)

    ctk.CTkButton(row, text='...', width=40, command=browse, **_secondary_btn_kwargs()).pack(side='left', padx=(8, 0))
    return entry

  def _headers_block(self, parent):
    frame = ctk.CTkFrame(parent, fg_color=THEME_CARD, corner_radius=12, border_width=1, border_color=THEME_CARD_BORDER)
    frame.pack(fill='both', expand=True, pady=(4, 0))

    top = ctk.CTkFrame(frame, fg_color='transparent')
    top.pack(fill='x', padx=12, pady=(12, 8))
    ctk.CTkLabel(top, text='Colunas do Excel (cabeçalho)', font=(FONT, 12, 'bold'), text_color='white').pack(side='left')
    self._headers_count = ctk.CTkLabel(top, text='0 colunas', font=(FONT, 11), text_color=THEME_TEXT_SECONDARY)
    self._headers_count.pack(side='right')

    ctk.CTkLabel(
      frame,
      text='Cole a linha de cabeçalho copiada do Excel (separada por tab) ou importe de um arquivo.',
      font=(FONT, 11),
      text_color=THEME_TEXT_SECONDARY,
      wraplength=600,
      justify='left',
    ).pack(fill='x', padx=12, pady=(0, 8))

    self._headers_text = ctk.CTkTextbox(
      frame,
      height=120,
      fg_color=THEME_BG,
      border_color=THEME_CARD_BORDER,
      border_width=1,
      corner_radius=8,
      text_color='white',
      font=(FONT, 11),
    )
    self._headers_text.pack(fill='x', padx=12, pady=(0, 8))
    self._headers_text.bind('<KeyRelease>', lambda _event: self._refresh_headers_count())

    actions = ctk.CTkFrame(frame, fg_color='transparent')
    actions.pack(fill='x', padx=12, pady=(0, 12))
    ctk.CTkButton(
      actions,
      text='Colar da área de transferência',
      command=self._paste_headers_from_clipboard,
      **_secondary_btn_kwargs(),
    ).pack(side='left')
    ctk.CTkButton(
      actions,
      text='Carregar do arquivo de referência',
      command=self._load_headers_from_reference,
      **_secondary_btn_kwargs(),
    ).pack(side='left')
    ctk.CTkButton(
      actions,
      text='Importar outro Excel',
      command=self._import_headers_from_excel,
      fg_color=THEME_ACCENT,
      hover_color=THEME_ACCENT_HOVER,
      corner_radius=8,
      height=32,
    ).pack(side='left', padx=(8, 0))

    return frame

  def _headers_text_value(self) -> str:
    return self._headers_text.get('1.0', 'end').strip()

  def _set_headers_text(self, headers: list[str]) -> None:
    self._headers_text.delete('1.0', 'end')
    if headers:
      self._headers_text.insert('1.0', '\t'.join(headers))
    self._refresh_headers_count()

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
    self._refresh_headers_count()

  def _load_headers_from_reference(self) -> None:
    path_value = self._header_source.get().strip()
    if not path_value:
      self._show_error('Informe o Excel de referência ou use Importar outro Excel.')
      return
    password = self._excel_password.get().strip() or None
    sheet_name = self._header_sheet.get().strip() or None
    try:
      headers = read_headers_from_excel(path_value, password=password, sheet_name=sheet_name)
    except ExcelPasswordError as exc:
      self._show_error(str(exc))
      return
    except Exception as exc:
      self._show_error(f'Não foi possível ler o Excel de referência: {exc}')
      return
    if not headers:
      self._show_error('Nenhuma coluna encontrada na primeira linha da aba selecionada.')
      return
    self._set_headers_text(headers)

  def _import_headers_from_excel(self) -> None:
    path = filedialog.askopenfilename(
      parent=self,
      title='Selecione o Excel de referência',
      filetypes=EXCEL_FILETYPES,
    )
    if not path:
      return
    self._header_source.delete(0, 'end')
    self._header_source.insert(0, path)
    password = self._excel_password.get().strip() or None
    sheet_name = self._header_sheet.get().strip() or None
    try:
      sheets = list_excel_sheets(path, password=password)
      if sheets and not sheet_name:
        from app.services.excel_service import current_month_sheet_name
        preferred = current_month_sheet_name()
        if preferred in sheets:
          sheet_name = preferred
          self._header_sheet.delete(0, 'end')
          self._header_sheet.insert(0, preferred)
      headers = read_headers_from_excel(path, password=password, sheet_name=sheet_name)
    except ExcelPasswordError as exc:
      self._show_error(str(exc))
      return
    except Exception as exc:
      self._show_error(f'Não foi possível ler o Excel: {exc}')
      return
    if not headers:
      self._show_error('Nenhuma coluna encontrada na primeira linha da planilha.')
      return
    self._set_headers_text(headers)

  def _fill(self):
    self._name.insert(0, self._flow.name)
    self._source.insert(0, self._flow.source_filename)
    self._excel_dir.insert(0, self._flow.excel_directory)
    self._excel_name.insert(0, self._flow.excel_filename)
    self._excel_password.insert(0, self._flow.excel_password)
    self._header_source.insert(0, self._flow.header_source_path)
    self._header_sheet.insert(0, self._flow.header_source_sheet)
    if self._flow.headers:
      self._set_headers_text(self._flow.headers)
    else:
      self._refresh_headers_count()

  def _save(self):
    name = self._name.get().strip()
    source = self._source.get().strip()
    excel_dir = self._excel_dir.get().strip()
    excel_name = self._excel_name.get().strip()
    excel_password = self._excel_password.get().strip()
    header_source_path = self._header_source.get().strip()
    header_source_sheet = self._header_sheet.get().strip()
    headers = parse_headers_from_text(self._headers_text_value())

    if not name or not source or not excel_dir or not excel_name:
      self._show_error('Preencha nome, arquivo de origem, pasta e nome do Excel.')
      return
    if not headers:
      self._show_error('Informe ao menos uma coluna (cole ou importe o cabeçalho).')
      return

    self._flow.name = name
    self._flow.source_filename = source
    self._flow.excel_directory = excel_dir
    self._flow.excel_filename = excel_name
    self._flow.excel_password = excel_password
    self._flow.header_source_path = header_source_path
    self._flow.header_source_sheet = header_source_sheet
    self._flow.headers = headers

    if self._on_save:
      self._on_save(self._flow)
    self.destroy()

  def _show_error(self, message: str):
    dialog = ctk.CTkToplevel(self)
    dialog.title('Validação')
    dialog.geometry('460x150')
    dialog.configure(fg_color=THEME_BG)
    dialog.transient(self)
    dialog.grab_set()
    ctk.CTkLabel(dialog, text=message, wraplength=420, text_color=THEME_ERROR_TEXT).pack(padx=16, pady=24)
    ctk.CTkButton(dialog, text='OK', command=dialog.destroy, fg_color=THEME_ACCENT, hover_color=THEME_ACCENT_HOVER).pack(pady=(0, 16))
