import datetime
import hashlib
import json
import os
import shutil
import tempfile
import threading
import zipfile
import msgpack
import copie_android
from langues import SETTINGS, tr
HERE = os.path.dirname(os.path.abspath(__file__))
VERSION_FILE = os.path.join(HERE, 'version.json')
PACKAGE_NAME = 'Ratchet_Ranger_Rumble'
OLD_PACKAGE_NAME = 'OutilSauvegardeRR'
OBSOLETE = ('lancer.sh', 'LIS_MOI.txt')
ASSET = 'Launcher_Ratchet_Ranger_Rumble.zip'
OLD_ASSETS = (PACKAGE_NAME + '.zip', OLD_PACKAGE_NAME + '.zip')
ENGINE = 'moteur'
KEPT = ('moteur', 'Sauvegardes')
DOWNLOAD_SHARE = 0.85
EDITOR_FOLDER = copie_android.EDITOR_FOLDER
APK_SAVE = 'assets/rr_offline/save.msgpack'
APK_VERSION = 'assets/rr_offline/version.json'
_SETTINGS_LOCK = threading.Lock()

class Problem(Exception):
    pass

def current() -> dict:
    with open(VERSION_FILE, encoding='utf-8') as handle:
        return json.load(handle)

def parse(version) -> tuple[int, ...]:
    parts = []
    for piece in str(version).lstrip('vV').split('.'):
        digits = ''.join((c for c in piece if c.isdigit()))
        parts.append(int(digits) if digits else 0)
    return tuple(parts)

def newer(candidate, installed) -> bool:
    a, b = (parse(candidate), parse(installed))
    width = max(len(a), len(b))
    return a + (0,) * (width - len(a)) > b + (0,) * (width - len(b))

def latest_release(depot: str | None=None) -> dict | None:
    depot = depot or current()['depot']
    with copie_android.url_open(f'https://api.github.com/repos/{depot}/releases/latest', timeout=15) as answer:
        release = json.load(answer)
    assets = {a.get('name'): a.get('browser_download_url') for a in release.get('assets', [])}
    tag = str(release.get('tag_name', '')).lstrip('vV')
    if not tag:
        return None
    archive = next((n for n in (ASSET, *OLD_ASSETS) if assets.get(n) and assets.get(n + '.sha256')), None)
    return {'version': tag, 'jeu': release_game(assets.get('version.json')), 'notes': (release.get('body') or '').strip(), 'page': release.get('html_url'), 'zip': assets[archive] if archive else None, 'sha256': assets[archive + '.sha256'] if archive else None}

def release_game(url: str | None):
    if not url:
        return None
    try:
        with copie_android.url_open(url, timeout=15) as answer:
            return json.load(answer).get('jeu')
    except Exception:
        return None

def download(url: str, path: str, progress=None) -> None:
    with copie_android.url_open(url, timeout=300) as answer, open(path, 'wb') as out:
        total = int(answer.headers.get('Content-Length') or 0)
        done = 0
        while (chunk := answer.read(1 << 20)):
            out.write(chunk)
            done += len(chunk)
            if progress and total:
                progress(min(1.0, done / total))

def update_tool(release: dict, root: str, say=print, progress=None) -> None:
    progress = progress or (lambda fraction, text: None)
    if not release.get('zip') or not release.get('sha256'):
        raise Problem(tr("Cette version n'a pas le fichier de l'outil attendu : il faut la télécharger à la main sur sa page."))
    work = tempfile.mkdtemp(prefix='rr_maj_')
    try:
        archive = download_checked(release, work, say, progress)
        new = unpacked_tool(archive, os.path.join(work, 'nouveau'), release['version'])
        say(tr('Installation...'))
        progress(0.9, tr('Installation...'))
        install_tool(new, root)
        done = tr("L'outil est maintenant en version {version}.", version=release['version'])
        say(done)
        progress(1.0, done)
    finally:
        shutil.rmtree(work, ignore_errors=True)

def download_checked(release: dict, work: str, say, progress) -> str:
    archive = os.path.join(work, ASSET)
    coming = tr('Téléchargement de la version {version}...', version=release['version'])
    say(coming)
    progress(0.0, coming)
    download(release['zip'], archive, lambda fraction: progress(DOWNLOAD_SHARE * fraction, coming))
    sums = os.path.join(work, 'sha256')
    download(release['sha256'], sums)
    with open(sums, encoding='utf-8') as handle:
        expected = handle.read().split()[0].lower()
    with open(archive, 'rb') as handle:
        digest = hashlib.file_digest(handle, 'sha256').hexdigest()
    if digest != expected:
        raise Problem(tr('Le fichier téléchargé est abîmé (empreinte différente). Réessayer plus tard.'))
    return archive

def unpacked_tool(archive: str, unpacked: str, version: str) -> str:
    with zipfile.ZipFile(archive) as content:
        inside = os.path.realpath(unpacked) + os.sep
        if any((not os.path.realpath(os.path.join(unpacked, name)).startswith(inside) for name in content.namelist())):
            raise Problem(tr('Le fichier téléchargé contient des chemins inattendus.'))
        content.extractall(unpacked)
        for info in content.infolist():
            mode = info.external_attr >> 16 & 511
            if mode and os.name != 'nt':
                os.chmod(os.path.join(unpacked, info.filename), mode)
    new = os.path.join(unpacked, PACKAGE_NAME)
    if not os.path.isdir(new):
        new = os.path.join(unpacked, OLD_PACKAGE_NAME)
    engine = os.path.join(new, ENGINE, 'appli_patch')
    new_version = os.path.join(engine, 'version.json')
    if not os.path.isfile(new_version) or not os.path.isfile(os.path.join(engine, 'appli.py')):
        raise Problem(tr("Le fichier téléchargé n'est pas l'outil attendu."))
    with open(new_version, encoding='utf-8') as handle:
        if json.load(handle).get('version') != version:
            raise Problem(tr("Le fichier téléchargé n'est pas la version annoncée."))
    return new

def install_tool(new: str, root: str) -> None:
    engine, old_engine = (os.path.join(root, ENGINE), os.path.join(root, ENGINE + '.ancien'))
    shutil.rmtree(old_engine, ignore_errors=True)
    os.replace(engine, old_engine)
    try:
        shutil.copytree(os.path.join(new, ENGINE), engine)
    except BaseException:
        shutil.rmtree(engine, ignore_errors=True)
        os.replace(old_engine, engine)
        raise
    for name in os.listdir(new):
        source, target = (os.path.join(new, name), os.path.join(root, name))
        if name.endswith('.app') and os.path.isdir(source):
            shutil.rmtree(target, ignore_errors=True)
            shutil.copytree(source, target)
        elif name not in KEPT and os.path.isfile(source):
            shutil.copy2(source, target + '.nouveau')
            os.replace(target + '.nouveau', target)
    for name in OBSOLETE:
        if os.path.isfile(os.path.join(root, name)) and (not os.path.exists(os.path.join(new, name))):
            os.remove(os.path.join(root, name))
    shutil.rmtree(old_engine, ignore_errors=True)

def settings() -> dict:
    try:
        with open(SETTINGS, encoding='utf-8') as handle:
            stored = json.load(handle)
    except (OSError, ValueError):
        return {}
    return stored if isinstance(stored, dict) else {}

def remember(**values) -> None:
    with _SETTINGS_LOCK:
        stored = settings()
        stored.update({k: v for k, v in values.items() if v is not None})
        os.makedirs(os.path.dirname(SETTINGS), exist_ok=True)
        temporary = SETTINGS + '.tmp'
        with open(temporary, 'w', encoding='utf-8') as handle:
            json.dump(stored, handle, ensure_ascii=False, indent=1)
        os.replace(temporary, SETTINGS)

def phone_run(adb: str, serial: str, *args, timeout: int=60) -> tuple[int, str, str]:
    return copie_android.run(adb, '-s', serial, *args, timeout=timeout)

def phone_signature(adb: str, serial: str):
    _, out, _ = phone_run(adb, serial, 'shell', 'dumpsys', 'package', copie_android.PACKAGE)
    found = copie_android.SIGNATURES.search(out)
    return found.group(1) if found else None

def phone_game_version(adb: str, serial: str):
    _, out, _ = phone_run(adb, serial, 'shell', 'cat', copie_android.EDITOR_VERSION)
    try:
        info = json.loads(out)
    except ValueError:
        return None
    return info.get('jeu') or info.get('version') if isinstance(info, dict) else None

def apk_game_version(apk: str):
    try:
        with zipfile.ZipFile(apk) as archive:
            info = json.loads(archive.read(APK_VERSION))
    except (OSError, KeyError, ValueError, zipfile.BadZipFile):
        return None
    return info.get('jeu') or info.get('version') if isinstance(info, dict) else None

def phone_save(adb: str, serial: str, copies: str):
    _, out, _ = phone_run(adb, serial, 'shell', 'ls', copie_android.EDITOR_SAVE)
    if copie_android.EDITOR_SAVE not in out:
        return None
    os.makedirs(copies, exist_ok=True)
    local = os.path.join(copies, f'TELEPHONE_{datetime.datetime.now():%Y-%m-%d_%H%M%S}.msgpack')
    phone_run(adb, serial, 'pull', copie_android.EDITOR_SAVE, local, timeout=120)
    return local if os.path.isfile(local) and os.path.getsize(local) > 0 else None

def reinstall(adb: str, serial: str, apk: str, progress=None) -> None:
    phone_run(adb, serial, 'uninstall', copie_android.PACKAGE, timeout=300)
    copie_android.install(adb, serial, apk, progress)

def apply_apk_save(adb: str, serial: str, apk: str) -> None:
    with zipfile.ZipFile(apk) as archive:
        data = archive.read(APK_SAVE)
    phone_run(adb, serial, 'shell', 'am', 'force-stop', copie_android.PACKAGE)
    parts = msgpack.unpackb(data, raw=False, strict_map_key=False, timestamp=0).get('save') or {}
    _, listing, _ = phone_run(adb, serial, 'shell', 'ls', '-d', EDITOR_FOLDER)
    if 'UnlockedHeroes' not in parts or EDITOR_FOLDER not in listing:
        _, out, err = phone_run(adb, serial, 'shell', 'pm', 'clear', copie_android.PACKAGE, timeout=120)
        if 'Success' not in out + err:
            raise copie_android.Problem(tr("La sauvegarde n'a pas pu être posée sur le téléphone."))
        return
    with tempfile.TemporaryDirectory() as work:
        local = os.path.join(work, 'a_importer.msgpack')
        with open(local, 'wb') as handle:
            handle.write(data)
        phone_run(adb, serial, 'push', local, copie_android.EDITOR_IMPORT + '.tmp', timeout=120)
    phone_run(adb, serial, 'shell', 'mv', copie_android.EDITOR_IMPORT + '.tmp', copie_android.EDITOR_IMPORT)
    _, check, _ = phone_run(adb, serial, 'shell', 'ls', '-l', copie_android.EDITOR_IMPORT)
    if str(len(data)) not in check:
        raise copie_android.Problem(tr("La sauvegarde n'a pas pu être posée sur le téléphone."))
