import json
import os
HERE = os.path.dirname(os.path.abspath(__file__))
TABLE_FILE = os.path.join(HERE, 'ressources', 'langues.json')
SETTINGS = os.path.join(os.path.expanduser('~'), '.sauvegarde-rr', 'reglages.json')
LANGUAGES = (('en', 'English'), ('fr', 'Français'), ('es', 'Español'), ('de', 'Deutsch'), ('it', 'Italiano'), ('pt', 'Português'))
DEFAULT = 'en'

def _load(path, default):
    try:
        with open(path, encoding='utf-8') as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return default
TABLE = _load(TABLE_FILE, {})
_chosen = _load(SETTINGS, {}).get('langue')
CURRENT = _chosen if _chosen in dict(LANGUAGES) else DEFAULT

def tr(text, /, **values):
    if CURRENT != 'fr':
        core = text.strip()
        if core:
            lead = text[:len(text) - len(text.lstrip())]
            trail = text[len(text.rstrip()):]
            entry = TABLE.get(core, {})
            text = lead + (entry.get(CURRENT) or entry.get('en') or core) + trail
    return text.format(**values) if values else text

def names_language():
    return 'fr' if CURRENT == 'fr' else 'en'
