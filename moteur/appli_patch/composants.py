import glob
import importlib
import os
import shutil
import subprocess
import sys
import sysconfig
import tempfile
import zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from langues import tr
COMPONENTS = ['mitmproxy==12.3.1', 'msgpack==1.2.4', 'segno==1.6.1', 'numpy==2.5.4', 'pillow==13.0.0']
UNITYPY = 'UnityPy==1.25.4'
UNITYPY_NEEDS = ['brotli', 'texture2ddecoder>=1.0.5', 'etcpak', 'astc-encoder-py>=0.1.12', 'fmod_toolkit', 'fsspec', 'attrs', 'tpk_ar']

def pip(*args) -> bool:
    return subprocess.run([sys.executable, '-m', 'pip', '--disable-pip-version-check', *args]).returncode == 0

def lz4_in(site: str) -> None:
    try:
        import lz4.block
    except ImportError:
        shutil.copytree(os.path.join(HERE, 'lz4_pur', 'lz4'), os.path.join(site, 'lz4'), dirs_exist_ok=True)

def unitypy_in(site: str) -> bool:
    with tempfile.TemporaryDirectory() as work:
        for minor in range(sys.version_info[1] - 1, 11, -1):
            if pip('download', '-q', '--no-deps', '--only-binary', ':all:', '--python-version', f'3.{minor}', '-d', work, UNITYPY):
                break
        wheels = glob.glob(os.path.join(work, '*.whl'))
        if not wheels:
            return False
        with zipfile.ZipFile(wheels[0]) as wheel:
            wheel.extractall(site)
    return True

def main() -> int:
    site = sysconfig.get_paths()['purelib']
    print(tr('Autre installation des composants (sans compilateur)...'), flush=True)
    if not pip('install', '-q', '--prefer-binary', *COMPONENTS, *UNITYPY_NEEDS):
        return 1
    lz4_in(site)
    if not unitypy_in(site):
        return 1
    importlib.invalidate_caches()
    try:
        import UnityPy
    except Exception as error:
        print(f'UnityPy : {error}')
        return 1
    return 0
if __name__ == '__main__':
    sys.exit(main())
