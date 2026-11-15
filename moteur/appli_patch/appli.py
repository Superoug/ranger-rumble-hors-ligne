import asyncio
import importlib.util
import io
import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import copie_android
import donnees_capture
import editeur
import mises_a_jour
import patcher
ROOT = HERE.parent.parent if HERE.parent.name == 'moteur' else HERE.parent
COPIES = Path(os.environ.get('RR_COPIES') or ROOT / 'Sauvegardes')
TOOL = next((path for path in (HERE.parent / 'outil' / 'sauvegarde_rr.py', HERE.parent / 'outil_sauvegarde_source' / 'sauvegarde_rr.py') if path.exists()))
TITLE = 'Ranger Rumble hors ligne'
PLATFORMS = (('ios', 'iPhone ou iPad'), ('android', 'Android'))
COPY_TEXTS = {'': "Choisis d'abord, en haut de la fenêtre, où est ton jeu Ranger Rumble.", 'ios': "Garde une copie de ta sauvegarde officielle, et les données du jeu qu'il faut pour fabriquer l'APK hors ligne, tant que les serveurs sont ouverts (jusqu'au 1er mai 2027). L'iPhone ou l'iPad doit être sur le même Wi-Fi que cet ordinateur : choisis ce Wi-Fi ci-dessous et clique sur Démarrer. Vise ensuite le QR code avec l'appareil photo de l'iPhone et suis les étapes : le profil RatchetRR règle tout seul l'iPhone, il n'y a plus de proxy à taper.", 'android': "Ta sauvegarde n'est pas sur ton téléphone : seuls les serveurs officiels la gardent, et Android ne laisse aucune autre appli la lire (sans root). Ce que l'outil peut copier par le câble, ce sont les données du jeu, qui servent à fabriquer l'APK hors ligne avec une nouvelle partie ou une sauvegarde exportée.\nBranche le téléphone (débogage USB activé, voir LIS_MOI.txt) et clique sur « Copier par le câble ». Ne désinstalle pas le jeu officiel pour cela."}
COPY_BUTTONS = {'': 'Démarrer', 'ios': 'Démarrer', 'android': 'Copier par le câble'}
BUILD_TEXTS = {'': "Fabrique l'APK hors ligne à partir du jeu officiel en versions 1.10.4 et 1.10.3 (fichiers .xapk ou .apkm que tu te procures toi-même ; la 1.10.3 donne les 7 héros jamais sortis) et d'une copie faite dans l'onglet 1, dont la sauvegarde est mise dans l'APK. Il faut environ 5 Go libres.", 'ios': "Fabrique l'APK hors ligne à partir du jeu officiel en versions 1.10.4 et 1.10.3 (fichiers .xapk ou .apkm que tu te procures toi-même ; la 1.10.3 donne les 7 héros jamais sortis) et de ta copie faite dans l'onglet 1. Il faut environ 5 Go libres. La version hors ligne se joue sur un téléphone ou une tablette Android : il n'y en a pas pour iPhone ou iPad.", 'android': "Fabrique l'APK hors ligne à partir du jeu officiel en versions 1.10.4 et 1.10.3 (fichiers .xapk ou .apkm que tu te procures toi-même ; la 1.10.3 donne les 7 héros jamais sortis) et de la copie faite par le câble (onglet 1), avec une sauvegarde exportée ou une nouvelle partie. Il faut environ 5 Go libres. Sur ton téléphone, désinstalle le jeu officiel avant d'installer l'APK (même nom d'appli) : fais-le seulement quand tu n'en as plus besoin."}
STATUS = {'ready': 'prête', 'partial': 'données du serveur incomplètes', 'old': 'ancienne copie, sans les données du serveur : refais-en une'}
NO_SAVE = 'sans sauvegarde'

def load_tool():
    spec = importlib.util.spec_from_file_location('sauvegarde_rr', TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.OUT = COPIES
    return module

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

def open_folder(path):
    path = str(path)
    if sys.platform == 'win32':
        os.startfile(path)
    elif sys.platform == 'darwin':
        subprocess.Popen(['open', path])
    else:
        subprocess.Popen(['xdg-open', path])

def paragraph(parent, text):
    label = ttk.Label(parent, text=text, justify='left')
    label.bind('<Configure>', lambda event: label.configure(wraplength=event.width))
    label.pack(fill='x', anchor='w')
    return label

def is_save(path):
    import msgpack
    try:
        with open(path, 'rb') as handle:
            value = msgpack.unpackb(handle.read(8 << 20), raw=False, strict_map_key=False, timestamp=0)
    except (OSError, ValueError, msgpack.UnpackException):
        return False
    parts = value.get('save') if isinstance(value, dict) else None
    return isinstance(parts, dict) and 'UnlockedHeroes' in parts

def status(folder):
    if not (Path(folder) / 'donnees_serveur').is_dir():
        return 'old'
    return 'partial' if donnees_capture.missing_files(str(folder)) else 'ready'

def has_save(folder):
    return (Path(folder) / 'save.msgpack').is_file()

def label_of(folder):
    state = STATUS[status(folder)]
    return f"{Path(folder).name}  ({state}{('' if has_save(folder) else ', ' + NO_SAVE)})"

def copies():
    found = []
    if COPIES.is_dir():
        for folder in COPIES.iterdir():
            if has_save(folder) or (folder / 'donnees_serveur').is_dir():
                found.append((folder.stat().st_mtime, label_of(folder), folder))
    return [(label, folder) for _, label, folder in sorted(found, reverse=True)]

class Application:

    def __init__(self, root):
        self.root = root
        self.output = Output()
        self.target = None
        self.copy_state = None
        self.tool = None
        self.wifi_loaded = False
        self.building = False
        root.title(TITLE)
        root.geometry('980x700')
        root.minsize(760, 520)
        top = ttk.Frame(root, padding=(14, 12, 14, 0))
        top.pack(fill='x')
        ttk.Label(top, text='Mon jeu Ranger Rumble est sur :').pack(side='left')
        self.platform = tk.StringVar(value='')
        self.platform_buttons = []
        for value, label in PLATFORMS:
            button = ttk.Radiobutton(top, text=label, value=value, variable=self.platform, command=self.platform_changed)
            button.pack(side='left', padx=10)
            self.platform_buttons.append(button)
        notebook = ttk.Notebook(root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        notebook.add(self.copy_tab(notebook), text='  1. Copier la sauvegarde  ')
        notebook.add(self.build_tab(notebook), text="  2. Fabriquer l'APK  ")
        self.editor = editeur.Editor(notebook, self)
        notebook.add(self.editor, text='  3. Éditer une sauvegarde  ')
        notebook.add(self.updates_tab(notebook), text='  4. Mises à jour  ')
        self.notebook = notebook
        self.restore_settings()
        threading.Thread(target=self.check_release, daemon=True).start()
        sys.stdout = self.output
        sys.stderr = self.output
        root.protocol('WM_DELETE_WINDOW', self.close)
        root.after(100, self.pump)

    @staticmethod
    def copies_folder():
        COPIES.mkdir(exist_ok=True)
        return COPIES

    @staticmethod
    def log_box(parent):
        box = tk.Text(parent, height=18, wrap='word', state='disabled', font=('Courier', 11))
        scroll = ttk.Scrollbar(parent, command=box.yview)
        box.configure(yscrollcommand=scroll.set)
        return (box, scroll)

    def pump(self):
        try:
            while True:
                text = self.output.queue.get_nowait()
                if self.target is not None:
                    self.target.configure(state='normal')
                    self.target.insert('end', text)
                    self.target.see('end')
                    self.target.configure(state='disabled')
        except queue.Empty:
            pass
        self.root.after(100, self.pump)

    def copy_tab(self, notebook):
        tab = ttk.Frame(notebook, padding=12)
        self.copy_intro = paragraph(tab, COPY_TEXTS[''])
        self.wifi_row = ttk.Frame(tab)
        ttk.Label(self.wifi_row, text="Wi-Fi de l'iPhone :").pack(side='left')
        self.wifi = tk.StringVar(value='')
        self.wifi_box = ttk.Combobox(self.wifi_row, textvariable=self.wifi, width=34)
        self.wifi_box.pack(side='left', padx=8)
        ttk.Label(self.wifi_row, text="(son nom dans Réglages > Wi-Fi de l'iPhone)").pack(side='left')
        self.wifi.trace_add('write', self.wifi_changed)
        buttons = ttk.Frame(tab)
        buttons.pack(anchor='w', pady=10)
        self.copy_buttons = buttons
        self.copy_button = ttk.Button(buttons, text='Démarrer', command=self.toggle_copy, state='disabled')
        self.copy_button.pack(side='left')
        ttk.Button(buttons, text='Ouvrir le dossier des copies', command=lambda: (COPIES.mkdir(exist_ok=True), open_folder(COPIES))).pack(side='left', padx=8)
        frame = ttk.Frame(tab)
        frame.pack(fill='both', expand=True)
        self.copy_log, scroll = self.log_box(frame)
        self.qr_panel = ttk.Frame(frame)
        self.qr_label = ttk.Label(self.qr_panel)
        self.qr_label.pack()
        self.qr_text = ttk.Label(self.qr_panel, justify='center', wraplength=230)
        self.qr_text.pack(pady=6)
        self.copy_scroll = scroll
        scroll.pack(side='right', fill='y')
        self.copy_log.pack(fill='both', expand=True)
        return tab

    def load_wifi(self):
        self.wifi_loaded = True

        def work():
            try:
                current, known = load_tool().wifi_networks()
            except Exception:
                current, known = ('', [])
            self.root.after(0, lambda: self.wifi_found(current, known))
        threading.Thread(target=work, daemon=True).start()

    def wifi_found(self, current, known):
        self.wifi_box.configure(values=known)
        if current and (not self.wifi.get()):
            self.wifi.set(current)

    def wifi_changed(self, *_):
        if self.tool is not None:
            self.tool.WIFI = self.wifi.get().strip()

    def show_qr(self, url):
        try:
            import segno
            data = segno.make(url, error='m').png_data_uri(scale=6, border=2).split(',', 1)[1]
            self.qr_image = tk.PhotoImage(data=data)
            self.qr_label.configure(image=self.qr_image)
        except Exception:
            self.qr_label.configure(image='')
        self.qr_text.configure(text=f"Vise ce code avec l'appareil photo de l'iPhone\n{url}")
        self.qr_panel.pack(side='right', anchor='n', padx=(10, 0), before=self.copy_scroll)

    def hide_qr(self):
        self.qr_panel.pack_forget()

    def platform_changed(self):
        platform = self.platform.get()
        self.copy_intro.configure(text=COPY_TEXTS[platform])
        self.build_intro.configure(text=BUILD_TEXTS[platform])
        if not self.copy_state and (not getattr(self, 'android_copying', False)):
            self.copy_button.configure(text=COPY_BUTTONS[platform], state='normal' if platform else 'disabled')
        if platform == 'ios':
            self.wifi_row.pack(fill='x', pady=(10, 0), before=self.copy_buttons)
            if not self.wifi_loaded:
                self.load_wifi()
        else:
            self.wifi_row.pack_forget()

    def toggle_copy(self):
        if self.platform.get() == 'android':
            self.copy_android()
            return
        if self.copy_state:
            loop, master = self.copy_state
            loop.call_soon_threadsafe(master.shutdown)
            self.copy_button.configure(text='Arrêt...', state='disabled')
            return
        if self.building:
            messagebox.showinfo(TITLE, "Attends la fin de la fabrication de l'APK.")
            return
        if not self.wifi.get().strip() and (not messagebox.askyesno(TITLE, "Aucun Wi-Fi choisi : le profil ne pourra pas régler l'iPhone tout seul, il faudra régler son proxy à la main. Continuer quand même ?")):
            return
        self.target = self.copy_log
        self.copy_button.configure(text='Arrêter')
        for button in self.platform_buttons:
            button.configure(state='disabled')

        def ready(master, _page):
            self.copy_state = (asyncio.get_running_loop(), master)

        def work():
            try:
                tool = load_tool()
                tool.WIFI = self.wifi.get().strip()
                self.tool = tool
                address, proxy_port, page_port = tool.prepare()
                self.root.after(0, lambda: self.show_qr(f'http://{address}:{page_port}'))
                asyncio.run(tool.run(address, proxy_port, page_port, ready))
            except Exception as error:
                print(f'\nErreur : {error}')
            finally:
                self.copy_state = None
                self.tool = None
                print("\nCopie arrêtée. Quand tu as fini, supprime le profil RatchetRR de l'iPhone (Réglages > Général > VPN et gestion de l'appareil) : il oublie alors ce Wi-Fi, reconnecte-toi avec ton mot de passe.\n")
                self.root.after(0, self.hide_qr)
                self.root.after(0, self.copy_stopped)
                self.root.after(0, self.refresh_copies)
        threading.Thread(target=work, daemon=True).start()

    def copy_android(self):
        if self.building:
            messagebox.showinfo(TITLE, "Attends la fin de la fabrication de l'APK.")
            return
        adb = copie_android.find_adb()
        if not adb and (not messagebox.askyesno(TITLE, "Pour lire le téléphone par le câble, l'outil a besoin des outils Android de Google (« platform-tools », environ 10 Mo). Les télécharger maintenant depuis le site de Google ?\n\nEn les téléchargeant, tu acceptes leurs conditions d'utilisation : " + copie_android.ADB_PAGE)):
            return
        self.target = self.copy_log
        self.android_copying = True
        self.copy_button.configure(text='Copie...', state='disabled')
        for button in self.platform_buttons:
            button.configure(state='disabled')

        def work():
            folder = None
            try:
                tool = adb or copie_android.download_adb()
                ready = [p for p in copie_android.phones(tool) if p[1] == 'device']
                waiting = [p for p in copie_android.phones(tool) if p[1] == 'unauthorized']
                if not ready:
                    if waiting:
                        raise copie_android.Problem('Le téléphone est branché, mais il attend ton accord : touche « Autoriser » dans la fenêtre « Autoriser le débogage USB ? » sur son écran, puis recommence.')
                    raise copie_android.Problem('Aucun téléphone trouvé. Vérifie que le débogage USB est activé (voir LIS_MOI.txt), que le câble transmet les données, puis recommence.')
                COPIES.mkdir(exist_ok=True)
                refusals = []
                for serial, _, model in ready:
                    print(f'Téléphone : {model or serial}.')
                    try:
                        folder = copie_android.copy_phone(tool, serial, str(COPIES))
                        break
                    except copie_android.Problem as problem:
                        refusals.append(str(problem))
                        if len(ready) > 1:
                            print(f'  {problem}')
                if folder is None:
                    raise copie_android.Problem(refusals[0] if len(refusals) == 1 else "Aucun des téléphones branchés n'a pu être copié.")
                if has_save(folder):
                    print("\nTu peux passer à l'onglet 2 : cette copie a une sauvegarde.\n")
                else:
                    print("\nTu peux passer à l'onglet 2 : choisis cette copie, puis une sauvegarde exportée ou « Nouvelle partie ».\n")
            except copie_android.Problem as problem:
                print(f'\n{problem}\n')
            except Exception as error:
                print(f'\nErreur : {error}\n')
            finally:
                self.android_copying = False
                self.root.after(0, self.copy_stopped)
                self.root.after(0, lambda: self.refresh_copies(select=Path(folder) if folder else None))
        threading.Thread(target=work, daemon=True).start()

    def copy_stopped(self):
        self.copy_button.configure(text=COPY_BUTTONS[self.platform.get()])
        for button in self.platform_buttons:
            button.configure(state='normal')
        self.platform_changed()

    def build_tab(self, notebook):
        tab = ttk.Frame(notebook, padding=12)
        self.build_intro = paragraph(tab, BUILD_TEXTS[''])
        form = ttk.Frame(tab)
        form.pack(fill='x', pady=10)
        form.columnconfigure(1, weight=1)
        self.official = tk.StringVar()
        self.old_version = tk.StringVar()
        self.copy_choice = tk.StringVar()
        self.output_path = tk.StringVar(value=str(Path.home() / 'RangerRumble_hors_ligne.apk'))
        ttk.Label(form, text='Jeu officiel 1.10.4 :').grid(row=0, column=0, sticky='w', pady=3)
        ttk.Entry(form, textvariable=self.official).grid(row=0, column=1, sticky='ew', padx=6)
        ttk.Button(form, text='Choisir...', command=self.pick_official).grid(row=0, column=2)
        ttk.Label(form, text='Jeu officiel 1.10.3 :').grid(row=1, column=0, sticky='w', pady=3)
        ttk.Entry(form, textvariable=self.old_version).grid(row=1, column=1, sticky='ew', padx=6)
        ttk.Button(form, text='Choisir...', command=self.pick_old_version).grid(row=1, column=2)
        ttk.Label(form, text='Copie de sauvegarde :').grid(row=2, column=0, sticky='w', pady=3)
        self.copy_box = ttk.Combobox(form, textvariable=self.copy_choice, state='readonly')
        self.copy_box.grid(row=2, column=1, sticky='ew', padx=6)
        ttk.Button(form, text='Autre dossier...', command=self.pick_copy).grid(row=2, column=2)
        self.phone_save = tk.StringVar()
        ttk.Label(form, text='Sauvegarde exportée\n(facultatif) :').grid(row=3, column=0, sticky='w', pady=3)
        ttk.Entry(form, textvariable=self.phone_save).grid(row=3, column=1, sticky='ew', padx=6)
        ttk.Button(form, text='Choisir...', command=self.pick_phone_save).grid(row=3, column=2)
        self.new_game = tk.BooleanVar(value=False)
        ttk.Checkbutton(form, text='Nouvelle partie (sans sauvegarde : un nouveau compte, tutoriel passé, avec le héros de départ)', variable=self.new_game).grid(row=4, column=1, sticky='w', padx=6, pady=3)
        self.artworks = tk.StringVar()
        ttk.Label(form, text='Images de la galerie\n(facultatif) :').grid(row=5, column=0, sticky='w', pady=3)
        ttk.Entry(form, textvariable=self.artworks).grid(row=5, column=1, sticky='ew', padx=6)
        ttk.Button(form, text='Choisir...', command=self.pick_artworks).grid(row=5, column=2)
        ttk.Label(form, text='APK à créer :').grid(row=6, column=0, sticky='w', pady=3)
        ttk.Entry(form, textvariable=self.output_path).grid(row=6, column=1, sticky='ew', padx=6)
        ttk.Button(form, text='Choisir...', command=self.pick_output).grid(row=6, column=2)
        paragraph(tab, "Sauvegarde exportée : un fichier exporté depuis RR Options (le jeu hors ligne sur Android), ou le save.msgpack d'une copie. S'il est choisi, l'APK part de cette progression au lieu de la sauvegarde de la copie. Une copie faite par le câble (Android) n'a pas de sauvegarde : choisis alors une sauvegarde exportée, ou « Nouvelle partie ». Images de la galerie : tes images (png, jpg), à voir dans le jeu par le menu (les 3 traits) > ARTBOOK.")
        actions = ttk.Frame(tab)
        actions.pack(anchor='w', pady=4)
        self.build_button = ttk.Button(actions, text="Fabriquer l'APK", command=self.build)
        self.build_button.pack(side='left')
        self.progress = ttk.Progressbar(actions, mode='indeterminate', length=240)
        self.progress.pack(side='left', padx=10)
        frame = ttk.Frame(tab)
        frame.pack(fill='both', expand=True, pady=(8, 0))
        self.build_log, scroll = self.log_box(frame)
        scroll.pack(side='right', fill='y')
        self.build_log.pack(fill='both', expand=True)
        self.copy_folders = {}
        self.refresh_copies()
        return tab

    def refresh_copies(self, select=None):
        listed = copies()
        if select and all((folder != select for _, folder in listed)):
            listed.insert(0, (label_of(select), select))
        self.copy_folders = dict(listed)
        self.copy_box['values'] = [label for label, _ in listed]
        if listed and (select or not self.copy_choice.get()):
            self.copy_choice.set(next((label for label, folder in listed if folder == (select or listed[0][1]))))

    def pick_official(self):
        path = filedialog.askopenfilename(title='Jeu officiel 1.10.4', filetypes=[('Jeu Android', '*.xapk *.apkm'), ('Tous les fichiers', '*')])
        if path:
            self.official.set(path)

    def pick_old_version(self):
        path = filedialog.askopenfilename(title='Jeu officiel 1.10.3', filetypes=[('Jeu Android', '*.apkm *.xapk'), ('Tous les fichiers', '*')])
        if path:
            self.old_version.set(path)

    def pick_copy(self):
        path = filedialog.askdirectory(title="Dossier d'une copie de sauvegarde", initialdir=str(COPIES))
        if not path:
            return
        if not has_save(path) and (not (Path(path) / 'donnees_serveur').is_dir()):
            messagebox.showerror(TITLE, 'Ce dossier ne contient pas de copie (save.msgpack ou donnees_serveur).')
            return
        self.refresh_copies(select=Path(path))

    def pick_phone_save(self):
        path = filedialog.askopenfilename(title='Sauvegarde exportée depuis RR Options', filetypes=[('Sauvegarde', '*.msgpack'), ('Tous les fichiers', '*')])
        if path:
            self.phone_save.set(path)

    def pick_artworks(self):
        path = filedialog.askdirectory(title="Dossier d'images pour la galerie du jeu")
        if path:
            self.artworks.set(path)

    def pick_output(self):
        path = filedialog.asksaveasfilename(title='APK à créer', defaultextension='.apk', initialfile='RangerRumble_hors_ligne.apk', filetypes=[('APK Android', '*.apk')])
        if path:
            self.output_path.set(path)

    def build(self):
        official, out = (self.official.get().strip(), self.output_path.get().strip())
        folder = self.copy_folders.get(self.copy_choice.get())
        old = self.old_version.get().strip()
        if not official or not os.path.isfile(official):
            messagebox.showerror(TITLE, 'Choisis le fichier du jeu officiel 1.10.4 (.xapk ou .apkm).')
            return
        if not old or not os.path.isfile(old):
            messagebox.showerror(TITLE, 'Choisis aussi le fichier du jeu officiel 1.10.3 (.apkm ou .xapk) : il contient les 7 héros jamais sortis.')
            return
        if folder is None:
            messagebox.showerror(TITLE, 'Choisis une copie de sauvegarde (onglet 1, ou Autre dossier).')
            return
        if status(folder) == 'old':
            messagebox.showerror(TITLE, "Cette copie a été faite avec l'ancienne version de l'outil, qui ne gardait pas les données du serveur. Refais une copie (onglet 1).")
            return
        lacking = donnees_capture.missing_files(str(folder))
        if lacking:
            messagebox.showerror(TITLE, "Cette copie n'a pas toutes les données du serveur. Refais une copie (onglet 1) : ouvre le jeu et attends l'écran d'accueil.\n\nManque : " + ', '.join(lacking[:6]))
            return
        phone_save = self.phone_save.get().strip() or None
        new_game = self.new_game.get()
        artworks = self.artworks.get().strip() or None
        if artworks and (not os.path.isdir(artworks)):
            messagebox.showerror(TITLE, "Le dossier d'images de la galerie n'existe pas.")
            return
        if phone_save and (not is_save(phone_save)):
            messagebox.showerror(TITLE, "La sauvegarde exportée choisie n'est pas une sauvegarde de Ranger Rumble.")
            return
        if phone_save and new_game:
            messagebox.showerror(TITLE, 'Choisis soit une sauvegarde exportée, soit « Nouvelle partie », pas les deux.')
            return
        if not phone_save and (not new_game) and (not has_save(folder)):
            messagebox.showerror(TITLE, "Cette copie n'a pas de sauvegarde (copie faite par le câble) : choisis une sauvegarde exportée, ou coche « Nouvelle partie ».")
            return
        if not out:
            messagebox.showerror(TITLE, "Choisis où créer l'APK.")
            return
        if self.copy_state:
            messagebox.showinfo(TITLE, "Arrête d'abord la copie (onglet 1).")
            return
        self.building = True
        self.target = self.build_log
        self.build_button.configure(state='disabled')
        self.progress.start(12)
        mises_a_jour.remember(official=official, old=old, copy=str(folder), output=out, artworks=artworks or '')

        def work():
            error = None
            try:
                patcher.build(official, old, out, save=phone_save, copy=str(folder), new_game=new_game, artworks=artworks)
            except SystemExit as stop:
                error = str(stop)
            except Exception as failure:
                error = f'{type(failure).__name__} : {failure}'
            self.root.after(0, lambda: self.built(out, error))
        threading.Thread(target=work, daemon=True).start()

    def built(self, out, error):
        self.building = False
        self.progress.stop()
        self.build_button.configure(state='normal')
        if error:
            print(f'\nÉchec : {error}\n')
            messagebox.showerror(TITLE, f"L'APK n'a pas pu être fabriqué :\n\n{error}")
            return
        print("\nL'APK est prêt. Copie-le sur le téléphone Android et ouvre-le pour l'installer.\n")
        if messagebox.askyesno(TITLE, f"L'APK est prêt :\n{out}\n\nOuvrir son dossier ?"):
            open_folder(Path(out).parent)

    def updates_tab(self, notebook):
        tab = ttk.Frame(notebook, padding=12)
        self.version = mises_a_jour.current()['version']
        ttk.Label(tab, text="L'outil", font=('TkDefaultFont', 13, 'bold')).pack(anchor='w')
        self.release_text = paragraph(tab, f"Version de l'outil : {self.version}. Recherche d'une nouvelle version...")
        row = ttk.Frame(tab)
        row.pack(anchor='w', pady=6)
        ttk.Button(row, text='Vérifier maintenant', command=lambda: threading.Thread(target=self.check_release, args=(True,), daemon=True).start()).pack(side='left')
        self.tool_button = ttk.Button(row, text="Mettre à jour l'outil", command=self.update_tool, state='disabled')
        self.tool_button.pack(side='left', padx=8)
        ttk.Separator(tab).pack(fill='x', pady=10)
        ttk.Label(tab, text='Le jeu sur le téléphone Android', font=('TkDefaultFont', 13, 'bold')).pack(anchor='w')
        paragraph(tab, "Quand une nouvelle version de l'outil est installée, le jeu hors ligne de ton téléphone peut recevoir ses nouveautés : branche le téléphone (débogage USB activé), puis clique ci-dessous. L'outil refabrique l'APK avec les fichiers de l'onglet 2 et la sauvegarde actuelle du téléphone, puis l'installe par-dessus l'ancien : ta progression est gardée. Le jeu se ferme pendant l'installation. Le jeu hors ligne prévient aussi tout seul, dans sa boîte de réception (Inbox), quand une nouvelle version est sortie.")
        row = ttk.Frame(tab)
        row.pack(anchor='w', pady=6)
        self.phone_button = ttk.Button(row, text='Mettre à jour le jeu du téléphone', command=self.update_phone)
        self.phone_button.pack(side='left')
        self.update_progress = ttk.Progressbar(row, mode='indeterminate', length=240)
        self.update_progress.pack(side='left', padx=10)
        frame = ttk.Frame(tab)
        frame.pack(fill='both', expand=True, pady=(8, 0))
        self.update_log, scroll = self.log_box(frame)
        scroll.pack(side='right', fill='y')
        self.update_log.pack(fill='both', expand=True)
        self.release = None
        return tab

    def restore_settings(self):
        stored = mises_a_jour.settings()
        for key, variable in (('official', self.official), ('old', self.old_version), ('artworks', self.artworks), ('output', self.output_path)):
            value = stored.get(key)
            if value and (key == 'output' or os.path.exists(value)) and (not variable.get().strip()):
                variable.set(value)
        if stored.get('copy') and os.path.isdir(stored['copy']):
            self.refresh_copies(select=Path(stored['copy']))

    def check_release(self, asked=False):
        release = mises_a_jour.latest_release()
        self.root.after(0, lambda: self.release_found(release, asked))

    def release_found(self, release, asked):
        self.release = release
        if release is None:
            self.release_text.configure(text=f"Version de l'outil : {self.version}. Aucune version publiée n'a été trouvée (pas d'Internet, ou les mises à jour ne sont pas encore en ligne).")
            self.tool_button.configure(state='disabled')
        elif mises_a_jour.newer(release['version'], self.version):
            notes = f"\n\nNouveautés :\n{release['notes'][:600]}" if release['notes'] else ''
            self.release_text.configure(text=f"Version de l'outil : {self.version}. La version {release['version']} est sortie !{notes}")
            self.tool_button.configure(state='normal')
            self.root.title(f"{TITLE}  —  nouvelle version {release['version']} disponible (onglet 4)")
            if not asked:
                return
        else:
            self.release_text.configure(text=f"Version de l'outil : {self.version}. C'est la plus récente.")
            self.tool_button.configure(state='disabled')
        if asked and release is not None and (not mises_a_jour.newer(release['version'], self.version)):
            messagebox.showinfo(TITLE, "L'outil est déjà à jour.")

    def update_tool(self):
        release = self.release
        if not release or self.building:
            return
        if not messagebox.askyesno(TITLE, f"Installer la version {release['version']} de l'outil ?\n\nTes copies (dossier Sauvegardes) ne bougent pas. L'outil se fermera : relance-le ensuite."):
            return
        self.target = self.update_log
        self.tool_button.configure(state='disabled')
        self.update_progress.start(12)

        def work():
            error = None
            try:
                mises_a_jour.update_tool(release, str(ROOT))
            except Exception as failure:
                error = str(failure)
            self.root.after(0, lambda: self.tool_updated(error))
        threading.Thread(target=work, daemon=True).start()

    def tool_updated(self, error):
        self.update_progress.stop()
        if error:
            print(f'\nÉchec : {error}\n')
            messagebox.showerror(TITLE, f"La mise à jour de l'outil a échoué :\n\n{error}")
            self.tool_button.configure(state='normal')
            return
        messagebox.showinfo(TITLE, "L'outil est à jour. Il se ferme maintenant : relance-le (Lancer (Mac) ou Lancer (Windows)), puis mets à jour le jeu du téléphone dans l'onglet 4.")
        self.root.destroy()

    def update_phone(self):
        if self.building:
            messagebox.showinfo(TITLE, 'Attends la fin de la fabrication en cours.')
            return
        official, old = (self.official.get().strip(), self.old_version.get().strip())
        folder = self.copy_folders.get(self.copy_choice.get())
        if not (official and os.path.isfile(official) and old and os.path.isfile(old)) or folder is None or status(folder) != 'ready':
            messagebox.showinfo(TITLE, "Pour refabriquer le jeu, l'outil a besoin des fichiers de l'onglet 2 : le jeu officiel 1.10.4, le 1.10.3 et une copie complète. Remplis-les, puis reviens ici.")
            return
        found = self.editor.phone()
        if not found:
            return
        adb, serial = found
        signature = mises_a_jour.phone_signature(adb, serial)
        if signature == copie_android.OFFICIAL_SIGNATURE:
            messagebox.showinfo(TITLE, "Le téléphone a le jeu officiel, pas la version hors ligne : il n'y a rien à mettre à jour. Pour installer la version hors ligne, fabrique l'APK dans l'onglet 2.")
            return
        out = self.output_path.get().strip() or str(Path.home() / 'RangerRumble_hors_ligne.apk')
        artworks = self.artworks.get().strip() or None
        self.building = True
        self.target = self.update_log
        self.phone_button.configure(state='disabled')
        self.update_progress.start(12)

        def work():
            error, retry, save = (None, False, None)
            try:
                save = mises_a_jour.phone_save(adb, serial, str(self.copies_folder()))
                print('Sauvegarde du téléphone lue.' if save else "La version du jeu sur le téléphone ne donne pas sa sauvegarde par le câble : l'APK partira de celle de la copie (seulement s'il fallait le réinstaller).")
                patcher.build(official, old, out, save=save, copy=str(folder), artworks=artworks)
                print('Installation sur le téléphone (le jeu se ferme)...')
                copie_android.install(adb, serial, out)
            except copie_android.Problem as problem:
                error = str(problem)
                retry = "signé par quelqu'un d'autre" in error and save is not None
            except SystemExit as stop:
                error = str(stop)
            except Exception as failure:
                error = f'{type(failure).__name__} : {failure}'
            self.root.after(0, lambda: self.phone_updated(adb, serial, out, error, retry))
        threading.Thread(target=work, daemon=True).start()

    def phone_updated(self, adb, serial, out, error, retry):
        if retry and messagebox.askyesno(TITLE, "Le jeu du téléphone a été fabriqué sur un autre ordinateur (autre signature) : l'outil ne peut pas l'installer par-dessus.\n\nIl peut le désinstaller, puis installer la nouvelle version, qui repart de ta sauvegarde actuelle (elle vient d'être lue et est gardée dans le dossier Sauvegardes). Les réglages du jeu (son, graphismes, RR Options) reviennent à leurs valeurs de départ.\n\nDésinstaller et réinstaller ?"):

            def work():
                problem = None
                try:
                    print("Désinstallation de l'ancienne version, puis installation...")
                    mises_a_jour.reinstall(adb, serial, out)
                except Exception as failure:
                    problem = str(failure)
                self.root.after(0, lambda: self.phone_updated(adb, serial, out, problem, False))
            threading.Thread(target=work, daemon=True).start()
            return
        self.building = False
        self.update_progress.stop()
        self.phone_button.configure(state='normal')
        if error:
            print(f'\nÉchec : {error}\n')
            messagebox.showerror(TITLE, f"La mise à jour du téléphone n'a pas abouti :\n\n{error}")
            return
        print('\nLe jeu du téléphone est à jour.\n')
        messagebox.showinfo(TITLE, 'Le jeu du téléphone est à jour. Ta progression est gardée.')

    def close(self):
        if self.editor.save is not None and self.editor.save.changed() and (not messagebox.askyesno(TITLE, "La sauvegarde ouverte dans l'onglet 3 a des changements pas encore enregistrés. Quitter quand même ?")):
            return
        if self.building and (not messagebox.askyesno(TITLE, "L'APK est en cours de fabrication. Quitter quand même ?")):
            return
        if self.copy_state:
            loop, master = self.copy_state
            loop.call_soon_threadsafe(master.shutdown)
        self.root.destroy()

def main():
    root = tk.Tk()
    Application(root)
    root.mainloop()
if __name__ == '__main__':
    main()
