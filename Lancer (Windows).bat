@echo off
chcp 65001 >nul
setlocal
set "BASE=%LOCALAPPDATA%\sauvegarde-rr"
set "VPY=%BASE%\venv\Scripts\python.exe"

"%VPY%" -c "import mitmproxy, msgpack, segno, tkinter, UnityPy, numpy, PIL" >nul 2>&1
if not errorlevel 1 goto run

set "PY="
py -3 -c "import sys, tkinter; sys.exit(sys.version_info < (3, 12))" >nul 2>&1
if not errorlevel 1 set "PY=py -3"
if defined PY goto install
python -c "import sys, tkinter; sys.exit(sys.version_info < (3, 12))" >nul 2>&1
if not errorlevel 1 set "PY=python"
if defined PY goto install
echo Il faut Python 3.12 ou plus recent : https://www.python.org/downloads/
echo Pendant son installation, coche la case "Add python.exe to PATH"
echo (et laisse cochee l'option "tcl/tk and IDLE").
pause
exit /b 1

:install
echo Premiere utilisation : installation des composants, quelques minutes...
if exist "%BASE%\venv" rmdir /s /q "%BASE%\venv"
%PY% -m venv "%BASE%\venv"
if errorlevel 1 goto fail
"%VPY%" -m pip install --disable-pip-version-check -q "mitmproxy==12.3.1" "msgpack==1.2.4" "segno==1.6.1" "UnityPy==1.25.4" "numpy==2.5.4" "pillow==13.0.0"
if errorlevel 1 goto fail

:run
echo La fenetre de l'outil s'ouvre. Laisse cette fenetre noire ouverte tant qu'elle sert.
"%VPY%" -I "%~dp0moteur\appli_patch\appli.py"
if errorlevel 1 pause
exit /b 0

:fail
echo L'installation a echoue. Verifie la connexion Internet et reessaie.
pause
exit /b 1
