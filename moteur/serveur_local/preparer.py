import glob
import gzip
import hashlib
import json
import os
import re
import shutil
import sys
import msgpack
WEAPONS_FILE = None

def unpack(raw):
    return msgpack.unpackb(raw, raw=False, strict_map_key=False, timestamp=0)

def pack(value):
    return msgpack.packb(value, use_bin_type=True)

def body(entry, side='res_body'):
    name = entry.get(side)
    if not name:
        return b''
    raw = open(os.path.join(entry['session'], 'corps', name), 'rb').read()
    headers = entry['res_headers'] if side == 'res_body' else entry['req_headers']
    encoding = {k.lower(): v for k, v in headers}.get('content-encoding', '')
    return gzip.decompress(raw) if 'gzip' in encoding else raw
entries = []

def load_captures(capture):
    for index in sorted(glob.glob(capture + '/*/index.jsonl')):
        with open(index, encoding='utf-8') as fh:
            for line in fh:
                entry = json.loads(line)
                entry['session'] = os.path.dirname(index)
                entries.append(entry)

def latest(pattern, method=None, status=200):
    hits = [e for e in entries if re.search(pattern, e['url'].split('?')[0]) and e['status'] == status and (method is None or e['method'] == method) and e.get('res_body')]
    return hits[-1] if hits else None

def emptied(value):
    if isinstance(value, dict):
        return {k: emptied(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return []
    if isinstance(value, str):
        return ''
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return 0
    return None

def force_offline(config_map):
    items = {item['key']: item for item in config_map['items']}
    modes = json.loads(items['gamemodesdata']['value'])
    modes = modes.get('data', modes)
    ids = modes['permanentGameModes'] + modes['allCycleGameModes'] + modes['limitedTimeGameModes']
    item = items['matchmakingconfigdata']
    settings = json.loads(item['value'])
    settings['PingChecksEnabled'] = False
    configured = settings['GameModeConfigs']
    for entry in configured:
        entry['forceOffline'] = True
    present = {entry['gameModeId'] for entry in configured}
    added = sorted(set(ids) - present)
    configured.extend(({'gameModeId': i, 'forceOffline': True, 'noBotFill': False} for i in added))
    item['value'] = json.dumps(settings, separators=(',', ':'), ensure_ascii=False).encode()
    item['hash'] = hashlib.md5(item['value']).hexdigest()[:12]
    print(f'modes hors ligne : {len(configured)} ({len(added)} ajoutes)')
CHARACTERS = {'SANDY': 2, 'RAIDEN': 3, 'LIL_ANN': 4, 'CELESTE': 5, 'CHIP': 6, 'STEELJAW': 7, 'FUSE': 8, 'LUMP': 9, 'MARKUS': 10, 'CHANCE': 11, 'MOLLY': 12, 'HELEN': 13, 'SPROCKET': 14, 'ZEDONE': 15, 'GRIMSHOT': 17, 'FLARE': 18, 'NAKARI': 19, 'TERRY': 20, 'CRUMBY': 21, 'RATCHET': 22}
WEAPONS = {'BLASTER': 1, 'GRENADELAUNCHER': 2, 'MINELAUNCHER': 3, 'GATLING': 4, 'SHOTGUN': 5, 'VOIDREPULSER': 6, 'GLOVEOFDOOM': 10, 'COLDSNAP': 64, 'WARMONGER': 65, 'ENFORCER': 106, 'BUZZBLADES': 113, 'PYROCITOR': 127, 'TESLACLAW': 128, 'LAVAGUN': 130, 'RATCHETBLASTER': 232}
BOT_DIFFICULTY = 100
BOT_POWER = {'Bucket 1': 6000, 'Bucket 2': 9000, 'Bucket 3': 11000, 'Beginner': 6000}
BOT_EXTRA_POWER = {'Weak': 1, 'Normal': 6, 'Strong': 6, 'VeryStrong': 3}

def stronger_bots(config_map):
    item = next((i for i in config_map['items'] if i['key'] == 'matchmakingconfigdata'))
    settings = json.loads(item['value'])
    for bucket in settings['MedalSteps'] + [settings['BeginnerBucket'], settings['FTUEBucket']]:
        bucket['botDifficulty'] = BOT_DIFFICULTY
        power = next((v for k, v in BOT_POWER.items() if bucket['name'].startswith(k)))
        bucket['botPowerStat'] = max(bucket['botPowerStat'], power)
    for name, weight in BOT_EXTRA_POWER.items():
        settings[f'BotExtraPower_{name}']['weight'] = {'RawValue': weight << 16, 'AsLong': weight, 'AsInt': weight, 'AsShort': weight, 'AsFloat': float(weight), 'AsDouble': float(weight)}
    item['value'] = json.dumps(settings, separators=(',', ':'), ensure_ascii=False).encode()
    item['hash'] = hashlib.md5(item['value']).hexdigest()[:12]
    print(f'bots : difficulte {BOT_DIFFICULTY}, puissance {sorted(BOT_POWER.values())}')

def custom_weapons(config_map):
    path = WEAPONS_FILE
    if not path or not os.path.exists(path):
        return
    chosen = json.load(open(path, encoding='utf-8')).get('heros') or {}
    if not chosen:
        return
    item = next((i for i in config_map['items'] if i['key'] == 'characterfavoriteweaponsdata'))
    table = json.loads(item['value'])
    for hero, weapon in chosen.items():
        if hero not in CHARACTERS or weapon not in WEAPONS:
            raise SystemExit(f'armes.json : {hero} / {weapon} inconnu')
        table['defaultWeapons'][CHARACTERS[hero]] = WEAPONS[weapon]
    item['value'] = json.dumps(table, separators=(',', ':')).encode()
    item['hash'] = hashlib.md5(item['value']).hexdigest()[:12]
    print(f'armes personnalisees : {len(chosen)}')

def reopen_arsenal(config_map):
    item = next((i for i in config_map['items'] if i['key'] == 'raritieseconomydata'))
    table = json.loads(item['value'])
    hidden = []
    for name, entry in table['unlockablesRarities'].items():
        if name.startswith('WP_') and entry['rarity'] == 0:
            entry['availabilityType'] = 2
            hidden.append(name)
    item['value'] = json.dumps(table, separators=(',', ':'), ensure_ascii=False).encode()
    item['hash'] = hashlib.md5(item['value']).hexdigest()[:12]
    print(f"armes cachees de l'Arsenal : {hidden}")

def restore_blueprints(config_map):
    item = next((i for i in config_map['items'] if i['key'] == 'lootboxeseconomydata'))
    table = json.loads(item['value'])
    entries = table['lootDataTable']
    twins = {}
    for entry in list(entries):
        if entry['lootData']['type'] != 13:
            continue
        twin = json.loads(json.dumps(entry))
        twin['index'] = len(entries)
        twin['lootData']['type'] = 5
        entries.append(twin)
        twins[entry['index']] = twin['index']
    for box in table['lootBoxesInfoTable']:
        for draw in list(box['allDraws']):
            if draw['lootID'] in twins:
                box['allDraws'].append({**draw, 'lootID': twins[draw['lootID']]})
    item['value'] = json.dumps(table, separators=(',', ':'), ensure_ascii=False).encode()
    item['hash'] = hashlib.md5(item['value']).hexdigest()[:12]
    print(f"plans d'armes remis dans les coffres : {len(twins)}")

def reopen_events(config_map):
    item = next((i for i in config_map['items'] if i['key'] == 'eventseconomydata'))
    table = json.loads(item['value'])
    next((e for e in table['nonScheduledEventsInfos'] if e['eventID'] == 4))['isInfinite'] = True
    next((e for e in table['nonScheduledEventsInfos'] if e['eventID'] == 3))['isInfinite'] = False
    next((e for e in table['events'] if e['id'] == 5))['disableNewInstances'] = False
    item['value'] = json.dumps(table, separators=(',', ':'), ensure_ascii=False).encode()
    item['hash'] = hashlib.md5(item['value']).hexdigest()[:12]

def give_medal_roads(config_map):
    models = {3: (5, 74), 2: (3, 70)}
    heroes = [(11, 119, 3), (12, 122, 2), (13, 123, 2), (18, 209, 3), (19, 210, 3), (20, 211, 3), (21, 227, 3)]
    item = next((i for i in config_map['items'] if i['key'] == 'medalrun'))
    table = json.loads(item['value'])
    roads = table['medalRoadByCharacterId']
    for character, hero, rarity in heroes:
        model_character, model_hero = models[rarity]
        road = json.loads(json.dumps(roads[model_character]))
        for step in road['Rewards']:
            loot = step['loot']
            if loot['unlockableID'] == model_hero:
                loot['unlockableID'] = hero
            elif loot['type'] == 2:
                loot.update(type=6, amount=20, unlockableID=0, currencyID=1)
        roads[character] = road
    item['value'] = json.dumps(table, separators=(',', ':'), ensure_ascii=False).encode()
    item['hash'] = hashlib.md5(item['value']).hexdigest()[:12]

def add_orb_offers(config_map):
    item = next((i for i in config_map['items'] if i['key'] == 'shopdata'))
    table = json.loads(item['value'])
    offers = table['shopOffers']
    models = {3: 'Lorbs_R3_300', 2: 'Lorbs_R2_300'}
    heroes = [('Chance', 119, 3), ('Molly', 122, 2), ('Helen', 123, 2), ('Flare', 209, 3), ('Nakari', 210, 3), ('Terry', 211, 3), ('Crumby', 227, 3)]
    next_id = max((o['uniqueID']['_internalPackedID'] for o in offers if o['enumName'].startswith('Lorbs'))) + 1
    next_id = max(next_id, next((o for o in offers if o['enumName'] == 'Cores_1_RSS'))['uniqueID']['_internalPackedID'] + 1)
    for name, hero, rarity in heroes:
        model = next((o for o in offers if o['enumName'] == models[rarity]))
        offer = json.loads(json.dumps(model))
        offer['uniqueID']['_internalPackedID'] = next_id
        offer['enumName'] = offer['title'] = f'Lorbs_{name}_300'
        offer['condition'] = 0
        offer['contentLoots'][0].update(unlockableID=hero, rarityInfo=0)
        offers.append(offer)
        next_id += 1
    item['value'] = json.dumps(table, separators=(',', ':'), ensure_ascii=False).encode()
    item['hash'] = hashlib.md5(item['value']).hexdigest()[:12]

def add_plan_offers(config_map):
    item = next((i for i in config_map['items'] if i['key'] == 'shopdata'))
    table = json.loads(item['value'])
    offers = table['shopOffers']
    model = next((o for o in offers if o['enumName'] == 'DailyOffer06'))
    next_id = max((o['uniqueID']['_internalPackedID'] for o in offers if o['uniqueID']['_internalPackedID'] >> 16 == 513)) + 1
    for rarity, unit_price in ((1, 5), (2, 10), (3, 15)):
        offer = json.loads(json.dumps(model))
        offer['uniqueID']['_internalPackedID'] = next_id
        offer['enumName'] = f'DailyBlueprints_R{rarity}'
        offer['condition'] = 1
        offer['weightedContentLoots'] = []
        for amount in (100, 200, 300):
            cost = dict(model['costData'], currencyId=1, cost=unit_price * amount // 100)
            loot = {'type': 5, 'amount': amount, 'unlockableID': 0, 'currencyID': 0, 'rarityInfo': rarity, 'lootBoxID': 0}
            offer['weightedContentLoots'].append({'weight': 34, 'costData': cost, 'contentLoots': [loot]})
        offer['costData'] = offer['weightedContentLoots'][0]['costData']
        offers.append(offer)
        next_id += 1
    item['value'] = json.dumps(table, separators=(',', ':'), ensure_ascii=False).encode()
    item['hash'] = hashlib.md5(item['value']).hexdigest()[:12]

def add_mixed_plan_offer(config_map):
    item = next((i for i in config_map['items'] if i['key'] == 'shopdata'))
    table = json.loads(item['value'])
    offers = table['shopOffers']
    if any((o['enumName'] == 'DailyBlueprints_Mix' for o in offers)):
        return
    model = next((o for o in offers if o['enumName'] == 'DailyBlueprints_R1'))
    offer = json.loads(json.dumps(model))
    offer['uniqueID']['_internalPackedID'] = max((o['uniqueID']['_internalPackedID'] for o in offers if o['uniqueID']['_internalPackedID'] >> 16 == 513)) + 1
    offer['enumName'] = 'DailyBlueprints_Mix'
    offer['weightedContentLoots'] = []
    for rarity, amount, unit_price in ((1, 300, 5), (2, 200, 10), (3, 100, 15)):
        cost = dict(model['costData'], currencyId=1, cost=unit_price * amount // 100)
        loot = {'type': 5, 'amount': amount, 'unlockableID': 0, 'currencyID': 0, 'rarityInfo': rarity, 'lootBoxID': 0}
        offer['weightedContentLoots'].append({'weight': 34, 'costData': cost, 'contentLoots': [loot]})
    offer['costData'] = offer['weightedContentLoots'][0]['costData']
    offers.append(offer)
    item['value'] = json.dumps(table, separators=(',', ':'), ensure_ascii=False).encode()
    item['hash'] = hashlib.md5(item['value']).hexdigest()[:12]

def add_flail_plan_offer(config_map):
    item = next((i for i in config_map['items'] if i['key'] == 'shopdata'))
    table = json.loads(item['value'])
    offers = table['shopOffers']
    if any((o['enumName'] == 'Blueprints_ScorpionFlail_100' for o in offers)):
        return
    model = next((o for o in offers if o['enumName'] == 'Lorbs_R2_100'))
    offer = json.loads(json.dumps(model))
    offer['uniqueID']['_internalPackedID'] = max((o['uniqueID']['_internalPackedID'] for o in offers if o['uniqueID']['_internalPackedID'] >> 16 == 770)) + 1
    offer['enumName'] = offer['title'] = 'Blueprints_ScorpionFlail_100'
    offer['condition'] = 0
    offer['costData'] = dict(model['costData'], currencyId=1, cost=10)
    offer['contentLoots'] = [{'type': 5, 'amount': 100, 'unlockableID': 9, 'currencyID': 0, 'rarityInfo': 0, 'lootBoxID': 0}]
    offers.append(offer)
    item['value'] = json.dumps(table, separators=(',', ':'), ensure_ascii=False).encode()
    item['hash'] = hashlib.md5(item['value']).hexdigest()[:12]

def remove_paid_offers(config_map):
    item = next((i for i in config_map['items'] if i['key'] == 'shopdata'))
    table = json.loads(item['value'])
    paid = [offer for offer in table['shopOffers'] if offer['IsInAppPurchase']]
    for offer in paid:
        offer['disabled'] = True
    item['value'] = json.dumps(table, separators=(',', ':'), ensure_ascii=False).encode()
    item['hash'] = hashlib.md5(item['value']).hexdigest()[:12]
    print(f'offres payantes retirees : {len(paid)}')

def build_data(config_raw, vnum, items, login, answers, revenue, user, data_dir):
    os.makedirs(os.path.join(data_dir, 'items'), exist_ok=True)
    config_map = unpack(config_raw)
    force_offline(config_map)
    stronger_bots(config_map)
    custom_weapons(config_map)
    missing = []
    hash_ok = 0
    for item in config_map['items']:
        if item.get('value'):
            continue
        url = item['url'].decode() if isinstance(item['url'], bytes) else item['url']
        name = url.rstrip('/').rsplit('/', 1)[1].split('?')[0]
        if name not in items:
            missing.append(name)
            continue
        content = items[name]
        open(os.path.join(data_dir, 'items', name), 'wb').write(content)
        wanted = item.get('hash') or ''
        digests = [hashlib.md5(content), hashlib.sha1(content), hashlib.sha256(content)]
        hash_ok += any((d.hexdigest().startswith(wanted) for d in digests))
        item['value'] = content
        item['url'] = None
    reopen_arsenal(config_map)
    restore_blueprints(config_map)
    reopen_events(config_map)
    remove_paid_offers(config_map)
    give_medal_roads(config_map)
    add_orb_offers(config_map)
    add_plan_offers(config_map)
    add_mixed_plan_offer(config_map)
    add_flail_plan_offer(config_map)
    open(os.path.join(data_dir, 'config-map.msgpack'), 'wb').write(pack(config_map))
    login = dict(login)
    for key in ('obbToken', 'SessionToken', 'updatedSecret'):
        login[key] = ''
    open(os.path.join(data_dir, 'login_modele.msgpack'), 'wb').write(pack(login))
    responses = {key: answers[key] if key == 'groups' else emptied(answers[key]) for key in ('invites', 'chats', 'friends', 'groups')}
    open(os.path.join(data_dir, 'reponses.msgpack'), 'wb').write(pack(responses))
    open(os.path.join(data_dir, 'er.json'), 'wb').write(revenue)
    json.dump({'vnum': vnum, 'user': user}, open(os.path.join(data_dir, 'meta.json'), 'w'), indent=1)
    print(f"configuration {vnum} : {len(config_map['items'])} elements, {len(items)} fichiers, {len(missing)} manquants")
    print(f'empreintes verifiees : {hash_ok} sur {len(items)}')
    return missing

def main():
    global WEAPONS_FILE
    capture, out, user = sys.argv[1:4]
    reset_save = '--reset-save' in sys.argv
    data_dir = os.path.join(out, 'donnees')
    state_dir = os.path.join(out, 'etat')
    os.makedirs(state_dir, exist_ok=True)
    WEAPONS_FILE = os.path.join(out, 'armes.json')
    load_captures(capture)
    config = latest('/game-config/config-map$', 'POST')
    vnum = {k.lower(): v for k, v in config['res_headers']}.get('obb-client-vnum', '')
    items = {}
    for entry in entries:
        if '/game-config/items/value/' in entry['url'] and entry['status'] == 200:
            items[entry['url'].split('?')[0].rsplit('/', 1)[1]] = body(entry)
    login = next((unpack(body(e)) for e in reversed(entries) if e['url'].endswith('/auth/login') and unpack(body(e)).get('publicId') == user and (not unpack(body(e)).get('networkChoiceRequired'))))
    answers = {}
    for key, pattern in (('invites', '/profiles/[^/]+/invites$'), ('chats', '/profiles/[^/]+/chats$'), ('friends', '/profiles/[^/]+/friends$'), ('groups', '/profiles/[^/]+/groups$')):
        answers[key] = unpack(body(latest(pattern, 'GET')))
    revenue = body(latest('/tools/revenue/er\\.json$', 'GET'))
    build_data(body(config), vnum, items, login, answers, revenue, user, data_dir)
    save_path = os.path.join(state_dir, 'save.msgpack')
    if reset_save or not os.path.exists(save_path):
        save = latest(f'/users/{user}/save$', 'GET')
        open(save_path, 'wb').write(body(save))
        print('sauvegarde de depart copiee')
    else:
        print('sauvegarde existante conservee')
    print('parties de sauvegarde :', len(unpack(open(save_path, 'rb').read())['save']))
if __name__ == '__main__':
    main()
