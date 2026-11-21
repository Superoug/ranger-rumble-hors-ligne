import importlib.util
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from langues import tr
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent if HERE.parent.name == 'moteur' else HERE.parent
COPIES = Path(os.environ.get('RR_COPIES') or ROOT / 'Sauvegardes')
TOOL = next((path for path in (HERE.parent / 'outil' / 'sauvegarde_rr.py', HERE.parent / 'outil_sauvegarde_source' / 'sauvegarde_rr.py') if path.exists()))
BASE = Path.home() / '.sauvegarde-rr'
DETAILS = BASE / 'journal_details.txt'
DEFAULT_APK = Path.home() / 'RangerRumble_hors_ligne.apk'
SAVE_NAME = 'save.msgpack'
STEP = re.compile('(\\d)/6 ')
BUILD_STEPS = {1: (0, 20, 8), 2: (20, 78, 20), 3: (78, 82, 2), 4: (82, 93, 4), 5: (93, 99, 2)}
NAME_DATE = re.compile('_(\\d{4})-(\\d{2})-(\\d{2})_(\\d{2})(\\d{2})\\d{2}$')
SAVE_CHECKS: dict[tuple[str, int], bool] = {}

def start_details() -> None:
    try:
        BASE.mkdir(parents=True, exist_ok=True)
        DETAILS.write_text('', encoding='utf-8')
    except OSError:
        pass

def keep_details(text: str) -> None:
    if not text.strip():
        return
    try:
        BASE.mkdir(parents=True, exist_ok=True)
        with open(DETAILS, 'a', encoding='utf-8') as handle:
            handle.write(text if text.endswith('\n') else text + '\n')
    except OSError:
        pass

def load_tool():
    spec = importlib.util.spec_from_file_location('sauvegarde_rr', TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.OUT = COPIES
    return module

def open_folder(path, reveal: bool=False) -> None:
    path = str(path)
    if sys.platform == 'win32':
        if reveal:
            subprocess.Popen(['explorer', '/select,', path])
        else:
            os.startfile(path)
    else:
        subprocess.Popen(['open', '-R', path] if reveal else ['open', path])

def is_save(path) -> bool:
    try:
        key = (str(path), os.stat(path).st_mtime_ns)
    except OSError:
        return False
    if key not in SAVE_CHECKS:
        SAVE_CHECKS[key] = read_is_save(path)
    return SAVE_CHECKS[key]

def read_is_save(path) -> bool:
    import msgpack
    try:
        with open(path, 'rb') as handle:
            value = msgpack.unpackb(handle.read(8 << 20), raw=False, strict_map_key=False, timestamp=0)
    except (OSError, ValueError, msgpack.UnpackException):
        return False
    parts = value.get('save') if isinstance(value, dict) else None
    return isinstance(parts, dict) and 'UnlockedHeroes' in parts

def has_save(folder) -> bool:
    return (Path(folder) / SAVE_NAME).is_file()

def newest_first(paths) -> list[Path]:
    return sorted(paths, key=lambda path: path.stat().st_mtime, reverse=True)

def copies(folder=None) -> list[Path]:
    folder = Path(folder or COPIES)
    if not folder.is_dir():
        return []
    return newest_first((copy for copy in folder.iterdir() if copy.is_dir() and has_save(copy)))

def save_kind(path) -> str:
    path = Path(path)
    if path.name == SAVE_NAME:
        return 'iphone'
    if path.name.startswith('TELEPHONE_'):
        return 'telephone'
    if path.name.startswith('ENVOYEE_'):
        return 'envoyee'
    return 'fichier'

def save_date(path) -> str:
    path = Path(path)
    named = NAME_DATE.search(path.parent.name if path.name == SAVE_NAME else path.stem)
    if named:
        _, month, day, hour, minute = named.groups()
        return f'{day}/{month} {hour}:{minute}'
    try:
        return time.strftime('%d/%m %H:%M', time.localtime(path.stat().st_mtime))
    except OSError:
        return ''

def save_label(path) -> str:
    path = Path(path)
    date, kind = (save_date(path), save_kind(path))
    if kind == 'iphone':
        label = tr('iPhone {account}, copiée le {date}', account=path.parent.name.split('_')[0], date=date)
        folder = path.parent.parent
    else:
        folder = path.parent
        label = {'telephone': tr('Téléphone, gardée le {date}', date=date), 'envoyee': tr('Envoyée au téléphone le {date}', date=date)}.get(kind, path.name)
    return label if folder == COPIES else f'{label}  ·  {folder.name}'

def saves(folder=None) -> list[Path]:
    folder = Path(folder or COPIES)
    if not folder.is_dir():
        return []
    own = [folder / SAVE_NAME] if has_save(folder) else []
    files = newest_first((file for file in folder.glob('*.msgpack') if file.name != SAVE_NAME and is_save(file)))
    return own + [copy / SAVE_NAME for copy in copies(folder)] + files
