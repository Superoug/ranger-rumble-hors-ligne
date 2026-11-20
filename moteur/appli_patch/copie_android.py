import base64
import datetime
import functools
import os
import platform
import random
import re
import shutil
import ssl
import stat
import subprocess
import time
import urllib.request
import zipfile
import msgpack
from langues import tr
PACKAGE = 'com.playstation.rattlesnake'
EDITOR_FOLDER = f'/sdcard/Android/data/{PACKAGE}/files/rr_editeur'
EDITOR_VERSION = EDITOR_FOLDER + '/version.json'
EDITOR_SAVE = EDITOR_FOLDER + '/sauvegarde_actuelle.msgpack'
EDITOR_IMPORT = EDITOR_FOLDER + '/a_importer.msgpack'
SERVER_DATA = 'donnees_serveur'
ADB_FOLDER = os.path.join(os.path.expanduser('~'), '.sauvegarde-rr', 'android-sdk', 'platform-tools')
ADB_PAGE = 'https://developer.android.com/tools/releases/platform-tools'
ADB_ZIP = 'https://dl.google.com/android/repository/platform-tools-latest-{}.zip'
OFFICIAL_SIGNATURE = '7a1339bc'
SIGNATURES = re.compile('signatures:\\[([0-9a-f]+)\\]')
ID_LETTERS = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
QUIET = {'creationflags': subprocess.CREATE_NO_WINDOW} if os.name == 'nt' else {}
PHONE_TEMPORARY = '/data/local/tmp/rr_installation.apk'
INSTALL_COPY_SHARE = 0.8
BUILTIN_CONFIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ressources', 'config_jeu.msgpack')
NO_DATE = msgpack.Timestamp(-62135596800, 0)

class Problem(Exception):
    pass

class OtherSignature(Problem):
    pass

def say(text: str='') -> None:
    print(text, flush=True)

def unpack(raw: bytes, **options):
    return msgpack.unpackb(raw, raw=False, strict_map_key=False, **options)

def pack(value) -> bytes:
    return msgpack.packb(value, use_bin_type=True)

def random_text(letters: str, size: int) -> str:
    chance = random.SystemRandom()
    return ''.join((chance.choice(letters) for _ in range(size)))

@functools.cache
def _https_context() -> ssl.SSLContext:
    try:
        import certifi
    except ImportError:
        return ssl.create_default_context()
    return ssl.create_default_context(cafile=certifi.where())

def url_open(url: str, timeout: int=60):
    request = urllib.request.Request(url, headers={'User-Agent': 'RangerRumbleHorsLigne'})
    return urllib.request.urlopen(request, timeout=timeout, context=_https_context())

def find_adb() -> str | None:
    name = 'adb.exe' if os.name == 'nt' else 'adb'
    home = os.path.expanduser('~')
    places = [shutil.which('adb'), os.path.join(ADB_FOLDER, name), os.path.join(home, 'Library', 'Android', 'sdk', 'platform-tools', name), os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Android', 'Sdk', 'platform-tools', name)]
    return next((p for p in places if p and os.path.isfile(p)), None)

def download_adb() -> str:
    system = 'darwin' if platform.system() == 'Darwin' else 'windows'
    target = os.path.dirname(ADB_FOLDER)
    os.makedirs(target, exist_ok=True)
    archive = os.path.join(target, 'platform-tools.zip')
    say(tr('Téléchargement des outils Android...'))
    with url_open(ADB_ZIP.format(system), timeout=120) as answer, open(archive, 'wb') as out:
        shutil.copyfileobj(answer, out)
    shutil.rmtree(ADB_FOLDER, ignore_errors=True)
    with zipfile.ZipFile(archive) as content:
        content.extractall(target)
    os.remove(archive)
    adb = find_adb()
    if not adb:
        raise Problem(tr("Les outils Android n'ont pas pu être installés."))
    if os.name != 'nt':
        os.chmod(adb, os.stat(adb).st_mode | stat.S_IXUSR)
    return adb

def run(adb: str, *args, timeout: int=60) -> tuple[int, str, str]:
    done = subprocess.run([adb, *args], capture_output=True, timeout=timeout, **QUIET)
    return (done.returncode, done.stdout.decode('utf-8', 'replace'), done.stderr.decode('utf-8', 'replace'))

def phones(adb: str) -> list[tuple[str, str, str]]:
    _, out, _ = run(adb, 'devices', '-l', timeout=30)
    found = []
    for line in out.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2:
            model = next((p.split(':', 1)[1] for p in parts[2:] if p.startswith('model:')), '')
            found.append((parts[0], parts[1], model.replace('_', ' ')))
    return found

def install(adb: str, serial: str, apk: str, progress=None) -> None:
    text = sent_install(adb, serial, apk, progress) if progress else None
    if text is None:
        code, out, err = run(adb, '-s', serial, 'install', '-r', apk, timeout=900)
        text = (out + err).strip()
        if code == 0 and 'Success' in text:
            return
    elif text == 'Success':
        return
    if 'UPDATE_INCOMPATIBLE' in text or 'SIGNATURES_DO_NOT_MATCH' in text:
        raise OtherSignature(tr("Ranger Rumble est déjà sur le téléphone, signé par quelqu'un d'autre : il faut le désinstaller, puis recommencer."))
    if no_room(text):
        raise Problem(tr('Pas assez de place sur le téléphone (3 Go).'))
    raise Problem(tr('Installation impossible : {v}', v=text[-300:]))

def no_room(answer: str) -> bool:
    return 'INSUFFICIENT_STORAGE' in answer or 'not enough space' in answer

def sent_install(adb: str, serial: str, apk: str, progress) -> str | None:
    size = os.path.getsize(apk)
    copying = subprocess.Popen([adb, '-s', serial, 'push', apk, PHONE_TEMPORARY], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **QUIET)
    try:
        while copying.poll() is None:
            time.sleep(1)
            _, out, _ = run(adb, '-s', serial, 'shell', 'stat', '-c', '%s', PHONE_TEMPORARY, timeout=30)
            if out.strip().isdigit():
                progress(min(int(out.strip()) / size, 1) * INSTALL_COPY_SHARE)
        if copying.returncode != 0:
            return None
        progress(INSTALL_COPY_SHARE)
        _, out, err = run(adb, '-s', serial, 'shell', 'pm', 'install', '-r', PHONE_TEMPORARY, timeout=900)
        text = (out + err).strip()
        if no_room(text):
            return None
        return 'Success' if 'Success' in text else text
    finally:
        if copying.poll() is None:
            copying.kill()
            copying.wait()
        run(adb, '-s', serial, 'shell', 'rm', '-f', PHONE_TEMPORARY, timeout=60)

def new_player_id() -> str:
    return random_text(ID_LETTERS, 8)

def timestamp(when: datetime.datetime) -> msgpack.Timestamp:
    return msgpack.Timestamp.from_unix(when.timestamp())

def login_answer(player: str) -> dict:
    now = datetime.datetime.now(datetime.timezone.utc)
    offset = round(datetime.datetime.now().astimezone().utcoffset().total_seconds() / 3600, 2)
    return {'publicId': player, 'obbToken': '', 'userCountryCode': '', 'createdAt': timestamp(now), 'UtcOffset': float(offset), 'Tags': None, 'JWTMetadata': {}, 'SessionToken': '', 'error': '', 'updatedSecret': '', 'networkChoiceRequired': False, 'usersFound': None, 'usersCreateDates': None, 'deleteStatus': '', 'deleteAt': NO_DATE}
SOCIAL = {'invites': {'groupInvites': None, 'friendInvitesReceived': None, 'friendInvitesSent': None, 'profiles': None, 'groups': None, 'friendReceived': None, 'friendSent': None, 'received': [], 'sent': [], 'groupReceived': None, 'groupSent': None}, 'chats': {'chats': [], 'authors': [], 'count': 0}, 'friends': {'friendsList': [], 'friends': [], 'count': 0}, 'groups': {'groups': [], 'count': 0}}

def exchange_rates() -> bytes:
    day = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d 00:00:00+00')
    return ('{"date":"%s","base":"USD","rates":{"USD":"1"}}' % day).encode()
NEW_GAME_PARTS = '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'
STARTER_WEAPONS = (1, 229)

def new_account_save() -> dict:
    save = new_save()
    save['save'] = {}
    return save

def new_save() -> dict:
    parts = unpack(base64.b64decode(NEW_GAME_PARTS), timestamp=0)
    weapons = unpack(parts['UnlockedWeapons'][1])
    owned = weapons[0][0]
    owned += [[uid, []] for uid in STARTER_WEAPONS if not any((entry[0] == uid for entry in owned))]
    parts['UnlockedWeapons'][1] = pack(weapons)
    identity = unpack(parts['UserIdentity'][1])
    identity[0] = 'Player_' + random_text('0123456789abcdef', 5)
    parts['UserIdentity'][1] = pack(identity)
    save = {part: {'className': '', 'version': version, 'bytes': data, 'jsonDump': '', 'overlayClassName': '', 'overlayVersion': 0, 'bytesOverlay': None, 'overlayJsonDump': '', 'isPublic': False} for part, (version, data) in parts.items()}
    return {'cheatingTimeOffset': 0, 'utcOffset': 1.0, 'platform': 'android', 'buildNumber': '8689', 'gcVersionId': '1.10.4.124:platform/android,build/8689', 'lastExecDate': NO_DATE, 'CustomBundleHash': '', 'UnreadSinceAppliedBackup': False, 'events': {}, 'save': save}

def builtin_copy(folder: str) -> str | None:
    if not os.path.isfile(BUILTIN_CONFIG):
        return None
    with open(BUILTIN_CONFIG, 'rb') as handle:
        config = unpack(handle.read())
    return write_copy(config, folder)

def write_copy(config: dict, copies: str, player: str | None=None) -> str:
    player = player or new_player_id()
    stamp = datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')
    folder = os.path.join(copies, f'ANDROID_{player}_{stamp}')
    data = os.path.join(folder, SERVER_DATA)
    os.makedirs(os.path.join(data, 'items'))
    files = {'config-map.msgpack': pack(config), 'vnum.txt': config['Vnum'].encode(), 'login.msgpack': pack(login_answer(player)), **{f'{name}.msgpack': pack(answer) for name, answer in SOCIAL.items()}, 'er.json': exchange_rates()}
    for name, content in files.items():
        with open(os.path.join(data, name), 'wb') as handle:
            handle.write(content)
    return folder
