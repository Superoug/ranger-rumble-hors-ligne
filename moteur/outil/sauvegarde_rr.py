import asyncio
import base64
import datetime
import gzip
import hashlib
import json
import os
import plistlib
import re
import socket
import subprocess
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import msgpack
from mitmproxy import certs, http, options
from mitmproxy.tools.dump import DumpMaster
HERE = Path(__file__).resolve().parent
OUT = Path(os.environ.get('RR_SORTIE') or HERE / 'Sauvegardes')
CONF = Path.home() / '.sauvegarde-rr' / 'certificat'
CA_FILE = CONF / 'mitmproxy-ca-cert.pem'
PROFILE = 'RatchetRR'
GAME_HOSTS = ['(^|\\.)obb\\.(cloud|com)(:\\d+)?$', '(^|\\.)ohbibi\\.com(:\\d+)?$', '(^|-)ohbibi[a-z0-9-]*\\.cloudfunctions\\.net(:\\d+)?$']
GAME = re.compile('|'.join(GAME_HOSTS))
SAVE = re.compile('/afuncs/users/([^/?]+)/save$')
EVENTS = re.compile('/afuncs/users/([^/?]+)/events$')
CONFIG_MAP = re.compile('/game-config/config-map$')
CONFIG_ITEM = re.compile('/game-config/items/value/([^/?]+)$')
SOCIAL = re.compile('/profiles/[^/]+/(invites|chats|friends|groups)$')
REVENUE = re.compile('/tools/revenue/er\\.json$')
SERVER_DATA = 'donnees_serveur'
ITEM_WAIT = 25
SECRET_KEYS = ('userSecret', 'socialCredentials', 'obbToken', 'SessionToken', 'updatedSecret')
WIFI = os.environ.get('RR_WIFI', '')
PROFILE_FILE = 'RatchetRR.mobileconfig'
PAC_FILE = 'rr.pac'

def say(message=''):
    print(f"{time.strftime('%H:%M:%S')}  {message}" if message else '', flush=True)

def local_ip():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(('192.0.2.1', 9))
        return sock.getsockname()[0]
    except OSError:
        return '127.0.0.1'
    finally:
        sock.close()

def free_port(start, taken=()):
    for port in range(start, start + 40):
        if port in taken:
            continue
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if os.name != 'nt':
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(('0.0.0.0', port))
            return port
        except OSError:
            continue
        finally:
            sock.close()
    raise SystemExit(f'Aucun port libre entre {start} et {start + 39}.')

def run_quiet(command):
    try:
        return subprocess.run(command, capture_output=True, text=True, errors='replace', timeout=10).stdout
    except (OSError, subprocess.SubprocessError):
        return ''

def wifi_networks():
    current, known = ('', [])
    if sys.platform == 'darwin':
        ports = run_quiet(['networksetup', '-listallhardwareports']).splitlines()
        device = next((ports[i + 1].split(':', 1)[1].strip() for i, line in enumerate(ports[:-1]) if line.strip() in ('Hardware Port: Wi-Fi', 'Hardware Port: AirPort')), 'en0')
        found = re.search('Network: (.+)', run_quiet(['networksetup', '-getairportnetwork', device]))
        if found:
            current = found.group(1).strip()
        known = [line.strip() for line in run_quiet(['networksetup', '-listpreferredwirelessnetworks', device]).splitlines()[1:] if line.strip()]
    elif os.name == 'nt':
        found = re.search('^\\s*SSID\\s*:\\s*(.+)$', run_quiet(['netsh', 'wlan', 'show', 'interfaces']), re.M)
        if found:
            current = found.group(1).strip()
        known = [m.group(1).strip() for m in re.finditer(':\\s*(.+)$', run_quiet(['netsh', 'wlan', 'show', 'profiles']), re.M) if m.group(1).strip()]
    else:
        for line in run_quiet(['nmcli', '-t', '-f', 'active,ssid', 'dev', 'wifi']).splitlines():
            if line.startswith('yes:'):
                current = line[4:].replace('\\:', ':')
        for line in run_quiet(['nmcli', '-t', '-f', 'name,type', 'connection', 'show']).splitlines():
            name, _, kind = line.rpartition(':')
            if 'wireless' in kind and name:
                known.append(name.replace('\\:', ':'))
    if 'redacted' in current.lower():
        current = ''
    known = [name for name in dict.fromkeys(known) if 'redacted' not in name.lower()]
    if current and current not in known:
        known.insert(0, current)
    return (current, known)

def pac(address, proxy_port):
    return f'function FindProxyForURL(url, host) {{\n  host = host.toLowerCase();\n  if (host == "obb.cloud" || dnsDomainIs(host, ".obb.cloud") ||\n      host == "obb.com" || dnsDomainIs(host, ".obb.com") ||\n      host == "ohbibi.com" || dnsDomainIs(host, ".ohbibi.com") ||\n      shExpMatch(host, "ohbibi*.cloudfunctions.net") || shExpMatch(host, "*-ohbibi*.cloudfunctions.net"))\n    return "PROXY {address}:{proxy_port}; DIRECT";\n  return "DIRECT";\n}}\n'.encode()

def ca_der():
    pem = CA_FILE.read_text()
    body = pem.split('-----BEGIN CERTIFICATE-----')[1].split('-----END CERTIFICATE-----')[0]
    return base64.b64decode(''.join(body.split()))

def mobileconfig(address, page_port, wifi):
    der = ca_der()
    base = uuid.uuid5(uuid.NAMESPACE_URL, 'ratchetrr:' + hashlib.sha256(der).hexdigest())
    content = [{'PayloadType': 'com.apple.security.root', 'PayloadVersion': 1, 'PayloadIdentifier': 'fr.ratchetrr.copie.certificat', 'PayloadUUID': str(uuid.uuid5(base, 'certificat')).upper(), 'PayloadDisplayName': PROFILE, 'PayloadCertificateFileName': PROFILE + '.cer', 'PayloadContent': der}]
    if wifi:
        content.append({'PayloadType': 'com.apple.wifi.managed', 'PayloadVersion': 1, 'PayloadIdentifier': 'fr.ratchetrr.copie.wifi', 'PayloadUUID': str(uuid.uuid5(base, 'wifi')).upper(), 'PayloadDisplayName': f'Wi-Fi {wifi}', 'SSID_STR': wifi, 'HIDDEN_NETWORK': False, 'AutoJoin': True, 'EncryptionType': 'Any', 'IsHotspot': False, 'ProxyType': 'Auto', 'ProxyPACURL': f'http://{address}:{page_port}/{PAC_FILE}', 'ProxyPACFallbackAllowed': True})
    return plistlib.dumps({'PayloadType': 'Configuration', 'PayloadVersion': 1, 'PayloadIdentifier': 'fr.ratchetrr.copie', 'PayloadUUID': str(base).upper(), 'PayloadDisplayName': PROFILE, 'PayloadOrganization': PROFILE, 'PayloadDescription': "Copie de sauvegarde Ranger Rumble : le certificat de l'ordinateur et le réglage automatique du proxy du Wi-Fi, seulement pour les serveurs du jeu. À supprimer quand la copie est faite.", 'PayloadRemovalDisallowed': False, 'PayloadContent': content})

def inflate(raw):
    if raw and raw[:2] == b'\x1f\x8b':
        return gzip.decompress(raw)
    return raw or b''

def unpack(raw):
    try:
        return msgpack.unpackb(inflate(raw), raw=False, strict_map_key=False, timestamp=0)
    except Exception:
        return None

def plain(value):
    if isinstance(value, dict):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    if isinstance(value, bytes):
        try:
            return plain(msgpack.unpackb(value, raw=False, strict_map_key=False, timestamp=0))
        except Exception:
            return {'hex': value.hex()}
    if isinstance(value, msgpack.Timestamp):
        return str(value.to_datetime())
    if isinstance(value, msgpack.ExtType):
        return {'ext': value.code, 'hex': value.data.hex()}
    return value

def strings(value, found):
    if isinstance(value, str) and len(value) > 8:
        found.add(value.encode())
    elif isinstance(value, dict):
        for item in value.values():
            strings(item, found)
    elif isinstance(value, (list, tuple)):
        for item in value:
            strings(item, found)

class Recorder:

    def __init__(self):
        self.secrets = set()
        self.devices = set()
        self.folders = {}
        self.copied = {}
        self.pending_events = {}
        self.refused_at = 0.0
        self.accepted = False
        self.server = {'items': {}, 'answers': {}, 'logins': {}}
        self.fetching = False

    def client_connected(self, client):
        address = client.peername[0] if client.peername else '?'
        if address not in self.devices:
            self.devices.add(address)
            say(f"Un appareil passe par l'ordinateur ({address}).")

    def request(self, flow: http.HTTPFlow):
        if not GAME.search(flow.request.pretty_host):
            return
        flow.metadata['rr_jeu'] = True
        auth = flow.request.headers.get('authorization', '')
        if len(auth) > 8:
            self.secrets.add(auth.encode())
            self.secrets.add(auth.split()[-1].encode())

    def response(self, flow: http.HTTPFlow):
        req, res = (flow.request, flow.response)
        if res is None or not flow.metadata.get('rr_jeu'):
            return
        path = req.path.split('?')[0]
        if path.endswith('/auth/login'):
            self.on_login(req, res)
            return
        if not 200 <= res.status_code < 300:
            return
        if req.method == 'POST' and CONFIG_MAP.search(path):
            self.on_config(res)
            return
        if req.method != 'GET':
            return
        match = CONFIG_ITEM.search(path)
        if match:
            self.server['items'][match.group(1)] = res.content
            self.flush_server()
            return
        match = SOCIAL.search(path)
        if match:
            self.server['answers'][match.group(1)] = res.content
            self.flush_server()
            return
        if REVENUE.search(path):
            self.server['er'] = res.content
            self.flush_server()
            return
        match = SAVE.search(path)
        if match:
            self.on_save(match.group(1), res.content)
            return
        match = EVENTS.search(path)
        if match:
            self.on_events(match.group(1), res.content)

    def on_login(self, req, res):
        for side in (req.content, res.content):
            body = unpack(side)
            if isinstance(body, dict):
                for key in SECRET_KEYS:
                    strings(body.get(key), self.secrets)
        body = unpack(res.content)
        if isinstance(body, dict) and body.get('publicId'):
            say(f"Le jeu se connecte au compte {body['publicId']}.")
            if not body.get('networkChoiceRequired'):
                for key in SECRET_KEYS:
                    if key in body:
                        body[key] = ''
                self.server['logins'][body['publicId']] = msgpack.packb(body, use_bin_type=True)
                self.flush_server()

    def on_config(self, res):
        config = unpack(res.content)
        if not isinstance(config, dict) or not config.get('items'):
            return
        self.server['config'] = res.content
        self.server['vnum'] = res.headers.get('obb-client-vnum', '')
        urls = {}
        for item in (config or {}).get('items', []):
            url = item.get('url')
            if url and (not item.get('value')):
                url = url.decode() if isinstance(url, bytes) else url
                urls[url.split('?')[0].rstrip('/').rsplit('/', 1)[1]] = url
        self.server['urls'] = urls
        self.flush_server()

    def server_folder(self):
        folder = next(iter(self.folders.values()), None)
        if folder is None:
            return None
        target = folder / SERVER_DATA
        target.mkdir(exist_ok=True)
        (target / 'items').mkdir(exist_ok=True)
        return target

    def flush_server(self):
        target = self.server_folder()
        if target is None:
            return
        data = self.server
        written = data.setdefault('written', {})

        def put(name, content):
            if not content:
                return
            digest = hashlib.sha256(content).digest()
            if written.get(name) != digest and self.write(target, name, content):
                written[name] = digest
        if 'config' in data:
            put('config-map.msgpack', data['config'])
            put('vnum.txt', data['vnum'].encode())
        for name, content in data['items'].items():
            put(f'items/{name}', content)
        for name, content in data['answers'].items():
            put(f'{name}.msgpack', inflate(content))
        put('er.json', data.get('er'))
        user = next(iter(self.folders))
        put('login.msgpack', data['logins'].get(user))
        if 'config' in data and (not self.fetching):
            self.fetching = True
            threading.Timer(ITEM_WAIT, self.fetch_missing_items).start()

    def fetch_missing_items(self):
        import urllib.request
        missing = {name: url for name, url in self.server.get('urls', {}).items() if name not in self.server['items']}
        for name, url in missing.items():
            try:
                import ssl
                import certifi
                context = ssl.create_default_context(cafile=certifi.where())
                with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'RangerRumble'}), timeout=30, context=context) as answer:
                    self.server['items'][name] = answer.read()
            except Exception as error:
                say(f'  Fichier de configuration {name} non téléchargé : {error}')
        self.flush_server()
        target = self.server_folder()
        lacking = [n for n in ('config-map.msgpack', 'login.msgpack', 'er.json', 'invites.msgpack', 'chats.msgpack', 'friends.msgpack', 'groups.msgpack') if not (target / n).exists()]
        lacking += [f'items/{n}' for n in self.server.get('urls', {}) if not (target / 'items' / n).exists()]
        if lacking:
            say('Données du serveur incomplètes (il manque : ' + ', '.join(lacking) + ').')
            say("  Ferme complètement le jeu, rouvre-le et attends l'écran d'accueil.")
            self.fetching = False
        else:
            self.finished()

    def finished(self):
        folder = next(iter(self.folders.values()))
        say()
        say('=' * 62)
        say("  C'EST FAIT : SAUVEGARDE ET DONNÉES COPIÉES !")
        say(f'  Dossier : {folder}')
        say('=' * 62)
        say("Maintenant, sur l'iPhone, supprime le profil RatchetRR :")
        say("  Réglages > Général > VPN et gestion de l'appareil > RatchetRR > Supprimer le profil.")
        say("  L'iPhone oublie alors ce Wi-Fi : reconnecte-toi avec ton mot de passe.")
        say('  (Si tu avais réglé le proxy à la main, remets-le sur Désactivé.)')
        say('Ensuite tu peux arrêter la copie.')
        say()

    def write(self, folder, name, data):
        if any((secret in data for secret in self.secrets)):
            say(f'  {name} ignoré : il contenait une donnée de connexion.')
            return False
        (folder / name).write_bytes(data)
        return True

    def on_save(self, user, raw):
        content = inflate(raw)
        body = unpack(content)
        parts = body.get('save') if isinstance(body, dict) else None
        if not parts:
            say('La sauvegarde reçue est vide ou illisible. Ferme le jeu et relance-le.')
            return
        digest = hashlib.sha256(content).hexdigest()
        if self.copied.get(user) == digest:
            say('Le jeu a renvoyé la même sauvegarde : elle est déjà copiée.')
            return
        stamp = datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')
        base = OUT / f"{re.sub('[^A-Za-z0-9_-]', '_', user)}_{stamp}"
        folder, number = (base, 1)
        while folder.exists():
            number += 1
            folder = base.with_name(f'{base.name}_{number}')
        folder.mkdir(parents=True)
        if not self.write(folder, 'save.msgpack', content):
            return
        readable = json.dumps(plain(body), indent=1, ensure_ascii=False, default=str).encode()
        self.write(folder, 'sauvegarde_lisible.json', readable)
        info = '\n'.join(['Copie de sauvegarde - Ratchet & Clank: Ranger Rumble', f'Compte : {user}', f"Copiée le : {datetime.datetime.now().strftime('%d/%m/%Y à %H:%M')}", f"Plateforme : {body.get('platform')}  |  version du jeu : {body.get('buildNumber')}", f'Parties de sauvegarde : {len(parts)}', f'Empreinte de save.msgpack (sha256) : {digest}', '', 'save.msgpack est la sauvegarde exacte envoyée par les serveurs officiels.', 'sauvegarde_lisible.json est la même chose en texte lisible.', 'Ce dossier ne contient ni mot de passe ni jeton de connexion.', ''])
        self.write(folder, 'INFO.txt', info.encode())
        self.folders[user] = folder
        self.copied[user] = digest
        events = self.pending_events.pop(user, None)
        if events:
            self.write(folder, 'events.msgpack', events)
        say(f'Sauvegarde copiée : compte {user}, {len(parts)} parties.')
        say("  Reste sur l'écran d'accueil du jeu : il reste les données du serveur (environ 30 secondes).")
        self.flush_server()

    def on_events(self, user, raw):
        content = inflate(raw)
        folder = self.folders.get(user)
        if folder:
            self.write(folder, 'events.msgpack', content)
        else:
            self.pending_events[user] = content

    def tls_established_client(self, data):
        host = data.context.client.sni or ''
        if GAME.search(host) and (not self.accepted):
            self.accepted = True
            say('Le jeu accepte le certificat : la copie peut se faire.')

    def tls_failed_client(self, data):
        host = data.context.client.sni or ''
        if not GAME.search(host) or time.time() - self.refused_at < 30:
            return
        self.refused_at = time.time()
        say(f"Le jeu refuse le certificat de l'ordinateur ({host}).")
        say("  Sur l'iPhone, le profil doit être installé ET accepté :")
        say("  1. Réglages > Général > VPN et gestion de l'appareil > RatchetRR > Installer.")
        say('  2. Réglages > Général > Informations, tout en bas « Réglages des certificats » :')
        say('     active RatchetRR > Continuer.')
        say('  Puis ferme complètement le jeu et rouvre-le.')
        say(f'  (détail : {data.conn.error})')

def page(address, proxy_port, wifi):
    if wifi:
        network = f"<p>Ce profil règle le Wi-Fi <b>{html_escape(wifi)}</b>. Si ton iPhone est sur un autre Wi-Fi, change-le dans la fenêtre de l'ordinateur, puis recharge cette page.</p>"
    else:
        network = "<p><b>Choisis d'abord le Wi-Fi de l'iPhone dans la fenêtre de l'ordinateur</b>, puis recharge cette page (sans cela, il faut régler le proxy à la main, voir tout en bas).</p>"
    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n<title>Copie de sauvegarde Ranger Rumble</title>\n<style>body{{font-family:-apple-system,system-ui,sans-serif;max-width:34em;margin:1em auto;padding:0 1em;line-height:1.5}}\na.b{{display:block;text-align:center;background:#1b6ef3;color:#fff;padding:.9em;border-radius:.6em;text-decoration:none;font-weight:600;margin:1em 0}}\ncode{{background:#eee;padding:.1em .3em;border-radius:.3em}} small{{color:#555}}</style></head><body>\n<h1>Copie de sauvegarde</h1>\n{network}\n<p><b>1.</b> Touche le bouton, puis <b>Autoriser</b>.</p>\n<a class="b" href="/{PROFILE_FILE}">Télécharger le profil RatchetRR</a>\n<p><b>2.</b> Ouvre <b>Réglages</b> : en haut, touche <b>Profil téléchargé</b> (ou Général &gt; <b>VPN et gestion\nde l'appareil</b> &gt; RatchetRR). Touche <b>Installer</b>, le code de l'iPhone, et encore <b>Installer</b>.\nSi l'iPhone demande le mot de passe du Wi-Fi, tape-le.</p>\n<p><b>3.</b> Réglages &gt; Général &gt; <b>Informations</b> (pas VPN). Tout en bas de cette page :\n<b>Réglages des certificats</b> (la ligne n'apparaît qu'après l'étape 2).\nActive <b>RatchetRR</b>, puis <b>Continuer</b>.</p>\n<p><b>4.</b> Ouvre Ranger Rumble et attends l'écran d'accueil. C'est tout : la fenêtre de l'ordinateur\ndira quand c'est fini.</p>\n<p><b>Après :</b> supprime le profil (Réglages &gt; Général &gt; VPN et gestion de l'appareil &gt; RatchetRR).\nL'iPhone oublie alors ce Wi-Fi : reconnecte-toi avec ton mot de passe.</p>\n<p><small>Si la copie ne démarre pas, règle le proxy à la main : Réglages &gt; Wi-Fi &gt; (i) &gt; Configurer le\nproxy &gt; Manuel, serveur <code>{address}</code>, port <code>{proxy_port}</code> (et remets-le sur Désactivé\naprès).</small></p>\n</body></html>""".encode()

def html_escape(text):
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')

def serve_page(address, proxy_port, page_port):
    certificate = CA_FILE.read_bytes()
    told = set()

    def once(what, message):
        if what not in told:
            told.add(what)
            say(message)

    class Handler(BaseHTTPRequestHandler):

        def do_GET(self):
            path = self.path.split('?')[0]
            if path == f'/{PROFILE_FILE}':
                say(f"L'iPhone télécharge le profil RatchetRR (Wi-Fi : {WIFI or 'aucun'}).")
                body, kind = (mobileconfig(address, page_port, WIFI), 'application/x-apple-aspen-config')
            elif path == f'/{PAC_FILE}':
                once('pac', "L'iPhone utilise le réglage automatique du profil : ouvre le jeu.")
                body, kind = (pac(address, proxy_port), 'application/x-ns-proxy-autoconfig')
            elif path.startswith('/certificat'):
                say('Le téléphone télécharge le certificat.')
                body, kind = (certificate, 'application/x-x509-ca-cert')
            else:
                once('page', "Le téléphone a ouvert la page d'aide.")
                body, kind = (page(address, proxy_port, WIFI), 'text/html; charset=utf-8')
            self.send_response(200)
            self.send_header('Content-Type', kind)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass
    server = ThreadingHTTPServer(('0.0.0.0', page_port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server

async def run(address, proxy_port, page_port, ready=None):
    opts = options.Options(listen_host='0.0.0.0', listen_port=proxy_port, confdir=str(CONF))
    master = DumpMaster(opts, with_termlog=True, with_dumper=False)
    settings = {'allow_hosts': GAME_HOSTS, 'termlog_verbosity': 'error'}
    master.options.update(**settings)
    master.addons.add(Recorder())
    page_server = serve_page(address, proxy_port, page_port)
    if ready:
        ready(master, page_server)
    try:
        await master.run()
    finally:
        page_server.shutdown()
        page_server.server_close()

def profile_name():
    try:
        return certs.Cert.from_pem(CA_FILE.read_bytes()).cn
    except (OSError, ValueError):
        return None

def prepare():
    OUT.mkdir(parents=True, exist_ok=True)
    CONF.mkdir(parents=True, exist_ok=True)
    if profile_name() != PROFILE:
        for old in CONF.glob('mitmproxy-ca*'):
            old.unlink()
        certs.CertStore.create_store(CONF, 'mitmproxy', 2048, organization=PROFILE, cn=PROFILE)
    address = local_ip()
    proxy_port = free_port(8080)
    page_port = free_port(8090, taken=(proxy_port,))
    print()
    print('=== Copie de sauvegarde - Ratchet & Clank: Ranger Rumble ===')
    print()
    print("L'iPhone et cet ordinateur doivent être sur le même Wi-Fi.")
    print()
    print("ÉTAPE 1 - sur l'iPhone, vise le QR code de la fenêtre avec l'appareil photo")
    print(f"      (ou ouvre Safari à l'adresse http://{address}:{page_port} ).")
    print('      Touche « Télécharger le profil RatchetRR », puis « Autoriser ».')
    print()
    print('ÉTAPE 2 - installe le profil : Réglages > « Profil téléchargé » (en haut)')
    print("      > Installer > code de l'iPhone > Installer.")
    print("      Si l'iPhone demande le mot de passe du Wi-Fi, tape-le.")
    print()
    print('ÉTAPE 3 - accepte le profil (sinon le jeu le refuse) :')
    print('      Réglages > Général > Informations > tout en bas « Réglages des certificats »')
    print('      > active « RatchetRR » > Continuer.')
    print()
    print("ÉTAPE 4 - ouvre Ranger Rumble et attends l'écran d'accueil. C'est tout.")
    if WIFI:
        print(f'      (Le profil règle tout seul le proxy du Wi-Fi « {WIFI} ».)')
    else:
        print('      Aucun Wi-Fi choisi : le profil ne règle pas le proxy. Règle-le à la main :')
        print('      Réglages > Wi-Fi > (i) > Configurer le proxy > Manuel')
        print(f'      Serveur : {address}      Port : {proxy_port}')
    print()
    print('Laisse cette fenêtre ouverte : elle dira quand la sauvegarde est copiée.')
    print(f'Les copies vont dans : {OUT}')
    print()
    return (address, proxy_port, page_port)

def main():
    global WIFI
    sys.stdout.reconfigure(line_buffering=True)
    if not WIFI:
        current, _ = wifi_networks()
        WIFI = current or input("Nom du Wi-Fi de l'iPhone (Entrée pour régler le proxy à la main) : ").strip()
    address, proxy_port, page_port = prepare()
    try:
        asyncio.run(run(address, proxy_port, page_port))
    except KeyboardInterrupt:
        pass
if __name__ == '__main__':
    sys.exit(main())
