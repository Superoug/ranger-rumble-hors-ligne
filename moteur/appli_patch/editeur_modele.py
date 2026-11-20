import datetime
from pathlib import Path
import copie_android
import sauvegarde as sv
from langues import tr
PACKAGE = copie_android.PACKAGE
PHONE_FOLDER = f'/sdcard/Android/data/{PACKAGE}/files/rr_editeur'
PHONE_SAVE = PHONE_FOLDER + '/sauvegarde_actuelle.msgpack'
PHONE_IMPORT = PHONE_FOLDER + '/a_importer.msgpack'
GAME_ACTIVITY = f'{PACKAGE}/com.ohbibi.AndroidActivity.OhbibiUnityPlayerActivity'
HERO_LEVEL_MAX = 10
WEAPON_LEVEL_MAX = 10
TALENTS_MAX = 6
ENHANCEMENT_MAX = 3
EXTRA_HEROES = {23: 83}
HERO_NAMES = {7: 'Wendy', 23: 'Juycee'}
EXTRA_WEAPONS = {9}
CURRENCIES = [1, 5, 6, 9, 10, 4, 2]
ICONS = Path(__file__).resolve().parent / 'ressources' / 'icones'
TABS = ('profil', 'heros', 'armes', 'costumes', 'modes')

class Refus(Exception):
    pass

class NoAdb(Exception):
    pass

def icon(folder, key):
    return f'{folder}/{key}' if (ICONS / folder / f'{key}.png').is_file() else None

def name(enum, value):
    return sv.name_of(enum, value)

def columns(tab):
    return {'profil': [('name', tr('Valeur'), 360, None), ('value', '', 160, 'int')], 'heros': [('name', tr('Héros'), 200, None), ('owned', tr('Débloqué'), 80, 'bool'), ('level', tr('Niveau'), 70, 'int'), ('talents', tr('Talents'), 70, 'int'), ('lorbs', tr('Lorbes'), 80, 'int'), ('medals', tr('Médailles'), 90, 'int'), ('streak', tr('Série de victoires'), 120, 'int')], 'armes': [('name', tr('Arme'), 220, None), ('owned', tr('Débloquée'), 80, 'bool'), ('level', tr('Niveau'), 70, 'int'), ('enhancement', tr('Améliorations'), 100, 'int'), ('blueprints', tr('Plans'), 90, 'int'), ('equipped', tr('Équipée'), 70, None)], 'costumes': [('hero', tr('Héros'), 160, None), ('name', tr('Costume'), 260, None), ('owned', tr('Possédé'), 80, 'bool'), ('equipped', tr('Porté'), 70, None)], 'modes': [('name', tr('Mode'), 240, None), ('owned', tr('Débloqué'), 80, 'bool'), ('battles', tr('Jouées'), 80, 'int'), ('wins', tr('Gagnées'), 80, 'int'), ('losses', tr('Perdues'), 80, 'int'), ('draws', tr('Égalités'), 80, 'int')]}[tab]

class Row:

    def __init__(self, values, setter=None, bounds=None, editable=None):
        self.values, self.setter, self._bounds, self._editable = (values, setter, bounds or {}, editable)

    def get(self, key):
        return self.values.get(key)

    def set(self, key, value):
        self.setter(key, value)

    def bounds(self, key):
        return self._bounds.get(key, (0, 2 ** 31 - 1))

    def editable(self, key):
        return self.setter is not None and (self._editable is None or self._editable(key))

def adb_text(adb, serial, *args):
    _, out, err = copie_android.run(adb, '-s', serial, *args, timeout=180)
    return out + err

def adb_ok(adb, serial, *args):
    return copie_android.run(adb, '-s', serial, *args, timeout=180)[0] == 0

def find_phone(need_game=True, adb=None):
    adb = adb or copie_android.find_adb()
    if not adb:
        raise NoAdb()
    listed = copie_android.phones(adb)
    ready = sorted((p for p in listed if p[1] == 'device'), key=lambda p: p[0].startswith('emulator-'))
    if not ready:
        if any((p[1] == 'unauthorized' for p in listed)):
            raise Refus(tr('Touche « Autoriser » sur le téléphone, puis recommence.'))
        raise Refus(tr("Aucun téléphone trouvé. Active le débogage USB et mets l'USB en « Transfert de fichiers », puis recommence."))
    if not need_game:
        return (adb, ready[0][0])
    for serial, _, _ in ready:
        if has_game(adb, serial):
            return (adb, serial)
    raise Refus(tr("Le jeu n'est pas sur ce téléphone."))

def has_game(adb, serial):
    return PACKAGE in adb_text(adb, serial, 'shell', 'pm', 'list', 'packages', PACKAGE)

def pull_phone_save(adb, serial, copies):
    listing = adb_text(adb, serial, 'shell', 'ls', PHONE_SAVE)
    if 'No such file' in listing or PHONE_SAVE not in listing:
        raise Refus(tr('Ouvre le jeu une fois sur le téléphone, puis recommence.'))
    local = Path(copies) / f'TELEPHONE_{datetime.datetime.now():%Y-%m-%d_%H%M%S}.msgpack'
    local.parent.mkdir(parents=True, exist_ok=True)
    adb_ok(adb, serial, 'pull', PHONE_SAVE, str(local))
    if not local.is_file():
        raise Refus(tr("La sauvegarde du téléphone n'a pas pu être lue."))
    return local

def push_save(adb, serial, data, copies):
    sv.Save(data)
    local = Path(copies) / f'ENVOYEE_{datetime.datetime.now():%Y-%m-%d_%H%M%S}.msgpack'
    local.parent.mkdir(parents=True, exist_ok=True)
    local.write_bytes(data)
    if PHONE_FOLDER not in adb_text(adb, serial, 'shell', 'ls', '-d', PHONE_FOLDER):
        raise Refus(tr('Ouvre le jeu une fois sur le téléphone, puis recommence.'))
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

    def load(self, raw, source):
        try:
            save = sv.Save(raw)
        except Exception as error:
            raise ValueError(tr("Ce fichier n'est pas une sauvegarde lisible de Ranger Rumble :\n\n{error}", error=error)) from error
        self.save, self.raw, self.source = (save, raw, source)

    def changes(self):
        return self.save.changed() if self.save is not None else []

    def mark_saved(self, where):
        self.raw = self.save.to_bytes()
        self.save = sv.Save(self.raw)
        self.source = where

    def revert(self):
        self.save = sv.Save(self.raw)

    def nickname(self):
        identity = self.save.part('UserIdentity', create=False)
        return identity[0] if identity else None

    def summary(self):
        s = self.save
        currencies = s.part('MainCurrencies', create=False)
        values = (currencies or [[]])[0] or []
        money = [{'id': c, 'name': name('CURRENCY', c), 'icon': icon('monnaies', c), 'value': values[c] if c < len(values) else 0} for c in CURRENCIES[:5]]
        counts = []
        for key, label, part, total in (('heros', tr('Héros'), 'UnlockedHeroes', len(self.heroes())), ('armes', tr('Armes'), 'UnlockedWeapons', len(self.weapon_ids())), ('costumes', tr('Costumes'), 'UnlockedSkins', None)):
            counts.append({'key': key, 'label': label, 'owned': len(s.collection(part)) if part in s.values else 0, 'total': total})
        return {'nickname': self.nickname(), 'currencies': money, 'counts': counts}

    def rows(self, tab):
        return {'profil': self.profile_rows, 'heros': self.hero_rows, 'armes': self.weapon_rows, 'costumes': self.skin_rows, 'modes': self.mode_rows}[tab]()

    def profile_rows(self):
        if self.save is None:
            return []
        s = self.save
        rows = []

        def field(part, path, label, low=0, high=2 ** 31 - 1, text=False, picture=None):
            value = s.part(part, create=False)
            current = value
            try:
                for key in path:
                    current = current[key]
            except (TypeError, IndexError, KeyError):
                current = '' if text else 0

            def setter(_, new):
                target = s.part(part)
                for key in path[:-1]:
                    while isinstance(target, list) and len(target) <= key:
                        target.append(None)
                    if target[key] is None:
                        target[key] = []
                    target = target[key]
                while isinstance(target, list) and len(target) <= path[-1]:
                    target.append(0)
                target[path[-1]] = new
            rows.append(Row({'name': label, 'value': current, 'icon': icon('ui', picture) if picture else None}, setter, {'value': (low, high)}))
            return rows[-1]
        field('UserIdentity', [0], tr('Pseudo'), text=True, picture='pseudo')
        currencies = s.part('MainCurrencies', create=False)
        values = (currencies or [[]])[0] or []
        for currency in CURRENCIES:

            def set_currency(_, new, currency=currency):
                part = s.part('MainCurrencies')
                for index in (0, 3, 4):
                    if part[index] is None:
                        part[index] = []
                    while len(part[index]) <= currency:
                        part[index].append(0)
                part[0][currency] = new
            rows.append(Row({'name': name('CURRENCY', currency), 'icon': icon('monnaies', currency), 'value': values[currency] if currency < len(values) else 0}, set_currency))
        battle = s.part('BattleInfo', create=False)
        played = battle[0] if battle else 0
        won = battle[1] if battle else 0

        def set_lost(_, new):
            part = s.part('BattleInfo')
            part[0] = part[1] + new
        field('BattleInfo', [0], tr('Parties jouées'), picture='jouees')
        field('BattleInfo', [1], tr('Parties gagnées'), picture='gagnees')
        rows.append(Row({'name': tr('Parties perdues'), 'value': max(0, played - won), 'icon': icon('ui', 'perdues')}, set_lost))
        field('BattleInfo', [6], tr("Victoires aujourd'hui"), picture='jour_gagnees')
        field('BattleInfo', [7], tr("Défaites aujourd'hui"), picture='jour_perdues')
        field('BattleInfo', [2, 3], tr('Série de victoires en cours'), picture='serie')
        field('BattleInfo', [2, 2], tr('Meilleure série de victoires'), picture='meilleure_serie')
        field('BattleInfo', [5], tr('Difficulté des bots (0 à 100)'), 0, 100, picture='bots')
        medals_part = s.part('MedalRunState', create=False)
        owned_medals = (medals_part[2] if medals_part and len(medals_part) > 2 else None) or []
        rows.append(Row({'name': tr('Médailles (actuelles)'), 'value': sum(owned_medals), 'icon': icon('ui', 'medailles')}, lambda _, new: self.set_total_medals(new), {'value': (0, 10 ** 7)}))
        field('MedalRunState', [7], tr('Médailles (record)'), picture='medailles')
        field('MedalRunState', [8], tr('Ranger Road : récompenses prises'), picture='route')
        field('MedalRunState', [4], tr('Médailles bonus'), picture='medailles_bonus')
        field('GameModeProgression', [0], tr('Invasion : niveau atteint'), picture='invasion')
        return rows

    @staticmethod
    def heroes():
        found = [(c, sv.hero_unlockable(c)) for c in sv.CHARACTERS if c != 1]
        found += list(EXTRA_HEROES.items())
        return [(c, u) for c, u in found if u is not None]

    def hero_rows(self):
        if self.save is None:
            return []
        s = self.save
        owned = {e[0]: e for e in s.collection('UnlockedHeroes')} if 'UnlockedHeroes' in s.values else {}
        medals_part = s.part('MedalRunState', create=False)
        medals = (medals_part[2] if medals_part and len(medals_part) > 2 else None) or []
        battle = s.part('BattleInfo', create=False)
        streaks = (battle[2][4] if battle and battle[2] and (len(battle[2]) > 4) else None) or {}
        rows = []
        for character, unlockable in self.heroes():
            if unlockable in EXTRA_HEROES.values() and unlockable not in owned:
                continue
            entry = owned.get(unlockable)
            data = entry[1] or [] if entry else []
            values = {'name': HERO_NAMES.get(character) or name('CHARACTER_ID', character), 'owned': entry is not None, 'icon': icon('heros', character), 'level': (data[1] + 1 if len(data) > 1 else 1) if entry else None, 'talents': (data[4] if len(data) > 4 else 0) if entry else None, 'lorbs': (data[3] if len(data) > 3 else 0) if entry else None, 'medals': medals[character] if character < len(medals) else 0, 'streak': streaks.get(character, 0)}
            rows.append(Row(values, lambda key, new, c=character, u=unlockable: self.set_hero(c, u, key, new), {'level': (1, HERO_LEVEL_MAX), 'talents': (0, TALENTS_MAX), 'lorbs': (0, 10 ** 7), 'medals': (0, 10 ** 6), 'streak': (0, 10 ** 6)}, editable=lambda key, owned=entry is not None: owned or key in ('owned', 'medals', 'streak')))
        return rows

    def set_hero(self, character, unlockable, key, value):
        s = self.save
        heroes = s.collection('UnlockedHeroes')
        entry = next((e for e in heroes if e[0] == unlockable), None)
        if key == 'owned':
            skins = s.collection('UnlockedSkins')
            if value and entry is None:
                heroes.append([unlockable, [0, 0, 0, 0]])
                if unlockable not in skins:
                    skins.append(unlockable)
            elif not value and entry is not None:
                equipped = s.part('EquippedSkins', create=False)
                slots = s.collection('EquippedSkins') if equipped is not None else []
                hero_skins = {u for u, _ in sv.skins_of(character)} | {unlockable}
                if any((slot in hero_skins for slot in slots)):
                    raise Refus(tr("C'est le héros choisi dans le jeu : choisis-en un autre dans le jeu avant de le retirer."))
                if len(heroes) <= 1:
                    raise Refus(tr('Il faut garder au moins un héros.'))
                heroes.remove(entry)
                for skin in list(skins):
                    if skin in hero_skins:
                        skins.remove(skin)
            return
        if key == 'medals':
            part = s.part('MedalRunState')
            for index in (2, 6):
                if part[index] is None:
                    part[index] = []
                while len(part[index]) <= character:
                    part[index].append(0)
            part[2][character] = value
            part[7] = max(part[7] or 0, sum(part[2]))
            return
        if key == 'streak':
            part = s.part('BattleInfo')
            if part[2][4] is None:
                part[2][4] = {}
            part[2][4][character] = value
            part[2][2] = max(part[2][2] or 0, value)
            return
        if entry is None:
            return
        data = entry[1] if entry[1] is not None else []
        entry[1] = data
        index = {'level': 1, 'lorbs': 3, 'talents': 4}[key]
        while len(data) <= index:
            data.append(0)
        data[index] = value - 1 if key == 'level' else value

    def set_total_medals(self, total):
        part = self.save.part('MedalRunState')
        owned = {e[0] for e in self.save.collection('UnlockedHeroes')} if 'UnlockedHeroes' in self.save.values else set()
        characters = [c for c, u in self.heroes() if u in owned] or [c for c, _ in self.heroes()][:1]
        size = max([len(part[2] or []), len(part[6] or [])] + [c + 1 for c in characters])
        for index in (2, 6):
            if part[index] is None:
                part[index] = []
            while len(part[index]) < size:
                part[index].append(0)
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

    def all_heroes(self):
        for character, unlockable in self.heroes():
            if unlockable not in EXTRA_HEROES.values():
                self.set_hero(character, unlockable, 'owned', True)

    @staticmethod
    def max_heroes(rows):
        if not rows:
            raise Refus(tr("Sélectionne d'abord des héros dans la liste (clic, Maj+clic ou Cmd/Ctrl+clic)."))
        for row in rows:
            if row.get('owned'):
                row.set('level', HERO_LEVEL_MAX)
                row.set('talents', TALENTS_MAX)

    def weapon_ids(self):
        ids = [w for w, _ in sv.weapons()] + sorted(EXTRA_WEAPONS)
        if self.save is not None and 'UnlockedWeapons' in self.save.values:
            ids += [e[0] for e in self.save.collection('UnlockedWeapons') if e[0] not in ids]
        return ids

    def weapon_rows(self):
        if self.save is None:
            return []
        s = self.save
        owned = {e[0]: e for e in s.collection('UnlockedWeapons')} if 'UnlockedWeapons' in s.values else {}
        status = s.part('WeaponsStatus', create=False)
        locked = (status[0] if status else None) or {}
        loadout = set(s.collection('WeaponLoadoutByUID')) if 'WeaponLoadoutByUID' in s.values else set()
        rows = []
        for weapon in self.weapon_ids():
            entry = owned.get(weapon)
            data = entry[1] or [] if entry else []
            values = {'name': name('UNLOCKABLE_ID', weapon), 'owned': entry is not None, 'icon': icon('armes', weapon), 'level': (data[0] + 1 if data else 1) if entry else None, 'enhancement': (data[1] if len(data) > 1 else 0) if entry else None, 'blueprints': (data[2] if len(data) > 2 else 0) if entry else locked.get(weapon, 0), 'equipped': tr('oui') if weapon in loadout else ''}
            rows.append(Row(values, lambda key, new, w=weapon: self.set_weapon(w, key, new), {'level': (1, WEAPON_LEVEL_MAX), 'enhancement': (0, ENHANCEMENT_MAX), 'blueprints': (0, 10 ** 7)}, editable=lambda key, owned=entry is not None: owned or key in ('owned', 'blueprints')))
        return rows

    def set_weapon(self, weapon, key, value):
        s = self.save
        weapons = s.collection('UnlockedWeapons')
        entry = next((e for e in weapons if e[0] == weapon), None)
        if key == 'owned':
            if value and entry is None:
                status = s.part('WeaponsStatus')
                blueprints = (status[0] or {}).pop(weapon, 0) if status[0] else 0
                weapons.append([weapon, [0, 0, blueprints] if blueprints else []])
            elif not value and entry is not None:
                if 'WeaponLoadoutByUID' in s.values and weapon in s.collection('WeaponLoadoutByUID'):
                    raise Refus(tr('Cette arme est équipée : équipe-en une autre dans le jeu avant de la retirer.'))
                weapons.remove(entry)
            return
        if entry is None:
            if key == 'blueprints':
                status = s.part('WeaponsStatus')
                if status[0] is None:
                    status[0] = {}
                if value:
                    status[0][weapon] = value
                else:
                    status[0].pop(weapon, None)
            return
        data = entry[1] if entry[1] is not None else []
        entry[1] = data
        index = {'level': 0, 'enhancement': 1, 'blueprints': 2}[key]
        while len(data) <= index:
            data.append(0)
        data[index] = value - 1 if key == 'level' else value

    def all_weapons(self):
        for weapon in self.weapon_ids():
            if weapon not in EXTRA_WEAPONS:
                self.set_weapon(weapon, 'owned', True)

    @staticmethod
    def max_weapons(rows):
        if not rows:
            raise Refus(tr("Sélectionne d'abord des armes dans la liste (clic, Maj+clic ou Cmd/Ctrl+clic)."))
        for row in rows:
            if row.get('owned'):
                row.set('level', WEAPON_LEVEL_MAX)
                row.set('enhancement', ENHANCEMENT_MAX)

    def skin_rows(self):
        if self.save is None:
            return []
        s = self.save
        owned = set(s.collection('UnlockedSkins')) if 'UnlockedSkins' in s.values else set()
        worn = set(s.collection('EquippedSkins')) if 'EquippedSkins' in s.values else set()
        rows = []
        for character in sorted(sv.CHARACTERS):
            if character in (1, 7):
                continue
            for skin, code in sv.skins_of(character):
                if code.endswith('_SKIN00') or code.endswith('_DEPRECATED'):
                    continue
                rows.append(Row({'hero': name('CHARACTER_ID', character), 'name': name('UNLOCKABLE_ID', skin), 'icon': icon('costumes', skin), 'owned': skin in owned, 'equipped': tr('oui') if skin in worn else ''}, lambda key, new, k=skin: self.set_skin(k, new)))
        return rows

    def set_skin(self, skin, value):
        skins = self.save.collection('UnlockedSkins')
        if value and skin not in skins:
            skins.append(skin)
        elif not value and skin in skins:
            if skin in set(self.save.collection('EquippedSkins')):
                raise Refus(tr('Ce costume est porté : change de costume dans le jeu avant de le retirer.'))
            skins.remove(skin)

    def all_skins(self):
        for row in self.skin_rows():
            if not row.get('owned'):
                row.set('owned', True)

    def mode_rows(self):
        if self.save is None:
            return []
        s = self.save
        owned = set(s.collection('UnlockedGameModes')) if 'UnlockedGameModes' in s.values else set()
        progression = s.part('GameModeProgression', create=False)
        stats = (progression[1] if progression and len(progression) > 1 else None) or {}
        modes = [(int(v), n) for v, n in sv.SCHEMA['enums']['UNLOCKABLE_ID'].items() if n.startswith('GAME_MODE_')]
        rows = []
        for mode, code in modes:
            if code.endswith('_DEPRECATED') and mode not in owned and (mode not in (68, 114, 57)):
                continue
            entry = stats.get(mode) or [0, 0, 0, 0]
            rows.append(Row({'name': name('UNLOCKABLE_ID', mode), 'owned': mode in owned, 'battles': entry[0], 'icon': icon('modes', mode), 'wins': entry[1], 'losses': entry[2], 'draws': entry[3] if len(entry) > 3 else 0}, lambda key, new, m=mode: self.set_mode(m, key, new)))
        return rows

    def set_mode(self, mode, key, value):
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
        while len(entry) < 4:
            entry.append(0)
        entry[{'battles': 0, 'wins': 1, 'losses': 2, 'draws': 3}[key]] = value

    def value_at(self, part, path):
        value = self.save.values[part]
        for key in path:
            value = value[key]
        return value

    @staticmethod
    def show(value, what, detail):
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

    def node(self, part, path, kind, label):
        value = self.value_at(part, path)
        what, detail = sv.describe(kind)
        text, children = self.show(value, what, detail)
        return {'label': label, 'part': part, 'path': list(path), 'kind': kind, 'text': text, 'children': children}

    def roots(self):
        return [self.node(part, (), self.save.part_type(part) or '?', part) for part in sorted(self.save.values)]

    def children(self, part, path, kind):
        path = tuple(path)
        value = self.value_at(part, path)
        what, detail = sv.describe(kind)
        found = []
        if what == 'object' and isinstance(value, list):
            known = {k: (n, t) for k, n, t in sv.fields(detail) if isinstance(k, int)}
            for index in range(len(value)):
                field_name, field_kind = known.get(index, (f'[{index}]', '?'))
                found.append(self.node(part, path + (index,), field_kind, field_name))
        elif what == 'object' and isinstance(value, dict):
            known = {k: (n, t) for k, n, t in sv.fields(detail)}
            for key in value:
                field_name, field_kind = known.get(key, (str(key), '?'))
                found.append(self.node(part, path + (key,), field_kind, field_name))
        elif what == 'list' or (what not in ('map', 'object') and isinstance(value, list)):
            for index in range(len(value)):
                found.append(self.node(part, path + (index,), detail if what == 'list' else '?', f'[{index}]'))
        elif isinstance(value, dict):
            key_kind, item_kind = detail if what == 'map' else ('?', '?')
            for key in value:
                key_what, key_detail = sv.describe(key_kind)
                label = sv.name_of(key_detail, key) if key_what == 'enum' else str(key)
                found.append(self.node(part, path + (key,), item_kind, label))
        return found

    def set_at(self, part, path, new):
        self.value_at(part, tuple(path)[:-1])[path[-1]] = new

    @staticmethod
    def add_item(target, kind):
        target.append(sv.default(kind))

    @staticmethod
    def add_key(target, key, item_kind):
        if key in target:
            raise Refus(tr('Cette clé existe déjà.'))
        target[key] = sv.default(item_kind)

    @staticmethod
    def remove_item(parent, key):
        if isinstance(parent, list):
            del parent[key]
        else:
            parent.pop(key, None)
