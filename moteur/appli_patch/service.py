import argparse
import asyncio
import collections
import datetime
import io
import json
import mimetypes
import os
import queue
import secrets
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import commun
import copie_android
import editeur_modele as em
import jeu_mac
import langues
import mises_a_jour
import sauvegarde as sv
from langues import tr
WEB = HERE / 'web'
PICTURES = HERE / 'ressources'
SHOWN_PICTURES = ('lanceur', 'icones')
FILE_TYPES = {'.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.svg': 'image/svg+xml', '.ico': 'image/x-icon', '.webp': 'image/webp', '.otf': 'font/otf', '.ttf': 'font/ttf'}
KEY = commun.BASE / 'cle_apk.p12'
CERTIFICATE = commun.BASE / 'certificat'
READY_MARK = commun.BASE / 'venv' / 'rr-pret'
READY_EXPECTED = HERE.parent / 'pret.txt'
DEFAULTS = {'langue': langues.CURRENT, 'maj_demarrage': True, 'page_depart': 'accueil', 'derniere_page': 'android', 'son_fin': True, 'anti_veille': True, 'animations': 'completes', 'accent': 'vert', 'adb': '', 'dossier_travail': '', 'official': '', 'output': str(commun.DEFAULT_APK), 'artworks': '', 'sauvegarde': '', 'nouvelle_partie': False, 'dossier_sauvegardes': ''}
CHOICES = {'page_depart': ('accueil', 'derniere'), 'animations': ('completes', 'reduites', 'aucune'), 'accent': ('or', 'bleu', 'vert', 'violet'), 'langue': tuple(dict(langues.LANGUAGES))}
FLAGS = ('maj_demarrage', 'son_fin', 'anti_veille', 'nouvelle_partie')
BAR_TASKS = ('fabrication', 'maj_telephone', 'ordinateur')
WORK_FOLDER_TASKS = BAR_TASKS + ('maj_outil',)
PHONE_TASKS = ('installation', 'maj_telephone')
LAST_STEP = 6
PHONES_EVERY = 3
VERSION_EVERY = 5
ADB_ERRORS = (OSError, subprocess.SubprocessError)
ES_CONTINUOUS, ES_SYSTEM_REQUIRED = (2147483648, 1)

class Erreur(Exception):

    def __init__(self, message: str, code: str | None=None, **details):
        super().__init__(message)
        self.code, self.details = (code, details)

def stamp() -> str:
    return f'{datetime.datetime.now():%Y-%m-%d_%H%M%S}'

def file_day(path: Path) -> str:
    return datetime.datetime.fromtimestamp(path.stat().st_mtime).strftime('%d/%m/%Y')

def put_aside(path: Path, prefix: str, suffix: str) -> None:
    path.rename(path.with_name(f'{prefix}_{stamp()}{suffix}'))

class Bus:
    STICKY = ('copie', 'copie_qr', 'telephones', 'maj', 'tache', 'barre')

    def __init__(self):
        self.lock = threading.Lock()
        self.listeners = []
        self.lines = collections.deque(maxlen=3000)
        self.last = {}

    def send(self, kind: str, **data) -> None:
        event = {'type': kind, **data}
        with self.lock:
            if kind == 'journal':
                self.lines.append(data['texte'])
            if kind in self.STICKY:
                self.last[kind] = event
            if kind == 'tache' and data.get('etat') == 'fin':
                self.last.pop('tache', None)
                self.last.pop('barre', None)
            for listener in self.listeners:
                listener.put(event)

    def listen(self) -> queue.Queue:
        listener = queue.Queue()
        with self.lock:
            for event in self.last.values():
                listener.put(event)
            self.listeners.append(listener)
        return listener

    def leave(self, listener: queue.Queue) -> None:
        with self.lock:
            if listener in self.listeners:
                self.listeners.remove(listener)

    def listening(self) -> bool:
        with self.lock:
            return bool(self.listeners)

    def journal(self) -> list[str]:
        with self.lock:
            return list(self.lines)
BUS = Bus()

class Output(io.TextIOBase):
    encoding = 'utf-8'

    def __init__(self):
        super().__init__()
        self.lock = threading.Lock()
        self.pending = ''

    def writable(self) -> bool:
        return True

    def write(self, text: str) -> int:
        with self.lock:
            self.pending += text
            *lines, self.pending = self.pending.split('\n')
        for line in lines:
            self.line(line)
        return len(text)

    def flush(self) -> None:
        with self.lock:
            line, self.pending = (self.pending, '')
        if line:
            self.line(line)

    @staticmethod
    def line(text: str) -> None:
        step = commun.STEP.match(text.strip())
        if step and WORK.name in BAR_TASKS:
            number = int(step.group(1))
            what = tr('Préparation pour Mac') if WORK.name == 'ordinateur' else tr('Fabrication')
            if number in commun.BUILD_STEPS:
                start, goal, seconds = commun.BUILD_STEPS[number]
                bar(start, goal, seconds / 2, what, number)
            elif number == LAST_STEP:
                bar(100, 100, 0, what, LAST_STEP)
        BUS.send('journal', texte=text, tache=WORK.name)

def bar(start: float, goal: float, seconds: float, what: str, step: int | None=None) -> None:
    BUS.send('barre', tache=WORK.name, debut=start, but=goal, secondes=seconds, texte=what, etape=step)

def sending(what: str):

    def progress(fraction):
        if fraction >= copie_android.INSTALL_COPY_SHARE:
            bar(80, 99, 8, what)
        else:
            bar(fraction * 100, fraction * 100, 0, what)
    return progress

def fraction_bar(step: int | None=None):
    return lambda fraction, text: bar(fraction * 100, fraction * 100, 0, text, step)

def windows_keep_awake(on: bool) -> None:
    import ctypes
    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | (ES_SYSTEM_REQUIRED if on else 0))

class Work:
    PROBLEMS = (copie_android.Problem, mises_a_jour.Problem, em.Refus, jeu_mac.Probleme)

    def __init__(self):
        self.lock = threading.Lock()
        self.name = None
        self.awake_lock = threading.Lock()
        self.awake = None

    def start(self, name: str, function, *args) -> None:
        with self.lock:
            if self.name:
                raise Erreur(tr('Une tâche est déjà en cours : {name}.', name=task_name(self.name)), 'occupe')
            self.name = name
        BUS.send('tache', nom=name, etat='debut')
        self.keep_awake(True)
        threading.Thread(target=self.run, args=(name, function, args), daemon=True).start()

    def run(self, name: str, function, args: tuple) -> None:
        result, error, code, details = (None, None, None, {})
        windows_awake = os.name == 'nt' and setting('anti_veille')
        if windows_awake:
            windows_keep_awake(True)
        try:
            result = function(*args)
        except copie_android.OtherSignature as problem:
            error, code = (str(problem), 'autre_signature')
        except self.PROBLEMS as problem:
            error = str(problem)
        except Erreur as problem:
            error, code, details = (str(problem), problem.code, problem.details)
        except SystemExit as stop:
            error = str(stop)
        except Exception as failure:
            error = f'{type(failure).__name__} : {failure}'
            print(traceback.format_exc())
        finally:
            sys.stdout.flush()
            self.keep_awake(False)
            if windows_awake:
                windows_keep_awake(False)
            with self.lock:
                self.name = None
        if error:
            print(tr('Échec : {error}', error=error))
        BUS.send('tache', nom=name, etat='fin', ok=error is None, erreur=error, code=code, resultat=result, **details)

    def keep_awake(self, on: bool) -> None:
        with self.awake_lock:
            if self.awake is not None:
                self.awake.terminate()
                self.awake.wait()
                self.awake = None
            if on and setting('anti_veille') and (sys.platform == 'darwin') and shutil.which('caffeinate'):
                self.awake = subprocess.Popen(['caffeinate', '-i', '-w', str(os.getpid())])
WORK = Work()

def task_name(name: str) -> str:
    return {'copie': tr('Copie de la sauvegarde'), 'fabrication': tr('Fabrication'), 'installation': tr('Installation'), 'maj_telephone': tr('Mise à jour du téléphone'), 'maj_outil': tr("Mise à jour de l'outil"), 'adb': tr('Outils Android'), 'ordinateur': tr('Préparation pour Mac')}.get(name, name)

def refuse_while_building() -> None:
    if WORK.name in WORK_FOLDER_TASKS:
        raise Erreur(tr('Il faut attendre la fin de la tâche en cours.'), 'occupe')

def settings() -> dict:
    stored = mises_a_jour.settings()
    return {**DEFAULTS, **{k: v for k, v in stored.items() if v is not None}}

def setting(key: str):
    return settings().get(key)

def checked_setting(key: str, value):
    if key not in DEFAULTS:
        raise Erreur(tr('Réglage inconnu : {key}', key=key))
    if key in FLAGS:
        return bool(value)
    if key in CHOICES and value not in CHOICES[key] or not isinstance(value, str):
        raise Erreur(tr('Valeur refusée pour {key}.', key=key))
    return value

def cmd_reglages_ecrire(body):
    values = {key: checked_setting(key, value) for key, value in body.items()}
    if 'langue' in values:
        if WORK.name:
            raise Erreur(tr('Il faut attendre la fin de la tâche en cours.'), 'occupe')
        langues.CURRENT = values['langue']
    mises_a_jour.remember(**values)
    return {'reglages': settings()}

def cmd_reinitialiser(_):
    path = Path(mises_a_jour.SETTINGS)
    if path.exists():
        put_aside(path, 'reglages', '.ancien.json')
    mises_a_jour.remember(langue=langues.CURRENT)
    return {'reglages': settings()}

def cmd_bonjour(_):
    info = mises_a_jour.current()
    return {'version': info['version'], 'jeu': info.get('jeu') or info['version'], 'depot': info.get('depot'), 'langue': langues.CURRENT, 'langues': [list(item) for item in langues.LANGUAGES], 'reglages': settings(), 'racine': str(commun.ROOT), 'moteur': str(HERE), 'ressources': str(PICTURES), 'copies': str(commun.COPIES), 'base': str(commun.BASE), 'systeme': sys.platform, 'tache': WORK.name}

def existing(path) -> str:
    if not path or not isinstance(path, str) or (not os.path.exists(path)):
        raise Erreur(tr('Introuvable : {path}', path=path or '?'))
    return path

def cmd_ouvrir(body):
    commun.open_folder(existing(body.get('chemin')), reveal=bool(body.get('montrer')))
    return {}

def free_space(path) -> int:
    folder = Path(path or Path.home())
    while not folder.exists() and folder != folder.parent:
        folder = folder.parent
    return shutil.disk_usage(folder).free

def cmd_espace(body):
    return {'libre': free_space(body.get('chemin'))}

def cmd_sauvegardes(body):
    folder = body.get('dossier') or setting('dossier_sauvegardes')
    listed = commun.saves(folder) if folder and os.path.isdir(folder) else []
    listed += [path for path in commun.saves() if path not in listed]
    chosen = setting('sauvegarde')
    if chosen and os.path.isfile(chosen) and (Path(chosen) not in listed) and commun.is_save(chosen):
        listed.insert(0, Path(chosen))
    return {'sauvegardes': [{'chemin': str(path), 'libelle': commun.save_label(path), 'type': commun.save_kind(path), 'date': commun.save_date(path)} for path in listed]}

def cmd_journal(_):
    return {'lignes': BUS.journal()}

class Copy:

    def __init__(self):
        self.lock = threading.Lock()
        self.starting = False
        self.stop_asked = False
        self.running = None

    def begin(self) -> None:
        with self.lock:
            if self.running is None:
                self.starting, self.stop_asked = (True, False)

    def ready(self, loop, master) -> None:
        with self.lock:
            self.running, self.starting = ((loop, master), False)
            stop = self.stop_asked
        if stop:
            master.shutdown()

    def request_stop(self) -> bool:
        with self.lock:
            if self.running is not None:
                loop, master = self.running
                loop.call_soon_threadsafe(master.shutdown)
                return True
            if self.starting:
                self.stop_asked = True
            return False

    def end(self) -> None:
        with self.lock:
            self.running, self.starting = (None, False)
COPY = Copy()

def qr_svg(url: str) -> str | None:
    try:
        import segno
        return segno.make(url, error='m').svg_inline(scale=8, border=2, dark='#0a1022', light='#ffffff')
    except Exception:
        return None

def cmd_copie_demarrer(_):
    COPY.begin()
    WORK.start('copie', copy_work)
    return {}

def copy_work():
    started = time.time()
    BUS.send('copie', etat='attente')
    reached = []

    def on_state(name):
        reached.append(name)
        BUS.send('copie', etat=name)

    def ready(master, _page):
        COPY.ready(asyncio.get_running_loop(), master)
        if os.name == 'nt':
            threading.Thread(target=check_firewall, daemon=True).start()
    try:
        tool = commun.load_tool()
        tool.ON_STATE = on_state
        address, proxy_port, page_port = tool.prepare()
        if not address.startswith(('192.168.', '10.', '172.')):
            print(tr("Cet ordinateur n'a pas d'adresse sur un réseau local ({address}) : il faut le mettre sur le même Wi-Fi que l'iPhone.", address=address))
        url = f'http://{address}:{page_port}'
        BUS.send('copie_qr', url=url, svg=qr_svg(url))
        asyncio.run(tool.run(address, proxy_port, page_port, ready))
    finally:
        COPY.end()
        BUS.send('copie_qr', url=None, svg=None)
        print(tr("Copie arrêtée. Il faut supprimer le profil RatchetRR de l'iPhone (Réglages > Général > VPN et gestion de l'appareil)."))
        BUS.send('copie', etat='arret', fini='fini' in reached)
    made = [folder for folder in commun.copies() if folder.stat().st_mtime >= started]
    if made:
        save = str(made[0] / commun.SAVE_NAME)
        mises_a_jour.remember(sauvegarde=save, nouvelle_partie=False)
        return {'sauvegarde': save, 'libelle': commun.save_label(save)}
    return {'sauvegarde': None}

def cmd_copie_arreter(_):
    COPY.request_stop()
    return {}

def check_firewall():
    import pare_feu
    time.sleep(6)
    if pare_feu.check():
        BUS.send('pare_feu', bloque=True)

def cmd_pare_feu_regler(_):
    import pare_feu
    return {'regle': bool(pare_feu.fix())}

def adb_path() -> str | None:
    chosen = setting('adb')
    return chosen if chosen and os.path.isfile(chosen) else copie_android.find_adb()

def phone(need_game: bool=True) -> tuple[str, str]:
    try:
        return em.find_phone(need_game, adb_path())
    except em.NoAdb:
        raise Erreur(tr('Il faut les outils Android de Google (10 Mo).'), 'adb_absent', page=copie_android.ADB_PAGE)
    except em.Refus as refus:
        raise Erreur(str(refus), 'pas_de_telephone')

def java_hash(blob: bytes) -> str:
    value = 1
    for byte in blob:
        value = 31 * value + (byte - 256 if byte > 127 else byte) & 4294967295
    return f'{value:x}'

def own_signature() -> str | None:
    if not KEY.is_file():
        return None
    try:
        from cryptography.hazmat.primitives.serialization import Encoding, pkcs12
        _, cert, _ = pkcs12.load_key_and_certificates(KEY.read_bytes(), None)
        return java_hash(cert.public_bytes(Encoding.DER))
    except Exception:
        return None

class Phones:

    def __init__(self):
        self.lock = threading.Lock()
        self.known = {}
        self.version_read = {}
        self.shown_lock = threading.Lock()
        self.shown = None
        self.failure = None

    @staticmethod
    def details(adb: str, serial: str, state: str, model: str) -> dict:
        found = {'serie': serial, 'etat': state, 'modele': model or serial, 'emulateur': serial.startswith('emulator-'), 'jeu': False, 'version': None, 'signature': None, 'origine': None}
        if state != 'device':
            return found
        try:
            signature = mises_a_jour.phone_signature(adb, serial)
        except ADB_ERRORS:
            signature = None
        if signature:
            origin = 'officiel' if signature == copie_android.OFFICIAL_SIGNATURE else 'cet_ordinateur' if signature == own_signature() else 'autre'
            found.update(jeu=True, signature=signature, origine=origin)
            if origin != 'officiel':
                try:
                    found['version'] = mises_a_jour.phone_game_version(adb, serial)
                except ADB_ERRORS:
                    pass
        return found

    def read(self, fresh: bool=False) -> dict:
        adb = adb_path()
        if not adb:
            return {'adb': None, 'telephones': []}
        try:
            listed = copie_android.phones(adb)
        except ADB_ERRORS:
            listed = []
        with self.lock:
            if fresh:
                self.known = {}
            phones = []
            for serial, state, model in listed:
                key = (serial, state)
                if key in self.known:
                    self.known[key] = self.fresh_version(adb, self.known[key])
                else:
                    self.known[key] = self.details(adb, serial, state, model)
                    self.version_read[serial] = time.monotonic()
                phones.append(self.known[key])
            current = {(serial, state) for serial, state, _ in listed}
            self.known = {key: found for key, found in self.known.items() if key in current}
        phones.sort(key=lambda p: (p['emulateur'], p['etat'] != 'device'))
        return {'adb': adb, 'telephones': phones}

    def fresh_version(self, adb: str, phone: dict) -> dict:
        if phone['etat'] != 'device' or not phone['jeu'] or phone['origine'] == 'officiel':
            return phone
        now = time.monotonic()
        if now - self.version_read.get(phone['serie'], 0) < VERSION_EVERY:
            return phone
        self.version_read[phone['serie']] = now
        try:
            version = mises_a_jour.phone_game_version(adb, phone['serie'])
        except ADB_ERRORS:
            return phone
        return phone if version == phone['version'] else {**phone, 'version': version}

    def show(self, found: dict, always: bool=False) -> None:
        with self.shown_lock:
            if always or found != self.shown:
                self.shown = found
                BUS.send('telephones', **found)

    def watch(self) -> None:
        while True:
            if BUS.listening() and WORK.name not in PHONE_TASKS:
                try:
                    self.show(self.read())
                except Exception:
                    failure = traceback.format_exc()
                    if failure != self.failure:
                        self.failure = failure
                        print(failure)
            time.sleep(PHONES_EVERY)

    def forget(self) -> None:
        with self.lock:
            self.known = {}
PHONES = Phones()

def cmd_telephones(body):
    found = PHONES.read(fresh=bool(body.get('rafraichir')))
    PHONES.show(found, always=True)
    return found

def cmd_adb_telecharger(_):

    def work():
        adb = copie_android.download_adb()
        PHONES.forget()
        return {'adb': adb}
    WORK.start('adb', work)
    return {}

def cmd_installer(body):
    apk = existing(body.get('apk'))
    adb, serial = phone(need_game=False)
    replace = body.get('remplacer')
    if replace is None:
        signature = mises_a_jour.phone_signature(adb, serial)
        if signature and signature != copie_android.OFFICIAL_SIGNATURE:
            raise Erreur(tr('Le jeu hors ligne est déjà sur le téléphone.'), 'question_remplacer')

    def work():
        print(tr('Installation sur le téléphone...'))
        bar(0, 0, 0, tr('Installation'))
        copie_android.install(adb, serial, apk, sending(tr('Installation')))
        kept = None
        if replace:
            kept = mises_a_jour.phone_save(adb, serial, str(copies_folder()))
            mises_a_jour.apply_apk_save(adb, serial, apk)
            print(tr("La sauvegarde de l'APK remplace celle du téléphone."))
        return installed(adb, serial, kept)
    WORK.start('installation', work)
    return {}

def installed(adb: str, serial: str, kept) -> dict:
    PHONES.forget()
    model = next((m for p, _, m in copie_android.phones(adb) if p == serial and m), tr('le téléphone'))
    print(tr('Le jeu est installé sur {model}.', model=model))
    return {'modele': model, 'gardee': kept}

def cmd_reinstaller(body):
    apk = existing(body.get('apk'))
    adb, serial = phone(need_game=False)

    def work():
        bar(0, 0, 0, tr('Installation'))
        copy = mises_a_jour.phone_save(adb, serial, str(copies_folder()))
        if copy:
            print(tr('Sauvegarde du téléphone copiée : {copy}', copy=copy))
        print(tr('Désinstallation, puis installation...'))
        mises_a_jour.reinstall(adb, serial, apk, sending(tr('Installation')))
        return installed(adb, serial, copy)
    WORK.start(body.get('tache') or 'installation', work)
    return {}

def copies_folder() -> Path:
    commun.COPIES.mkdir(parents=True, exist_ok=True)
    return commun.COPIES

def work_folder(out: str) -> str:
    chosen = setting('dossier_travail')
    place = chosen if chosen and os.path.isdir(chosen) else os.path.dirname(os.path.abspath(out))
    return tempfile.mkdtemp(prefix='rr_patch_', dir=place)

def build_choices(body) -> tuple[str, str | None, bool, str | None]:
    official = (body.get('jeu') or '').strip()
    save = (body.get('sauvegarde') or '').strip() or None
    new_game = bool(body.get('nouvelle'))
    artworks = (body.get('images') or '').strip() or None
    if not official or not os.path.isfile(official):
        raise Erreur(tr('Il faut choisir le fichier du jeu officiel 1.10.4 (.xapk, .apkm ou .apk).'), 'jeu')
    if artworks and (not os.path.isdir(artworks)):
        raise Erreur(tr("Le dossier d'images de la galerie n'existe pas."), 'images')
    if new_game:
        save = None
    elif not save:
        raise Erreur(tr('Il faut choisir une sauvegarde, ou « Nouvelle partie ».'), 'sauvegarde')
    elif not commun.is_save(save):
        raise Erreur(tr("Ce fichier n'est pas une sauvegarde Ranger Rumble."), 'sauvegarde')
    return (official, save, new_game, artworks)

def cmd_fabriquer(body):
    import patcher
    official, save, new_game, artworks = build_choices(body)
    out = (body.get('sortie') or '').strip()
    if not out:
        raise Erreur(tr("Il faut choisir où créer l'APK."), 'sortie')
    mises_a_jour.remember(official=official, output=out, artworks=artworks or '', sauvegarde=save or '', nouvelle_partie=new_game)

    def work():
        bar(0, 0, 0, tr('Fabrication'), 0)
        patcher.build(official, out, save=save, new_game=new_game, artworks=artworks, work=work_folder(out))
        print(tr("L'APK est prêt."))
        return {'apk': out}
    WORK.start('fabrication', work)
    return {}

def cmd_ordinateur_etat(_):
    return jeu_mac.state()

def cmd_ordinateur_preparer(body):
    official, save, new_game, artworks = build_choices(body)
    if jeu_mac.coming_soon():
        raise Erreur(jeu_mac.missing())
    if not jeu_mac.supported():
        raise Erreur(tr('Il faut un Mac avec une puce Apple (M1 ou plus récent).'))
    if jeu_mac.running_pid():
        raise Erreur(tr("Il faut d'abord fermer le jeu."))
    mises_a_jour.remember(official=official, artworks=artworks or '', sauvegarde=save or '', nouvelle_partie=new_game)
    out = str(jeu_mac.APK)
    game = mises_a_jour.current().get('jeu') or ''

    def work():
        jeu_mac.BASE.mkdir(parents=True, exist_ok=True)
        bar(0, 0, 0, tr('Préparation pour Mac'), 0)
        return jeu_mac.prepare(official, save, new_game, artworks, work_folder(out), game, fraction_bar(LAST_STEP))
    WORK.start('ordinateur', work)
    return {}

def cmd_ordinateur_jouer(_):

    def ended(code):
        BUS.send('ordinateur', etat='arret', erreur=jeu_mac.end_text(code))
    try:
        state = jeu_mac.play(ended)
    except jeu_mac.Probleme as problem:
        raise Erreur(str(problem))
    BUS.send('ordinateur', etat='en_cours')
    return state

def cmd_ordinateur_arreter(_):
    return jeu_mac.stop()

def cmd_ordinateur_touches(body):
    try:
        return {'touches': jeu_mac.set_keys(None if body.get('defaut') else body.get('touches'))}
    except jeu_mac.Probleme as problem:
        raise Erreur(str(problem))
RELEASE = {}

def check_release() -> dict:
    info = mises_a_jour.current()
    try:
        release = mises_a_jour.latest_release()
    except Exception:
        event = {'etat': 'impossible'}
    else:
        if release and mises_a_jour.newer(release['version'], info['version']):
            RELEASE.update(release)
            game = release.get('jeu')
            event = {'etat': 'nouvelle', 'version': release['version'], 'jeu': game, 'notes': release['notes'], 'page': release['page'], 'jeu_plus_recent': bool(game and mises_a_jour.newer(game, info.get('jeu') or '0'))}
        else:
            event = {'etat': 'a_jour', 'version': release['version'] if release else None}
    event['verifie'] = datetime.datetime.now().strftime('%H:%M')
    BUS.send('maj', **event)
    return event

def cmd_maj_verifier(_):
    return check_release()

def cmd_maj_outil(_):
    if not RELEASE:
        raise Erreur(tr('Aucune mise à jour à installer.'))
    release = dict(RELEASE)

    def work():
        mises_a_jour.update_tool(release, str(commun.ROOT), progress=fraction_bar())
        return {'version': release['version']}
    WORK.start('maj_outil', work)
    return {}

def cmd_maj_telephone(body):
    import patcher
    official = setting('official')
    if not (official and os.path.isfile(official)):
        raise Erreur(tr("Il faut d'abord choisir le jeu officiel 1.10.4 (Réglages > Jeu et fichiers)."), 'jeu')
    adb, serial = phone()
    signature = mises_a_jour.phone_signature(adb, serial)
    if signature == copie_android.OFFICIAL_SIGNATURE:
        raise Erreur(tr("Le téléphone a le jeu officiel : il faut d'abord installer le jeu hors ligne."), 'officiel')
    game = mises_a_jour.current().get('jeu')
    on_phone = mises_a_jour.phone_game_version(adb, serial)
    if on_phone and game and (not mises_a_jour.newer(game, on_phone)) and (not body.get('forcer')):
        raise Erreur(tr('Le jeu du téléphone est déjà à jour ({version}).', version=on_phone), 'deja_a_jour', version=on_phone)
    out = setting('output') or str(commun.DEFAULT_APK)
    artworks = setting('artworks') or None
    exported = setting('sauvegarde')

    def work():
        bar(0, 0, 0, tr('Fabrication'), 0)
        save = mises_a_jour.phone_save(adb, serial, str(copies_folder()))
        if save:
            print(tr('Sauvegarde du téléphone lue.'))
        elif exported and commun.is_save(exported):
            print(tr("Sauvegarde du téléphone illisible : la sauvegarde choisie pour l'APK sera utilisée."))
            save = exported
        else:
            raise SystemExit(tr("La sauvegarde du téléphone n'a pas pu être lue."))
        patcher.build(official, out, save=save, artworks=artworks if artworks and os.path.isdir(artworks) else None, work=work_folder(out))
        print(tr('Installation sur le téléphone...'))
        bar(0, 0, 0, tr('Installation'))
        try:
            copie_android.install(adb, serial, out, sending(tr('Installation')))
        except copie_android.OtherSignature as problem:
            raise Erreur(str(problem), 'autre_signature', apk=out)
        print(tr('Le jeu du téléphone est à jour.'))
        return installed(adb, serial, None) | {'apk': out}
    WORK.start('maj_telephone', work)
    return {}

class Editing:

    def __init__(self):
        self.lock = threading.Lock()
        self.model = em.Model()
EDIT = Editing()

def plain(value):
    if isinstance(value, bytes):
        return value.hex()
    if isinstance(value, dict):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    return value

def editor_state() -> dict:
    model = EDIT.model
    if model.save is None:
        return {'ouvert': False}
    return {'ouvert': True, 'source': model.source, 'changements': model.changes(), 'resume': model.summary()}

def opened() -> em.Model:
    if EDIT.model.save is None:
        raise Erreur(tr('Aucune sauvegarde ouverte.'))
    return EDIT.model

def list_changed() -> Erreur:
    return Erreur(tr('La liste a changé : il faut recommencer.'), 'liste')

def editor_source(body) -> tuple[bytes, str]:
    source, path = (body.get('source'), body.get('chemin'))
    if source == 'fichier':
        return (Path(existing(path)).read_bytes(), path)
    if source == 'copie':
        path = existing(path)
        save = Path(path) / commun.SAVE_NAME if os.path.isdir(path) else Path(path)
        if not save.is_file():
            raise Erreur(tr("Cette copie n'a pas de sauvegarde (save.msgpack)."))
        return (save.read_bytes(), str(save))
    if source == 'nouvelle':
        return (copie_android.pack(copie_android.new_save()), tr('partie vierge'))
    if source == 'telephone':
        adb, serial = phone()
        try:
            local = em.pull_phone_save(adb, serial, copies_folder())
        except em.Refus as refus:
            raise Erreur(str(refus))
        return (local.read_bytes(), tr('téléphone (copie gardée dans {name})', name=local.name))
    raise Erreur(tr('Source inconnue.'))

def cmd_ed_ouvrir(body):
    raw, label = editor_source(body)
    with EDIT.lock:
        if EDIT.model.save is not None and EDIT.model.changes() and (not body.get('oublier')):
            raise Erreur(tr('Des changements ne sont pas enregistrés.'), 'changements')
        fresh = em.Model()
        try:
            fresh.load(raw, label)
        except ValueError as error:
            raise Erreur(str(error))
        EDIT.model = fresh
        return editor_state()

def cmd_ed_etat(_):
    with EDIT.lock:
        return editor_state()

def row_json(row: em.Row, columns: list) -> dict:
    values = {key: plain(row.get(key)) for key, _, _, _ in columns}
    return {'valeurs': values, 'icone': row.get('icon'), 'possede': row.get('owned'), 'modifiable': {key: row.editable(key) for key, _, _, kind in columns if kind}, 'bornes': {key: list(row.bounds(key)) for key, _, _, kind in columns if kind == 'int'}}

def cmd_ed_lignes(body):
    tab = body.get('onglet')
    if tab not in em.TABS:
        raise Erreur(tr('Onglet inconnu.'))
    with EDIT.lock:
        model = opened()
        columns = em.columns(tab)
        return {'colonnes': [{'cle': key, 'titre': title, 'type': kind} for key, title, _, kind in columns], 'lignes': [row_json(row, columns) for row in model.rows(tab)]}

def out_of_range(low: int, high: int) -> Erreur:
    return Erreur(tr('Il faut un nombre de {low} à {high}.', low=low, high=high))

def row_value(row: em.Row, key: str, kind: str, value):
    if kind == 'bool':
        return bool(value)
    if isinstance(row.get(key), str):
        return str(value)
    low, high = row.bounds(key)
    try:
        value = int(value)
    except (TypeError, ValueError):
        raise Erreur(tr('Il faut un nombre.')) from None
    if not low <= value <= high:
        raise out_of_range(low, high)
    return value

def cmd_ed_changer(body):
    tab, index, key = (body.get('onglet'), body.get('ligne'), body.get('cle'))
    with EDIT.lock:
        model = opened()
        rows = model.rows(tab)
        if not isinstance(index, int) or not 0 <= index < len(rows) or (body.get('nom') is not None and rows[index].get('name') != body.get('nom')):
            raise list_changed()
        row = rows[index]
        kind = next((k for c, _, _, k in em.columns(tab) if c == key), None)
        if not kind or not row.editable(key):
            raise Erreur(tr('Cette valeur ne peut pas changer.'))
        value = row_value(row, key, kind, body.get('valeur'))
        try:
            row.set(key, value)
        except em.Refus as refus:
            raise Erreur(str(refus), 'refus')
        return editor_state()

def cmd_ed_action(body):
    action, picked = (body.get('action'), body.get('lignes') or [])
    with EDIT.lock:
        model = opened()
        unlock = {'tous_heros': model.all_heroes, 'toutes_armes': model.all_weapons, 'tous_costumes': model.all_skins}.get(action) if isinstance(action, str) else None
        try:
            if unlock:
                unlock()
            elif action in ('max_heros', 'max_armes'):
                heroes = action == 'max_heros'
                rows = model.rows('heros' if heroes else 'armes')
                chosen = [rows[i] for i in picked if isinstance(i, int) and 0 <= i < len(rows)]
                (model.max_heroes if heroes else model.max_weapons)(chosen)
            else:
                raise Erreur(tr('Action inconnue.'))
        except em.Refus as refus:
            raise Erreur(str(refus), 'refus')
        return editor_state()

def node_path(body) -> tuple[em.Model, str, tuple]:
    part, path = (body.get('partie'), body.get('chemin') or [])
    model = opened()
    if part not in model.save.values:
        raise list_changed()
    try:
        model.value_at(part, path)
    except (KeyError, IndexError, TypeError):
        raise list_changed() from None
    return (model, part, tuple(path))

def cmd_ed_arbre(body):
    with EDIT.lock:
        model = opened()
        if not body.get('partie'):
            nodes = model.roots()
        else:
            model, part, path = node_path(body)
            nodes = model.children(part, path, body.get('type') or '?')
        for node in nodes:
            node['path'] = plain(node['path'])
            what, _ = sv.describe(node['kind'])
            value = model.value_at(node['part'], node['path'])
            node['modifiable'] = bool(node['path']) and what not in ('object', 'list', 'map') and (not isinstance(value, (list, dict)))
        return {'noeuds': nodes}

def node_value(old, kind: str, new):
    what, detail = sv.describe(kind)
    try:
        if what == 'bool' or isinstance(old, bool):
            return bool(new)
        if what == 'string' or isinstance(old, str):
            return str(new)
        if what == 'bytes':
            return bytes.fromhex(str(new))
        if what == 'float' or isinstance(old, float):
            single = isinstance(old, sv.F32) or detail in sv.SINGLE_FLOATS
            return sv.F32(float(new)) if single else float(new)
        new = int(new)
    except (TypeError, ValueError):
        raise Erreur(tr('Valeur refusée.')) from None
    low, high = detail if what == 'int' else (-2 ** 63, 2 ** 64 - 1)
    if not low <= new <= high:
        raise out_of_range(low, high)
    return new

def cmd_ed_noeud_changer(body):
    with EDIT.lock:
        model, part, path = node_path(body)
        if not path:
            raise Erreur(tr('Cette valeur ne peut pas changer.'))
        new = node_value(model.value_at(part, path), body.get('type') or '?', body.get('valeur'))
        model.set_at(part, path, new)
        return editor_state()

def cmd_ed_enregistrer(body):
    path = (body.get('chemin') or '').strip()
    if not path:
        raise Erreur(tr('Il faut choisir où enregistrer.'))
    with EDIT.lock:
        model = opened()
        try:
            model.save.write(path)
        except Exception as error:
            raise Erreur(tr('Enregistrement impossible :\n\n{error}', error=error))
        model.mark_saved(path)
        if body.get('pour_apk'):
            mises_a_jour.remember(sauvegarde=path, nouvelle_partie=False)
        return editor_state() | {'chemin': path}

def cmd_ed_envoyer(_):
    adb, serial = phone()
    with EDIT.lock:
        model = opened()
        try:
            local = em.push_save(adb, serial, model.save.to_bytes(), copies_folder())
        except em.Refus as refus:
            raise Erreur(str(refus))
        model.mark_saved(str(local))
        return editor_state()

def cmd_ed_annuler(_):
    with EDIT.lock:
        opened().revert()
        return editor_state()

def cmd_cle_info(_):
    found = {'chemin': str(KEY), 'existe': KEY.is_file(), 'signature': own_signature(), 'date': None}
    if KEY.is_file():
        found['date'] = file_day(KEY)
    return found

def cmd_cle_exporter(body):
    target = (body.get('chemin') or '').strip()
    if not KEY.is_file():
        raise Erreur(tr("Aucune clé sur cet ordinateur pour l'instant."))
    if not target:
        raise Erreur(tr('Il faut choisir où enregistrer.'))
    shutil.copy2(KEY, target)
    return {'chemin': target}

def cmd_cle_importer(body):
    source = existing(body.get('chemin'))
    try:
        from cryptography.hazmat.primitives.serialization import pkcs12
        key, cert, _ = pkcs12.load_key_and_certificates(Path(source).read_bytes(), None)
    except Exception:
        key = cert = None
    if key is None or cert is None:
        raise Erreur(tr("Ce fichier n'est pas une clé de l'outil (cle_apk.p12)."))
    if KEY.is_file():
        put_aside(KEY, 'cle_apk', '.p12.ancienne')
    commun.BASE.mkdir(exist_ok=True)
    shutil.copy2(source, KEY)
    PHONES.forget()
    return cmd_cle_info({})

def cmd_certificat_info(_):
    authority = CERTIFICATE / 'mitmproxy-ca-cert.pem'
    return {'dossier': str(CERTIFICATE), 'existe': authority.is_file() or (CERTIFICATE / 'dns-copie.pem').is_file(), 'date': file_day(authority) if authority.is_file() else None}

def cmd_certificat_recreer(_):
    if WORK.name == 'copie':
        raise Erreur(tr("Il faut d'abord arrêter la copie."), 'occupe')
    if CERTIFICATE.exists():
        put_aside(CERTIFICATE, 'certificat', '.ancien')
    return cmd_certificat_info({})

def size_of(folder: str) -> int:
    total = 0
    for base, _, files in os.walk(folder):
        for name in files:
            try:
                total += os.path.getsize(os.path.join(base, name))
            except OSError:
                pass
    return total

def leftovers() -> list[str]:
    chosen = settings()
    output = chosen.get('output') or str(commun.DEFAULT_APK)
    places = [tempfile.gettempdir(), os.path.dirname(os.path.abspath(output)), str(jeu_mac.BASE)]
    if chosen.get('dossier_travail'):
        places.append(chosen['dossier_travail'])
    found = []
    for place in dict.fromkeys(places):
        try:
            names = os.listdir(place) if os.path.isdir(place) else []
        except OSError:
            continue
        found += [os.path.join(place, name) for name in names if name.startswith(('rr_patch_', 'rr_maj_')) and os.path.isdir(os.path.join(place, name))]
    return found

def cmd_temporaires(_):
    if WORK.name in WORK_FOLDER_TASKS:
        return {'dossiers': [], 'taille': 0}
    found = leftovers()
    return {'dossiers': found, 'taille': sum((size_of(path) for path in found))}

def to_trash(path: str) -> None:
    if sys.platform != 'darwin':
        shutil.rmtree(path, ignore_errors=True)
        return
    trash = Path.home() / '.Trash'
    target, number = (trash / Path(path).name, 2)
    while target.exists():
        target, number = (trash / f'{Path(path).name} {number}', number + 1)
    shutil.move(path, target)

def cmd_nettoyer(_):
    refuse_while_building()
    found = leftovers()
    freed = sum((size_of(path) for path in found))
    for path in found:
        to_trash(path)
    return {'liberes': freed, 'dossiers': len(found)}

def text_of(path: Path) -> str | None:
    return path.read_text().strip() if path.is_file() else None

def path_if_file(path: Path) -> str | None:
    return str(path) if path.is_file() else None

def cmd_composants(_):
    expected, mark = (text_of(READY_EXPECTED), text_of(READY_MARK))
    return {'python': sys.version.split()[0], 'chemin': sys.executable, 'pret': mark, 'attendu': expected, 'ok': mark is not None and (expected is None or mark == expected), 'pip_log': path_if_file(commun.BASE / 'pip.log'), 'erreur_log': path_if_file(commun.BASE / 'erreur.log')}

def cmd_composants_reparer(_):
    if READY_MARK.is_file():
        READY_MARK.unlink()
    return {}

def start_folder(start: str) -> str | None:
    if not start:
        return None
    return start if os.path.isdir(start) else os.path.dirname(start)

def ask_path_mac(kind: str, title: str, start: str, name: str) -> str | None:
    what = {'dossier': 'choose folder', 'enregistrer': 'choose file name', 'fichier': 'choose file'}[kind]
    script = f'POSIX path of ({what} with prompt {json.dumps(title)}'
    if kind == 'enregistrer' and name:
        script += f' default name {json.dumps(name)}'
    folder = start_folder(start)
    if folder and os.path.isdir(folder):
        script += f' default location (POSIX file {json.dumps(folder)})'
    done = subprocess.run(['osascript', '-e', script + ')'], capture_output=True, text=True)
    return done.stdout.strip() or None

def ask_path_tk(kind: str, title: str, types, start: str, name: str) -> str | None:
    found = {}

    def window():
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        patterns = ' '.join((f'*.{t}' for t in types))
        filetypes = [(patterns, patterns), ('*', '*')] if types else [('*', '*')]
        options = {'title': title, 'initialdir': start_folder(start) or None, 'parent': root}
        if kind == 'dossier':
            found['chemin'] = filedialog.askdirectory(**options)
        elif kind == 'enregistrer':
            found['chemin'] = filedialog.asksaveasfilename(initialfile=name, filetypes=filetypes, defaultextension=f'.{types[0]}' if types else '', **options)
        else:
            found['chemin'] = filedialog.askopenfilename(filetypes=filetypes, **options)
        root.destroy()
    thread = threading.Thread(target=window)
    thread.start()
    thread.join()
    return found.get('chemin') or None

def ask_path(kind: str, title: str, types=(), start: str='', name: str='') -> str | None:
    if sys.platform == 'darwin':
        return ask_path_mac(kind, title, start, name)
    return ask_path_tk(kind, title, types, start, name)

def window_choose(body) -> dict:
    kind = 'enregistrer' if body.get('type') == 'enregistrer' else 'dossier' if body.get('dossier') else 'fichier'
    title = {'enregistrer': tr('Enregistrer'), 'dossier': tr('Choisir un dossier')}.get(kind, tr('Choisir un fichier'))
    return {'valeur': ask_path(kind, title, body.get('types') or (), body.get('depart') or '', body.get('nom') or '')}

def window_show(body) -> dict:
    path = body.get('chemin') or ''
    if body.get('type') == 'ouvrir' and path and (not os.path.exists(path)):
        os.makedirs(path, exist_ok=True)
    commun.open_folder(existing(path), reveal=body.get('type') == 'montrer')
    return {'valeur': True}

def window_link(body) -> dict:
    if str(body.get('url', '')).startswith('https://'):
        import webbrowser
        webbrowser.open(body['url'])
    return {'valeur': True}

def window_restart(_) -> dict:
    launcher = HERE / 'lanceur_web.py'
    if os.name == 'nt' and launcher.is_file():
        flags = getattr(subprocess, 'DETACHED_PROCESS', 0) | getattr(subprocess, 'CREATE_NEW_PROCESS_GROUP', 0)
        subprocess.Popen([sys.executable, '-I', str(launcher)], creationflags=flags, close_fds=True)
        threading.Timer(1, stop).start()
    return {'valeur': True}
WINDOW_REQUESTS = {'choisir': window_choose, 'enregistrer': window_choose, 'montrer': window_show, 'ouvrir': window_show, 'lien': window_link, 'relancer': window_restart}

def cmd_fenetre(body):
    kind = body.get('type')
    request = WINDOW_REQUESTS.get(kind) if isinstance(kind, str) else None
    if request is None:
        raise Erreur(tr('Demande inconnue.'))
    return request(body)
COMMANDS = {name[4:]: function for name, function in globals().items() if name.startswith('cmd_')}

def stop():
    if COPY.request_stop():
        time.sleep(1)
    WORK.keep_awake(False)
    os._exit(0)

class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    server_version = 'RangerRumble'
    PROBLEMS = (copie_android.Problem, mises_a_jour.Problem)

    def log_message(self, *_):
        pass

    def allowed_host(self) -> bool:
        host = (self.headers.get('Host') or '').lower()
        return host in (f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}')

    def has_key(self, query: dict) -> bool:
        given = self.headers.get('X-Jeton') or (query.get('jeton') or [''])[0]
        return secrets.compare_digest(given.encode(), self.server.key.encode())

    def answer(self, status: int, body: bytes, kind: str='application/json; charset=utf-8', cache: bool=False):
        self.send_response(status)
        self.send_header('Content-Type', kind)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'max-age=3600' if cache else 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(body)

    def answer_json(self, value: dict, status: int=200):
        self.answer(status, json.dumps(value, ensure_ascii=False, default=str).encode())

    def do_GET(self):
        url = urlparse(self.path)
        if not self.allowed_host():
            return self.answer(403, b'{}')
        if url.path == '/api/evenements':
            if not self.has_key(parse_qs(url.query)):
                return self.answer(403, b'{}')
            return self.events()
        if url.path in ('/', '/index.html'):
            return self.file(WEB / 'index.html', WEB)
        if url.path.startswith('/web/'):
            return self.file(WEB / url.path[len('/web/'):], WEB)
        if url.path == '/ressources/langues.json':
            return self.file(PICTURES / 'langues.json', PICTURES)
        for folder in SHOWN_PICTURES:
            if url.path.startswith(f'/ressources/{folder}/'):
                return self.file(PICTURES / url.path[len('/ressources/'):], PICTURES / folder, cache=True)
        return self.answer(404, b'{}')

    def file(self, path: Path, inside: Path, cache: bool=False):
        try:
            parts = path.relative_to(inside).parts
        except ValueError:
            return self.answer(404, b'{}')
        if not parts or any((part in ('..', '.') or ':' in part or '\\' in part for part in parts)) or (not path.is_file()):
            print(f"[fenêtre] fichier refusé : {self.path.split('?')[0]} ({path})")
            return self.answer(404, b'{}')
        kind = FILE_TYPES.get(path.suffix.lower()) or mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
        if kind.startswith('text/') or kind in ('application/javascript', 'application/json'):
            kind += '; charset=utf-8'
        return self.answer(200, path.read_bytes(), kind, cache)

    def events(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.close_connection = True
        listener = BUS.listen()
        try:
            self.wfile.write(b'retry: 1000\n\n')
            self.wfile.flush()
            while True:
                try:
                    event = listener.get(timeout=15)
                    data = json.dumps(event, ensure_ascii=False, default=str)
                    self.wfile.write(f'data: {data}\n\n'.encode())
                except queue.Empty:
                    self.wfile.write(b': ping\n\n')
                self.wfile.flush()
        except OSError:
            pass
        finally:
            BUS.leave(listener)

    def request_body(self) -> dict:
        length = int(self.headers.get('Content-Length') or 0)
        if length < 0:
            raise ValueError(length)
        body = json.loads(self.rfile.read(length) or b'{}') if length else {}
        if not isinstance(body, dict):
            raise ValueError(type(body).__name__)
        return body

    def do_POST(self):
        url = urlparse(self.path)
        if not self.allowed_host() or not self.has_key({}):
            return self.answer(403, b'{}')
        name = url.path[len('/api/'):] if url.path.startswith('/api/') else ''
        command = COMMANDS.get(name)
        if command is None:
            return self.answer_json({'ok': False, 'erreur': tr('Commande inconnue.')}, 404)
        try:
            body = self.request_body()
        except ValueError:
            return self.answer_json({'ok': False, 'erreur': tr('Demande illisible.')}, 400)
        try:
            result = command(body) or {}
            self.answer_json({'ok': True, **result})
        except Erreur as refused:
            self.answer_json({'ok': False, 'erreur': str(refused), 'code': refused.code, **refused.details})
        except self.PROBLEMS as problem:
            self.answer_json({'ok': False, 'erreur': str(problem), 'code': None})
        except Exception as failure:
            print(traceback.format_exc())
            self.answer_json({'ok': False, 'erreur': f'{type(failure).__name__} : {failure}', 'code': 'interne'})

def watch_stdin():
    try:
        while sys.stdin.buffer.read(1024):
            pass
    except (OSError, ValueError):
        pass
    stop()

def watch_window(first: float=90, after: float=10):
    seen, alone = (False, time.monotonic())
    while True:
        time.sleep(1)
        if BUS.listening():
            seen, alone = (True, time.monotonic())
        elif time.monotonic() - alone > (after if seen else first) and WORK.name is None:
            stop()

def new_server(port: int=0, key: str | None=None) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    server.daemon_threads = True
    server.key = key or secrets.token_urlsafe(24)
    return server

def serve(server: ThreadingHTTPServer, ends: str | None) -> None:
    sys.stdout = sys.stderr = Output()
    if ends == 'stdin':
        threading.Thread(target=watch_stdin, daemon=True).start()
    elif ends == 'fenetre':
        threading.Thread(target=watch_window, daemon=True).start()
    threading.Thread(target=PHONES.watch, daemon=True).start()
    if setting('maj_demarrage'):
        threading.Thread(target=check_release, daemon=True).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        stop()

def remove_old_mac_app() -> None:
    old_app = commun.ROOT / 'Ranger Rumble hors ligne.app'
    if sys.platform == 'darwin' and old_app.is_dir() and (commun.ROOT / 'Launcher Ratchet Ranger Rumble.app').is_dir():
        try:
            to_trash(str(old_app))
        except OSError:
            pass

def main():
    parser = argparse.ArgumentParser(description="The launcher's engine, over HTTP on 127.0.0.1.")
    parser.add_argument('--port', type=int, default=0)
    parser.add_argument('--jeton')
    parser.add_argument('--garder', action='store_true', help="ne pas s'arrêter quand l'entrée standard se ferme")
    args = parser.parse_args()
    remove_old_mac_app()
    server = new_server(args.port, args.jeton)
    sys.stdout.write(json.dumps({'port': server.server_port, 'jeton': server.key}) + '\n')
    sys.stdout.flush()
    serve(server, None if args.garder else 'stdin')
if __name__ == '__main__':
    main()
