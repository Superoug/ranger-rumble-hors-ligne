import json
import os
import platform
import plistlib
import shutil
import signal
import subprocess
import sys
import threading
import time
import zipfile
from pathlib import Path
import langues
from langues import tr
HERE = Path(__file__).resolve().parent
NATIVE = HERE.parent / 'jeu_natif'
BASE = Path.home() / 'Library' / 'Application Support' / 'RangerRumble Mac'
APK = BASE / 'jeu.apk'
LIBS = BASE / 'lib' / 'arm64-v8a'
INFO = BASE / 'jeu.json'
PID = BASE / 'jeu.pid'
APP_SOURCE = BASE / 'app_source.txt'
APP = BASE / 'Ranger Rumble.app'
ICON = APP / 'Contents' / 'Resources' / 'icone.png'
EXECUTABLE = APP / 'Contents' / 'MacOS' / 'Ranger Rumble'
PORT = 18443
KEYS = BASE / 'touches.txt'
ACTIONS = ('haut', 'bas', 'gauche', 'droite', 'saut', 'eclair', 'cle', 'dash', 'ultime')
DEFAULT_KEYS = {'haut': [13, 126], 'bas': [1, 125], 'gauche': [0, 123], 'droite': [2, 124], 'saut': [49], 'eclair': [14], 'cle': [12, 3], 'dash': [56], 'ultime': [15]}
NOT_KEYS = {53, 54, 55}
KEY_CODES = 128
KEYS_PER_ACTION = 4
STUDIO_JAVA = Path('/Applications/Android Studio.app/Contents/jbr/Contents/Home/bin/java')
SDK_MOLTENVK = Path.home() / 'Library/Android/sdk/emulator/lib64/vulkan/libMoltenVK.dylib'

class Probleme(Exception):
    pass

def supported() -> bool:
    return sys.platform == 'darwin' and platform.machine() == 'arm64'

def program() -> Path | None:
    path = NATIVE / 'essai_p1'
    return path if path.is_file() else None

def server_classes() -> Path | None:
    path = NATIVE / 'serveur_mac' / 'classes'
    return path if (path / 'rr' / 'offline' / 'ServeurMac.class').is_file() else None

def moltenvk() -> Path | None:
    return next((path for path in (NATIVE / 'libMoltenVK.dylib', SDK_MOLTENVK) if path.is_file()), None)

def java() -> Path | None:
    for path in (NATIVE / 'java' / 'bin' / 'java', STUDIO_JAVA):
        if path.is_file():
            return path
    try:
        home = subprocess.run(['/usr/libexec/java_home'], capture_output=True, text=True, timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        home = ''
    path = Path(home) / 'bin' / 'java' if home else None
    return path if path and path.is_file() else None

def info() -> dict:
    try:
        return json.loads(INFO.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}

def prepared() -> bool:
    return APK.is_file() and (LIBS / 'libunity.so').is_file() and (LIBS / 'libil2cpp.so').is_file()

def running_pid() -> int | None:
    try:
        pid = int(PID.read_text())
        os.kill(pid, 0)
        return pid
    except (OSError, ValueError):
        return None

def coming_soon() -> bool:
    return not NATIVE.is_dir()

def missing() -> str | None:
    if coming_soon():
        return tr('Le jeu hors ligne sur ordinateur est en préparation.')
    if not supported():
        return tr('Il faut un Mac avec une puce Apple (M1 ou plus récent).')
    if not program() or not server_classes():
        return tr("Le programme du jeu pour Mac manque dans l'outil.")
    if not moltenvk():
        return tr("MoltenVK manque dans l'outil.")
    if not java():
        return tr('Java manque sur ce Mac.')
    return None

def state() -> dict:
    soon = coming_soon()
    return {'bientot': soon, 'mac': supported() and (not soon), 'manque': missing(), 'pret': prepared(), 'infos': info(), 'en_cours': running_pid() is not None, 'dossier': str(BASE), 'touches': keys()}

def keys() -> dict[str, list[int]]:
    try:
        lines = KEYS.read_text(encoding='utf-8').splitlines()
    except OSError:
        return {action: list(codes) for action, codes in DEFAULT_KEYS.items()}
    found = {action: [] for action in ACTIONS}
    for line in lines:
        parts = line.split()
        if parts and parts[0] in found:
            found[parts[0]] = [int(part) for part in parts[1:1 + KEYS_PER_ACTION] if part.isdigit() and int(part) < KEY_CODES]
    return found

def set_keys(chosen) -> dict[str, list[int]]:
    if chosen is None:
        KEYS.unlink(missing_ok=True)
        return keys()
    if not isinstance(chosen, dict):
        raise Probleme(tr('Touches illisibles.'))
    taken, lines = (set(), [])
    for action in ACTIONS:
        codes = []
        for code in chosen.get(action) or []:
            if isinstance(code, int) and 0 <= code < KEY_CODES and (code not in NOT_KEYS) and (code not in taken):
                codes.append(code)
                taken.add(code)
        lines.append(' '.join([action] + [str(code) for code in codes[:KEYS_PER_ACTION]]))
    BASE.mkdir(parents=True, exist_ok=True)
    KEYS.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return keys()

def prepare(official: str, save: str | None, new_game: bool, artworks: str | None, work: str, game_version: str, step) -> dict:
    import patcher
    if not supported():
        raise Probleme(tr('Il faut un Mac avec une puce Apple (M1 ou plus récent).'))
    if running_pid():
        raise Probleme(tr("Il faut d'abord fermer le jeu."))
    BASE.mkdir(parents=True, exist_ok=True)
    fresh = BASE / 'jeu_nouveau.apk'
    patcher.build(official, str(fresh), save=save, new_game=new_game, artworks=artworks, work=work, mac=True)
    step(0.99, tr('Préparation pour Mac...'))
    os.replace(fresh, APK)
    unpack_libraries()
    make_app()
    INFO.write_text(json.dumps({'jeu': game_version, 'date': time.strftime('%Y-%m-%d %H:%M'), 'sauvegarde': '' if new_game else os.path.basename(save or ''), 'nouvelle': bool(new_game)}, ensure_ascii=False), encoding='utf-8')
    print(tr('Le jeu est prêt sur ce Mac.'))
    return state()

def unpack_libraries() -> None:
    shutil.rmtree(LIBS, ignore_errors=True)
    LIBS.mkdir(parents=True)
    with zipfile.ZipFile(APK) as archive:
        for entry in archive.infolist():
            if entry.filename.startswith('lib/arm64-v8a/') and entry.filename.endswith('.so'):
                with archive.open(entry) as source, open(LIBS / os.path.basename(entry.filename), 'wb') as target:
                    shutil.copyfileobj(source, target, 1 << 20)

def make_app() -> None:
    source = program()
    if not source:
        raise Probleme(tr("Le programme du jeu pour Mac manque dans l'outil."))
    temporary = BASE / 'Ranger Rumble.app.tmp'
    contents = temporary / 'Contents'
    shutil.rmtree(temporary, ignore_errors=True)
    (contents / 'MacOS').mkdir(parents=True)
    (contents / 'Resources').mkdir()
    shutil.copy2(source, contents / 'MacOS' / 'Ranger Rumble')
    with open(contents / 'Info.plist', 'wb') as handle:
        plistlib.dump({'CFBundleName': 'Ranger Rumble', 'CFBundleDisplayName': 'Ranger Rumble', 'CFBundleIdentifier': 'rr.horsligne.jeu', 'CFBundleExecutable': 'Ranger Rumble', 'CFBundlePackageType': 'APPL', 'CFBundleShortVersionString': info().get('jeu', '1.0'), 'LSMinimumSystemVersion': '14.4', 'NSHighResolutionCapable': True}, handle)
    picture = game_icon()
    if picture is not None:
        (contents / 'Resources' / 'icone.png').write_bytes(picture)
    rights = NATIVE / 'droits.plist'
    command = ['codesign', '-f', '-s', '-'] + (['--entitlements', str(rights)] if rights.is_file() else [])
    done = subprocess.run(command + [str(temporary)], capture_output=True, text=True)
    if done.returncode:
        raise Probleme(tr('Signature du jeu impossible : {error}', error=done.stderr.strip()))
    shutil.rmtree(APP, ignore_errors=True)
    os.replace(temporary, APP)
    APP_SOURCE.write_text(fingerprint(source))

def game_icon() -> bytes | None:
    if not APK.is_file():
        return None
    with zipfile.ZipFile(APK) as archive:
        names = set(archive.namelist())
        for density in ('xxxhdpi', 'xxhdpi', 'xhdpi', 'hdpi'):
            for suffix in ('-v4', ''):
                name = f'res/mipmap-{density}{suffix}/app_icon.png'
                if name in names:
                    return archive.read(name)
    return None

def fingerprint(path: Path) -> str:
    status = path.stat()
    return f'{status.st_size} {int(status.st_mtime)}'

def app_current() -> bool:
    source = program()
    try:
        return EXECUTABLE.is_file() and source is not None and (APP_SOURCE.read_text() == fingerprint(source))
    except OSError:
        return False
WRAPPER = '\nS=\nif ! nc -z 127.0.0.1 "$RR_PORT" 2>/dev/null; then\n  "$RR_JAVA" -cp "$RR_CLASSES" rr.offline.ServeurMac "$RR_BASE" "$RR_APK" > "$RR_BASE/serveur.log" 2>&1 &\n  S=$!\n  i=0\n  while ! nc -z 127.0.0.1 "$RR_PORT" 2>/dev/null && [ $i -lt 150 ]; do\n    kill -0 $S 2>/dev/null || exit 90\n    sleep 0.1; i=$((i+1))\n  done\nfi\n"$RR_EXE" "$RR_APK" "$RR_LIBS" "$RR_BASE" > "$RR_BASE/jeu.log" 2>&1\nR=$?\n[ -n "$S" ] && kill $S 2>/dev/null\nexit $R\n'

def play(on_end) -> dict:
    problem = missing()
    if problem:
        raise Probleme(problem)
    if not prepared():
        raise Probleme(tr("Il faut d'abord préparer le jeu."))
    if running_pid():
        raise Probleme(tr('Le jeu est déjà ouvert.'))
    if not app_current():
        make_app()
    env = dict(os.environ, RR_PORT=str(PORT), RR_JAVA=str(java()), RR_CLASSES=str(server_classes()), RR_BASE=str(BASE), RR_APK=str(APK), RR_LIBS=str(LIBS), RR_EXE=str(EXECUTABLE), RR_MOLTENVK=str(moltenvk()), RR_LANGUE=langues.CURRENT)
    if ICON.is_file():
        env['RR_ICONE'] = str(ICON)
    process = subprocess.Popen(['/bin/sh', '-c', WRAPPER], env=env, start_new_session=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    PID.write_text(str(process.pid))

    def wait():
        code = process.wait()
        try:
            if PID.read_text().strip() == str(process.pid):
                PID.unlink()
        except OSError:
            pass
        on_end(code)
    threading.Thread(target=wait, daemon=True).start()
    return state()

def stop() -> dict:
    pid = running_pid()
    if pid:
        try:
            os.killpg(pid, signal.SIGTERM)
        except OSError:
            pass
    return state()

def end_text(code: int) -> str | None:
    if code in (0, -signal.SIGTERM, 128 + signal.SIGTERM):
        return None
    if code == 90:
        return tr("Le serveur hors ligne n'a pas démarré. Voir {log}.", log=str(BASE / 'serveur.log'))
    return tr("Le jeu s'est arrêté (code {code}). Voir {log}.", code=code, log=str(BASE / 'jeu.log'))
