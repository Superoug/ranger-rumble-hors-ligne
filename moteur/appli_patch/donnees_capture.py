import os
import sys
import msgpack
from langues import tr
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'serveur_local'))
import preparer
SERVER_DATA = 'donnees_serveur'
SOCIAL = ('invites', 'chats', 'friends', 'groups')
REQUIRED = ('config-map.msgpack', 'vnum.txt', 'login.msgpack', 'er.json') + tuple((f'{key}.msgpack' for key in SOCIAL))

def unpack(raw: bytes):
    return msgpack.unpackb(raw, raw=False, strict_map_key=False, timestamp=0)

def read(folder: str, name: str) -> bytes:
    with open(os.path.join(folder, name), 'rb') as handle:
        return handle.read()

def server_folder(path: str) -> str:
    return path if os.path.basename(os.path.normpath(path)) == SERVER_DATA else os.path.join(path, SERVER_DATA)

def item_names(config: dict) -> list[str]:
    names = []
    for item in config['items']:
        url = item.get('url')
        if url and (not item.get('value')):
            url = url.decode() if isinstance(url, bytes) else url
            names.append(url.split('?')[0].rstrip('/').rsplit('/', 1)[1])
    return names

def missing_files(path: str) -> list[str]:
    folder = server_folder(path)
    lacking = [name for name in REQUIRED if not os.path.isfile(os.path.join(folder, name))]
    if 'config-map.msgpack' not in lacking:
        config = unpack(read(folder, 'config-map.msgpack'))
        lacking += [f'items/{name}' for name in item_names(config) if not os.path.isfile(os.path.join(folder, 'items', name))]
    return lacking

def convert(path: str, out_dir: str) -> str:
    folder = server_folder(path)
    lacking = missing_files(folder)
    if lacking:
        raise SystemExit(tr('Données du serveur incomplètes : ') + ', '.join(lacking))
    items_dir = os.path.join(folder, 'items')
    items = {name: read(items_dir, name) for name in os.listdir(items_dir)}
    login = unpack(read(folder, 'login.msgpack'))
    answers = {key: unpack(read(folder, f'{key}.msgpack')) for key in SOCIAL}
    vnum = read(folder, 'vnum.txt').decode().strip()
    preparer.build_data(read(folder, 'config-map.msgpack'), vnum, items, login, answers, read(folder, 'er.json'), login['publicId'], out_dir)
    return out_dir
if __name__ == '__main__':
    convert(sys.argv[1], sys.argv[2])
