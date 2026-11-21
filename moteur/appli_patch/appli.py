import asyncio
import io
import math
import os
import platform
import queue
import subprocess
import sys
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import accueil
from commun import BUILD_STEPS, COPIES, ROOT, STEP, copies, is_save, load_tool, open_folder, save_label, saves
import copie_android
import editeur
import langues
import mises_a_jour
import pare_feu
import patcher
import theme
from langues import tr
TITLE = tr('Ranger Rumble hors ligne')
PLATFORMS = (('ios', tr('iPhone ou iPad')), ('android', 'Android'))
COPY_TEXTS = {'': tr('Choisir en haut où est le jeu.'), 'ios': tr("iPhone sur le même Wi-Fi que cet ordinateur. Cliquer sur Démarrer, puis scanner le QR code avec l'iPhone. Avant le 1er mai 2027."), 'android': tr("Sur Android, rien à copier : aller à l'étape 2 et choisir la sauvegarde exportée ou « Nouvelle partie ».")}
COPY_BUTTON = tr('Démarrer')
BUILD_TEXT = tr("Choisir le jeu officiel 1.10.4 et la sauvegarde (ou « Nouvelle partie »), puis cliquer sur « Fabriquer l'APK ». Il faut 5 Go libres.")
BUILD_TEXTS = {'': BUILD_TEXT, 'ios': BUILD_TEXT + ' ' + tr('Le jeu hors ligne se joue sur Android uniquement.'), 'android': BUILD_TEXT + ' ' + tr("Il faut désinstaller le jeu officiel du téléphone avant d'installer l'APK.")}
APK_NAME = 'RangerRumble_hors_ligne.apk'
LIGHTS = {'attente': ('#8a8a8a', "En attente de l'iPhone..."), 'iphone': ('#e0a020', "L'iPhone parle à l'outil. Ouvrir le jeu."), 'jeu': ('#e0a020', "Le jeu passe par l'outil : copie en cours..."), 'certificat': ('#d04040', "Le jeu refuse le certificat : refais l'étape 3."), 'sauvegarde': ('#e0a020', "Sauvegarde reçue : reste sur l'écran d'accueil du jeu..."), 'fini': ('#30b050', 'Sauvegarde copiée !'), 'arret': ('#8a8a8a', 'Copie arrêtée, rien de copié.')}
MAX_WIDTH = 1080

def describe(error):
    return f'{type(error).__name__} : {error}'

def in_background(work):
    threading.Thread(target=work, daemon=True).start()

class Output(io.TextIOBase):
    encoding = 'utf-8'

    def __init__(self):
        super().__init__()
        self.queue = queue.Queue()

    def writable(self):
        return True

    def write(self, text):
        self.queue.put(text)
        return len(text)

class Bar:

    def __init__(self, root, parent):
        self.root = root
        self.frame = ttk.Frame(parent)
        self.bar = ttk.Progressbar(self.frame, mode='determinate', length=240, maximum=100)
        self.bar.pack(side='left')
        self.text = ttk.Label(self.frame, width=-18)
        self.text.pack(side='left', padx=8)
        self.what = ''
        self.start = self.goal = 0.0
        self.seconds = 0
        self.since = 0.0
        self.ticking = False

    def begin(self, what):
        self.what = what
        self.set(0)

    def set(self, value, goal=None, seconds=0):
        self.start, self.goal, self.seconds = (value, value if goal is None else goal, seconds)
        self.since = time.monotonic()
        self.show(value)
        if not self.ticking:
            self.ticking = True
            self.tick()

    def step(self, number):
        if number in BUILD_STEPS:
            start, goal, seconds = BUILD_STEPS[number]
            self.set(start, goal, seconds / 2)
        elif number == 6:
            self.set(100)

    def sending(self, fraction, direct=False):
        if direct:
            self.what = tr('Installation directe...')
            self.set(0, 99, copie_android.DIRECT_SECONDS)
        elif fraction >= 0.8:
            self.set(80, 99, 8)
        else:
            self.set(fraction * 100)

    def tick(self):
        if not self.ticking:
            return
        if self.seconds and self.goal > self.start:
            spent = time.monotonic() - self.since
            self.show(self.start + (self.goal - self.start) * (1 - math.exp(-spent / self.seconds)))
        self.root.after(250, self.tick)

    def show(self, value):
        self.bar['value'] = max(value, 6) if value > 0 else 0
        self.text['text'] = f'{self.what} {int(value)} %'

    def done(self, ok):
        self.ticking = False
        if ok:
            self.show(100)
        else:
            self.bar['value'] = 0
            self.text['text'] = ''

def centre(outer, inner):

    def placed(event):
        width = min(event.width, MAX_WIDTH)
        inner.place(x=(event.width - width) // 2, y=0, width=width, height=event.height)
    outer.bind('<Configure>', placed)

def centred(parent, padding=(22, 14, 22, 18), height=None):
    outer = ttk.Frame(parent, height=height or 1)
    inner = ttk.Frame(outer, padding=padding)
    centre(outer, inner)
    return (outer, inner)

def paragraph(parent, text):
    label = ttk.Label(parent, text=text, justify='left')
    label.bind('<Configure>', lambda event: label.configure(wraplength=event.width))
    label.pack(fill='x', anchor='w')
    return label

def log_box(parent):
    ttk.Label(parent, text=tr('Journal').upper(), style='Small.TLabel').pack(side='top', anchor='w', pady=(0, 4))
    card = ttk.Frame(parent, style='Card.TFrame', padding=6)
    card.pack(fill='both', expand=True)
    box = tk.Text(card, height=18, wrap='word', state='disabled')
    theme.log_colours(box)
    scroll = ttk.Scrollbar(card, command=box.yview)
    box.configure(yscrollcommand=scroll.set)
    scroll.pack(side='right', fill='y')
    box.pack(fill='both', expand=True)
    return (box, card)

def framed_log(parent):
    holder = ttk.Frame(parent)
    holder.pack(fill='both', expand=True)
    box, card = log_box(holder)
    return (box, card, holder)

class Application:

    def __init__(self, root):
        self.root = root
        self.output = Output()
        self.target = None
        self.bar = None
        self.copy_state = None
        self.copy_started = time.time()
        self.light_state = None
        self.building = False
        self.restart = False
        self.release = None
        self.platforms = PLATFORMS
        root.title(TITLE)
        self._place_window()
        theme.apply(root)
        root.configure(background=theme.NAVY)
        try:
            self.icon = tk.PhotoImage(file=str(HERE / 'ressources' / 'lanceur' / 'icone.png'))
            root.iconphoto(True, self.icon)
        except tk.TclError:
            pass
        self.work = ttk.Frame(root)
        top_line = self._platform_line()
        self.notebook = self._pages()
        self.home = accueil.Home(root, self)
        self.header = accueil.Header(self.work, self, self.home)
        self.header.canvas.pack(fill='x', before=top_line)
        self.notebook.bind('<<NotebookTabChanged>>', lambda _event: self.header.select(self.notebook.index(self.notebook.select())))
        self.platform.trace_add('write', lambda *_: self.home.refresh())
        root.bind('<Activate>', lambda event: event.widget is root and self.home.pause(False))
        root.bind('<Deactivate>', lambda event: event.widget is root and self.home.pause(True))
        self.restore_settings()
        self.show_home()
        in_background(self.check_release)
        sys.stdout = self.output
        sys.stderr = self.output
        root.protocol('WM_DELETE_WINDOW', self.close)
        root.after(100, self.pump)

    def _place_window(self):
        root = self.root
        screen_width, screen_height = (root.winfo_screenwidth(), root.winfo_screenheight())
        width, height = (min(980, screen_width - 40), min(700, screen_height - 110))
        root.geometry(f'{width}x{height}+{max(0, (screen_width - width) // 2)}+{max(0, (screen_height - height) // 2 - 30)}')
        root.minsize(min(800, width), min(590, height))

    def _platform_line(self):
        top_line, top = centred(self.work, (22, 12, 22, 0), height=60)
        top_line.pack(fill='x')
        ttk.Label(top, text=tr('Mon jeu Ranger Rumble est sur :'), style='Soft.TLabel').pack(side='left')
        self.platform = tk.StringVar(value='')
        self.platform_buttons = []
        for value, label in PLATFORMS:
            button = ttk.Radiobutton(top, text=label, value=value, variable=self.platform, command=self.platform_changed)
            button.pack(side='left', padx=10)
            self.platform_buttons.append(button)
        names = dict(langues.LANGUAGES)
        self.language = tk.StringVar(value=names[langues.CURRENT])
        chooser = ttk.Combobox(top, textvariable=self.language, values=list(names.values()), state='readonly', width=11)
        chooser.pack(side='right')
        chooser.bind('<<ComboboxSelected>>', self.language_changed)
        ttk.Label(top, text=tr('Langue :'), style='Soft.TLabel').pack(side='right', padx=(0, 6))
        return top_line

    def _pages(self):
        notebook = ttk.Notebook(self.work, style='Pages.TNotebook')
        notebook.pack(fill='both', expand=True)
        notebook.add(self.copy_tab(notebook), text=tr('  1. Copier la sauvegarde  '))
        notebook.add(self.build_tab(notebook), text=tr("  2. Fabriquer l'APK  "))
        editor_page = ttk.Frame(notebook)
        self.editor = editeur.Editor(editor_page, self)
        centre(editor_page, self.editor)
        notebook.add(editor_page, text=tr('  3. Éditer une sauvegarde  '))
        notebook.add(self.updates_tab(notebook), text=tr('  4. Mises à jour  '))
        return notebook

    def show_home(self):
        self.work.pack_forget()
        self.home.canvas.pack(fill='both', expand=True)
        self.home.start()

    def show_page(self, index):
        self.home.stop()
        self.home.canvas.pack_forget()
        self.notebook.select(index)
        self.header.select(index)
        self.work.pack(fill='both', expand=True)

    @staticmethod
    def copies_folder():
        COPIES.mkdir(exist_ok=True)
        return COPIES

    def later(self, callback, *args):
        self.root.after(0, callback, *args)

    def pump(self):
        try:
            while True:
                text = self.output.queue.get_nowait()
                step = STEP.match(text)
                if step and self.bar is not None:
                    self.bar.step(int(step.group(1)))
                if self.target is not None:
                    self.target.configure(state='normal')
                    self.target.insert('end', text)
                    self.target.see('end')
                    self.target.configure(state='disabled')
        except queue.Empty:
            pass
        self.root.after(100, self.pump)

    def show_failure(self, error, text):
        print(tr('\nÉchec : {error}\n', error=error))
        messagebox.showerror(TITLE, text)

    def copy_tab(self, notebook):
        page, tab = centred(notebook)
        ttk.Label(tab, text=tr('Copier ma sauvegarde'), style='Big.TLabel').pack(anchor='w', pady=(0, 6))
        self.copy_intro = paragraph(tab, COPY_TEXTS[''])
        buttons = ttk.Frame(tab)
        buttons.pack(anchor='w', pady=(12, 16))
        self.copy_button = ttk.Button(buttons, text=COPY_BUTTON, command=self.toggle_copy, state='disabled', style='Primary.TButton')
        self.copy_button.pack(side='left')
        ttk.Button(buttons, text=tr('Ouvrir le dossier des copies'), command=lambda: open_folder(self.copies_folder())).pack(side='left', padx=8)
        self.light = tk.Canvas(buttons, width=18, height=18, highlightthickness=0, background=ttk.Style(self.root).lookup('TFrame', 'background') or None)
        self.light_dot = self.light.create_oval(2, 2, 16, 16, fill='#8a8a8a', outline='')
        self.light_text = ttk.Label(buttons, text='')
        self.copy_log, self.copy_card, frame = framed_log(tab)
        self.qr_panel = ttk.Frame(frame)
        self.qr_label = ttk.Label(self.qr_panel)
        self.qr_label.pack()
        self.qr_text = ttk.Label(self.qr_panel, justify='center', wraplength=230, style='Soft.TLabel')
        self.qr_text.pack(pady=6)
        return page

    def show_qr(self, url):
        try:
            import segno
            data = segno.make(url, error='m').png_data_uri(scale=6, border=2).split(',', 1)[1]
            self.qr_image = tk.PhotoImage(data=data)
            self.qr_label.configure(image=self.qr_image)
        except (ImportError, ValueError, tk.TclError):
            self.qr_label.configure(image='')
        self.qr_text.configure(text=tr("Scanner avec l'iPhone\n{url}", url=url))
        self.qr_panel.pack(side='right', anchor='n', padx=(10, 0), before=self.copy_card)

    def hide_qr(self):
        self.qr_panel.pack_forget()

    def platform_changed(self):
        where = self.platform.get()
        if where:
            mises_a_jour.remember(plateforme=where)
        self.copy_intro.configure(text=COPY_TEXTS[where])
        self.build_intro.configure(text=BUILD_TEXTS[where])
        if not self.copy_state:
            self.copy_button.configure(text=COPY_BUTTON, state='normal' if where == 'ios' else 'disabled')

    def toggle_copy(self):
        if self.copy_state == 'depart':
            return
        if self.copy_state:
            self.stop_copy()
            self.copy_button.configure(text=tr('Arrêt...'), state='disabled')
            return
        if self.building:
            messagebox.showinfo(TITLE, tr("Il faut attendre la fin de la fabrication de l'APK."))
            return
        self.start_copy()

    def stop_copy(self):
        if isinstance(self.copy_state, tuple):
            loop, master = self.copy_state
            loop.call_soon_threadsafe(master.shutdown)

    def start_copy(self):
        self.target = self.copy_log
        self.copy_state = 'depart'
        self.copy_button.configure(text=tr('Arrêter'), state='disabled')
        for button in self.platform_buttons:
            button.configure(state='disabled')
        started = self.copy_started = time.time()
        self.light_state = None
        self.copy_light('attente')
        in_background(lambda: self.copy_work(started))

    def copy_ready(self, master, _page):
        self.copy_state = (asyncio.get_running_loop(), master)
        self.later(lambda: self.copy_button.configure(state='normal'))
        if os.name == 'nt':
            in_background(self.check_firewall)

    def copy_work(self, started):
        try:
            tool = load_tool()
            tool.ON_STATE = lambda name: self.later(self.copy_light, name)
            address, proxy_port, page_port = tool.prepare()
            if not address.startswith(('192.168.', '10.', '172.')):
                print(tr("Cet ordinateur n'a pas d'adresse sur un réseau local ({address}) : il faut le mettre sur le même Wi-Fi que l'iPhone.", address=address))
            self.later(self.show_qr, f'http://{address}:{page_port}')
            asyncio.run(tool.run(address, proxy_port, page_port, self.copy_ready))
        except Exception as error:
            print(tr('\nErreur : {error}', error=error))
        finally:
            self.copy_state = None
            print(tr("\nCopie arrêtée. Supprime le profil RatchetRR de l'iPhone (Réglages > Général > VPN et gestion de l'appareil).\n"))
            self.later(self.hide_qr)
            self.later(self.copy_stopped)
            self.later(self.take_copy_save, started)
            self.later(self.copy_light, 'arret')

    def check_firewall(self):
        time.sleep(6)
        if pare_feu.check():
            self.later(self.firewall_blocked)

    def firewall_blocked(self):
        print(tr("Le pare-feu de Windows empêche l'iPhone d'arriver jusqu'à l'outil."))
        if messagebox.askyesno(TITLE, tr("Le pare-feu de Windows bloque l'iPhone.\n\nL'autoriser sur le réseau local ? Windows va demander l'accord.")):
            in_background(lambda: self.later(self.firewall_fixed, pare_feu.fix()))

    def firewall_fixed(self, done):
        if done:
            print(tr("Pare-feu réglé : l'iPhone peut arriver jusqu'à l'outil."))
            messagebox.showinfo(TITLE, tr("C'est réglé. Rescanne le QR code avec l'iPhone."))
        else:
            messagebox.showwarning(TITLE, tr('Pas réglé. Sécurité Windows > Pare-feu > Autoriser une application : cocher Python (Privé et Public).'))

    def copy_stopped(self):
        self.copy_button.configure(text=COPY_BUTTON)
        for button in self.platform_buttons:
            button.configure(state='normal')
        self.platform_changed()

    def copy_light(self, name):
        if self.light_state == 'fini':
            return
        color, text = LIGHTS[name]
        self.light_state = name
        self.light.itemconfigure(self.light_dot, fill=color)
        self.light_text.configure(text=tr(text))
        self.light.pack(side='left', padx=(12, 4))
        self.light_text.pack(side='left')
        if name == 'fini':
            self.take_copy_save(self.copy_started)
            messagebox.showinfo(TITLE, tr("Sauvegarde copiée ! Elle est choisie à l'étape 2.\n\nSur l'iPhone, supprimer le profil RatchetRR (Réglages > Général > VPN et gestion de l'appareil)."))

    def take_copy_save(self, since):
        made = [folder for folder in copies() if folder.stat().st_mtime >= since]
        if made:
            self.choose_save(made[0] / 'save.msgpack')

    def build_tab(self, notebook):
        page, tab = centred(notebook)
        ttk.Label(tab, text=tr('Installer le jeu'), style='Big.TLabel').pack(anchor='w', pady=(0, 6))
        self.build_intro = paragraph(tab, BUILD_TEXTS[''])
        form = ttk.Frame(tab)
        form.pack(fill='x', pady=(14, 8))
        form.columnconfigure(1, weight=1)
        self.official = tk.StringVar()
        self.output_path = tk.StringVar(value=str(Path.home() / APK_NAME))
        self.artworks = tk.StringVar()
        self.form_row(form, 0, tr('Jeu officiel 1.10.4 :'), ttk.Entry(form, textvariable=self.official), tr('Choisir...'), self.pick_official)
        self.phone_save = tk.StringVar()
        self.save_choice = tk.StringVar()
        self.save_paths = {}
        self.save_box = ttk.Combobox(form, textvariable=self.save_choice, state='readonly')
        self.save_box.bind('<<ComboboxSelected>>', lambda _event: self.phone_save.set(str(self.save_paths.get(self.save_choice.get(), ''))))
        self.phone_save.trace_add('write', lambda *_: self.show_save())
        save_button = self.form_row(form, 1, tr('Sauvegarde exportée :'), self.save_box, tr('Dossier...'), self.pick_saves_folder)
        self.new_game = tk.BooleanVar(value=False)
        self.save_widgets = [(self.save_box, 'readonly'), (save_button, 'normal')]
        ttk.Checkbutton(form, text=tr('Nouvelle partie'), variable=self.new_game, command=self.new_game_changed).grid(row=2, column=1, sticky='w', padx=6, pady=3)
        self.form_row(form, 3, tr('Images de la galerie\n(facultatif) :'), ttk.Entry(form, textvariable=self.artworks), tr('Choisir...'), self.pick_artworks)
        self.form_row(form, 4, tr('APK à créer :'), ttk.Entry(form, textvariable=self.output_path), tr('Choisir...'), self.pick_output)
        actions = ttk.Frame(tab)
        actions.pack(anchor='w', pady=(6, 16))
        self.build_button = ttk.Button(actions, text=tr("1. Fabriquer l'APK"), command=self.build, style='Primary.TButton')
        self.build_button.pack(side='left')
        self.install_button = ttk.Button(actions, text=tr('2. Installer sur le téléphone'), command=self.install_apk, style='Primary.TButton')
        self.install_button.pack(side='left', padx=8)
        self.build_bar = Bar(self.root, actions)
        self.build_bar.frame.pack(side='left', padx=10)
        self.build_log, _, _ = framed_log(tab)
        stored = mises_a_jour.settings().get('dossier_sauvegardes')
        self.saves_folder = Path(stored) if stored and os.path.isdir(stored) else None
        self.list_saves()
        newest_iphone = next(iter(copies(self.saves_folder) or copies()), None)
        if newest_iphone:
            self.phone_save.set(str(newest_iphone / 'save.msgpack'))
        return page

    @staticmethod
    def form_row(form, row, label, field, button_text, command):
        ttk.Label(form, text=label, style='Soft.TLabel').grid(row=row, column=0, sticky='w', pady=3)
        field.grid(row=row, column=1, sticky='ew', padx=6)
        button = ttk.Button(form, text=button_text, command=command)
        button.grid(row=row, column=2)
        return button

    def list_saves(self):
        chosen = self.phone_save.get().strip()
        listed = saves(self.saves_folder) if self.saves_folder else []
        listed += [path for path in saves() if path not in listed]
        if chosen and Path(chosen) not in listed:
            listed.insert(0, Path(chosen))
        self.save_paths = {}
        for path in listed:
            label, number = (save_label(path), 2)
            while label in self.save_paths:
                label, number = (f'{save_label(path)} ({number})', number + 1)
            self.save_paths[label] = path
        self.save_box['values'] = list(self.save_paths)

    def show_save(self):
        self.list_saves()
        chosen = self.phone_save.get().strip()
        self.save_choice.set(next((label for label, path in self.save_paths.items() if str(path) == chosen), ''))

    def choose_save(self, path):
        self.phone_save.set(str(path))
        self.new_game.set(False)
        self.new_game_changed()

    def new_game_changed(self):
        for widget, normal in self.save_widgets:
            widget.configure(state='disabled' if self.new_game.get() else normal)

    def pick_official(self):
        path = filedialog.askopenfilename(title=tr('Jeu officiel 1.10.4'), filetypes=[(tr('Jeu Android'), '*.xapk *.apkm *.apk'), (tr('Tous les fichiers'), '*')])
        if path:
            self.official.set(path)

    def pick_saves_folder(self):
        start = self.saves_folder or (COPIES if COPIES.is_dir() else None)
        folder = filedialog.askdirectory(title=tr('Dossier des sauvegardes'), initialdir=str(start) if start else None)
        if not folder:
            return
        found = saves(folder)
        if not found:
            messagebox.showinfo(TITLE, tr('Aucune sauvegarde dans ce dossier.'))
            return
        self.saves_folder = Path(folder)
        mises_a_jour.remember(dossier_sauvegardes=folder)
        self.choose_save(found[0])

    def pick_artworks(self):
        path = filedialog.askdirectory(title=tr("Dossier d'images pour la galerie du jeu"))
        if path:
            self.artworks.set(path)

    def pick_output(self):
        path = filedialog.asksaveasfilename(title=tr('APK à créer'), defaultextension='.apk', initialfile=APK_NAME, filetypes=[(tr('APK Android'), '*.apk')])
        if path:
            self.output_path.set(path)

    def build_problem(self, official, out, phone_save, new_game, artworks):
        if not official or not os.path.isfile(official):
            return tr('Choisir le fichier du jeu officiel 1.10.4 (.xapk, .apkm ou .apk).')
        if artworks and (not os.path.isdir(artworks)):
            return tr("Le dossier d'images de la galerie n'existe pas.")
        if phone_save and (not is_save(phone_save)):
            return tr("Ce fichier n'est pas une sauvegarde Ranger Rumble.")
        if phone_save and new_game:
            return tr('Choisir une sauvegarde exportée ou « Nouvelle partie », pas les deux.')
        if not phone_save and (not new_game):
            return tr('Choisir une sauvegarde exportée, ou cocher « Nouvelle partie ».')
        if not out:
            return tr("Choisir où créer l'APK.")
        return None

    def build(self):
        official, out = (self.official.get().strip(), self.output_path.get().strip())
        phone_save = self.phone_save.get().strip() or None
        new_game = self.new_game.get()
        artworks = self.artworks.get().strip() or None
        problem = self.build_problem(official, out, phone_save, new_game, artworks)
        if problem:
            messagebox.showerror(TITLE, problem)
            return
        if self.copy_state:
            messagebox.showinfo(TITLE, tr("Arrête d'abord la copie (étape 1)."))
            return
        self.building = True
        self.target = self.build_log
        self.bar = self.build_bar
        self.build_bar.begin(tr('Fabrication'))
        self.busy(True)
        mises_a_jour.remember(official=official, output=out, artworks=artworks or '')

        def work():
            error = None
            try:
                patcher.build(official, out, save=phone_save, new_game=new_game, artworks=artworks)
            except SystemExit as stop:
                error = str(stop)
            except Exception as failure:
                error = describe(failure)
            self.later(self.built, out, error)
        in_background(work)

    def built(self, out, error):
        self.building = False
        self.busy(False)
        self.build_bar.done(error is None)
        if error:
            self.show_failure(error, tr("L'APK n'a pas pu être fabriqué :\n\n{error}", error=error))
            return
        print(tr("\nL'APK est prêt.\n"))
        if messagebox.askyesno(TITLE, tr("L'APK est prêt. L'installer sur le téléphone branché ?")):
            self.install_apk(out)
        elif messagebox.askyesno(TITLE, tr("L'APK est ici :\n{out}\n\nOuvrir son dossier ?", out=out)):
            open_folder(Path(out).parent)

    def sending(self, bar):
        return lambda fraction, direct=False: self.later(bar.sending, fraction, direct)

    def busy(self, on):
        for button in (self.build_button, self.install_button):
            button.configure(state='disabled' if on else 'normal')

    def install_apk(self, out=None):
        if self.building:
            messagebox.showinfo(TITLE, tr('Il faut attendre la fin de la fabrication en cours.'))
            return
        out = out or self.output_path.get().strip()
        if not (out and os.path.isfile(out)):
            out = filedialog.askopenfilename(title=tr('APK à installer'), filetypes=[('APK', '*.apk')])
            if not out:
                return
        found = self.editor.phone(need_game=False)
        if not found:
            return
        adb, serial = found
        replace = False
        signature = mises_a_jour.phone_signature(adb, serial)
        if signature and signature != copie_android.OFFICIAL_SIGNATURE:
            replace = messagebox.askyesnocancel(TITLE, tr("Le jeu hors ligne est déjà sur le téléphone.\n\nRemplacer sa progression par la sauvegarde de cet APK ? (L'ancienne est gardée dans Sauvegardes.)"))
            if replace is None:
                return
        self.building = True
        self.target = self.build_log
        self.busy(True)
        self.build_bar.begin(tr('Installation'))

        def work():
            error, other, kept = (None, False, None)
            try:
                print(tr('Installation sur le téléphone...'))
                copie_android.install(adb, serial, out, self.sending(self.build_bar))
                if replace:
                    kept = mises_a_jour.phone_save(adb, serial, str(self.copies_folder()))
                    mises_a_jour.apply_apk_save(adb, serial, out)
                    print(tr("La sauvegarde de l'APK remplace celle du téléphone."))
            except copie_android.Problem as problem:
                error = str(problem)
                other = isinstance(problem, copie_android.OtherSignature)
            except Exception as failure:
                error = describe(failure)
            self.later(self.installed, adb, serial, out, error, other, kept)
        in_background(work)

    def reinstall(self, adb, serial, out, bar, keep_save, then):
        bar.begin(tr('Installation'))

        def work():
            error, kept = (None, None)
            try:
                if keep_save:
                    kept = mises_a_jour.phone_save(adb, serial, str(self.copies_folder()))
                    if kept:
                        print(tr('Sauvegarde du téléphone copiée : {copy}', copy=kept))
                print(tr('Désinstallation, puis installation...'))
                mises_a_jour.reinstall(adb, serial, out, self.sending(bar))
            except Exception as failure:
                error = str(failure)
            self.later(then, error, kept)
        in_background(work)

    def installed(self, adb, serial, out, error, other, kept=None):
        if other and messagebox.askyesno(TITLE, tr('Un autre Ranger Rumble est sur le téléphone. Le désinstaller et installer celui-ci ?\n\nSa progression sur le téléphone sera effacée.')):
            self.reinstall(adb, serial, out, self.build_bar, True, lambda problem, copy: self.installed(adb, serial, out, problem, False, copy))
            return
        self.building = False
        self.busy(False)
        self.build_bar.done(error is None)
        if error:
            self.show_failure(error, tr('Installation impossible :\n\n{error}', error=error))
            return
        model = next((m for p, _, m in copie_android.phones(adb) if p == serial and m), tr('le téléphone'))
        print(tr('\nLe jeu est installé sur {model}.\n', model=model))
        text = tr('Le jeu est installé sur {model}.', model=model)
        if kept:
            text += tr('\n\nAncienne sauvegarde copiée :\n{name}', name=Path(kept).name)
        messagebox.showinfo(TITLE, text)

    def updates_tab(self, notebook):
        page, tab = centred(notebook)
        info = mises_a_jour.current()
        self.version = info['version']
        self.game = info.get('jeu') or info['version']
        ttk.Label(tab, text=tr('Mises à jour'), style='Big.TLabel').pack(anchor='w', pady=(0, 12))
        ttk.Label(tab, text=tr("L'outil"), style='Heading.TLabel').pack(anchor='w', pady=(0, 4))
        self.release_text = paragraph(tab, tr('Version {version}. Recherche de mise à jour...', version=self.version))
        row = ttk.Frame(tab)
        row.pack(anchor='w', pady=(10, 4))
        ttk.Button(row, text=tr('Vérifier maintenant'), command=lambda: in_background(lambda: self.check_release(True))).pack(side='left')
        self.tool_button = ttk.Button(row, text=tr("Mettre à jour l'outil"), command=self.update_tool, state='disabled', style='Primary.TButton')
        self.tool_button.pack(side='left', padx=8)
        ttk.Separator(tab).pack(fill='x', pady=16)
        ttk.Label(tab, text=tr('Le jeu du téléphone'), style='Heading.TLabel').pack(anchor='w', pady=(0, 4))
        paragraph(tab, tr('Version {game}. Brancher le téléphone (débogage USB activé) et cliquer ci-dessous. La progression est gardée.', game=self.game))
        row = ttk.Frame(tab)
        row.pack(anchor='w', pady=(10, 16))
        self.phone_button = ttk.Button(row, text=tr('Mettre à jour le jeu du téléphone'), command=self.update_phone, style='Primary.TButton')
        self.phone_button.pack(side='left')
        self.update_bar = Bar(self.root, row)
        self.update_bar.frame.pack(side='left', padx=10)
        self.update_log, _, _ = framed_log(tab)
        return page

    def restore_settings(self):
        stored = mises_a_jour.settings()
        for key, variable in (('official', self.official), ('artworks', self.artworks), ('output', self.output_path)):
            value = stored.get(key)
            if value and (key == 'output' or os.path.exists(value)) and (not variable.get().strip()):
                variable.set(value)
        if stored.get('plateforme') in dict(PLATFORMS):
            self.platform.set(stored['plateforme'])
            self.platform_changed()

    def check_release(self, asked=False):
        try:
            release = mises_a_jour.latest_release()
        except Exception:
            release = False
        self.later(self.release_found, release, asked)

    def release_found(self, release, asked):
        self.release = release
        if release is False:
            self.release_text.configure(text=tr('Version {version}. Vérification impossible.', version=self.version))
            self.tool_button.configure(state='disabled')
        elif release is None:
            self.release_text.configure(text=tr('Version {version}. Aucune mise à jour trouvée.', version=self.version))
            self.tool_button.configure(state='disabled')
        elif mises_a_jour.newer(release['version'], self.version):
            notes = tr('\n\nNouveautés :\n{v}', v=release['notes'][:600]) if release['notes'] else ''
            game = release.get('jeu')
            after = tr(' Il faut ensuite mettre à jour le jeu du téléphone.') if game and mises_a_jour.newer(game, self.game) else ''
            self.release_text.configure(text=tr('Version {version}. La version {version2} est disponible !{after}{notes}', version=self.version, version2=release['version'], after=after, notes=notes))
            self.tool_button.configure(state='normal')
            self.root.title(tr('{TITLE}  —  nouvelle version {version} disponible (Mises à jour)', TITLE=TITLE, version=release['version']))
            self.home.set_release(release['version'])
        else:
            self.release_text.configure(text=tr('Version {version}, à jour.', version=self.version))
            self.tool_button.configure(state='disabled')
            if asked:
                messagebox.showinfo(TITLE, tr("L'outil est déjà à jour."))

    def update_tool(self):
        release = self.release
        if not release or self.building:
            return
        if not messagebox.askyesno(TITLE, tr("Installer la version {version} ? L'outil se fermera, il faudra le relancer.", version=release['version'])):
            return
        self.target = self.update_log
        self.tool_button.configure(state='disabled')

        def work():
            error = None
            try:
                mises_a_jour.update_tool(release, str(ROOT))
            except Exception as failure:
                error = str(failure)
            self.later(self.tool_updated, error)
        in_background(work)

    def tool_updated(self, error):
        if error:
            self.show_failure(error, tr("La mise à jour de l'outil a échoué :\n\n{error}", error=error))
            self.tool_button.configure(state='normal')
            return
        messagebox.showinfo(TITLE, tr("L'outil est à jour. Il faut le relancer."))
        self.close()

    def update_phone(self):
        if self.building:
            messagebox.showinfo(TITLE, tr('Il faut attendre la fin de la fabrication en cours.'))
            return
        official = self.official.get().strip()
        if not (official and os.path.isfile(official)):
            messagebox.showinfo(TITLE, tr("Remplis d'abord l'étape 2 (jeu officiel)."))
            return
        exported = self.phone_save.get().strip() or None
        exported = exported if exported and is_save(exported) else None
        found = self.editor.phone()
        if not found:
            return
        adb, serial = found
        signature = mises_a_jour.phone_signature(adb, serial)
        if signature == copie_android.OFFICIAL_SIGNATURE:
            messagebox.showinfo(TITLE, tr("Le téléphone a le jeu officiel : fabrique d'abord l'APK (étape 2)."))
            return
        phone_game = mises_a_jour.phone_game_version(adb, serial)
        if phone_game and (not mises_a_jour.newer(self.game, phone_game)) and (not messagebox.askyesno(TITLE, tr('Le jeu du téléphone est déjà à jour ({phone_game}). Le réinstaller quand même ?', phone_game=phone_game))):
            return
        out = self.output_path.get().strip() or str(Path.home() / APK_NAME)
        artworks = self.artworks.get().strip() or None
        self.building = True
        self.target = self.update_log
        self.bar = self.update_bar
        self.update_bar.begin(tr('Fabrication'))
        self.phone_button.configure(state='disabled')

        def work():
            error, retry, save = (None, False, None)
            try:
                save = mises_a_jour.phone_save(adb, serial, str(self.copies_folder()))
                if save:
                    print(tr('Sauvegarde du téléphone lue.'))
                elif exported:
                    print(tr('Sauvegarde du téléphone illisible : la sauvegarde exportée (étape 2) sera utilisée.'))
                    save = exported
                else:
                    raise SystemExit(tr("La sauvegarde du téléphone n'a pas pu être lue."))
                patcher.build(official, out, save=save, artworks=artworks)
                print(tr('Installation sur le téléphone...'))
                self.later(self.update_bar.begin, tr('Installation'))
                copie_android.install(adb, serial, out, self.sending(self.update_bar))
            except copie_android.Problem as problem:
                error = str(problem)
                retry = isinstance(problem, copie_android.OtherSignature) and save is not None
            except SystemExit as stop:
                error = str(stop)
            except Exception as failure:
                error = describe(failure)
            self.later(self.phone_updated, adb, serial, out, error, retry)
        in_background(work)

    def phone_updated(self, adb, serial, out, error, retry):
        if retry and messagebox.askyesno(TITLE, tr("Ce jeu vient d'un autre ordinateur : il faut d'abord le désinstaller. La progression est gardée, pas les réglages du jeu.\n\nDésinstaller et réinstaller ?")):
            self.reinstall(adb, serial, out, self.update_bar, False, lambda problem, _copy: self.phone_updated(adb, serial, out, problem, False))
            return
        self.building = False
        self.phone_button.configure(state='normal')
        self.update_bar.done(error is None)
        if error:
            self.show_failure(error, tr("La mise à jour du téléphone n'a pas abouti :\n\n{error}", error=error))
            return
        print(tr('\nLe jeu du téléphone est à jour.\n'))
        messagebox.showinfo(TITLE, tr('Le jeu du téléphone est à jour. La progression est gardée.'))

    def language_changed(self, _event=None):
        code = next((code for code, name in langues.LANGUAGES if name == self.language.get()))
        if code == langues.CURRENT:
            return
        if not self.close(restart=True):
            self.language.set(dict(langues.LANGUAGES)[langues.CURRENT])
            return
        mises_a_jour.remember(langue=code)
        self.restart = True

    def close(self, restart=False):
        if self.editor.save is not None and self.editor.save.changed() and (not messagebox.askyesno(TITLE, tr('Changements non enregistrés dans « Éditer ». Continuer quand même ?') if restart else tr('Changements non enregistrés dans « Éditer ». Quitter quand même ?'))):
            return False
        if self.building and (not messagebox.askyesno(TITLE, tr('Fabrication en cours. Continuer quand même ?') if restart else tr('Fabrication en cours. Quitter quand même ?'))):
            return False
        self.stop_copy()
        self.root.destroy()
        return True
NEW_APP = 'Launcher Ratchet Ranger Rumble.app'

def open_new_launcher():
    mac_13 = sys.platform == 'darwin' and int((platform.mac_ver()[0] or '0').split('.')[0]) >= 13
    if mac_13 and (ROOT / NEW_APP).is_dir() and (HERE / 'service.py').is_file():
        subprocess.Popen(['open', str(ROOT / NEW_APP)])
        return True
    if os.name == 'nt' and (HERE / 'lanceur_web.py').is_file() and (HERE / 'web' / 'index.html').is_file():
        import lanceur_web
        lanceur_web.main()
        return True
    return False

def windows_look():
    import ctypes
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('RangerRumble.HorsLigne')
    except (AttributeError, OSError):
        pass
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-5))
    except (AttributeError, OSError):
        pass

def start_failed(details):
    log = Path.home() / '.sauvegarde-rr' / 'erreur.log'
    try:
        log.parent.mkdir(exist_ok=True)
        log.write_text(details, encoding='utf-8')
    except OSError:
        pass
    sys.stdout, sys.stderr = (sys.__stdout__, sys.__stderr__)
    messagebox.showerror(TITLE, details[-1500:])

def restart_tool():
    sys.stdout, sys.stderr = (sys.__stdout__, sys.__stderr__)
    command = [sys.executable, '-I', os.path.abspath(__file__)]
    if os.name == 'nt':
        subprocess.Popen(command)
    else:
        os.execv(sys.executable, command)

def main():
    if open_new_launcher():
        return
    if os.name == 'nt':
        windows_look()
    root = tk.Tk()
    try:
        application = Application(root)
    except Exception:
        import traceback
        start_failed(traceback.format_exc())
        raise
    root.report_callback_exception = lambda kind, error, trace: messagebox.showerror(TITLE, tr('Erreur : {error}', error=error))
    root.mainloop()
    if application.restart:
        restart_tool()
if __name__ == '__main__':
    main()
