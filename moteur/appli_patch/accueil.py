import math
import os
import sys
import time
import tkinter as tk
from tkinter import font as tkfont
import langues
import theme
from langues import tr
from theme import BACK, CARD, CARD_PICTURE, CHIP, GLOW, GREEN, NAV, NAVY, PILL
HERE = os.path.dirname(os.path.abspath(__file__))
PICTURES = os.path.join(HERE, 'ressources', 'lanceur')
BACKGROUNDS = 6
CARD_TEXT_X = 78
PILL_TEXT_X = 66
WHITE = '#ffffff'
SOFT = '#aab7d4'
GOLD = '#ffcd46'
FRAME = 50
SLIDE = 11.0
XFADE = 1.4
XFADE_FRAMES = 24
PREPARE = 2.6
HINT_SECONDS = 3.5

def mixed(first, second, amount):
    low = bytes((int(value * (1 - amount)) for value in range(256)))
    high = bytes((int(value * amount) for value in range(256)))
    total = int.from_bytes(first.translate(low), 'big') + int.from_bytes(second.translate(high), 'big')
    return total.to_bytes(len(first), 'big')

class Element:

    def __init__(self, home, size=(0, 0), action=None):
        self.home = home
        self.tag = f'e{id(self)}'
        self.size = size
        self.action = action
        self.x = self.y = 0
        self.shift = self.goal = 0.0
        self.applied = 0
        self.start = 0.0
        self.hover = False

    def place(self, x, y):
        x, y = (round(x), round(y))
        self.home.canvas.move(self.tag, x - self.x, y - self.y)
        self.x, self.y = (x, y)

    def enter(self, delay, distance):
        self.home.canvas.move(self.tag, 0, round(distance) - self.applied)
        self.shift, self.applied, self.goal = (float(distance), round(distance), 0.0)
        self.start = time.monotonic() + delay

    def step(self, now):
        if now < self.start or self.shift == self.goal:
            return
        self.shift += (self.goal - self.shift) * 0.2
        if abs(self.goal - self.shift) < 0.4:
            self.shift = self.goal
        whole = round(self.shift)
        if whole != self.applied:
            self.home.canvas.move(self.tag, 0, whole - self.applied)
            self.applied = whole

    def contains(self, x, y):
        top = self.y + self.applied
        return self.x <= x < self.x + self.size[0] and top <= y < top + self.size[1]

    def set_hover(self, on):
        self.hover = on
        self.goal = -5.0 if on else 0.0
        self.start = 0.0
        self.home.refresh()

class TextLink(Element):
    MARGIN = 4

    def __init__(self, home, action):
        super().__init__(home, action=action)
        self.text = None

    def contains(self, x, y):
        box = self.home.canvas.bbox(self.text)
        return bool(box) and box[0] - self.MARGIN <= x <= box[2] + self.MARGIN and (box[1] - self.MARGIN <= y <= box[3] + self.MARGIN)

    def set_hover(self, on):
        self.home.canvas.itemconfigure(self.text, fill=GREEN if on else WHITE)

class Home:

    def __init__(self, root, app):
        self.root = root
        self.app = app
        self.canvas = tk.Canvas(root, highlightthickness=0, background=NAVY, borderwidth=0)
        self.fonts = theme.fonts(root)
        self.images = {}
        self.width, self.height = (980, 700)
        self.running = False
        self.slide = 0
        self.slide_started = time.monotonic()
        self.ticking = None
        self.hint_until = 0.0
        self.hovered = None
        self.layout_pending = None
        self.started = time.monotonic()
        self.entered = False
        self.back_place = None
        self.frames = []
        self.parts = None
        self.following = None
        self.fading_since = None
        self.frame_shown = -1
        self.paused_at = 0.0
        mode = os.environ.get('RR_ACCUEIL') or ('calme' if sys.platform == 'darwin' else '')
        self.calm = mode == 'calme'
        self.cost_checked = mode in ('calme', 'anime')
        self.cost_mark = None
        self.current = self.picture('fond_1')
        self.background = self.canvas.create_image(0, 0, anchor='nw', image=self.current)
        self.back_size = (self.current.width(), self.current.height())
        self._make_title()
        self._make_chips()
        self._make_cards()
        self._make_pills()
        self._make_foot()
        self.targets = self.chips + self.cards + self.pills + [self.language]
        self.moving = [self.logo, self.tagline, self.chips_row, self.hint, self.foot] + self.targets
        self.canvas.bind('<Configure>', self.resized)
        self.canvas.bind('<Map>', lambda _event: self.root.after(60, self.redraw))
        self.canvas.bind('<Motion>', self.moved)
        self.canvas.bind('<Leave>', lambda _event: self.moved(None))
        self.canvas.bind('<Button-1>', self.clicked)
        self.refresh()

    def _make_title(self):
        self.logo = Element(self)
        self.logo_item = self.canvas.create_image(0, 0, anchor='n', image=self.picture('logo'), tags=self.logo.tag)
        self.tagline = Element(self)
        spaced = '   '.join((' '.join(word) for word in tr('Hors ligne').upper().split()))
        self.shadowed_text(self.tagline, spaced, self.fonts['tagline'], GREEN, 'center')

    def _make_chips(self):
        canvas = self.canvas
        self.chips_row = Element(self)
        self.shadowed_text(self.chips_row, tr('Mon jeu Ranger Rumble est sur :'), self.fonts['text'], SOFT, 'center')
        self.chips = []
        for value, label in self.app.platforms:
            chip = Element(self, CHIP, lambda value=value: self.choose(value))
            chip.value = value
            chip.image = canvas.create_image(-GLOW, -GLOW, anchor='nw', image=self.picture('puce_off'), tags=chip.tag)
            chip.text = canvas.create_text(CHIP[0] // 2, CHIP[1] // 2, text=label, font=self.fonts['chip'], fill=WHITE, tags=chip.tag)
            self.chips.append(chip)
        self.hint = Element(self)
        self.shadowed_text(self.hint, tr("Choisir d'abord où est le jeu."), self.fonts['text'], GOLD, 'center')
        canvas.itemconfigure(self.hint.tag, state='hidden')

    def _make_cards(self):
        canvas = self.canvas
        self.cards = []
        for number, name, title in ((1, 'copier', tr('Copier ma sauvegarde')), (2, 'installer', tr('Installer le jeu'))):
            card = Element(self, CARD, lambda number=number: self.open_step(number))
            card.name = name
            card.image = canvas.create_image(-GLOW, -GLOW, anchor='nw', image=self.picture(f'carte_{name}'), tags=card.tag)
            canvas.create_text(CARD_TEXT_X, CARD_PICTURE + 10, text=title, anchor='nw', font=self.fonts['title'], fill=WHITE, tags=card.tag)
            card.text = canvas.create_text(CARD_TEXT_X, CARD_PICTURE + 42, text='', anchor='nw', font=self.fonts['text'], fill=SOFT, width=CARD[0] - 94, tags=card.tag)
            self.cards.append(card)

    def _make_pills(self):
        canvas = self.canvas
        self.pills = []
        for page, name, title in ((2, 'editer', tr('Éditer une sauvegarde')), (3, 'maj', tr('Mises à jour'))):
            pill = Element(self, PILL, lambda page=page: self.app.show_page(page))
            pill.name = name
            pill.title = title
            pill.image = canvas.create_image(-GLOW, -GLOW, anchor='nw', image=self.picture(f'bouton_{name}'), tags=pill.tag)
            pill.text = canvas.create_text(PILL_TEXT_X, PILL[1] // 2, text=title, anchor='w', font=self.fonts['button'], fill=WHITE, tags=pill.tag)
            self.pills.append(pill)
        updates = self.pills[1]
        updates.note = canvas.create_text(PILL_TEXT_X, PILL[1] // 2 + 11, text='', anchor='w', font=self.fonts['small'], fill=GREEN, tags=updates.tag, state='hidden')
        updates.dot = canvas.create_image(PILL[0] - 26, PILL[1] // 2, image=self.picture('point'), tags=updates.tag, state='hidden')

    def _make_foot(self):
        self.foot = Element(self)
        self.shadowed_text(self.foot, tr('Outil {version}  ·  Jeu {game}', version=self.app.version, game=self.app.game), self.fonts['small'], SOFT, 'w')
        names = dict(langues.LANGUAGES)
        self.language = TextLink(self, self.language_menu)
        self.language.text = self.shadowed_text(self.language, f"{tr('Langue :')} {names[langues.CURRENT]}  ▾", self.fonts['small'], WHITE, 'e')
        self.menu = tk.Menu(self.canvas, tearoff=0)
        for _, name in langues.LANGUAGES:
            self.menu.add_radiobutton(label=name, value=name, variable=self.app.language, command=self.app.language_changed)

    def picture(self, name):
        if name not in self.images:
            self.images[name] = tk.PhotoImage(file=os.path.join(PICTURES, name + '.png'))
        return self.images[name]

    def shadowed_text(self, element, text, font, color, anchor):
        self.canvas.create_text(1, 2, text=text, font=font, fill='#000000', anchor=anchor, tags=element.tag)
        return self.canvas.create_text(0, 0, text=text, font=font, fill=color, anchor=anchor, tags=element.tag)

    def resized(self, event):
        self.width, self.height = (event.width, event.height)
        if self.layout_pending is None:
            self.layout_pending = self.root.after(40, self.layout)

    def layout(self):
        self.layout_pending = None
        width, height = (self.width, self.height)
        middle = width / 2
        compact = height < 690
        self.canvas.itemconfigure(self.logo_item, image=self.picture('logo_moyen' if compact else 'logo'))
        if compact:
            top = max(0, (height - 590) / 2)
            spots = {'logo': 2, 'tagline': 150, 'label': 178, 'chips': 192, 'hint': 248, 'cards': 256, 'pills': 500, 'foot': 578}
        else:
            top = max(0, (height - 700) / 2)
            spots = {'logo': 6, 'tagline': 206, 'label': 238, 'chips': 254, 'hint': 318, 'cards': 336, 'pills': 588, 'foot': 676}
        self.drop_crossfade()
        self.back_place = None
        self.logo.place(middle, top + spots['logo'])
        self.tagline.place(middle, top + spots['tagline'])
        self.chips_row.place(middle, top + spots['label'])
        self._place_pair(self.chips, CHIP[0], 16, middle, top + spots['chips'])
        self.hint.place(middle, top + spots['hint'])
        self._place_pair(self.cards, CARD[0], 28, middle, top + spots['cards'])
        self._place_pair(self.pills, PILL[0], 28, middle, top + spots['pills'])
        foot = max(top + spots['foot'], height - (14 if compact else 24))
        self.foot.place(22, foot)
        self.language.place(width - 22, foot)
        self.pan(self.slide, self.progress(time.monotonic()))

    @staticmethod
    def _place_pair(elements, width, gap, middle, y):
        for index, element in enumerate(elements):
            element.place(middle - width - gap / 2 + index * (width + gap), y)

    def start(self):
        if self.running:
            return
        self.running = True
        now = time.monotonic()
        if self.paused_at:
            self.slide_started += now - self.paused_at
            if self.fading_since is not None:
                self.fading_since += now - self.paused_at
            self.paused_at = 0.0
        if not self.entered:
            self.entered = True
            self.logo.enter(0.1, -36)
            self.tagline.enter(0.25, -24)
            self.chips_row.enter(0.35, 30)
            for index, element in enumerate(self.chips + self.cards + self.pills):
                element.enter(0.4 + 0.07 * index, 60)
            self.slide_started = now
        self.redraw()
        self.tick()

    def redraw(self):
        self.back_place = None
        if self.running and self.back_size:
            self.canvas.coords(self.background, *self.canvas.coords(self.background))

    def stop(self):
        if self.running:
            self.paused_at = time.monotonic()
        self.running = False
        if self.ticking:
            self.root.after_cancel(self.ticking)
            self.ticking = None
        self.cost_mark = None

    def pause(self, paused):
        if paused:
            self.stop()
        elif self.canvas.winfo_ismapped():
            self.start()

    def tick(self):
        self.ticking = None
        if not self.running:
            return
        now = time.monotonic()
        self.slideshow(now)
        for element in self.moving:
            element.step(now)
        self.check_cost(now)
        if self.hint_until and now > self.hint_until:
            self.hide_hint()
        self.ticking = self.root.after(15 if self.fading_since is not None else FRAME, self.tick)

    def check_cost(self, now):
        if self.calm or self.cost_checked:
            return
        if self.cost_mark is None:
            if now - self.started >= 1.5:
                self.cost_mark = (time.process_time(), now)
            return
        cpu, wall = self.cost_mark
        if now - wall >= 2.0:
            self.cost_checked = True
            if (time.process_time() - cpu) / (now - wall) > 0.3:
                self.calm = True

    def progress(self, now):
        return 0.5 if self.calm else min(1.0, (now - self.slide_started) / SLIDE)

    def slideshow(self, now):
        if self.fading_since is not None:
            self.show_crossfade(now)
            return
        spent = now - self.slide_started
        self.pan(self.slide, self.progress(now))
        if spent >= SLIDE - PREPARE:
            ready = self.prepare_crossfade()
            if ready and spent >= SLIDE:
                self.fading_since = now
                self.show_crossfade(now)
            elif spent >= SLIDE + 1.5:
                self.finish_slide()

    def place_for(self, slide, progress):
        slack_x = max(0, self.back_size[0] - self.width)
        slack_y = max(0, self.back_size[1] - self.height)
        eased = 0.5 - 0.5 * math.cos(math.pi * progress)
        direction = 1 if slide % 2 == 0 else -1
        start_x = slack_x * (0.15 if direction > 0 else 0.85)
        x = start_x + direction * slack_x * 0.7 * eased
        y = slack_y * (0.3 + 0.4 * (eased if slide % 3 else 1 - eased))
        if self.back_size[0] < self.width:
            x = -(self.width - self.back_size[0]) / 2
        if self.back_size[1] < self.height:
            y = -(self.height - self.back_size[1]) / 2
        return (-round(x), -round(y))

    def pan(self, slide, progress):
        place = self.place_for(slide, progress)
        if place != self.back_place:
            self.back_place = place
            self.canvas.coords(self.background, *place)

    def visible_part(self, photo, place):
        data = self.root.tk.call(photo.name, 'data', '-format', 'ppm')
        start = data.index(b'\n', data.index(b'\n', 3) + 1) + 1
        width, height = (photo.width(), photo.height())
        if len(data) - start != width * height * 3:
            raise ValueError('ppm')
        left, top = (max(0, -place[0]), max(0, -place[1]))
        shown_width = min(width - left, self.width - max(0, place[0]))
        shown_height = min(height - top, self.height - max(0, place[1]))
        stride = width * 3
        rows = b''.join((data[start + (top + row) * stride + left * 3:start + (top + row) * stride + (left + shown_width) * 3] for row in range(shown_height)))
        return (rows, shown_width, shown_height, (max(0, place[0]), max(0, place[1])))

    def prepare_crossfade(self):
        if self.parts is False:
            return False
        if len(self.frames) == XFADE_FRAMES:
            return True
        if self.parts is None:
            self.parts = self._crossfade_parts()
            return False
        old, new, width, height, _ = self.parts
        step = (len(self.frames) + 1) / XFADE_FRAMES
        amount = step * step * (3 - 2 * step)
        self.frames.append(tk.PhotoImage(data=b'P6\n%d %d\n255\n' % (width, height) + mixed(old, new, amount), format='ppm'))
        return len(self.frames) == XFADE_FRAMES

    def _crossfade_parts(self):
        following = (self.slide + 1) % BACKGROUNDS
        try:
            self.following = self.picture(f'fond_{following + 1}')
            old = self.visible_part(self.current, self.place_for(self.slide, 0.5 if self.calm else 1.0))
            new = self.visible_part(self.following, self.place_for(following, 0.5 if self.calm else 0.0))
        except (tk.TclError, ValueError):
            return False
        if old[1:] != new[1:]:
            return False
        return (old[0], new[0]) + old[1:]

    def show_crossfade(self, now):
        index = int((now - self.fading_since) / XFADE * XFADE_FRAMES)
        if index >= XFADE_FRAMES:
            self.finish_slide()
            return
        if index != self.frame_shown:
            self.frame_shown = index
            self.canvas.itemconfigure(self.background, image=self.frames[index])
            self.canvas.coords(self.background, *self.parts[4])
            self.back_place = None

    def finish_slide(self):
        old = f'fond_{self.slide + 1}'
        self.slide = (self.slide + 1) % BACKGROUNDS
        self.current = self.following or self.picture(f'fond_{self.slide + 1}')
        if old != f'fond_{self.slide + 1}':
            self.images.pop(old, None)
        self.back_size = (self.current.width(), self.current.height())
        self.canvas.itemconfigure(self.background, image=self.current)
        self.slide_started = time.monotonic()
        self.back_place = None
        self.pan(self.slide, self.progress(self.slide_started))
        self.frames, self.parts, self.following = ([], None, None)
        self.fading_since, self.frame_shown = (None, -1)

    def drop_crossfade(self):
        if self.fading_since is not None:
            self.finish_slide()
        self.frames, self.parts = ([], None)

    def target_at(self, x, y):
        return next((element for element in self.targets if element.contains(x, y) and self.enabled(element)), None)

    def enabled(self, element):
        return not (element is self.cards[0] and self.app.platform.get() == 'android')

    def moved(self, event):
        target = self.target_at(event.x, event.y) if event is not None else None
        if target is self.hovered:
            return
        if self.hovered is not None:
            self.hovered.set_hover(False)
        self.hovered = target
        if target is not None:
            target.set_hover(True)
        self.canvas.configure(cursor='hand2' if target is not None else '')

    def clicked(self, event):
        target = self.target_at(event.x, event.y)
        if target is not None and target.action:
            target.action()

    def hide_hint(self):
        self.hint_until = 0.0
        self.canvas.itemconfigure(self.hint.tag, state='hidden')

    def choose(self, value):
        self.hide_hint()
        self.app.platform.set(value)
        self.app.platform_changed()

    def open_step(self, number):
        if not self.app.platform.get():
            self.hint_until = time.monotonic() + HINT_SECONDS
            self.canvas.itemconfigure(self.hint.tag, state='normal')
            for chip in self.chips:
                chip.enter(0, -10)
            return
        self.app.show_page(number - 1)

    def language_menu(self):
        box = self.canvas.bbox(self.language.text)
        x = self.canvas.winfo_rootx() + (box[0] if box else self.width - 120)
        y = self.canvas.winfo_rooty() + (box[1] if box else self.height - 30)
        self.menu.update_idletasks()
        height = self.menu.winfo_reqheight()
        if height < 40:
            height = 24 * len(langues.LANGUAGES)
        try:
            self.menu.tk_popup(x, y - height - 4)
        finally:
            self.menu.grab_release()

    def set_release(self, version):
        pill = self.pills[1]
        middle = pill.y + pill.applied + PILL[1] // 2
        self.canvas.itemconfigure(pill.text, text=pill.title)
        self.canvas.coords(pill.text, pill.x + PILL_TEXT_X, middle - 9)
        self.canvas.itemconfigure(pill.note, text=tr('Version {version} disponible', version=version), state='normal')
        self.canvas.coords(pill.note, pill.x + PILL_TEXT_X, middle + 11)
        self.canvas.itemconfigure(pill.dot, state='normal')

    def refresh(self):
        platform = self.app.platform.get()
        for chip in self.chips:
            chosen = chip.value == platform
            state = 'puce_on' if chosen else 'puce_survol' if chip.hover else 'puce_off'
            self.canvas.itemconfigure(chip.image, image=self.picture(state))
            self.canvas.itemconfigure(chip.text, fill=NAVY if chosen else WHITE)
        copy, install = self.cards
        if platform == 'android':
            copy_picture, copy_text = ('carte_copier_gris', tr("Rien à copier sur Android : passe à l'étape 2."))
        else:
            copy_picture = self._hovered_picture(copy, 'carte')
            copy_text = tr("Depuis l'iPhone, par le Wi-Fi.") if platform == 'ios' else tr("Depuis l'iPhone ou l'iPad.")
        self.canvas.itemconfigure(copy.image, image=self.picture(copy_picture))
        self.canvas.itemconfigure(copy.text, text=copy_text)
        self.canvas.itemconfigure(install.image, image=self.picture(self._hovered_picture(install, 'carte')))
        self.canvas.itemconfigure(install.text, text=tr("Fabriquer l'APK et l'installer sur Android."))
        for pill in self.pills:
            self.canvas.itemconfigure(pill.image, image=self.picture(self._hovered_picture(pill, 'bouton')))

    @staticmethod
    def _hovered_picture(element, kind):
        return f"{kind}_{element.name}{('_survol' if element.hover else '')}"

class NavTab:

    def __init__(self, image, label):
        self.image, self.label, self.x = (image, label, 0)

class Header:
    HEIGHT = 78
    GAP = 8
    MARGIN = 16

    def __init__(self, root, app, home):
        self.app = app
        self.home = home
        self.canvas = tk.Canvas(root, height=self.HEIGHT, highlightthickness=0, background=NAVY, borderwidth=0)
        canvas = self.canvas
        self.middle = self.HEIGHT // 2
        canvas.create_image(0, 0, anchor='nw', image=home.picture('bandeau'))
        self.back = canvas.create_image(self.MARGIN - GLOW, self.middle - BACK[1] // 2 - GLOW, anchor='nw', image=home.picture('retour'))
        canvas.create_text(self.MARGIN + BACK[0] // 2, self.middle, text='←  ' + tr('Accueil'), font=home.fonts['button'], fill=WHITE)
        self.logo = canvas.create_image(0, self.middle, anchor='e', image=home.picture('logo_petit'))
        self.pages = []
        for number, label in enumerate((tr('Copier'), tr('Installer'), tr('Éditer'), tr('Mises à jour'))):
            text = f'{number + 1}   {label}'
            font = home.fonts['button']
            if tkfont.Font(font=font).measure(text) > NAV[0] - 24:
                font = home.fonts['small'] + ('bold',)
            self.pages.append(NavTab(canvas.create_image(0, 0, anchor='nw', image=home.picture('onglet')), canvas.create_text(0, 0, text=text, font=font, fill=WHITE)))
        self.current = 0
        self.over = None
        canvas.bind('<Configure>', lambda event: self.layout(event.width))
        canvas.bind('<Motion>', lambda event: self.hover(self.target(event.x, event.y)))
        canvas.bind('<Leave>', lambda _event: self.hover(None))
        canvas.bind('<Button-1>', self.clicked)

    def layout(self, width):
        row = len(self.pages) * NAV[0] + (len(self.pages) - 1) * self.GAP
        start = max(round((width - row) / 2), self.MARGIN + BACK[0] + self.MARGIN)
        for index, page in enumerate(self.pages):
            page.x = start + index * (NAV[0] + self.GAP)
            self.canvas.coords(page.image, page.x - GLOW, self.middle - NAV[1] // 2 - GLOW)
            self.canvas.coords(page.label, page.x + NAV[0] // 2, self.middle)
        self.canvas.coords(self.logo, width - 18, self.middle)
        room = width - 18 - self.home.picture('logo_petit').width() - 16 >= start + row
        self.canvas.itemconfigure(self.logo, state='normal' if room else 'hidden')
        self.paint()

    def target(self, x, y):
        if abs(y - self.middle) > NAV[1] // 2:
            return None
        if self.MARGIN <= x <= self.MARGIN + BACK[0]:
            return 'home'
        return next((index for index, page in enumerate(self.pages) if page.x <= x <= page.x + NAV[0]), None)

    def hover(self, target):
        if target != self.over:
            self.over = target
            self.paint()
            self.canvas.configure(cursor='hand2' if target is not None and target != self.current else '')

    def clicked(self, event):
        target = self.target(event.x, event.y)
        if target == 'home':
            self.app.show_home()
        elif target is not None and target != self.current:
            self.app.show_page(target)

    def select(self, index):
        self.current = index
        self.paint()

    def paint(self):
        picture = self.home.picture
        self.canvas.itemconfigure(self.back, image=picture('retour_survol' if self.over == 'home' else 'retour'))
        for index, page in enumerate(self.pages):
            chosen = index == self.current
            state = 'onglet_on' if chosen else 'onglet_survol' if self.over == index else 'onglet'
            self.canvas.itemconfigure(page.image, image=picture(state))
            self.canvas.itemconfigure(page.label, fill=NAVY if chosen else WHITE)
