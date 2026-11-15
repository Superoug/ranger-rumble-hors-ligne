import datetime
import hashlib
import os
import platform
import random
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
import msgpack
PACKAGE = 'com.playstation.rattlesnake'
CACHE = f'/sdcard/Android/data/{PACKAGE}/files/online-cache/gc'
CACHE_PASSWORD = 'online-cache/gc/'
RECORDINGS = f'/sdcard/Android/data/{PACKAGE}/files/copie'
ACCOUNT = re.compile('[A-Za-z0-9_-]{4,40}')
VNUM = '1.10.4.124'
BUILD = b'8689'
SERVER_DATA = 'donnees_serveur'
ADB_FOLDER = os.path.join(os.path.expanduser('~'), '.sauvegarde-rr', 'android-sdk', 'platform-tools')
ADB_PAGE = 'https://developer.android.com/tools/releases/platform-tools'
ADB_ZIP = 'https://dl.google.com/android/repository/platform-tools-latest-{}.zip'
HASH = re.compile('[0-9a-f]{12}')
OFFICIAL_SIGNATURE = '7a1339bc'
SIGNATURES = re.compile('signatures:\\[([0-9a-f]+)\\]')
ID_LETTERS = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'

class Problem(Exception):
    pass

def say(text=''):
    print(text, flush=True)

def url_open(url, timeout=60):
    import ssl
    try:
        import certifi
        context = ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        context = ssl.create_default_context()
    request = urllib.request.Request(url, headers={'User-Agent': 'RangerRumbleHorsLigne'})
    return urllib.request.urlopen(request, timeout=timeout, context=context)

def find_adb():
    name = 'adb.exe' if os.name == 'nt' else 'adb'
    places = [shutil.which('adb'), os.path.join(ADB_FOLDER, name)]
    home = os.path.expanduser('~')
    places += [os.path.join(home, 'Library', 'Android', 'sdk', 'platform-tools', name), os.path.join(home, 'Android', 'Sdk', 'platform-tools', name), os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Android', 'Sdk', 'platform-tools', name)]
    return next((p for p in places if p and os.path.isfile(p)), None)

def download_adb():
    system = {'Darwin': 'darwin', 'Windows': 'windows'}.get(platform.system(), 'linux')
    target = os.path.dirname(ADB_FOLDER)
    os.makedirs(target, exist_ok=True)
    archive = os.path.join(target, 'platform-tools.zip')
    say('Téléchargement des outils Android de Google (environ 10 Mo)...')
    with url_open(ADB_ZIP.format(system), timeout=120) as answer, open(archive, 'wb') as out:
        shutil.copyfileobj(answer, out)
    shutil.rmtree(ADB_FOLDER, ignore_errors=True)
    with zipfile.ZipFile(archive) as content:
        content.extractall(target)
    os.remove(archive)
    adb = find_adb()
    if adb and os.name != 'nt':
        os.chmod(adb, os.stat(adb).st_mode | stat.S_IXUSR)
    if not adb:
        raise Problem("Les outils Android n'ont pas pu être installés.")
    return adb

def run(adb, *args, timeout=60):
    done = subprocess.run([adb, *args], capture_output=True, timeout=timeout)
    return (done.returncode, done.stdout.decode('utf-8', 'replace'), done.stderr.decode('utf-8', 'replace'))

def phones(adb):
    code, out, err = run(adb, 'devices', '-l', timeout=30)
    found = []
    for line in out.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2:
            model = next((p.split(':', 1)[1] for p in parts[2:] if p.startswith('model:')), '')
            found.append((parts[0], parts[1], model.replace('_', ' ')))
    return found

def pull_cache(adb, serial, folder):
    code, out, err = run(adb, '-s', serial, 'shell', 'pm', 'list', 'packages', PACKAGE)
    if f'package:{PACKAGE}' not in out.split():
        raise Problem("Ranger Rumble n'est pas installé sur ce téléphone.")
    code, out, err = run(adb, '-s', serial, 'shell', 'dumpsys', 'package', PACKAGE)
    found = SIGNATURES.search(out)
    if found and found.group(1) != OFFICIAL_SIGNATURE:
        raise Problem("Ce téléphone a une version hors ligne de Ranger Rumble, pas le jeu officiel. La copie se fait depuis le jeu officiel, avant d'installer la version hors ligne.")
    code, out, err = run(adb, '-s', serial, 'shell', 'ls', CACHE)
    names = [n for n in out.split() if HASH.fullmatch(n) or n == 'manifest']
    if 'manifest' not in names:
        if 'denied' in (out + err).lower():
            raise Problem("Le téléphone refuse l'accès au dossier du jeu.")
        raise Problem("Le jeu officiel n'a pas encore enregistré ses données sur ce téléphone : ouvre-le, connecté à internet, et attends l'écran d'accueil.")
    os.makedirs(folder, exist_ok=True)
    for name in names:
        code, out, err = run(adb, '-s', serial, 'pull', f'{CACHE}/{name}', os.path.join(folder, name), timeout=120)
        if code != 0:
            raise Problem(f'Copie impossible depuis le téléphone : {(err or out).strip()[:200]}')
    return len(names)

def decrypt(blob, password):
    from cryptography.hazmat.primitives import padding
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    size = blob[0]
    if size not in (16, 24, 32) or len(blob) < 1 + 2 * size + 16:
        raise ValueError('format inconnu')
    salt, iv, data = (blob[1:1 + size], blob[1 + size:1 + 2 * size], blob[1 + 2 * size:])
    key = hashlib.pbkdf2_hmac('sha1', password.encode('utf-8'), salt, 16, size)
    decryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
    plain = decryptor.update(data) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    return unpadder.update(plain) + unpadder.finalize()

def binary_strings(data):
    found = []
    i = 0
    while i < len(data) - 6:
        if data[i] == 6:
            length, shift, j = (0, 0, i + 5)
            while j < len(data) and shift < 35:
                byte = data[j]
                length |= (byte & 127) << shift
                j += 1
                shift += 7
                if not byte & 128:
                    break
            if 0 < length <= 256 and j + length <= len(data):
                try:
                    text = data[j:j + length].decode('utf-8')
                except UnicodeDecodeError:
                    text = None
                if text and text.isprintable():
                    found.append(text)
                    i = j + length
                    continue
        i += 1
    return found

def manifest_items(manifest):
    if BUILD not in manifest:
        raise Problem('Les données du jeu sur ce téléphone ne sont pas celles de la version 1.10.4.')
    strings = binary_strings(manifest)
    pairs = []
    for key, value in zip(strings, strings[1:]):
        if HASH.fullmatch(value) and (not HASH.fullmatch(key)):
            pairs.append((key, value))
    return pairs

def config_from_cache(folder):
    manifest = decrypt(open(os.path.join(folder, 'manifest'), 'rb').read(), CACHE_PASSWORD + 'manifest')
    items = []
    missing = []
    for key, digest in manifest_items(manifest):
        path = os.path.join(folder, digest)
        if not os.path.isfile(path):
            missing.append(key)
            continue
        items.append({'key': key, 'hash': digest, 'url': None, 'value': decrypt(open(path, 'rb').read(), CACHE_PASSWORD + digest)})
    if missing or len(items) < 30:
        raise Problem("Les données du jeu sur ce téléphone sont incomplètes : ouvre le jeu officiel, connecté à internet, attends l'écran d'accueil, puis recommence.")
    return {'items': items, 'Vnum': VNUM}

def new_player_id():
    return ''.join((random.SystemRandom().choice(ID_LETTERS) for _ in range(8)))

def timestamp(when):
    return msgpack.Timestamp.from_unix(when.timestamp())

def login_answer(player):
    now = datetime.datetime.now(datetime.timezone.utc)
    offset = round(datetime.datetime.now().astimezone().utcoffset().total_seconds() / 3600, 2)
    return {'publicId': player, 'obbToken': '', 'userCountryCode': '', 'createdAt': timestamp(now), 'UtcOffset': float(offset), 'Tags': None, 'JWTMetadata': {}, 'SessionToken': '', 'error': '', 'updatedSecret': '', 'networkChoiceRequired': False, 'usersFound': None, 'usersCreateDates': None, 'deleteStatus': '', 'deleteAt': msgpack.Timestamp(-62135596800, 0)}
SOCIAL = {'invites': {'groupInvites': None, 'friendInvitesReceived': None, 'friendInvitesSent': None, 'profiles': None, 'groups': None, 'friendReceived': None, 'friendSent': None, 'received': [], 'sent': [], 'groupReceived': None, 'groupSent': None}, 'chats': {'chats': [], 'authors': [], 'count': 0}, 'friends': {'friendsList': [], 'friends': [], 'count': 0}, 'groups': {'groups': [], 'count': 0}}

def exchange_rates():
    day = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d 00:00:00+00')
    return ('{"date":"%s","base":"USD","rates":{"USD":"1"}}' % day).encode()
NEW_GAME_PARTS = '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'

def new_save():
    import base64
    parts = msgpack.unpackb(base64.b64decode(NEW_GAME_PARTS), raw=False, strict_map_key=False, timestamp=0)
    name = 'Player_' + ''.join((random.SystemRandom().choice('0123456789abcdef') for _ in range(5)))
    identity = msgpack.unpackb(parts['UserIdentity'][1], raw=False)
    identity[0] = name
    parts['UserIdentity'][1] = msgpack.packb(identity, use_bin_type=True)
    save = {}
    for part, (version, data) in parts.items():
        save[part] = {'className': '', 'version': version, 'bytes': data, 'jsonDump': '', 'overlayClassName': '', 'overlayVersion': 0, 'bytesOverlay': None, 'overlayJsonDump': '', 'isPublic': False}
    return {'cheatingTimeOffset': 0, 'utcOffset': 1.0, 'platform': 'android', 'buildNumber': '8689', 'gcVersionId': '1.10.4.124:platform/android,build/8689', 'lastExecDate': msgpack.Timestamp(-62135596800, 0), 'CustomBundleHash': '', 'UnreadSinceAppliedBackup': False, 'events': {}, 'save': save}

def pack(value):
    return msgpack.packb(value, use_bin_type=True)

def write_copy(config, copies, player=None):
    player = player or new_player_id()
    stamp = datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')
    folder = os.path.join(copies, f'ANDROID_{player}_{stamp}')
    data = os.path.join(folder, SERVER_DATA)
    os.makedirs(os.path.join(data, 'items'))
    open(os.path.join(data, 'config-map.msgpack'), 'wb').write(pack(config))
    open(os.path.join(data, 'vnum.txt'), 'w').write(config['Vnum'])
    open(os.path.join(data, 'login.msgpack'), 'wb').write(pack(login_answer(player)))
    for name, answer in SOCIAL.items():
        open(os.path.join(data, f'{name}.msgpack'), 'wb').write(pack(answer))
    open(os.path.join(data, 'er.json'), 'wb').write(exchange_rates())
    with open(os.path.join(folder, 'INFO.txt'), 'w', encoding='utf-8') as info:
        info.write(f"Copie Android par câble du {stamp}\nIdentifiant du joueur : {player}\nÉléments de configuration : {len(config['items'])}\nPas de sauvegarde : choisis une sauvegarde exportée, ou une nouvelle partie, pour l'APK.\n")
    return folder

def file_digest(path):
    with open(path, 'rb') as handle:
        return hashlib.sha256(handle.read()).hexdigest()

def pull_recordings(adb, serial, copies):
    import donnees_capture
    code, out, err = run(adb, '-s', serial, 'shell', 'ls', RECORDINGS)
    accounts = [name for name in out.split() if ACCOUNT.fullmatch(name)] if code == 0 else []
    found = []
    for account in accounts:
        work = tempfile.mkdtemp(prefix='rr_copie_')
        try:
            code, out, err = run(adb, '-s', serial, 'pull', '-a', f'{RECORDINGS}/{account}', work, timeout=600)
            source = os.path.join(work, account)
            save = os.path.join(source, 'save.msgpack')
            if code != 0 or not os.path.isfile(save):
                continue
            when = os.path.getmtime(save)
            complete = not donnees_capture.missing_files(source)
            same = [os.path.join(copies, name) for name in sorted(os.listdir(copies)) if name.startswith(f'ANDROID_{account}_') and os.path.isfile(os.path.join(copies, name, 'save.msgpack')) and (file_digest(os.path.join(copies, name, 'save.msgpack')) == file_digest(save)) and (not donnees_capture.missing_files(os.path.join(copies, name)))]
            if same:
                say(f'Compte {account} : cette sauvegarde est déjà copiée.')
                found.append((when, same[-1], True))
                continue
            stamp = datetime.datetime.fromtimestamp(when).strftime('%Y-%m-%d_%H%M%S')
            folder = os.path.join(copies, f'ANDROID_{account}_{stamp}')
            if os.path.exists(folder):
                shutil.rmtree(folder)
            shutil.copytree(source, folder, ignore=shutil.ignore_patterns('*.tmp'))
            found.append((when, folder, complete))
        finally:
            shutil.rmtree(work, ignore_errors=True)
    return [(folder, complete) for _, folder, complete in sorted(found, reverse=True)]

def install(adb, serial, apk):
    code, out, err = run(adb, '-s', serial, 'install', '-r', apk, timeout=900)
    text = (out + err).strip()
    if code == 0 and 'Success' in text:
        return
    if 'UPDATE_INCOMPATIBLE' in text or 'SIGNATURES_DO_NOT_MATCH' in text:
        raise Problem("Le téléphone a déjà Ranger Rumble, signé par quelqu'un d'autre (le jeu officiel, ou une version hors ligne d'un autre ordinateur). Désinstalle-le sur le téléphone (appui long sur son icône > Désinstaller), puis recommence.")
    if 'INSUFFICIENT_STORAGE' in text:
        raise Problem('Pas assez de place sur le téléphone : il faut environ 3 Go libres.')
    raise Problem(f'Installation impossible : {text[-300:]}')

def copy_phone(adb, serial, copies):
    recorded = pull_recordings(adb, serial, copies)
    if recorded:
        for folder, complete in recorded:
            if complete:
                say(f'Copie de RR Copie récupérée, avec la sauvegarde : {folder}')
                return folder
        for folder, _ in recorded:
            shutil.rmtree(folder, ignore_errors=True)
        raise Problem("RR Copie n'a pas fini sa copie sur ce téléphone. Ouvre RR Copie, connecté à internet, attends le message « C'est fait » sur l'écran d'accueil du jeu, puis recommence.")
    code, out, err = run(adb, '-s', serial, 'shell', 'dumpsys', 'package', PACKAGE)
    found = SIGNATURES.search(out)
    if found and found.group(1) != OFFICIAL_SIGNATURE and ('rr.offline.Options' not in out):
        raise Problem("RR Copie est installée mais n'a encore rien copié. Ouvre-la, connecte-toi à ton compte, attends le message « C'est fait » sur l'écran d'accueil du jeu, puis recommence.")
    work = tempfile.mkdtemp(prefix='rr_android_')
    try:
        say('Copie des données du jeu depuis le téléphone...')
        count = pull_cache(adb, serial, work)
        say(f'  {count} fichiers copiés. Déchiffrement...')
        config = config_from_cache(work)
        folder = write_copy(config, copies)
        say(f"Copie terminée : {len(config['items'])} éléments de configuration du jeu.")
        say(f'  Dossier : {folder}')
        return folder
    finally:
        shutil.rmtree(work, ignore_errors=True)
if __name__ == '__main__':
    config = config_from_cache(sys.argv[1])
    print(write_copy(config, sys.argv[2]))
