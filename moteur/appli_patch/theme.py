import os
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk
PIECES = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ressources', 'lanceur')
_kept = []
NAVY = '#0a1022'
PAGE = '#0e1630'
PANEL = '#152043'
RAISED = '#1d2a55'
HOVER = '#283a72'
PRESSED = '#16214a'
FIELD = '#0a1126'
LINE = '#2a3a6e'
TEXT = '#eef2fb'
SOFT = '#9fb0d4'
DIM = '#5d6b90'
GREEN = '#50ec80'
GREEN_HOVER = '#7af5a0'
GREEN_DIM = '#21402f'
SELECT = '#2f5aa8'
RED = '#ff7a7a'
OWNED = '#163a2a'
GLOW = 14
CARD = (360, 232)
CARD_PICTURE = 150
PILL = (360, 58)
CHIP = (190, 44)
BACK = (132, 38)
NAV = (156, 36)

def _first_family(root, names, default):
    families = set(tkfont.families(root))
    return next((name for name in names if name in families), default)

def family(root):
    return _first_family(root, ('Avenir Next', 'Segoe UI', 'Helvetica Neue', 'Helvetica', 'Arial'), 'TkDefaultFont')

def mono_family(root):
    return _first_family(root, ('Menlo', 'Consolas', 'Courier New'), 'TkFixedFont')

def fonts(root):
    main = family(root)
    return {'text': (main, -13), 'small': (main, -12), 'bold': (main, -13, 'bold'), 'button': (main, -13, 'bold'), 'heading': (main, -16, 'bold'), 'title': (main, -17, 'bold'), 'big': (main, -22, 'bold'), 'chip': (main, -13, 'bold'), 'tagline': (main, -13, 'bold'), 'mono': (mono_family(root), -12)}

def apply(root):
    found = fonts(root)
    _named_fonts(found)
    root.configure(background=PAGE)
    _plain_widgets(root, found)
    style = ttk.Style(root)
    style.theme_use('clam')
    _ttk_styles(style, found)
    rounded(root, style)

def _named_fonts(found):
    for name, spec in (('TkDefaultFont', found['text']), ('TkTextFont', found['text']), ('TkHeadingFont', found['bold']), ('TkFixedFont', found['mono']), ('TkCaptionFont', found['heading'])):
        named = tkfont.nametofont(name)
        named.configure(family=spec[0], size=spec[1], weight=spec[2] if len(spec) > 2 else 'normal')

def _plain_widgets(root, found):
    for option, value in (('*Background', PAGE), ('*Foreground', TEXT), ('*Entry.Background', FIELD), ('*insertBackground', TEXT), ('*selectBackground', SELECT), ('*selectForeground', TEXT), ('*highlightBackground', PAGE), ('*highlightColor', LINE), ('*activeBackground', HOVER), ('*activeForeground', TEXT), ('*disabledForeground', DIM), ('*TCombobox*Listbox.background', FIELD), ('*TCombobox*Listbox.foreground', TEXT), ('*TCombobox*Listbox.selectBackground', SELECT), ('*TCombobox*Listbox.font', found['text'])):
        root.option_add(option, value)

def _ttk_styles(style, found):
    style.configure('.', background=PAGE, foreground=TEXT, fieldbackground=FIELD, bordercolor=LINE, lightcolor=PAGE, darkcolor=PAGE, troughcolor=FIELD, focuscolor=PAGE, selectbackground=SELECT, selectforeground=TEXT, insertcolor=TEXT, arrowcolor=SOFT, font=found['text'])
    style.map('.', foreground=[('disabled', DIM)])
    style.configure('TFrame', background=PAGE)
    style.configure('TLabel', background=PAGE, foreground=TEXT)
    style.configure('Soft.TLabel', foreground=SOFT)
    style.configure('Small.TLabel', foreground=SOFT, font=found['small'])
    style.configure('Heading.TLabel', font=found['heading'])
    style.configure('Big.TLabel', font=found['big'])
    style.configure('TSeparator', background=LINE)
    style.configure('TButton', background=PAGE, foreground=TEXT, padding=(12, 7), font=found['button'], focusthickness=0)
    style.map('TButton', foreground=[('disabled', DIM)])
    style.configure('Primary.TButton', foreground=NAVY)
    style.map('Primary.TButton', foreground=[('disabled', '#5f8a70')])
    field = {'fieldbackground': FIELD, 'foreground': TEXT, 'bordercolor': LINE, 'lightcolor': FIELD, 'darkcolor': FIELD, 'insertcolor': TEXT, 'padding': 6}
    style.configure('TEntry', **field)
    style.configure('TCombobox', **dict(field, background=FIELD, bordercolor=FIELD, arrowcolor=SOFT, arrowsize=12, padding=(8, 6)))
    style.map('TCombobox', fieldbackground=[('readonly', FIELD), ('disabled', '#0d1430')], foreground=[('readonly', TEXT), ('disabled', DIM)], background=[('active', FIELD)], arrowcolor=[('active', GREEN)], selectbackground=[('readonly', FIELD)], selectforeground=[('readonly', TEXT)])
    marks = {'background': PAGE, 'foreground': TEXT, 'indicatorbackground': FIELD, 'indicatorforeground': GREEN, 'upperbordercolor': LINE, 'lowerbordercolor': LINE, 'indicatormargin': (0, 0, 8, 0), 'padding': 2}
    for kind in ('TCheckbutton', 'TRadiobutton'):
        style.configure(kind, **marks)
        style.map(kind, background=[('active', PAGE)], indicatorbackground=[('pressed', HOVER), ('active', RAISED)], upperbordercolor=[('selected', GREEN), ('active', GREEN)], lowerbordercolor=[('selected', GREEN), ('active', GREEN)])
    style.configure('Horizontal.TProgressbar', background=GREEN, troughcolor=FIELD, bordercolor=GREEN, lightcolor=GREEN, darkcolor=GREEN, thickness=10)
    for kind in ('Vertical.TScrollbar', 'Horizontal.TScrollbar'):
        style.configure(kind, background=RAISED, troughcolor=FIELD, bordercolor=FIELD, lightcolor=RAISED, darkcolor=RAISED, arrowcolor=SOFT, gripcount=0, arrowsize=12)
        style.map(kind, background=[('active', HOVER)], lightcolor=[('active', HOVER)], darkcolor=[('active', HOVER)])
    style.configure('Treeview', background=FIELD, fieldbackground=FIELD, foreground=TEXT, bordercolor=FIELD, lightcolor=FIELD, darkcolor=FIELD)
    style.map('Treeview', background=[('selected', SELECT)], foreground=[('selected', TEXT)])
    style.configure('Treeview.Heading', background=PANEL, foreground=SOFT, bordercolor=LINE, lightcolor=PANEL, darkcolor=PANEL, relief='flat', font=found['bold'], padding=(8, 6))
    style.map('Treeview.Heading', background=[('active', HOVER)])
    style.configure('TNotebook', background=PAGE, bordercolor=PAGE, lightcolor=PAGE, darkcolor=PAGE, tabmargins=(0, 4, 0, 0), padding=(0, 8, 0, 0))
    style.configure('TNotebook.Tab', background=PAGE, foreground=SOFT, bordercolor=LINE, lightcolor=PAGE, darkcolor=PAGE, padding=(10, 6), font=(found['small'][0], found['small'][1], 'bold'))
    style.map('TNotebook.Tab', background=[('selected', PANEL), ('active', RAISED)], lightcolor=[('selected', GREEN)], foreground=[('selected', TEXT), ('active', TEXT)])
    style.layout('Pages.TNotebook.Tab', [])
    style.configure('Pages.TNotebook', background=PAGE, borderwidth=0, bordercolor=PAGE, lightcolor=PAGE, darkcolor=PAGE, tabmargins=0, padding=0)

def rounded(root, style):

    def picture(name):
        image = tk.PhotoImage(master=root, file=os.path.join(PIECES, f'w_{name}.png'))
        _kept.append(image)
        return image

    def element(name, base, states, border, **options):
        style.element_create(name, 'image', picture(base), *[(state, picture(other)) for state, other in states], border=border, sticky='nsew', **options)
    element('RR.button', 'bouton', [('disabled', 'bouton_inactif'), ('pressed', 'bouton_appuye'), ('active', 'bouton_actif')], 10)
    element('RR.green', 'vert', [('disabled', 'vert_inactif'), ('pressed', 'vert_appuye'), ('active', 'vert_actif')], 10)
    element('RR.field', 'champ', [('disabled', 'champ_inactif'), ('focus', 'champ_focus')], 10)
    element('RR.card', 'cadre', [], 13)
    element('RR.trough', 'barre', [], 9, padding=4)
    element('RR.pbar', 'barre_pleine', [], 7)
    style.configure('Horizontal.TProgressbar', background=PAGE, troughcolor=PAGE)
    label = [('Button.padding', {'sticky': 'nsew', 'children': [('Button.label', {'sticky': 'nsew'})]})]
    style.layout('TButton', [('RR.button', {'sticky': 'nsew', 'children': label})])
    style.layout('Primary.TButton', [('RR.green', {'sticky': 'nsew', 'children': label})])
    style.layout('TEntry', [('RR.field', {'sticky': 'nsew', 'children': [('Entry.padding', {'sticky': 'nsew', 'children': [('Entry.textarea', {'sticky': 'nsew'})]})]})])
    style.layout('TCombobox', [('RR.field', {'sticky': 'nsew', 'children': [('Combobox.downarrow', {'side': 'right', 'sticky': 'ns'}), ('Combobox.padding', {'sticky': 'nsew', 'children': [('Combobox.textarea', {'sticky': 'nsew'})]})]})])
    style.layout('Card.TFrame', [('RR.card', {'sticky': 'nsew'})])
    style.layout('Horizontal.TProgressbar', [('RR.trough', {'sticky': 'nsew', 'children': [('RR.pbar', {'side': 'left', 'sticky': 'ns'})]})])

def log_colours(box):
    box.configure(background=FIELD, foreground='#cfd8ee', insertbackground=TEXT, selectbackground=SELECT, relief='flat', borderwidth=0, highlightthickness=0, padx=8, pady=6, font='TkFixedFont')
