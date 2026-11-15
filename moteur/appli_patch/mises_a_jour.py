import hashlib
import json
import os
import shutil
import tempfile
import zipfile
import copie_android
HERE = os.path.dirname(os.path.abspath(__file__))
VERSION_FILE = os.path.join(HERE, 'version.json')
SETTINGS = os.path.join(os.path.expanduser('~'), '.sauvegarde-rr', 'reglages.json')
PACKAGE_NAME = 'OutilSauvegardeRR'
ASSET = PACKAGE_NAME + '.zip'

class Problem(Exception):
    pass

def current():
    with open(VERSION_FILE, encoding='utf-8') as handle:
        return json.load(handle)

def parse(version):
    parts = []
    for piece in str(version).lstrip('vV').split('.'):
        digits = ''.join((c for c in piece if c.isdigit()))
        parts.append(int(digits) if digits else 0)
    return tuple(parts)

def newer(candidate, installed):
    a, b = (parse(candidate), parse(installed))
    width = max(len(a), len(b))
    return a + (0,) * (width - len(a)) > b + (0,) * (width - len(b))

def latest_release(depot=None):
    depot = depot or current()['depot']
    try:
        with copie_android.url_open(f'https://api.github.com/repos/{depot}/releases/latest', timeout=15) as answer:
            release = json.load(answer)
    except Exception:
        return None
    assets = {a.get('name'): a.get('browser_download_url') for a in release.get('assets', [])}
    tag = str(release.get('tag_name', '')).lstrip('vV')
    if not tag:
        return None
    game = None
    if assets.get('version.json'):
        try:
            with copie_android.url_open(assets['version.json'], timeout=15) as answer:
                game = json.load(answer).get('jeu')
        except Exception:
            game = None
    return {'version': tag, 'jeu': game, 'notes': (release.get('body') or '').strip(), 'page': release.get('html_url'), 'zip': assets.get(ASSET), 'sha256': assets.get(ASSET + '.sha256')}

def download(url, path):
    with copie_android.url_open(url, timeout=300) as answer, open(path, 'wb') as out:
        shutil.copyfileobj(answer, out)

def update_tool(release, root, say=print):
    if not release.get('zip') or not release.get('sha256'):
        raise Problem("Cette version n'a pas le fichier de l'outil attendu : télécharge-la à la main sur sa page.")
    work = tempfile.mkdtemp(prefix='rr_maj_')
    try:
        archive = os.path.join(work, ASSET)
        say(f"Téléchargement de la version {release['version']}...")
        download(release['zip'], archive)
        sums = os.path.join(work, 'sha256')
        download(release['sha256'], sums)
        expected = open(sums, encoding='utf-8').read().split()[0].lower()
        digest = hashlib.sha256(open(archive, 'rb').read()).hexdigest()
        if digest != expected:
            raise Problem('Le fichier téléchargé est abîmé (empreinte différente). Réessaie plus tard.')
        unpacked = os.path.join(work, 'nouveau')
        with zipfile.ZipFile(archive) as content:
            for name in content.namelist():
                target = os.path.realpath(os.path.join(unpacked, name))
                if not target.startswith(os.path.realpath(unpacked) + os.sep):
                    raise Problem('Le fichier téléchargé contient des chemins inattendus.')
            content.extractall(unpacked)
        new = os.path.join(unpacked, PACKAGE_NAME)
        new_version = os.path.join(new, 'moteur', 'appli_patch', 'version.json')
        if not os.path.isfile(new_version) or not os.path.isfile(os.path.join(new, 'moteur', 'appli_patch', 'appli.py')):
            raise Problem("Le fichier téléchargé n'est pas l'outil attendu.")
        if json.load(open(new_version, encoding='utf-8')).get('version') != release['version']:
            raise Problem("Le fichier téléchargé n'est pas la version annoncée.")
        say('Installation...')
        old_engine = os.path.join(root, 'moteur.ancien')
        shutil.rmtree(old_engine, ignore_errors=True)
        os.replace(os.path.join(root, 'moteur'), old_engine)
        try:
            shutil.copytree(os.path.join(new, 'moteur'), os.path.join(root, 'moteur'))
        except Exception:
            shutil.rmtree(os.path.join(root, 'moteur'), ignore_errors=True)
            os.replace(old_engine, os.path.join(root, 'moteur'))
            raise
        for name in os.listdir(new):
            source = os.path.join(new, name)
            if name in ('moteur', 'Sauvegardes') or not os.path.isfile(source):
                continue
            shutil.copy2(source, os.path.join(root, name))
        shutil.rmtree(old_engine, ignore_errors=True)
        say(f"L'outil est maintenant en version {release['version']}.")
    finally:
        shutil.rmtree(work, ignore_errors=True)

def settings():
    try:
        with open(SETTINGS, encoding='utf-8') as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return {}

def remember(**values):
    stored = settings()
    stored.update({k: v for k, v in values.items() if v is not None})
    os.makedirs(os.path.dirname(SETTINGS), exist_ok=True)
    temporary = SETTINGS + '.tmp'
    with open(temporary, 'w', encoding='utf-8') as handle:
        json.dump(stored, handle, ensure_ascii=False, indent=1)
    os.replace(temporary, SETTINGS)

def phone_signature(adb, serial):
    _, out, _ = copie_android.run(adb, '-s', serial, 'shell', 'dumpsys', 'package', copie_android.PACKAGE, timeout=60)
    found = copie_android.SIGNATURES.search(out)
    return found.group(1) if found else None

def phone_game_version(adb, serial):
    remote = f'/sdcard/Android/data/{copie_android.PACKAGE}/files/rr_editeur/version.json'
    code, out, _ = copie_android.run(adb, '-s', serial, 'shell', 'cat', remote, timeout=60)
    try:
        info = json.loads(out)
        return info.get('jeu') or info.get('version')
    except ValueError:
        return None

def phone_save(adb, serial, copies):
    import datetime
    remote = f'/sdcard/Android/data/{copie_android.PACKAGE}/files/rr_editeur/sauvegarde_actuelle.msgpack'
    _, out, err = copie_android.run(adb, '-s', serial, 'shell', 'ls', remote, timeout=60)
    if remote not in out:
        return None
    os.makedirs(copies, exist_ok=True)
    local = os.path.join(copies, f'TELEPHONE_{datetime.datetime.now():%Y-%m-%d_%H%M%S}.msgpack')
    copie_android.run(adb, '-s', serial, 'pull', remote, local, timeout=120)
    return local if os.path.isfile(local) and os.path.getsize(local) > 0 else None

def reinstall(adb, serial, apk):
    copie_android.run(adb, '-s', serial, 'uninstall', copie_android.PACKAGE, timeout=300)
    copie_android.install(adb, serial, apk)
