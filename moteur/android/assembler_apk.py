import collections
import contextlib
import functools
import hashlib
import io
import json
import os
import re
import sys
import unicodedata
import zipfile
import msgpack
HERE = os.path.dirname(os.path.abspath(__file__))
STORED = zipfile.ZIP_STORED
ENTRY_DATE = (1981, 1, 1, 1, 1, 0)
OFFLINE = 'assets/rr_offline/'
BASE_PART, LIBRARY_PART, PACK_PART = ('com.playstation.rattlesnake.apk', 'config.arm64_v8a.apk', 'UnityDataAssetPack.apk')
LIBRARY = 'lib/arm64-v8a/libil2cpp.so'
RELEASE = '1.10.4'
HEROES_RELEASE = '1.10.3'
HEROES_BUILD = '8571'
WEAPON_UNLOCK, SKIN, LOOT_BOX, CURRENCY, HERO_UNLOCK, HERO_LORBS = (1, 2, 3, 6, 12, 13)
RARITANIUM, EVENT_TOKENS, CREDITS = (1, 4, 5)
COMMON_BOX, EPIC_BOX = (2, 4)

class PlainZip:

    def __init__(self, path):
        self.zip = zipfile.ZipFile(path, 'w', allowZip64=True)

    def add(self, name, content, compress):
        entry = zipfile.ZipInfo(name, date_time=ENTRY_DATE)
        entry.compress_type = compress
        self.zip.writestr(entry, content)

    def close(self):
        self.zip.close()

def zip_writer_class():
    if os.environ.get('RR_ALIGNE') != '1':
        return PlainZip
    sys.path.insert(0, os.path.join(HERE, '..', 'appli_patch'))
    from signature import AlignedZip
    return AlignedZip

class ApkWriter:

    def __init__(self, path):
        self.zip = zip_writer_class()(path)
        self.names = set()

    def add(self, name, content, compress=STORED):
        if name in self.names:
            raise SystemExit(f'doublon : {name}')
        self.names.add(name)
        self.zip.add(name, content, compress)

    def close(self):
        self.zip.close()

def read_file(path):
    with open(path, 'rb') as handle:
        return handle.read()
SKIN_BUNDLE = re.compile('skins_character_([a-z]+)_skin(\\d+)_assets_all')
OFFLINE_GAME_PATCH = (69183428, bytes.fromhex('1b000014'))
PHOTON_SETTINGS = 'assets/bin/Data/3df92cddd091603488eec50366992dc0'
PHOTON_LOCAL_HOST = b'\t\x00\x00\x00127.0.0.1'
MONOSCRIPTS_BUNDLE = 'assets/aa/Android/913fdc02988c9f04b9d53c5645e34846_monoscripts_b5e55861ec07d2dfb6815884c7e4041c.bundle'
GALLERY_ARROW = 'arrow_02'

class PatchedGame:

    def __init__(self, folder):
        self.base = zipfile.ZipFile(os.path.join(folder, BASE_PART))
        self.libs = zipfile.ZipFile(os.path.join(folder, LIBRARY_PART))
        self.pack = zipfile.ZipFile(os.path.join(folder, PACK_PART))
        self.pack_names = self.pack.namelist()

    def close(self):
        for part in (self.base, self.libs, self.pack):
            part.close()

    def has_model(self, name):
        return any((f'skins_character_{name}_assets_all_' in path for path in self.pack_names))

    @functools.cached_property
    def skins_with_model(self):
        skins = set()
        for name in self.pack_names:
            match = SKIN_BUNDLE.search(name)
            if match:
                skins.add(f'{match.group(1).upper()}_SKIN{match.group(2)}')
        return skins

    def ready_for_squads(self):
        offset, code = OFFLINE_GAME_PATCH
        if self.libs.read(LIBRARY)[offset:offset + len(code)] != code:
            return False
        return PHOTON_LOCAL_HOST in self.pack.read(PHOTON_SETTINGS)

    def has_collect_screen(self):
        return MONOSCRIPTS_BUNDLE in self.pack_names and b'EventRewardCollectUI' in self.pack.read(MONOSCRIPTS_BUNDLE)

    def gallery_arrow(self):
        import UnityPy
        for name in self.pack_names:
            if name.split('/')[-1].startswith('ui_atlases_'):
                for obj in UnityPy.load(self.pack.read(name)).objects:
                    if obj.type.name == 'Sprite' and obj.peek_name() == GALLERY_ARROW:
                        picture = io.BytesIO()
                        obj.read().image.save(picture, 'PNG')
                        return picture.getvalue()
        return None

def config_item(config, key):
    return next((i for i in config['items'] if i['key'] == key))

def decoded(config, key):
    return json.loads(config_item(config, key)['value'])

def store(item, value):
    item['value'] = json.dumps(value, separators=(',', ':'), ensure_ascii=False).encode()
    item['hash'] = hashlib.md5(item['value']).hexdigest()[:12]

@contextlib.contextmanager
def edited(config, key):
    item = config_item(config, key)
    value = json.loads(item['value'])
    yield value
    store(item, value)

def json_copy(value):
    return json.loads(json.dumps(value))

@functools.cache
def skin_ids():
    with open(os.path.join(HERE, 'skin_ids.json'), encoding='utf-8') as handle:
        return json.load(handle)

def loot(kind, amount=1, currency=0, box=0, unlockable=0):
    return {'type': kind, 'amount': amount, 'unlockableID': unlockable, 'currencyID': currency, 'rarityInfo': 0, 'lootBoxID': box}
SHOP_OFFER = 770
DAILY_OFFER = 513

def offer_family(offer):
    return offer['uniqueID']['_internalPackedID'] >> 16

def next_offer_id(offers, family=SHOP_OFFER):
    return max((o['uniqueID']['_internalPackedID'] for o in offers if offer_family(o) == family)) + 1

def offer_named(offers, name):
    return next((o for o in offers if o['enumName'] == name))

def has_offer(offers, name):
    return any((o['enumName'] == name for o in offers))

def offer_copy(model, offer_id, name, title=None):
    offer = json_copy(model)
    offer['uniqueID']['_internalPackedID'] = offer_id
    offer['enumName'] = name
    if title is not None:
        offer['title'] = title
    return offer
HIDDEN_HEROES = {'CHANCE': 119, 'MOLLY': 122, 'HELEN': 123, 'FLARE': 209, 'NAKARI': 210, 'TERRY': 211, 'CRUMBY': 227}
BASE_SKINS = {70, 71, 74, 80, 82, 85, 104, 107, 108, 119, 122, 123, 143, 151, 160, 161, 209, 210, 211, 227, 228}
NEW_SKIN_RARITIES = {'helen_skin01': 'SKIN_HELEN_SKIN01', 'juycee_skin01': 'SKIN_JUYCEE_SKIN01', 'juycee_skin02': 'SKIN_JUYCEE_SKIN02', 'juycee_skin03': 'SKIN_JUYCEE_SKIN03', 'juycee_skin04': 'SKIN_JUYCEE_SKIN04', 'rivet': 'SKIN_RATCHET_SKIN01'}
MAIN_SOURCE, LOOTABLE_SOURCE = (2, 4)
EDITOR_ONLY = 1

def shop_without_cdn_skins(config):
    rarities = decoded(config, 'raritieseconomydata')
    ids = skin_ids()
    with edited(config, 'shopdata') as table:
        for offer in table['shopOffers']:
            if offer['enumName'].startswith('DailySkin'):
                offer['disabled'] = True
        for name in rarities['unlockablesRarities']:
            uid = ids.get(name)
            if name.startswith('SKIN_') and uid is not None and (uid not in BASE_SKINS) and (uid not in table['skinsForbiddenInShop']):
                table['skinsForbiddenInShop'].append(uid)

def open_hidden_hero_skin(name, entry, old, modelled):
    costume = name[5:].replace('_DEPRECATED', '')
    if old or name.endswith('_SKIN00') or costume in modelled:
        entry['availabilityType'] = 0
    else:
        entry['availabilityType'] = EDITOR_ONLY
    if old:
        return
    if costume in modelled:
        entry['source'] = 0
    if name.endswith('_SKIN00'):
        entry['source'] = LOOTABLE_SOURCE
        entry['seasonPassIndex'] = -1

def open_hidden_heroes(config, game, release):
    old = release == HEROES_RELEASE
    modelled = set() if old else game.skins_with_model
    with edited(config, 'raritieseconomydata') as table:
        rarities = table['unlockablesRarities']
        for name, entry in rarities.items():
            if name.startswith('SKIN_') and name.split('_')[1] in HIDDEN_HEROES:
                open_hidden_hero_skin(name, entry, old, modelled)
        if not old:
            for bundle, skin in NEW_SKIN_RARITIES.items():
                if game.has_model(bundle):
                    rarities[skin] = {'rarity': 2, 'availabilityType': 0, 'source': 0, 'seasonPassIndex': -1}
        rarities['WP_SCORPIONFLAIL_DEPRECATED'] = {'rarity': 2, 'availabilityType': 0, 'source': 2, 'seasonPassIndex': -1}
        if not old and 'WP_WIDGETMELEEGADGET' in rarities:
            rarities['WP_WIDGETMELEEGADGET'].update(rarity=1, availabilityType=0)
        if old:
            table['possibleUserSkins'] = [skin for skin in table['possibleUserSkins'] if skin in BASE_SKINS]
        else:
            possible = table['possibleUserSkins']
            possible += [uid for uid in HIDDEN_HEROES.values() if uid not in possible]

def add_modelled_costumes(apk, game):
    ids = skin_ids()
    worn = sorted((ids[key] for name in game.skins_with_model if name.split('_')[0] in HIDDEN_HEROES for key in (f'SKIN_{name}', f'SKIN_{name}_DEPRECATED') if key in ids))
    if worn:
        apk.add(OFFLINE + 'costumes.txt', '\n'.join(map(str, worn)).encode())
        print(f'costumes avec modele : {worn}')
HERO_POWER_RARITIES = {(3000, 900): ('SANDY', 'CHIP', 'SPROCKET', 'TERRY', 'FLARE', 'NAKARI'), (3900, 850): ('FUSE', 'LIL_ANN', 'LUMP', 'MARKUS', 'RAIDEN', 'HELEN', 'MOLLY', 'CRUMBY'), (4800, 800): ('CELESTE', 'CHANCE', 'GRIMSHOT', 'STEELJAW', 'ZEDONE', 'RATCHET')}
JUYCEE_SKINS = (83, 84, 86, 109, 41)

def add_hero_powers(apk, game):
    powers = {name: power for power, names in HERO_POWER_RARITIES.items() for name in names}
    powers['AVATAR'] = (4800, 800) if game.has_model('rivet') else (3000, 900)
    ids = skin_ids()
    lines = {}
    for key, skin in ids.items():
        hero = re.sub('_SKIN\\d+(_DEPRECATED)?$', '', key[len('SKIN_'):])
        base = ids.get(f'SKIN_{hero}_SKIN00')
        if hero in powers and base is not None:
            lines[skin] = (base, *powers[hero])
    if game.has_model('juycee'):
        for skin in JUYCEE_SKINS:
            lines[skin] = (JUYCEE_SKINS[0], 4800, 800)
    apk.add(OFFLINE + 'puissances.txt', '\n'.join((f'{skin} {base} {first} {step}' for skin, (base, first, step) in sorted(lines.items()))).encode())
BOLT_RUSH_MODE = 114
BOLT_KING_MODE = 131
BOLT_RUSH_SOLO_MODE = 68
BATTLE_ROYALE_MODE = 57
LAST_STAND_MODE = 219
FREE_FOR_ALL_MODE = 125

def add_bolt_rush_mode(config):
    with edited(config, 'gamemodesdata') as value:
        listed = value.get('data', value)['permanentGameModes']
        if BOLT_RUSH_MODE not in listed:
            listed.insert(listed.index(BOLT_KING_MODE) + 1, BOLT_RUSH_MODE)
        if BOLT_RUSH_SOLO_MODE not in listed:
            listed.insert(listed.index(BOLT_RUSH_MODE) + 1, BOLT_RUSH_SOLO_MODE)
        if BATTLE_ROYALE_MODE not in listed:
            listed.insert(listed.index(LAST_STAND_MODE) + 1, BATTLE_ROYALE_MODE)
    with edited(config, 'matchmakingconfigdata') as value:
        configured = value.get('data', value)['GameModeConfigs']
        for mode in (BOLT_RUSH_MODE, BOLT_RUSH_SOLO_MODE, BATTLE_ROYALE_MODE):
            if not any((entry['gameModeId'] == mode for entry in configured)):
                configured.append({'gameModeId': mode, 'forceOffline': True, 'noBotFill': False})
OFFLINE_ONLY_MODES = {159}

def allow_squads(config):
    with edited(config, 'matchmakingconfigdata') as value:
        settings = value.get('data', value)
        for entry in settings['GameModeConfigs']:
            entry['forceOffline'] = entry['gameModeId'] in OFFLINE_ONLY_MODES
    shared = sum((1 for entry in settings['GameModeConfigs'] if not entry['forceOffline']))
    print(f'modes jouables en groupe : {shared}')
    item = config_item(config, 'eventseconomydata')
    table = json.loads(item['value'])
    opened = []
    for event in table['events']:
        info = event.get('additionalInfo') or {}
        if info.get('disableSquad') and info.get('eventGameMode') not in OFFLINE_ONLY_MODES:
            info['disableSquad'] = 0
            opened.append(event['id'])
    if opened:
        store(item, table)
    print(f'evenements ouverts au groupe : {opened}')
GALLERY_URL = 'rrgalerie://artworks'
PICTURES = ('.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp')

def open_gallery(config):
    item = next((i for i in config['items'] if i['key'] == 'urlconfigdata'), None)
    if item is None or not item.get('value'):
        return
    value = json.loads(item['value'])
    value['URLInstagram'] = GALLERY_URL
    store(item, value)

def files_under(folder):
    for root, folders, names in os.walk(folder):
        folders[:] = sorted((f for f in folders if not f.startswith('.')))
        for name in sorted(names):
            if not name.startswith('.'):
                yield (root, name)

def add_artbook(apk):
    folder = os.environ.get('RR_ARTBOOK')
    if not folder or not os.path.isfile(os.path.join(folder, 'artbook.json')):
        return 0
    count = 0
    for root, name in files_under(folder):
        path = os.path.join(root, name)
        relative = os.path.relpath(path, folder).replace(os.sep, '/')
        apk.add(f'{OFFLINE}artbook/{relative}', read_file(path))
        if name.endswith('.webp') and '/v/' not in f'/{relative}':
            count += 1
    return count

def add_artworks(apk):
    folder = os.environ.get('RR_ARTWORKS')
    if not folder or not os.path.isdir(folder):
        return 0
    taken = set()
    for root, name in files_under(folder):
        if not name.lower().endswith(PICTURES) or name.lower().startswith('screenshot'):
            continue
        name_in_apk = unicodedata.normalize('NFC', name)
        if name_in_apk in taken:
            continue
        taken.add(name_in_apk)
        apk.add(f'{OFFLINE}artworks/{name_in_apk}', read_file(os.path.join(root, name)))
    return len(taken)

def add_gallery(apk, game):
    book = add_artbook(apk)
    pictures = add_artworks(apk)
    if not (book or pictures):
        return
    arrow = game.gallery_arrow()
    if arrow:
        apk.add(OFFLINE + 'galerie/fleche.png', arrow)
    print(f'galerie : {book or pictures} images' + (' (artbook)' if book else '') + (', fleches du jeu' if arrow else ''))
ZURKON_EVENT = 1
RANDOM_WEAPON_EVENT = 2
RESCUE_MOPZ_EVENT = 3
ZURKON_CATEGORY = 1
RANDOM_WEAPON_CATEGORY = 2
DROP_TOKENS_MODIFIER, RANDOM_WEAPON_MODIFIER = (1, 2)
ZURKON_CARDS_PER_MISSION = 5
ELIMINATE_N_MOBS, ELIMINATE_N_OPPONENTS, WIN_N_BATTLES, BREAK_N_CRATES = (1, 2, 3, 4)
USE_ULTIMATE_N_TIMES, PLAY_N_GAMES, GATHER_BOLTS = (5, 13, 16)

def mission(objective, target):
    return {'objective': objective, 'targetProgression': target, 'modifier': {'type': 0, 'metadata': []}}

def old_event(event_id, category, **fields):
    event = {'id': event_id, 'category': category, 'activeEvent': 0, 'ticketInfo': {'maxAmount': 0, 'rechargeTime': 0}, 'accessMode': 0, 'modifier': {'modifier': 0, 'value': 0}, 'rewardTrack': {'rewards': [], 'loopMode': 0}, 'onWin': {'rankToWin': 0, 'tokenAmount': 0}, 'dialogueID': 0, 'missions': {'missionsPerDay': []}, 'daysLocalNotificationsPrefix': '', 'nbDaysLocalNotifications': 0, 'excludeWeaponAndHeroLootsFromLootboxesIfActive': 0, 'durationInHours': 24, 'notDisplayedInEventsSelectionScreen': 0, 'delayAfterNotifIncrementMinutes': 0, 'additionalInfo': {'eventConditions': [], 'eventGameMode': 0, 'disablePlayAgain': 0, 'disableSquad': 0, 'showInfoPopupOnlyOnce': 0, 'directlyGoBackToMenuAfterBattle': 0}, 'leaderboardInfo': {'hasLeaderboard': 0, 'needToPreregisterLeaderboard': 0, 'realPlayersMaxCount': 0, 'playersCount': 0, 'rewards': [], 'scoreType': 0, 'menuRefreshDelaySeconds': 0.0}, 'disableNewInstances': 0}
    event.update(fields)
    return event

def zurkon_event(collect):
    track = [(loot(CURRENCY, 150, RARITANIUM), 15), (loot(LOOT_BOX, box=EPIC_BOX), 25), (loot(CURRENCY, 300, RARITANIUM), 35), (loot(LOOT_BOX, box=EPIC_BOX), 50), (loot(LOOT_BOX, box=EPIC_BOX), 75), (loot(CURRENCY, 25, RARITANIUM), 75 if collect else 100)]
    days = [[mission(BREAK_N_CRATES, 10), mission(PLAY_N_GAMES, 3), mission(ELIMINATE_N_OPPONENTS, 10), mission(GATHER_BOLTS, 300), mission(WIN_N_BATTLES, 2)], [mission(BREAK_N_CRATES, 20), mission(PLAY_N_GAMES, 5), mission(ELIMINATE_N_MOBS, 15), mission(USE_ULTIMATE_N_TIMES, 5), mission(WIN_N_BATTLES, 3)], [mission(BREAK_N_CRATES, 30), mission(PLAY_N_GAMES, 7), mission(ELIMINATE_N_OPPONENTS, 20), mission(GATHER_BOLTS, 600), mission(WIN_N_BATTLES, 4)]]
    rewards = [loot(CURRENCY, ZURKON_CARDS_PER_MISSION, EVENT_TOKENS)] * 5
    return old_event(ZURKON_EVENT, ZURKON_CATEGORY, modifier={'modifier': DROP_TOKENS_MODIFIER, 'value': 0}, durationInHours=72, rewardTrack={'rewards': [{'lootData': data, 'price': price, 'fastPrice': ''} for data, price in track], 'loopMode': 0}, missions={'missionsPerDay': [] if collect else [{'missions': day, 'rewards': rewards} for day in days]})

def random_weapon_event():
    box = {'lootData': loot(LOOT_BOX, box=COMMON_BOX), 'price': 1, 'fastPrice': ''}
    return old_event(RANDOM_WEAPON_EVENT, RANDOM_WEAPON_CATEGORY, activeEvent=1, accessMode=1, modifier={'modifier': RANDOM_WEAPON_MODIFIER, 'value': 0}, rewardTrack={'rewards': [box] * 6, 'loopMode': 0}, onWin={'rankToWin': int(os.environ.get('RR_RANG_ARME', '5')), 'tokenAmount': 1}, durationInHours=96, delayAfterNotifIncrementMinutes=180, additionalInfo={'eventConditions': [{'triggerCondition': 0, 'triggerConditionParameter': 0, 'triggerConditionParameterString': ''}], 'eventGameMode': FREE_FOR_ALL_MODE, 'disablePlayAgain': 1, 'disableSquad': 1, 'showInfoPopupOnlyOnce': 1, 'directlyGoBackToMenuAfterBattle': 1}, leaderboardInfo={'hasLeaderboard': 1, 'needToPreregisterLeaderboard': 0, 'realPlayersMaxCount': 2, 'playersCount': 6, 'rewards': [], 'scoreType': 1, 'menuRefreshDelaySeconds': 120.0})

def add_old_events(config, game):
    item = config_item(config, 'eventseconomydata')
    table = json.loads(item['value'])
    if any((e['id'] in (ZURKON_EVENT, RANDOM_WEAPON_EVENT) for e in table['events'])):
        return
    table['events'][:0] = [zurkon_event(game.has_collect_screen()), random_weapon_event()]
    table['eventSchedulers'] += [{'eventID': RANDOM_WEAPON_EVENT, 'startDay': 3}]
    mopz = next((info for info in table['nonScheduledEventsInfos'] if info['eventID'] == RESCUE_MOPZ_EVENT))
    table['nonScheduledEventsInfos'].append({'eventID': ZURKON_EVENT, 'condition': dict(mopz['condition']), 'durationInHours': 72, 'isInfinite': False})
    store(item, table)
RIVET_SKIN, RIVET_CHARACTER, RATCHET_CHARACTER, RATCHET_SKIN = (160, 16, 22, 228)
WENDY_SKIN, WENDY_CHARACTER = (85, 7)
JUYCEE_SKIN, JUYCEE_CHARACTER, CHANCE_CHARACTER, CHANCE_SKIN = (83, 23, 11, 119)
STEELJAW_COSTUMES = ('SKIN_STEELJAW_SKIN01', 'SKIN_STEELJAW_SKIN02', 'SKIN_STEELJAW_SKIN03', 'SKIN_STEELJAW_SKIN04')
WENDY_VISIBLE = os.environ.get('RR_WENDY') == '1'

def open_cinematic_hero(config, character, skin, skin_name, offer_name, model=RATCHET_CHARACTER, model_skin=RATCHET_SKIN, model_skin_name='SKIN_RATCHET_SKIN00', hidden=False, sold=False):
    with edited(config, 'characterfavoriteweaponsdata') as weapons:
        for values in weapons.values():
            if len(values) > model:
                while len(values) <= character:
                    values.append(values[model])
                values[character] = values[model]
    with edited(config, 'raritieseconomydata') as rarities:
        rarities['unlockablesRarities'][skin_name] = dict(rarities['unlockablesRarities'][model_skin_name])
        if sold:
            rarities['unlockablesRarities'][skin_name].update(source=LOOTABLE_SOURCE, seasonPassIndex=-1)
        if skin not in rarities['possibleUserSkins'] and (not hidden):
            rarities['possibleUserSkins'].append(skin)
        if character == WENDY_CHARACTER:
            for costume in STEELJAW_COSTUMES:
                if costume in rarities['unlockablesRarities']:
                    rarities['unlockablesRarities'][costume]['availabilityType'] = EDITOR_ONLY
    with edited(config, 'medalrun') as medals:
        roads = medals['medalRoadByCharacterId']
        road = json_copy(roads[model])
        for reward in road['Rewards']:
            if reward['loot']['unlockableID'] == model_skin:
                reward['loot']['unlockableID'] = skin
        while len(roads) <= character:
            roads.append({'Rewards': []})
        roads[character] = road
    with edited(config, 'shopdata') as shop:
        offers = shop['shopOffers']
        if not hidden and (not has_offer(offers, offer_name)):
            offer = offer_copy(offer_named(offers, 'Lorbs_Chance_300'), next_offer_id(offers), offer_name, offer_name)
            offer['costData'] = dict(offer_named(offers, 'Lorbs_R1_300')['costData'])
            offer['contentLoots'][0]['unlockableID'] = skin
            offers.append(offer)

def add_cinematic_heroes(apk, game, config):
    if game.has_model('wendy'):
        open_cinematic_hero(config, WENDY_CHARACTER, WENDY_SKIN, 'SKIN_STEELJAW_SKIN00', 'Lorbs_Wendy_300', hidden=not WENDY_VISIBLE)
        apk.add(OFFLINE + 'wendy', str(WENDY_SKIN).encode())
        print('Wendy : heroine a part (personnage STEELJAW)' + ('' if WENDY_VISIBLE else ', cachee'))
    if game.has_model('rivet'):
        open_cinematic_hero(config, RIVET_CHARACTER, RIVET_SKIN, 'SKIN_AVATAR_SKIN00', 'Lorbs_Rivet_300', sold=True)
        print('Rivet : heroine a part (personnage AVATAR)')
    if game.has_model('juycee'):
        open_cinematic_hero(config, JUYCEE_CHARACTER, JUYCEE_SKIN, 'SKIN_JUYCEE_SKIN00', 'Lorbs_Juycee_300', CHANCE_CHARACTER, CHANCE_SKIN, 'SKIN_CHANCE_SKIN00')
        print('Juycee : heroine a part (personnage 23)')
CORES_PRICE = 100
DAILY_RARITANIUM = {3: 15, 7: 25}

def daily_rewards(config):
    with edited(config, 'dailyrewardsdata') as value:
        rewards = value['permanentDailyRewards']['allRewards']
        for day, amount in DAILY_RARITANIUM.items():
            reward = rewards[day - 1]
            if (reward['type'], reward['currencyID']) != (CURRENCY, RARITANIUM):
                raise SystemExit(f'recompense du jour {day} : pas du Raritanium')
            reward['amount'] = amount

def is_hero_orbs_offer(offer):
    contents = offer.get('contentLoots') or []
    return offer_family(offer) == SHOP_OFFER and bool(contents) and all((content['type'] == HERO_LORBS and content['unlockableID'] for content in contents))

def skins_on_roads(medals):
    skins = {r['loot']['unlockableID'] for r in medals['mainRoad'] if r['loot']['type'] == SKIN}
    skins |= {r['loot']['unlockableID'] for road in medals['medalRoadByCharacterId'] for r in road['Rewards'] if r['loot']['type'] == SKIN}
    return skins

def shop_adjustments(config):
    removed = 0
    with edited(config, 'shopdata') as shop:
        for offer in shop['shopOffers']:
            if offer['enumName'] == 'Cores_1_RSS':
                offer['costData'] = dict(offer['costData'], currencyId=RARITANIUM, cost=CORES_PRICE)
            if offer['enumName'] == 'Blueprints_ScorpionFlail_100' and (not offer.get('disabled')):
                offer['disabled'] = True
                removed += 1
            if is_hero_orbs_offer(offer) and (not offer.get('disabled')):
                offer['disabled'] = True
                removed += 1
        on_roads = skins_on_roads(decoded(config, 'medalrun'))
        freed = [skin for skin in shop['skinsForbiddenInShop'] if skin not in on_roads]
        shop['skinsForbiddenInShop'] = [skin for skin in shop['skinsForbiddenInShop'] if skin in on_roads]
    print(f'boutique : Power cores a {CORES_PRICE} Raritanium, {removed} offres retirees (orbes de heros, plans du fleau)')
    print(f'boutique : costumes du passe de saison remis dans les offres du jour {freed}')
HEADHUNTER = 11
HEADHUNTER_OFFER = 'Weapon_Headhunter'
WEAPON_OFFER_MODEL = 'Blueprints_ScorpionFlail_100'

def headhunter_offer(config):
    item = config_item(config, 'shopdata')
    shop = json.loads(item['value'])
    offers = shop['shopOffers']
    if has_offer(offers, HEADHUNTER_OFFER):
        return
    costs = decoded(config, 'weaponsunlockdata')['costsByRarity']
    rarity = decoded(config, 'raritieseconomydata')['unlockablesRarities']['WP_HEADHUNTER']['rarity']
    offer = offer_copy(offer_named(offers, WEAPON_OFFER_MODEL), next_offer_id(offers), HEADHUNTER_OFFER, HEADHUNTER_OFFER)
    offer['disabled'] = True
    offer['costData'] = dict(next((c['costData'] for c in costs if c['rarity'] == rarity)))
    offer['contentLoots'] = [loot(WEAPON_UNLOCK, unlockable=HEADHUNTER)]
    offer['ignoreOfferIfAnyWeaponAlreadyOwned'] = [HEADHUNTER]
    offers.append(offer)
    store(item, shop)
    print(f"boutique : offre Headhunter desactivee (offre {offer['uniqueID']['_internalPackedID']:#x})")
HERO_SHEET_PRICE = 750

def hero_sheet_price(config):
    with edited(config, 'heroesunlockeconomydata') as table:
        for price in table['HeroPricingPerRarity']:
            if price['costData']['currencyId'] != RARITANIUM:
                raise SystemExit('prix des heros : monnaie inattendue')
            price['costData']['cost'] = HERO_SHEET_PRICE
    print(f'heros a acheter sur leur fiche : {HERO_SHEET_PRICE} Raritanium')
OWNERLESS_WEAPONS = {106: ('WP_ENFORCER', 'Weapon_Enforcer'), 115: ('WP_PLASMASTRIKER', 'Weapon_PlasmaStriker'), 9: ('WP_SCORPIONFLAIL_DEPRECATED', 'Weapon_ScorpionFlail')}
OWNERLESS_PRICE = 250

def ownerless_weapon_offers(config):
    costs = decoded(config, 'weaponsunlockdata')['costsByRarity']
    rarities = decoded(config, 'raritieseconomydata')['unlockablesRarities']
    with edited(config, 'shopdata') as shop:
        offers = shop['shopOffers']
        model = offer_named(offers, WEAPON_OFFER_MODEL)
        for weapon, (name, offer_name) in OWNERLESS_WEAPONS.items():
            if has_offer(offers, offer_name):
                continue
            rarity = rarities.get(name, {}).get('rarity')
            cost = next((dict(c['costData']) for c in costs if c['rarity'] == rarity), None)
            offer = offer_copy(model, next_offer_id(offers), offer_name, offer_name)
            offer['disabled'] = False
            offer['costData'] = cost or dict(model['costData'], currencyId=RARITANIUM, cost=OWNERLESS_PRICE)
            offer['contentLoots'] = [loot(WEAPON_UNLOCK, unlockable=weapon)]
            offer['ignoreOfferIfAnyWeaponAlreadyOwned'] = [weapon]
            offers.append(offer)
    print(f'boutique : armes sans heros {sorted(OWNERLESS_WEAPONS)}')
QREDITS_PER_RARITANIUM = 40
QREDIT_PLAN_OFFERS = ('DailyBlueprints_Qredits1', 'DailyBlueprints_Qredits2')
RARITANIUM_FOR_QREDITS = {25: 1000, 50: 2200, 100: 4800}
EXCHANGE_OFFERS = ('Credits900', 'Credits2000', 'Credits4500') + tuple((f'Raritanium{amount}_Qredits' for amount in RARITANIUM_FOR_QREDITS))

def qredit_plan_offers(config):
    with edited(config, 'shopdata') as shop:
        offers = shop['shopOffers']
        model = offer_named(offers, 'DailyBlueprints_Mix')
        for name in QREDIT_PLAN_OFFERS:
            if has_offer(offers, name):
                continue
            offer = offer_copy(model, next_offer_id(offers, DAILY_OFFER), name)
            for choice in offer['weightedContentLoots']:
                cost = choice['costData']
                choice['costData'] = dict(cost, currencyId=CREDITS, cost=cost['cost'] * QREDITS_PER_RARITANIUM)
            offer['costData'] = offer['weightedContentLoots'][0]['costData']
            offers.append(offer)
    print(f'boutique : 2 offres de plans en Qredits ({QREDITS_PER_RARITANIUM} Qredits le Raritanium)')

def raritanium_for_qredits(config):
    with edited(config, 'shopdata') as shop:
        offers = shop['shopOffers']
        model = offer_named(offers, 'Credits900')
        for amount, price in RARITANIUM_FOR_QREDITS.items():
            name = f'Raritanium{amount}_Qredits'
            if has_offer(offers, name):
                continue
            offer = offer_copy(model, next_offer_id(offers), name, f'{amount} Raritanium')
            offer['costData'] = dict(model['costData'], currencyId=CREDITS, cost=price)
            offer['contentLoots'] = [loot(CURRENCY, amount, currency=RARITANIUM)]
            offers.append(offer)
    print(f'boutique : Raritanium contre Qredits {RARITANIUM_FOR_QREDITS}')

def exchanges_last(config):
    with edited(config, 'shopdata') as shop:
        offers = shop['shopOffers']
        exchanges = [offer_named(offers, name) for name in EXCHANGE_OFFERS]
        shop['shopOffers'] = [o for o in offers if o['enumName'] not in EXCHANGE_OFFERS] + exchanges
    print('boutique : echanges Raritanium / Qredits a la fin des ressources')
RANGER_ROAD_HEROES = {122: 420, 123: 800, 211: 1250, 227: 2700, 119: 4000, 209: 5600, 83: 6200, 160: 8000}
RANGER_ROAD_ORBS = [(490, 122, 600), (1000, 123, 800), (1800, 211, 600), (3600, 227, 800), (4300, 123, 800), (4500, 119, 800), (5400, 122, 800), (5700, 209, 1000), (6600, 83, 1000), (7000, 209, 1000), (7500, 119, 1000), (7600, 211, 1000), (7900, 227, 1000), (8200, 160, 1000), (9200, 160, 1000)]
NAKARI_SKIN, NAKARI_PRICE, NAKARI_OFFER = (210, 750, 'Hero_Nakari')
NAKARI_CHARACTER, NAKARI_MEDAL_ORBS = (19, {100: 600, 400: 600, 500: 700, 700: 1000, 800: 1000})
HERO_WEAPONS = {82: (1, 229), 70: (4, 230), 71: (5, 231), 74: (113, 135), 80: (128, 10), 104: (127, 3), 107: (130, 129), 108: (64, 6), 143: (2, 69), 151: (65, 116), 161: (11, 117), 228: (232, 233), 160: (232, 233)}
HERO_WEAPONS.update({skin: (1, 10) for skin in (119, 122, 123, 209, 210, 211, 227, 83)})
STARTER_HEROES = (82,)
WEAPON_STEP_OFFSETS = (0, 0)
HERO_LOOTABLE_WEAPONS = ('WP_MINELAUNCHER', 'WP_GATLING', 'WP_BUZZBLADES', 'WP_BOMBARDIER', 'WP_HOLOSHIELDGLOVE', 'WP_AMOEBOIDLAUNCHER', 'WP_LAVAGUN', 'WP_CRYOSLIDER')

def road_step(reward):
    return (reward['medalCountRequirement'], reward['loot']['type'], reward['loot']['unlockableID'])

def ranger_road_heroes(config, present):
    with edited(config, 'medalrun') as medals:
        road = medals['mainRoad']
        owned = {r['loot']['unlockableID'] for r in road if r['loot']['type'] in (SKIN, HERO_UNLOCK)}
        for skin, count in RANGER_ROAD_HEROES.items():
            if skin not in owned and present.get(skin, True):
                road.append({'medalCountRequirement': count, 'loot': loot(SKIN, unlockable=skin)})
        steps = {road_step(r) for r in road}
        for count, skin, orbs in RANGER_ROAD_ORBS:
            if (count, HERO_LORBS, skin) not in steps and present.get(skin, True):
                road.append({'medalCountRequirement': count, 'loot': loot(HERO_LORBS, orbs, unlockable=skin)})
        road.sort(key=lambda r: r['medalCountRequirement'])
        for reward in medals['medalRoadByCharacterId'][NAKARI_CHARACTER]['Rewards']:
            orbs = NAKARI_MEDAL_ORBS.get(reward['medalCountRequirement'])
            if orbs and reward['loot']['type'] == HERO_LORBS and (reward['loot']['unlockableID'] == NAKARI_SKIN):
                reward['loot']['amount'] = orbs

def nakari_offer(config):
    with edited(config, 'shopdata') as shop:
        offers = shop['shopOffers']
        if not has_offer(offers, NAKARI_OFFER):
            offer = offer_copy(offer_named(offers, 'Cores_1_RSS'), next_offer_id(offers), NAKARI_OFFER, NAKARI_OFFER)
            offer['costData'] = dict(offer['costData'], currencyId=RARITANIUM, cost=NAKARI_PRICE)
            offer['contentLoots'] = [loot(HERO_UNLOCK, unlockable=NAKARI_SKIN)]
            offer['ignoreOfferIfAnyHeroAlreadyOwned'] = [NAKARI_SKIN]
            offers.append(offer)

def ranger_road_weapons(config):
    with edited(config, 'medalrun') as medals:
        road = medals['mainRoad']
        given = {weapon for skin in STARTER_HEROES for weapon in HERO_WEAPONS[skin]}
        steps = {road_step(r) for r in road}
        added = []
        for reward in sorted(road, key=lambda r: r['medalCountRequirement']):
            hero = reward['loot']
            if hero['type'] not in (SKIN, HERO_UNLOCK) or hero['unlockableID'] not in HERO_WEAPONS:
                continue
            for weapon, offset in zip(HERO_WEAPONS[hero['unlockableID']], WEAPON_STEP_OFFSETS):
                if weapon in given:
                    continue
                given.add(weapon)
                count = reward['medalCountRequirement'] + offset
                if (count, WEAPON_UNLOCK, weapon) not in steps:
                    added.append({'medalCountRequirement': count, 'loot': loot(WEAPON_UNLOCK, unlockable=weapon)})
        road.extend(added)
        road.sort(key=lambda r: r['medalCountRequirement'])
    print(f'Ranger Road : {len(added)} armes et gadgets de heros')

def road_steps(config):
    return [(r['medalCountRequirement'], json.dumps(r['loot'], sort_keys=True)) for r in decoded(config, 'medalrun')['mainRoad']]

def road_tags(official, with_heroes, final):
    left_official, left_heroes = (collections.Counter(official), collections.Counter(with_heroes))
    left_heroes.subtract(official)
    tags = []
    for step in final:
        if left_official[step] > 0:
            left_official[step] -= 1
            tags.append('o')
        elif left_heroes[step] > 0:
            left_heroes[step] -= 1
            tags.append('h')
        else:
            tags.append('w')
    return ''.join(tags)

def add_ranger_road(apk, game, config):
    official = road_steps(config)
    ranger_road_heroes(config, {RIVET_SKIN: game.has_model('rivet'), JUYCEE_SKIN: game.has_model('juycee')})
    nakari_offer(config)
    print(f'Ranger Road : {len(RANGER_ROAD_HEROES)} heros, {len(RANGER_ROAD_ORBS)} orbes ; Nakari a {NAKARI_PRICE} Raritanium')
    hero_sheet_price(config)
    with_heroes = road_steps(config)
    ranger_road_weapons(config)
    apk.add(OFFLINE + 'route.txt', road_tags(official, with_heroes, road_steps(config)).encode())

def weapon_sources(config):
    with edited(config, 'raritieseconomydata') as table:
        rarities = table['unlockablesRarities']
        for name in HERO_LOOTABLE_WEAPONS:
            if rarities.get(name, {}).get('source') == LOOTABLE_SOURCE:
                rarities[name]['source'] = MAIN_SOURCE
        for name, _ in OWNERLESS_WEAPONS.values():
            if name in rarities:
                rarities[name]['source'] = LOOTABLE_SOURCE
ADDED_MODE_MEDALS = {BOLT_RUSH_MODE: BOLT_KING_MODE, BOLT_RUSH_SOLO_MODE: BOLT_KING_MODE, BATTLE_ROYALE_MODE: LAST_STAND_MODE}
MEDAL_GAIN_FACTOR = 2
RATCHET_FOR_GOOD_MEDALS = 1000

def added_mode_medal_gains(config):
    with edited(config, 'medalrun') as medals:
        gains = medals['medalRunGainsByGameMode']
        by_mode = {entry['gameModeHash']: entry for entry in gains}
        added = []
        for mode, model in ADDED_MODE_MEDALS.items():
            if mode not in by_mode and model in by_mode:
                gains.append(dict(json_copy(by_mode[model]), gameModeHash=mode))
                added.append(mode)
    print(f'medailles : gains ajoutes pour les modes {added}')

def double_medal_gains(config):
    doubled = 0
    with edited(config, 'medalrun') as medals:
        for mode in medals['medalRunGainsByGameMode']:
            for row in mode['gainMatrix']:
                values = row['values']
                for k, value in enumerate(values):
                    if value > 0:
                        values[k] = value * MEDAL_GAIN_FACTOR
                        doubled += 1
    print(f'medailles : gains x{MEDAL_GAIN_FACTOR} ({doubled} valeurs, pertes inchangees)')

def ratchet_medal_road(config):
    with edited(config, 'medalrun') as medals:
        road = medals['medalRoadByCharacterId'][RATCHET_CHARACTER]['Rewards']
        reward = next((r for r in road if r['medalCountRequirement'] == RATCHET_FOR_GOOD_MEDALS))
        reward['loot'] = loot(HERO_UNLOCK, unlockable=RATCHET_SKIN)
    print(f'Ratchet : lui-meme sur sa ligne de medailles a {RATCHET_FOR_GOOD_MEDALS}')
MOPZ_SKIN = 70

@contextlib.contextmanager
def edited_save_part(parts, name):
    value = msgpack.unpackb(parts[name]['bytes'], raw=False, strict_map_key=False)
    yield value
    parts[name]['bytes'] = msgpack.packb(value, use_bin_type=True)

def give_hidden_heroes(raw):
    save = msgpack.unpackb(raw, raw=False, strict_map_key=False, timestamp=0)
    parts = save['save']
    with edited_save_part(parts, 'UnlockedHeroes') as heroes:
        heroes[0][0].extend(([uid, [0, 1, 0, 0]] for uid in HIDDEN_HEROES.values()))
    with edited_save_part(parts, 'UnlockedSkins') as skins:
        skins[0][0].extend(HIDDEN_HEROES.values())
    with edited_save_part(parts, 'EquippedSkins') as equipped:
        equipped[0][0][0] = MOPZ_SKIN
    with edited_save_part(parts, 'SkinPreferences') as preferences:
        preferences[0] = {hero: hero for hero in preferences[0]}
    with edited_save_part(parts, 'SaveInfo') as info:
        info[4] = HEROES_RELEASE
    save['buildNumber'] = HEROES_BUILD
    save['gcVersionId'] = f'{HEROES_RELEASE}.124:platform/android,build/{HEROES_BUILD}'
    return msgpack.packb(save, use_bin_type=True)
SERVER_ANSWERS = ('login_modele.msgpack', 'reponses.msgpack', 'er.json')

def for_release(vnum, release):
    return release + vnum[len(RELEASE):] if vnum.startswith(RELEASE) else vnum

def edit_config(apk, game, config, release):
    open_hidden_heroes(config, game, release)
    if release == HEROES_RELEASE:
        shop_without_cdn_skins(config)
    else:
        add_modelled_costumes(apk, game)
        add_hero_powers(apk, game)
        if os.environ.get('RR_BOLT_RUSH', '1') == '1':
            add_bolt_rush_mode(config)
            if os.environ.get('RR_EVENEMENTS', '1') == '1':
                add_old_events(config, game)
    if release != RELEASE:
        return
    if game.ready_for_squads():
        allow_squads(config)
    open_gallery(config)
    add_cinematic_heroes(apk, game, config)
    shop_adjustments(config)
    daily_rewards(config)
    headhunter_offer(config)
    add_ranger_road(apk, game, config)
    ownerless_weapon_offers(config)
    qredit_plan_offers(config)
    raritanium_for_qredits(config)
    exchanges_last(config)
    weapon_sources(config)
    added_mode_medal_gains(config)
    double_medal_gains(config)
    ratchet_medal_road(config)

def add_version(apk):
    path = os.environ.get('RR_VERSION_OUTIL') or os.path.join(os.path.dirname(HERE), 'appli_patch', 'version.json')
    if not os.path.isfile(path):
        return
    with open(path, encoding='utf-8') as handle:
        tool = json.load(handle)
    version = {'jeu': tool.get('jeu', tool['version']), 'outil': tool['version'], 'depot': tool['depot']}
    if os.environ.get('RR_MAJ_URL'):
        version['url'] = os.environ['RR_MAJ_URL']
    apk.add(OFFLINE + 'version.json', json.dumps(version).encode())
    print(f"version du jeu : {version['jeu']} (outil {version['outil']})")

def add_offline_data(apk, game, local):
    release = os.environ.get('RR_VERSION', RELEASE)
    data = os.path.join(local, 'donnees')
    with open(os.path.join(data, 'meta.json'), encoding='utf-8') as handle:
        meta = json.load(handle)
    meta['vnum'] = for_release(meta['vnum'], release)
    apk.add(OFFLINE + 'meta.msgpack', msgpack.packb(meta, use_bin_type=True))
    config = msgpack.unpackb(read_file(os.path.join(data, 'config-map.msgpack')), raw=False, strict_map_key=False)
    config['Vnum'] = for_release(config['Vnum'], release)
    edit_config(apk, game, config, release)
    apk.add(OFFLINE + 'config-map.msgpack', msgpack.packb(config, use_bin_type=True))
    for name in SERVER_ANSWERS:
        apk.add(OFFLINE + name, read_file(os.path.join(data, name)))
    save = read_file(os.environ.get('RR_SAUVEGARDE') or os.path.join(local, 'etat', 'save.msgpack'))
    apk.add(OFFLINE + 'save.msgpack', give_hidden_heroes(save) if release == HEROES_RELEASE else save)
    add_version(apk)
    add_gallery(apk, game)

def next_dex_name(names):
    number = 2
    while f'classes{number}.dex' in names:
        number += 1
    return f'classes{number}.dex'

def add_game(apk, base, game, dex):
    for info in base.infolist():
        name = info.filename
        if name.startswith('META-INF/') or name == 'stamp-cert-sha256':
            continue
        source = game.base if name.startswith('assets/bin/Data/') else base
        compress = STORED if name == 'resources.arsc' or name.endswith('.dex') else info.compress_type
        apk.add(name, source.read(name), compress)
    apk.add(next_dex_name(apk.names), read_file(dex))
    for info in game.libs.infolist():
        if info.filename.startswith('lib/'):
            apk.add(info.filename, game.libs.read(info.filename))
    for info in game.pack.infolist():
        if info.filename.startswith('assets/') and info.filename not in apk.names:
            apk.add(info.filename, game.pack.read(info.filename), info.compress_type)

def main(rebuilt, patched, dex, local, out):
    game = PatchedGame(patched)
    try:
        with zipfile.ZipFile(rebuilt) as base:
            apk = ApkWriter(out)
            add_game(apk, base, game, dex)
            add_offline_data(apk, game, local)
            apk.close()
    finally:
        game.close()
    print(f'{len(apk.names)} fichiers, {os.path.getsize(out) / 1048576:.0f} Mo')
if __name__ == '__main__':
    main(*sys.argv[1:6])
