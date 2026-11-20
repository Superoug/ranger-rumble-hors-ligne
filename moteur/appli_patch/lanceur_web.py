import os
import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import commun
import service
PROFILE = commun.BASE / 'fenetre_web'

def browser():
    places = []
    for variable in ('PROGRAMFILES(X86)', 'PROGRAMFILES', 'LOCALAPPDATA'):
        root = os.environ.get(variable)
        if root:
            places += [Path(root) / 'Microsoft' / 'Edge' / 'Application' / 'msedge.exe', Path(root) / 'Google' / 'Chrome' / 'Application' / 'chrome.exe']
    places += [Path(p) for p in (shutil.which('msedge'), shutil.which('chrome')) if p]
    edge_first = sorted(places, key=lambda p: p.name != 'msedge.exe')
    return next((str(p) for p in edge_first if p.is_file()), None)

def main():
    server = service.new_server()
    url = f'http://127.0.0.1:{server.server_port}/?jeton={server.key}&fenetre=windows'
    found = browser()
    if found:
        PROFILE.mkdir(parents=True, exist_ok=True)
        quiet = {'creationflags': subprocess.CREATE_NO_WINDOW} if os.name == 'nt' else {}
        subprocess.Popen([found, f'--app={url}', f'--user-data-dir={PROFILE}', '--window-size=1260,840', '--no-first-run', '--no-default-browser-check', '--disable-sync', '--disable-features=Translate,msEdgeSidebarV2,msHubApps'], **quiet)
    else:
        webbrowser.open(url)
    service.serve(server, 'fenetre')
if __name__ == '__main__':
    main()
