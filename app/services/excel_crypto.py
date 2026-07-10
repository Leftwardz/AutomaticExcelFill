from __future__ import annotations

import io
from pathlib import Path
from typing import Optional

import msoffcrypto
from msoffcrypto.exceptions import InvalidKeyError
from msoffcrypto.format.ooxml import OOXMLFile
from openpyxl import Workbook, load_workbook
from openpyxl.workbook.workbook import Workbook as WorkbookType


class ExcelPasswordError(ValueError):
  pass


def is_encrypted_excel(path: Path) -> bool:
  if not path.is_file():
    return False
  with open(path, 'rb') as handle:
    office_file = msoffcrypto.OfficeFile(handle)
    return bool(office_file.is_encrypted())


def load_workbook_from_path(path: Path, password: Optional[str] = None) -> WorkbookType:
  if not path.is_file():
    raise FileNotFoundError(str(path))

  with open(path, 'rb') as handle:
    office_file = msoffcrypto.OfficeFile(handle)
    if office_file.is_encrypted():
      if not password:
        raise ExcelPasswordError(
          'O arquivo Excel está protegido por senha. Informe a senha no cadastro do fluxo.',
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
  if not password:
    workbook.save(path)
    return

  plain_buffer = io.BytesIO()
  workbook.save(plain_buffer)
  plain_buffer.seek(0)
  encrypted_buffer = io.BytesIO()
  ooxml_file = OOXMLFile(plain_buffer)
  ooxml_file.encrypt(password, encrypted_buffer)
  path.write_bytes(encrypted_buffer.getvalue())


def create_empty_workbook() -> WorkbookType:
  workbook = Workbook()
  default_sheet = workbook.active
  workbook.remove(default_sheet)
  return workbook
