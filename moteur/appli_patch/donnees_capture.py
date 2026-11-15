import os
import sys
import msgpack
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'serveur_local'))
import preparer
SOCIAL = ('invites', 'chats', 'friends', 'groups')

def unpack(raw):
    return msgpack.unpackb(raw, raw=False, strict_map_key=False, timestamp=0)

def server_folder(path):
    return path if os.path.basename(os.path.normpath(path)) == 'donnees_serveur' else os.path.join(path, 'donnees_serveur')

def missing_files(path):
    folder = server_folder(path)
    lacking = [name for name in ['config-map.msgpack', 'vnum.txt', 'login.msgpack', 'er.json'] + [f'{key}.msgpack' for key in SOCIAL] if not os.path.isfile(os.path.join(folder, name))]
    if 'config-map.msgpack' not in lacking:
        config = unpack(open(os.path.join(folder, 'config-map.msgpack'), 'rb').read())
        for item in config['items']:
            url = item.get('url')
            if url and (not item.get('value')):
                url = url.decode() if isinstance(url, bytes) else url
                name = url.split('?')[0].rstrip('/').rsplit('/', 1)[1]
                if not os.path.isfile(os.path.join(folder, 'items', name)):
                    lacking.append(f'items/{name}')
    return lacking

def convert(path, out_dir):
    folder = server_folder(path)
    lacking = missing_files(folder)
    if lacking:
        raise SystemExit('Données du serveur incomplètes : ' + ', '.join(lacking))

    def read(name):
        return open(os.path.join(folder, name), 'rb').read()
    items_dir = os.path.join(folder, 'items')
    items = {name: open(os.path.join(items_dir, name), 'rb').read() for name in os.listdir(items_dir)}
    login = unpack(read('login.msgpack'))
    answers = {key: unpack(read(f'{key}.msgpack')) for key in SOCIAL}
    vnum = read('vnum.txt').decode().strip()
    preparer.build_data(read('config-map.msgpack'), vnum, items, login, answers, read('er.json'), login['publicId'], out_dir)
    return out_dir
if __name__ == '__main__':
    convert(sys.argv[1], sys.argv[2])
