import argparse
import hashlib
import os
import runpy
import shutil
import sys
import tempfile
import zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
ANDROID = os.path.join(HERE, '..', 'android')
sys.path.insert(0, HERE)
import copie_android
import donnees_capture
import manifeste
import signature
EXPECTED = {'lib/arm64-v8a/libil2cpp.so': 'bb8134f5de8b646caa8db1441cb9d3253cf1ac8d75710972d13e768b9c57a5aa', 'assets/bin/Data/Managed/Metadata/global-metadata.dat': '028b8ac2aafe771681d2c81e28ded2616662bc6e00211863c3e68b0410d95e8b'}
PARTS = {'com.playstation.rattlesnake.apk': ('com.playstation.rattlesnake.apk', 'base.apk'), 'config.arm64_v8a.apk': ('config.arm64_v8a.apk', 'split_config.arm64_v8a.apk'), 'UnityDataAssetPack.apk': ('UnityDataAssetPack.apk', 'split_UnityDataAssetPack.apk')}
KEY_FOLDER = os.path.join(os.path.expanduser('~'), '.sauvegarde-rr')
HERO_BUNDLES = [f'assets/aa/Android/skins_character_{name}_assets_all_{digest}.bundle' for name, digest in (('chance', 'ea1ae1112a40301e645b11ad648e496e'), ('molly', '80f842b062ace3fefa745878c83a6881'), ('helen', '4ef63d6105788453fb4e18743712bea3'), ('flare', '8159a571a17f52f74c15b2204f78c986'), ('nakari', 'a4eb9425bfd989f6ee7fb28826b49a60'), ('terry', 'de70656b1216b2c5250c779049a63de3'), ('crumby', '93cb392aad4df1691bf261475d287895'))]

def say(text):
    print(text, flush=True)

def extract(package, folder, wanted):
    with zipfile.ZipFile(package) as archive:
        names = set(archive.namelist())
        for target, choices in wanted.items():
            found = next((name for name in choices if name in names), None)
            if not found:
                raise SystemExit(f'{os.path.basename(package)} : {choices[0]} introuvable')
            with archive.open(found) as source, open(os.path.join(folder, target), 'wb') as out:
                shutil.copyfileobj(source, out, 1 << 22)

def check_version(folder):
    for part in ('config.arm64_v8a.apk', 'com.playstation.rattlesnake.apk'):
        with zipfile.ZipFile(os.path.join(folder, part)) as apk:
            for inner, digest in EXPECTED.items():
                if inner in apk.namelist() and hashlib.sha256(apk.read(inner)).hexdigest() != digest:
                    raise SystemExit("Ce fichier n'est pas la version 1.10.4 attendue du jeu.")

def old_version_pack(package, folder):
    os.makedirs(folder)
    try:
        extract(package, folder, {'split_UnityDataAssetPack.apk': PARTS['UnityDataAssetPack.apk']})
    except (zipfile.BadZipFile, SystemExit):
        raise SystemExit("Le deuxième fichier n'est pas le jeu officiel en version 1.10.3 (.apkm ou .xapk).")
    with zipfile.ZipFile(os.path.join(folder, 'split_UnityDataAssetPack.apk')) as pack:
        names = set(pack.namelist())
    if any((name not in names for name in HERO_BUNDLES)):
        raise SystemExit("Le deuxième fichier n'est pas la version 1.10.3 attendue du jeu.")
OLD_110_BUNDLES = ('scene_mainmenu_landscape_', '69b923348c4df9ad548573d6b86b9c62_monoscripts_')

def check_110(package):
    import io
    try:
        with zipfile.ZipFile(package) as archive:
            pack = zipfile.ZipFile(io.BytesIO(archive.read('UnityDataAssetPack.apk')))
            names = [n.split('/')[-1] for n in pack.namelist() if n.startswith('assets/aa/Android/')]
    except (OSError, KeyError, zipfile.BadZipFile):
        raise SystemExit("Le troisième fichier n'est pas le jeu officiel en version 1.1.0 (.xapk).")
    if not all((any((n.startswith(prefix) for n in names)) for prefix in OLD_110_BUNDLES)):
        raise SystemExit("Le troisième fichier n'est pas la version 1.1.0 attendue du jeu.")

def rebuilt_base(original, target, copy=False):
    with zipfile.ZipFile(original) as source, zipfile.ZipFile(target, 'w', allowZip64=True) as out:
        for info in source.infolist():
            if info.filename.startswith('META-INF/') or info.filename == 'stamp-cert-sha256':
                continue
            content = source.read(info.filename)
            if info.filename == 'AndroidManifest.xml':
                content = manifeste.modify(content, copy)
            out.writestr(info, content)

def run_script(path, argv, env):
    saved_argv, saved_env = (sys.argv, dict(os.environ))
    sys.argv = [path] + argv
    os.environ.update(env)
    sys.path.insert(0, os.path.dirname(path))
    try:
        runpy.run_path(path, run_name='__main__')
    finally:
        sys.argv = saved_argv
        os.environ.clear()
        os.environ.update(saved_env)
        sys.path.remove(os.path.dirname(path))

def build(official, old, out, data=None, save=None, copy=None, key_store=None, password=None, work=None, new_game=False, artworks=None, old_110=None):
    work = work or tempfile.mkdtemp(prefix='rr_patch_', dir=os.path.dirname(os.path.abspath(out)))
    try:
        parts = os.path.join(work, 'xapk')
        os.makedirs(parts)
        say('1/6 Lecture du jeu officiel...')
        extract(official, parts, PARTS)
        check_version(parts)
        old_version_pack(old, os.path.join(work, 'v1103'))
        if old_110:
            check_110(old_110)
            say("Jeu 1.1.0 fourni : l'écran de collecte de Mme Zurkon sera remis.")
        if copy:
            data = donnees_capture.convert(copy, os.path.join(work, 'donnees'))
            if not save and (not new_game) and os.path.isfile(os.path.join(copy, 'save.msgpack')):
                save = os.path.join(copy, 'save.msgpack')
        if new_game and (not save):
            save = os.path.join(work, 'nouvelle_partie.msgpack')
            with open(save, 'wb') as handle:
                handle.write(copie_android.pack(copie_android.new_save()))
        if not save:
            raise SystemExit('Choisis une sauvegarde, ou une nouvelle partie.')
        say('2/6 Retouches du jeu (quelques minutes)...')
        run_script(os.path.join(ANDROID, 'construire_apk.py'), [parts, os.path.join(work, 'patched')], {'RR_SANS_CLANG': '1', 'RR_VERSION': '1.10.4', 'RR_HEROS_DOSSIER': os.path.join(work, 'heros'), 'RR_JEU_110': os.path.abspath(old_110) if old_110 else ''})
        say('3/6 Manifeste...')
        rebuilt_base(os.path.join(parts, 'com.playstation.rattlesnake.apk'), os.path.join(work, 'base.apk'))
        say('4/6 Serveur, donnees et sauvegarde...')
        server = os.path.join(work, 'serveur')
        os.makedirs(os.path.join(server, 'etat'))
        shutil.copytree(data, os.path.join(server, 'donnees'))
        unsigned = out + '.tmp'
        run_script(os.path.join(ANDROID, 'assembler_apk.py'), [os.path.join(work, 'base.apk'), os.path.join(work, 'patched'), os.path.join(HERE, 'ressources', 'serveur.dex'), server, unsigned], {'RR_ALIGNE': '1', 'RR_SAUVEGARDE': os.path.abspath(save), 'RR_VERSION': '1.10.4', 'RR_ARTWORKS': os.path.abspath(artworks) if artworks else ''})
        say('5/6 Signature...')
        key, cert = signature.load_key(key_store, password) if key_store else signature.load_or_make_key(KEY_FOLDER)
        signature.sign(unsigned, key, cert)
        os.replace(unsigned, out)
        say(f'6/6 Fini : {out} ({os.path.getsize(out) / 1048576:.0f} Mo)')
    finally:
        shutil.rmtree(work, ignore_errors=True)

def build_copy(official, out, key_store=None, password=None, work=None, upstream=''):
    work = work or tempfile.mkdtemp(prefix='rr_copie_', dir=os.path.dirname(os.path.abspath(out)))
    try:
        parts = os.path.join(work, 'xapk')
        os.makedirs(parts)
        say('1/5 Lecture du jeu officiel...')
        extract(official, parts, PARTS)
        check_version(parts)
        say('2/5 Retouches du jeu (adresse du serveur seulement)...')
        run_script(os.path.join(ANDROID, 'construire_apk.py'), [parts, os.path.join(work, 'patched')], {'RR_SANS_CLANG': '1', 'RR_VERSION': '1.10.4', 'RR_COPIE': '1'})
        say('3/5 Manifeste...')
        rebuilt_base(os.path.join(parts, 'com.playstation.rattlesnake.apk'), os.path.join(work, 'base.apk'), copy=True)
        say('4/5 Relais de copie...')
        unsigned = out + '.tmp'
        run_script(os.path.join(ANDROID, 'assembler_apk.py'), [os.path.join(work, 'base.apk'), os.path.join(work, 'patched'), os.path.join(HERE, 'ressources', 'serveur.dex'), work, unsigned], {'RR_ALIGNE': '1', 'RR_VERSION': '1.10.4', 'RR_COPIE': '1', 'RR_RELAIS': upstream})
        say('5/5 Signature...')
        key, cert = signature.load_key(key_store, password) if key_store else signature.load_or_make_key(KEY_FOLDER)
        signature.sign(unsigned, key, cert)
        os.replace(unsigned, out)
        say(f'Fini : {out} ({os.path.getsize(out) / 1048576:.0f} Mo)')
    finally:
        shutil.rmtree(work, ignore_errors=True)

def main():
    parser = argparse.ArgumentParser(description="Fabrique l'APK hors ligne de Ranger Rumble.")
    if len(sys.argv) > 1 and sys.argv[1] == '--rr-copie':
        copy_parser = argparse.ArgumentParser(description="Fabrique RR Copie, l'appli qui copie la sauvegarde.")
        copy_parser.add_argument('officiel')
        copy_parser.add_argument('sortie')
        copy_parser.add_argument('--cle')
        copy_parser.add_argument('--mot-de-passe')
        copy_parser.add_argument('--serveur', default='', help=argparse.SUPPRESS)
        args = copy_parser.parse_args(sys.argv[2:])
        build_copy(args.officiel, args.sortie, args.cle, args.mot_de_passe, upstream=args.serveur)
        return
    parser.add_argument('officiel')
    parser.add_argument('ancien', help='le jeu officiel en version 1.10.3 (les héros jamais sortis)')
    parser.add_argument('sortie')
    parser.add_argument('--copie')
    parser.add_argument('--donnees')
    parser.add_argument('--sauvegarde')
    parser.add_argument('--nouvelle-partie', action='store_true')
    parser.add_argument('--cle')
    parser.add_argument('--mot-de-passe')
    parser.add_argument('--artworks', help="un dossier d'images pour la galerie du jeu (facultatif)")
    parser.add_argument('--jeu-110', help="le jeu officiel en version 1.1.0 (facultatif : l'écran de Mme Zurkon)")
    args = parser.parse_args()
    if not args.copie and (not (args.donnees and (args.sauvegarde or args.nouvelle_partie))):
        parser.error('--copie, ou --donnees avec --sauvegarde ou --nouvelle-partie')
    build(args.officiel, args.ancien, args.sortie, args.donnees, args.sauvegarde, args.copie, args.cle, args.mot_de_passe, new_game=args.nouvelle_partie, artworks=args.artworks, old_110=args.jeu_110)
if __name__ == '__main__':
    main()
