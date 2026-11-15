import struct
ZURKON_EVENT = 1
RANDOM_WEAPON_EVENT = 2
EVENTS_META = (2250300884880255326, 1782976, 1940)
LOCAL_DATA_OBJECTS = (555856, 13096)
ATLAS = 3
NONE = (0, 0)
ICO_EVENT_ZURKON = (ATLAS, -6637609791931294474)
ICO_ZURKON = (ATLAS, 6377909532205259558)
ICO_EVENT_RANDOM_WEAPON = (ATLAS, 8197178227638723673)
ICO_RANDOM_WEAPON = (ATLAS, -6591038775427732196)
HUD_EVENT01_BG = (0, -2060039781620032191)
HUD_EVENT01_VALIDATE_BG = (0, 2409956357016157554)
HUD_EVENT00_BG = (0, 644244601077067271)
CARD_BACKGROUND_EVENT03 = (0, -8656910176408572051)
CARD_ROOT_IMAGE = 2324320
CARD_ILLUSTRATION_IMAGE = 1736144
CARD_ILLUSTRATION_RECT = 2788704
BG_EVENT01 = (2, 788590339457935646)
PICTURE = False
ZURKON_KEY = 4331717916415248115
TEXTURE_TEMPLATE = 3630189853526896061
SPRITE_TEMPLATE = -7206711618453787203
ZURKON_TEXTURE = TEXTURE_TEMPLATE ^ ZURKON_KEY
ZURKON_SPRITE = SPRITE_TEMPLATE ^ ZURKON_KEY
MOPZ_ILLUSTRATION = -6833857084070029598
MOPZ_ILLUSTRATION_OBJECTS = [-6833857084070029598, 3406277644904109794, -4109599926355945758, -5664358716021664030, -3411647593059445022, 6022980171252963042, 3938610661646604002, 2262031918369085154, 7724443635253384930, 5359327874125469410, -5381130000964577566]
MOPZ_FIGURE = (-3411647593059445022, 6022980171252963042, 2262031918369085154)
ZURKON_ILLUSTRATION = MOPZ_ILLUSTRATION ^ ZURKON_KEY
ZURKON_FIGURE_SIZE = (250.0, 292.0)
ZURKON_FIGURE_OFFSET = (45.0, -20.0)
CARD = False
CARD_KEY = 7654872262872278513
CARD_TEXTURE = TEXTURE_TEMPLATE ^ CARD_KEY
CARD_SPRITE = SPRITE_TEMPLATE ^ CARD_KEY
CARDS_PER_MISSION = 5
EVENT_TOKENS_SPRITE = (ATLAS, 4177870253614828354)
ZURKON_TOKEN = -5237341124298122588
TOKEN_ON_GROUND = True
ZURKON_TOKEN_OBJECTS = (ZURKON_TOKEN, 5952319859663788708, -2466255425291003228, 7861148539676220068)

def card_event03_edits():
    picture = struct.pack('<iq', 0, ZURKON_SPRITE) if PICTURE else struct.pack('<iq', *ICO_EVENT_ZURKON)
    anchors = (0.36, 0.04, 0.78, 0.96) if PICTURE else (0.45, 0.05, 0.9, 0.75)
    return [(CARD_ROOT_IMAGE + 12, b'\x00', b'\x01'), (CARD_ROOT_IMAGE + 88, struct.pack('<iq', ATLAS, -81423715014193705), struct.pack('<iq', *BG_EVENT01)), (CARD_ROOT_IMAGE + 104, b'\x01', b'\x00'), (CARD_ILLUSTRATION_IMAGE + 88, struct.pack('<iq', ATLAS, 3487435678033934294), picture), (CARD_ILLUSTRATION_RECT + 68, bytes.fromhex('9e71b335da40a736e6ff7f3fb0ff7f3f'), struct.pack('<4f', *anchors))]
CARD_EVENT03_OBJECTS = [-8656910176408572051, -6098841626221023379, 3474090388851584877, 533049979149479789, -6213716865482559635, 3513255527455059821, -3006274117324509331, -3740602691665596563]
COPY_KEY = 6820431451652218957
CARD_EVENT04 = (0, CARD_EVENT03_OBJECTS[0] ^ COPY_KEY)
GRADIENT2 = (ATLAS, -7441113594088017417)
CARD_EVENT04_TINT = (0.2, 0.45, 0.95, 1.0)
EVENT_INFO_POPUP = (0, -7515808230911447187)
LEADERBOARD_REWARDS_POPUP = (0, -1566872096122892834)
RIVET_BOT_BEHAVIOURS = [(0, 4457749605718931784), (0, -1551908171866690828), (0, -1551908171866690828), (0, 1325605632935867877)]
RIVET_BOT_PROFILES = [(0, 918726665249132734)]
NO_CHARACTER = (('NONE', 0, 0), ('IDLE', 0, 0), ('BOTTOM_LEFT', 0, 0), 0.0, 0)

def entry(event_id, icon, title, description, *, image=NONE, background=NONE, animated_illustration=NONE, animated_background=NONE, completed_background=NONE, card=NONE, info_popup=NONE, rewards_popup=NONE, in_battle_menus=0, rules=('', 0), token_icon=NONE, token_prefab=NONE, bot_behaviours=(), bot_profiles=()):
    return {'eventID': event_id, 'icon': icon, 'allAnimatedIcons': [icon] * 4, 'image': image, 'background': background, 'animatedIllustration': animated_illustration, 'animatedBackground': animated_background, 'animatedIllustration_eventCompleted': NONE, 'animatedBackground_eventCompleted': completed_background, 'eventCardBackground': card, 'mainCharacter': 0, 'legacyCharacter': NO_CHARACTER, 'infoPopupPrefab': info_popup, 'giveRewardsPopupPrefab': NONE, 'leaderboardRewardsPopupPrefab': rewards_popup, 'leaderboardRankPrefab': NONE, 'displayEventInBattleMenus': in_battle_menus, 'legacyCharacterEndGameScreen': NO_CHARACTER, 'legacyCharacterEndGameScreenLose': NO_CHARACTER, 'title': (title, 0), 'description': (description, 0), 'rules': rules, 'compensationPart1': ('', 0), 'compensationPart2': ('', 0), 'tokenIcon': token_icon, 'tokenPrefab': token_prefab, 'ticketIcon': NONE, 'requiredCharacters': [], 'sfx': (0, 0, 0, 0), 'botBehaviours': list(bot_behaviours), 'botProfiles': list(bot_profiles)}

def new_entries():
    zurkon = {'animated_background': HUD_EVENT01_BG, 'completed_background': HUD_EVENT01_VALIDATE_BG}
    if PICTURE:
        zurkon = {'image': (0, ZURKON_SPRITE), 'animated_illustration': (0, ZURKON_ILLUSTRATION), 'background': BG_EVENT01, 'animated_background': HUD_EVENT00_BG, 'completed_background': HUD_EVENT01_VALIDATE_BG}
    return [entry(ZURKON_EVENT, ICO_ZURKON, 'UI.EVENT.ZURKON.TITLE', 'UI.EVENT.ZURKON.DESC', card=CARD_BACKGROUND_EVENT03, token_icon=ICO_ZURKON, token_prefab=(0, ZURKON_TOKEN) if TOKEN_ON_GROUND else NONE, rules=('UI.EVENT.ZURKON.RULES', 0), **zurkon), entry(RANDOM_WEAPON_EVENT, ICO_EVENT_RANDOM_WEAPON, 'UI.EVENT.RANDOM_WEAPON.TITLE', 'UI.EVENT.RANDOM_WEAPON.DESC', card=CARD_EVENT04, info_popup=EVENT_INFO_POPUP, rewards_popup=LEADERBOARD_REWARDS_POPUP, in_battle_menus=1, rules=('', 1), token_icon=ICO_RANDOM_WEAPON, bot_behaviours=RIVET_BOT_BEHAVIOURS, bot_profiles=RIVET_BOT_PROFILES)]

def string(text):
    raw = text.encode()
    return struct.pack('<I', len(raw)) + raw + bytes(-len(raw) % 4)

def pptr(ref):
    return struct.pack('<iq', *ref)

def pptrs(refs):
    return struct.pack('<i', len(refs)) + b''.join((pptr(r) for r in refs))

def character(action):
    *proxies, duration, easing = action
    raw = b''.join((string(name) + struct.pack('<ii', index, value) for name, index, value in proxies))
    return raw + struct.pack('<fi', duration, easing)

def key(value):
    text, mode = value
    return string(text) + struct.pack('<i', mode)

def serialize(e):
    raw = struct.pack('<i', e['eventID']) + pptr(e['icon']) + pptrs(e['allAnimatedIcons'])
    for name in ('image', 'background', 'animatedIllustration', 'animatedBackground', 'animatedIllustration_eventCompleted', 'animatedBackground_eventCompleted', 'eventCardBackground'):
        raw += pptr(e[name])
    raw += struct.pack('<i', e['mainCharacter']) + character(e['legacyCharacter'])
    for name in ('infoPopupPrefab', 'giveRewardsPopupPrefab', 'leaderboardRewardsPopupPrefab', 'leaderboardRankPrefab'):
        raw += pptr(e[name])
    raw += struct.pack('<B3x', e['displayEventInBattleMenus'])
    raw += character(e['legacyCharacterEndGameScreen']) + character(e['legacyCharacterEndGameScreenLose'])
    for name in ('title', 'description', 'rules', 'compensationPart1', 'compensationPart2'):
        raw += key(e[name])
    raw += pptr(e['tokenIcon']) + pptr(e['tokenPrefab']) + pptr(e['ticketIcon'])
    raw += struct.pack('<i', len(e['requiredCharacters'])) + b''.join((struct.pack('<i', c) for c in e['requiredCharacters']))
    raw += struct.pack('<4I', *e['sfx'])
    return raw + pptrs(e['botBehaviours']) + pptrs(e['botProfiles'])

def from_json(e):

    def ref(p):
        return (p['m_FileID'], p['m_PathID'])

    def act(a):
        proxies = [a[f'<{n}>k__BackingField'] for n in ('CharacterID', 'ExpressionID', 'CharacterScreenPosition')]
        return (*[(p['_proxy'], p['_index'], p['_value']) for p in proxies], a['<CharacterMoveDuration>k__BackingField'], a['<CharacterMoveEasing>k__BackingField'])
    out = {k: ref(v) if isinstance(v, dict) and 'm_PathID' in v else v for k, v in e.items()}
    out['allAnimatedIcons'] = [ref(p) for p in e['allAnimatedIcons']]
    out['botBehaviours'] = [ref(p) for p in e['botBehaviours']]
    out['botProfiles'] = [ref(p) for p in e['botProfiles']]
    for name in ('legacyCharacter', 'legacyCharacterEndGameScreen', 'legacyCharacterEndGameScreenLose'):
        out[name] = act(e[name])
    for name in ('title', 'description', 'rules', 'compensationPart1', 'compensationPart2'):
        out[name] = (e[name]['_value'], e[name]['_mode'])
    out['sfx'] = (e['startGameSFX'], e['winGameSFX'], e['loseGameSFX'], e['levelUpSFX'])
    return out

def events_meta(old):
    name_size, = struct.unpack_from('<I', old, 28)
    count_at = 32 + name_size + -name_size % 4
    count, = struct.unpack_from('<i', old, count_at)
    if old[32:32 + name_size] != b'EventsMetaData' or count != 3:
        raise SystemExit('EventsMetaData inattendu')
    entries = new_entries()
    added = b''.join((serialize(e) for e in entries))
    return old[:count_at] + struct.pack('<i', count + len(entries)) + old[count_at + 4:] + added

def card_event04(object_id, raw):
    for old in CARD_EVENT03_OBJECTS:
        raw = raw.replace(struct.pack('<iq', 0, old), struct.pack('<iq', 0, old ^ COPY_KEY))
    raw = bytearray(raw)
    if object_id == CARD_EVENT03_OBJECTS[0]:
        at = raw.index(b'CardBackground_Event03')
        raw[at:at + 22] = b'CardBackground_Event04'
    elif object_id == CARD_EVENT03_OBJECTS[1]:
        father = raw.index(struct.pack('<iq', 0, 3690149658893217645))
        raw[father:father + 12] = struct.pack('<iq', 0, 0)
    elif object_id == CARD_EVENT03_OBJECTS[3]:
        raw[44:60] = struct.pack('<4f', *CARD_EVENT04_TINT)
        raw[88:100] = struct.pack('<iq', *GRADIENT2)
        raw[104] = 0
    elif object_id == CARD_EVENT03_OBJECTS[5]:
        raw[68:84] = struct.pack('<4f', 0.5, 0.24, 0.8, 0.76)
    elif object_id == CARD_EVENT03_OBJECTS[7]:
        raw[88:100] = struct.pack('<iq', *ICO_EVENT_RANDOM_WEAPON)
    return bytes(raw)
