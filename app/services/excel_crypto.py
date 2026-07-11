from __future__ import annotations

import io
import os
import tempfile
import zipfile
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree as ET

import msoffcrypto
from msoffcrypto.exceptions import InvalidKeyError
from openpyxl import Workbook, load_workbook
from openpyxl.utils.protection import hash_password
from openpyxl.workbook.workbook import Workbook as WorkbookType

MAIN_NS = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
REL_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'


class ExcelPasswordError(ValueError):
  pass


def is_encrypted_excel(path: Path) -> bool:
  if not path.is_file():
    return False
  with open(path, 'rb') as handle:
    office_file = msoffcrypto.OfficeFile(handle)
    return bool(office_file.is_encrypted())


def _inject_windows_modify_password(path: Path, password: str) -> None:
  """Emula Excel: Salvar como → Ferramentas → Opções gerais → Senha para modificar."""
  pwd_hash = hash_password(password)
  with zipfile.ZipFile(path, 'r') as zin:
    items = [(item, zin.read(item.filename)) for item in zin.infolist()]

  workbook_xml = next(data for item, data in items if item.filename == 'xl/workbook.xml')
  root = ET.fromstring(workbook_xml)

  for child in list(root):
    if child.tag == f'{{{MAIN_NS}}}fileSharing':
      root.remove(child)

  file_sharing = ET.Element(f'{{{MAIN_NS}}}fileSharing')
  file_sharing.set('readOnlyRecommended', '1')
  file_sharing.set('reservationPassword', pwd_hash)
  file_sharing.set('userName', 'AutomaticExcelFill')
  root.insert(0, file_sharing)

  ET.register_namespace('', MAIN_NS)
  ET.register_namespace('r', REL_NS)
  new_xml = ET.tostring(root, encoding='UTF-8', xml_declaration=True)

  buffer = io.BytesIO()
  with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zout:
    for item, data in items:
      if item.filename == 'xl/workbook.xml':
        data = new_xml
      zout.writestr(item, data)
  path.write_bytes(buffer.getvalue())


def read_file_sharing_password_hash(path: Path) -> Optional[str]:
  if not path.is_file():
    return None
  with zipfile.ZipFile(path, 'r') as zin:
    if 'xl/workbook.xml' not in zin.namelist():
      return None
    root = ET.fromstring(zin.read('xl/workbook.xml'))
  for child in root:
    if child.tag == f'{{{MAIN_NS}}}fileSharing':
      return child.get('reservationPassword')
  return None


def load_workbook_from_path(path: Path, password: Optional[str] = None) -> WorkbookType:
  if not path.is_file():
    raise FileNotFoundError(str(path))

  with open(path, 'rb') as handle:
    office_file = msoffcrypto.OfficeFile(handle)
    if office_file.is_encrypted():
      if not password:
        raise ExcelPasswordError(
          'Este Excel foi salvo com senha de abertura (formato antigo). '
          'Informe a senha no fluxo ou salve novamente pelo app para usar senha para modificar.',
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
  fd, tmp_name = tempfile.mkstemp(suffix='.xlsx.tmp', dir=path.parent)
  os.close(fd)
  tmp_path = Path(tmp_name)
  try:
    workbook.save(tmp_path)
    if password:
      _inject_windows_modify_password(tmp_path, password)
    os.replace(tmp_path, path)
  except Exception:
    tmp_path.unlink(missing_ok=True)
    raise


def create_empty_workbook() -> WorkbookType:
  workbook = Workbook()
  default_sheet = workbook.active
  workbook.remove(default_sheet)
  return workbook
