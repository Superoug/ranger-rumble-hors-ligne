import base64
import json
import os
import subprocess
import sys
QUIET = {'creationflags': subprocess.CREATE_NO_WINDOW} if os.name == 'nt' else {}
RULE = 'Ranger Rumble hors ligne'

def programs() -> list[str]:
    found = []
    for path in (getattr(sys, '_base_executable', None), sys.executable):
        if not path:
            continue
        for name in ('python.exe', 'pythonw.exe'):
            candidate = os.path.join(os.path.dirname(path), name)
            if os.path.isfile(candidate) and candidate.lower() not in (f.lower() for f in found):
                found.append(candidate)
    return found

def quoted(paths) -> str:
    return ','.join(("'" + path.replace("'", "''") + "'" for path in paths))

def powershell(script: str, timeout: int=60) -> str:
    done = subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command', script], capture_output=True, text=True, timeout=timeout, **QUIET)
    return done.stdout
CHECK = '\n$ErrorActionPreference = \'SilentlyContinue\'\n$progs = @(@PROGRAMS@)\n$nets = @(Get-NetConnectionProfile | ForEach-Object { @{name = "$($_.Name)"; category = "$($_.NetworkCategory)"} })\n$walls = @(Get-NetFirewallProfile | ForEach-Object { @{name = "$($_.Name)"; enabled = "$($_.Enabled)"} })\n$rules = @(Get-NetFirewallApplicationFilter | Where-Object { $p = $_.Program; @($progs | Where-Object { $_ -ieq $p }).Count -gt 0 } |\n  Get-NetFirewallRule | Where-Object { "$($_.Direction)" -eq \'Inbound\' -and "$($_.Enabled)" -eq \'True\' } |\n  ForEach-Object { @{action = "$($_.Action)"; profile = "$($_.Profile)"} })\nConvertTo-Json -Compress -Depth 4 @{networks = $nets; walls = $walls; rules = $rules}\n'
FIX = '\n$progs = @(@PROGRAMS@)\nGet-NetFirewallApplicationFilter | Where-Object { $p = $_.Program; @($progs | Where-Object { $_ -ieq $p }).Count -gt 0 } |\n  Get-NetFirewallRule | Where-Object { "$($_.Direction)" -eq \'Inbound\' -and "$($_.Action)" -eq \'Block\' } |\n  Disable-NetFirewallRule\nRemove-NetFirewallRule -DisplayName \'@RULE@\' -ErrorAction SilentlyContinue\nforeach ($p in $progs) {\n  New-NetFirewallRule -DisplayName \'@RULE@\' -Direction Inbound -Program $p -Action Allow -Profile Any -RemoteAddress LocalSubnet | Out-Null\n}\n'
PROFILES = {'DomainAuthenticated': 'Domain'}

def covers(rule_profiles: str, profile: str) -> bool:
    return rule_profiles == 'Any' or profile in rule_profiles

def blocked(found: dict) -> bool:
    walls = {wall.get('name'): wall.get('enabled') == 'True' for wall in found.get('walls') or []}
    rules = found.get('rules') or []

    def any_rule(action, profile):
        return any((rule.get('action') == action and covers(rule.get('profile', ''), profile) for rule in rules))
    for network in found.get('networks') or []:
        profile = PROFILES.get(network.get('category'), network.get('category'))
        if not walls.get(profile, True):
            continue
        if any_rule('Block', profile) or not any_rule('Allow', profile):
            return True
    return False

def check() -> bool | None:
    if os.name != 'nt':
        return False
    try:
        out = powershell(CHECK.replace('@PROGRAMS@', quoted(programs())))
        found = json.loads(out) if out.strip() else None
    except (OSError, ValueError, subprocess.SubprocessError):
        return None
    return blocked(found) if isinstance(found, dict) else None

def fix() -> bool:
    script = FIX.replace('@PROGRAMS@', quoted(programs())).replace('@RULE@', RULE)
    encoded = base64.b64encode(script.encode('utf-16-le')).decode()
    try:
        powershell(f"try {{ Start-Process powershell -Verb RunAs -Wait -WindowStyle Hidden -ArgumentList '-NoProfile','-EncodedCommand','{encoded}'; 'ok' }} catch {{ 'refus' }}", timeout=300)
    except (OSError, subprocess.SubprocessError):
        return False
    return check() is False
