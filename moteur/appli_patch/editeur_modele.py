import datetime
from pathlib import Path
import copie_android
import sauvegarde as sv
from langues import tr
PACKAGE = copie_android.PACKAGE
PHONE_FOLDER = copie_android.EDITOR_FOLDER
PHONE_SAVE = copie_android.EDITOR_SAVE
PHONE_IMPORT = copie_android.EDITOR_IMPORT
GAME_ACTIVITY = f'{PACKAGE}/com.ohbibi.AndroidActivity.OhbibiUnityPlayerActivity'
ADB_TIMEOUT = 180
HERO_LEVEL_MAX = 10
WEAPON_LEVEL_MAX = 10
TALENTS_MAX = 6
ENHANCEMENT_MAX = 3
INT_MAX = 2 ** 31 - 1
EXTRA_HEROES = {23: 83}
HERO_NAMES = {7: 'Wendy', 23: 'Juycee'}
EXTRA_WEAPONS = {9}
ADDED_MODES = (68, 114, 57)
CURRENCIES = [1, 5, 6, 9, 10, 4, 2]
SHOWN_CURRENCIES = 5
ICONS = Path(__file__).resolve().parent / 'ressources' / 'icones'
TABS = ('profil', 'heros', 'armes', 'costumes', 'modes')
HERO_DATA = {'level': 1, 'lorbs': 3, 'talents': 4}
WEAPON_DATA = {'level': 0, 'enhancement': 1, 'blueprints': 2}
HERO_FREE_KEYS = ('owned', 'medals', 'streak')
WEAPON_FREE_KEYS = ('owned', 'blueprints')
MODE_STATS = {'battles': 0, 'wins': 1, 'losses': 2, 'draws': 3}

class Refus(Exception):
    pass

class NoAdb(Exception):
    pass

def icon(folder: str, key) -> str | None:
    return f'{folder}/{key}' if (ICONS / folder / f'{key}.png').is_file() else None

def columns(tab: str) -> list[tuple]:
    return {'profil': [('name', tr('Valeur'), 360, None), ('value', '', 160, 'int')], 'heros': [('name', tr('Héros'), 200, None), ('owned', tr('Débloqué'), 80, 'bool'), ('level', tr('Niveau'), 70, 'int'), ('talents', tr('Talents'), 70, 'int'), ('lorbs', tr('Lorbes'), 80, 'int'), ('medals', tr('Médailles'), 90, 'int'), ('streak', tr('Série de victoires'), 120, 'int')], 'armes': [('name', tr('Arme'), 220, None), ('owned', tr('Débloquée'), 80, 'bool'), ('level', tr('Niveau'), 70, 'int'), ('enhancement', tr('Améliorations'), 100, 'int'), ('blueprints', tr('Plans'), 90, 'int'), ('equipped', tr('Équipée'), 70, None)], 'costumes': [('hero', tr('Héros'), 160, None), ('name', tr('Costume'), 260, None), ('owned', tr('Possédé'), 80, 'bool'), ('equipped', tr('Porté'), 70, None)], 'modes': [('name', tr('Mode'), 240, None), ('owned', tr('Débloqué'), 80, 'bool'), ('battles', tr('Jouées'), 80, 'int'), ('wins', tr('Gagnées'), 80, 'int'), ('losses', tr('Perdues'), 80, 'int'), ('draws', tr('Égalités'), 80, 'int')]}[tab]

class Row:

    def __init__(self, values: dict, setter=None, bounds: dict | None=None, editable=None):
        self.values, self.setter, self._bounds, self._editable = (values, setter, bounds or {}, editable)

    def get(self, key: str):
        return self.values.get(key)

    def set(self, key: str, value) -> None:
        self.setter(key, value)

    def bounds(self, key: str) -> tuple[int, int]:
        return self._bounds.get(key, (0, INT_MAX))

    def editable(self, key: str) -> bool:
        return self.setter is not None and (self._editable is None or self._editable(key))

def item(values: list, index: int, missing=0):
    return values[index] if index < len(values) else missing

def pad(values: list, size: int, fill=0) -> None:
    while len(values) < size:
        values.append(fill)

def number_lists(part: list, indexes, size: int) -> None:
    for index in indexes:
        if part[index] is None:
            part[index] = []
        pad(part[index], size)

def value_at_path(value, path, missing):
    try:
        for key in path:
            value = value[key]
    except (TypeError, IndexError, KeyError):
        return missing
    return value

def set_at_path(target, path, new) -> None:
    for key in path[:-1]:
        while isinstance(target, list) and len(target) <= key:
            target.append(None)
        if target[key] is None:
            target[key] = []
        target = target[key]
    while isinstance(target, list) and len(target) <= path[-1]:
        target.append(0)
    target[path[-1]] = new

def currency_values(save: sv.Save) -> list:
    currencies = save.part('MainCurrencies', create=False)
    return (currencies or [[]])[0] or []

def hero_medals(save: sv.Save) -> list:
    medals = save.part('MedalRunState', create=False)
    return (medals[2] if medals and len(medals) > 2 else None) or []

def now_stamp() -> str:
    return f'{datetime.datetime.now():%Y-%m-%d_%H%M%S}'

def adb_text(adb: str, serial: str, *args) -> str:
    _, out, err = copie_android.run(adb, '-s', serial, *args, timeout=ADB_TIMEOUT)
    return out + err

def adb_ok(adb: str, serial: str, *args) -> bool:
    return copie_android.run(adb, '-s', serial, *args, timeout=ADB_TIMEOUT)[0] == 0

def find_phone(need_game: bool=True, adb: str | None=None) -> tuple[str, str]:
    adb = adb or copie_android.find_adb()
    if not adb:
        raise NoAdb()
    listed = copie_android.phones(adb)
    ready = sorted((p for p in listed if p[1] == 'device'), key=lambda p: p[0].startswith('emulator-'))
    if not ready:
        if any((p[1] == 'unauthorized' for p in listed)):
            raise Refus(tr('Toucher « Autoriser » sur le téléphone, puis recommencer.'))
        raise Refus(tr("Aucun téléphone trouvé. Activer le débogage USB et mettre l'USB en « Transfert de fichiers », puis recommencer."))
    if not need_game:
        return (adb, ready[0][0])
    for serial, _, _ in ready:
        if has_game(adb, serial):
            return (adb, serial)
    raise Refus(tr("Le jeu n'est pas sur ce téléphone."))

def has_game(adb: str, serial: str) -> bool:
    return PACKAGE in adb_text(adb, serial, 'shell', 'pm', 'list', 'packages', PACKAGE)

def pull_phone_save(adb: str, serial: str, copies) -> Path:
    listing = adb_text(adb, serial, 'shell', 'ls', PHONE_SAVE)
    if 'No such file' in listing or PHONE_SAVE not in listing:
        raise Refus(tr('Ouvrir le jeu une fois sur le téléphone, puis recommencer.'))
    local = Path(copies) / f'TELEPHONE_{now_stamp()}.msgpack'
    local.parent.mkdir(parents=True, exist_ok=True)
    adb_ok(adb, serial, 'pull', PHONE_SAVE, str(local))
    if not local.is_file():
        raise Refus(tr("La sauvegarde du téléphone n'a pas pu être lue."))
    return local

def push_save(adb: str, serial: str, data: bytes, copies) -> Path:
    sv.Save(data)
    local = Path(copies) / f'ENVOYEE_{now_stamp()}.msgpack'
    local.parent.mkdir(parents=True, exist_ok=True)
    local.write_bytes(data)
    if PHONE_FOLDER not in adb_text(adb, serial, 'shell', 'ls', '-d', PHONE_FOLDER):
        raise Refus(tr('Ouvrir le jeu une fois sur le téléphone, puis recommencer.'))
    adb_ok(adb, serial, 'shell', 'am', 'force-stop', PACKAGE)
    adb_ok(adb, serial, 'push', str(local), PHONE_IMPORT + '.tmp')
    adb_ok(adb, serial, 'shell', 'mv', PHONE_IMPORT + '.tmp', PHONE_IMPORT)
    check = adb_text(adb, serial, 'shell', 'ls', '-l', PHONE_IMPORT)
    if str(len(data)) not in check:
        raise Refus(tr("La sauvegarde n'a pas pu être posée sur le téléphone."))
    adb_ok(adb, serial, 'shell', 'am', 'start', '-n', GAME_ACTIVITY)
    return local

class Model:

    def __init__(self):
        self.save = None
        self.raw = None
        self.source = None

    def load(self, raw: bytes, source) -> None:
        try:
            save = sv.Save(raw)
        except Exception as error:
            raise ValueError(tr("Ce fichier n'est pas une sauvegarde lisible de Ranger Rumble :\n\n{error}", error=error)) from error
        self.save, self.raw, self.source = (save, raw, source)

    def changes(self) -> list[str]:
        return self.save.changed() if self.save is not None else []

    def mark_saved(self, where) -> None:
        self.raw = self.save.to_bytes()
        self.save = sv.Save(self.raw)
        self.source = where

    def revert(self) -> None:
        self.save = sv.Save(self.raw)

    def nickname(self):
        identity = self.save.part('UserIdentity', create=False)
        return identity[0] if identity else None

    def summary(self) -> dict:
        s = self.save
        values = currency_values(s)
        money = [{'id': c, 'name': sv.name_of('CURRENCY', c), 'icon': icon('monnaies', c), 'value': item(values, c)} for c in CURRENCIES[:SHOWN_CURRENCIES]]
        counts = [{'key': key, 'label': label, 'owned': len(s.existing_collection(part)), 'total': total} for key, label, part, total in (('heros', tr('Héros'), 'UnlockedHeroes', len(self.heroes())), ('armes', tr('Armes'), 'UnlockedWeapons', len(self.weapon_ids())), ('costumes', tr('Costumes'), 'UnlockedSkins', None))]
        return {'nickname': self.nickname(), 'currencies': money, 'counts': counts}

    def rows(self, tab: str) -> list[Row]:
        if self.save is None:
            return []
        return {'profil': self.profile_rows, 'heros': self.hero_rows, 'armes': self.weapon_rows, 'costumes': self.skin_rows, 'modes': self.mode_rows}[tab]()

    def field_row(self, part: str, path: list, label: str, low: int=0, high: int=INT_MAX, text: bool=False, picture: str | None=None) -> Row:
        current = value_at_path(self.save.part(part, create=False), path, '' if text else 0)

        def setter(_, new):
            set_at_path(self.save.part(part), path, new)
        return Row({'name': label, 'value': current, 'icon': icon('ui', picture) if picture else None}, setter, {'value': (low, high)})

    def profile_rows(self) -> list[Row]:
        battle = self.save.part('BattleInfo', create=False)
        played = battle[0] if battle else 0
        won = battle[1] if battle else 0
        field = self.field_row
        return [field('UserIdentity', [0], tr('Pseudo'), text=True, picture='pseudo'), *self.currency_rows(), field('BattleInfo', [0], tr('Parties jouées'), picture='jouees'), field('BattleInfo', [1], tr('Parties gagnées'), picture='gagnees'), Row({'name': tr('Parties perdues'), 'value': max(0, played - won), 'icon': icon('ui', 'perdues')}, self.set_lost), field('BattleInfo', [6], tr("Victoires aujourd'hui"), picture='jour_gagnees'), field('BattleInfo', [7], tr("Défaites aujourd'hui"), picture='jour_perdues'), field('BattleInfo', [2, 3], tr('Série de victoires en cours'), picture='serie'), field('BattleInfo', [2, 2], tr('Meilleure série de victoires'), picture='meilleure_serie'), field('BattleInfo', [5], tr('Difficulté des bots (0 à 100)'), 0, 100, picture='bots'), Row({'name': tr('Médailles (actuelles)'), 'value': sum(hero_medals(self.save)), 'icon': icon('ui', 'medailles')}, lambda _, new: self.set_total_medals(new), {'value': (0, 10 ** 7)}), field('MedalRunState', [7], tr('Médailles (record)'), picture='medailles'), field('MedalRunState', [8], tr('Ranger Road : récompenses prises'), picture='route'), field('MedalRunState', [4], tr('Médailles bonus'), picture='medailles_bonus'), self.siege_row()]

    def currency_rows(self) -> list[Row]:
        values = currency_values(self.save)
        return [Row({'name': sv.name_of('CURRENCY', currency), 'icon': icon('monnaies', currency), 'value': item(values, currency)}, lambda _, new, currency=currency: self.set_currency(currency, new)) for currency in CURRENCIES]

    def set_currency(self, currency: int, value: int) -> None:
        part = self.save.part('MainCurrencies')
        number_lists(part, (0, 3, 4), currency + 1)
        part[0][currency] = value

    def set_lost(self, _, value: int) -> None:
        part = self.save.part('BattleInfo')
        part[0] = part[1] + value

    def siege_row(self) -> Row:
        siege = self.save.part('GameModeProgression', create=False)
        stats = siege[2] if isinstance(siege, list) and len(siege) > 2 and isinstance(siege[2], list) else None
        reached = stats[0] if stats and isinstance(stats[0], int) else 0
        return Row({'name': tr('Invasion : niveau atteint'), 'value': max(0, reached), 'icon': icon('ui', 'invasion')}, self.set_siege, {'value': (0, 999)})

    def set_siege(self, _, value: int) -> None:
        part = self.save.part('GameModeProgression')
        pad(part, 3, None)
        if not isinstance(part[2], list) or len(part[2]) < 6:
            part[2] = [0, -1, 0, -1, 0, -1]
        part[2][0] = part[2][2] = part[2][4] = value
        part[2][1] = part[2][3] = part[2][5] = -1

    @staticmethod
    def heroes() -> list[tuple[int, int]]:
        found = [(c, sv.hero_unlockable(c)) for c in sv.CHARACTERS if c != 1]
        found += list(EXTRA_HEROES.items())
        return [(c, u) for c, u in found if u is not None]

    def hero_rows(self) -> list[Row]:
        s = self.save
        owned = {e[0]: e for e in s.existing_collection('UnlockedHeroes')}
        medals = hero_medals(s)
        battle = s.part('BattleInfo', create=False)
        streaks = (battle[2][4] if battle and battle[2] and (len(battle[2]) > 4) else None) or {}
        rows = []
        for character, unlockable in self.heroes():
            if unlockable in EXTRA_HEROES.values() and unlockable not in owned:
                continue
            entry = owned.get(unlockable)
            data = entry[1] or [] if entry else []
            values = {'name': HERO_NAMES.get(character) or sv.name_of('CHARACTER_ID', character), 'owned': entry is not None, 'icon': icon('heros', character), 'level': item(data, 1, 0) + 1 if entry else None, 'talents': item(data, 4) if entry else None, 'lorbs': item(data, 3) if entry else None, 'medals': item(medals, character), 'streak': streaks.get(character, 0)}
            rows.append(Row(values, lambda key, new, c=character, u=unlockable: self.set_hero(c, u, key, new), {'level': (1, HERO_LEVEL_MAX), 'talents': (0, TALENTS_MAX), 'lorbs': (0, 10 ** 7), 'medals': (0, 10 ** 6), 'streak': (0, 10 ** 6)}, editable=lambda key, owned=entry is not None: owned or key in HERO_FREE_KEYS))
        return rows

    def set_hero(self, character: int, unlockable: int, key: str, value) -> None:
        heroes = self.save.collection('UnlockedHeroes')
        entry = next((e for e in heroes if e[0] == unlockable), None)
        if key == 'owned':
            self.set_hero_owned(character, unlockable, heroes, entry, value)
        elif key == 'medals':
            self.set_hero_medals(character, value)
        elif key == 'streak':
            self.set_hero_streak(character, value)
        elif entry is not None:
            if entry[1] is None:
                entry[1] = []
            index = HERO_DATA[key]
            pad(entry[1], index + 1)
            entry[1][index] = value - 1 if key == 'level' else value

    def set_hero_owned(self, character: int, unlockable: int, heroes: list, entry, owned: bool) -> None:
        skins = self.save.collection('UnlockedSkins')
        if owned and entry is None:
            heroes.append([unlockable, [0, 0, 0, 0]])
            if unlockable not in skins:
                skins.append(unlockable)
        elif not owned and entry is not None:
            hero_skins = {u for u, _ in sv.skins_of(character)} | {unlockable}
            if any((slot in hero_skins for slot in self.save.existing_collection('EquippedSkins'))):
                raise Refus(tr("C'est le héros choisi dans le jeu : il faut en choisir un autre dans le jeu avant de le retirer."))
            if len(heroes) <= 1:
                raise Refus(tr('Il faut garder au moins un héros.'))
            heroes.remove(entry)
            skins[:] = [skin for skin in skins if skin not in hero_skins]

    def set_hero_medals(self, character: int, value: int) -> None:
        part = self.save.part('MedalRunState')
        number_lists(part, (2, 6), character + 1)
        part[2][character] = value
        part[7] = max(part[7] or 0, sum(part[2]))

    def set_hero_streak(self, character: int, value: int) -> None:
        part = self.save.part('BattleInfo')
        if part[2][4] is None:
            part[2][4] = {}
        part[2][4][character] = value
        part[2][2] = max(part[2][2] or 0, value)

    def set_total_medals(self, total: int) -> None:
        part = self.save.part('MedalRunState')
        owned = {e[0] for e in self.save.existing_collection('UnlockedHeroes')}
        characters = [c for c, u in self.heroes() if u in owned] or [c for c, _ in self.heroes()][:1]
        size = max([len(part[2] or []), len(part[6] or [])] + [c + 1 for c in characters])
        number_lists(part, (2, 6), size)
        medals = part[2]
        change = total - sum(medals)
        if change > 0:
            richest = max(characters or range(len(medals)), key=lambda c: medals[c])
            medals[richest] += change
        while change < 0:
            richest = max(range(len(medals)), key=lambda c: medals[c])
            taken = min(medals[richest], -change)
            medals[richest] -= taken
            change += taken
        part[7] = max(part[7] or 0, sum(medals))

    def all_heroes(self) -> None:
        for character, unlockable in self.heroes():
            if unlockable not in EXTRA_HEROES.values():
                self.set_hero(character, unlockable, 'owned', True)

    @staticmethod
    def max_heroes(rows: list[Row]) -> None:
        if not rows:
            raise Refus(tr("Sélectionner d'abord des héros dans la liste (clic, Maj+clic ou Cmd/Ctrl+clic)."))
        for row in rows:
            if row.get('owned'):
                row.set('level', HERO_LEVEL_MAX)
                row.set('talents', TALENTS_MAX)

    def weapon_ids(self) -> list[int]:
        ids = [w for w, _ in sv.weapons()] + sorted(EXTRA_WEAPONS)
        if self.save is not None:
            ids += [e[0] for e in self.save.existing_collection('UnlockedWeapons') if e[0] not in ids]
        return ids

    def weapon_rows(self) -> list[Row]:
        s = self.save
        owned = {e[0]: e for e in s.existing_collection('UnlockedWeapons')}
        status = s.part('WeaponsStatus', create=False)
        locked = (status[0] if status else None) or {}
        loadout = set(s.existing_collection('WeaponLoadoutByUID'))
        rows = []
        for weapon in self.weapon_ids():
            entry = owned.get(weapon)
            data = entry[1] or [] if entry else []
            values = {'name': sv.name_of('UNLOCKABLE_ID', weapon), 'owned': entry is not None, 'icon': icon('armes', weapon), 'level': item(data, 0, 0) + 1 if entry else None, 'enhancement': item(data, 1) if entry else None, 'blueprints': item(data, 2) if entry else locked.get(weapon, 0), 'equipped': tr('oui') if weapon in loadout else ''}
            rows.append(Row(values, lambda key, new, w=weapon: self.set_weapon(w, key, new), {'level': (1, WEAPON_LEVEL_MAX), 'enhancement': (0, ENHANCEMENT_MAX), 'blueprints': (0, 10 ** 7)}, editable=lambda key, owned=entry is not None: owned or key in WEAPON_FREE_KEYS))
        return rows

    def set_weapon(self, weapon: int, key: str, value) -> None:
        weapons = self.save.collection('UnlockedWeapons')
        entry = next((e for e in weapons if e[0] == weapon), None)
        if key == 'owned':
            self.set_weapon_owned(weapon, weapons, entry, value)
        elif entry is None:
            if key == 'blueprints':
                self.set_locked_blueprints(weapon, value)
        else:
            if entry[1] is None:
                entry[1] = []
            index = WEAPON_DATA[key]
            pad(entry[1], index + 1)
            entry[1][index] = value - 1 if key == 'level' else value

    def set_weapon_owned(self, weapon: int, weapons: list, entry, owned: bool) -> None:
        if owned and entry is None:
            status = self.save.part('WeaponsStatus')
            blueprints = status[0].pop(weapon, 0) if status[0] else 0
            weapons.append([weapon, [0, 0, blueprints] if blueprints else []])
        elif not owned and entry is not None:
            if weapon in self.save.existing_collection('WeaponLoadoutByUID'):
                raise Refus(tr('Cette arme est équipée : il faut en équiper une autre dans le jeu avant de la retirer.'))
            weapons.remove(entry)

    def set_locked_blueprints(self, weapon: int, value: int) -> None:
        status = self.save.part('WeaponsStatus')
        if status[0] is None:
            status[0] = {}
        if value:
            status[0][weapon] = value
        else:
            status[0].pop(weapon, None)

    def all_weapons(self) -> None:
        for weapon in self.weapon_ids():
            if weapon not in EXTRA_WEAPONS:
                self.set_weapon(weapon, 'owned', True)

    @staticmethod
    def max_weapons(rows: list[Row]) -> None:
        if not rows:
            raise Refus(tr("Sélectionner d'abord des armes dans la liste (clic, Maj+clic ou Cmd/Ctrl+clic)."))
        for row in rows:
            if row.get('owned'):
                row.set('level', WEAPON_LEVEL_MAX)
                row.set('enhancement', ENHANCEMENT_MAX)

    def skin_rows(self) -> list[Row]:
        s = self.save
        owned = set(s.existing_collection('UnlockedSkins'))
        worn = set(s.existing_collection('EquippedSkins'))
        rows = []
        for character in sorted(sv.CHARACTERS):
            if character in (1, 7):
                continue
            for skin, code in sv.skins_of(character):
                if code.endswith('_SKIN00') or code.endswith('_DEPRECATED'):
                    continue
                rows.append(Row({'hero': sv.name_of('CHARACTER_ID', character), 'name': sv.name_of('UNLOCKABLE_ID', skin), 'icon': icon('costumes', skin), 'owned': skin in owned, 'equipped': tr('oui') if skin in worn else ''}, lambda key, new, k=skin: self.set_skin(k, new)))
        return rows

    def set_skin(self, skin: int, value: bool) -> None:
        skins = self.save.collection('UnlockedSkins')
        if value and skin not in skins:
            skins.append(skin)
        elif not value and skin in skins:
            if skin in set(self.save.collection('EquippedSkins')):
                raise Refus(tr('Ce costume est porté : il faut changer de costume dans le jeu avant de le retirer.'))
            skins.remove(skin)

    def all_skins(self) -> None:
        for row in self.skin_rows():
            if not row.get('owned'):
                row.set('owned', True)

    def mode_rows(self) -> list[Row]:
        s = self.save
        owned = set(s.existing_collection('UnlockedGameModes'))
        progression = s.part('GameModeProgression', create=False)
        stats = (progression[1] if progression and len(progression) > 1 else None) or {}
        modes = [(int(v), n) for v, n in sv.SCHEMA['enums']['UNLOCKABLE_ID'].items() if n.startswith('GAME_MODE_')]
        rows = []
        for mode, code in modes:
            if code.endswith('_DEPRECATED') and mode not in owned and (mode not in ADDED_MODES):
                continue
            entry = stats.get(mode) or [0, 0, 0, 0]
            rows.append(Row({'name': sv.name_of('UNLOCKABLE_ID', mode), 'owned': mode in owned, 'battles': entry[0], 'icon': icon('modes', mode), 'wins': entry[1], 'losses': entry[2], 'draws': item(entry, 3)}, lambda key, new, m=mode: self.set_mode(m, key, new)))
        return rows

    def set_mode(self, mode: int, key: str, value) -> None:
        s = self.save
        if key == 'owned':
            modes = s.collection('UnlockedGameModes')
            if value and mode not in modes:
                modes.append(mode)
            elif not value and mode in modes:
                modes.remove(mode)
            return
        part = s.part('GameModeProgression')
        if part[1] is None:
            part[1] = {}
        entry = part[1].setdefault(mode, [0, 0, 0, 0])
        pad(entry, 4)
        entry[MODE_STATS[key]] = value

    def value_at(self, part: str, path):
        value = self.save.values[part]
        for key in path:
            value = value[key]
        return value

    @staticmethod
    def show(value, what: str, detail) -> tuple[str, bool]:
        if value is None:
            return (tr('(vide)'), False)
        if what == 'object':
            return ('', True)
        if what in ('list', 'map'):
            return (tr('{n} élément(s)', n=len(value)), len(value) > 0)
        if what == 'enum':
            return (f'{sv.name_of(detail, value)}  ({value})', False)
        if what == 'bytes':
            return (value.hex() if len(value) <= 32 else tr('{n} octets', n=len(value)), False)
        if isinstance(value, (list, dict)):
            return (tr('{n} élément(s)', n=len(value)), len(value) > 0)
        return (repr(value) if isinstance(value, str) else str(value), False)

    def node(self, part: str, path, kind: str, label: str) -> dict:
        value = self.value_at(part, path)
        what, detail = sv.describe(kind)
        text, children = self.show(value, what, detail)
        return {'label': label, 'part': part, 'path': list(path), 'kind': kind, 'text': text, 'children': children}

    def roots(self) -> list[dict]:
        return [self.node(part, (), self.save.part_type(part) or '?', part) for part in sorted(self.save.values)]

    def children(self, part: str, path, kind: str) -> list[dict]:
        path = tuple(path)
        value = self.value_at(part, path)
        what, detail = sv.describe(kind)
        if what == 'object' and isinstance(value, (list, dict)):
            known = {k: (n, t) for k, n, t in sv.fields(detail)}
            if isinstance(value, list):
                labelled = [(index, f'[{index}]') for index in range(len(value))]
            else:
                labelled = [(key, str(key)) for key in value]
            found = []
            for key, label in labelled:
                name, item_kind = known.get(key, (label, '?'))
                found.append(self.node(part, path + (key,), item_kind, name))
            return found
        if what == 'list' or (what not in ('map', 'object') and isinstance(value, list)):
            item_kind = detail if what == 'list' else '?'
            return [self.node(part, path + (index,), item_kind, f'[{index}]') for index in range(len(value))]
        if isinstance(value, dict):
            key_kind, item_kind = detail if what == 'map' else ('?', '?')
            key_what, key_detail = sv.describe(key_kind)
            return [self.node(part, path + (key,), item_kind, sv.name_of(key_detail, key) if key_what == 'enum' else str(key)) for key in value]
        return []

    def set_at(self, part: str, path, new) -> None:
        self.value_at(part, tuple(path)[:-1])[path[-1]] = new

    @staticmethod
    def add_item(target: list, kind: str) -> None:
        target.append(sv.default(kind))

    @staticmethod
    def add_key(target: dict, key, item_kind: str) -> None:
        if key in target:
            raise Refus(tr('Cette clé existe déjà.'))
        target[key] = sv.default(item_kind)

    @staticmethod
    def remove_item(parent, key) -> None:
        if isinstance(parent, list):
            del parent[key]
        else:
            parent.pop(key, None)
