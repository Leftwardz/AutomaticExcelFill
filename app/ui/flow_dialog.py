from __future__ import annotations

import customtkinter as ctk
from tkinter import filedialog

from app.models.schema import Flow
from app.ui.constants import (
  BTN_HOVER_RED,
  BTN_RED,
  FONT,
  THEME_ACCENT,
  THEME_ACCENT_HOVER,
  THEME_BG,
  THEME_CARD,
  THEME_CARD_BORDER,
  THEME_NAV_ACTIVE,
  THEME_TEXT_SECONDARY,
)


def _entry_kwargs(**extra):
  return dict(
    fg_color=THEME_BG,
    border_color=THEME_CARD_BORDER,
    border_width=2,
    corner_radius=8,
    height=34,
    text_color='white',
    placeholder_text_color=THEME_TEXT_SECONDARY,
    **extra,
  )


def _secondary_btn_kwargs(**extra):
  return dict(
    fg_color=THEME_NAV_ACTIVE,
    hover_color=THEME_CARD_BORDER,
    border_width=1,
    border_color=THEME_CARD_BORDER,
    corner_radius=8,
    height=32,
    **extra,
  )


class FlowDialog(ctk.CTkToplevel):
  def __init__(self, master, flow: Flow | None = None, on_save=None):
    super().__init__(master)
    self.title('Fluxo' if flow is None else f'Editar fluxo — {flow.name}')
    self.geometry('620x560')
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
    self._source = self._labeled_entry(body, 'Arquivo esperado na pasta', 'Ex.: relatorio.csv')
    self._excel_dir = self._path_row(body, 'Pasta do Excel', is_directory=True)
    self._excel_name = self._labeled_entry(body, 'Nome do arquivo Excel', 'Ex.: consolidado.xlsx')
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
    ctk.CTkButton(
      top,
      text='+ Coluna',
      width=90,
      command=self._add_header_row,
      fg_color=THEME_ACCENT,
      hover_color=THEME_ACCENT_HOVER,
      corner_radius=8,
      height=28,
    ).pack(side='right')

    self._headers_container = ctk.CTkFrame(frame, fg_color='transparent')
    self._headers_container.pack(fill='both', expand=True, padx=12, pady=(0, 12))
    self._header_entries: list[ctk.CTkEntry] = []
    return frame

  def _add_header_row(self, value: str = ''):
    row = ctk.CTkFrame(self._headers_container, fg_color='transparent')
    row.pack(fill='x', pady=2)
    entry = ctk.CTkEntry(row, placeholder_text='Nome da coluna', **_entry_kwargs())
    entry.pack(side='left', fill='x', expand=True)
    if value:
      entry.insert(0, value)
    ctk.CTkButton(
      row,
      text='×',
      width=34,
      command=lambda: self._remove_header_row(row, entry),
      fg_color=BTN_RED,
      hover_color=BTN_HOVER_RED,
      corner_radius=8,
      height=32,
    ).pack(side='left', padx=(8, 0))
    self._header_entries.append(entry)

  def _remove_header_row(self, row, entry):
    if entry in self._header_entries:
      self._header_entries.remove(entry)
    row.destroy()

  def _fill(self):
    self._name.insert(0, self._flow.name)
    self._source.insert(0, self._flow.source_filename)
    self._excel_dir.insert(0, self._flow.excel_directory)
    self._excel_name.insert(0, self._flow.excel_filename)
    if self._flow.headers:
      for header in self._flow.headers:
        self._add_header_row(header)
    else:
      self._add_header_row()

  def _save(self):
    name = self._name.get().strip()
    source = self._source.get().strip()
    excel_dir = self._excel_dir.get().strip()
    excel_name = self._excel_name.get().strip()
    headers = [entry.get().strip() for entry in self._header_entries if entry.get().strip()]

    if not name or not source or not excel_dir or not excel_name:
      self._show_error('Preencha nome, arquivo de origem, pasta e nome do Excel.')
      return
    if not headers:
      self._show_error('Adicione ao menos uma coluna no cabeçalho.')
      return

    self._flow.name = name
    self._flow.source_filename = source
    self._flow.excel_directory = excel_dir
    self._flow.excel_filename = excel_name
    self._flow.headers = headers

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
    ctk.CTkLabel(dialog, text=message, wraplength=380, text_color='white').pack(padx=16, pady=24)
    ctk.CTkButton(dialog, text='OK', command=dialog.destroy, fg_color=THEME_ACCENT, hover_color=THEME_ACCENT_HOVER).pack(pady=(0, 16))
