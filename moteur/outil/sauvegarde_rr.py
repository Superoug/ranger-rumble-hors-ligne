import asyncio
import base64
import datetime
import gzip
import hashlib
import http.client
import ipaddress
import json
import os
import plistlib
import re
import socket
import ssl
import sys
import threading
import time
import urllib.request
import uuid
import zlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import msgpack
PURE = os.name == 'nt' or os.environ.get('RR_MOTEUR_PUR') == '1'
if PURE:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import moteur_pur
else:
    from cryptography import x509
    from cryptography.hazmat.primitives import serialization
    from mitmproxy import certs, dns, options
    from mitmproxy.proxy.mode_specs import ReverseMode
    from mitmproxy.tools.dump import DumpMaster
try:
    from langues import tr
    from langues import CURRENT as LANGUAGE
except ImportError:
    LANGUAGE = 'fr'

    def tr(text, /, **values):
        return text.format(**values) if values else text
HERE = Path(__file__).resolve().parent
OUT = Path(os.environ.get('RR_SORTIE') or HERE / 'Sauvegardes')
CONF = Path.home() / '.sauvegarde-rr' / 'certificat'
CA_FILE = CONF / 'mitmproxy-ca-cert.pem'
PROFILE = 'RatchetRR'
PROFILE_FILE = f'{PROFILE}.mobileconfig'
GAME_HOSTS = ['(^|\\.)obb\\.(cloud|com)(:\\d+)?$', '(^|\\.)ohbibi\\.com(:\\d+)?$', '(^|-)ohbibi[a-z0-9-]*\\.cloudfunctions\\.net(:\\d+)?$']
GAME = re.compile('|'.join(GAME_HOSTS))
SAVE = re.compile('/afuncs/users/([^/?]+)/save$')
EVENTS = re.compile('/afuncs/users/([^/?]+)/events$')
CONFIG_MAP = re.compile('/game-config/config-map$')
CONFIG_ITEM = re.compile('/game-config/items/value/([^/?]+)$')
SOCIAL = re.compile('/profiles/[^/]+/(invites|chats|friends|groups)$')
REVENUE = re.compile('/tools/revenue/er\\.json$')
SERVER_DATA = 'donnees_serveur'
SERVER_FILES = ('config-map.msgpack', 'login.msgpack', 'er.json', 'invites.msgpack', 'chats.msgpack', 'friends.msgpack', 'groups.msgpack')
ITEM_WAIT = 25
SECRET_KEYS = ('userSecret', 'socialCredentials', 'obbToken', 'SessionToken', 'updatedSecret')
DNS_DOMAINS = ['obb.cloud', 'obb.com', 'ohbibi.com', 'cloudfunctions.net']
DNS_NAME = 'dns.ratchetrr'
DOT_PORT = 853
HTTPS_PORT = 443
AUTO = True
PORT_TRIES = 40
UNREADABLE = (ValueError, TypeError, EOFError, OSError, zlib.error, msgpack.UnpackException)
DOWNLOAD_ERRORS = (OSError, ValueError, EOFError, zlib.error, http.client.HTTPException, ImportError)
ON_STATE = None
STOP = None
STOP_DELAY = 3

def say(message=''):
    print(f"{time.strftime('%H:%M:%S')}  {message}" if message else '', flush=True)

def state(name):
    if ON_STATE is not None:
        try:
            ON_STATE(name)
        except Exception:
            pass

def is_game(host):
    return bool(GAME.search(host))

class Throttle:

    def __init__(self, seconds=30):
        self.seconds = seconds
        self.last = 0.0

    def ready(self):
        now = time.time()
        if now - self.last < self.seconds:
            return False
        self.last = now
        return True

def local_ip():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(('192.0.2.1', 9))
        return sock.getsockname()[0]
    except OSError:
        return '127.0.0.1'
    finally:
        sock.close()

def can_listen(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if os.name != 'nt':
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind(('0.0.0.0', port))
        return True
    except OSError:
        return False
    finally:
        sock.close()

def free_port(start, taken=()):
    for port in range(start, start + PORT_TRIES):
        if port not in taken and can_listen(port):
            return port
    raise SystemExit(tr('Aucun port libre entre {start} et {v}.', start=start, v=start + PORT_TRIES - 1))

def public_context():
    import certifi
    return ssl.create_default_context(cafile=certifi.where())

def ca_der():
    pem = CA_FILE.read_text()
    body = pem.split('-----BEGIN CERTIFICATE-----')[1].split('-----END CERTIFICATE-----')[0]
    return base64.b64decode(''.join(body.split()))

def mobileconfig(address, auto):
    der = ca_der()
    base = uuid.uuid5(uuid.NAMESPACE_URL, 'ratchetrr:' + hashlib.sha256(der).hexdigest())
    content = [{'PayloadType': 'com.apple.security.root', 'PayloadVersion': 1, 'PayloadIdentifier': 'fr.ratchetrr.copie.certificat', 'PayloadUUID': str(uuid.uuid5(base, 'certificat')).upper(), 'PayloadDisplayName': PROFILE, 'PayloadCertificateFileName': PROFILE + '.cer', 'PayloadContent': der}]
    if auto:
        content.append({'PayloadType': 'com.apple.dnsSettings.managed', 'PayloadVersion': 1, 'PayloadIdentifier': 'fr.ratchetrr.copie.dns', 'PayloadUUID': str(uuid.uuid5(base, 'dns')).upper(), 'PayloadDisplayName': PROFILE, 'DNSSettings': {'DNSProtocol': 'TLS', 'ServerName': DNS_NAME, 'ServerAddresses': [address], 'SupplementalMatchDomains': DNS_DOMAINS}, 'ProhibitDisablement': False})
    return plistlib.dumps({'PayloadType': 'Configuration', 'PayloadVersion': 1, 'PayloadIdentifier': 'fr.ratchetrr.copie', 'PayloadUUID': str(base).upper(), 'PayloadDisplayName': PROFILE, 'PayloadOrganization': PROFILE, 'PayloadDescription': tr("Copie de sauvegarde Ranger Rumble : le certificat de l'ordinateur et un DNS pour les serveurs du jeu seulement. À supprimer quand la copie est faite."), 'PayloadRemovalDisallowed': False, 'PayloadContent': content})

def inflate(raw):
    if raw and raw[:2] == b'\x1f\x8b':
        return gzip.decompress(raw)
    return raw or b''

def msgpack_value(data):
    return msgpack.unpackb(data, raw=False, strict_map_key=False, timestamp=0)

def unpack(raw):
    try:
        return msgpack_value(inflate(raw))
    except UNREADABLE:
        return None

def plain(value):
    if isinstance(value, dict):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    if isinstance(value, bytes):
        try:
            return plain(msgpack_value(value))
        except UNREADABLE:
            return {'hex': value.hex()}
    if isinstance(value, msgpack.Timestamp):
        return str(value.to_datetime())
    if isinstance(value, msgpack.ExtType):
        return {'ext': value.code, 'hex': value.data.hex()}
    return value

def long_strings(value, found):
    if isinstance(value, str) and len(value) > 8:
        found.add(value.encode())
    elif isinstance(value, dict):
        for item in value.values():
            long_strings(item, found)
    elif isinstance(value, (list, tuple)):
        for item in value:
            long_strings(item, found)

def dns_certificate(address):
    store = certs.CertStore.from_store(CONF, 'mitmproxy', 2048)
    entry = store.get_cert(DNS_NAME, [x509.DNSName(DNS_NAME), x509.IPAddress(ipaddress.ip_address(address))], organization=PROFILE)
    key = entry.privatekey.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL, serialization.NoEncryption())
    pem = CONF / 'dns-copie.pem'
    pem.write_bytes(entry.cert.to_pem() + key)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(str(pem))
    return context

async def dns_answer(query, address):
    message = dns.DNSMessage.unpack(query)
    answers = []
    for question in message.questions:
        name = question.name.rstrip('.').lower()
        if question.type not in (dns.types.A, dns.types.AAAA):
            continue
        if is_game(name):
            if question.type == dns.types.A:
                answers.append(dns.ResourceRecord.A(question.name, ipaddress.IPv4Address(address), ttl=5))
            continue
        family = socket.AF_INET if question.type == dns.types.A else socket.AF_INET6
        try:
            found = await asyncio.get_running_loop().getaddrinfo(name, None, family=family, type=socket.SOCK_STREAM)
        except OSError:
            found = []
        for ip in dict.fromkeys((item[4][0] for item in found)):
            if question.type == dns.types.A:
                answers.append(dns.ResourceRecord.A(question.name, ipaddress.IPv4Address(ip), ttl=60))
            else:
                answers.append(dns.ResourceRecord.AAAA(question.name, ipaddress.IPv6Address(ip.split('%')[0]), ttl=60))
    return message.succeed(answers).packed

async def pure_dns_answer(query, address):
    name, kind, _ = moteur_pur.dns_question(query)
    if kind not in (moteur_pur.DNS_A, moteur_pur.DNS_AAAA):
        return moteur_pur.dns_reply(query, [])
    if is_game(name):
        return moteur_pur.dns_reply(query, [(address, 5)] if kind == moteur_pur.DNS_A else [])
    found = await asyncio.get_running_loop().run_in_executor(None, moteur_pur.resolve, name, kind)
    return moteur_pur.dns_reply(query, [(ip, 60) for ip in found])

class DnsOverTls:

    def __init__(self, address, context, answer):
        self.address, self.context, self.answer = (address, context, answer)
        self.used = False
        self.refusals = Throttle()

    async def client(self, reader, writer):
        try:
            if await self._handshake(writer):
                await self._answer_queries(reader, writer)
        finally:
            writer.close()

    async def _handshake(self, writer):
        try:
            await asyncio.wait_for(writer.start_tls(self.context), 15)
        except ssl.SSLError:
            if self.refusals.ready():
                state('certificat')
                say(tr("L'iPhone refuse le certificat de l'ordinateur."))
                say(tr('  Réglages > Général > Informations > Réglages des certificats > activer RatchetRR.'))
            return False
        except OSError:
            return False
        if not self.used:
            self.used = True
            state('iphone')
            say(tr("L'iPhone utilise le profil RatchetRR : ouvrir le jeu."))
        return True

    async def _answer_queries(self, reader, writer):
        try:
            while True:
                head = await asyncio.wait_for(reader.readexactly(2), 120)
                query = await reader.readexactly(int.from_bytes(head, 'big'))
                reply = await self.answer(query, self.address)
                writer.write(len(reply).to_bytes(2, 'big') + reply)
                await writer.drain()
        except Exception:
            pass

async def serve_dns(address, context=None, answer=None):
    server = DnsOverTls(address, context or dns_certificate(address), answer or dns_answer)
    return await asyncio.start_server(server.client, '0.0.0.0', DOT_PORT)

class Recorder:

    def __init__(self):
        self.secrets = set()
        self.devices = set()
        self.folders = {}
        self.copied = {}
        self.pending_events = {}
        self.refusals = Throttle()
        self.accepted = False
        self.server = {'items': {}, 'answers': {}, 'logins': {}}
        self.written = {}
        self.fetching = False
        self.config_asked = False
        self.flush_lock = threading.Lock()

    def client_connected(self, client):
        address = client.peername[0] if client.peername else '?'
        if address not in self.devices:
            self.devices.add(address)
            state('iphone')
            say(tr("Un appareil passe par l'ordinateur ({address}).", address=address))

    def tls_clienthello(self, data):
        if isinstance(data.context.client.proxy_mode, ReverseMode):
            name = (data.client_hello.sni or '').lower()
            if is_game(name):
                data.context.server.address = (name, 443)
                data.context.server.sni = name

    def request(self, flow):
        if not is_game(flow.request.pretty_host):
            return
        flow.metadata['rr_jeu'] = True
        auth = flow.request.headers.get('authorization', '')
        if len(auth) > 8:
            self.secrets.add(auth.encode())
            self.secrets.add(auth.split()[-1].encode())

    def response(self, flow):
        request, answer = (flow.request, flow.response)
        if answer is None or not flow.metadata.get('rr_jeu'):
            return
        path = request.path.split('?')[0]
        if path.endswith('/auth/login'):
            self.on_login(request, answer)
        elif not 200 <= answer.status_code < 300:
            return
        elif request.method == 'POST' and CONFIG_MAP.search(path):
            self.on_config_map(request, answer)
        elif request.method == 'GET':
            self.on_download(path, answer.content)

    def tls_established_client(self, data):
        self.tls_ok(data.context.client.sni or '')

    def tls_failed_client(self, data):
        self.tls_refused(data.context.client.sni or '', data.conn.error)

    def tls_ok(self, host):
        if is_game(host) and (not self.accepted):
            self.accepted = True
            state('jeu')
            say(tr('Le jeu accepte le certificat : la copie peut se faire.'))

    def tls_refused(self, host, error):
        if not is_game(host) or self.accepted or (not self.refusals.ready()):
            return
        state('certificat')
        say(tr("Le jeu refuse le certificat de l'ordinateur ({host}).", host=host))
        say(tr("  Sur l'iPhone, le profil doit être installé ET accepté :"))
        say(tr("  1. Réglages > Général > VPN et gestion de l'appareil > RatchetRR > Installer."))
        say(tr('  2. Réglages > Général > Informations, tout en bas « Réglages des certificats » :'))
        say(tr('     activer RatchetRR > Continuer.'))
        say(tr('  Puis fermer complètement le jeu et le rouvrir.'))
        say(tr('  (détail : {error})', error=error))

    def on_login(self, request, answer):
        for side in (request.content, answer.content):
            body = unpack(side)
            if isinstance(body, dict):
                for key in SECRET_KEYS:
                    long_strings(body.get(key), self.secrets)
        body = unpack(answer.content)
        if not isinstance(body, dict) or not body.get('publicId'):
            return
        state('jeu')
        say(tr('Le jeu se connecte au compte {publicId}.', publicId=body['publicId']))
        if not body.get('networkChoiceRequired'):
            for key in SECRET_KEYS:
                if key in body:
                    body[key] = ''
            self.server['logins'][body['publicId']] = msgpack.packb(body, use_bin_type=True)
            self.flush_server()

    def on_config_map(self, request, answer):
        if self.on_config(answer.content, answer.headers.get('obb-client-vnum', '')) or self.config_asked:
            return
        self.config_asked = True
        threading.Thread(target=self.ask_config, args=(request.copy(),), daemon=True).start()

    def on_download(self, path, content):
        if (match := CONFIG_ITEM.search(path)):
            self.server['items'][match.group(1)] = content
            self.flush_server()
        elif (match := SOCIAL.search(path)):
            self.server['answers'][match.group(1)] = content
            self.flush_server()
        elif REVENUE.search(path):
            self.server['er'] = content
            self.flush_server()
        elif (match := SAVE.search(path)):
            self.on_save(match.group(1), content)
        elif (match := EVENTS.search(path)):
            self.on_events(match.group(1), content)

    def on_config(self, content, vnum):
        config = unpack(content)
        if not isinstance(config, dict) or not config.get('items'):
            return False
        self.server['config'] = content
        self.server['vnum'] = vnum
        urls = {}
        for item in config['items']:
            url = item.get('url')
            if url and (not item.get('value')):
                url = url.decode() if isinstance(url, bytes) else url
                urls[url.split('?')[0].rstrip('/').rsplit('/', 1)[1]] = url
        self.server['urls'] = urls
        self.flush_server()
        return True

    def ask_config(self, request):
        body = unpack(request.content)
        if not isinstance(body, dict):
            return
        body['hashes'] = {}
        headers = {name: value for name, value in request.headers.items() if name.lower() not in ('authorization', 'cookie', 'content-length', 'host', 'content-encoding')}
        build = request.headers.get('obb-build-version')
        if build:
            for name in ('obb-game-config-vnum', 'obb-client-vnum'):
                if name in request.headers:
                    headers[name] = f'{build}.0'
        try:
            context = public_context()
            asked = urllib.request.Request(request.url, data=msgpack.packb(body, use_bin_type=True), headers=headers, method='POST')
            with urllib.request.urlopen(asked, timeout=30, context=context) as answer:
                content = answer.read()
                if answer.headers.get('Content-Encoding', '').lower() == 'gzip' or content[:2] == b'\x1f\x8b':
                    content = gzip.decompress(content)
                if self.on_config(content, answer.headers.get('obb-client-vnum', '')):
                    return
        except DOWNLOAD_ERRORS as error:
            say(tr('  Configuration du jeu non reçue : {error}', error=error))
        say(tr("  Fermer complètement le jeu, le rouvrir et attendre l'écran d'accueil."))
        self.config_asked = False

    def on_save(self, user, raw):
        content = inflate(raw)
        body = unpack(content)
        parts = body.get('save') if isinstance(body, dict) else None
        if not parts:
            say(tr('La sauvegarde reçue est vide ou illisible. Fermer le jeu et le relancer.'))
            return
        digest = hashlib.sha256(content).hexdigest()
        if self.copied.get(user) == digest:
            say(tr('Le jeu a renvoyé la même sauvegarde : elle est déjà copiée.'))
            return
        now = datetime.datetime.now()
        folder = new_folder(OUT / f"{re.sub('[^A-Za-z0-9_-]', '_', user)}_{now:%Y-%m-%d_%H%M%S}")
        if not self.write(folder, 'save.msgpack', content):
            return
        readable = json.dumps(plain(body), indent=1, ensure_ascii=False, default=str).encode()
        self.write(folder, 'sauvegarde_lisible.json', readable)
        self.write(folder, 'INFO.txt', save_info(user, body, parts, digest, now).encode())
        self.folders[user] = folder
        self.copied[user] = digest
        events = self.pending_events.pop(user, None)
        if events:
            self.write(folder, 'events.msgpack', events)
        state('sauvegarde')
        say(tr('Sauvegarde copiée : compte {user}, {n_parts} parties.', user=user, n_parts=len(parts)))
        say(tr("  Rester sur l'écran d'accueil du jeu : il reste les données du serveur (environ 30 secondes)."))
        self.flush_server()

    def on_events(self, user, raw):
        content = inflate(raw)
        folder = self.folders.get(user)
        if folder:
            self.write(folder, 'events.msgpack', content)
        else:
            self.pending_events[user] = content

    def write(self, folder, name, data):
        if any((secret in data for secret in self.secrets)):
            say(tr('  {name} ignoré : il contenait une donnée de connexion.', name=name))
            return False
        (folder / name).write_bytes(data)
        return True

    def server_folder(self):
        folder = next(iter(self.folders.values()), None)
        if folder is None:
            return None
        target = folder / SERVER_DATA
        target.mkdir(exist_ok=True)
        (target / 'items').mkdir(exist_ok=True)
        return target

    def flush_server(self):
        with self.flush_lock:
            target = self.server_folder()
            if target is None:
                return
            for name, content in self.server_files():
                if not content:
                    continue
                digest = hashlib.sha256(content).digest()
                if self.written.get(name) != digest and self.write(target, name, content):
                    self.written[name] = digest
            if 'config' in self.server and (not self.fetching):
                self.fetching = True
                threading.Timer(ITEM_WAIT, self.fetch_missing_items).start()

    def server_files(self):
        data = self.server
        if 'config' in data:
            yield ('config-map.msgpack', data['config'])
            yield ('vnum.txt', data['vnum'].encode())
        for name, content in list(data['items'].items()):
            yield (f'items/{name}', content)
        for name, content in list(data['answers'].items()):
            yield (f'{name}.msgpack', inflate(content))
        yield ('er.json', data.get('er'))
        yield ('login.msgpack', data['logins'].get(next(iter(self.folders))))

    def fetch_missing_items(self):
        missing = {name: url for name, url in self.server.get('urls', {}).items() if name not in self.server['items']}
        for name, url in missing.items():
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'RangerRumble'}), timeout=30, context=public_context()) as answer:
                    self.server['items'][name] = answer.read()
            except DOWNLOAD_ERRORS as error:
                say(tr('  Fichier de configuration {name} non téléchargé : {error}', name=name, error=error))
        self.flush_server()
        target = self.server_folder()
        lacking = [name for name in SERVER_FILES if not (target / name).exists()]
        lacking += [f'items/{name}' for name in self.server.get('urls', {}) if not (target / 'items' / name).exists()]
        if lacking:
            say(tr('Données du serveur incomplètes (il manque : ') + ', '.join(lacking) + ').')
            say(tr("  Fermer complètement le jeu, le rouvrir et attendre l'écran d'accueil."))
            self.fetching = False
        else:
            self.finished()

    def finished(self):
        folder = next(iter(self.folders.values()))
        say()
        say('=' * 62)
        state('fini')
        say(tr("  C'EST FAIT : SAUVEGARDE ET DONNÉES COPIÉES !"))
        say(tr('  Dossier : {folder}', folder=folder))
        say('=' * 62)
        say(tr("Maintenant, sur l'iPhone, supprimer le profil RatchetRR :"))
        say(tr("  Réglages > Général > VPN et gestion de l'appareil > RatchetRR > Supprimer le profil."))
        say(tr('  (Si le proxy a été réglé à la main, le remettre sur Désactivé.)'))
        say(tr("La copie s'arrête toute seule."))
        say()
        if STOP is not None:
            threading.Timer(STOP_DELAY, STOP).start()

def new_folder(base):
    folder, number = (base, 1)
    while folder.exists():
        number += 1
        folder = base.with_name(f'{base.name}_{number}')
    folder.mkdir(parents=True)
    return folder

def save_info(user, body, parts, digest, when):
    return '\n'.join([tr('Copie de sauvegarde - Ratchet & Clank: Ranger Rumble'), tr('Compte : {user}', user=user), tr('Copiée le : {v}', v=when.strftime('%d/%m/%Y à %H:%M')), tr('Plateforme : {v}  |  version du jeu : {v2}', v=body.get('platform'), v2=body.get('buildNumber')), tr('Parties de sauvegarde : {n_parts}', n_parts=len(parts)), tr('Empreinte de save.msgpack (sha256) : {digest}', digest=digest), '', tr('save.msgpack est la sauvegarde exacte envoyée par les serveurs officiels.'), tr('sauvegarde_lisible.json est la même chose en texte lisible.'), tr('Ce dossier ne contient ni mot de passe ni jeton de connexion.'), ''])

def page(address, proxy_port):
    steps = [tr('<b>1.</b> Toucher le bouton, puis <b>Autoriser</b>.'), tr("<b>2.</b> Ouvrir <b>Réglages</b> : en haut, toucher <b>Profil téléchargé</b> (ou Général &gt; <b>VPN et gestion de l'appareil</b> &gt; RatchetRR). Toucher <b>Installer</b>, le code de l'iPhone, et encore <b>Installer</b>."), tr("<b>3.</b> Réglages &gt; Général &gt; <b>Informations</b> (pas VPN). Tout en bas de cette page : <b>Réglages des certificats</b> (la ligne n'apparaît qu'après l'étape 2). Activer <b>RatchetRR</b>, puis <b>Continuer</b>."), tr("<b>4.</b> Ouvrir Ranger Rumble et attendre l'écran d'accueil. C'est tout : la fenêtre de l'ordinateur dira quand c'est fini."), tr("<b>À la fin :</b> supprimer le profil (Réglages &gt; Général &gt; VPN et gestion de l'appareil &gt; RatchetRR). Sinon le jeu ne se connecte plus.")]
    manual = tr('Si la copie ne démarre pas, régler le proxy à la main : Réglages &gt; Wi-Fi &gt; (i) &gt; Configurer le proxy &gt; Manuel, serveur <code>{address}</code>, port <code>{port}</code> (et le remettre sur Désactivé après).', address=address, port=proxy_port)
    title = tr('Copie de sauvegarde')
    return f'''<!doctype html><html lang="{LANGUAGE}"><head><meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n<title>{title} Ranger Rumble</title>\n<style>body{{font-family:-apple-system,system-ui,sans-serif;max-width:34em;margin:1em auto;padding:0 1em;line-height:1.5}}\na.b{{display:block;text-align:center;background:#1b6ef3;color:#fff;padding:.9em;border-radius:.6em;text-decoration:none;font-weight:600;margin:1em 0}}\ncode{{background:#eee;padding:.1em .3em;border-radius:.3em}} small{{color:#555}}</style></head><body>\n<h1>{title}</h1>\n<p>{steps[0]}</p>\n<a class="b" href="/{PROFILE_FILE}">{tr('Télécharger le profil RatchetRR')}</a>\n{''.join((f'<p>{step}</p>' for step in steps[1:]))}\n<p><small>{manual}</small></p>\n</body></html>'''.encode()

def serve_page(address, proxy_port, page_port):
    certificate = CA_FILE.read_bytes()
    told = set()

    class Handler(BaseHTTPRequestHandler):

        def do_GET(self):
            path = self.path.split('?')[0]
            if path == f'/{PROFILE_FILE}':
                state('iphone')
                say(tr("L'iPhone télécharge le profil RatchetRR."))
                body, kind = (mobileconfig(address, AUTO), 'application/x-apple-aspen-config')
            elif path.startswith('/certificat'):
                say(tr('Le téléphone télécharge le certificat.'))
                body, kind = (certificate, 'application/x-x509-ca-cert')
            else:
                state('iphone')
                if 'page' not in told:
                    told.add('page')
                    say(tr("Le téléphone a ouvert la page d'aide."))
                body, kind = (page(address, proxy_port), 'text/html; charset=utf-8')
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

def set_stop(shutdown):
    global STOP
    loop = asyncio.get_running_loop()

    def stop():
        loop.call_soon_threadsafe(shutdown)
    STOP = stop

def close_helpers(page_server, dns_server):
    if page_server is not None:
        page_server.shutdown()
        page_server.server_close()
    if dns_server is not None:
        dns_server.close()

async def run_pure(address, proxy_port, page_port, ready=None):
    authority = moteur_pur.make_authority(CONF, PROFILE)
    insecure = False
    proxy = moteur_pur.Proxy(authority, Recorder(), is_game, insecure)
    await proxy.start(proxy_port, HTTPS_PORT if AUTO else None)
    set_stop(proxy.shutdown)
    dns_server = page_server = None
    try:
        if AUTO:
            dns_server = await serve_dns(address, moteur_pur.dns_context(authority, DNS_NAME, address), pure_dns_answer)
        page_server = serve_page(address, proxy_port, page_port)
        if ready:
            ready(proxy, page_server)
    except BaseException:
        proxy.shutdown()
        raise
    finally:
        try:
            await proxy.wait()
        finally:
            close_helpers(page_server, dns_server)

def mitmproxy_master(proxy_port):
    opts = options.Options(listen_host='0.0.0.0', listen_port=proxy_port, confdir=str(CONF))
    master = DumpMaster(opts, with_termlog=True, with_dumper=False)
    settings = {'allow_hosts': GAME_HOSTS, 'termlog_verbosity': 'error'}
    if AUTO:
        settings.update(mode=[f'regular@{proxy_port}', f'reverse:https://obb.cloud@{HTTPS_PORT}'], connection_strategy='lazy')
    master.options.update(**settings)
    master.addons.add(Recorder())
    return master

async def close_listeners(master):
    proxy_server = master.addons.get('proxyserver')
    if proxy_server is not None:
        await proxy_server.servers.update([])

async def run(address, proxy_port, page_port, ready=None):
    if PURE:
        return await run_pure(address, proxy_port, page_port, ready)
    master = mitmproxy_master(proxy_port)
    set_stop(master.shutdown)
    dns_server = page_server = None
    try:
        if AUTO:
            dns_server = await serve_dns(address)
        page_server = serve_page(address, proxy_port, page_port)
        if ready:
            ready(master, page_server)
        await master.run()
    finally:
        try:
            await close_listeners(master)
        finally:
            close_helpers(page_server, dns_server)

def profile_name():
    if PURE:
        return moteur_pur.authority_name(CONF)
    try:
        return certs.Cert.from_pem(CA_FILE.read_bytes()).cn
    except (OSError, ValueError):
        return None

def make_certificate():
    if PURE:
        moteur_pur.new_authority(CONF, PROFILE)
        return
    for old in CONF.glob('mitmproxy-ca*'):
        old.unlink()
    certs.CertStore.create_store(CONF, 'mitmproxy', 2048, organization=PROFILE, cn=PROFILE)

def instructions(address, proxy_port, page_port):
    lines = ['', tr('=== Copie de sauvegarde - Ratchet & Clank: Ranger Rumble ===')]
    lines += ['', tr("L'iPhone et cet ordinateur doivent être sur le même Wi-Fi."), '', tr("ÉTAPE 1 - sur l'iPhone, viser le QR code de la fenêtre avec l'appareil photo"), tr("      (ou ouvrir Safari à l'adresse http://{address}:{page_port} ).", address=address, page_port=page_port), tr('      Toucher « Télécharger le profil RatchetRR », puis « Autoriser ».'), '', tr('ÉTAPE 2 - installer le profil : Réglages > « Profil téléchargé » (en haut)'), tr("      > Installer > code de l'iPhone > Installer."), '', tr('ÉTAPE 3 - accepter le profil (sinon le jeu le refuse) :'), tr('      Réglages > Général > Informations > tout en bas « Réglages des certificats »'), tr('      > activer « RatchetRR » > Continuer.'), '', tr("ÉTAPE 4 - ouvrir Ranger Rumble et attendre l'écran d'accueil. C'est tout."), '']
    if not AUTO:
        lines.append(tr('Ports {a} et {b} pris sur cet ordinateur : il faut régler le proxy à la main.', a=HTTPS_PORT, b=DOT_PORT))
    lines += [tr("SI RIEN NE SE PASSE - régler le proxy à la main sur l'iPhone :"), tr('      Réglages > Wi-Fi > (i) > Configurer le proxy > Manuel'), tr('      Serveur : {address}      Port : {proxy_port}', address=address, proxy_port=proxy_port), tr('      Puis fermer complètement le jeu et le rouvrir.'), '', tr("À LA FIN - supprimer le profil RatchetRR de l'iPhone et remettre le proxy sur Désactivé."), '', tr('Laisser cette fenêtre ouverte : elle dira quand la sauvegarde est copiée.'), tr('Les copies vont dans : {OUT}', OUT=OUT), '']
    return lines

def prepare():
    global AUTO
    OUT.mkdir(parents=True, exist_ok=True)
    CONF.mkdir(parents=True, exist_ok=True)
    if profile_name() != PROFILE:
        make_certificate()
    address = local_ip()
    proxy_port = free_port(8080)
    page_port = free_port(8090, taken=(proxy_port,))
    AUTO = can_listen(HTTPS_PORT) and can_listen(DOT_PORT)
    for line in instructions(address, proxy_port, page_port):
        print(line)
    return (address, proxy_port, page_port)

def main():
    sys.stdout.reconfigure(line_buffering=True)
    address, proxy_port, page_port = prepare()
    try:
        asyncio.run(run(address, proxy_port, page_port))
    except KeyboardInterrupt:
        pass
if __name__ == '__main__':
    sys.exit(main())
