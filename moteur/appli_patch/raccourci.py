import importlib.util
import os
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
NEEDED = ('mitmproxy', 'msgpack', 'segno', 'UnityPy', 'numpy', 'PIL', 'tkinter')
if not all((importlib.util.find_spec(name) for name in NEEDED)):
    os.startfile(os.path.join(ROOT, 'Lancer (Windows).bat'))
    sys.exit(0)
sys.path.insert(0, HERE)
if os.path.isfile(os.path.join(HERE, 'web', 'index.html')) and os.path.isfile(os.path.join(HERE, 'lanceur_web.py')):
    import lanceur_web
    lanceur_web.main()
else:
    import appli
    appli.main()
