import datetime
import os
import platform
import random
import re
import shutil
import stat
import subprocess
import time
import urllib.request
import zipfile
import msgpack
from langues import tr
PACKAGE = 'com.playstation.rattlesnake'
SERVER_DATA = 'donnees_serveur'
ADB_FOLDER = os.path.join(os.path.expanduser('~'), '.sauvegarde-rr', 'android-sdk', 'platform-tools')
ADB_PAGE = 'https://developer.android.com/tools/releases/platform-tools'
ADB_ZIP = 'https://dl.google.com/android/repository/platform-tools-latest-{}.zip'
OFFICIAL_SIGNATURE = '7a1339bc'
SIGNATURES = re.compile('signatures:\\[([0-9a-f]+)\\]')
ID_LETTERS = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'

class Problem(Exception):
    pass

class OtherSignature(Problem):
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
    places += [os.path.join(home, 'Library', 'Android', 'sdk', 'platform-tools', name), os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Android', 'Sdk', 'platform-tools', name)]
    return next((p for p in places if p and os.path.isfile(p)), None)

def download_adb():
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
    if adb and os.name != 'nt':
        os.chmod(adb, os.stat(adb).st_mode | stat.S_IXUSR)
    if not adb:
        raise Problem(tr("Les outils Android n'ont pas pu être installés."))
    return adb
QUIET = {'creationflags': subprocess.CREATE_NO_WINDOW} if os.name == 'nt' else {}

def run(adb, *args, timeout=60):
    done = subprocess.run([adb, *args], capture_output=True, timeout=timeout, **QUIET)
    return (done.returncode, done.stdout.decode('utf-8', 'replace'), done.stderr.decode('utf-8', 'replace'))

def phones(adb):
    _, out, _ = run(adb, 'devices', '-l', timeout=30)
    found = []
    for line in out.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2:
            model = next((p.split(':', 1)[1] for p in parts[2:] if p.startswith('model:')), '')
            found.append((parts[0], parts[1], model.replace('_', ' ')))
    return found

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
STARTER_WEAPONS = (1, 229)

def new_account_save():
    save = new_save()
    save['save'] = {}
    return save

def new_save():
    import base64
    parts = msgpack.unpackb(base64.b64decode(NEW_GAME_PARTS), raw=False, strict_map_key=False, timestamp=0)
    weapons = msgpack.unpackb(parts['UnlockedWeapons'][1], raw=False, strict_map_key=False)
    owned = weapons[0][0]
    owned += [[uid, []] for uid in STARTER_WEAPONS if not any((entry[0] == uid for entry in owned))]
    parts['UnlockedWeapons'][1] = msgpack.packb(weapons, use_bin_type=True)
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
BUILTIN_CONFIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ressources', 'config_jeu.msgpack')

def builtin_copy(folder):
    if not os.path.isfile(BUILTIN_CONFIG):
        return None
    with open(BUILTIN_CONFIG, 'rb') as handle:
        config = msgpack.unpackb(handle.read(), raw=False, strict_map_key=False)
    return write_copy(config, folder)

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
    return folder

def install(adb, serial, apk, progress=None):
    text = sent_install(adb, serial, apk, progress) if progress else None
    if text is None:
        code, out, err = run(adb, '-s', serial, 'install', '-r', apk, timeout=900)
        text = (out + err).strip()
        if code == 0 and 'Success' in text:
            return
    elif text == 'Success':
        return
    if 'UPDATE_INCOMPATIBLE' in text or 'SIGNATURES_DO_NOT_MATCH' in text:
        raise OtherSignature(tr("Ranger Rumble est déjà sur le téléphone, signé par quelqu'un d'autre : désinstalle-le, puis recommence."))
    if 'INSUFFICIENT_STORAGE' in text or 'not enough space' in text:
        raise Problem(tr('Pas assez de place sur le téléphone (3 Go).'))
    raise Problem(tr('Installation impossible : {v}', v=text[-300:]))
PHONE_TEMPORARY = '/data/local/tmp/rr_installation.apk'

def sent_install(adb, serial, apk, progress):
    size = os.path.getsize(apk)
    copying = subprocess.Popen([adb, '-s', serial, 'push', apk, PHONE_TEMPORARY], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **QUIET)
    try:
        while copying.poll() is None:
            time.sleep(1)
            _, out, _ = run(adb, '-s', serial, 'shell', 'stat', '-c', '%s', PHONE_TEMPORARY, timeout=30)
            if out.strip().isdigit():
                progress(min(int(out.strip()) / size, 1) * 0.8)
        if copying.returncode != 0:
            return None
        progress(0.8)
        _, out, err = run(adb, '-s', serial, 'shell', 'pm', 'install', '-r', PHONE_TEMPORARY, timeout=900)
        text = (out + err).strip()
        if 'INSUFFICIENT_STORAGE' in text or 'not enough space' in text:
            return None
        return 'Success' if 'Success' in text else text
    finally:
        if copying.poll() is None:
            copying.kill()
        run(adb, '-s', serial, 'shell', 'rm', '-f', PHONE_TEMPORARY, timeout=60)
