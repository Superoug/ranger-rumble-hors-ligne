import datetime
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk
import copie_android
import sauvegarde as sv
import theme
from langues import tr
TITLE = tr('Ranger Rumble hors ligne')
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
_IMAGES = {}
OWNED_BG, MISSING_FG = (theme.OWNED, '#6c7899')

def icon(folder, key):
    path = ICONS / folder / f'{key}.png'
    if path not in _IMAGES:
        try:
            _IMAGES[path] = tk.PhotoImage(file=str(path)) if path.is_file() else None
        except tk.TclError:
            _IMAGES[path] = None
    return _IMAGES[path]

def with_icon(key):
    image = icon('ui', key)
    return {'image': image, 'compound': 'left'} if image else {}

def name(enum, value):
    return sv.name_of(enum, value)

def adb_text(adb, serial, *args):
    _, out, err = copie_android.run(adb, '-s', serial, *args, timeout=180)
    return out + err

def adb_ok(adb, serial, *args):
    return copie_android.run(adb, '-s', serial, *args, timeout=180)[0] == 0

class Table(ttk.Frame):

    def __init__(self, parent, columns, rows, changed, height=16, icons=0, style='Icones.Treeview'):
        super().__init__(parent, style='Card.TFrame', padding=6)
        self.columns, self.rows_of, self.changed = (columns, rows, changed)
        self.tree = ttk.Treeview(self, columns=[c[0] for c in columns], show='tree headings' if icons else 'headings', height=height, selectmode='extended', style=style)
        if icons:
            self.tree.column('#0', width=icons + 18, minwidth=icons + 18, stretch=False, anchor='center')
        self.tree.tag_configure('possede', background=OWNED_BG)
        self.tree.tag_configure('absent', foreground=MISSING_FG)
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
                    value = '✔ ' + tr('oui') if value else '✖ ' + tr('non')
                values.append('' if value is None else value)
            owned = row.get('owned')
            tags = () if owned is None else ('possede',) if owned else ('absent',)
            self.tree.insert('', 'end', iid=str(i), values=values, image=row.get('icon') or '', tags=tags)
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
                new = simpledialog.askinteger(TITLE, tr('{title} — {v} ({low} à {high}) :', title=title, v=row.get('name'), low=low, high=high), initialvalue=value if value is not None else low, minvalue=low, maxvalue=high, parent=self)
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
        super().__init__(parent, padding=(22, 14, 22, 18))
        self.app = app
        self.save = None
        self.source = None
        style = ttk.Style(self)
        style.configure('Icones.Treeview', rowheight=46)
        style.configure('Cartes.Treeview', rowheight=54)
        family = theme.family(self)
        style.configure('Grand.TLabel', font=(family, -17, 'bold'))
        style.configure('Chiffre.TLabel', font=(family, -14, 'bold'))
        ttk.Label(self, text=tr('Éditer une sauvegarde'), style='Big.TLabel').pack(anchor='w', pady=(0, 10))
        top = ttk.Frame(self)
        top.pack(fill='x')
        ttk.Label(top, text=tr('Ouvrir :'), style='Soft.TLabel').pack(side='left')
        ttk.Button(top, text=tr('Le téléphone (câble)'), command=self.open_phone, **with_icon('telephone')).pack(side='left', padx=4)
        ttk.Button(top, text=tr('Un fichier...'), command=self.open_file, **with_icon('fichier')).pack(side='left', padx=4)
        ttk.Button(top, text=tr('Une copie...'), command=self.open_copy, **with_icon('copie')).pack(side='left', padx=4)
        ttk.Button(top, text=tr('Partie vierge'), command=self.open_new, **with_icon('vierge')).pack(side='left', padx=4)
        self.status = ttk.Label(self, text=tr('Ouvre une sauvegarde, en haut.'), foreground=theme.SOFT)
        self.status.pack(fill='x', pady=(10, 6))
        self.summary = ttk.Frame(self)
        self.summary.pack(fill='x', pady=(0, 6))
        bottom = ttk.Frame(self)
        bottom.pack(side='bottom', fill='x', pady=(8, 0))
        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill='both', expand=True)
        self.tables = []
        self.profile_tab()
        self.heroes_tab()
        self.weapons_tab()
        self.skins_tab()
        self.modes_tab()
        self.all_tab()
        self.save_buttons = [ttk.Button(bottom, text=tr('Envoyer au téléphone'), command=self.send_phone, **with_icon('envoyer')), ttk.Button(bottom, text=tr('Enregistrer sous...'), command=self.save_as, **with_icon('enregistrer')), ttk.Button(bottom, text=tr("Utiliser pour fabriquer l'APK"), command=self.use_for_apk, **with_icon('apk')), ttk.Button(bottom, text=tr('Annuler mes changements'), command=self.revert, **with_icon('annuler'))]
        for button in self.save_buttons:
            button.pack(side='left', padx=(0, 8))
            button.configure(state='disabled')

    def load(self, raw, source):
        try:
            save = sv.Save(raw)
        except Exception as error:
            messagebox.showerror(TITLE, tr("Ce fichier n'est pas une sauvegarde lisible de Ranger Rumble :\n\n{error}", error=error))
            return
        if self.save is not None and self.save.changed() and (not messagebox.askyesno(TITLE, tr("Tes changements dans la sauvegarde ouverte ne sont pas enregistrés. L'oublier ?"))):
            return
        self.save, self.raw, self.source = (save, raw, source)
        for button in self.save_buttons:
            button.configure(state='normal')
        self.refresh()

    def open_file(self):
        path = filedialog.askopenfilename(title=tr('Sauvegarde à ouvrir'), filetypes=[(tr('Sauvegarde'), '*.msgpack'), (tr('Tous les fichiers'), '*')])
        if path:
            self.load(Path(path).read_bytes(), path)

    def open_copy(self):
        folder = filedialog.askdirectory(title=tr("Dossier d'une copie de sauvegarde"), initialdir=str(self.app.copies_folder()))
        if not folder:
            return
        path = Path(folder) / 'save.msgpack'
        if not path.is_file():
            messagebox.showerror(TITLE, tr("Cette copie n'a pas de sauvegarde (save.msgpack)."))
            return
        self.load(path.read_bytes(), str(path))

    def open_new(self):
        self.load(copie_android.pack(copie_android.new_save()), tr('partie vierge'))

    def phone(self, need_game=True):
        adb = copie_android.find_adb()
        if not adb:
            if not messagebox.askyesno(TITLE, tr('Il faut les outils Android de Google (10 Mo). Les télécharger ?\n\nConditions : ') + copie_android.ADB_PAGE):
                return None
            adb = copie_android.download_adb()
        listed = copie_android.phones(adb)
        ready = sorted((p for p in listed if p[1] == 'device'), key=lambda p: p[0].startswith('emulator-'))
        if not ready:
            if any((p[1] == 'unauthorized' for p in listed)):
                messagebox.showinfo(TITLE, tr('Touche « Autoriser » sur le téléphone, puis recommence.'))
            else:
                messagebox.showinfo(TITLE, tr("Aucun téléphone trouvé. Active le débogage USB et mets l'USB en « Transfert de fichiers », puis recommence."))
            return None
        if not need_game:
            return (adb, ready[0][0])
        for serial, _, _ in ready:
            if PACKAGE in adb_text(adb, serial, 'shell', 'pm', 'list', 'packages', PACKAGE):
                return (adb, serial)
        messagebox.showinfo(TITLE, tr("Le jeu n'est pas sur ce téléphone."))
        return None

    def open_phone(self):
        found = self.phone()
        if not found:
            return
        adb, serial = found
        listing = adb_text(adb, serial, 'shell', 'ls', PHONE_SAVE)
        if 'No such file' in listing or PHONE_SAVE not in listing:
            messagebox.showinfo(TITLE, tr('Ouvre le jeu une fois sur le téléphone, puis recommence.'))
            return
        local = Path(self.app.copies_folder()) / f'TELEPHONE_{datetime.datetime.now():%Y-%m-%d_%H%M%S}.msgpack'
        local.parent.mkdir(parents=True, exist_ok=True)
        adb_ok(adb, serial, 'pull', PHONE_SAVE, str(local))
        if not local.is_file():
            messagebox.showerror(TITLE, tr("La sauvegarde du téléphone n'a pas pu être lue."))
            return
        self.load(local.read_bytes(), tr('téléphone (copie gardée dans {name})', name=local.name))

    def save_as(self):
        path = filedialog.asksaveasfilename(title=tr('Enregistrer la sauvegarde'), defaultextension='.msgpack', initialfile=f'RangerRumble_sauvegarde_{datetime.datetime.now():%Y-%m-%d_%H%M}.msgpack', filetypes=[(tr('Sauvegarde'), '*.msgpack')])
        if not path:
            return None
        try:
            self.save.write(path)
        except Exception as error:
            messagebox.showerror(TITLE, tr('Enregistrement impossible :\n\n{error}', error=error))
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
            self.app.new_game_changed()
            messagebox.showinfo(TITLE, tr("C'est fait : l'APK partira de cette sauvegarde."))

    def send_phone(self):
        found = self.phone()
        if not found:
            return
        adb, serial = found
        if not messagebox.askyesno(TITLE, tr("Envoyer cette sauvegarde au téléphone ? Le jeu se ferme s'il est ouvert.")):
            return
        data = self.save.to_bytes()
        sv.Save(data)
        stamp = f'{datetime.datetime.now():%Y-%m-%d_%H%M%S}'
        local = Path(self.app.copies_folder()) / f'ENVOYEE_{stamp}.msgpack'
        local.parent.mkdir(parents=True, exist_ok=True)
        local.write_bytes(data)
        if PHONE_FOLDER not in adb_text(adb, serial, 'shell', 'ls', '-d', PHONE_FOLDER):
            messagebox.showinfo(TITLE, tr('Ouvre le jeu une fois sur le téléphone, puis recommence.'))
            return
        adb_ok(adb, serial, 'shell', 'am', 'force-stop', PACKAGE)
        adb_ok(adb, serial, 'push', str(local), PHONE_IMPORT + '.tmp')
        adb_ok(adb, serial, 'shell', 'mv', PHONE_IMPORT + '.tmp', PHONE_IMPORT)
        check = adb_text(adb, serial, 'shell', 'ls', '-l', PHONE_IMPORT)
        if str(len(data)) not in check:
            messagebox.showerror(TITLE, tr("La sauvegarde n'a pas pu être posée sur le téléphone."))
            return
        adb_ok(adb, serial, 'shell', 'am', 'start', '-n', GAME_ACTIVITY)
        self.mark_saved(str(local))
        messagebox.showinfo(TITLE, tr('Sauvegarde envoyée.'))

    def revert(self):
        if self.save is not None and messagebox.askyesno(TITLE, tr("Oublier tous les changements depuis l'ouverture ?")):
            self.save = sv.Save(self.raw)
            self.refresh()

    def changed(self):
        self.refresh()

    def refresh(self):
        if self.save is None:
            return
        changes = self.save.changed()
        self.status.configure(text=tr('Sauvegarde : {source}  —  {v}  —  ', source=self.source, v=self.nickname() or tr('sans nom')) + (tr('{n_changes} partie(s) modifiée(s), pas encore enregistrée(s)', n_changes=len(changes)) if changes else tr('aucun changement')), foreground=theme.RED if changes else theme.SOFT)
        for table in self.tables:
            table.refresh()
        self.refresh_all()
        self.refresh_summary()

    def refresh_summary(self):
        for child in self.summary.winfo_children():
            child.destroy()
        s = self.save
        ttk.Label(self.summary, text=self.nickname() or tr('Sans nom'), style='Grand.TLabel').pack(side='left', padx=(0, 18))
        currencies = s.part('MainCurrencies', create=False)
        values = (currencies or [[]])[0] or []
        for currency in CURRENCIES[:5]:
            amount = values[currency] if currency < len(values) else 0
            tile = ttk.Frame(self.summary)
            tile.pack(side='left', padx=6)
            image = icon('monnaies', currency)
            if image:
                ttk.Label(tile, image=image).pack(side='left')
            ttk.Label(tile, text=f'{amount:,}'.replace(',', ' '), style='Chiffre.TLabel').pack(side='left', padx=2)
        counts = [(tr('Costumes'), 'UnlockedSkins', None), (tr('Armes'), 'UnlockedWeapons', len(self.weapon_ids())), (tr('Héros'), 'UnlockedHeroes', len(self.heroes()))]
        for label, part, total in counts:
            owned = len(s.collection(part)) if part in s.values else 0
            tile = ttk.Frame(self.summary)
            tile.pack(side='right', padx=8)
            ttk.Label(tile, text=label, foreground=theme.SOFT).pack(side='left', padx=(0, 4))
            ttk.Label(tile, text=f'{owned}/{total}' if total else str(owned), style='Chiffre.TLabel').pack(side='left')

    def nickname(self):
        identity = self.save.part('UserIdentity', create=False)
        return identity[0] if identity else None

    def profile_tab(self):
        tab = ttk.Frame(self.tabs, padding=8)
        self.tabs.add(tab, text=tr('Profil et statistiques'), **with_icon('profil'))
        ttk.Label(tab, text=tr('Double-clique sur une valeur pour la changer.')).pack(anchor='w')
        table = Table(tab, [('name', tr('Valeur'), 360, None), ('value', '', 160, 'int')], self.profile_rows, self.changed, height=24, icons=28)
        table.pack(fill='both', expand=True, pady=6)
        self.tables.append(table)

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

    def heroes_tab(self):
        tab = ttk.Frame(self.tabs, padding=8)
        self.tabs.add(tab, text=tr('Héros'), **with_icon('heros'))
        ttk.Label(tab, text=tr('Double-clique pour changer une valeur.')).pack(anchor='w')
        columns = [('name', tr('Héros'), 200, None), ('owned', tr('Débloqué'), 80, 'bool'), ('level', tr('Niveau'), 70, 'int'), ('talents', tr('Talents'), 70, 'int'), ('lorbs', tr('Lorbes'), 80, 'int'), ('medals', tr('Médailles'), 90, 'int'), ('streak', tr('Série de victoires'), 120, 'int')]
        table = Table(tab, columns, self.hero_rows, self.changed, height=12, icons=40)
        table.pack(fill='both', expand=True, pady=6)
        self.tables.append(table)
        buttons = ttk.Frame(tab)
        buttons.pack(anchor='w')
        ttk.Button(buttons, text=tr('Débloquer tous les héros'), command=lambda: self.all_heroes(table, True), **with_icon('tout_debloquer')).pack(side='left')
        ttk.Button(buttons, text=tr('Niveau max pour la sélection'), command=lambda: self.max_heroes(table), **with_icon('niveau_max')).pack(side='left', padx=8)

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
                    messagebox.showinfo(TITLE, tr("C'est le héros choisi dans le jeu : choisis-en un autre dans le jeu avant de le retirer."))
                    return
                if len(heroes) <= 1:
                    messagebox.showinfo(TITLE, tr('Il faut garder au moins un héros.'))
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

    def all_heroes(self, table, value):
        for character, unlockable in self.heroes():
            if unlockable not in EXTRA_HEROES.values():
                self.set_hero(character, unlockable, 'owned', value)
        self.changed()

    def max_heroes(self, table):
        rows = table.selected_rows()
        if not rows:
            messagebox.showinfo(TITLE, tr("Sélectionne d'abord des héros dans la liste (clic, Maj+clic ou Cmd/Ctrl+clic)."))
            return
        for row in rows:
            if row.get('owned'):
                row.set('level', HERO_LEVEL_MAX)
                row.set('talents', TALENTS_MAX)
        self.changed()

    def weapons_tab(self):
        tab = ttk.Frame(self.tabs, padding=8)
        self.tabs.add(tab, text=tr('Armes et gadgets'), **with_icon('armes'))
        ttk.Label(tab, text=tr('Double-clique pour changer une valeur.')).pack(anchor='w')
        columns = [('name', tr('Arme'), 220, None), ('owned', tr('Débloquée'), 80, 'bool'), ('level', tr('Niveau'), 70, 'int'), ('enhancement', tr('Améliorations'), 100, 'int'), ('blueprints', tr('Plans'), 90, 'int'), ('equipped', tr('Équipée'), 70, None)]
        table = Table(tab, columns, self.weapon_rows, self.changed, height=12, icons=40)
        table.pack(fill='both', expand=True, pady=6)
        self.tables.append(table)
        buttons = ttk.Frame(tab)
        buttons.pack(anchor='w')
        ttk.Button(buttons, text=tr('Débloquer toutes les armes'), command=self.all_weapons, **with_icon('tout_debloquer')).pack(side='left')
        ttk.Button(buttons, text=tr('Niveau max pour la sélection'), command=lambda: self.max_weapons(table), **with_icon('niveau_max')).pack(side='left', padx=8)

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
                    messagebox.showinfo(TITLE, tr('Cette arme est équipée : équipe-en une autre dans le jeu avant de la retirer.'))
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
            messagebox.showinfo(TITLE, tr("Sélectionne d'abord des armes dans la liste (clic, Maj+clic ou Cmd/Ctrl+clic)."))
            return
        for row in rows:
            if row.get('owned'):
                row.set('level', WEAPON_LEVEL_MAX)
                row.set('enhancement', ENHANCEMENT_MAX)
        self.changed()

    def skins_tab(self):
        tab = ttk.Frame(self.tabs, padding=8)
        self.tabs.add(tab, text=tr('Costumes'), **with_icon('costumes'))
        ttk.Label(tab, text=tr('Double-clique pour donner ou retirer un costume.')).pack(anchor='w')
        table = Table(tab, [('hero', tr('Héros'), 160, None), ('name', tr('Costume'), 260, None), ('owned', tr('Possédé'), 80, 'bool'), ('equipped', tr('Porté'), 70, None)], self.skin_rows, self.changed, height=10, icons=64, style='Cartes.Treeview')
        table.pack(fill='both', expand=True, pady=6)
        self.tables.append(table)
        ttk.Button(tab, text=tr('Donner tous les costumes'), command=self.all_skins, **with_icon('tout_debloquer')).pack(anchor='w')

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
                messagebox.showinfo(TITLE, tr('Ce costume est porté : change de costume dans le jeu avant de le retirer.'))
                return
            skins.remove(skin)

    def all_skins(self):
        for row in self.skin_rows():
            if not row.get('owned'):
                row.set('owned', True)
        self.changed()

    def modes_tab(self):
        tab = ttk.Frame(self.tabs, padding=8)
        self.tabs.add(tab, text=tr('Modes de jeu'), **with_icon('modes'))
        ttk.Label(tab, text=tr('Modes proposés dans le jeu, et les parties de chacun.')).pack(anchor='w')
        table = Table(tab, [('name', tr('Mode'), 240, None), ('owned', tr('Débloqué'), 80, 'bool'), ('battles', tr('Jouées'), 80, 'int'), ('wins', tr('Gagnées'), 80, 'int'), ('losses', tr('Perdues'), 80, 'int'), ('draws', tr('Égalités'), 80, 'int')], self.mode_rows, self.changed, height=12, icons=32)
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

    def all_tab(self):
        tab = ttk.Frame(self.tabs, padding=8)
        self.tabs.add(tab, text=tr('Tout (avancé)'), **with_icon('tout'))
        ttk.Label(tab, text=tr('Toute la sauvegarde. Double-clique pour changer, clic droit pour ajouter ou retirer. Avec précaution.')).pack(anchor='w')
        frame = ttk.Frame(tab, style='Card.TFrame', padding=6)
        frame.pack(fill='both', expand=True, pady=6)
        self.tree = ttk.Treeview(frame, columns=('value', 'type'), height=22)
        self.tree.heading('#0', text=tr('Champ'))
        self.tree.heading('value', text=tr('Valeur'))
        self.tree.heading('type', text=tr('Type'))
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
            return simpledialog.askinteger(TITLE, tr('{label} : un nombre parmi\n{hint}', label=label, hint=hint), initialvalue=value or 0, parent=self)
        if what == 'string' or isinstance(value, str):
            return simpledialog.askstring(TITLE, f'{label} :', initialvalue=value or '', parent=self)
        if what == 'float' or isinstance(value, float):
            new = simpledialog.askfloat(TITLE, f'{label} :', initialvalue=value or 0.0, parent=self)
            return None if new is None else sv.F32(new) if isinstance(value, sv.F32) or detail in ('float', 'Single') else new
        if what == 'bytes':
            text = simpledialog.askstring(TITLE, tr('{label} (en hexadécimal) :', label=label), initialvalue=(value or b'').hex(), parent=self)
            try:
                return None if text is None else bytes.fromhex(text)
            except ValueError:
                messagebox.showerror(TITLE, tr("Ce n'est pas de l'hexadécimal."))
                return None
        low, high = detail if what == 'int' else (-2 ** 63, 2 ** 64 - 1)
        return simpledialog.askinteger(TITLE, tr('{label} ({low} à {high}) :', label=label, low=low, high=high), initialvalue=value if value is not None else 0, minvalue=low, maxvalue=high, parent=self)

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
            menu.add_command(label=tr('Ajouter un élément'), command=lambda: self.add_item(value, detail))
        elif what == 'list' and value is None and path:
            menu.add_command(label=tr('Créer la liste'), command=lambda: self.set_at(part, path, []))
        if what == 'map' and isinstance(value, dict):
            menu.add_command(label=tr('Ajouter une clé'), command=lambda: self.add_key(value, detail))
        if path:
            parent = self.value_at(part, path[:-1])
            parent_kind = self.nodes.get(self.tree.parent(item), (None, None, '?'))[2]
            if isinstance(parent, list) and sv.describe(parent_kind)[0] == 'list':
                menu.add_command(label=tr('Retirer cet élément'), command=lambda: self.remove_item(parent, path[-1]))
            if isinstance(parent, dict) and sv.describe(parent_kind)[0] == 'map':
                menu.add_command(label=tr('Retirer cette clé'), command=lambda: self.remove_item(parent, path[-1]))
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
        key = self.ask_value(tr('Nouvelle clé'), 0 if what in ('int', 'enum') else '', what, inner)
        if key is None:
            return
        if key in target:
            messagebox.showinfo(TITLE, tr('Cette clé existe déjà.'))
            return
        target[key] = sv.default(item_kind)
        self.changed()

    def remove_item(self, parent, key):
        if isinstance(parent, list):
            del parent[key]
        else:
            parent.pop(key, None)
        self.changed()
