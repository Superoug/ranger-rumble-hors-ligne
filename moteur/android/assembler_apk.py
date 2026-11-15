import hashlib
import json
import os
import sys
import zipfile
import msgpack
import re
import unicodedata
rebuilt, patched, dex, local, out = sys.argv[1:6]
data = os.path.join(local, 'donnees')
state = os.path.join(local, 'etat')
base = zipfile.ZipFile(rebuilt)
patched_base = zipfile.ZipFile(os.path.join(patched, 'com.playstation.rattlesnake.apk'))
libs = zipfile.ZipFile(os.path.join(patched, 'config.arm64_v8a.apk'))
pack = zipfile.ZipFile(os.path.join(patched, 'UnityDataAssetPack.apk'))
seen = set()
STORED = zipfile.ZIP_STORED
if os.environ.get('RR_ALIGNE') == '1':
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'appli_patch'))
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
HIDDEN_HEROES = {'CHANCE': 119, 'MOLLY': 122, 'HELEN': 123, 'FLARE': 209, 'NAKARI': 210, 'TERRY': 211, 'CRUMBY': 227}
BASE_SKINS = {70, 71, 74, 80, 82, 85, 104, 107, 108, 119, 122, 123, 143, 151, 160, 161, 209, 210, 211, 227, 228}
OLD_BUILD = '8571'

def shop_without_cdn_skins(config):
    shop = next((i for i in config['items'] if i['key'] == 'shopdata'))
    table = json.loads(shop['value'])
    for offer in table['shopOffers']:
        if offer['enumName'].startswith('DailySkin'):
            offer['disabled'] = True
    rarities = json.loads(next((i for i in config['items'] if i['key'] == 'raritieseconomydata'))['value'])
    ids = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'skin_ids.json')))
    for name in rarities['unlockablesRarities']:
        uid = ids.get(name)
        if name.startswith('SKIN_') and uid is not None and (uid not in BASE_SKINS) and (uid not in table['skinsForbiddenInShop']):
            table['skinsForbiddenInShop'].append(uid)
    shop['value'] = json.dumps(table, separators=(',', ':'), ensure_ascii=False).encode()
    shop['hash'] = hashlib.md5(shop['value']).hexdigest()[:12]
NEW_SKIN_RARITIES = {'helen_skin01': 'SKIN_HELEN_SKIN01', 'juycee_skin01': 'SKIN_JUYCEE_SKIN01', 'juycee_skin02': 'SKIN_JUYCEE_SKIN02', 'juycee_skin03': 'SKIN_JUYCEE_SKIN03', 'juycee_skin04': 'SKIN_JUYCEE_SKIN04', 'rivet': 'SKIN_RATCHET_SKIN01'}

def skins_with_model():
    found = set()
    for info in pack.infolist():
        match = re.search('skins_character_([a-z]+)_skin(\\d+)_assets_all', info.filename)
        if match:
            found.add(f'{match.group(1).upper()}_SKIN{match.group(2)}')
    return found

def open_hidden_heroes(config, release):
    item = next((i for i in config['items'] if i['key'] == 'raritieseconomydata'))
    table = json.loads(item['value'])
    modelled = skins_with_model() if release != '1.10.3' else set()
    for name, entry in table['unlockablesRarities'].items():
        if name.startswith('SKIN_') and name.split('_')[1] in HIDDEN_HEROES:
            if release == '1.10.3' or name.endswith('_SKIN00') or name[5:].replace('_DEPRECATED', '') in modelled:
                entry['availabilityType'] = 0
            elif release != '1.10.3':
                entry['availabilityType'] = 1
            if release != '1.10.3' and name[5:].replace('_DEPRECATED', '') in modelled:
                entry['source'] = 0
            if release != '1.10.3' and name.endswith('_SKIN00'):
                entry['source'] = 4
                entry['seasonPassIndex'] = -1
    for bundle, skins in NEW_SKIN_RARITIES.items():
        if release != '1.10.3' and any((f'skins_character_{bundle}_assets_all_' in i.filename for i in pack.infolist())):
            for skin in [skins] if isinstance(skins, str) else skins:
                table['unlockablesRarities'][skin] = {'rarity': 2, 'availabilityType': 0, 'source': 0, 'seasonPassIndex': -1}
    table['unlockablesRarities']['WP_SCORPIONFLAIL_DEPRECATED'] = {'rarity': 2, 'availabilityType': 0, 'source': 2, 'seasonPassIndex': -1}
    if release != '1.10.3' and 'WP_WIDGETMELEEGADGET' in table['unlockablesRarities']:
        table['unlockablesRarities']['WP_WIDGETMELEEGADGET'].update(rarity=1, availabilityType=0)
    if release == '1.10.3':
        table['possibleUserSkins'] = [skin for skin in table['possibleUserSkins'] if skin in BASE_SKINS]
    else:
        table['possibleUserSkins'] += [uid for uid in HIDDEN_HEROES.values() if uid not in table['possibleUserSkins']]
    item['value'] = json.dumps(table, separators=(',', ':'), ensure_ascii=False).encode()
    item['hash'] = hashlib.md5(item['value']).hexdigest()[:12]
BOLT_RUSH_MODE = 114
BOLT_KING_MODE = 131
BOLT_RUSH_SOLO_MODE = 68
BATTLE_ROYALE_MODE = 57
LAST_STAND_MODE = 219

def add_bolt_rush_mode(config):
    items = {item['key']: item for item in config['items']}

    def edit(key, change):
        item = items[key]
        value = json.loads(item['value'])
        change(value.get('data', value))
        item['value'] = json.dumps(value, separators=(',', ':'), ensure_ascii=False).encode()
        item['hash'] = hashlib.md5(item['value']).hexdigest()[:12]

    def modes(table):
        listed = table['permanentGameModes']
        if BOLT_RUSH_MODE not in listed:
            listed.insert(listed.index(BOLT_KING_MODE) + 1, BOLT_RUSH_MODE)
        if BOLT_RUSH_SOLO_MODE not in listed:
            listed.insert(listed.index(BOLT_RUSH_MODE) + 1, BOLT_RUSH_SOLO_MODE)
        if BATTLE_ROYALE_MODE not in listed:
            listed.insert(listed.index(LAST_STAND_MODE) + 1, BATTLE_ROYALE_MODE)

    def matchmaking(settings):
        configured = settings['GameModeConfigs']
        for mode in (BOLT_RUSH_MODE, BOLT_RUSH_SOLO_MODE, BATTLE_ROYALE_MODE):
            if not any((entry['gameModeId'] == mode for entry in configured)):
                configured.append({'gameModeId': mode, 'forceOffline': True, 'noBotFill': False})
    edit('gamemodesdata', modes)
    edit('matchmakingconfigdata', matchmaking)
OFFLINE_ONLY_MODES = {159}
OFFLINE_GAME_PATCH = (69183428, bytes.fromhex('1b000014'))
PHOTON_SETTINGS = 'assets/bin/Data/3df92cddd091603488eec50366992dc0'

def ready_for_squads():
    library = libs.read('lib/arm64-v8a/libil2cpp.so')
    offset, patched_code = OFFLINE_GAME_PATCH
    if library[offset:offset + len(patched_code)] != patched_code:
        return False
    settings = pack.read(PHOTON_SETTINGS)
    return b'\t\x00\x00\x00127.0.0.1' in settings

def allow_squads(config):
    item = next((i for i in config['items'] if i['key'] == 'matchmakingconfigdata'))
    value = json.loads(item['value'])
    settings = value.get('data', value)
    for entry in settings['GameModeConfigs']:
        entry['forceOffline'] = entry['gameModeId'] in OFFLINE_ONLY_MODES
    item['value'] = json.dumps(value, separators=(',', ':'), ensure_ascii=False).encode()
    item['hash'] = hashlib.md5(item['value']).hexdigest()[:12]
    shared = sum((1 for entry in settings['GameModeConfigs'] if not entry['forceOffline']))
    print(f'modes jouables en groupe : {shared}')
    item = next((i for i in config['items'] if i['key'] == 'eventseconomydata'))
    table = json.loads(item['value'])
    opened = []
    for event in table['events']:
        info = event.get('additionalInfo') or {}
        if info.get('disableSquad') and info.get('eventGameMode') not in OFFLINE_ONLY_MODES:
            info['disableSquad'] = 0
            opened.append(event['id'])
    if opened:
        item['value'] = json.dumps(table, separators=(',', ':'), ensure_ascii=False).encode()
        item['hash'] = hashlib.md5(item['value']).hexdigest()[:12]
    print(f'evenements ouverts au groupe : {opened}')
GALLERY_URL = 'rrgalerie://artworks'
PICTURES = ('.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp')

def open_gallery(config):
    item = next((i for i in config['items'] if i['key'] == 'urlconfigdata'), None)
    if item is None or not item.get('value'):
        return
    value = json.loads(item['value'])
    value['URLInstagram'] = GALLERY_URL
    item['value'] = json.dumps(value, separators=(',', ':'), ensure_ascii=False).encode()
    item['hash'] = hashlib.md5(item['value']).hexdigest()[:12]
GALLERY_ARROW = 'arrow_02'

def add_gallery_arrow(target):
    import io
    import UnityPy
    for info in pack.infolist():
        if info.filename.split('/')[-1].startswith('ui_atlases_'):
            for o in UnityPy.load(pack.read(info.filename)).objects:
                if o.type.name == 'Sprite' and o.peek_name() == GALLERY_ARROW:
                    out = io.BytesIO()
                    o.read().image.save(out, 'PNG')
                    add(target, 'assets/rr_offline/galerie/fleche.png', out.getvalue(), STORED)
                    return True
    return False

def add_artbook(target):
    folder = os.environ.get('RR_ARTBOOK')
    if not folder or not os.path.isfile(os.path.join(folder, 'artbook.json')):
        return 0
    count = 0
    for root, folders, names in os.walk(folder):
        folders[:] = sorted((f for f in folders if not f.startswith('.')))
        for name in sorted(names):
            if name.startswith('.'):
                continue
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
    for root, folders, names in os.walk(folder):
        folders[:] = sorted((f for f in folders if not f.startswith('.')))
        for name in sorted(names):
            if name.startswith('.') or not name.lower().endswith(PICTURES):
                continue
            if name.lower().startswith('screenshot'):
                continue
            name_in_apk = unicodedata.normalize('NFC', name)
            if name_in_apk in taken:
                continue
            taken.add(name_in_apk)
            data = open(os.path.join(root, name), 'rb').read()
            add(target, f'assets/rr_offline/artworks/{name_in_apk}', data, STORED)
    return len(taken)
ZURKON_EVENT = 1
RANDOM_WEAPON_EVENT = 2
ZURKON_CATEGORY = 1
FREE_FOR_ALL_MODE = 125

def loot(kind, amount=1, currency=0, box=0):
    return {'type': kind, 'amount': amount, 'unlockableID': 0, 'currencyID': currency, 'rarityInfo': 0, 'lootBoxID': box}

def mission(objective, target):
    return {'objective': objective, 'targetProgression': target, 'modifier': {'type': 0, 'metadata': []}}
CREDITS, RARITANIUM, EVENT_TOKENS = (5, 1, 4)
ZURKON_CARDS_PER_MISSION = 5
CURRENCY, LOOT_BOX = (6, 3)
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
    item = next((i for i in config['items'] if i['key'] == 'eventseconomydata'))
    table = json.loads(item['value'])
    if any((e['id'] in (ZURKON_EVENT, RANDOM_WEAPON_EVENT) for e in table['events'])):
        return
    table['events'][:0] = [zurkon_event(), random_weapon_event()]
    table['eventSchedulers'] += [{'eventID': RANDOM_WEAPON_EVENT, 'startDay': 3}]
    mopz = next((info for info in table['nonScheduledEventsInfos'] if info['eventID'] == 3))
    table['nonScheduledEventsInfos'].append({'eventID': ZURKON_EVENT, 'condition': dict(mopz['condition']), 'durationInHours': 72, 'isInfinite': False})
    item['value'] = json.dumps(table, separators=(',', ':'), ensure_ascii=False).encode()
    item['hash'] = hashlib.md5(item['value']).hexdigest()[:12]
RIVET_SKIN, RIVET_CHARACTER, RATCHET_CHARACTER, RATCHET_SKIN = (160, 16, 22, 228)
WENDY_SKIN, WENDY_CHARACTER = (85, 7)
JUYCEE_SKIN, JUYCEE_CHARACTER, CHANCE_CHARACTER, CHANCE_SKIN = (83, 23, 11, 119)
STEELJAW_COSTUMES = ('SKIN_STEELJAW_SKIN01', 'SKIN_STEELJAW_SKIN02', 'SKIN_STEELJAW_SKIN03', 'SKIN_STEELJAW_SKIN04')

def rivet_in_pack():
    return any(('skins_character_rivet_assets_all_' in i.filename for i in pack.infolist()))

def wendy_in_pack():
    return any(('skins_character_wendy_assets_all_' in i.filename for i in pack.infolist()))

def juycee_in_pack():
    return any(('skins_character_juycee_assets_all_' in i.filename for i in pack.infolist()))
WENDY_VISIBLE = os.environ.get('RR_WENDY') == '1'
CORES_PRICE = 500

def shop_adjustments(config):
    item = next((i for i in config['items'] if i['key'] == 'shopdata'))
    shop = json.loads(item['value'])
    hero_orbs = 0
    for offer in shop['shopOffers']:
        if offer['enumName'] == 'Cores_1_RSS':
            offer['costData'] = dict(offer['costData'], currencyId=1, cost=CORES_PRICE)
        if offer['enumName'] == 'Blueprints_ScorpionFlail_100' and (not offer.get('disabled')):
            offer['disabled'] = True
            hero_orbs += 1
        loots = offer.get('contentLoots') or []
        if offer['uniqueID']['_internalPackedID'] >> 16 == 770 and loots and all((loot['type'] == 13 and loot['unlockableID'] for loot in loots)) and (not offer.get('disabled')):
            offer['disabled'] = True
            hero_orbs += 1
    item['value'] = json.dumps(shop, separators=(',', ':'), ensure_ascii=False).encode()
    item['hash'] = hashlib.md5(item['value']).hexdigest()[:12]
    print(f'boutique : Power cores a {CORES_PRICE} Raritanium, {hero_orbs} offres retirees (orbes de heros, plans du fleau)')
GADGET_PLANS_OFFER = 'DailyBlueprints_Gadgets'
GADGET_UNLOCKABLES = {229: 'WP_WIDGETMELEEGADGET', 230: 'WP_ELECTRICGRENADE', 231: 'WP_LILANNMELEEGADGET', 135: 'WP_CRYOSLIDER', 10: 'WP_GLOVEOFDOOM', 3: 'WP_MINELAUNCHER', 129: 'WP_AMOEBOIDLAUNCHER', 6: 'WP_VOIDREPULSER', 69: 'WP_HOVERBOOTS', 116: 'WP_BOMBARDIER', 117: 'WP_HOLOSHIELDGLOVE', 233: 'WP_WRENCHTHROW'}

def gadget_plans_offer(config):
    item = next((i for i in config['items'] if i['key'] == 'shopdata'))
    shop = json.loads(item['value'])
    offers = shop['shopOffers']
    if any((o['enumName'] == GADGET_PLANS_OFFER for o in offers)):
        return
    rarities = json.loads(next((i for i in config['items'] if i['key'] == 'raritieseconomydata'))['value'])
    by_name = {o['enumName']: o for o in offers}
    price = {rarity: by_name[f'DailyBlueprints_R{rarity}']['weightedContentLoots'][0] for rarity in (1, 2, 3)}
    offer = json.loads(json.dumps(by_name['DailyBlueprints_R1']))
    offer['uniqueID']['_internalPackedID'] = max((o['uniqueID']['_internalPackedID'] for o in offers if o['uniqueID']['_internalPackedID'] >> 16 == 770)) + 1
    offer['enumName'] = GADGET_PLANS_OFFER
    entries = []
    for uid, name in GADGET_UNLOCKABLES.items():
        rarity = rarities['unlockablesRarities'][name]['rarity']
        model = price[rarity]
        if model['contentLoots'][0]['type'] != 5 or model['contentLoots'][0]['amount'] != 100:
            raise SystemExit('offre de plans inattendue')
        loot = dict(model['contentLoots'][0], unlockableID=uid, rarityInfo=rarity)
        entries.append({'weight': 1, 'costData': dict(model['costData']), 'contentLoots': [loot]})
    offer['weightedContentLoots'] = entries
    offer['costData'] = dict(entries[0]['costData'])
    offers.append(offer)
    item['value'] = json.dumps(shop, separators=(',', ':'), ensure_ascii=False).encode()
    item['hash'] = hashlib.md5(item['value']).hexdigest()[:12]
    print(f"boutique : plans des gadgets ({len(entries)} gadgets, offre {offer['uniqueID']['_internalPackedID']:#x})")
MEDAL_GAIN_FACTOR = 2

def double_medal_gains(config):
    item = next((i for i in config['items'] if i['key'] == 'medalrun'))
    medals = json.loads(item['value'])
    doubled = 0
    for mode in medals['medalRunGainsByGameMode']:
        for row in mode['gainMatrix']:
            values = row['values']
            for k, value in enumerate(values):
                if value > 0:
                    values[k] = value * MEDAL_GAIN_FACTOR
                    doubled += 1
    item['value'] = json.dumps(medals, separators=(',', ':'), ensure_ascii=False).encode()
    item['hash'] = hashlib.md5(item['value']).hexdigest()[:12]
    print(f'medailles : gains x{MEDAL_GAIN_FACTOR} ({doubled} valeurs, pertes inchangees)')

def open_cinematic_hero(config, character, skin, skin_name, offer_name, model=RATCHET_CHARACTER, model_skin=RATCHET_SKIN, model_skin_name='SKIN_RATCHET_SKIN00', hidden=False):
    items = {i['key']: i for i in config['items']}
    weapons = json.loads(items['characterfavoriteweaponsdata']['value'])
    for name, values in weapons.items():
        if len(values) > model:
            while len(values) <= character:
                values.append(values[model])
            values[character] = values[model]
    rarities = json.loads(items['raritieseconomydata']['value'])
    rarities['unlockablesRarities'][skin_name] = dict(rarities['unlockablesRarities'][model_skin_name])
    if skin not in rarities['possibleUserSkins'] and (not hidden):
        rarities['possibleUserSkins'].append(skin)
    if character == WENDY_CHARACTER:
        for costume in STEELJAW_COSTUMES:
            if costume in rarities['unlockablesRarities']:
                rarities['unlockablesRarities'][costume]['availabilityType'] = 1
    medals = json.loads(items['medalrun']['value'])
    roads = medals['medalRoadByCharacterId']
    road = json.loads(json.dumps(roads[model]))
    for reward in road['Rewards']:
        if reward['loot']['unlockableID'] == model_skin:
            reward['loot']['unlockableID'] = skin
    while len(roads) <= character:
        roads.append({'Rewards': []})
    roads[character] = road
    shop = json.loads(items['shopdata']['value'])
    offers = shop['shopOffers']
    if not hidden and (not any((o['enumName'] == offer_name for o in offers))):
        model = next((o for o in offers if o['enumName'] == 'Lorbs_Chance_300'))
        price = next((o for o in offers if o['enumName'] == 'Lorbs_R1_300'))['costData']
        offer = json.loads(json.dumps(model))
        offer['uniqueID']['_internalPackedID'] = max((o['uniqueID']['_internalPackedID'] for o in offers if o['uniqueID']['_internalPackedID'] >> 16 == 770)) + 1
        offer['enumName'] = offer['title'] = offer_name
        offer['costData'] = dict(price)
        offer['contentLoots'][0]['unlockableID'] = skin
        offers.append(offer)
    for key, value in (('characterfavoriteweaponsdata', weapons), ('raritieseconomydata', rarities), ('medalrun', medals), ('shopdata', shop)):
        items[key]['value'] = json.dumps(value, separators=(',', ':'), ensure_ascii=False).encode()
        items[key]['hash'] = hashlib.md5(items[key]['value']).hexdigest()[:12]

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
target = AlignedZip(out) if AlignedZip else zipfile.ZipFile(out, 'w', allowZip64=True)
for info in base.infolist():
    name = info.filename
    if name.startswith('META-INF/') or name == 'stamp-cert-sha256':
        continue
    source = patched_base if name.startswith('assets/bin/Data/') else base
    compress = STORED if name in ('resources.arsc',) or name.endswith('.dex') else info.compress_type
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
if os.environ.get('RR_COPIE') == '1':
    add(target, 'assets/rr_offline/relais', os.environ.get('RR_RELAIS', '').encode(), STORED)
else:
    release = os.environ.get('RR_VERSION', '1.10.4')

    def for_release(vnum):
        return release + vnum[len('1.10.4'):] if vnum.startswith('1.10.4') else vnum
    meta = json.load(open(os.path.join(data, 'meta.json')))
    meta['vnum'] = for_release(meta['vnum'])
    add(target, 'assets/rr_offline/meta.msgpack', msgpack.packb(meta, use_bin_type=True), STORED)
    config = msgpack.unpackb(open(os.path.join(data, 'config-map.msgpack'), 'rb').read(), raw=False, strict_map_key=False)
    config['Vnum'] = for_release(config['Vnum'])
    open_hidden_heroes(config, release)
    if release != '1.10.3':
        skin_ids = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'skin_ids.json')))
        worn = sorted((skin_ids[key] for name in skins_with_model() if name.split('_')[0] in HIDDEN_HEROES for key in (f'SKIN_{name}', f'SKIN_{name}_DEPRECATED') if key in skin_ids))
        if worn:
            add(target, 'assets/rr_offline/costumes.txt', '\n'.join(map(str, worn)).encode(), STORED)
            print(f'costumes avec modele : {worn}')
    if release == '1.10.3':
        shop_without_cdn_skins(config)
    if release != '1.10.3' and os.environ.get('RR_BOLT_RUSH', '1') == '1':
        add_bolt_rush_mode(config)
        if os.environ.get('RR_EVENEMENTS', '1') == '1':
            add_old_events(config)
    if release == '1.10.4' and ready_for_squads():
        allow_squads(config)
    if release == '1.10.4':
        open_gallery(config)
    if release == '1.10.4' and wendy_in_pack():
        open_cinematic_hero(config, WENDY_CHARACTER, WENDY_SKIN, 'SKIN_STEELJAW_SKIN00', 'Lorbs_Wendy_300', hidden=not WENDY_VISIBLE)
        add(target, 'assets/rr_offline/wendy', b'85', STORED)
        print('Wendy : heroine a part (personnage STEELJAW)' + ('' if WENDY_VISIBLE else ', cachee'))
    if release == '1.10.4' and rivet_in_pack():
        open_cinematic_hero(config, RIVET_CHARACTER, RIVET_SKIN, 'SKIN_AVATAR_SKIN00', 'Lorbs_Rivet_300')
    if release == '1.10.4' and juycee_in_pack():
        open_cinematic_hero(config, JUYCEE_CHARACTER, JUYCEE_SKIN, 'SKIN_JUYCEE_SKIN00', 'Lorbs_Juycee_300', CHANCE_CHARACTER, CHANCE_SKIN, 'SKIN_CHANCE_SKIN00')
        add(target, 'assets/rr_offline/juycee', b'83', STORED)
        print('Juycee : heroine a part (personnage 23)')
        add(target, 'assets/rr_offline/rivet', b'160', STORED)
        print('Rivet : heroine a part (personnage AVATAR)')
    if release == '1.10.4':
        shop_adjustments(config)
        gadget_plans_offer(config)
        double_medal_gains(config)
    add(target, 'assets/rr_offline/config-map.msgpack', msgpack.packb(config, use_bin_type=True), STORED)
    for name in ('login_modele.msgpack', 'reponses.msgpack', 'er.json'):
        add(target, f'assets/rr_offline/{name}', open(os.path.join(data, name), 'rb').read(), STORED)
    save = open(os.environ.get('RR_SAUVEGARDE') or os.path.join(state, 'save.msgpack'), 'rb').read()
    add(target, 'assets/rr_offline/save.msgpack', give_hidden_heroes(save) if release == '1.10.3' else save, STORED)
    version_file = os.environ.get('RR_VERSION_OUTIL') or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'appli_patch', 'version.json')
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
target.close()
print(f'{len(seen)} fichiers, {os.path.getsize(out) / 1048576:.0f} Mo')
