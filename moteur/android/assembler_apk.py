import hashlib
import json
import os
import re
import sys
import unicodedata
import zipfile
import msgpack
HERE = os.path.dirname(os.path.abspath(__file__))
rebuilt, patched, dex, local, out = sys.argv[1:6]
data = os.path.join(local, 'donnees')
state = os.path.join(local, 'etat')
base = zipfile.ZipFile(rebuilt)
patched_base = zipfile.ZipFile(os.path.join(patched, 'com.playstation.rattlesnake.apk'))
libs = zipfile.ZipFile(os.path.join(patched, 'config.arm64_v8a.apk'))
pack = zipfile.ZipFile(os.path.join(patched, 'UnityDataAssetPack.apk'))
PACK_NAMES = pack.namelist()
seen = set()
STORED = zipfile.ZIP_STORED
if os.environ.get('RR_ALIGNE') == '1':
    sys.path.insert(0, os.path.join(HERE, '..', 'appli_patch'))
    from signature import AlignedZip
else:
    AlignedZip = None

def add(target, name, content, compress):
    if name in seen:
        raise SystemExit(f'doublon : {name}')
    seen.add(name)
    if AlignedZip:
        target.add(name, content, compress)
        return
    entry = zipfile.ZipInfo(name, date_time=(1981, 1, 1, 1, 1, 0))
    entry.compress_type = compress
    target.writestr(entry, content)

def config_item(config, key):
    return next((i for i in config['items'] if i['key'] == key))

def store(item, value):
    item['value'] = json.dumps(value, separators=(',', ':'), ensure_ascii=False).encode()
    item['hash'] = hashlib.md5(item['value']).hexdigest()[:12]

def edit_item(config, key, change):
    item = config_item(config, key)
    value = json.loads(item['value'])
    change(value)
    store(item, value)

def json_copy(value):
    return json.loads(json.dumps(value))

def bundle_in_pack(fragment):
    return any((fragment in name for name in PACK_NAMES))

def skin_ids():
    return json.load(open(os.path.join(HERE, 'skin_ids.json')))
HIDDEN_HEROES = {'CHANCE': 119, 'MOLLY': 122, 'HELEN': 123, 'FLARE': 209, 'NAKARI': 210, 'TERRY': 211, 'CRUMBY': 227}
BASE_SKINS = {70, 71, 74, 80, 82, 85, 104, 107, 108, 119, 122, 123, 143, 151, 160, 161, 209, 210, 211, 227, 228}
OLD_BUILD = '8571'

def shop_without_cdn_skins(config):
    shop = config_item(config, 'shopdata')
    table = json.loads(shop['value'])
    for offer in table['shopOffers']:
        if offer['enumName'].startswith('DailySkin'):
            offer['disabled'] = True
    rarities = json.loads(config_item(config, 'raritieseconomydata')['value'])
    ids = skin_ids()
    for name in rarities['unlockablesRarities']:
        uid = ids.get(name)
        if name.startswith('SKIN_') and uid is not None and (uid not in BASE_SKINS) and (uid not in table['skinsForbiddenInShop']):
            table['skinsForbiddenInShop'].append(uid)
    store(shop, table)
NEW_SKIN_RARITIES = {'helen_skin01': 'SKIN_HELEN_SKIN01', 'juycee_skin01': 'SKIN_JUYCEE_SKIN01', 'juycee_skin02': 'SKIN_JUYCEE_SKIN02', 'juycee_skin03': 'SKIN_JUYCEE_SKIN03', 'juycee_skin04': 'SKIN_JUYCEE_SKIN04', 'rivet': 'SKIN_RATCHET_SKIN01'}
_skins_with_model = None

def skins_with_model():
    global _skins_with_model
    if _skins_with_model is None:
        _skins_with_model = set()
        for name in PACK_NAMES:
            match = re.search('skins_character_([a-z]+)_skin(\\d+)_assets_all', name)
            if match:
                _skins_with_model.add(f'{match.group(1).upper()}_SKIN{match.group(2)}')
    return _skins_with_model

def open_hidden_heroes(config, release):
    old = release == '1.10.3'
    item = config_item(config, 'raritieseconomydata')
    table = json.loads(item['value'])
    rarities = table['unlockablesRarities']
    modelled = set() if old else skins_with_model()
    for name, entry in rarities.items():
        if name.startswith('SKIN_') and name.split('_')[1] in HIDDEN_HEROES:
            costume = name[5:].replace('_DEPRECATED', '')
            if old or name.endswith('_SKIN00') or costume in modelled:
                entry['availabilityType'] = 0
            else:
                entry['availabilityType'] = 1
            if old:
                continue
            if costume in modelled:
                entry['source'] = 0
            if name.endswith('_SKIN00'):
                entry['source'] = 4
                entry['seasonPassIndex'] = -1
    if not old:
        for bundle, skin in NEW_SKIN_RARITIES.items():
            if bundle_in_pack(f'skins_character_{bundle}_assets_all_'):
                rarities[skin] = {'rarity': 2, 'availabilityType': 0, 'source': 0, 'seasonPassIndex': -1}
    rarities['WP_SCORPIONFLAIL_DEPRECATED'] = {'rarity': 2, 'availabilityType': 0, 'source': 2, 'seasonPassIndex': -1}
    if not old and 'WP_WIDGETMELEEGADGET' in rarities:
        rarities['WP_WIDGETMELEEGADGET'].update(rarity=1, availabilityType=0)
    if old:
        table['possibleUserSkins'] = [skin for skin in table['possibleUserSkins'] if skin in BASE_SKINS]
    else:
        table['possibleUserSkins'] += [uid for uid in HIDDEN_HEROES.values() if uid not in table['possibleUserSkins']]
    store(item, table)
BOLT_RUSH_MODE = 114
BOLT_KING_MODE = 131
BOLT_RUSH_SOLO_MODE = 68
BATTLE_ROYALE_MODE = 57
LAST_STAND_MODE = 219

def add_bolt_rush_mode(config):

    def modes(value):
        listed = value.get('data', value)['permanentGameModes']
        if BOLT_RUSH_MODE not in listed:
            listed.insert(listed.index(BOLT_KING_MODE) + 1, BOLT_RUSH_MODE)
        if BOLT_RUSH_SOLO_MODE not in listed:
            listed.insert(listed.index(BOLT_RUSH_MODE) + 1, BOLT_RUSH_SOLO_MODE)
        if BATTLE_ROYALE_MODE not in listed:
            listed.insert(listed.index(LAST_STAND_MODE) + 1, BATTLE_ROYALE_MODE)

    def matchmaking(value):
        configured = value.get('data', value)['GameModeConfigs']
        for mode in (BOLT_RUSH_MODE, BOLT_RUSH_SOLO_MODE, BATTLE_ROYALE_MODE):
            if not any((entry['gameModeId'] == mode for entry in configured)):
                configured.append({'gameModeId': mode, 'forceOffline': True, 'noBotFill': False})
    edit_item(config, 'gamemodesdata', modes)
    edit_item(config, 'matchmakingconfigdata', matchmaking)
OFFLINE_ONLY_MODES = {159}
OFFLINE_GAME_PATCH = (69183428, bytes.fromhex('1b000014'))
PHOTON_SETTINGS = 'assets/bin/Data/3df92cddd091603488eec50366992dc0'

def ready_for_squads():
    library = libs.read('lib/arm64-v8a/libil2cpp.so')
    offset, patched_code = OFFLINE_GAME_PATCH
    if library[offset:offset + len(patched_code)] != patched_code:
        return False
    return b'\t\x00\x00\x00127.0.0.1' in pack.read(PHOTON_SETTINGS)

def allow_squads(config):
    item = config_item(config, 'matchmakingconfigdata')
    value = json.loads(item['value'])
    settings = value.get('data', value)
    for entry in settings['GameModeConfigs']:
        entry['forceOffline'] = entry['gameModeId'] in OFFLINE_ONLY_MODES
    store(item, value)
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
GALLERY_ARROW = 'arrow_02'

def open_gallery(config):
    item = next((i for i in config['items'] if i['key'] == 'urlconfigdata'), None)
    if item is None or not item.get('value'):
        return
    value = json.loads(item['value'])
    value['URLInstagram'] = GALLERY_URL
    store(item, value)

def add_gallery_arrow(target):
    import io
    import UnityPy
    for name in PACK_NAMES:
        if name.split('/')[-1].startswith('ui_atlases_'):
            for o in UnityPy.load(pack.read(name)).objects:
                if o.type.name == 'Sprite' and o.peek_name() == GALLERY_ARROW:
                    picture = io.BytesIO()
                    o.read().image.save(picture, 'PNG')
                    add(target, 'assets/rr_offline/galerie/fleche.png', picture.getvalue(), STORED)
                    return True
    return False

def files_under(folder):
    for root, folders, names in os.walk(folder):
        folders[:] = sorted((f for f in folders if not f.startswith('.')))
        for name in sorted(names):
            if not name.startswith('.'):
                yield (root, name)

def add_artbook(target):
    folder = os.environ.get('RR_ARTBOOK')
    if not folder or not os.path.isfile(os.path.join(folder, 'artbook.json')):
        return 0
    count = 0
    for root, name in files_under(folder):
        path = os.path.join(root, name)
        relative = os.path.relpath(path, folder).replace(os.sep, '/')
        add(target, f'assets/rr_offline/artbook/{relative}', open(path, 'rb').read(), STORED)
        count += name.endswith('.webp') and '/v/' not in f'/{relative}'
    return count

def add_artworks(target):
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
        add(target, f'assets/rr_offline/artworks/{name_in_apk}', open(os.path.join(root, name), 'rb').read(), STORED)
    return len(taken)
ZURKON_EVENT = 1
RANDOM_WEAPON_EVENT = 2
ZURKON_CATEGORY = 1
FREE_FOR_ALL_MODE = 125

def loot(kind, amount=1, currency=0, box=0, unlockable=0):
    return {'type': kind, 'amount': amount, 'unlockableID': unlockable, 'currencyID': currency, 'rarityInfo': 0, 'lootBoxID': box}

def mission(objective, target):
    return {'objective': objective, 'targetProgression': target, 'modifier': {'type': 0, 'metadata': []}}
CREDITS, RARITANIUM, EVENT_TOKENS = (5, 1, 4)
ZURKON_CARDS_PER_MISSION = 5
CURRENCY, LOOT_BOX, HERO_UNLOCK, HERO_LORBS = (6, 3, 12, 13)
COMMON_BOX, EPIC_BOX = (2, 4)
ELIMINATE_N_MOBS, ELIMINATE_N_OPPONENTS, WIN_N_BATTLES, BREAK_N_CRATES = (1, 2, 3, 4)
USE_ULTIMATE_N_TIMES, PLAY_N_GAMES, GATHER_BOLTS = (5, 13, 16)

def old_event(event_id, category, **fields):
    event = {'id': event_id, 'category': category, 'activeEvent': 0, 'ticketInfo': {'maxAmount': 0, 'rechargeTime': 0}, 'accessMode': 0, 'modifier': {'modifier': 0, 'value': 0}, 'rewardTrack': {'rewards': [], 'loopMode': 0}, 'onWin': {'rankToWin': 0, 'tokenAmount': 0}, 'dialogueID': 0, 'missions': {'missionsPerDay': []}, 'daysLocalNotificationsPrefix': '', 'nbDaysLocalNotifications': 0, 'excludeWeaponAndHeroLootsFromLootboxesIfActive': 0, 'durationInHours': 24, 'notDisplayedInEventsSelectionScreen': 0, 'delayAfterNotifIncrementMinutes': 0, 'additionalInfo': {'eventConditions': [], 'eventGameMode': 0, 'disablePlayAgain': 0, 'disableSquad': 0, 'showInfoPopupOnlyOnce': 0, 'directlyGoBackToMenuAfterBattle': 0}, 'leaderboardInfo': {'hasLeaderboard': 0, 'needToPreregisterLeaderboard': 0, 'realPlayersMaxCount': 0, 'playersCount': 0, 'rewards': [], 'scoreType': 0, 'menuRefreshDelaySeconds': 0.0}, 'disableNewInstances': 0}
    event.update(fields)
    return event
MONOSCRIPTS_BUNDLE = 'assets/aa/Android/913fdc02988c9f04b9d53c5645e34846_monoscripts_b5e55861ec07d2dfb6815884c7e4041c.bundle'

def collect_screen_in_pack():
    try:
        return b'EventRewardCollectUI' in pack.read(MONOSCRIPTS_BUNDLE)
    except KeyError:
        return False

def zurkon_event():
    collect = collect_screen_in_pack()
    track = [(loot(CURRENCY, 150, RARITANIUM), 15), (loot(LOOT_BOX, box=EPIC_BOX), 25), (loot(CURRENCY, 300, RARITANIUM), 35), (loot(LOOT_BOX, box=EPIC_BOX), 50), (loot(LOOT_BOX, box=EPIC_BOX), 75), (loot(CURRENCY, 25, RARITANIUM), 75 if collect else 100)]
    days = [[mission(BREAK_N_CRATES, 10), mission(PLAY_N_GAMES, 3), mission(ELIMINATE_N_OPPONENTS, 10), mission(GATHER_BOLTS, 300), mission(WIN_N_BATTLES, 2)], [mission(BREAK_N_CRATES, 20), mission(PLAY_N_GAMES, 5), mission(ELIMINATE_N_MOBS, 15), mission(USE_ULTIMATE_N_TIMES, 5), mission(WIN_N_BATTLES, 3)], [mission(BREAK_N_CRATES, 30), mission(PLAY_N_GAMES, 7), mission(ELIMINATE_N_OPPONENTS, 20), mission(GATHER_BOLTS, 600), mission(WIN_N_BATTLES, 4)]]
    rewards = [loot(CURRENCY, ZURKON_CARDS_PER_MISSION, EVENT_TOKENS)] * 5
    return old_event(ZURKON_EVENT, ZURKON_CATEGORY, modifier={'modifier': 1, 'value': 0}, durationInHours=72, rewardTrack={'rewards': [{'lootData': data, 'price': price, 'fastPrice': ''} for data, price in track], 'loopMode': 0}, missions={'missionsPerDay': [] if collect else [{'missions': day, 'rewards': rewards} for day in days]})

def random_weapon_event():
    box = {'lootData': loot(LOOT_BOX, box=COMMON_BOX), 'price': 1, 'fastPrice': ''}
    return old_event(RANDOM_WEAPON_EVENT, 2, activeEvent=1, accessMode=1, modifier={'modifier': 2, 'value': 0}, rewardTrack={'rewards': [box] * 6, 'loopMode': 0}, onWin={'rankToWin': int(os.environ.get('RR_RANG_ARME', '5')), 'tokenAmount': 1}, durationInHours=96, delayAfterNotifIncrementMinutes=180, additionalInfo={'eventConditions': [{'triggerCondition': 0, 'triggerConditionParameter': 0, 'triggerConditionParameterString': ''}], 'eventGameMode': FREE_FOR_ALL_MODE, 'disablePlayAgain': 1, 'disableSquad': 1, 'showInfoPopupOnlyOnce': 1, 'directlyGoBackToMenuAfterBattle': 1}, leaderboardInfo={'hasLeaderboard': 1, 'needToPreregisterLeaderboard': 0, 'realPlayersMaxCount': 2, 'playersCount': 6, 'rewards': [], 'scoreType': 1, 'menuRefreshDelaySeconds': 120.0})

def add_old_events(config):
    item = config_item(config, 'eventseconomydata')
    table = json.loads(item['value'])
    if any((e['id'] in (ZURKON_EVENT, RANDOM_WEAPON_EVENT) for e in table['events'])):
        return
    table['events'][:0] = [zurkon_event(), random_weapon_event()]
    table['eventSchedulers'] += [{'eventID': RANDOM_WEAPON_EVENT, 'startDay': 3}]
    mopz = next((info for info in table['nonScheduledEventsInfos'] if info['eventID'] == 3))
    table['nonScheduledEventsInfos'].append({'eventID': ZURKON_EVENT, 'condition': dict(mopz['condition']), 'durationInHours': 72, 'isInfinite': False})
    store(item, table)
RIVET_SKIN, RIVET_CHARACTER, RATCHET_CHARACTER, RATCHET_SKIN = (160, 16, 22, 228)
WENDY_SKIN, WENDY_CHARACTER = (85, 7)
JUYCEE_SKIN, JUYCEE_CHARACTER, CHANCE_CHARACTER, CHANCE_SKIN = (83, 23, 11, 119)
STEELJAW_COSTUMES = ('SKIN_STEELJAW_SKIN01', 'SKIN_STEELJAW_SKIN02', 'SKIN_STEELJAW_SKIN03', 'SKIN_STEELJAW_SKIN04')
WENDY_VISIBLE = os.environ.get('RR_WENDY') == '1'

def hero_in_pack(name):
    return bundle_in_pack(f'skins_character_{name}_assets_all_')
CORES_PRICE = 100
SHOP_OFFER = 770

def next_offer_id(offers):
    return max((o['uniqueID']['_internalPackedID'] for o in offers if o['uniqueID']['_internalPackedID'] >> 16 == SHOP_OFFER)) + 1
DAILY_RARITANIUM = {3: 15, 7: 25}

def daily_rewards(config):

    def change(value):
        rewards = value['permanentDailyRewards']['allRewards']
        for day, amount in DAILY_RARITANIUM.items():
            reward = rewards[day - 1]
            if (reward['type'], reward['currencyID']) != (CURRENCY, RARITANIUM):
                raise SystemExit(f'recompense du jour {day} : pas du Raritanium')
            reward['amount'] = amount
    edit_item(config, 'dailyrewardsdata', change)

def shop_adjustments(config):
    item = config_item(config, 'shopdata')
    shop = json.loads(item['value'])
    hero_orbs = 0
    for offer in shop['shopOffers']:
        if offer['enumName'] == 'Cores_1_RSS':
            offer['costData'] = dict(offer['costData'], currencyId=1, cost=CORES_PRICE)
        if offer['enumName'] == 'Blueprints_ScorpionFlail_100' and (not offer.get('disabled')):
            offer['disabled'] = True
            hero_orbs += 1
        contents = offer.get('contentLoots') or []
        if offer['uniqueID']['_internalPackedID'] >> 16 == SHOP_OFFER and contents and all((content['type'] == 13 and content['unlockableID'] for content in contents)) and (not offer.get('disabled')):
            offer['disabled'] = True
            hero_orbs += 1
    medals = json.loads(config_item(config, 'medalrun')['value'])
    on_roads = {r['loot']['unlockableID'] for r in medals['mainRoad'] if r['loot']['type'] == SKIN}
    on_roads |= {r['loot']['unlockableID'] for road in medals['medalRoadByCharacterId'] for r in road['Rewards'] if r['loot']['type'] == SKIN}
    freed = [skin for skin in shop['skinsForbiddenInShop'] if skin not in on_roads]
    shop['skinsForbiddenInShop'] = [skin for skin in shop['skinsForbiddenInShop'] if skin in on_roads]
    store(item, shop)
    print(f'boutique : Power cores a {CORES_PRICE} Raritanium, {hero_orbs} offres retirees (orbes de heros, plans du fleau)')
    print(f'boutique : costumes du passe de saison remis dans les offres du jour {freed}')
HEADHUNTER = 11
HEADHUNTER_OFFER = 'Weapon_Headhunter'
WEAPON_UNLOCK = 1

def headhunter_offer(config):
    item = config_item(config, 'shopdata')
    shop = json.loads(item['value'])
    offers = shop['shopOffers']
    if any((o['enumName'] == HEADHUNTER_OFFER for o in offers)):
        return
    costs = json.loads(config_item(config, 'weaponsunlockdata')['value'])['costsByRarity']
    rarity = json.loads(config_item(config, 'raritieseconomydata')['value'])['unlockablesRarities']['WP_HEADHUNTER']['rarity']
    offer = json_copy(next((o for o in offers if o['enumName'] == 'Blueprints_ScorpionFlail_100')))
    offer['uniqueID']['_internalPackedID'] = next_offer_id(offers)
    offer['enumName'] = offer['title'] = HEADHUNTER_OFFER
    offer['disabled'] = True
    offer['costData'] = dict(next((c['costData'] for c in costs if c['rarity'] == rarity)))
    offer['contentLoots'] = [loot(WEAPON_UNLOCK, unlockable=HEADHUNTER)]
    offer['ignoreOfferIfAnyWeaponAlreadyOwned'] = [HEADHUNTER]
    offers.append(offer)
    store(item, shop)
    print(f"boutique : offre Headhunter desactivee (offre {offer['uniqueID']['_internalPackedID']:#x})")
RANGER_ROAD_HEROES = {122: 420, 123: 800, 211: 1250, 227: 2700, 119: 4000, 209: 5600, 83: 6200, 160: 8000}
RANGER_ROAD_ORBS = [(490, 122, 600), (1000, 123, 800), (1800, 211, 600), (3600, 227, 800), (4300, 123, 800), (4500, 119, 800), (5400, 122, 800), (5700, 209, 1000), (6600, 83, 1000), (7000, 209, 1000), (7500, 119, 1000), (7600, 211, 1000), (7900, 227, 1000), (8200, 160, 1000), (9200, 160, 1000)]
NAKARI_SKIN, NAKARI_PRICE, NAKARI_OFFER = (210, 750, 'Hero_Nakari')
NAKARI_CHARACTER, NAKARI_MEDAL_ORBS = (19, {100: 600, 400: 600, 500: 700, 700: 1000, 800: 1000})
HERO_SHEET_PRICE = 750

def hero_sheet_price(config):
    item = config_item(config, 'heroesunlockeconomydata')
    table = json.loads(item['value'])
    for price in table['HeroPricingPerRarity']:
        if price['costData']['currencyId'] != RARITANIUM:
            raise SystemExit('prix des heros : monnaie inattendue')
        price['costData']['cost'] = HERO_SHEET_PRICE
    store(item, table)
    print(f'heros a acheter sur leur fiche : {HERO_SHEET_PRICE} Raritanium')

def ranger_road_heroes(config, present):
    item = config_item(config, 'medalrun')
    medals = json.loads(item['value'])
    road = medals['mainRoad']
    owned = {r['loot']['unlockableID'] for r in road if r['loot']['type'] in (SKIN, HERO_UNLOCK)}
    for skin, count in RANGER_ROAD_HEROES.items():
        if skin not in owned and present.get(skin, True):
            road.append({'medalCountRequirement': count, 'loot': loot(SKIN, unlockable=skin)})
    steps = {(r['medalCountRequirement'], r['loot']['type'], r['loot']['unlockableID']) for r in road}
    for count, skin, orbs in RANGER_ROAD_ORBS:
        if (count, HERO_LORBS, skin) not in steps and present.get(skin, True):
            road.append({'medalCountRequirement': count, 'loot': loot(HERO_LORBS, orbs, unlockable=skin)})
    road.sort(key=lambda r: r['medalCountRequirement'])
    for reward in medals['medalRoadByCharacterId'][NAKARI_CHARACTER]['Rewards']:
        orbs = NAKARI_MEDAL_ORBS.get(reward['medalCountRequirement'])
        if orbs and reward['loot']['type'] == HERO_LORBS and (reward['loot']['unlockableID'] == NAKARI_SKIN):
            reward['loot']['amount'] = orbs
    store(item, medals)
    shop_item = config_item(config, 'shopdata')
    shop = json.loads(shop_item['value'])
    offers = shop['shopOffers']
    if not any((o['enumName'] == NAKARI_OFFER for o in offers)):
        offer = json_copy(next((o for o in offers if o['enumName'] == 'Cores_1_RSS')))
        offer['uniqueID']['_internalPackedID'] = next_offer_id(offers)
        offer['enumName'] = offer['title'] = NAKARI_OFFER
        offer['costData'] = dict(offer['costData'], currencyId=RARITANIUM, cost=NAKARI_PRICE)
        offer['contentLoots'] = [loot(HERO_UNLOCK, unlockable=NAKARI_SKIN)]
        offer['ignoreOfferIfAnyHeroAlreadyOwned'] = [NAKARI_SKIN]
        offers.append(offer)
    store(shop_item, shop)
    print(f'Ranger Road : {len(RANGER_ROAD_HEROES)} heros, {len(RANGER_ROAD_ORBS)} orbes ; Nakari a {NAKARI_PRICE} Raritanium')
SKIN = 2
HERO_WEAPONS = {82: (1, 229), 70: (4, 230), 71: (5, 231), 74: (113, 135), 80: (128, 10), 104: (127, 3), 107: (130, 129), 108: (64, 6), 143: (2, 69), 151: (65, 116), 161: (11, 117), 228: (232, 233), 160: (232, 233)}
HERO_WEAPONS.update({skin: (1, 10) for skin in (119, 122, 123, 209, 210, 211, 227, 83)})
STARTER_HEROES = (82,)
WEAPON_STEP_OFFSETS = (0, 0)
OWNERLESS_WEAPONS = {106: ('WP_ENFORCER', 'Weapon_Enforcer'), 115: ('WP_PLASMASTRIKER', 'Weapon_PlasmaStriker'), 9: ('WP_SCORPIONFLAIL_DEPRECATED', 'Weapon_ScorpionFlail')}
OWNERLESS_PRICE = 250
HERO_LOOTABLE_WEAPONS = ('WP_MINELAUNCHER', 'WP_GATLING', 'WP_BUZZBLADES', 'WP_BOMBARDIER', 'WP_HOLOSHIELDGLOVE', 'WP_AMOEBOIDLAUNCHER', 'WP_LAVAGUN', 'WP_CRYOSLIDER')
MAIN_SOURCE, LOOTABLE_SOURCE = (2, 4)

def ranger_road_weapons(config):
    item = config_item(config, 'medalrun')
    medals = json.loads(item['value'])
    road = medals['mainRoad']
    given = {weapon for skin in STARTER_HEROES for weapon in HERO_WEAPONS[skin]}
    steps = {(r['medalCountRequirement'], r['loot']['type'], r['loot']['unlockableID']) for r in road}
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
    store(item, medals)
    print(f'Ranger Road : {len(added)} armes et gadgets de heros')

def ownerless_weapon_offers(config):
    item = config_item(config, 'shopdata')
    shop = json.loads(item['value'])
    offers = shop['shopOffers']
    costs = json.loads(config_item(config, 'weaponsunlockdata')['value'])['costsByRarity']
    rarities = json.loads(config_item(config, 'raritieseconomydata')['value'])['unlockablesRarities']
    model = next((o for o in offers if o['enumName'] == 'Blueprints_ScorpionFlail_100'))
    for weapon, (name, offer_name) in OWNERLESS_WEAPONS.items():
        if any((o['enumName'] == offer_name for o in offers)):
            continue
        rarity = rarities.get(name, {}).get('rarity')
        cost = next((dict(c['costData']) for c in costs if c['rarity'] == rarity), None)
        offer = json_copy(model)
        offer['uniqueID']['_internalPackedID'] = next_offer_id(offers)
        offer['enumName'] = offer['title'] = offer_name
        offer['disabled'] = False
        offer['costData'] = cost or dict(model['costData'], currencyId=RARITANIUM, cost=OWNERLESS_PRICE)
        offer['contentLoots'] = [loot(WEAPON_UNLOCK, unlockable=weapon)]
        offer['ignoreOfferIfAnyWeaponAlreadyOwned'] = [weapon]
        offers.append(offer)
    store(item, shop)
    print(f'boutique : armes sans heros {sorted(OWNERLESS_WEAPONS)}')
DAILY_OFFER = 513
QREDITS_PER_RARITANIUM = 40
QREDIT_PLAN_OFFERS = ('DailyBlueprints_Qredits1', 'DailyBlueprints_Qredits2')
RARITANIUM_FOR_QREDITS = {25: 1000, 50: 2200, 100: 4800}

def qredit_plan_offers(config):
    item = config_item(config, 'shopdata')
    shop = json.loads(item['value'])
    offers = shop['shopOffers']
    model = next((o for o in offers if o['enumName'] == 'DailyBlueprints_Mix'))
    for name in QREDIT_PLAN_OFFERS:
        if any((o['enumName'] == name for o in offers)):
            continue
        offer = json_copy(model)
        offer['uniqueID']['_internalPackedID'] = max((o['uniqueID']['_internalPackedID'] for o in offers if o['uniqueID']['_internalPackedID'] >> 16 == DAILY_OFFER)) + 1
        offer['enumName'] = name
        for choice in offer['weightedContentLoots']:
            cost = choice['costData']
            choice['costData'] = dict(cost, currencyId=CREDITS, cost=cost['cost'] * QREDITS_PER_RARITANIUM)
        offer['costData'] = offer['weightedContentLoots'][0]['costData']
        offers.append(offer)
    store(item, shop)
    print(f'boutique : 2 offres de plans en Qredits ({QREDITS_PER_RARITANIUM} Qredits le Raritanium)')

def raritanium_for_qredits(config):
    item = config_item(config, 'shopdata')
    shop = json.loads(item['value'])
    offers = shop['shopOffers']
    model = next((o for o in offers if o['enumName'] == 'Credits900'))
    for amount, price in RARITANIUM_FOR_QREDITS.items():
        name = f'Raritanium{amount}_Qredits'
        if any((o['enumName'] == name for o in offers)):
            continue
        offer = json_copy(model)
        offer['uniqueID']['_internalPackedID'] = next_offer_id(offers)
        offer['enumName'] = name
        offer['title'] = f'{amount} Raritanium'
        offer['costData'] = dict(model['costData'], currencyId=CREDITS, cost=price)
        offer['contentLoots'] = [loot(CURRENCY, amount, currency=RARITANIUM)]
        offers.append(offer)
    store(item, shop)
    print(f'boutique : Raritanium contre Qredits {RARITANIUM_FOR_QREDITS}')
EXCHANGE_OFFERS = ('Credits900', 'Credits2000', 'Credits4500') + tuple((f'Raritanium{amount}_Qredits' for amount in RARITANIUM_FOR_QREDITS))

def exchanges_last(config):
    item = config_item(config, 'shopdata')
    shop = json.loads(item['value'])
    offers = shop['shopOffers']
    exchanges = [next((o for o in offers if o['enumName'] == name)) for name in EXCHANGE_OFFERS]
    shop['shopOffers'] = [o for o in offers if o['enumName'] not in EXCHANGE_OFFERS] + exchanges
    store(item, shop)
    print('boutique : echanges Raritanium / Qredits a la fin des ressources')

def road_steps(config):
    return [(r['medalCountRequirement'], json.dumps(r['loot'], sort_keys=True)) for r in json.loads(config_item(config, 'medalrun')['value'])['mainRoad']]

def road_tags(official, with_heroes, final):
    import collections
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

def weapon_sources(config):
    item = config_item(config, 'raritieseconomydata')
    table = json.loads(item['value'])
    rarities = table['unlockablesRarities']
    for name in HERO_LOOTABLE_WEAPONS:
        if rarities.get(name, {}).get('source') == LOOTABLE_SOURCE:
            rarities[name]['source'] = MAIN_SOURCE
    for name, _ in OWNERLESS_WEAPONS.values():
        if name in rarities:
            rarities[name]['source'] = LOOTABLE_SOURCE
    store(item, table)
ADDED_MODE_MEDALS = {BOLT_RUSH_MODE: BOLT_KING_MODE, BOLT_RUSH_SOLO_MODE: BOLT_KING_MODE, BATTLE_ROYALE_MODE: LAST_STAND_MODE}
MEDAL_GAIN_FACTOR = 2
RATCHET_FOR_GOOD_MEDALS = 1000

def added_mode_medal_gains(config):
    item = config_item(config, 'medalrun')
    medals = json.loads(item['value'])
    gains = medals['medalRunGainsByGameMode']
    by_mode = {entry['gameModeHash']: entry for entry in gains}
    added = []
    for mode, model in ADDED_MODE_MEDALS.items():
        if mode not in by_mode and model in by_mode:
            gains.append(dict(json_copy(by_mode[model]), gameModeHash=mode))
            added.append(mode)
    store(item, medals)
    print(f'medailles : gains ajoutes pour les modes {added}')

def double_medal_gains(config):
    item = config_item(config, 'medalrun')
    medals = json.loads(item['value'])
    doubled = 0
    for mode in medals['medalRunGainsByGameMode']:
        for row in mode['gainMatrix']:
            values = row['values']
            for k, value in enumerate(values):
                if value > 0:
                    values[k] = value * MEDAL_GAIN_FACTOR
                    doubled += 1
    store(item, medals)
    print(f'medailles : gains x{MEDAL_GAIN_FACTOR} ({doubled} valeurs, pertes inchangees)')

def ratchet_medal_road(config):
    item = config_item(config, 'medalrun')
    medals = json.loads(item['value'])
    road = medals['medalRoadByCharacterId'][RATCHET_CHARACTER]['Rewards']
    reward = next((r for r in road if r['medalCountRequirement'] == RATCHET_FOR_GOOD_MEDALS))
    reward['loot'] = loot(HERO_UNLOCK, unlockable=RATCHET_SKIN)
    store(item, medals)
    print(f'Ratchet : lui-meme sur sa ligne de medailles a {RATCHET_FOR_GOOD_MEDALS}')

def open_cinematic_hero(config, character, skin, skin_name, offer_name, model=RATCHET_CHARACTER, model_skin=RATCHET_SKIN, model_skin_name='SKIN_RATCHET_SKIN00', hidden=False, sold=False):
    items = {i['key']: i for i in config['items']}
    weapons = json.loads(items['characterfavoriteweaponsdata']['value'])
    for values in weapons.values():
        if len(values) > model:
            while len(values) <= character:
                values.append(values[model])
            values[character] = values[model]
    rarities = json.loads(items['raritieseconomydata']['value'])
    rarities['unlockablesRarities'][skin_name] = dict(rarities['unlockablesRarities'][model_skin_name])
    if sold:
        rarities['unlockablesRarities'][skin_name].update(source=4, seasonPassIndex=-1)
    if skin not in rarities['possibleUserSkins'] and (not hidden):
        rarities['possibleUserSkins'].append(skin)
    if character == WENDY_CHARACTER:
        for costume in STEELJAW_COSTUMES:
            if costume in rarities['unlockablesRarities']:
                rarities['unlockablesRarities'][costume]['availabilityType'] = 1
    medals = json.loads(items['medalrun']['value'])
    roads = medals['medalRoadByCharacterId']
    road = json_copy(roads[model])
    for reward in road['Rewards']:
        if reward['loot']['unlockableID'] == model_skin:
            reward['loot']['unlockableID'] = skin
    while len(roads) <= character:
        roads.append({'Rewards': []})
    roads[character] = road
    shop = json.loads(items['shopdata']['value'])
    offers = shop['shopOffers']
    if not hidden and (not any((o['enumName'] == offer_name for o in offers))):
        orbs = next((o for o in offers if o['enumName'] == 'Lorbs_Chance_300'))
        price = next((o for o in offers if o['enumName'] == 'Lorbs_R1_300'))['costData']
        offer = json_copy(orbs)
        offer['uniqueID']['_internalPackedID'] = next_offer_id(offers)
        offer['enumName'] = offer['title'] = offer_name
        offer['costData'] = dict(price)
        offer['contentLoots'][0]['unlockableID'] = skin
        offers.append(offer)
    for key, value in (('characterfavoriteweaponsdata', weapons), ('raritieseconomydata', rarities), ('medalrun', medals), ('shopdata', shop)):
        store(items[key], value)

def give_hidden_heroes(raw):
    save = msgpack.unpackb(raw, raw=False, strict_map_key=False, timestamp=0)
    parts = save['save']

    def edit(name, change):
        value = msgpack.unpackb(parts[name]['bytes'], raw=False, strict_map_key=False)
        change(value[0][0])
        parts[name]['bytes'] = msgpack.packb(value, use_bin_type=True)
    edit('UnlockedHeroes', lambda heroes: heroes.extend(([uid, [0, 1, 0, 0]] for uid in HIDDEN_HEROES.values())))
    edit('UnlockedSkins', lambda skins: skins.extend(HIDDEN_HEROES.values()))

    def base_skin(equipped):
        equipped[0] = 70
    edit('EquippedSkins', base_skin)
    preferences = msgpack.unpackb(parts['SkinPreferences']['bytes'], raw=False, strict_map_key=False)
    preferences[0] = {hero: hero for hero in preferences[0]}
    parts['SkinPreferences']['bytes'] = msgpack.packb(preferences, use_bin_type=True)
    info = msgpack.unpackb(parts['SaveInfo']['bytes'], raw=False, strict_map_key=False)
    info[4] = '1.10.3'
    parts['SaveInfo']['bytes'] = msgpack.packb(info, use_bin_type=True)
    save['buildNumber'] = OLD_BUILD
    save['gcVersionId'] = f'1.10.3.124:platform/android,build/{OLD_BUILD}'
    return msgpack.packb(save, use_bin_type=True)

def add_offline_data(target):
    release = os.environ.get('RR_VERSION', '1.10.4')
    old = release == '1.10.3'

    def for_release(vnum):
        return release + vnum[len('1.10.4'):] if vnum.startswith('1.10.4') else vnum
    meta = json.load(open(os.path.join(data, 'meta.json')))
    meta['vnum'] = for_release(meta['vnum'])
    add(target, 'assets/rr_offline/meta.msgpack', msgpack.packb(meta, use_bin_type=True), STORED)
    config = msgpack.unpackb(open(os.path.join(data, 'config-map.msgpack'), 'rb').read(), raw=False, strict_map_key=False)
    config['Vnum'] = for_release(config['Vnum'])
    open_hidden_heroes(config, release)
    if old:
        shop_without_cdn_skins(config)
    else:
        ids = skin_ids()
        worn = sorted((ids[key] for name in skins_with_model() if name.split('_')[0] in HIDDEN_HEROES for key in (f'SKIN_{name}', f'SKIN_{name}_DEPRECATED') if key in ids))
        if worn:
            add(target, 'assets/rr_offline/costumes.txt', '\n'.join(map(str, worn)).encode(), STORED)
            print(f'costumes avec modele : {worn}')
        if os.environ.get('RR_BOLT_RUSH', '1') == '1':
            add_bolt_rush_mode(config)
            if os.environ.get('RR_EVENEMENTS', '1') == '1':
                add_old_events(config)
    if release == '1.10.4':
        if ready_for_squads():
            allow_squads(config)
        open_gallery(config)
        if hero_in_pack('wendy'):
            open_cinematic_hero(config, WENDY_CHARACTER, WENDY_SKIN, 'SKIN_STEELJAW_SKIN00', 'Lorbs_Wendy_300', hidden=not WENDY_VISIBLE)
            add(target, 'assets/rr_offline/wendy', b'85', STORED)
            print('Wendy : heroine a part (personnage STEELJAW)' + ('' if WENDY_VISIBLE else ', cachee'))
        if hero_in_pack('rivet'):
            open_cinematic_hero(config, RIVET_CHARACTER, RIVET_SKIN, 'SKIN_AVATAR_SKIN00', 'Lorbs_Rivet_300', sold=True)
        if hero_in_pack('juycee'):
            open_cinematic_hero(config, JUYCEE_CHARACTER, JUYCEE_SKIN, 'SKIN_JUYCEE_SKIN00', 'Lorbs_Juycee_300', CHANCE_CHARACTER, CHANCE_SKIN, 'SKIN_CHANCE_SKIN00')
            print('Juycee : heroine a part (personnage 23)')
            print('Rivet : heroine a part (personnage AVATAR)')
        shop_adjustments(config)
        daily_rewards(config)
        headhunter_offer(config)
        official_road = road_steps(config)
        ranger_road_heroes(config, {RIVET_SKIN: hero_in_pack('rivet'), JUYCEE_SKIN: hero_in_pack('juycee')})
        hero_sheet_price(config)
        road_with_heroes = road_steps(config)
        ranger_road_weapons(config)
        add(target, 'assets/rr_offline/route.txt', road_tags(official_road, road_with_heroes, road_steps(config)).encode(), STORED)
        ownerless_weapon_offers(config)
        qredit_plan_offers(config)
        raritanium_for_qredits(config)
        exchanges_last(config)
        weapon_sources(config)
        added_mode_medal_gains(config)
        double_medal_gains(config)
        ratchet_medal_road(config)
    add(target, 'assets/rr_offline/config-map.msgpack', msgpack.packb(config, use_bin_type=True), STORED)
    for name in ('login_modele.msgpack', 'reponses.msgpack', 'er.json'):
        add(target, f'assets/rr_offline/{name}', open(os.path.join(data, name), 'rb').read(), STORED)
    save = open(os.environ.get('RR_SAUVEGARDE') or os.path.join(state, 'save.msgpack'), 'rb').read()
    add(target, 'assets/rr_offline/save.msgpack', give_hidden_heroes(save) if old else save, STORED)
    version_file = os.environ.get('RR_VERSION_OUTIL') or os.path.join(os.path.dirname(HERE), 'appli_patch', 'version.json')
    if os.path.isfile(version_file):
        tool_version = json.load(open(version_file, encoding='utf-8'))
        game_version = {'jeu': tool_version.get('jeu', tool_version['version']), 'outil': tool_version['version'], 'depot': tool_version['depot']}
        if os.environ.get('RR_MAJ_URL'):
            game_version['url'] = os.environ['RR_MAJ_URL']
        add(target, 'assets/rr_offline/version.json', json.dumps(game_version).encode(), STORED)
        print(f"version du jeu : {game_version['jeu']} (outil {game_version['outil']})")
    book = add_artbook(target)
    pictures = add_artworks(target)
    if book or pictures:
        print(f'galerie : {book or pictures} images' + (' (artbook)' if book else '') + (', fleches du jeu' if add_gallery_arrow(target) else ''))
target = AlignedZip(out) if AlignedZip else zipfile.ZipFile(out, 'w', allowZip64=True)
for info in base.infolist():
    name = info.filename
    if name.startswith('META-INF/') or name == 'stamp-cert-sha256':
        continue
    source = patched_base if name.startswith('assets/bin/Data/') else base
    compress = STORED if name == 'resources.arsc' or name.endswith('.dex') else info.compress_type
    add(target, name, source.read(name), compress)
number = 2
while f'classes{number}.dex' in seen:
    number += 1
add(target, f'classes{number}.dex', open(dex, 'rb').read(), STORED)
for info in libs.infolist():
    if info.filename.startswith('lib/'):
        add(target, info.filename, libs.read(info.filename), STORED)
for info in pack.infolist():
    if info.filename.startswith('assets/') and info.filename not in seen:
        add(target, info.filename, pack.read(info.filename), info.compress_type)
add_offline_data(target)
target.close()
print(f'{len(seen)} fichiers, {os.path.getsize(out) / 1048576:.0f} Mo')
