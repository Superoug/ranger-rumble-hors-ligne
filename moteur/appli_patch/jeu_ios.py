import importlib.util
import io
import json
import os
import plistlib
import shutil
import time
import zipfile
from pathlib import Path
from langues import tr
HERE = Path(__file__).resolve().parent
IOS = HERE.parent / 'jeu_ios'
SIMULATOR = os.environ.get('RR_IOS_SIMULATEUR') == '1'
READY_MADE = IOS / ('livrable_simulateur' if SIMULATOR else 'livrable')
PLATFORM = 'ios-sim' if SIMULATOR else 'ios'
PROGRAM = READY_MADE / 'RangerRumble'
FRAMEWORKS = ('MoltenVK.framework', 'ServeurRR.framework')
X18_RECIPE = IOS / 'x18_recette_libunity.json'
CONVERTER = IOS / 'elf_vers_macho.py'
IPA_NAME = 'RangerRumble_hors_ligne.ipa'
INFO_NAME = 'RangerRumble_hors_ligne.ipa.json'
BUNDLE_ID = 'fr.rangerrumble.horsligne'
SIDELOADLY = 'https://sideloadly.io'
STEP_CONVERSION, STEP_IPA, STEP_DONE = (6, 7, 8)
APK_SHARE, CONVERSION_SHARE = (0.75, 0.1)

class Probleme(Exception):
    pass

def coming_soon() -> bool:
    return not (PROGRAM.is_file() and CONVERTER.is_file())

def missing() -> str | None:
    if coming_soon():
        return tr('Le jeu hors ligne sur iPhone et iPad est en préparation.')
    if not all(((READY_MADE / name).is_dir() for name in FRAMEWORKS)) or not X18_RECIPE.is_file():
        return tr("Des fichiers du jeu pour iPhone manquent dans l'outil.")
    return None

def ipa_path(output: str) -> Path:
    folder = Path(output).expanduser().parent if output else Path.home()
    return folder / IPA_NAME

def state(output: str) -> dict:
    ipa = ipa_path(output)
    infos = {}
    try:
        infos = json.loads((ipa.parent / INFO_NAME).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        pass
    ready = ipa.is_file()
    return {'bientot': coming_soon(), 'manque': missing(), 'pret': ready, 'ipa': str(ipa), 'taille': ipa.stat().st_size if ready else 0, 'infos': infos if ready else {}, 'sideloadly': SIDELOADLY}

def converter():
    spec = importlib.util.spec_from_file_location('elf_vers_macho', CONVERTER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def game_icon(apk: zipfile.ZipFile) -> bytes | None:
    names = set(apk.namelist())
    for density in ('xxxhdpi', 'xxhdpi', 'xhdpi', 'hdpi'):
        for suffix in ('', '-v4'):
            name = f'res/mipmap-{density}{suffix}/app_icon.png'
            if name in names:
                return apk.read(name)
    return None

def icons(picture: bytes) -> dict[str, bytes]:
    sizes = {'AppIcon60x60@2x.png': 120, 'AppIcon60x60@3x.png': 180, 'AppIcon76x76@2x~ipad.png': 152, 'AppIcon83.5x83.5@2x~ipad.png': 167}
    try:
        from PIL import Image
        image = Image.open(io.BytesIO(picture)).convert('RGB')
    except Exception:
        return {name: picture for name in sizes}
    made = {}
    for name, side in sizes.items():
        out = io.BytesIO()
        image.resize((side, side), Image.LANCZOS).save(out, 'PNG')
        made[name] = out.getvalue()
    return made

def info_plist(game_version: str) -> bytes:
    scene = {'UIWindowSceneSessionRoleApplication': [{'UISceneConfigurationName': 'Jeu', 'UISceneDelegateClassName': 'DelegueScene'}]}
    plist = {'CFBundleExecutable': 'RangerRumble', 'CFBundleIdentifier': BUNDLE_ID, 'CFBundleName': 'Ranger Rumble', 'CFBundleDisplayName': 'Ranger Rumble', 'CFBundleDevelopmentRegion': 'fr', 'CFBundlePackageType': 'APPL', 'CFBundleShortVersionString': game_version or '1.0', 'CFBundleVersion': '1', 'CFBundleSupportedPlatforms': ['iPhoneSimulator' if SIMULATOR else 'iPhoneOS'], 'MinimumOSVersion': '15.0', 'UIDeviceFamily': [1, 2], 'UIRequiredDeviceCapabilities': ['arm64', 'metal'], 'UISupportedInterfaceOrientations': ['UIInterfaceOrientationLandscapeRight', 'UIInterfaceOrientationLandscapeLeft'], 'UISupportedInterfaceOrientations~ipad': ['UIInterfaceOrientationLandscapeRight', 'UIInterfaceOrientationLandscapeLeft'], 'UIRequiresFullScreen': True, 'UIStatusBarHidden': True, 'UILaunchScreen': {}, 'UIFileSharingEnabled': True, 'LSSupportsOpeningDocumentsInPlace': True, 'UIApplicationSupportsIndirectInputEvents': True, 'NSLocalNetworkUsageDescription': 'Ranger Rumble : amis sur le même Wi-Fi.', 'UIApplicationSceneManifest': {'UIApplicationSupportsMultipleScenes': False, 'UISceneConfigurations': scene}, 'CFBundleIcons': {'CFBundlePrimaryIcon': {'CFBundleIconFiles': ['AppIcon60x60']}}, 'CFBundleIcons~ipad': {'CFBundlePrimaryIcon': {'CFBundleIconFiles': ['AppIcon60x60', 'AppIcon76x76', 'AppIcon83.5x83.5']}}}
    return plistlib.dumps(plist)

def tree_files(source: Path) -> list[Path]:
    return [path for path in sorted(source.rglob('*')) if path.is_file() and (not path.name.startswith('.'))]

def add_tree(archive: zipfile.ZipFile, source: Path, inside: str, written=None) -> None:
    for path in tree_files(source):
        add_file(archive, path, f'{inside}/{path.relative_to(source).as_posix()}', written=written)

def add_file(archive: zipfile.ZipFile, path: Path, name: str, stored: bool=False, written=None) -> None:
    entry = zipfile.ZipInfo(name, date_time=time.localtime(path.stat().st_mtime)[:6])
    entry.external_attr = (493 if os.access(path, os.X_OK) or path.suffix in ('', '.dylib') else 420) << 16
    entry.compress_type = zipfile.ZIP_STORED if stored else zipfile.ZIP_DEFLATED
    with open(path, 'rb') as source, archive.open(entry, 'w', force_zip64=True) as target:
        while (piece := source.read(16 << 20)):
            target.write(piece)
            if written:
                written(len(piece))

def add_bytes(archive: zipfile.ZipFile, name: str, data: bytes, executable: bool=False) -> None:
    entry = zipfile.ZipInfo(name, date_time=time.localtime()[:6])
    entry.external_attr = (493 if executable else 420) << 16
    entry.compress_type = zipfile.ZIP_DEFLATED
    archive.writestr(entry, data)

def prepare(official: str, save: str | None, new_game: bool, artworks: str | None, output: str, work: str, game_version: str, step) -> dict:
    import patcher
    problem = missing()
    if problem:
        raise Probleme(problem)
    ipa = ipa_path(output)
    ipa.parent.mkdir(parents=True, exist_ok=True)
    apk = Path(work) / 'jeu.apk'
    patcher.build(official, str(apk), save=save, new_game=new_game, artworks=artworks, work=str(Path(work) / 'apk'))
    build_ipa(apk, ipa, Path(work) / 'ios', game_version, step)
    (ipa.parent / INFO_NAME).write_text(json.dumps({'jeu': game_version, 'date': time.strftime('%Y-%m-%d %H:%M'), 'sauvegarde': '' if new_game else os.path.basename(save or ''), 'nouvelle': bool(new_game)}, ensure_ascii=False), encoding='utf-8')
    print(tr("L'IPA est prête : {path}", path=str(ipa)))
    return state(output)

def build_ipa(apk: Path, ipa: Path, work: Path, game_version: str, step) -> None:
    convert = converter()
    libraries = work / 'elf'
    converted = work / 'Frameworks'
    shutil.rmtree(work, ignore_errors=True)
    libraries.mkdir(parents=True)
    converted.mkdir()
    with zipfile.ZipFile(apk) as archive:
        names = [entry for entry in archive.infolist() if entry.filename.startswith('lib/arm64-v8a/') and entry.filename.endswith('.so')]
        for entry in names:
            with archive.open(entry) as source, open(libraries / os.path.basename(entry.filename), 'wb') as target:
                shutil.copyfileobj(source, target, 1 << 20)
        picture = game_icon(archive)
    if not names:
        raise Probleme(tr("Le jeu fabriqué n'a pas ses bibliothèques ARM64."))
    so_files = sorted(libraries.iterdir())
    total, done = (sum((library.stat().st_size for library in so_files)), 0)
    for library in so_files:
        step(APK_SHARE + CONVERSION_SHARE * done / total, tr('Conversion pour iPhone : {name}', name=library.name), STEP_CONVERSION)
        done += library.stat().st_size
        recipe = str(X18_RECIPE) if library.name == 'libunity.so' else None
        try:
            convert.convertir(str(library), str(converted / (library.name[:-3] + '.dylib')), PLATFORM, recipe)
        except SystemExit as error:
            raise Probleme(tr('Conversion de {name} impossible : {error}', name=library.name, error=error))
    app = 'Payload/RangerRumble.app'
    temporary = ipa.with_name(ipa.name + '.tmp')
    start = APK_SHARE + CONVERSION_SHARE
    total = sum((path.stat().st_size for path in [PROGRAM, apk, *converted.iterdir(), *(path for name in FRAMEWORKS for path in tree_files(READY_MADE / name))]))
    copied = 0
    text = tr("Assemblage de l'IPA...")

    def written(size):
        nonlocal copied
        before, copied = (copied, copied + size)
        if int(200 * before / total) != int(200 * copied / total):
            step(start + (1 - start) * min(copied / total, 0.99), text, STEP_IPA)
    step(start, text, STEP_IPA)
    with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED, allowZip64=True) as archive:
        add_file(archive, PROGRAM, f'{app}/RangerRumble', written=written)
        add_bytes(archive, f'{app}/Info.plist', info_plist(game_version))
        if picture:
            for name, data in icons(picture).items():
                add_bytes(archive, f'{app}/{name}', data)
        for library in sorted(converted.iterdir()):
            add_file(archive, library, f'{app}/Frameworks/{library.name}', written=written)
        for framework in FRAMEWORKS:
            add_tree(archive, READY_MADE / framework, f'{app}/Frameworks/{framework}', written=written)
        for library in so_files:
            add_bytes(archive, f'{app}/lib/arm64-v8a/{library.name}', b'')
        for notice in sorted(READY_MADE.glob('*.txt')):
            add_file(archive, notice, f'{app}/{notice.name}')
        add_file(archive, apk, f'{app}/jeu.apk', stored=True, written=written)
    os.replace(temporary, ipa)
    shutil.rmtree(work, ignore_errors=True)
    step(1.0, tr("L'IPA est prête"), STEP_DONE)
