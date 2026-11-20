import datetime
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk
import copie_android
import editeur_modele as em
import sauvegarde as sv
import theme
from langues import tr
TITLE = tr('Ranger Rumble hors ligne')
_IMAGES = {}
OWNED_BG, MISSING_FG = (theme.OWNED, '#6c7899')

def picture(key):
    if not key:
        return None
    path = em.ICONS / f'{key}.png'
    if path not in _IMAGES:
        try:
            _IMAGES[path] = tk.PhotoImage(file=str(path)) if path.is_file() else None
        except tk.TclError:
            _IMAGES[path] = None
    return _IMAGES[path]

def icon(folder, key):
    return picture(em.icon(folder, key))

def with_icon(key):
    image = icon('ui', key)
    return {'image': image, 'compound': 'left'} if image else {}

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
            self.tree.insert('', 'end', iid=str(i), values=values, image=picture(row.get('icon')) or '', tags=tags)
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
            new = not value
        else:
            low, high = row.bounds(key)
            if isinstance(value, str):
                new = simpledialog.askstring(TITLE, f"{title} — {row.get('name')} :", initialvalue=value, parent=self)
            else:
                new = simpledialog.askinteger(TITLE, tr('{title} — {v} ({low} à {high}) :', title=title, v=row.get('name'), low=low, high=high), initialvalue=value if value is not None else low, minvalue=low, maxvalue=high, parent=self)
            if new is None:
                return
        try:
            row.set(key, new)
        except em.Refus as refus:
            messagebox.showinfo(TITLE, str(refus))
            return
        self.changed()

class Editor(ttk.Frame):

    def __init__(self, parent, app):
        super().__init__(parent, padding=(22, 14, 22, 18))
        self.app = app
        self.model = em.Model()
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

    @property
    def save(self):
        return self.model.save

    def load(self, raw, source):
        fresh = em.Model()
        try:
            fresh.load(raw, source)
        except ValueError as error:
            messagebox.showerror(TITLE, str(error))
            return
        if self.save is not None and self.save.changed() and (not messagebox.askyesno(TITLE, tr("Tes changements dans la sauvegarde ouverte ne sont pas enregistrés. L'oublier ?"))):
            return
        self.model = fresh
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
        adb = None
        try:
            try:
                return em.find_phone(need_game)
            except em.NoAdb:
                if not messagebox.askyesno(TITLE, tr('Il faut les outils Android de Google (10 Mo). Les télécharger ?\n\nConditions : ') + copie_android.ADB_PAGE):
                    return None
                adb = copie_android.download_adb()
            return em.find_phone(need_game, adb)
        except em.Refus as refus:
            messagebox.showinfo(TITLE, str(refus))
            return None

    def open_phone(self):
        found = self.phone()
        if not found:
            return
        try:
            local = em.pull_phone_save(*found, self.app.copies_folder())
        except em.Refus as refus:
            messagebox.showinfo(TITLE, str(refus))
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
        self.model.mark_saved(where)
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
        if not messagebox.askyesno(TITLE, tr("Envoyer cette sauvegarde au téléphone ? Le jeu se ferme s'il est ouvert.")):
            return
        try:
            local = em.push_save(*found, self.save.to_bytes(), self.app.copies_folder())
        except em.Refus as refus:
            messagebox.showerror(TITLE, str(refus))
            return
        self.mark_saved(str(local))
        messagebox.showinfo(TITLE, tr('Sauvegarde envoyée.'))

    def revert(self):
        if self.save is not None and messagebox.askyesno(TITLE, tr("Oublier tous les changements depuis l'ouverture ?")):
            self.model.revert()
            self.refresh()

    def changed(self):
        self.refresh()

    def act(self, change):
        if self.save is None:
            return
        try:
            change()
        except em.Refus as refus:
            messagebox.showinfo(TITLE, str(refus))
        self.changed()

    def refresh(self):
        if self.save is None:
            return
        changes = self.save.changed()
        self.status.configure(text=tr('Sauvegarde : {source}  —  {v}  —  ', source=self.model.source, v=self.model.nickname() or tr('sans nom')) + (tr('{n_changes} partie(s) modifiée(s), pas encore enregistrée(s)', n_changes=len(changes)) if changes else tr('aucun changement')), foreground=theme.RED if changes else theme.SOFT)
        for table in self.tables:
            table.refresh()
        self.refresh_all()
        self.refresh_summary()

    def refresh_summary(self):
        for child in self.summary.winfo_children():
            child.destroy()
        summary = self.model.summary()
        ttk.Label(self.summary, text=summary['nickname'] or tr('Sans nom'), style='Grand.TLabel').pack(side='left', padx=(0, 18))
        for currency in summary['currencies']:
            tile = ttk.Frame(self.summary)
            tile.pack(side='left', padx=6)
            image = picture(currency['icon'])
            if image:
                ttk.Label(tile, image=image).pack(side='left')
            ttk.Label(tile, text=f"{currency['value']:,}".replace(',', ' '), style='Chiffre.TLabel').pack(side='left', padx=2)
        for count in summary['counts']:
            tile = ttk.Frame(self.summary)
            tile.pack(side='right', padx=8)
            ttk.Label(tile, text=count['label'], foreground=theme.SOFT).pack(side='left', padx=(0, 4))
            text = f"{count['owned']}/{count['total']}" if count['total'] else str(count['owned'])
            ttk.Label(tile, text=text, style='Chiffre.TLabel').pack(side='left')

    def table(self, tab, rows_tab, height, icons, style='Icones.Treeview'):
        table = Table(tab, em.columns(rows_tab), lambda: self.model.rows(rows_tab), self.changed, height=height, icons=icons, style=style)
        table.pack(fill='both', expand=True, pady=6)
        self.tables.append(table)
        return table

    def profile_tab(self):
        tab = ttk.Frame(self.tabs, padding=8)
        self.tabs.add(tab, text=tr('Profil et statistiques'), **with_icon('profil'))
        ttk.Label(tab, text=tr('Double-clique sur une valeur pour la changer.')).pack(anchor='w')
        self.table(tab, 'profil', 24, 28)

    def heroes_tab(self):
        tab = ttk.Frame(self.tabs, padding=8)
        self.tabs.add(tab, text=tr('Héros'), **with_icon('heros'))
        ttk.Label(tab, text=tr('Double-clique pour changer une valeur.')).pack(anchor='w')
        table = self.table(tab, 'heros', 12, 40)
        buttons = ttk.Frame(tab)
        buttons.pack(anchor='w')
        ttk.Button(buttons, text=tr('Débloquer tous les héros'), command=lambda: self.act(self.model.all_heroes), **with_icon('tout_debloquer')).pack(side='left')
        ttk.Button(buttons, text=tr('Niveau max pour la sélection'), command=lambda: self.act(lambda: self.model.max_heroes(table.selected_rows())), **with_icon('niveau_max')).pack(side='left', padx=8)

    def weapons_tab(self):
        tab = ttk.Frame(self.tabs, padding=8)
        self.tabs.add(tab, text=tr('Armes et gadgets'), **with_icon('armes'))
        ttk.Label(tab, text=tr('Double-clique pour changer une valeur.')).pack(anchor='w')
        table = self.table(tab, 'armes', 12, 40)
        buttons = ttk.Frame(tab)
        buttons.pack(anchor='w')
        ttk.Button(buttons, text=tr('Débloquer toutes les armes'), command=lambda: self.act(self.model.all_weapons), **with_icon('tout_debloquer')).pack(side='left')
        ttk.Button(buttons, text=tr('Niveau max pour la sélection'), command=lambda: self.act(lambda: self.model.max_weapons(table.selected_rows())), **with_icon('niveau_max')).pack(side='left', padx=8)

    def skins_tab(self):
        tab = ttk.Frame(self.tabs, padding=8)
        self.tabs.add(tab, text=tr('Costumes'), **with_icon('costumes'))
        ttk.Label(tab, text=tr('Double-clique pour donner ou retirer un costume.')).pack(anchor='w')
        self.table(tab, 'costumes', 10, 64, style='Cartes.Treeview')
        ttk.Button(tab, text=tr('Donner tous les costumes'), command=lambda: self.act(self.model.all_skins), **with_icon('tout_debloquer')).pack(anchor='w')

    def modes_tab(self):
        tab = ttk.Frame(self.tabs, padding=8)
        self.tabs.add(tab, text=tr('Modes de jeu'), **with_icon('modes'))
        ttk.Label(tab, text=tr('Modes proposés dans le jeu, et les parties de chacun.')).pack(anchor='w')
        self.table(tab, 'modes', 12, 32)

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
        for node in self.model.roots():
            self.add_node('', node)
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

    def add_node(self, parent, node):
        item = self.tree.insert(parent, 'end', text=node['label'], values=(node['text'], node['kind']))
        self.nodes[item] = (node['part'], tuple(node['path']), node['kind'])
        if node['children']:
            self.tree.insert(item, 'end', text='…')
        return item

    def expand(self, event=None, item=None):
        item = item or self.tree.focus()
        if item not in self.nodes:
            return
        children = self.tree.get_children(item)
        if len(children) != 1 or self.tree.item(children[0], 'text') != '…':
            return
        self.tree.delete(children[0])
        for node in self.model.children(*self.nodes[item]):
            self.add_node(item, node)

    def edit_node(self, event):
        item = self.tree.identify_row(event.y)
        if item not in self.nodes:
            return
        part, path, kind = self.nodes[item]
        if not path:
            return
        value = self.model.value_at(part, path)
        what, detail = sv.describe(kind)
        if what in ('object', 'list', 'map') or isinstance(value, (list, dict)):
            return
        new = self.ask_value(self.tree.item(item, 'text'), value, what, detail)
        if new is None:
            return
        self.model.set_at(part, path, new)
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
        value = self.model.value_at(part, path)
        what, detail = sv.describe(kind)
        menu = tk.Menu(self, tearoff=False)
        if what == 'list' and isinstance(value, list):
            menu.add_command(label=tr('Ajouter un élément'), command=lambda: self.act(lambda: self.model.add_item(value, detail)))
        elif what == 'list' and value is None and path:
            menu.add_command(label=tr('Créer la liste'), command=lambda: self.act(lambda: self.model.set_at(part, path, [])))
        if what == 'map' and isinstance(value, dict):
            menu.add_command(label=tr('Ajouter une clé'), command=lambda: self.add_key(value, detail))
        if path:
            parent = self.model.value_at(part, path[:-1])
            parent_kind = self.nodes.get(self.tree.parent(item), (None, None, '?'))[2]
            if isinstance(parent, list) and sv.describe(parent_kind)[0] == 'list' or (isinstance(parent, dict) and sv.describe(parent_kind)[0] == 'map'):
                label = tr('Retirer cet élément') if isinstance(parent, list) else tr('Retirer cette clé')
                menu.add_command(label=label, command=lambda: self.act(lambda: self.model.remove_item(parent, path[-1])))
        if menu.index('end') is not None:
            menu.tk_popup(event.x_root, event.y_root)

    def add_key(self, target, detail):
        key_kind, item_kind = detail
        what, inner = sv.describe(key_kind)
        key = self.ask_value(tr('Nouvelle clé'), 0 if what in ('int', 'enum') else '', what, inner)
        if key is not None:
            self.act(lambda: self.model.add_key(target, key, item_kind))
