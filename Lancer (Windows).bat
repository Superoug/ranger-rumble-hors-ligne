@echo off
chcp 65001 >nul
setlocal
set "BASE=%LOCALAPPDATA%\sauvegarde-rr"
set "VPY=%BASE%\venv\Scripts\python.exe"
set "FR="
findstr /c:"\"langue\": \"fr\"" "%USERPROFILE%\.sauvegarde-rr\reglages.json" >nul 2>&1 && set "FR=1"
if defined FR (
  set "M_DOWNLOAD=Python manque sur cet ordinateur : telechargement de Python pour l'outil (environ 45 Mo)..."
  set "M_NOPY1=Impossible d'avoir Python. Verifie la connexion Internet et reessaie,"
  set "M_NOPY2=ou installe Python : https://www.python.org/downloads/"
  set "M_NOPY3=(coche Add python.exe to PATH pendant son installation)."
  set "M_FIRST=Premiere utilisation : installation des composants, quelques minutes..."
  set "M_RUN=La fenetre de l'outil s'ouvre. Raccourci sur le Bureau : Launcher Ratchet Ranger Rumble."
  set "M_FAIL=L'installation a echoue. Verifie la connexion Internet et reessaie."
) else (
  set "M_DOWNLOAD=Python is missing on this computer: downloading Python for the tool (about 45 MB)..."
  set "M_NOPY1=Could not get Python. Check the Internet connection and try again,"
  set "M_NOPY2=or install Python: https://www.python.org/downloads/"
  set "M_NOPY3=(tick Add python.exe to PATH while installing it)."
  set "M_FIRST=First use: installing the components, a few minutes..."
  set "M_RUN=The tool's window opens. Shortcut on the Desktop: Launcher Ratchet Ranger Rumble."
  set "M_FAIL=The installation failed. Check the Internet connection and try again."
)

rem New components (another mark) or missing ones: installed again.
set "MARK="
if exist "%BASE%\venv\rr-pret" set /p MARK=<"%BASE%\venv\rr-pret"
if not "%MARK%"=="821fed449874" goto findpython
"%VPY%" -c "import mitmproxy, msgpack, segno, tkinter, UnityPy, numpy, PIL" >nul 2>&1
if not errorlevel 1 goto run

:findpython

set "PY="
for %%C in ("py -3.13" "py -3.12" "py -3.14" "py -3" "python") do if not defined PY (
  %%~C -c "import sys, tkinter; print('rr-ok' if sys.version_info >= (3, 12) else '')" 2>nul | find "rr-ok" >nul && set "PY=%%~C"
)
if defined PY goto install
"%BASE%\python\python.exe" -c "import sys, tkinter; sys.exit(sys.version_info < (3, 12))" >nul 2>&1
if not errorlevel 1 set "PY="%BASE%\python\python.exe""
if defined PY goto install

echo %M_DOWNLOAD%
if not exist "%BASE%" mkdir "%BASE%"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; $f=Join-Path $env:BASE 'python.tar.gz'; Invoke-WebRequest -UseBasicParsing -Uri 'https://github.com/astral-sh/python-build-standalone/releases/download/20261021/cpython-3.13.17%%2B20261021-x86_64-pc-windows-msvc-install_only.tar.gz' -OutFile $f; if ((Get-FileHash $f -Algorithm SHA256).Hash -ne 'E10B46D9B03A3A494297F336770F55F86474D683061137B1CF595E12E47BCEF5') { Remove-Item $f; exit 1 }"
if errorlevel 1 goto nopython
if exist "%BASE%\python" rmdir /s /q "%BASE%\python"
tar -xzf "%BASE%\python.tar.gz" -C "%BASE%"
if errorlevel 1 goto nopython
del "%BASE%\python.tar.gz"
set "PY="%BASE%\python\python.exe""
goto install

:nopython
echo %M_NOPY1%
echo %M_NOPY2%
echo %M_NOPY3%
pause
exit /b 1

:install
echo %M_FIRST%
if exist "%BASE%\venv" rmdir /s /q "%BASE%\venv"
%PY% -m venv "%BASE%\venv"
if errorlevel 1 goto fail
"%VPY%" -m pip install --disable-pip-version-check -q "mitmproxy==12.3.1" "msgpack==1.2.4" "segno==1.6.1" "UnityPy==1.25.4" "numpy==2.5.4" "pillow==13.0.0" >"%BASE%\pip.log" 2>&1
if errorlevel 1 "%VPY%" -I "%~dp0moteur\appli_patch\composants.py"
if errorlevel 1 goto fail
echo 821fed449874>"%BASE%\venv\rr-pret"

:run
set "RR_HERE=%~dp0"
set "RR_APPLI=%~dp0moteur\appli_patch\lanceur_web.py"
set "RR_ENTRY=%~dp0moteur\appli_patch\raccourci.py"
set "RR_ICON=%~dp0moteur\appli_patch\ressources\lanceur\icone.ico"
set "RR_TARGET=%BASE%\venv\Scripts\pythonw.exe"
if not exist "%RR_TARGET%" goto console
rem The shortcut (Desktop and this folder): the window without this black one, with the game's icon
rem (raccourci.py comes back here when the components are missing).
powershell -NoProfile -ExecutionPolicy Bypass -Command "$w=New-Object -ComObject WScript.Shell; $q=[char]34; foreach($d in @([Environment]::GetFolderPath('Desktop'), $env:RR_HERE)){ $l=$w.CreateShortcut((Join-Path $d 'Launcher Ratchet Ranger Rumble.lnk')); $l.TargetPath=$env:RR_TARGET; $l.Arguments='-I '+$q+$env:RR_ENTRY+$q; $l.WorkingDirectory=$env:RR_HERE; $l.IconLocation=$env:RR_ICON+',0'; $l.Description='Launcher Ratchet Ranger Rumble'; $l.Save() }" >nul 2>&1
echo %M_RUN%
start "" "%RR_TARGET%" -I "%RR_APPLI%"
exit /b 0

:console
"%VPY%" -I "%RR_APPLI%"
if errorlevel 1 pause
exit /b 0

:fail
echo %M_FAIL%
pause
exit /b 1
