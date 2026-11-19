import asyncio
import base64
import datetime
import gzip
import hashlib
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
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import msgpack
PUR = os.name == 'nt' or os.environ.get('RR_MOTEUR_PUR') == '1'
if PUR:
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
PROFILE_FILE = 'RatchetRR.mobileconfig'
DNS_DOMAINS = ['obb.cloud', 'obb.com', 'ohbibi.com', 'cloudfunctions.net']
DNS_NAME = 'dns.ratchetrr'
DOT_PORT = 853
HTTPS_PORT = 443
AUTO = True

def say(message=''):
    print(f"{time.strftime('%H:%M:%S')}  {message}" if message else '', flush=True)
ON_STATE = None
STOP = None
STOP_DELAY = 3

def state(name):
    if ON_STATE is not None:
        try:
            ON_STATE(name)
        except Exception:
            pass

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
    raise SystemExit(tr('Aucun port libre entre {start} et {v}.', start=start, v=start + 39))

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
        if GAME.search(name):
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
    if kind not in (1, 28):
        return moteur_pur.dns_reply(query, [])
    if GAME.search(name):
        return moteur_pur.dns_reply(query, [(address, 5)] if kind == 1 else [])
    found = await asyncio.get_running_loop().run_in_executor(None, moteur_pur.resolve, name, kind)
    return moteur_pur.dns_reply(query, [(ip, 60) for ip in found])

async def serve_dns(address, context=None, answer=None):
    context = context or dns_certificate(address)
    answer = answer or dns_answer
    seen = {'used': False, 'refused_at': 0.0}

    async def client(reader, writer):
        try:
            await asyncio.wait_for(writer.start_tls(context), 15)
        except Exception as error:
            if isinstance(error, ssl.SSLError) and time.time() - seen['refused_at'] > 30:
                seen['refused_at'] = time.time()
                state('certificat')
                say(tr("L'iPhone refuse le certificat de l'ordinateur."))
                say(tr('  Réglages > Général > Informations > Réglages des certificats > active RatchetRR.'))
            writer.close()
            return
        if not seen['used']:
            seen['used'] = True
            state('iphone')
            say(tr("L'iPhone utilise le profil RatchetRR : ouvre le jeu."))
        try:
            while True:
                head = await asyncio.wait_for(reader.readexactly(2), 120)
                query = await reader.readexactly(int.from_bytes(head, 'big'))
                reply = await answer(query, address)
                writer.write(len(reply).to_bytes(2, 'big') + reply)
                await writer.drain()
        except Exception:
            pass
        finally:
            writer.close()
    return await asyncio.start_server(client, '0.0.0.0', DOT_PORT)

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
            if GAME.search(name):
                data.context.server.address = (name, 443)
                data.context.server.sni = name

    def request(self, flow):
        if not GAME.search(flow.request.pretty_host):
            return
        flow.metadata['rr_jeu'] = True
        auth = flow.request.headers.get('authorization', '')
        if len(auth) > 8:
            self.secrets.add(auth.encode())
            self.secrets.add(auth.split()[-1].encode())

    def response(self, flow):
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
            if not self.on_config(res.content, res.headers.get('obb-client-vnum', '')) and (not self.config_asked):
                self.config_asked = True
                threading.Thread(target=self.ask_config, args=(req.copy(),), daemon=True).start()
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
            state('jeu')
            say(tr('Le jeu se connecte au compte {publicId}.', publicId=body['publicId']))
            if not body.get('networkChoiceRequired'):
                for key in SECRET_KEYS:
                    if key in body:
                        body[key] = ''
                self.server['logins'][body['publicId']] = msgpack.packb(body, use_bin_type=True)
                self.flush_server()

    def on_config(self, content, vnum):
        config = unpack(content)
        if not isinstance(config, dict) or not config.get('items'):
            return False
        self.server['config'] = content
        self.server['vnum'] = vnum
        urls = {}
        for item in (config or {}).get('items', []):
            url = item.get('url')
            if url and (not item.get('value')):
                url = url.decode() if isinstance(url, bytes) else url
                urls[url.split('?')[0].rstrip('/').rsplit('/', 1)[1]] = url
        self.server['urls'] = urls
        self.flush_server()
        return True

    def ask_config(self, request):
        import urllib.request
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
        url = request.url
        try:
            import certifi
            context = ssl.create_default_context(cafile=certifi.where())
            asked = urllib.request.Request(url, data=msgpack.packb(body, use_bin_type=True), headers=headers, method='POST')
            with urllib.request.urlopen(asked, timeout=30, context=context) as answer:
                content = answer.read()
                if answer.headers.get('Content-Encoding', '').lower() == 'gzip' or content[:2] == b'\x1f\x8b':
                    content = gzip.decompress(content)
                if self.on_config(content, answer.headers.get('obb-client-vnum', '')):
                    return
        except Exception as error:
            say(tr('  Configuration du jeu non reçue : {error}', error=error))
        say(tr("  Ferme complètement le jeu, rouvre-le et attends l'écran d'accueil."))
        self.config_asked = False

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
            self._flush_server()

    def _flush_server(self):
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
        for name, content in list(data['items'].items()):
            put(f'items/{name}', content)
        for name, content in list(data['answers'].items()):
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
                say(tr('  Fichier de configuration {name} non téléchargé : {error}', name=name, error=error))
        self.flush_server()
        target = self.server_folder()
        lacking = [n for n in ('config-map.msgpack', 'login.msgpack', 'er.json', 'invites.msgpack', 'chats.msgpack', 'friends.msgpack', 'groups.msgpack') if not (target / n).exists()]
        lacking += [f'items/{n}' for n in self.server.get('urls', {}) if not (target / 'items' / n).exists()]
        if lacking:
            say(tr('Données du serveur incomplètes (il manque : ') + ', '.join(lacking) + ').')
            say(tr("  Ferme complètement le jeu, rouvre-le et attends l'écran d'accueil."))
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
        say(tr("Maintenant, sur l'iPhone, supprime le profil RatchetRR :"))
        say(tr("  Réglages > Général > VPN et gestion de l'appareil > RatchetRR > Supprimer le profil."))
        say(tr('  (Si tu avais réglé le proxy à la main, remets-le sur Désactivé.)'))
        say(tr("La copie s'arrête toute seule."))
        say()
        if STOP is not None:
            threading.Timer(STOP_DELAY, STOP).start()

    def write(self, folder, name, data):
        if any((secret in data for secret in self.secrets)):
            say(tr('  {name} ignoré : il contenait une donnée de connexion.', name=name))
            return False
        (folder / name).write_bytes(data)
        return True

    def on_save(self, user, raw):
        content = inflate(raw)
        body = unpack(content)
        parts = body.get('save') if isinstance(body, dict) else None
        if not parts:
            say(tr('La sauvegarde reçue est vide ou illisible. Ferme le jeu et relance-le.'))
            return
        digest = hashlib.sha256(content).hexdigest()
        if self.copied.get(user) == digest:
            say(tr('Le jeu a renvoyé la même sauvegarde : elle est déjà copiée.'))
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
        info = '\n'.join([tr('Copie de sauvegarde - Ratchet & Clank: Ranger Rumble'), tr('Compte : {user}', user=user), tr('Copiée le : {v}', v=datetime.datetime.now().strftime('%d/%m/%Y à %H:%M')), tr('Plateforme : {v}  |  version du jeu : {v2}', v=body.get('platform'), v2=body.get('buildNumber')), tr('Parties de sauvegarde : {n_parts}', n_parts=len(parts)), tr('Empreinte de save.msgpack (sha256) : {digest}', digest=digest), '', tr('save.msgpack est la sauvegarde exacte envoyée par les serveurs officiels.'), tr('sauvegarde_lisible.json est la même chose en texte lisible.'), tr('Ce dossier ne contient ni mot de passe ni jeton de connexion.'), ''])
        self.write(folder, 'INFO.txt', info.encode())
        self.folders[user] = folder
        self.copied[user] = digest
        events = self.pending_events.pop(user, None)
        if events:
            self.write(folder, 'events.msgpack', events)
        state('sauvegarde')
        say(tr('Sauvegarde copiée : compte {user}, {n_parts} parties.', user=user, n_parts=len(parts)))
        say(tr("  Reste sur l'écran d'accueil du jeu : il reste les données du serveur (environ 30 secondes)."))
        self.flush_server()

    def on_events(self, user, raw):
        content = inflate(raw)
        folder = self.folders.get(user)
        if folder:
            self.write(folder, 'events.msgpack', content)
        else:
            self.pending_events[user] = content

    def tls_established_client(self, data):
        self.tls_ok(data.context.client.sni or '')

    def tls_failed_client(self, data):
        self.tls_refused(data.context.client.sni or '', data.conn.error)

    def tls_ok(self, host):
        if GAME.search(host) and (not self.accepted):
            self.accepted = True
            state('jeu')
            say(tr('Le jeu accepte le certificat : la copie peut se faire.'))

    def tls_refused(self, host, error):
        if not GAME.search(host) or self.accepted or time.time() - self.refused_at < 30:
            return
        self.refused_at = time.time()
        state('certificat')
        say(tr("Le jeu refuse le certificat de l'ordinateur ({host}).", host=host))
        say(tr("  Sur l'iPhone, le profil doit être installé ET accepté :"))
        say(tr("  1. Réglages > Général > VPN et gestion de l'appareil > RatchetRR > Installer."))
        say(tr('  2. Réglages > Général > Informations, tout en bas « Réglages des certificats » :'))
        say(tr('     active RatchetRR > Continuer.'))
        say(tr('  Puis ferme complètement le jeu et rouvre-le.'))
        say(tr('  (détail : {error})', error=error))

def page(address, proxy_port):
    steps = [tr('<b>1.</b> Touche le bouton, puis <b>Autoriser</b>.'), tr("<b>2.</b> Ouvre <b>Réglages</b> : en haut, touche <b>Profil téléchargé</b> (ou Général &gt; <b>VPN et gestion de l'appareil</b> &gt; RatchetRR). Touche <b>Installer</b>, le code de l'iPhone, et encore <b>Installer</b>."), tr("<b>3.</b> Réglages &gt; Général &gt; <b>Informations</b> (pas VPN). Tout en bas de cette page : <b>Réglages des certificats</b> (la ligne n'apparaît qu'après l'étape 2). Active <b>RatchetRR</b>, puis <b>Continuer</b>."), tr("<b>4.</b> Ouvre Ranger Rumble et attends l'écran d'accueil. C'est tout : la fenêtre de l'ordinateur dira quand c'est fini."), tr("<b>À la fin :</b> supprime le profil (Réglages &gt; Général &gt; VPN et gestion de l'appareil &gt; RatchetRR). Sinon le jeu ne se connecte plus.")]
    manual = tr('Si la copie ne démarre pas, règle le proxy à la main : Réglages &gt; Wi-Fi &gt; (i) &gt; Configurer le proxy &gt; Manuel, serveur <code>{address}</code>, port <code>{port}</code> (et remets-le sur Désactivé après).', address=address, port=proxy_port)
    title = tr('Copie de sauvegarde')
    return f'''<!doctype html><html lang="{LANGUAGE}"><head><meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n<title>{title} Ranger Rumble</title>\n<style>body{{font-family:-apple-system,system-ui,sans-serif;max-width:34em;margin:1em auto;padding:0 1em;line-height:1.5}}\na.b{{display:block;text-align:center;background:#1b6ef3;color:#fff;padding:.9em;border-radius:.6em;text-decoration:none;font-weight:600;margin:1em 0}}\ncode{{background:#eee;padding:.1em .3em;border-radius:.3em}} small{{color:#555}}</style></head><body>\n<h1>{title}</h1>\n<p>{steps[0]}</p>\n<a class="b" href="/{PROFILE_FILE}">{tr('Télécharger le profil RatchetRR')}</a>\n{''.join((f'<p>{step}</p>' for step in steps[1:]))}\n<p><small>{manual}</small></p>\n</body></html>'''.encode()

def serve_page(address, proxy_port, page_port):
    certificate = CA_FILE.read_bytes()
    told = set()

    def once(what, message):
        state('iphone')
        if what not in told:
            told.add(what)
            say(message)

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
                once('page', tr("Le téléphone a ouvert la page d'aide."))
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

async def run_pure(address, proxy_port, page_port, ready=None):
    authority = moteur_pur.make_authority(CONF, PROFILE)
    insecure = False
    global STOP
    proxy = moteur_pur.Proxy(authority, Recorder(), lambda host: bool(GAME.search(host)), insecure)
    await proxy.start(proxy_port, HTTPS_PORT if AUTO else None)
    loop = asyncio.get_running_loop()
    STOP = lambda: loop.call_soon_threadsafe(proxy.shutdown)
    dns_server = page_server = None
    try:
        if AUTO:
            dns_server = await serve_dns(address, moteur_pur.dns_context(authority, DNS_NAME, address), pure_dns_answer)
        page_server = serve_page(address, proxy_port, page_port)
        if ready:
            ready(proxy, page_server)
    except BaseException:
        proxy.shutdown()
        await proxy.wait()
        if dns_server is not None:
            dns_server.close()
        raise
    try:
        await proxy.wait()
    finally:
        page_server.shutdown()
        page_server.server_close()
        if dns_server is not None:
            dns_server.close()

async def run(address, proxy_port, page_port, ready=None):
    if PUR:
        return await run_pure(address, proxy_port, page_port, ready)
    opts = options.Options(listen_host='0.0.0.0', listen_port=proxy_port, confdir=str(CONF))
    master = DumpMaster(opts, with_termlog=True, with_dumper=False)
    settings = {'allow_hosts': GAME_HOSTS, 'termlog_verbosity': 'error'}
    dns_server = None
    if AUTO:
        settings.update(mode=[f'regular@{proxy_port}', f'reverse:https://obb.cloud@{HTTPS_PORT}'], connection_strategy='lazy')
        dns_server = await serve_dns(address)
    master.options.update(**settings)
    master.addons.add(Recorder())
    global STOP
    loop = asyncio.get_running_loop()
    STOP = lambda: loop.call_soon_threadsafe(master.shutdown)
    page_server = serve_page(address, proxy_port, page_port)
    if ready:
        ready(master, page_server)
    try:
        await master.run()
    finally:
        page_server.shutdown()
        page_server.server_close()
        if dns_server is not None:
            dns_server.close()

def profile_name():
    if PUR:
        return moteur_pur.authority_name(CONF)
    try:
        return certs.Cert.from_pem(CA_FILE.read_bytes()).cn
    except (OSError, ValueError):
        return None

def prepare():
    global AUTO
    OUT.mkdir(parents=True, exist_ok=True)
    CONF.mkdir(parents=True, exist_ok=True)
    if profile_name() != PROFILE:
        if PUR:
            moteur_pur.new_authority(CONF, PROFILE)
        else:
            for old in CONF.glob('mitmproxy-ca*'):
                old.unlink()
            certs.CertStore.create_store(CONF, 'mitmproxy', 2048, organization=PROFILE, cn=PROFILE)
    address = local_ip()
    proxy_port = free_port(8080)
    page_port = free_port(8090, taken=(proxy_port,))
    AUTO = can_listen(HTTPS_PORT) and can_listen(DOT_PORT)
    print()
    print(tr('=== Copie de sauvegarde - Ratchet & Clank: Ranger Rumble ==='))
    print()
    print(tr("L'iPhone et cet ordinateur doivent être sur le même Wi-Fi."))
    print()
    print(tr("ÉTAPE 1 - sur l'iPhone, vise le QR code de la fenêtre avec l'appareil photo"))
    print(tr("      (ou ouvre Safari à l'adresse http://{address}:{page_port} ).", address=address, page_port=page_port))
    print(tr('      Touche « Télécharger le profil RatchetRR », puis « Autoriser ».'))
    print()
    print(tr('ÉTAPE 2 - installe le profil : Réglages > « Profil téléchargé » (en haut)'))
    print(tr("      > Installer > code de l'iPhone > Installer."))
    print()
    print(tr('ÉTAPE 3 - accepte le profil (sinon le jeu le refuse) :'))
    print(tr('      Réglages > Général > Informations > tout en bas « Réglages des certificats »'))
    print(tr('      > active « RatchetRR » > Continuer.'))
    print()
    print(tr("ÉTAPE 4 - ouvre Ranger Rumble et attends l'écran d'accueil. C'est tout."))
    print()
    if not AUTO:
        print(tr('Ports {a} et {b} pris sur cet ordinateur : règle le proxy à la main.', a=HTTPS_PORT, b=DOT_PORT))
    print(tr("SI RIEN NE SE PASSE - règle le proxy à la main sur l'iPhone :"))
    print(tr('      Réglages > Wi-Fi > (i) > Configurer le proxy > Manuel'))
    print(tr('      Serveur : {address}      Port : {proxy_port}', address=address, proxy_port=proxy_port))
    print(tr('      Puis ferme complètement le jeu et rouvre-le.'))
    print()
    print(tr("À LA FIN - supprime le profil RatchetRR de l'iPhone et remets le proxy sur Désactivé."))
    print()
    print(tr('Laisse cette fenêtre ouverte : elle dira quand la sauvegarde est copiée.'))
    print(tr('Les copies vont dans : {OUT}', OUT=OUT))
    print()
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
