from __future__ import annotations

import io
from pathlib import Path
from typing import Optional

import msoffcrypto
from msoffcrypto.exceptions import InvalidKeyError
from openpyxl import Workbook, load_workbook
from openpyxl.workbook.protection import WorkbookProtection
from openpyxl.workbook.workbook import Workbook as WorkbookType


class ExcelPasswordError(ValueError):
  pass


def is_encrypted_excel(path: Path) -> bool:
  if not path.is_file():
    return False
  with open(path, 'rb') as handle:
    office_file = msoffcrypto.OfficeFile(handle)
    return bool(office_file.is_encrypted())


def apply_edit_protection(workbook: WorkbookType, password: str) -> None:
  """Protege contra edição no Excel; o arquivo abre em leitura sem senha de abertura."""
  if not password:
    return

  if workbook.security is None:
    workbook.security = WorkbookProtection(lockStructure=True, lockWindows=False)
  else:
    workbook.security.lockStructure = True
    workbook.security.lockWindows = False
  workbook.security.set_workbook_password(password)

  for sheet in workbook.worksheets:
    sheet.protection.sheet = True
    sheet.protection.password = password
    sheet.protection.enable()


def load_workbook_from_path(path: Path, password: Optional[str] = None) -> WorkbookType:
  if not path.is_file():
    raise FileNotFoundError(str(path))

  with open(path, 'rb') as handle:
    office_file = msoffcrypto.OfficeFile(handle)
    if office_file.is_encrypted():
      if not password:
        raise ExcelPasswordError(
          'Este Excel foi salvo com senha de abertura (formato antigo). '
          'Informe a senha no fluxo ou salve novamente a partir do app para usar somente senha de edição.',
        )
      try:
        office_file.load_key(password=password)
        decrypted = io.BytesIO()
        office_file.decrypt(decrypted)
      except InvalidKeyError as exc:
        raise ExcelPasswordError('Senha do Excel incorreta.') from exc
      except Exception as exc:
        raise ExcelPasswordError('Não foi possível abrir o Excel com a senha informada.') from exc
      decrypted.seek(0)
      return load_workbook(decrypted)

    handle.seek(0)
    return load_workbook(handle)


def save_workbook_to_path(workbook: WorkbookType, path: Path, password: Optional[str] = None) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  if password:
    apply_edit_protection(workbook, password)
  workbook.save(path)


def create_empty_workbook() -> WorkbookType:
  workbook = Workbook()
  default_sheet = workbook.active
  workbook.remove(default_sheet)
  return workbook
