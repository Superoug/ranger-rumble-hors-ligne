import argparse
import contextlib
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
import commun
import copie_android
import donnees_capture
import manifeste
import signature
from langues import tr
GAME_VERSION = '1.10.4'
EXPECTED = {'lib/arm64-v8a/libil2cpp.so': 'bb8134f5de8b646caa8db1441cb9d3253cf1ac8d75710972d13e768b9c57a5aa', 'assets/bin/Data/Managed/Metadata/global-metadata.dat': '028b8ac2aafe771681d2c81e28ded2616662bc6e00211863c3e68b0410d95e8b'}
BASE_PART, LIBRARY_PART, ASSET_PACK_PART = ('com.playstation.rattlesnake.apk', 'config.arm64_v8a.apk', 'UnityDataAssetPack.apk')
PARTS = {BASE_PART: (BASE_PART, 'base.apk'), LIBRARY_PART: (LIBRARY_PART, 'split_config.arm64_v8a.apk'), ASSET_PACK_PART: (ASSET_PACK_PART, 'split_UnityDataAssetPack.apk')}
BASE_ASSETS = {'assets/bin/Data/Managed/Metadata/global-metadata.dat', 'assets/bin/Data/Managed/Resources/OhbibiCore.dll-resources.dat', 'assets/bin/Data/Managed/Resources/System.Collections.Immutable.dll-resources.dat', 'assets/bin/Data/Managed/Resources/System.Data.dll-resources.dat', 'assets/bin/Data/Managed/Resources/System.Drawing.dll-resources.dat', 'assets/bin/Data/Managed/Resources/mscorlib.dll-resources.dat', 'assets/bin/Data/Resources/unity default resources', 'assets/bin/Data/Resources/unity_builtin_extra', 'assets/bin/Data/RuntimeInitializeOnLoads.json', 'assets/bin/Data/ScriptingAssemblies.json', 'assets/bin/Data/boot.config', 'assets/bin/Data/globalgamemanagers', 'assets/bin/Data/globalgamemanagers.assets.split0', 'assets/bin/Data/globalgamemanagers.assets.split1', 'assets/bin/Data/globalgamemanagers.assets.split2', 'assets/bin/Data/level0', 'assets/bin/Data/sharedassets0.assets', 'assets/bin/Data/sharedassets0.resource', 'assets/bin/Data/unity_app_guid', 'assets/dexopt/baseline.prof', 'assets/dexopt/baseline.profm'}
NATIVE_LIBRARIES = 'lib/arm64-v8a/'
COPY_BLOCK = 1 << 22
KEY_FOLDER = os.path.join(os.path.expanduser('~'), '.sauvegarde-rr')
ARTBOOK = os.path.join(HERE, '..', 'artbook')
OLD_110_SUBSET = os.path.join(HERE, '..', 'ressources_110', 'jeu_110_ecran_collecte.xapk')
if not os.path.isdir(ARTBOOK):
    ARTBOOK = os.path.join(HERE, '..', '..', 'Images', 'Artbook du jeu')
if not os.path.isfile(OLD_110_SUBSET):
    OLD_110_SUBSET = os.path.join(HERE, '..', '..', 'Jeux officiels', 'ratchet-and-clank-ranger-rumble-1-1-0.xapk')
HEROES = os.path.join(HERE, 'ressources', 'heros')
HERO_BUNDLES = [f'assets/aa/Android/skins_character_{name}_assets_all_{digest}.bundle' for name, digest in (('chance', 'ea1ae1112a40301e645b11ad648e496e'), ('molly', '80f842b062ace3fefa745878c83a6881'), ('helen', '4ef63d6105788453fb4e18743712bea3'), ('flare', '8159a571a17f52f74c15b2204f78c986'), ('nakari', 'a4eb9425bfd989f6ee7fb28826b49a60'), ('terry', 'de70656b1216b2c5250c779049a63de3'), ('crumby', '93cb392aad4df1691bf261475d287895'))]

def bundles_without_lz4():
    try:
        import lz4
    except ImportError:
        return
    if not getattr(lz4, 'PUR', False):
        return
    from UnityPy.files.BundleFile import BundleFile
    save = BundleFile.save
    BundleFile.save = lambda self, packer=None: save(self, 'none' if packer in ('lz4', 'lz4hc') else packer)
bundles_without_lz4()

def pictures_without_native_extras():
    import importlib
    import types
    missing = []
    for name in ('fmod_toolkit', 'astc_encoder'):
        if isinstance(sys.modules.get(name), types.ModuleType) and (not getattr(sys.modules[name], '__file__', None)):
            missing.append(name)
            continue
        try:
            importlib.import_module(name)
        except Exception as failure:
            commun.keep_details(f'{name} : {type(failure).__name__} : {failure}')
            sys.modules[name] = types.ModuleType(name)
            missing.append(name)
    if 'astc_encoder' in missing:
        try:
            import texture2ddecoder
            from PIL import Image
            from UnityPy.export import Texture2DConverter
        except Exception as failure:
            commun.keep_details(f'UnityPy.export : {type(failure).__name__} : {failure}')
            return missing

        def astc(image_data, width, height, block_size, hdr=False):
            raw = texture2ddecoder.decode_astc(image_data, width, height, *block_size)
            return Image.frombytes('RGBA', (width, height), raw, 'raw', 'BGRA')
        for texture_format, (function, args) in list(Texture2DConverter.CONV_TABLE.items()):
            if getattr(function, '__name__', '') == 'astc':
                Texture2DConverter.CONV_TABLE[texture_format] = (astc, args)
    return missing

def say(text):
    print(text, flush=True)

@contextlib.contextmanager
def hidden_output(errors_too=False):
    if os.environ.get('RR_DETAILS') == '1':
        yield
        return
    details = commun.LiveDetails()
    with contextlib.redirect_stdout(details), contextlib.redirect_stderr(details) if errors_too else contextlib.nullcontext():
        yield

def quietly(function, *args):
    with hidden_output():
        return function(*args)

def run_script(path, argv, env):
    saved_argv, saved_env, saved_path = (sys.argv, dict(os.environ), list(sys.path))
    sys.argv = [path] + argv
    os.environ.update(env)
    sys.path.insert(0, os.path.dirname(path))
    try:
        with hidden_output(errors_too=True):
            runpy.run_path(path, run_name='__main__')
    finally:
        sys.argv = saved_argv
        os.environ.clear()
        os.environ.update(saved_env)
        sys.path[:] = saved_path

def extract(package, folder, wanted):
    with zipfile.ZipFile(package) as archive:
        names = set(archive.namelist())
        for target, choices in wanted.items():
            found = next((name for name in choices if name in names), None)
            if not found:
                raise SystemExit(f'{os.path.basename(package)} : {choices[0]} introuvable')
            with archive.open(found) as source, open(os.path.join(folder, target), 'wb') as out:
                shutil.copyfileobj(source, out, COPY_BLOCK)

def read_official(package, folder):
    try:
        with zipfile.ZipFile(package) as archive:
            single = 'AndroidManifest.xml' in archive.namelist()
    except (OSError, zipfile.BadZipFile):
        raise SystemExit(tr("Ce fichier n'est pas le jeu (.xapk, .apkm ou .apk)."))
    if single:
        split_apk(package, folder)
    else:
        extract(package, folder, PARTS)

def part_of(name):
    if name.endswith('/') or (name.startswith('lib/') and (not name.startswith(NATIVE_LIBRARIES))):
        return None
    if name.startswith('lib/'):
        return LIBRARY_PART
    if name.startswith('assets/') and name not in BASE_ASSETS:
        return ASSET_PACK_PART
    return BASE_PART

def split_apk(package, folder):
    writers = {part: zipfile.ZipFile(os.path.join(folder, part), 'w', allowZip64=True) for part in PARTS}
    try:
        with zipfile.ZipFile(package) as archive:
            for info in archive.infolist():
                part = part_of(info.filename)
                if part is None:
                    continue
                entry = zipfile.ZipInfo(info.filename, date_time=info.date_time)
                entry.compress_type = info.compress_type
                entry.external_attr = info.external_attr
                entry.file_size = info.file_size
                with archive.open(info) as source, writers[part].open(entry, 'w') as out:
                    shutil.copyfileobj(source, out, COPY_BLOCK)
    finally:
        for writer in writers.values():
            writer.close()
    with zipfile.ZipFile(os.path.join(folder, LIBRARY_PART)) as code, zipfile.ZipFile(os.path.join(folder, ASSET_PACK_PART)) as data:
        if 'lib/arm64-v8a/libil2cpp.so' not in code.namelist() or 'assets/aa/catalog.bin' not in data.namelist():
            raise SystemExit(tr("Cette APK n'a pas tout le jeu : il faut le .xapk (APKPure) ou le .apkm (APKMirror)."))

def check_version(folder):
    for part in (LIBRARY_PART, BASE_PART):
        with zipfile.ZipFile(os.path.join(folder, part)) as apk:
            for inner, digest in EXPECTED.items():
                if inner in apk.namelist() and hashlib.sha256(apk.read(inner)).hexdigest() != digest:
                    raise SystemExit(tr("Ce fichier n'est pas la version 1.10.4 attendue du jeu."))

def check_heroes():
    names = set(os.listdir(HEROES)) if os.path.isdir(HEROES) else set()
    if 'heros.json' not in names or any((os.path.basename(name) not in names for name in HERO_BUNDLES)):
        raise SystemExit(tr("Les modèles des 7 héros jamais sortis manquent dans l'outil (moteur/appli_patch/ressources/heros) : retélécharge l'outil."))

def rebuilt_base(original, target):
    with zipfile.ZipFile(original) as source, zipfile.ZipFile(target, 'w', allowZip64=True) as out:
        for info in source.infolist():
            if info.filename.startswith('META-INF/') or info.filename == 'stamp-cert-sha256':
                continue
            content = source.read(info.filename)
            if info.filename == 'AndroidManifest.xml':
                content = manifeste.modify(content)
            out.writestr(info, content)

def server_data(copy, data, work):
    if not copy and (not data):
        copy = copie_android.builtin_copy(work)
        if not copy:
            raise SystemExit(tr('Choisir une copie de sauvegarde.'))
    if copy:
        data = quietly(donnees_capture.convert, copy, os.path.join(work, 'donnees'))
    return (data, copy)

def chosen_save(save, copy, new_game, work):
    if copy and (not save) and (not new_game) and os.path.isfile(os.path.join(copy, 'save.msgpack')):
        save = os.path.join(copy, 'save.msgpack')
    if new_game and (not save):
        save = os.path.join(work, 'nouvelle_partie.msgpack')
        with open(save, 'wb') as handle:
            handle.write(copie_android.pack(copie_android.new_account_save()))
    if not save:
        raise SystemExit(tr('Choisir une sauvegarde, ou une nouvelle partie.'))
    return save

def patch_game(parts, patched, mac):
    old_110 = OLD_110_SUBSET if os.path.isfile(OLD_110_SUBSET) else None
    run_script(os.path.join(ANDROID, 'construire_apk.py'), [parts, patched], {'RR_SANS_CLANG': '1', 'RR_VERSION': GAME_VERSION, 'RR_HEROS_DOSSIER': HEROES, 'RR_JEU_110': os.path.abspath(old_110) if old_110 else '', 'RR_MAC': '1' if mac else ''})

def assemble(work, data, save, artworks, unsigned):
    server = os.path.join(work, 'serveur')
    os.makedirs(os.path.join(server, 'etat'))
    shutil.copytree(data, os.path.join(server, 'donnees'))
    artbook = os.path.abspath(ARTBOOK) if os.path.isfile(os.path.join(ARTBOOK, 'artbook.json')) else ''
    run_script(os.path.join(ANDROID, 'assembler_apk.py'), [os.path.join(work, 'base.apk'), os.path.join(work, 'patched'), os.path.join(HERE, 'ressources', 'serveur.dex'), server, unsigned], {'RR_ALIGNE': '1', 'RR_SAUVEGARDE': os.path.abspath(save), 'RR_VERSION': GAME_VERSION, 'RR_ARTWORKS': os.path.abspath(artworks) if artworks else '', 'RR_ARTBOOK': artbook})

def build(official, out, data=None, save=None, copy=None, key_store=None, password=None, work=None, new_game=False, artworks=None, mac=False):
    try:
        os.getcwd()
    except OSError:
        os.chdir(os.path.expanduser('~'))
    commun.start_details()
    pictures_without_native_extras()
    work = work or tempfile.mkdtemp(prefix='rr_patch_', dir=os.path.dirname(os.path.abspath(out)))
    try:
        parts = os.path.join(work, 'xapk')
        os.makedirs(parts)
        say(tr('1/6 Lecture du jeu officiel...'))
        read_official(official, parts)
        check_version(parts)
        check_heroes()
        data, copy = server_data(copy, data, work)
        save = chosen_save(save, copy, new_game, work)
        say(tr('2/6 Modifications du jeu (quelques minutes)...'))
        patch_game(parts, os.path.join(work, 'patched'), mac)
        say(tr('3/6 Préparation...'))
        rebuilt_base(os.path.join(parts, BASE_PART), os.path.join(work, 'base.apk'))
        say(tr('4/6 Sauvegarde...'))
        unsigned = out + '.tmp'
        assemble(work, data, save, artworks, unsigned)
        say(tr('5/6 Signature...'))
        key, cert = signature.load_key(key_store, password) if key_store else signature.load_or_make_key(KEY_FOLDER)
        signature.sign(unsigned, key, cert)
        os.replace(unsigned, out)
        say(tr('6/6 Fini : {out}', out=out))
    finally:
        shutil.rmtree(work, ignore_errors=True)

def main():
    parser = argparse.ArgumentParser(description="Fabrique l'APK hors ligne de Ranger Rumble.")
    parser.add_argument('officiel')
    parser.add_argument('sortie')
    parser.add_argument('--copie')
    parser.add_argument('--donnees')
    parser.add_argument('--sauvegarde')
    parser.add_argument('--nouvelle-partie', action='store_true')
    parser.add_argument('--cle')
    parser.add_argument('--mot-de-passe')
    parser.add_argument('--artworks', help="un dossier d'images pour la galerie du jeu (facultatif)")
    args = parser.parse_args()
    if not args.copie and (not args.nouvelle_partie) and (not (args.donnees and args.sauvegarde)):
        parser.error('--copie, --nouvelle-partie, ou --donnees avec --sauvegarde')
    build(args.officiel, args.sortie, args.donnees, args.sauvegarde, args.copie, args.cle, args.mot_de_passe, new_game=args.nouvelle_partie, artworks=args.artworks)
if __name__ == '__main__':
    main()
