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
KEY = commun.BASE / 'cle_apk.p12'
CERTIFICATE = commun.BASE / 'certificat'
READY_MARK = commun.BASE / 'venv' / 'rr-pret'
READY_EXPECTED = HERE.parent / 'pret.txt'
DEFAULTS = {'langue': langues.CURRENT, 'maj_demarrage': True, 'page_depart': 'accueil', 'derniere_page': 'android', 'son_fin': True, 'anti_veille': True, 'theme': 'sombre', 'animations': 'completes', 'accent': 'or', 'adb': '', 'dossier_travail': '', 'official': '', 'output': str(commun.DEFAULT_APK), 'artworks': '', 'sauvegarde': '', 'nouvelle_partie': False, 'dossier_sauvegardes': ''}
CHOICES = {'page_depart': ('accueil', 'derniere'), 'theme': ('auto', 'sombre', 'clair'), 'animations': ('completes', 'reduites', 'aucune'), 'accent': ('or', 'bleu', 'vert', 'violet'), 'langue': tuple(dict(langues.LANGUAGES))}
FLAGS = ('maj_demarrage', 'son_fin', 'anti_veille', 'nouvelle_partie')

class Erreur(Exception):

    def __init__(self, message, code=None, **details):
        super().__init__(message)
        self.code, self.details = (code, details)

class Bus:
    STICKY = ('copie', 'copie_qr', 'telephones', 'maj', 'tache', 'barre')

    def __init__(self):
        self.lock = threading.Lock()
        self.listeners = []
        self.lines = collections.deque(maxlen=3000)
        self.last = {}

    def send(self, kind, **data):
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

    def listen(self):
        listener = queue.Queue()
        with self.lock:
            for event in self.last.values():
                listener.put(event)
            self.listeners.append(listener)
        return listener

    def leave(self, listener):
        with self.lock:
            if listener in self.listeners:
                self.listeners.remove(listener)

    def listening(self):
        with self.lock:
            return bool(self.listeners)
BUS = Bus()

class Output(io.TextIOBase):
    encoding = 'utf-8'

    def __init__(self):
        super().__init__()
        self.lock = threading.Lock()
        self.pending = ''

    def writable(self):
        return True

    def write(self, text):
        with self.lock:
            self.pending += text
            *lines, self.pending = self.pending.split('\n')
        for line in lines:
            self.line(line)
        return len(text)

    def flush(self):
        with self.lock:
            line, self.pending = (self.pending, '')
        if line:
            self.line(line)

    @staticmethod
    def line(text):
        step = commun.STEP.match(text.strip())
        if step and WORK.name in ('fabrication', 'maj_telephone', 'ordinateur'):
            number = int(step.group(1))
            what = tr('Préparation pour Mac') if WORK.name == 'ordinateur' else tr('Fabrication')
            if number in commun.BUILD_STEPS:
                start, goal, seconds = commun.BUILD_STEPS[number]
                bar(start, goal, seconds / 2, what, number)
            elif number == 6:
                bar(100, 100, 0, what, 6)
        BUS.send('journal', texte=text, tache=WORK.name)

def bar(start, goal, seconds, what, step=None):
    BUS.send('barre', tache=WORK.name, debut=start, but=goal, secondes=seconds, texte=what, etape=step)

def sending(what):

    def progress(fraction):
        if fraction >= 0.8:
            bar(80, 99, 8, what)
        else:
            bar(fraction * 100, fraction * 100, 0, what)
    return progress

class Work:

    def __init__(self):
        self.lock = threading.Lock()
        self.name = None
        self.awake = None

    def start(self, name, function, *args):
        with self.lock:
            if self.name:
                raise Erreur(tr('Une tâche est déjà en cours : {name}.', name=task_name(self.name)), 'occupe')
            self.name = name
        BUS.send('tache', nom=name, etat='debut')
        self.keep_awake(True)
        threading.Thread(target=self.run, args=(name, function, args), daemon=True).start()

    def run(self, name, function, args):
        result, error, code, details = (None, None, None, {})
        windows_awake = os.name == 'nt' and setting('anti_veille')
        if windows_awake:
            import ctypes
            ctypes.windll.kernel32.SetThreadExecutionState(2147483649)
        try:
            result = function(*args)
        except copie_android.OtherSignature as problem:
            error, code = (str(problem), 'autre_signature')
        except (copie_android.Problem, mises_a_jour.Problem, em.Refus, jeu_mac.Probleme) as problem:
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
                ctypes.windll.kernel32.SetThreadExecutionState(2147483648)
            with self.lock:
                self.name = None
        if error:
            print(tr('Échec : {error}', error=error))
        BUS.send('tache', nom=name, etat='fin', ok=error is None, erreur=error, code=code, resultat=result, **details)

    def keep_awake(self, on):
        if self.awake is not None:
            self.awake.terminate()
            self.awake = None
        if on and setting('anti_veille') and (sys.platform == 'darwin') and shutil.which('caffeinate'):
            self.awake = subprocess.Popen(['caffeinate', '-i', '-w', str(os.getpid())])
WORK = Work()

def task_name(name):
    return {'copie': tr('Copie de la sauvegarde'), 'fabrication': tr('Fabrication'), 'installation': tr('Installation'), 'maj_telephone': tr('Mise à jour du téléphone'), 'maj_outil': tr("Mise à jour de l'outil"), 'adb': tr('Outils Android'), 'ordinateur': tr('Préparation pour Mac')}.get(name, name)

def settings():
    stored = mises_a_jour.settings()
    return {**DEFAULTS, **{k: v for k, v in stored.items() if v is not None}}

def setting(key):
    return settings().get(key)

def cmd_reglages_lire(_):
    return {'reglages': settings()}

def cmd_reglages_ecrire(body):
    values = {}
    for key, value in body.items():
        if key not in DEFAULTS:
            raise Erreur(tr('Réglage inconnu : {key}', key=key))
        if key in FLAGS:
            value = bool(value)
        elif key in CHOICES and value not in CHOICES[key]:
            raise Erreur(tr('Valeur refusée pour {key}.', key=key))
        elif not isinstance(value, str):
            raise Erreur(tr('Valeur refusée pour {key}.', key=key))
        values[key] = value
    if 'langue' in values:
        if WORK.name:
            raise Erreur(tr('Il faut attendre la fin de la tâche en cours.'), 'occupe')
        langues.CURRENT = values['langue']
    mises_a_jour.remember(**values)
    return {'reglages': settings()}

def cmd_reinitialiser(_):
    path = Path(mises_a_jour.SETTINGS)
    if path.exists():
        path.rename(path.with_name(f'reglages_{datetime.datetime.now():%Y-%m-%d_%H%M%S}.ancien.json'))
    mises_a_jour.remember(langue=langues.CURRENT)
    return {'reglages': settings()}

def cmd_bonjour(_):
    info = mises_a_jour.current()
    return {'version': info['version'], 'jeu': info.get('jeu') or info['version'], 'depot': info.get('depot'), 'langue': langues.CURRENT, 'langues': [list(item) for item in langues.LANGUAGES], 'reglages': settings(), 'racine': str(commun.ROOT), 'moteur': str(HERE), 'ressources': str(PICTURES), 'copies': str(commun.COPIES), 'base': str(commun.BASE), 'systeme': sys.platform, 'tache': WORK.name}

def existing(path):
    if not path or not os.path.exists(path):
        raise Erreur(tr('Introuvable : {path}', path=path or '?'))
    return path

def cmd_ouvrir(body):
    commun.open_folder(existing(body.get('chemin')), reveal=bool(body.get('montrer')))
    return {}

def free_space(path):
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

def cmd_verifier_sauvegarde(body):
    return {'valide': commun.is_save(existing(body.get('chemin')))}

def cmd_verifier_jeu(body):
    path = existing(body.get('chemin'))
    ok = os.path.isfile(path) and path.lower().endswith(('.xapk', '.apkm', '.apk'))
    return {'valide': ok, 'taille': os.path.getsize(path) if os.path.isfile(path) else 0}

def cmd_journal(_):
    with BUS.lock:
        return {'lignes': list(BUS.lines)}

class Copy:

    def __init__(self):
        self.state = None
        self.stop_asked = False
COPY = Copy()

def qr_svg(url):
    try:
        import segno
        return segno.make(url, error='m').svg_inline(scale=8, border=2, dark='#0a1022', light='#ffffff')
    except Exception:
        return None

def cmd_copie_demarrer(_):
    COPY.state, COPY.stop_asked = ('depart', False)
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
        COPY.state = (asyncio.get_running_loop(), master)
        if COPY.stop_asked:
            master.shutdown()
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
        COPY.state = None
        BUS.send('copie_qr', url=None, svg=None)
        print(tr("Copie arrêtée. Il faut supprimer le profil RatchetRR de l'iPhone (Réglages > Général > VPN et gestion de l'appareil)."))
        BUS.send('copie', etat='arret', fini='fini' in reached)
    made = [folder for folder in commun.copies() if folder.stat().st_mtime >= started]
    if made:
        save = str(made[0] / 'save.msgpack')
        mises_a_jour.remember(sauvegarde=save, nouvelle_partie=False)
        return {'sauvegarde': save, 'libelle': commun.save_label(save)}
    return {'sauvegarde': None}

def cmd_copie_arreter(_):
    if isinstance(COPY.state, tuple):
        loop, master = COPY.state
        loop.call_soon_threadsafe(master.shutdown)
    elif COPY.state == 'depart':
        COPY.stop_asked = True
    return {}

def check_firewall():
    import pare_feu
    time.sleep(6)
    if pare_feu.check():
        BUS.send('pare_feu', bloque=True)

def cmd_pare_feu_regler(_):
    import pare_feu
    return {'regle': bool(pare_feu.fix())}

def adb_path():
    chosen = setting('adb')
    return chosen if chosen and os.path.isfile(chosen) else copie_android.find_adb()

def phone(need_game=True):
    try:
        return em.find_phone(need_game, adb_path())
    except em.NoAdb:
        raise Erreur(tr('Il faut les outils Android de Google (10 Mo).'), 'adb_absent', page=copie_android.ADB_PAGE)
    except em.Refus as refus:
        raise Erreur(str(refus), 'pas_de_telephone')

def java_hash(blob):
    value = 1
    for byte in blob:
        value = 31 * value + (byte - 256 if byte > 127 else byte) & 4294967295
    return f'{value:x}'

def own_signature():
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
        self.shown = None

    def details(self, adb, serial, state, model):
        found = {'serie': serial, 'etat': state, 'modele': model or serial, 'emulateur': serial.startswith('emulator-'), 'jeu': False, 'version': None, 'signature': None, 'origine': None}
        if state != 'device':
            return found
        try:
            signature = mises_a_jour.phone_signature(adb, serial)
        except Exception:
            signature = None
        if signature:
            own = own_signature()
            found.update(jeu=True, signature=signature, origine='officiel' if signature == copie_android.OFFICIAL_SIGNATURE else 'cet_ordinateur' if signature == own else 'autre')
            if found['origine'] != 'officiel':
                try:
                    found['version'] = mises_a_jour.phone_game_version(adb, serial)
                except Exception:
                    pass
        return found

    def read(self, fresh=False):
        adb = adb_path()
        if not adb:
            return {'adb': None, 'telephones': []}
        try:
            listed = copie_android.phones(adb)
        except Exception:
            listed = []
        with self.lock:
            if fresh:
                self.known = {}
            phones = []
            for serial, state, model in listed:
                key = (serial, state)
                if key not in self.known:
                    self.known[key] = self.details(adb, serial, state, model)
                phones.append(self.known[key])
            self.known = {k: v for k, v in self.known.items() if any((k == (p['serie'], p['etat']) for p in phones))}
        phones.sort(key=lambda p: (p['emulateur'], p['etat'] != 'device'))
        return {'adb': adb, 'telephones': phones}

    def watch(self):
        while True:
            if BUS.listening() and WORK.name not in ('installation', 'maj_telephone'):
                found = self.read()
                if found != self.shown:
                    self.shown = found
                    BUS.send('telephones', **found)
            time.sleep(3)

    def forget(self):
        with self.lock:
            self.known = {}
PHONES = Phones()

def cmd_telephones(body):
    found = PHONES.read(fresh=bool(body.get('rafraichir')))
    PHONES.shown = found
    BUS.send('telephones', **found)
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

def installed(adb, serial, kept):
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

def copies_folder():
    commun.COPIES.mkdir(parents=True, exist_ok=True)
    return commun.COPIES

def work_folder(out):
    chosen = setting('dossier_travail')
    place = chosen if chosen and os.path.isdir(chosen) else os.path.dirname(os.path.abspath(out))
    return tempfile.mkdtemp(prefix='rr_patch_', dir=place)

def build_choices(body):
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
        what = tr('Préparation pour Mac')
        bar(0, 0, 0, what, 0)
        return jeu_mac.prepare(official, save, new_game, artworks, work_folder(out), game, lambda fraction, text: bar(fraction * 100, fraction * 100, 0, text, 6))
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

def check_release():
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
        mises_a_jour.update_tool(release, str(commun.ROOT))
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

def editor_state():
    model = EDIT.model
    if model.save is None:
        return {'ouvert': False}
    return {'ouvert': True, 'source': model.source, 'changements': model.changes(), 'resume': model.summary()}

def opened():
    if EDIT.model.save is None:
        raise Erreur(tr('Aucune sauvegarde ouverte.'))
    return EDIT.model

def cmd_ed_ouvrir(body):
    source = body.get('source')
    path = body.get('chemin')
    if source == 'fichier':
        raw, label = (Path(existing(path)).read_bytes(), path)
    elif source == 'copie':
        path = existing(path)
        save = Path(path) / 'save.msgpack' if os.path.isdir(path) else Path(path)
        if not save.is_file():
            raise Erreur(tr("Cette copie n'a pas de sauvegarde (save.msgpack)."))
        raw, label = (save.read_bytes(), str(save))
    elif source == 'nouvelle':
        raw, label = (copie_android.pack(copie_android.new_save()), tr('partie vierge'))
    elif source == 'telephone':
        adb, serial = phone()
        try:
            local = em.pull_phone_save(adb, serial, copies_folder())
        except em.Refus as refus:
            raise Erreur(str(refus))
        raw, label = (local.read_bytes(), tr('téléphone (copie gardée dans {name})', name=local.name))
    else:
        raise Erreur(tr('Source inconnue.'))
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

def row_json(row, columns):
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

def cmd_ed_changer(body):
    tab, index, key, value = (body.get('onglet'), body.get('ligne'), body.get('cle'), body.get('valeur'))
    with EDIT.lock:
        model = opened()
        rows = model.rows(tab)
        if not isinstance(index, int) or not 0 <= index < len(rows) or (body.get('nom') is not None and rows[index].get('name') != body.get('nom')):
            raise Erreur(tr('La liste a changé : il faut recommencer.'), 'liste')
        row = rows[index]
        kind = next((k for c, _, _, k in em.columns(tab) if c == key), None)
        if not kind or not row.editable(key):
            raise Erreur(tr('Cette valeur ne peut pas changer.'))
        if kind == 'bool':
            value = bool(value)
        elif isinstance(row.get(key), str):
            value = str(value)
        else:
            low, high = row.bounds(key)
            try:
                value = int(value)
            except (TypeError, ValueError):
                raise Erreur(tr('Il faut un nombre.'))
            if not low <= value <= high:
                raise Erreur(tr('Il faut un nombre de {low} à {high}.', low=low, high=high))
        try:
            row.set(key, value)
        except em.Refus as refus:
            raise Erreur(str(refus), 'refus')
        return editor_state()

def cmd_ed_action(body):
    action, picked = (body.get('action'), body.get('lignes') or [])
    with EDIT.lock:
        model = opened()
        try:
            if action == 'tous_heros':
                model.all_heroes()
            elif action == 'toutes_armes':
                model.all_weapons()
            elif action == 'tous_costumes':
                model.all_skins()
            elif action in ('max_heros', 'max_armes'):
                rows = model.rows('heros' if action == 'max_heros' else 'armes')
                chosen = [rows[i] for i in picked if isinstance(i, int) and 0 <= i < len(rows)]
                (model.max_heroes if action == 'max_heros' else model.max_weapons)(chosen)
            else:
                raise Erreur(tr('Action inconnue.'))
        except em.Refus as refus:
            raise Erreur(str(refus), 'refus')
        return editor_state()

def node_path(body):
    part, path = (body.get('partie'), body.get('chemin') or [])
    model = opened()
    if part not in model.save.values:
        raise Erreur(tr('La liste a changé : il faut recommencer.'), 'liste')
    try:
        model.value_at(part, path)
    except (KeyError, IndexError, TypeError):
        raise Erreur(tr('La liste a changé : il faut recommencer.'), 'liste')
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

def cmd_ed_noeud(body):
    with EDIT.lock:
        model, part, path = node_path(body)
        value = model.value_at(part, path)
        what, detail = sv.describe(body.get('type') or '?')
        found = {'valeur': plain(value), 'quoi': what}
        if what == 'enum':
            found['choix'] = [[v, sv.name_of(detail, v)] for v, _ in sv.enum_values(detail)]
        if what == 'int':
            found['bornes'] = list(detail)
        if isinstance(value, bool):
            found['quoi'] = 'bool'
        elif what == 'unknown' and isinstance(value, (int, float, str)):
            found['quoi'] = {int: 'int', float: 'float', str: 'string'}[type(value)]
        return found

def cmd_ed_noeud_changer(body):
    with EDIT.lock:
        model, part, path = node_path(body)
        if not path:
            raise Erreur(tr('Cette valeur ne peut pas changer.'))
        old = model.value_at(part, path)
        what, detail = sv.describe(body.get('type') or '?')
        new = body.get('valeur')
        try:
            if what == 'bool' or isinstance(old, bool):
                new = bool(new)
            elif what == 'string' or isinstance(old, str):
                new = str(new)
            elif what == 'bytes':
                new = bytes.fromhex(str(new))
            elif what == 'float' or isinstance(old, float):
                new = sv.F32(float(new)) if isinstance(old, sv.F32) or detail in ('float', 'Single') else float(new)
            else:
                new = int(new)
                low, high = detail if what == 'int' else (-2 ** 63, 2 ** 64 - 1)
                if not low <= new <= high:
                    raise Erreur(tr('Il faut un nombre de {low} à {high}.', low=low, high=high))
        except (TypeError, ValueError):
            raise Erreur(tr('Valeur refusée.'))
        model.set_at(part, path, new)
        return editor_state()

def cmd_ed_noeud_ajouter(body):
    with EDIT.lock:
        model, part, path = node_path(body)
        target = model.value_at(part, path)
        what, detail = sv.describe(body.get('type') or '?')
        if what == 'list' and isinstance(target, list):
            model.add_item(target, detail)
        elif what == 'list' and target is None and path:
            model.set_at(part, path, [])
        elif what == 'map' and isinstance(target, dict):
            key_kind, item_kind = detail
            key = body.get('cle')
            key_what, _ = sv.describe(key_kind)
            try:
                key = int(key) if key_what in ('int', 'enum') else str(key)
            except (TypeError, ValueError):
                raise Erreur(tr('Il faut un nombre.'))
            try:
                model.add_key(target, key, item_kind)
            except em.Refus as refus:
                raise Erreur(str(refus))
        else:
            raise Erreur(tr('Rien à ajouter ici.'))
        return editor_state()

def cmd_ed_noeud_retirer(body):
    with EDIT.lock:
        model, part, path = node_path(body)
        if not path:
            raise Erreur(tr('Rien à retirer ici.'))
        parent = model.value_at(part, path[:-1])
        if not isinstance(parent, (list, dict)):
            raise Erreur(tr('Rien à retirer ici.'))
        model.remove_item(parent, path[-1])
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
        found['date'] = datetime.datetime.fromtimestamp(KEY.stat().st_mtime).strftime('%d/%m/%Y')
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
        if key is None or cert is None:
            raise ValueError
    except Exception:
        raise Erreur(tr("Ce fichier n'est pas une clé de l'outil (cle_apk.p12)."))
    if KEY.is_file():
        KEY.rename(KEY.with_name(f'cle_apk_{datetime.datetime.now():%Y-%m-%d_%H%M%S}.p12.ancienne'))
    commun.BASE.mkdir(exist_ok=True)
    shutil.copy2(source, KEY)
    PHONES.forget()
    return cmd_cle_info({})

def cmd_certificat_info(_):
    authority = CERTIFICATE / 'mitmproxy-ca-cert.pem'
    return {'dossier': str(CERTIFICATE), 'existe': authority.is_file() or (CERTIFICATE / 'dns-copie.pem').is_file(), 'date': datetime.datetime.fromtimestamp(authority.stat().st_mtime).strftime('%d/%m/%Y') if authority.is_file() else None}

def cmd_certificat_recreer(_):
    if WORK.name == 'copie':
        raise Erreur(tr("Il faut d'abord arrêter la copie."), 'occupe')
    if CERTIFICATE.exists():
        CERTIFICATE.rename(CERTIFICATE.with_name(f'certificat_{datetime.datetime.now():%Y-%m-%d_%H%M%S}.ancien'))
    return cmd_certificat_info({})

def size_of(folder):
    total = 0
    for base, _, files in os.walk(folder):
        for name in files:
            try:
                total += os.path.getsize(os.path.join(base, name))
            except OSError:
                pass
    return total

def leftovers():
    places = {tempfile.gettempdir(), os.path.dirname(os.path.abspath(setting('output') or str(commun.DEFAULT_APK))), str(jeu_mac.BASE)}
    if setting('dossier_travail'):
        places.add(setting('dossier_travail'))
    found = []
    for place in places:
        if os.path.isdir(place):
            for name in os.listdir(place):
                path = os.path.join(place, name)
                if name.startswith(('rr_patch_', 'rr_maj_')) and os.path.isdir(path):
                    found.append(path)
    return found

def cmd_temporaires(_):
    if WORK.name in ('fabrication', 'maj_telephone', 'maj_outil', 'ordinateur'):
        return {'dossiers': [], 'taille': 0}
    found = leftovers()
    return {'dossiers': found, 'taille': sum((size_of(path) for path in found))}

def to_trash(path):
    if sys.platform == 'darwin':
        trash = Path.home() / '.Trash'
        target, number = (trash / Path(path).name, 2)
        while target.exists():
            target, number = (trash / f'{Path(path).name} {number}', number + 1)
        shutil.move(path, target)
    else:
        shutil.rmtree(path, ignore_errors=True)

def cmd_nettoyer(_):
    if WORK.name in ('fabrication', 'maj_telephone', 'maj_outil', 'ordinateur'):
        raise Erreur(tr('Il faut attendre la fin de la tâche en cours.'), 'occupe')
    found = leftovers()
    freed = sum((size_of(path) for path in found))
    for path in found:
        to_trash(path)
    return {'liberes': freed, 'dossiers': len(found)}

def cmd_composants(_):
    expected = READY_EXPECTED.read_text().strip() if READY_EXPECTED.is_file() else None
    mark = READY_MARK.read_text().strip() if READY_MARK.is_file() else None
    return {'python': sys.version.split()[0], 'chemin': sys.executable, 'pret': mark, 'attendu': expected, 'ok': mark is not None and (expected is None or mark == expected), 'pip_log': str(commun.BASE / 'pip.log') if (commun.BASE / 'pip.log').is_file() else None, 'erreur_log': str(commun.BASE / 'erreur.log') if (commun.BASE / 'erreur.log').is_file() else None}

def cmd_composants_reparer(_):
    if READY_MARK.is_file():
        READY_MARK.unlink()
    return {}

def ask_path(kind, title, types=(), start='', name=''):
    if sys.platform == 'darwin':
        what = {'dossier': 'choose folder', 'enregistrer': 'choose file name', 'fichier': 'choose file'}[kind]
        script = f'POSIX path of ({what} with prompt {json.dumps(title)}'
        if kind == 'enregistrer' and name:
            script += f' default name {json.dumps(name)}'
        if start and os.path.isdir(start if os.path.isdir(start) else os.path.dirname(start)):
            folder = start if os.path.isdir(start) else os.path.dirname(start)
            script += f' default location (POSIX file {json.dumps(folder)})'
        done = subprocess.run(['osascript', '-e', script + ')'], capture_output=True, text=True)
        return done.stdout.strip() or None
    found = {}

    def window():
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        folder = start if os.path.isdir(start) else os.path.dirname(start) if start else None
        filetypes = [(' '.join((f'*.{t}' for t in types)), ' '.join((f'*.{t}' for t in types))), ('*', '*')] if types else None
        options = {'title': title, 'initialdir': folder or None, 'parent': root}
        if kind == 'dossier':
            found['chemin'] = filedialog.askdirectory(**options)
        elif kind == 'enregistrer':
            found['chemin'] = filedialog.asksaveasfilename(initialfile=name, filetypes=filetypes or [('*', '*')], defaultextension=f'.{types[0]}' if types else '', **options)
        else:
            found['chemin'] = filedialog.askopenfilename(filetypes=filetypes or [('*', '*')], **options)
        root.destroy()
    thread = threading.Thread(target=window)
    thread.start()
    thread.join()
    return found.get('chemin') or None

def cmd_fenetre(body):
    kind = body.get('type')
    if kind in ('choisir', 'enregistrer'):
        what = 'enregistrer' if kind == 'enregistrer' else 'dossier' if body.get('dossier') else 'fichier'
        title = {'enregistrer': tr('Enregistrer'), 'dossier': tr('Choisir un dossier')}.get(what, tr('Choisir un fichier'))
        return {'valeur': ask_path(what, title, body.get('types') or (), body.get('depart') or '', body.get('nom') or '')}
    if kind in ('montrer', 'ouvrir'):
        path = body.get('chemin') or ''
        if kind == 'ouvrir' and path and (not os.path.exists(path)):
            os.makedirs(path, exist_ok=True)
        commun.open_folder(existing(path), reveal=kind == 'montrer')
        return {'valeur': True}
    if kind == 'lien':
        if str(body.get('url', '')).startswith('https://'):
            import webbrowser
            webbrowser.open(body['url'])
        return {'valeur': True}
    if kind == 'relancer':
        launcher = HERE / 'lanceur_web.py'
        if os.name == 'nt' and launcher.is_file():
            flags = getattr(subprocess, 'DETACHED_PROCESS', 0) | getattr(subprocess, 'CREATE_NEW_PROCESS_GROUP', 0)
            subprocess.Popen([sys.executable, '-I', str(launcher)], creationflags=flags, close_fds=True)
            threading.Timer(1, stop).start()
        return {'valeur': True}
    raise Erreur(tr('Demande inconnue.'))

def cmd_quitter(_):
    threading.Timer(0.3, stop).start()
    return {}
COMMANDS = {name[4:]: function for name, function in globals().items() if name.startswith('cmd_')}

def stop():
    if isinstance(COPY.state, tuple):
        loop, master = COPY.state
        loop.call_soon_threadsafe(master.shutdown)
        time.sleep(1)
    WORK.keep_awake(False)
    os._exit(0)

class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    server_version = 'RangerRumble'

    def log_message(self, *_):
        pass

    def allowed_host(self):
        host = (self.headers.get('Host') or '').lower()
        return host in (f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}')

    def has_key(self, query):
        given = self.headers.get('X-Jeton') or (query.get('jeton') or [''])[0]
        return secrets.compare_digest(given, self.server.key)

    def answer(self, status, body, kind='application/json; charset=utf-8', cache=False):
        self.send_response(status)
        self.send_header('Content-Type', kind)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'max-age=3600' if cache else 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(body)

    def answer_json(self, value, status=200):
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
            return self.file(WEB / url.path[5:], WEB)
        if url.path == '/ressources/langues.json':
            return self.file(PICTURES / 'langues.json', PICTURES)
        for folder in SHOWN_PICTURES:
            if url.path.startswith(f'/ressources/{folder}/'):
                return self.file(PICTURES / url.path[len('/ressources/'):], PICTURES / folder, cache=True)
        self.answer(404, b'{}')

    def file(self, path, inside, cache=False):
        path = Path(os.path.realpath(path))
        if not str(path).startswith(os.path.realpath(inside) + os.sep) or not path.is_file():
            return self.answer(404, b'{}')
        kind = mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
        if kind.startswith('text/') or kind in ('application/javascript', 'application/json'):
            kind += '; charset=utf-8'
        self.answer(200, path.read_bytes(), kind, cache)

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
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        finally:
            BUS.leave(listener)

    def do_POST(self):
        url = urlparse(self.path)
        if not self.allowed_host() or not self.has_key({}):
            return self.answer(403, b'{}')
        name = url.path[len('/api/'):] if url.path.startswith('/api/') else ''
        command = COMMANDS.get(name)
        if command is None:
            return self.answer_json({'ok': False, 'erreur': tr('Commande inconnue.')}, 404)
        try:
            length = int(self.headers.get('Content-Length') or 0)
            body = json.loads(self.rfile.read(length) or b'{}') if length else {}
            if not isinstance(body, dict):
                raise ValueError
        except ValueError:
            return self.answer_json({'ok': False, 'erreur': tr('Demande illisible.')}, 400)
        try:
            result = command(body) or {}
            self.answer_json({'ok': True, **result})
        except Erreur as refused:
            self.answer_json({'ok': False, 'erreur': str(refused), 'code': refused.code, **refused.details})
        except (copie_android.Problem, mises_a_jour.Problem) as problem:
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

def watch_window(first=90, after=10):
    seen, alone = (False, time.monotonic())
    while True:
        time.sleep(1)
        if BUS.listening():
            seen, alone = (True, time.monotonic())
        elif time.monotonic() - alone > (after if seen else first) and WORK.name is None:
            stop()

def new_server(port=0, key=None):
    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    server.daemon_threads = True
    server.key = key or secrets.token_urlsafe(24)
    return server

def serve(server, ends):
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

def main():
    parser = argparse.ArgumentParser(description=(__doc__ or '').split('\n')[0])
    parser.add_argument('--port', type=int, default=0)
    parser.add_argument('--jeton')
    parser.add_argument('--garder', action='store_true', help="ne pas s'arrêter quand l'entrée standard se ferme")
    args = parser.parse_args()
    old_app = commun.ROOT / 'Ranger Rumble hors ligne.app'
    if sys.platform == 'darwin' and old_app.is_dir() and (commun.ROOT / 'Launcher Ratchet Ranger Rumble.app').is_dir():
        try:
            to_trash(str(old_app))
        except OSError:
            pass
    server = new_server(args.port, args.jeton)
    sys.stdout.write(json.dumps({'port': server.server_port, 'jeton': server.key}) + '\n')
    sys.stdout.flush()
    serve(server, None if args.garder else 'stdin')
if __name__ == '__main__':
    main()
