import datetime
import os
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk
import copie_android
import sauvegarde as sv
TITLE = 'Ranger Rumble hors ligne'
PACKAGE = copie_android.PACKAGE
PHONE_FOLDER = f'/sdcard/Android/data/{PACKAGE}/files/rr_editeur'
PHONE_SAVE = PHONE_FOLDER + '/sauvegarde_actuelle.msgpack'
PHONE_IMPORT = PHONE_FOLDER + '/a_importer.msgpack'
PHONE_DOWNLOAD = '/sdcard/Download/RangerRumble_sauvegarde_modifiee.msgpack'
GAME_ACTIVITY = f'{PACKAGE}/com.ohbibi.AndroidActivity.OhbibiUnityPlayerActivity'
HERO_LEVEL_MAX = 10
WEAPON_LEVEL_MAX = 10
TALENTS_MAX = 6
ENHANCEMENT_MAX = 3
EXTRA_HEROES = {23: 83}
EXTRA_WEAPONS = {9}
CURRENCIES = [1, 5, 6, 9, 10, 4, 2]

def name(enum, value):
    return sv.name_of(enum, value)

def adb_text(adb, serial, *args):
    _, out, err = copie_android.run(adb, '-s', serial, *args, timeout=180)
    return out + err

def adb_ok(adb, serial, *args):
    return copie_android.run(adb, '-s', serial, *args, timeout=180)[0] == 0

class Table(ttk.Frame):

    def __init__(self, parent, columns, rows, changed, height=16):
        super().__init__(parent)
        self.columns, self.rows_of, self.changed = (columns, rows, changed)
        self.tree = ttk.Treeview(self, columns=[c[0] for c in columns], show='headings', height=height, selectmode='extended')
        for key, title, width, _ in columns:
            self.tree.heading(key, text=title)
            self.tree.column(key, width=width, anchor='w' if width > 120 else 'center', stretch=width > 120)
        scroll = ttk.Scrollbar(self, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side='left', fill='both', expand=True)
        scroll.pack(side='right', fill='y')
        self.tree.bind('<Double-1>', self.clicked)
        self.tree.bind('<Return>', self.clicked)
        self.rows = []

    def refresh(self):
        selected = self.tree.selection()
        self.tree.delete(*self.tree.get_children())
        self.rows = self.rows_of()
        for i, row in enumerate(self.rows):
            values = []
            for key, _, _, kind in self.columns:
                value = row.get(key)
                if kind == 'bool':
                    value = '✔' if value else '—'
                values.append('' if value is None else value)
            self.tree.insert('', 'end', iid=str(i), values=values)
        for item in selected:
            if self.tree.exists(item):
                self.tree.selection_add(item)

    def selected_rows(self):
        return [self.rows[int(i)] for i in self.tree.selection()]

    def clicked(self, event):
        item = self.tree.focus() if event.type == tk.EventType.KeyPress else self.tree.identify_row(event.y)
        column = '#1' if event.type == tk.EventType.KeyPress else self.tree.identify_column(event.x)
        if not item or not column:
            return
        key, title, _, kind = self.columns[int(column[1:]) - 1]
        row = self.rows[int(item)]
        if kind is None or not row.editable(key):
            if event.type == tk.EventType.KeyPress:
                return
            for key, title, _, kind in self.columns:
                if kind == 'bool' and row.editable(key):
                    break
            else:
                return
        value = row.get(key)
        if kind == 'bool':
            row.set(key, not value)
        else:
            low, high = row.bounds(key)
            if isinstance(value, str):
                new = simpledialog.askstring(TITLE, f"{title} — {row.get('name')} :", initialvalue=value, parent=self)
            else:
                new = simpledialog.askinteger(TITLE, f"{title} — {row.get('name')} ({low} à {high}) :", initialvalue=value if value is not None else low, minvalue=low, maxvalue=high, parent=self)
            if new is None:
                return
            row.set(key, new)
        self.changed()

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

class Editor(ttk.Frame):

    def __init__(self, parent, app):
        super().__init__(parent, padding=12)
        self.app = app
        self.save = None
        self.source = None
        top = ttk.Frame(self)
        top.pack(fill='x')
        ttk.Label(top, text='Ouvrir :').pack(side='left')
        ttk.Button(top, text='Un fichier...', command=self.open_file).pack(side='left', padx=4)
        ttk.Button(top, text='Une copie...', command=self.open_copy).pack(side='left', padx=4)
        ttk.Button(top, text='Le téléphone (câble)', command=self.open_phone).pack(side='left', padx=4)
        ttk.Button(top, text='Partie vierge', command=self.open_new).pack(side='left', padx=4)
        self.status = ttk.Label(self, text="Aucune sauvegarde ouverte. Choisis d'où elle vient, en haut.", foreground='#555')
        self.status.pack(fill='x', pady=(8, 4))
        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill='both', expand=True)
        self.tables = []
        self.profile_tab()
        self.heroes_tab()
        self.weapons_tab()
        self.skins_tab()
        self.modes_tab()
        self.all_tab()
        bottom = ttk.Frame(self)
        bottom.pack(fill='x', pady=(8, 0))
        self.save_buttons = [ttk.Button(bottom, text='Enregistrer sous...', command=self.save_as), ttk.Button(bottom, text='Envoyer au téléphone', command=self.send_phone), ttk.Button(bottom, text="Utiliser pour fabriquer l'APK", command=self.use_for_apk), ttk.Button(bottom, text='Annuler mes changements', command=self.revert)]
        for button in self.save_buttons:
            button.pack(side='left', padx=(0, 8))
            button.configure(state='disabled')

    def load(self, raw, source):
        try:
            save = sv.Save(raw)
        except Exception as error:
            messagebox.showerror(TITLE, f"Ce fichier n'est pas une sauvegarde lisible de Ranger Rumble :\n\n{error}")
            return
        if self.save is not None and self.save.changed() and (not messagebox.askyesno(TITLE, "Tes changements dans la sauvegarde ouverte ne sont pas enregistrés. L'oublier ?")):
            return
        self.save, self.raw, self.source = (save, raw, source)
        for button in self.save_buttons:
            button.configure(state='normal')
        self.refresh()

    def open_file(self):
        path = filedialog.askopenfilename(title='Sauvegarde à ouvrir', filetypes=[('Sauvegarde', '*.msgpack'), ('Tous les fichiers', '*')])
        if path:
            self.load(Path(path).read_bytes(), path)

    def open_copy(self):
        folder = filedialog.askdirectory(title="Dossier d'une copie de sauvegarde", initialdir=str(self.app.copies_folder()))
        if not folder:
            return
        path = Path(folder) / 'save.msgpack'
        if not path.is_file():
            messagebox.showerror(TITLE, "Cette copie n'a pas de sauvegarde (save.msgpack).")
            return
        self.load(path.read_bytes(), str(path))

    def open_new(self):
        self.load(copie_android.pack(copie_android.new_save()), 'partie vierge')

    def phone(self):
        adb = copie_android.find_adb()
        if not adb:
            if not messagebox.askyesno(TITLE, "Pour parler au téléphone par le câble, l'outil a besoin des outils Android de Google (« platform-tools », environ 10 Mo). Les télécharger maintenant depuis le site de Google ?\n\nEn les téléchargeant, tu acceptes leurs conditions d'utilisation : " + copie_android.ADB_PAGE):
                return None
            adb = copie_android.download_adb()
        listed = copie_android.phones(adb)
        ready = [p for p in listed if p[1] == 'device']
        if not ready:
            if any((p[1] == 'unauthorized' for p in listed)):
                messagebox.showinfo(TITLE, 'Le téléphone attend ton accord : touche « Autoriser » dans la fenêtre « Autoriser le débogage USB ? » sur son écran, puis recommence.')
            else:
                messagebox.showinfo(TITLE, 'Aucun téléphone trouvé. Branche-le avec le débogage USB activé (voir LIS_MOI.txt), puis recommence.')
            return None
        for serial, _, _ in ready:
            if PACKAGE in adb_text(adb, serial, 'shell', 'pm', 'list', 'packages', PACKAGE):
                return (adb, serial)
        messagebox.showinfo(TITLE, "Le jeu n'est pas installé sur le téléphone branché.")
        return None

    def open_phone(self):
        found = self.phone()
        if not found:
            return
        adb, serial = found
        listing = adb_text(adb, serial, 'shell', 'ls', PHONE_SAVE)
        if 'No such file' in listing or PHONE_SAVE not in listing:
            messagebox.showinfo(TITLE, "Le jeu du téléphone ne donne pas encore sa sauvegarde par le câble : il faut la version hors ligne 1.0.0 ou plus récente, lancée au moins une fois.\n\nSinon, exporte-la dans RR Options (TA SAUVEGARDE HORS LIGNE > Exporter), copie le fichier sur l'ordinateur et ouvre-le avec « Un fichier... ».")
            return
        local = Path(self.app.copies_folder()) / f'TELEPHONE_{datetime.datetime.now():%Y-%m-%d_%H%M%S}.msgpack'
        local.parent.mkdir(parents=True, exist_ok=True)
        adb_ok(adb, serial, 'pull', PHONE_SAVE, str(local))
        if not local.is_file():
            messagebox.showerror(TITLE, "La sauvegarde du téléphone n'a pas pu être lue.")
            return
        self.load(local.read_bytes(), f'téléphone (copie gardée dans {local.name})')

    def save_as(self):
        path = filedialog.asksaveasfilename(title='Enregistrer la sauvegarde', defaultextension='.msgpack', initialfile=f'RangerRumble_sauvegarde_{datetime.datetime.now():%Y-%m-%d_%H%M}.msgpack', filetypes=[('Sauvegarde', '*.msgpack')])
        if not path:
            return None
        try:
            self.save.write(path)
        except Exception as error:
            messagebox.showerror(TITLE, f'Enregistrement impossible :\n\n{error}')
            return None
        self.mark_saved(path)
        return path

    def mark_saved(self, where):
        self.raw = self.save.to_bytes()
        self.save = sv.Save(self.raw)
        self.source = where
        self.refresh()

    def use_for_apk(self):
        path = self.save_as()
        if path:
            self.app.phone_save.set(path)
            self.app.new_game.set(False)
            messagebox.showinfo(TITLE, "C'est la « Sauvegarde exportée » de l'onglet 2 : l'APK fabriqué partira de cette sauvegarde.")

    def send_phone(self):
        found = self.phone()
        if not found:
            return
        adb, serial = found
        if not messagebox.askyesno(TITLE, "Envoyer cette sauvegarde au téléphone ?\n\nLe jeu se ferme s'il est ouvert. À son prochain lancement, il prend cette sauvegarde à la place de la sienne, qu'il range d'abord dans son historique."):
            return
        data = self.save.to_bytes()
        sv.Save(data)
        stamp = f'{datetime.datetime.now():%Y-%m-%d_%H%M%S}'
        local = Path(self.app.copies_folder()) / f'ENVOYEE_{stamp}.msgpack'
        local.parent.mkdir(parents=True, exist_ok=True)
        local.write_bytes(data)
        supports = PHONE_FOLDER in adb_text(adb, serial, 'shell', 'ls', '-d', PHONE_FOLDER)
        adb_ok(adb, serial, 'shell', 'am', 'force-stop', PACKAGE)
        if supports:
            adb_ok(adb, serial, 'push', str(local), PHONE_IMPORT + '.tmp')
            adb_ok(adb, serial, 'shell', 'mv', PHONE_IMPORT + '.tmp', PHONE_IMPORT)
            check = adb_text(adb, serial, 'shell', 'ls', '-l', PHONE_IMPORT)
            if str(len(data)) not in check:
                messagebox.showerror(TITLE, "La sauvegarde n'a pas pu être posée sur le téléphone.")
                return
            adb_ok(adb, serial, 'shell', 'am', 'start', '-n', GAME_ACTIVITY)
            self.mark_saved(str(local))
            messagebox.showinfo(TITLE, 'Sauvegarde envoyée : le jeu redémarre avec elle sur le téléphone.')
            return
        adb_ok(adb, serial, 'push', str(local), PHONE_DOWNLOAD)
        self.mark_saved(str(local))
        messagebox.showinfo(TITLE, "Le jeu du téléphone est d'une version qui ne prend pas encore la sauvegarde par le câble. Le fichier est dans son dossier Téléchargements (RangerRumble_sauvegarde_modifiee.msgpack) : ouvre RR Options > Importer et choisis-le.")

    def revert(self):
        if self.save is not None and messagebox.askyesno(TITLE, "Oublier tous les changements depuis l'ouverture ?"):
            self.save = sv.Save(self.raw)
            self.refresh()

    def changed(self):
        self.refresh()

    def refresh(self):
        if self.save is None:
            return
        changes = self.save.changed()
        self.status.configure(text=f"Sauvegarde : {self.source}  —  {self.nickname() or 'sans nom'}  —  " + (f'{len(changes)} partie(s) modifiée(s), pas encore enregistrée(s)' if changes else 'aucun changement'), foreground='#a33' if changes else '#555')
        for table in self.tables:
            table.refresh()
        self.refresh_all()

    def nickname(self):
        identity = self.save.part('UserIdentity', create=False)
        return identity[0] if identity else None

    def profile_tab(self):
        tab = ttk.Frame(self.tabs, padding=8)
        self.tabs.add(tab, text='Profil et statistiques')
        ttk.Label(tab, text='Double-clique sur une valeur pour la changer.').pack(anchor='w')
        table = Table(tab, [('name', 'Valeur', 360, None), ('value', '', 160, 'int')], self.profile_rows, self.changed, height=24)
        table.pack(fill='both', expand=True, pady=6)
        self.tables.append(table)

    def profile_rows(self):
        if self.save is None:
            return []
        s = self.save
        rows = []

        def field(part, path, label, low=0, high=2 ** 31 - 1, text=False):
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
            rows.append(Row({'name': label, 'value': current}, setter, {'value': (low, high)}))
            return rows[-1]
        field('UserIdentity', [0], 'Pseudo', text=True)
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
            rows.append(Row({'name': f"Monnaie : {name('CURRENCY', currency)}", 'value': values[currency] if currency < len(values) else 0}, set_currency))
        battle = s.part('BattleInfo', create=False)
        played = battle[0] if battle else 0
        won = battle[1] if battle else 0

        def set_lost(_, new):
            part = s.part('BattleInfo')
            part[0] = part[1] + new
        field('BattleInfo', [0], 'Parties jouées')
        field('BattleInfo', [1], 'Parties gagnées')
        rows.append(Row({'name': 'Parties perdues (jouées − gagnées)', 'value': max(0, played - won)}, set_lost))
        field('BattleInfo', [6], "Victoires aujourd'hui")
        field('BattleInfo', [7], "Défaites aujourd'hui")
        field('BattleInfo', [2, 3], 'Série de victoires en cours')
        field('BattleInfo', [2, 2], 'Meilleure série de victoires')
        field('BattleInfo', [5], 'Difficulté des bots (0 à 100)', 0, 100)
        field('MedalRunState', [7], 'Médailles : record absolu')
        field('MedalRunState', [8], 'Course aux médailles : récompenses récupérées')
        field('MedalRunState', [4], 'Médailles bonus (fakeMedals)')
        field('GameModeProgression', [0], 'Invasion : niveau atteint')
        return rows

    def heroes_tab(self):
        tab = ttk.Frame(self.tabs, padding=8)
        self.tabs.add(tab, text='Héros')
        ttk.Label(tab, text="Double-clique : « Débloqué » coche ou décoche, les nombres s'écrivent. Niveau comme dans le jeu (1 à 10).").pack(anchor='w')
        columns = [('name', 'Héros', 200, None), ('owned', 'Débloqué', 80, 'bool'), ('level', 'Niveau', 70, 'int'), ('talents', 'Talents', 70, 'int'), ('lorbs', 'Lorbes', 80, 'int'), ('medals', 'Médailles', 90, 'int'), ('streak', 'Série de victoires', 120, 'int')]
        table = Table(tab, columns, self.hero_rows, self.changed, height=20)
        table.pack(fill='both', expand=True, pady=6)
        self.tables.append(table)
        buttons = ttk.Frame(tab)
        buttons.pack(anchor='w')
        ttk.Button(buttons, text='Débloquer tous les héros', command=lambda: self.all_heroes(table, True)).pack(side='left')
        ttk.Button(buttons, text='Niveau max pour la sélection', command=lambda: self.max_heroes(table)).pack(side='left', padx=8)

    def heroes(self):
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
            values = {'name': name('CHARACTER_ID', character) if str(character) in sv.NAMES['CHARACTER_ID'] else name('UNLOCKABLE_ID', unlockable), 'owned': entry is not None, 'level': (data[1] + 1 if len(data) > 1 else 1) if entry else None, 'talents': (data[4] if len(data) > 4 else 0) if entry else None, 'lorbs': (data[3] if len(data) > 3 else 0) if entry else None, 'medals': medals[character] if character < len(medals) else 0, 'streak': streaks.get(character, 0)}
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
                    messagebox.showinfo(TITLE, "C'est le héros choisi dans le jeu : choisis-en un autre dans le jeu avant de le retirer.")
                    return
                if len([e for e in heroes]) <= 1:
                    messagebox.showinfo(TITLE, 'Il faut garder au moins un héros.')
                    return
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

    def all_heroes(self, table, value):
        for character, unlockable in self.heroes():
            if unlockable not in EXTRA_HEROES.values():
                self.set_hero(character, unlockable, 'owned', value)
        self.changed()

    def max_heroes(self, table):
        rows = table.selected_rows()
        if not rows:
            messagebox.showinfo(TITLE, "Sélectionne d'abord des héros dans la liste (clic, Maj+clic ou Cmd/Ctrl+clic).")
            return
        for row in rows:
            if row.get('owned'):
                row.set('level', HERO_LEVEL_MAX)
                row.set('talents', TALENTS_MAX)
        self.changed()

    def weapons_tab(self):
        tab = ttk.Frame(self.tabs, padding=8)
        self.tabs.add(tab, text='Armes et gadgets')
        ttk.Label(tab, text="Niveau comme dans le jeu (1 à 10). Plans : ceux de l'arme débloquée, ou ceux gardés pour une arme encore bloquée.").pack(anchor='w')
        columns = [('name', 'Arme', 220, None), ('owned', 'Débloquée', 80, 'bool'), ('level', 'Niveau', 70, 'int'), ('enhancement', 'Améliorations', 100, 'int'), ('blueprints', 'Plans', 90, 'int'), ('equipped', 'Équipée', 70, None)]
        table = Table(tab, columns, self.weapon_rows, self.changed, height=20)
        table.pack(fill='both', expand=True, pady=6)
        self.tables.append(table)
        buttons = ttk.Frame(tab)
        buttons.pack(anchor='w')
        ttk.Button(buttons, text='Débloquer toutes les armes', command=self.all_weapons).pack(side='left')
        ttk.Button(buttons, text='Niveau max pour la sélection', command=lambda: self.max_weapons(table)).pack(side='left', padx=8)

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
            values = {'name': name('UNLOCKABLE_ID', weapon), 'owned': entry is not None, 'level': (data[0] + 1 if data else 1) if entry else None, 'enhancement': (data[1] if len(data) > 1 else 0) if entry else None, 'blueprints': (data[2] if len(data) > 2 else 0) if entry else locked.get(weapon, 0), 'equipped': 'oui' if weapon in loadout else ''}
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
                    messagebox.showinfo(TITLE, 'Cette arme est équipée : équipe-en une autre dans le jeu avant de la retirer.')
                    return
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
        self.changed()

    def max_weapons(self, table):
        rows = table.selected_rows()
        if not rows:
            messagebox.showinfo(TITLE, "Sélectionne d'abord des armes dans la liste (clic, Maj+clic ou Cmd/Ctrl+clic).")
            return
        for row in rows:
            if row.get('owned'):
                row.set('level', WEAPON_LEVEL_MAX)
                row.set('enhancement', ENHANCEMENT_MAX)
        self.changed()

    def skins_tab(self):
        tab = ttk.Frame(self.tabs, padding=8)
        self.tabs.add(tab, text='Costumes')
        ttk.Label(tab, text="Double-clique pour donner ou retirer un costume. Un costume ne sert qu'avec son héros débloqué.").pack(anchor='w')
        table = Table(tab, [('hero', 'Héros', 160, None), ('name', 'Costume', 260, None), ('owned', 'Possédé', 80, 'bool'), ('equipped', 'Porté', 70, None)], self.skin_rows, self.changed, height=20)
        table.pack(fill='both', expand=True, pady=6)
        self.tables.append(table)
        ttk.Button(tab, text='Donner tous les costumes', command=self.all_skins).pack(anchor='w')

    def skin_rows(self):
        if self.save is None:
            return []
        s = self.save
        owned = set(s.collection('UnlockedSkins')) if 'UnlockedSkins' in s.values else set()
        worn = set(s.collection('EquippedSkins')) if 'EquippedSkins' in s.values else set()
        rows = []
        for character in sorted(sv.CHARACTERS):
            if character == 1:
                continue
            for skin, code in sv.skins_of(character):
                if code.endswith('_SKIN00') or code.endswith('_DEPRECATED'):
                    continue
                rows.append(Row({'hero': name('CHARACTER_ID', character), 'name': name('UNLOCKABLE_ID', skin), 'owned': skin in owned, 'equipped': 'oui' if skin in worn else ''}, lambda key, new, k=skin: self.set_skin(k, new)))
        return rows

    def set_skin(self, skin, value):
        skins = self.save.collection('UnlockedSkins')
        if value and skin not in skins:
            skins.append(skin)
        elif not value and skin in skins:
            if skin in set(self.save.collection('EquippedSkins')):
                messagebox.showinfo(TITLE, 'Ce costume est porté : change de costume dans le jeu avant de le retirer.')
                return
            skins.remove(skin)

    def all_skins(self):
        for row in self.skin_rows():
            if not row.get('owned'):
                row.set('owned', True)
        self.changed()

    def modes_tab(self):
        tab = ttk.Frame(self.tabs, padding=8)
        self.tabs.add(tab, text='Modes de jeu')
        ttk.Label(tab, text='Modes proposés dans le jeu, et les parties de chacun.').pack(anchor='w')
        table = Table(tab, [('name', 'Mode', 240, None), ('owned', 'Débloqué', 80, 'bool'), ('battles', 'Jouées', 80, 'int'), ('wins', 'Gagnées', 80, 'int'), ('losses', 'Perdues', 80, 'int'), ('draws', 'Égalités', 80, 'int')], self.mode_rows, self.changed, height=18)
        table.pack(fill='both', expand=True, pady=6)
        self.tables.append(table)

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
            rows.append(Row({'name': name('UNLOCKABLE_ID', mode), 'owned': mode in owned, 'battles': entry[0], 'wins': entry[1], 'losses': entry[2], 'draws': entry[3] if len(entry) > 3 else 0}, lambda key, new, m=mode: self.set_mode(m, key, new)))
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

    def all_tab(self):
        tab = ttk.Frame(self.tabs, padding=8)
        self.tabs.add(tab, text='Tout (avancé)')
        ttk.Label(tab, text='Toute la sauvegarde, avec les noms du code du jeu. Double-clique sur une valeur pour la changer ; clic droit sur une liste pour ajouter ou retirer un élément. À manier avec précaution.').pack(anchor='w')
        frame = ttk.Frame(tab)
        frame.pack(fill='both', expand=True, pady=6)
        self.tree = ttk.Treeview(frame, columns=('value', 'type'), height=22)
        self.tree.heading('#0', text='Champ')
        self.tree.heading('value', text='Valeur')
        self.tree.heading('type', text='Type')
        self.tree.column('#0', width=330)
        self.tree.column('value', width=300)
        self.tree.column('type', width=180)
        scroll = ttk.Scrollbar(frame, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side='left', fill='both', expand=True)
        scroll.pack(side='right', fill='y')
        self.tree.bind('<<TreeviewOpen>>', self.expand)
        self.tree.bind('<Double-1>', self.edit_node)
        self.tree.bind('<Button-2>' if self.tk.call('tk', 'windowingsystem') == 'aqua' else '<Button-3>', self.node_menu)
        self.nodes = {}

    def refresh_all(self):
        opened = {self.nodes[i][0:2] for i in self.nodes if self.tree.exists(i) and self.tree.item(i, 'open')}
        self.tree.delete(*self.tree.get_children())
        self.nodes = {}
        for part in sorted(self.save.values):
            kind = self.save.part_type(part) or '?'
            self.add_node('', part, (), kind, part)
        self.reopen(opened)

    def reopen(self, opened):
        changed = True
        while changed:
            changed = False
            for item, (part, path, _) in list(self.nodes.items()):
                if (part, path) in opened and (not self.tree.item(item, 'open')) and self.tree.get_children(item):
                    self.tree.item(item, open=True)
                    self.expand(item=item)
                    changed = True

    def value_at(self, part, path):
        value = self.save.values[part]
        for key in path:
            value = value[key]
        return value

    def add_node(self, parent, part, path, kind, label):
        value = self.value_at(part, path)
        what, detail = sv.describe(kind)
        shown, children = self.show(value, what, detail)
        item = self.tree.insert(parent, 'end', text=label, values=(shown, kind))
        self.nodes[item] = (part, path, kind)
        if children:
            self.tree.insert(item, 'end', text='…')
        return item

    @staticmethod
    def show(value, what, detail):
        if value is None:
            return ('(vide)', False)
        if what == 'object':
            return ('', True)
        if what in ('list', 'map'):
            return (f'{len(value)} élément(s)', len(value) > 0)
        if what == 'enum':
            return (f'{sv.name_of(detail, value)}  ({value})', False)
        if what == 'bytes':
            return (value.hex() if len(value) <= 32 else f'{len(value)} octets', False)
        if isinstance(value, (list, dict)):
            return (f'{len(value)} élément(s)', len(value) > 0)
        return (repr(value) if isinstance(value, str) else str(value), False)

    def expand(self, event=None, item=None):
        item = item or self.tree.focus()
        if item not in self.nodes:
            return
        children = self.tree.get_children(item)
        if len(children) != 1 or self.tree.item(children[0], 'text') != '…':
            return
        self.tree.delete(children[0])
        part, path, kind = self.nodes[item]
        value = self.value_at(part, path)
        what, detail = sv.describe(kind)
        if what == 'object' and isinstance(value, list):
            known = {k: (n, t) for k, n, t in sv.fields(detail) if isinstance(k, int)}
            for index in range(len(value)):
                field_name, field_kind = known.get(index, (f'[{index}]', '?'))
                self.add_node(item, part, path + (index,), field_kind, field_name)
        elif what == 'object' and isinstance(value, dict):
            known = {k: (n, t) for k, n, t in sv.fields(detail)}
            for key in value:
                field_name, field_kind = known.get(key, (str(key), '?'))
                self.add_node(item, part, path + (key,), field_kind, field_name)
        elif what == 'list' or (what not in ('map', 'object') and isinstance(value, list)):
            for index in range(len(value)):
                self.add_node(item, part, path + (index,), detail if what == 'list' else '?', f'[{index}]')
        elif isinstance(value, dict):
            key_kind, item_kind = detail if what == 'map' else ('?', '?')
            for key in value:
                key_what, key_detail = sv.describe(key_kind)
                label = sv.name_of(key_detail, key) if key_what == 'enum' else str(key)
                self.add_node(item, part, path + (key,), item_kind, label)

    def edit_node(self, event):
        item = self.tree.identify_row(event.y)
        if item not in self.nodes:
            return
        part, path, kind = self.nodes[item]
        if not path:
            return
        value = self.value_at(part, path)
        what, detail = sv.describe(kind)
        if what in ('object', 'list', 'map') or isinstance(value, (list, dict)):
            return
        new = self.ask_value(self.tree.item(item, 'text'), value, what, detail)
        if new is None:
            return
        parent = self.value_at(part, path[:-1])
        parent[path[-1]] = new
        self.changed()

    def ask_value(self, label, value, what, detail):
        if what == 'bool' or isinstance(value, bool):
            return not value
        if what == 'enum':
            choices = sv.enum_values(detail)
            hint = ', '.join((f'{v} = {sv.name_of(detail, v)}' for v, _ in choices[:40]))
            return simpledialog.askinteger(TITLE, f'{label} : un nombre parmi\n{hint}', initialvalue=value or 0, parent=self)
        if what == 'string' or isinstance(value, str):
            return simpledialog.askstring(TITLE, f'{label} :', initialvalue=value or '', parent=self)
        if what == 'float' or isinstance(value, float):
            new = simpledialog.askfloat(TITLE, f'{label} :', initialvalue=value or 0.0, parent=self)
            return None if new is None else sv.F32(new) if isinstance(value, sv.F32) or detail in ('float', 'Single') else new
        if what == 'bytes':
            text = simpledialog.askstring(TITLE, f'{label} (en hexadécimal) :', initialvalue=(value or b'').hex(), parent=self)
            try:
                return None if text is None else bytes.fromhex(text)
            except ValueError:
                messagebox.showerror(TITLE, "Ce n'est pas de l'hexadécimal.")
                return None
        low, high = detail if what == 'int' else (-2 ** 63, 2 ** 64 - 1)
        return simpledialog.askinteger(TITLE, f'{label} ({low} à {high}) :', initialvalue=value if value is not None else 0, minvalue=low, maxvalue=high, parent=self)

    def node_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item not in self.nodes:
            return
        self.tree.selection_set(item)
        part, path, kind = self.nodes[item]
        value = self.value_at(part, path)
        what, detail = sv.describe(kind)
        menu = tk.Menu(self, tearoff=False)
        if what == 'list' and isinstance(value, list):
            menu.add_command(label='Ajouter un élément', command=lambda: self.add_item(value, detail))
        elif what == 'list' and value is None and path:
            menu.add_command(label='Créer la liste', command=lambda: self.set_at(part, path, []))
        if what == 'map' and isinstance(value, dict):
            menu.add_command(label='Ajouter une clé', command=lambda: self.add_key(value, detail))
        if path:
            parent = self.value_at(part, path[:-1])
            parent_kind = self.nodes.get(self.tree.parent(item), (None, None, '?'))[2]
            if isinstance(parent, list) and sv.describe(parent_kind)[0] == 'list':
                menu.add_command(label='Retirer cet élément', command=lambda: self.remove_item(parent, path[-1]))
            if isinstance(parent, dict) and sv.describe(parent_kind)[0] == 'map':
                menu.add_command(label='Retirer cette clé', command=lambda: self.remove_item(parent, path[-1]))
        if menu.index('end') is not None:
            menu.tk_popup(event.x_root, event.y_root)

    def set_at(self, part, path, new):
        self.value_at(part, path[:-1])[path[-1]] = new
        self.changed()

    def add_item(self, target, kind):
        target.append(sv.default(kind))
        self.changed()

    def add_key(self, target, detail):
        key_kind, item_kind = detail
        what, inner = sv.describe(key_kind)
        key = self.ask_value('Nouvelle clé', 0 if what in ('int', 'enum') else '', what, inner)
        if key is None:
            return
        if key in target:
            messagebox.showinfo(TITLE, 'Cette clé existe déjà.')
            return
        target[key] = sv.default(item_kind)
        self.changed()

    def remove_item(self, parent, key):
        if isinstance(parent, list):
            del parent[key]
        else:
            parent.pop(key, None)
        self.changed()
