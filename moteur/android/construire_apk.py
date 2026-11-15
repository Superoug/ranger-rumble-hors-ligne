import io
import json
import os
import re
import struct
import sys
import zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import a64
import evenements
import heros_caches
xapk, out = sys.argv[1:3]
os.makedirs(out, exist_ok=True)
OLD_HOST = b'\x1a\x00\x00\x00rattlesnake-prod.obb.cloud'
NEW_HOST = b'\x1a\x00\x00\x0027.0.0.1:18443/xxxxxxxxxxx'
RETURN_FALSE = bytes.fromhex('00008052c0035fd6')
RETURN_TRUE = bytes.fromhex('20008052c0035fd6')
RETURN_LOCAL_NETWORK = bytes.fromhex('40008052c0035fd6')
RETURN_NOW = bytes.fromhex('c0035fd6')
ZERO_W0 = bytes.fromhex('00008052')
ZERO_W1 = bytes.fromhex('e1031f2a')
ZERO_W2 = bytes.fromhex('e2031f2a')
ARSENAL_NAME = b'\x16\x00\x00\x00FeatureEnabler_Arsenal'
BUILDS = {'1.10.4': {'https': 1049769, 'wss': 1119405, 'play_available': 72762232, 'play_autologin': 72761948, 'reachability': (142385556, 'fe4fbfa9137b00b0'), 'disable_feature': 64584032, 'ensure_weapon': 64583824, 'equip_button': 67155712, 'equip_selected': 67155880, 'try_button': 67156812, 'free_code': (64583828, 'f44f01a9d4cb02d0f30300aa88a6483988010037209e0290007046f9'), 'log_handler': 142824912, 'debug_log': 74693004, 'offline_game': (69183428, '487b02f0', 69183536), 'wander_tries': [(130818588, '1b018052', '1b088052'), (130818700, 'a0040036', '80040036'), (130818744, '40030037', '20030037'), (130818796, 'ad010054', '8d010054'), (130818836, '60000036', '40000036')], 'crc_getter': 140539672, 'crc_local': 140548552, 'crc_web': 140541016, 'crc_web_cached': 140541224, 'show_wip_heroes': None, 'map_pool_check': (66656456, '01fdff54'), 'ratchet_lock': (64500552, '99070037', 64500792), 'training_weapon': (66477052, 'e4179f1a'), 'select_map': 66499712, 'string_new': 63431916, 'prefs_get_string': 142892992, 'free_code_map': (64584036, 'f65701a9f44f02a9d5cb02d0369e02d0f403012aa8aa4839d61e41f9f30300aa88010037209e02b000cc43f91a7cfb97209e02d0002041f9177cfb97209e02d0001c41f9147cfb9728008052a8aa0839c00240f9b67cfb97e1031faa'), 'levels_bundle': 'assets/aa/Android/local_data_managers_assets_all_6ff0f696e005a7c20b7fe29b1123faca.bundle', 'heroes_bundle': 'assets/aa/Android/local_data_managers_assets_all_6ff0f696e005a7c20b7fe29b1123faca.bundle', 'heroes_without_ultimate': [2485100, 2487772, 2488572], 'sandy_ultimate': (29, 2773052598463922984), 'heroes_in_progress': [2484604, 2485408, 2488080, 2499728, 2500528, 2501332, 2503536], 'skins_without_model': [2486008, 2486476, 2486944], 'hero_models': True, 'hero_specs_bundle': 'assets/aa/Android/quantum_db_heroes_assets_all_30f4bf696fe07bd88d3fe14d4cbf42da.bundle', 'hero_specs_table': (147764, 91), 'levels': [(1051184, 0, b'q_FFA_Sargasso_02'), (1053304, 0, b'q_EL_Prototype_01'), (1054064, 0, b'q_EL_TorrenIV_01B'), (1054648, 0, b'q_EL_Ardolis_01B')], 'menu_bundle': 'assets/aa/Android/scene_mainmenu_landscape_scenes_all_8205e1f604aef6bc7603d040c2571063.bundle', 'gallery_label': (20923708, b'\t\x00\x00\x00INSTAGRAM', b'\t\x00\x00\x00 ARTBOOK '), 'arsenal_flag': 9994702, 'flail_tables': [(66168456, 120384924, True), (74993060, 94813676, False), (74996044, 119976552, True)], 'flail_cave': 64584132, 'flail_spec': ('assets/aa/Android/quantum_db_weapons_assets_all_3550076b9943b3b450be7dd2d2396dbf.bundle', 1608828), 'flail_sprites': (1609220, 1609244, 1609268), 'flail_reload': 1609740, 'flail_ammo': 1609780, 'flail_fire_button': 1609516, 'flail_autoshoot': 1609856, 'flail_fire_rate': 1609656, 'flail_projectile_speed': 1309624, 'flail_homing': 1311404, 'flail_anticipation': 1310164, 'flail_spin': (129922376, 72330704), 'flail_view': (66140112, 72330704 + 768), 'flail_auto': (67379356, 66260628, 72330704 + 2048, 72330704 + 5660, 142999140, 240), 'try_fix': (67156092, 67156128, 72330704 + 2560), 'difficulty': (70252920, 70252592), 'ultra_bots': {'talent_store': 129640332, 'runtime_config': 880, 'bots_power': 340}, 'difficulty_row_code': {'get_calls': (66621724, 66621760), 'get': 67818320, 'set_call': 66622004, 'set': 67818556, 'done': 66622256, 'set_string': 142892132, 'save': 142893956}, 'difficulty_row': {'scene': (6513924, 19204924), 'table': (1052044, 100066, 1), 'rows': [{'grid': 70831, 'objects': (399, 1157, 2448, 4259, 4591, 7337, 7727, 8355, 11355, 17241, 24370, 31572, 32005, 37290, 38882, 41623, 45953, 46173, 46762, 46879, 47399, 51201, 51948, 55076, 55434, 56953, 59255, 59402, 65328, 67404, 70347, 70831, 72352, 72593, 73985, 74412, 76459, 76675, 77652, 82191, 82766, 84478, 88904, 89034, 92003, 94372, 94923, 97534, 97572, 98605, 98873, 99520, 99970), 'content': (50699, 8264368, 228, 10), 'options': 98605, 'title': 76675, 'title_text': 73985, 'value': 76459, 'names': {4259: ('FOVGrid', 'DifficultyGrid'), 4591: ('CamFOVSelection', 'DifficultySelection')}}, {'grid': 68819, 'objects': (372, 1728, 2487, 4895, 5219, 7833, 7958, 8244, 10780, 16293, 22249, 29780, 33930, 37679, 40757, 43219, 45570, 46230, 46358, 47675, 47750, 49264, 54262, 54959, 55984, 56008, 57453, 58329, 62987, 66527, 68819, 69499, 72391, 72542, 74054, 74304, 76435, 76654, 79498, 79846, 83964, 85029, 91009, 91252, 92971, 96690, 96915, 97155, 97593, 97972, 98055, 99893, 99940), 'content': (48763, 8022224, 228, 10), 'options': 98055, 'title': 76654, 'title_text': 74054, 'value': 76435, 'names': {4895: ('FOVGrid', 'DifficultyGrid'), 5219: ('CamFOVSelection', 'DifficultySelection')}}]}, 'outline_silhouette': (65782180, '0910221e', '0910241e'), 'flail_blueprint': (67707376, 72330704 + 2688), 'flail_spin_aoe': (1449860, 1449956, 1450012, 1450016), 'flail_enhancements': {'table': (707152, 1850), 'weapon_spec': (5078801867238120315, 850512, 1328), 'mega': (-1977668264896138770, 335280, 352, 1237732778874375369), 'torque': (2311922125797020701, 659936, 340, 613788347279680364), 'spin_pusher': (-7802969303589263528, 153952, 412), 'torque_pusher': (-4648941861449245640, 265120, 356, 2339062322271808208), 'pusher_type': (49, 7505018460637316183), 'limit_scale': 1450064}, 'flail_damage': [(1546884, 1546928), (1633360, 1633404)]}, '1.10.3': {'https': 1050567, 'play_available': 72698364, 'play_autologin': 72698080, 'reachability': (142264064, 'fe4fbfa9137b00f0'), 'disable_feature': 64532484, 'ensure_weapon': 64532276, 'equip_button': 67080908, 'equip_selected': 67086228, 'try_button': 67114288, 'free_code': (64532280, 'f44f01a954cb02d0f30300aa885e713988010037809d02b000f447f9'), 'log_handler': 142702924, 'crc_getter': 140418112, 'crc_local': 140426992, 'crc_web': 140419456, 'crc_web_cached': 140419664, 'show_wip_heroes': 128633152, 'internet_check': (72154980, '00004239c0035fd6'), 'training_weapon': (66429744, 'e4179f1a'), 'heroes_bundle': 'assets/aa/Android/local_data_managers_assets_all_d9364b77f6fa2468ad69bcc67c4d7850.bundle', 'heroes_without_ultimate': [2472544, 2483276, 2486108, 2486940], 'sandy_ultimate': (30, 2773052598463922984), 'menu_bundle': 'assets/aa/Android/scene_mainmenu_landscape_scenes_all_75fdd8147a3f4d8dd07e67cb50f343ac.bundle', 'arsenal_flag': 9707534, 'init_bundle': 'assets/aa/Android/scene_init_scenes_all_0fa6525925f9632ff7f78218fb284673.bundle', 'init_host': 180212, 'flail_tables': [(66117716, 120162504, True), (74870060, 94713444, False), (74873044, 119756860, True)], 'flail_cave': 64532488, 'string_new': 63382176, 'flail_spec': ('assets/aa/Android/quantum_db_weapons_assets_all_364571c451faf8437afda9a6cf9d7419.bundle', 1642300), 'flail_sprites': (1642696, 1642720, 1642744), 'flail_reload': 1643200, 'flail_ammo': 1643240, 'flail_fire_button': 1642976, 'flail_autoshoot': 1643316, 'flail_auto': (None, 66209336, 72276792 + 8, 72276792 + 5660, 142876756, 224), 'flail_damage': [(1580356, 1580400), (1668880, 1668924)], 'flail_spin_spec': 1301860}}
BUILD = BUILDS[os.environ.get('RR_VERSION', '1.10.4')]
COPIE = os.environ.get('RR_COPIE') == '1'
if COPIE:
    os.environ['RR_PHOTON'] = '127.0.0.1'
GROUPE = not COPIE and os.environ.get('RR_GROUPE', '1') == '1' and ('offline_game' in BUILD)
if GROUPE:
    os.environ.setdefault('RR_PHOTON', '127.0.0.1')
if os.environ.get('RR_VERSION') == '1.10.3':
    NEW_HOST = NEW_HOST.replace(b'18443', b'18444')
assert len(OLD_HOST) == len(NEW_HOST)

def at(data, offset, old, new):
    if len(old) != len(new):
        raise SystemExit('longueurs differentes')
    if data[offset:offset + len(old)] != old:
        raise SystemExit(f'octets inattendus a {offset:#x} : {bytes(data[offset:offset + len(old)]).hex()}')
    data[offset:offset + len(new)] = new

def patch_metadata(data):
    at(data, BUILD['https'], b'https://', b'http://1')
    if 'hero_models' in BUILD and (not COPIE):
        for old, new in SKIN_RENAMES:
            if bytes(data).count(old) != 1:
                raise SystemExit(f'nom introuvable : {old}')
            at(data, bytes(data).index(old), old, new.ljust(len(old), b'\x00'))
    if BUILD.get('wss'):
        at(data, BUILD['wss'], b'wss://', b'ws://1')
    if BOLT_RUSH:
        for old, new in BOLT_RUSH_RENAMES:
            if bytes(data).count(old) != 1:
                raise SystemExit(f'nom introuvable : {old}')
            at(data, bytes(data).index(old), old, new.ljust(len(old), b'\x00'))
    if collect_screen_build():
        old, new = (b'Price: 2,99\xef\xbf\xbd', '5 000 Qrédits'.encode())
        if bytes(data).count(old) != 1:
            raise SystemExit("prix de l'ecran de collecte introuvable")
        at(data, bytes(data).index(old), old, new)

def patch_player_settings(data):
    at(data, 47624, struct.pack('<I', 0), struct.pack('<I', 2))

def patch_host(data):
    if data.count(OLD_HOST) != 1:
        raise SystemExit('hote introuvable')
    start = data.find(OLD_HOST)
    data[start:start + len(NEW_HOST)] = NEW_HOST

def patch_code(data):
    at(data, BUILD['play_available'], bytes.fromhex('fe0f1ef8f44f01a9'), RETURN_FALSE)
    at(data, BUILD['play_autologin'], bytes.fromhex('fe57bea9f44f01a9'), RETURN_FALSE)
    offset, original = BUILD['reachability']
    at(data, offset, bytes.fromhex(original), RETURN_LOCAL_NETWORK)
    at(data, BUILD['disable_feature'], bytes.fromhex('fe0f1df8'), RETURN_NOW)
    at(data, BUILD['ensure_weapon'], bytes.fromhex('fe0f1ef8'), RETURN_NOW)
    jump = BUILD['equip_selected'] - (BUILD['equip_button'] + 8) >> 2
    at(data, BUILD['equip_button'], bytes.fromhex('00a840f9e00000b4080040f9'), bytes.fromhex('e1031f2ae2031faa') + struct.pack('<I', 335544320 | jump))
    cave, original = BUILD['free_code']
    start = BUILD['try_button']

    def branch(opcode, source, target):
        return struct.pack('<I', opcode | target - source >> 2 & 67108863)
    at(data, cave, bytes.fromhex(original), bytes.fromhex('e07bbfa9') + bytes.fromhex('e1031f2a') + bytes.fromhex('e2031faa') + branch(2483027968, cave + 12, BUILD['equip_selected']) + bytes.fromhex('e07bc1a8') + bytes.fromhex('ff0301d1') + branch(335544320, cave + 24, start + 4))
    at(data, start, bytes.fromhex('ff0301d1'), branch(335544320, start, cave))
    if 'map_pool_check' in BUILD:
        offset, original = BUILD['map_pool_check']
        at(data, offset, bytes.fromhex(original), bytes.fromhex('1f2003d5'))
    if 'training_weapon' in BUILD:
        offset, original = BUILD['training_weapon']
        at(data, offset, bytes.fromhex(original), bytes.fromhex('e4031f2a'))
    if 'ratchet_lock' in BUILD:
        offset, original, skip = BUILD['ratchet_lock']
        at(data, offset, bytes.fromhex(original), a64.b(offset, skip))
        print("Ratchet : le jeu ne le retire plus seul en fin d'evenement")
    if 'select_map' in BUILD:
        cave, original = BUILD['free_code_map']
        start = BUILD['select_map']
        mode = BOLT_RUSH_SWITCH if BOLT_RUSH else None
        hook = bytes.fromhex('ffc300d1') + bytes.fromhex('e00700a9') + bytes.fromhex('e20f01a9') + bytes.fromhex('fe1300f9') + bytes.fromhex('610000b4') + bytes.fromhex('281040b9') + (bytes.fromhex('48010035') if mode else bytes.fromhex('28010035')) + (bytes.fromhex('e0010010') if mode else bytes.fromhex('c0010010')) + branch(2483027968, cave + 32, BUILD['string_new']) + bytes.fromhex('e1031faa') + branch(2483027968, cave + 40, BUILD['prefs_get_string']) + bytes.fromhex('800000b4') + bytes.fromhex('081040b9') + bytes.fromhex('48000034') + bytes.fromhex('e00700f9') + (branch(2483027968, cave + 60, mode) if mode else b'') + bytes.fromhex('e00740a9') + bytes.fromhex('e20f41a9') + bytes.fromhex('fe1340f9') + bytes.fromhex('ffc30091') + bytes.fromhex('ffc302d1')
        hook += branch(335544320, cave + len(hook), start + 4) + b'rr_map\x00\x00'
        if not mode and hook[:len(bytes.fromhex(original))] != hook:
            pass
        at(data, cave, bytes(data[cave:cave + len(hook)]) if mode else bytes.fromhex(original), hook)
        at(data, start, bytes.fromhex('ffc302d1'), branch(335544320, start, cave))
    if 'internet_check' in BUILD:
        offset, original = BUILD['internet_check']
        at(data, offset, bytes.fromhex(original), RETURN_TRUE)
    if BUILD['show_wip_heroes']:
        at(data, BUILD['show_wip_heroes'], bytes.fromhex('e0031f2ac0035fd6'), RETURN_TRUE)
    if os.environ.get('RR_JOURNAL'):
        at(data, BUILD['log_handler'], bytes.fromhex('010c01f8'), RETURN_NOW)
        if BUILD.get('debug_log'):
            at(data, BUILD['debug_log'], bytes.fromhex('48070034'), bytes.fromhex('1f2003d5'))
    if GROUPE:
        offset, original, target = BUILD['offline_game']
        at(data, offset, bytes.fromhex(original), branch(335544320, offset, target))
        for offset, original, fixed in BUILD['wander_tries']:
            at(data, offset, bytes.fromhex(original), bytes.fromhex(fixed))
    at(data, BUILD['crc_getter'], bytes.fromhex('001840b9'), ZERO_W0)
    at(data, BUILD['crc_local'], bytes.fromhex('011940b9'), ZERO_W1)
    at(data, BUILD['crc_web'], bytes.fromhex('011940b9'), ZERO_W1)
    at(data, BUILD['crc_web_cached'], bytes.fromhex('021940b9'), ZERO_W2)

def lz4_decompress(source, size):
    out = bytearray()
    i = 0
    while True:
        token = source[i]
        i += 1
        count = token >> 4
        if count == 15:
            while True:
                extra = source[i]
                i += 1
                count += extra
                if extra != 255:
                    break
        out += source[i:i + count]
        i += count
        if i >= len(source):
            break
        distance = source[i] | source[i + 1] << 8
        i += 2
        count = token & 15
        if count == 15:
            while True:
                extra = source[i]
                i += 1
                count += extra
                if extra != 255:
                    break
        for _ in range(count + 4):
            out.append(out[-distance])
    if len(out) != size:
        raise SystemExit('bloc LZ4 de taille inattendue')
    return out

def bundle_layout(source):
    position = source.index(b'\x00') + 1 + 4
    position = source.index(b'\x00', position) + 1
    position = source.index(b'\x00', position) + 1
    header_end = position
    _, packed_size, info_size, flags = struct.unpack('>qIII', source[position:position + 20])
    if flags & 63 != 3 or flags & 128 or (not flags & 512):
        raise SystemExit('format de paquet inattendu')
    info_start = position + 20 + 15 & ~15
    info = lz4_decompress(source[info_start:info_start + packed_size], info_size)
    count, = struct.unpack('>i', info[16:20])
    start = info_start + packed_size + 15 & ~15
    return (header_end, packed_size, flags, info_start, info, count, start)

def bundle_stream(source):
    _, _, _, _, info, count, start = bundle_layout(source)
    stream = bytearray()
    for index in range(count):
        plain, packed, block_flags = struct.unpack('>IIH', info[20 + index * 10:30 + index * 10])
        piece = source[start:start + packed]
        start += packed
        stream += lz4_decompress(piece, plain) if block_flags & 63 else piece
    return bytes(stream)

def replace_bundle_stream(data, stream, grown=0, node=0):
    source = bytes(data)
    header_end, _, flags, info_start, info, count, _ = bundle_layout(source)
    block_flags = struct.unpack('>H', info[28:30])[0] & ~63
    nodes = info[20 + count * 10:]
    node_count, = struct.unpack('>i', nodes[:4])
    if node_count != 1 and (not grown):
        raise SystemExit('paquet a plusieurs fichiers')
    blocks = [stream[i:i + BUNDLE_BLOCK] for i in range(0, len(stream), BUNDLE_BLOCK)]
    new_info = bytes(info[:16]) + struct.pack('>i', len(blocks))
    new_info += b''.join((struct.pack('>IIH', len(b), len(b), block_flags) for b in blocks))
    new_nodes = bytearray(nodes[:4])
    position = 4
    for index in range(node_count):
        offset, size, node_flags = struct.unpack('>qqI', nodes[position:position + 20])
        end = nodes.index(b'\x00', position + 20) + 1
        if node_count == 1:
            size = len(stream)
        elif offset == node:
            size += grown
        elif offset > node:
            offset += grown
        new_nodes += struct.pack('>qqI', offset, size, node_flags) + nodes[position + 20:end]
        position = end
    new_info += bytes(new_nodes) + bytes(nodes[position:])
    data_start = info_start + len(new_info) + 15 & ~15
    total = data_start + len(stream)
    head = source[:header_end] + struct.pack('>qIII', total, len(new_info), len(new_info), flags & ~63)
    head = head.ljust(info_start, b'\x00') + new_info
    data[:] = head.ljust(data_start, b'\x00') + bytes(stream)

def patch_bundle(data, edits):
    source = bytes(data)
    header_end, packed_size, flags, info_start, info, count, start = bundle_layout(source)
    stream = 0
    pieces = []
    for index in range(count):
        entry = 20 + index * 10
        plain, packed, block_flags = struct.unpack('>IIH', info[entry:entry + 10])
        piece = source[start:start + packed]
        start += packed
        here = [edit for edit in edits if stream <= edit[0] < stream + plain]
        if here:
            block = lz4_decompress(piece, plain)
            for offset, old, new in here:
                at(block, offset - stream, old, new)
            piece = bytes(block)
            info[entry:entry + 10] = struct.pack('>IIH', plain, plain, block_flags & ~63)
        pieces.append(piece)
        stream += plain
    if start != len(source):
        raise SystemExit('paquet mal lu')
    data_start = info_start + len(info) + 15 & ~15
    total = data_start + sum((len(piece) for piece in pieces))
    head = source[:header_end] + struct.pack('>qIII', total, len(info), len(info), flags & ~63)
    head = head.ljust(info_start, b'\x00') + bytes(info)
    data[:] = head.ljust(data_start, b'\x00') + b''.join(pieces)
_HEAVY = []

def heavy_tools():
    if not _HEAVY:
        try:
            import numpy
            import PIL
            import UnityPy
            _HEAVY.append(True)
        except ImportError:
            _HEAVY.append(False)
            print("UnityPy, numpy ou Pillow absent : retouches d'images et de modèles laissées de côté")
    return _HEAVY[0]

def artbook_menu(scene):
    try:
        import menu_artbook
    except ImportError:
        menu_artbook = None
    if menu_artbook is None or not heavy_tools():
        print('menu : ARTBOOK reste dans Social media')
        return scene
    return menu_artbook.artbook_menu(scene)

def patch_main_menu(data):
    arsenal = (BUILD['arsenal_flag'] - 30, ARSENAL_NAME + bytes(5), ARSENAL_NAME + bytes(4) + b'\x01')
    edits = [arsenal] + ([BUILD['gallery_label']] if 'gallery_label' in BUILD else [])
    if weapon_slots_build():
        edits += weapon_slots_flag_edits()
    if 'difficulty_row' not in BUILD:
        patch_bundle(data, edits)
        return
    stream = bytearray(bundle_stream(bytes(data)))
    for edit in edits:
        at(stream, *edit)
    start, size = BUILD['difficulty_row']['scene']
    scene = difficulty_row(bytearray(stream[start:start + size]))
    if collect_screen_build():
        graft = collect_graft()
        scene = bytearray(graft.graft(scene))
        if 'gallery_label' in BUILD:
            scene = bytearray(artbook_menu(scene))
        sizes = bundle_node_sizes(data)
        if len(sizes) != 3 or sum(sizes[:2]) != start or sizes[2] != size:
            raise SystemExit('paquet du menu inattendu')
        shared = graft.patch_preload(stream[:sizes[0]])
        stream = bytearray(shared) + stream[sizes[0]:start] + scene + stream[start + size:]
        replace_bundle_nodes(data, stream, [len(shared), sizes[1], len(scene)])
        return
    if 'gallery_label' in BUILD:
        scene = bytearray(artbook_menu(scene))
    stream[start:start + size] = scene
    replace_bundle_stream(data, stream, len(scene) - size, node=start)

def bundle_node_sizes(data):
    _, _, _, _, info, count, _ = bundle_layout(bytes(data))
    nodes = info[20 + count * 10:]
    node_count, = struct.unpack('>i', nodes[:4])
    position, sizes, expected = (4, [], 0)
    for _ in range(node_count):
        offset, size, _ = struct.unpack('>qqI', nodes[position:position + 20])
        if offset != expected:
            raise SystemExit('fichiers du paquet non contigus')
        sizes.append(size)
        expected += size
        position = nodes.index(b'\x00', position + 20) + 1
    return sizes

def replace_bundle_nodes(data, stream, sizes):
    source = bytes(data)
    header_end, _, flags, info_start, info, count, _ = bundle_layout(source)
    block_flags = struct.unpack('>H', info[28:30])[0] & ~63
    nodes = info[20 + count * 10:]
    node_count, = struct.unpack('>i', nodes[:4])
    if node_count != len(sizes) or sum(sizes) != len(stream):
        raise SystemExit('tailles de fichiers du paquet incoherentes')
    blocks = [stream[i:i + BUNDLE_BLOCK] for i in range(0, len(stream), BUNDLE_BLOCK)]
    new_info = bytes(info[:16]) + struct.pack('>i', len(blocks))
    new_info += b''.join((struct.pack('>IIH', len(b), len(b), block_flags) for b in blocks))
    new_nodes = bytearray(nodes[:4])
    position, offset = (4, 0)
    for size in sizes:
        _, _, node_flags = struct.unpack('>qqI', nodes[position:position + 20])
        end = nodes.index(b'\x00', position + 20) + 1
        new_nodes += struct.pack('>qqI', offset, size, node_flags) + nodes[position + 20:end]
        offset += size
        position = end
    new_info += bytes(new_nodes) + bytes(nodes[position:])
    data_start = info_start + len(new_info) + 15 & ~15
    total = data_start + len(stream)
    head = source[:header_end] + struct.pack('>qIII', total, len(new_info), len(new_info), flags & ~63)
    head = head.ljust(info_start, b'\x00') + new_info
    data[:] = head.ljust(data_start, b'\x00') + bytes(stream)
DIFFICULTY_ROW_TITLE = 'RR.SETTINGS.DIFFICULTY'
DIFFICULTY_ROW_KEYS = ('RR.DIFFICULTY.EASY', 'RR.DIFFICULTY.NORMAL', 'RR.DIFFICULTY.HARD', 'RR.DIFFICULTY.ULTRA')
DIFFICULTY_TEXTS = {'EN': ('Difficulty', 'Easy', 'Normal', 'Hard', 'Ultra hard'), 'FR': ('Difficulté', 'Facile', 'Normal', 'Difficile', 'Ultra difficile'), 'DE': ('Schwierigkeit', 'Leicht', 'Normal', 'Schwer', 'Ultraschwer'), 'ES': ('Dificultad', 'Fácil', 'Normal', 'Difícil', 'Ultradifícil'), 'IT': ('Difficoltà', 'Facile', 'Normale', 'Difficile', 'Ultra difficile'), 'BR': ('Dificuldade', 'Fácil', 'Normal', 'Difícil', 'Ultradifícil'), 'NL': ('Moeilijkheid', 'Makkelijk', 'Normaal', 'Moeilijk', 'Ultramoeilijk'), 'RU': ('Сложность', 'Легко', 'Нормально', 'Сложно', 'Ультрасложно'), 'TR': ('Zorluk', 'Kolay', 'Normal', 'Zor', 'Çok zor'), 'JP': ('難易度', 'かんたん', 'ふつう', 'むずかしい', 'ちょうむずかしい'), 'KR': ('난이도', '쉬움', '보통', '어려움', '매우 어려움'), 'CN': ('难度', '简单', '普通', '困难', '极难'), 'TW': ('難度', '簡單', '普通', '困難', '極難')}

def difficulty_texts(language):
    title, *levels = DIFFICULTY_TEXTS.get(language) or DIFFICULTY_TEXTS['EN']
    return {DIFFICULTY_ROW_TITLE: title, **dict(zip(DIFFICULTY_ROW_KEYS, levels))}

def difficulty_row(scene):
    table, count, padding = BUILD['difficulty_row']['table']
    if struct.unpack_from('>I', scene, 20)[0] + 48 <= table or struct.unpack_from('<q', scene, table + (count - 1) * 24)[0] != count:
        raise SystemExit('scene du menu inattendue')
    rows = BUILD['difficulty_row']['rows']
    olds = sorted((old for row in rows for old in row['objects']))
    if len(set(olds)) != len(olds):
        raise SystemExit('reglages de difficulte en double')
    new_ids = {old: count + 1 + index for index, old in enumerate(olds)}
    grows, edits = ({}, {})
    for row in rows:
        content, content_start, content_size, children = row['content']

        def add_child(old, children=children, grid=row['grid']):
            end = 56 + children * 12
            if struct.unpack_from('<i', old, 52)[0] != children or struct.unpack_from('<iq', old, end - 12) != (0, grid):
                raise SystemExit('liste des reglages inattendue')
            return old[:52] + struct.pack('<i', children + 1) + old[56:end] + struct.pack('<iq', 0, new_ids[grid]) + old[end:]
        grows[content] = (content_start, content_size, add_child)
        edits.update({row['options']: [(struct.pack('<I', 2) + raw_text('UI.SETTINGS.CAMFOV.NARROW') + raw_text('UI.SETTINGS.CAMFOV.WIDE'), struct.pack('<I', len(DIFFICULTY_ROW_KEYS)) + b''.join((raw_text(key) for key in DIFFICULTY_ROW_KEYS)))], row['title']: [(raw_text('UI.SETTINGS.CAMFOV_MODE'), raw_text(DIFFICULTY_ROW_TITLE))], row['title_text']: [(unity_string('Field of View'), unity_string(DIFFICULTY_TEXTS['EN'][0]))], row['value']: [(raw_text('UI.SETTINGS.CAMFOV.NARROW'), raw_text(DIFFICULTY_ROW_KEYS[1]))], **{object_id: [(unity_string(old), unity_string(new))] for object_id, (old, new) in row['names'].items()}})

    def copy(old_id):

        def change(raw):
            raw = bytearray(raw)
            for offset in range(0, len(raw) - 11, 4):
                file_id, path_id = struct.unpack_from('<iq', raw, offset)
                if file_id == 0 and path_id in new_ids:
                    struct.pack_into('<iq', raw, offset, 0, new_ids[path_id])
            raw = bytes(raw)
            for old, new in edits.get(old_id, ()):
                if raw.count(old) != 1:
                    raise SystemExit(f'objet {old_id} du reglage inattendu')
                raw = raw.replace(old, new)
            return raw
        return change
    grow_objects(scene, table, count, grows)
    scene, _ = add_object_copies(scene, table, count, {new_ids[old]: (old, copy(old)) for old in olds}, padding)
    return scene

def level_edits():
    edits = []
    for offset, status, name in BUILD.get('levels', []):
        size = struct.pack('<I', len(name)) + name
        edits.append((offset, struct.pack('<I', status) + size, struct.pack('<I', 2) + size))
    return edits

def hero_edits():
    empty = struct.pack('<iiq', 1, 0, 0)
    sandy = struct.pack('<iiq', 1, *BUILD['sandy_ultimate'])
    edits = [(offset, empty, sandy) for offset in BUILD.get('heroes_without_ultimate', [])]
    edits += [(offset, b'\x01', b'\x00') for offset in BUILD.get('heroes_in_progress', [])]
    modelled = cdn_skins_present()
    edits += [(offset, struct.pack('<i', 0), struct.pack('<i', 1)) for offset, skin in zip(BUILD.get('skins_without_model', []), ('Molly_Skin01', 'Molly_Skin02', 'Molly_Skin03')) if skin not in modelled]
    return edits

def model_reference_edits(stream, skins=None, heroes=True):
    edits = []
    targets = [(b'ico_miniPortrait_' + hero.encode(), hero, guid) for hero, guid in HERO_MODELS.items()] if heroes else []
    targets += skins or []
    for anchor, hero, guid in targets:
        portrait = stream.index(anchor)
        logo = stream.index(b'Logo_' + hero.encode(), portrait)
        position = logo + len(b'Logo_') + len(hero) + 3 & ~3
        size, = struct.unpack_from('<I', stream, position)
        end = position + 4 + size + 3 & ~3
        old = stream[position:end + 8]
        short_type = SPRITE_TYPE.ljust((size + 3 & ~3) - len(guid))
        new = struct.pack('<I', len(short_type)) + short_type.encode() + stream[end:end + 4]
        new += struct.pack('<I', len(guid)) + guid.encode()
        if old[-4:] != bytes(4) or len(new) != len(old):
            raise SystemExit(f'fiche inattendue : {hero}')
        cut = min(len(old), BUNDLE_BLOCK - position % BUNDLE_BLOCK)
        edits.append((position, old[:cut], new[:cut]))
        if cut < len(old):
            edits.append((position + cut, old[cut:], new[cut:]))
    return edits
NEW_SKIN_RECORDS = [('Helen_Skin01', 'HELEN', 'Skin01', 'SKIN_HELEN_SKIN01', 164, 'SKIN.HELEN_01', 'Helen_01'), ('Juycee', 'JUYCEE', 'Skin00', 'SKIN_JUYCEE_SKIN00', 83, 'SKIN.JUYCEE_00', 'Chance_01'), ('Juycee_Skin01', 'JUYCEE', 'Skin01', 'SKIN_JUYCEE_SKIN01', 84, 'SKIN.JUYCEE_01', 'Chance_02'), ('Juycee_Skin02', 'JUYCEE', 'Skin02', 'SKIN_JUYCEE_SKIN02', 86, 'SKIN.JUYCEE_02', 'Chance_03'), ('Juycee_Skin03', 'JUYCEE', 'Skin03', 'SKIN_JUYCEE_SKIN03', 109, 'SKIN.JUYCEE_03', 'Chance_04'), ('Juycee_Skin04', 'JUYCEE', 'Skin04', 'SKIN_JUYCEE_SKIN04', 41, 'SKIN.JUYCEE_04', 'Helen_02'), ('Rivet', 'RATCHET', 'Skin01', 'SKIN_RATCHET_SKIN01', 42, 'SKIN.RIVET_00', 'Avatar_00')]
SKIN_RENAMES = [(b'\x00SKIN_HELEN_SKIN01_DEPRECATED\x00', b'\x00SKIN_HELEN_SKIN01\x00'), (b'\x00SKIN_SANDY_SKIN01_DEPRECATED\x00', b'\x00SKIN_JUYCEE_SKIN00\x00'), (b'\x00SKIN_SANDY_SKIN03_DEPRECATED\x00', b'\x00SKIN_JUYCEE_SKIN01\x00'), (b'\x00SKIN_LIL_ANN_SKIN01_DEPRECATED\x00', b'\x00SKIN_JUYCEE_SKIN02\x00'), (b'\x00SKIN_MARKUS_SKIN01_DEPRECATED\x00', b'\x00SKIN_JUYCEE_SKIN03\x00'), (b'\x00SKIN_CLANK_BAG_SKIN01_DEPRECATED\x00', b'\x00SKIN_JUYCEE_SKIN04\x00'), (b'\x00SKIN_CLANK_BAG_SKIN02_DEPRECATED\x00', b'\x00SKIN_RATCHET_SKIN01\x00')]
CHARACTERS_TABLE = 1675660113974991469
PORTRAIT_GUIDS = {'Helen_01': '5fe037b27649b224bb050825b7394347', 'ico_dialog_rivet': '50a2ee5f61bc002478b510de6734f123', 'Avatar_00': '89021fa48bc16bd4d860f312445fd3ea', 'ico_dialog_Wendy': '9e30195c68d6d614a96fb2e04fc5ff20', 'Chance_01': '8a333de86511eac448e31832f5e23b24', 'Chance_02': '00504f4136ad1bb4db86dca6eed2c133', 'Chance_03': 'd9b6088f6f1a5c448ac61bc1ec83599c', 'Chance_04': 'e94e78b70f2a3f443a8eeadbdfff0f47', 'Helen_02': '229f47f367804114a98c390aecc73dcb', 'ico_dialog_evilWendy': '261e3233b77bcbc47ad820cf19bfea3f'}
JUYCEE_CARDS = [('Chance_01', 'Juycee_carte.png', (512, 374)), ('Chance_02', 'Juycee_carte_1.png', (512, 374)), ('Chance_03', 'Juycee_carte_2.png', (512, 374)), ('Chance_04', 'Juycee_carte_3.png', (512, 374)), ('Helen_02', 'Juycee_carte_4.png', (512, 374)), ('ico_dialog_evilWendy', 'Juycee_icone.png', (256, 256))]

def juycee_picture(name):
    for portrait, file, _ in JUYCEE_CARDS:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'juycee', file)
        if portrait == name and os.path.isfile(path):
            return path
    return None
RIVET_TEXTS = {'FR': ('Rivet', "La Lombax d'une autre dimension, venue faire équipe avec Ratchet."), 'EN': ('Rivet', 'The Lombax from another dimension, teaming up with Ratchet.')}
JUYCEE_TEXTS = {'FR': ['Juycee', 'Juycee Néon', 'Juycee Chantier', 'Juycee Crâne rouge', 'Juycee Améboïde'], 'EN': ['Juycee', 'Neon Juycee', 'Construction Juycee', 'Red Skull Juycee', 'Amoeboid Juycee']}

def new_skin_records():
    if 'hero_models' not in BUILD:
        return []
    try:
        import UnityPy
    except ImportError:
        print('UnityPy absent : pas de nouvelles fiches de costume')
        return []
    info = hero_sources()[0]
    records = [record for record in NEW_SKIN_RECORDS if record[0] in info]
    return [record[:6] + ('Chance_01',) if record[1] == 'JUYCEE' and (not juycee_picture(record[6])) else record for record in records]

def characters_table_change(data, records):
    import UnityPy
    from UnityPy.helpers import TypeTreeHelper
    from UnityPy.streams import EndianBinaryReader, EndianBinaryWriter
    env = UnityPy.load(bytes(data))
    table = next((o for o in env.objects if o.path_id == CHARACTERS_TABLE))
    node, assets = (table._get_typetree_node(), table.assets_file)
    start = table.byte_start - assets.header.data_offset
    info = hero_sources()[0]

    def change(old):
        tree = TypeTreeHelper.read_typetree(node, EndianBinaryReader(old, endian='<'), as_dict=True, byte_size=len(old), assetsfile=assets)
        characters = {c['enumName']: c for c in tree['characters']}
        if any((record[1] == 'JUYCEE' for record in records)) and 'JUYCEE' not in characters:
            juycee = juycee_character(characters['CHANCE'])
            tree['characters'].append(juycee)
            characters['JUYCEE'] = juycee
        for model, hero, codename, enum_name, value, text, portrait in records:
            skins = characters[hero]['skins']
            if any((s['unlockableID']['_value'] == value for s in skins)):
                continue
            base = dict(skins[0] if skins else characters['CHANCE']['skins'][0])
            entry = json_copy(base)
            entry['codename'] = codename
            entry['unlockableID'] = {'_proxy': enum_name, '_index': value, '_value': value}
            entry['localizedName'] = {'_value': text, '_mode': 0}
            entry['localizedDescription'] = {'_value': text + '.DESCRIPTION', '_mode': 0}
            entry['rarity'] = 2
            entry['availabilityType'] = 0
            entry['seasonPassIndex'] = -1
            entry['thumbnailRef'] = dict(base['thumbnailRef'], m_SubObjectName=portrait, m_AssetGUID=PORTRAIT_GUIDS.get(portrait, base['thumbnailRef']['m_AssetGUID']))
            entry['isMatSwap'] = 0
            entry['addressableRef'] = {'m_AssetGUID': info[model]['guid'], 'm_SubObjectName': '', 'm_SubObjectType': ''}
            entry['matSwap'] = {'materials': []}
            entry['menusAnimIDOverride'] = characters[hero]['menusAnimID']
            skins.append(entry)
        if 'Rivet' in info:
            rivet_hero(characters, info['Rivet']['guid'])
        if 'Wendy' in info:
            wendy_hero(characters, info['Wendy']['guid'])
        if weapon_slots_build():
            secondary_gadget_lists(characters)
        if 'JUYCEE' in characters and juycee_picture('ico_dialog_evilWendy'):
            icon = characters['JUYCEE']['thumbnailRef']
            for skin in characters['JUYCEE']['skins']:
                skin['thumbnailBackgroundRef'] = dict(icon)
        writer = EndianBinaryWriter(endian='<')
        TypeTreeHelper.write_typetree(tree, node, writer, assets)
        return writer.bytes
    return (CHARACTERS_TABLE, (start, table.byte_size, change))
AVATAR_SKIN = 160
RIVET_HERO_SPECS = [('HeroesTable', struct.pack('<iiq', 16, 0, -7414600841294808171), struct.pack('<iiq', 16, 0, -307863333376545080)), ('SimulationHeroesTable', struct.pack('<iq', 16, 1675496277196913591), struct.pack('<iq', 16, 640634350159564227))]
RIVET_HERO_TEXTS = {'FR': {'UI.CHARACTER.AVATAR': 'Rivet', 'SKIN.AVATAR_00': 'Rivet', 'CHARACTER.BIO.AVATAR': "Venue d'une autre dimension, Rivet la Lombax fait équipe avec Ratchet et Clank : mêmes armes, même gadget, même RYNO, et un sacré caractère."}, 'EN': {'UI.CHARACTER.AVATAR': 'Rivet', 'SKIN.AVATAR_00': 'Rivet', 'CHARACTER.BIO.AVATAR': 'From another dimension, Rivet the Lombax teams up with Ratchet and Clank: same weapons, same gadget, same RYNO, and plenty of attitude.'}}

def rivet_hero(characters, guid):
    avatar, ratchet = (characters['AVATAR'], characters['RATCHET'])
    for field in ('_defaultWeapon', '_commonFavoriteWeapon', '_rareFavoriteWeapon', '_epicFavoriteWeapon', 'ultimates', 'gadgets', 'meleeWeaponSpec', 'maxHeroImprovementLevel', 'equipMeleeWeaponInMenu', 'menusAnimID', 'specificWinLoseAnimID'):
        avatar[field] = json_copy(ratchet[field])
    portrait = {'m_AssetGUID': PORTRAIT_GUIDS['ico_dialog_rivet'], 'm_SubObjectName': 'ico_dialog_rivet', 'm_SubObjectType': ratchet['thumbnailRef']['m_SubObjectType']}
    avatar['thumbnailRef'] = dict(portrait)
    avatar['visibleInCharactersMenu'] = 1
    avatar['canBeUsedByBots'] = 0
    skin = next((s for s in avatar['skins'] if s['unlockableID']['_value'] == AVATAR_SKIN))
    ratchet_skin = ratchet['skins'][0]
    skin['localizedDescription'] = json_copy(ratchet_skin['localizedDescription'])
    skin['rarity'] = ratchet_skin['rarity']
    skin['thumbnailRef']['m_SubObjectName'] = RIVET_PORTRAIT[0]
    skin['thumbnailRef']['m_AssetGUID'] = RIVET_PORTRAIT[1]
    skin['thumbnailBackgroundRef'] = dict(portrait)
    skin['addressableRef'] = {'m_AssetGUID': guid, 'm_SubObjectName': '', 'm_SubObjectType': ''}
    skin['size'] = ratchet_skin['size']
    skin['menusAnimIDOverride'] = -1
PORTRAITS_BUNDLE = 'assets/aa/Android/ui_portraits_assets_all_c5d463435920b8f4fce5ae3bd7ff8f92.bundle'
RIVET_PORTRAIT = ('Avatar_00', '89021fa48bc16bd4d860f312445fd3ea')
RIVET_ILLUSTRATION = ('ui_atlases_assets_all', 'RivetsChallenge_Illustration')
RIVET_PORTRAIT_CROP = (230, 30, 790, 439)
RIVET_CARD = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rivet', 'Rivet_carte.png')

def rivet_portrait():
    import UnityPy
    from PIL import Image, ImageChops, ImageDraw, ImageFilter
    if os.path.isfile(RIVET_CARD):
        return Image.open(RIVET_CARD).convert('RGBA').resize((512, 374))
    _, atlas = asset_pack_bundle(RIVET_ILLUSTRATION[0])
    sprite = next((o for o in UnityPy.load(atlas).objects if o.type.name == 'Sprite' and o.peek_name() == RIVET_ILLUSTRATION[1]))
    picture = sprite.read().image.convert('RGBA').crop(RIVET_PORTRAIT_CROP).resize((512, 374), Image.LANCZOS)
    fade = Image.new('L', picture.size, 0)
    ImageDraw.Draw(fade).rounded_rectangle((14, 14, 497, 359), radius=40, fill=255)
    fade = fade.filter(ImageFilter.GaussianBlur(12))
    picture.putalpha(ImageChops.multiply(picture.getchannel('A'), fade))
    return picture

def full_rect_sprite(tree, texture_id, width, height):
    units = tree['m_PixelsToUnits']
    old_count = tree['m_RD']['m_VertexData']['m_VertexCount']
    if len(tree['m_RD']['m_VertexData']['m_DataSize']) != (old_count * 12 + 15 & ~15) + old_count * 8:
        raise SystemExit('maillage de sprite inattendu')
    rect = {'x': 0.0, 'y': 0.0, 'width': float(width), 'height': float(height)}
    tree['m_Rect'] = dict(rect)
    tree['m_PhysicsShape'] = []
    render = tree['m_RD']
    render['texture'] = {'m_FileID': 0, 'm_PathID': texture_id}
    render['textureRect'] = dict(rect)
    render['textureRectOffset'] = {'x': 0.0, 'y': 0.0}
    render['uvTransform'] = {'x': units, 'y': width / 2, 'z': units, 'w': height / 2}
    half_x, half_y = (width / 2 / units, height / 2 / units)
    corners = [(-half_x, half_y, 0.0, 1.0), (half_x, half_y, 1.0, 1.0), (-half_x, -half_y, 0.0, 0.0), (half_x, -half_y, 1.0, 0.0)]
    positions = b''.join((struct.pack('<3f', x, y, 0.0) for x, y, _, _ in corners))
    positions += bytes(-len(positions) % 16)
    render['m_VertexData']['m_VertexCount'] = 4
    render['m_VertexData']['m_DataSize'] = positions + b''.join((struct.pack('<2f', u, v) for _, _, u, v in corners))
    render['m_IndexBuffer'] = list(struct.pack('<6H', 0, 1, 2, 2, 1, 3))
    submesh = render['m_SubMeshes'][0]
    submesh.update(firstByte=0, indexCount=6, baseVertex=0, firstVertex=0, vertexCount=4)
    submesh['localAABB'] = {'m_Center': {'x': 0.0, 'y': 0.0, 'z': 0.0}, 'm_Extent': {'x': half_x, 'y': half_y, 'z': 0.0}}
    render['settingsRaw'] &= ~64

def rgba_texture(tree, picture):
    from PIL import Image
    pixels = picture.transpose(Image.FLIP_TOP_BOTTOM).tobytes()
    tree['m_Width'], tree['m_Height'] = picture.size
    tree['m_CompleteImageSize'] = len(pixels)
    tree['m_TextureFormat'] = 4
    tree['m_MipCount'] = 1
    tree['image data'] = pixels
    tree['m_StreamData'] = {'offset': 0, 'size': 0, 'path': ''}

def patch_rivet_portrait(data):
    if not heavy_tools():
        return
    from PIL import Image
    info = hero_sources()[0]
    pictures = []
    if 'Rivet' in info:
        pictures.append((RIVET_PORTRAIT[0], rivet_portrait()))
    if 'Wendy' in info and os.path.isfile(WENDY_PORTRAIT[1]):
        pictures.append((WENDY_PORTRAIT[0], Image.open(WENDY_PORTRAIT[1]).convert('RGBA').resize((512, 374))))
    if any((record[1] == 'JUYCEE' for record in new_skin_records())):
        for name, _, size in JUYCEE_CARDS:
            path = juycee_picture(name)
            if path:
                pictures.append((name, Image.open(path).convert('RGBA').resize(size)))
    if not pictures:
        return
    import UnityPy
    env = UnityPy.load(bytes(data))
    named = {(o.type.name, o.peek_name()): o for o in env.objects if o.type.name in ('Sprite', 'Texture2D')}
    for name, picture in pictures:
        sprite, texture = (named['Sprite', name], named['Texture2D', name])
        tree = texture.read_typetree()
        rgba_texture(tree, picture)
        texture.save_typetree(tree)
        tree = sprite.read_typetree()
        full_rect_sprite(tree, texture.path_id, *picture.size)
        sprite.save_typetree(tree)
    data[:] = env.file.save(packer='lz4')
    print(f"portraits de heros : {', '.join((name for name, _ in pictures))}")
WENDY_SKIN = 85
WENDY_HERO_SPECS = [('HeroesTable', struct.pack('<iiq', 7, 0, 2651809124107139903), struct.pack('<iiq', 7, 0, -307863333376545080)), ('SimulationHeroesTable', struct.pack('<iq', 7, 4109542338586538912), struct.pack('<iq', 7, 640634350159564227))]
WENDY_PORTRAIT = ('Steeljaw_00', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wendy', 'Wendy_carte.png'))
WENDY_HERO_TEXTS = {'FR': {'UI.CHARACTER.STEELJAW': 'Wendy', 'SKIN.STEELJAW_00': 'Wendy', 'CHARACTER.BIO.STEELJAW': "Sortie tout droit des cinématiques de la simulation, Wendy rejoint la bagarre avec l'arsenal de Ratchet : mêmes armes, même gadget, même RYNO."}, 'EN': {'UI.CHARACTER.STEELJAW': 'Wendy', 'SKIN.STEELJAW_00': 'Wendy', 'CHARACTER.BIO.STEELJAW': "Straight out of the simulation's cutscenes, Wendy joins the rumble with Ratchet's arsenal: same weapons, same gadget, same RYNO."}}
WENDY_VISIBLE = os.environ.get('RR_WENDY') == '1'

def wendy_hero(characters, guid):
    hero, ratchet = (characters['STEELJAW'], characters['RATCHET'])
    for field in ('_defaultWeapon', '_commonFavoriteWeapon', '_rareFavoriteWeapon', '_epicFavoriteWeapon', 'ultimates', 'gadgets', 'meleeWeaponSpec', 'maxHeroImprovementLevel', 'equipMeleeWeaponInMenu', 'menusAnimID', 'specificWinLoseAnimID', 'mainMenuAnimatorOverrideController'):
        hero[field] = json_copy(ratchet[field])
    icon = {'m_AssetGUID': PORTRAIT_GUIDS['ico_dialog_Wendy'], 'm_SubObjectName': 'ico_dialog_Wendy', 'm_SubObjectType': ratchet['thumbnailRef']['m_SubObjectType']}
    hero['thumbnailRef'] = dict(icon)
    hero['visibleInCharactersMenu'] = 1 if WENDY_VISIBLE else 0
    hero['wip'] = 0
    hero['canBeUsedByBots'] = 0
    ratchet_skin = ratchet['skins'][0]
    for skin in hero['skins']:
        if skin['unlockableID']['_value'] != WENDY_SKIN:
            skin['availabilityType'] = 1
            continue
        skin['localizedDescription'] = json_copy(ratchet_skin['localizedDescription'])
        skin['rarity'] = ratchet_skin['rarity']
        skin['thumbnailBackgroundRef'] = dict(icon)
        skin['addressableRef'] = {'m_AssetGUID': guid, 'm_SubObjectName': '', 'm_SubObjectType': ''}
        skin['size'] = ratchet_skin['size']
        skin['menusAnimIDOverride'] = -1
JUYCEE_TABLES = [(-5940201613183132357, struct.pack('<iiq', 2, 0, -1122880514257579180), struct.pack('<iiq', 22, 0, -307863333376545080), struct.pack('<iiq', 23, 0, 8164001146724866422)), (-2561997552144112879, struct.pack('<iq', 2, 3703090579129389015), struct.pack('<iq', 22, 640634350159564227), struct.pack('<iq', 23, 1437917254422004741))]

def juycee_hero_specs(stream, table, count):
    entries = {struct.unpack_from('<q', stream, table + i * 24)[0]: struct.unpack_from('<qqIi', stream, table + i * 24) for i in range(count)}
    changes = {}
    for object_id, first_entry, last, added in JUYCEE_TABLES:
        _, start, length, _ = entries[object_id]

        def change(old, first_entry=first_entry, last=last, added=added):
            if old.count(last) != 1 or old.count(first_entry) != 1:
                raise SystemExit('table de heros inattendue (Juycee)')
            at = old.index(last) + len(last)
            first = old.index(first_entry)
            n, = struct.unpack_from('<i', old, first - 4)
            if n != 21:
                raise SystemExit('table de heros : nombre inattendu')
            new = bytearray(old[:at] + added + old[at:])
            struct.pack_into('<i', new, first - 4, n + 1)
            return bytes(new)
        changes[object_id] = (start, length, change)
    grow_objects(stream, table, count, changes)

def rivet_hero_specs(stream, changes=RIVET_HERO_SPECS):
    for name, old, new in changes:
        if stream.count(old) != 1:
            raise SystemExit(f'table de heros inattendue : {name}')
        at = stream.index(old)
        stream[at:at + len(old)] = new
JUYCEE_CHARACTER = 23
JUYCEE_SKIN = 83
JUYCEE_SKINS = (83, 84, 86, 109, 41)
JUYCEE_HERO_TEXTS = {'FR': {'UI.CHARACTER.JUYCEE': 'Juycee', 'UI.CHARACTER.23': 'Juycee', 'CHARACTER.BIO.JUYCEE': 'Juycee, la Goon qui ne tient pas en place : jamais sortie, elle débarque enfin dans la simulation avec ses quatre tenues.'}, 'EN': {'UI.CHARACTER.JUYCEE': 'Juycee', 'UI.CHARACTER.23': 'Juycee', 'CHARACTER.BIO.JUYCEE': 'Juycee, the restless Goon: never released, she finally drops into the simulation with her four outfits.'}}

def juycee_character(chance):
    record = json_copy(chance)
    record['uniqueID'] = {'_proxy': 'JUYCEE', '_index': JUYCEE_CHARACTER, '_value': JUYCEE_CHARACTER}
    record['enumName'] = 'JUYCEE'
    record['bio'] = {'_value': 'CHARACTER.BIO.JUYCEE', '_mode': 0}
    record['visibleInCharactersMenu'] = 1
    record['wip'] = 0
    record['canBeUsedByBots'] = 0
    record['thumbnailRef'] = dict(record['thumbnailRef'], m_SubObjectName='ico_dialog_evilWendy', m_AssetGUID=PORTRAIT_GUIDS['ico_dialog_evilWendy'])
    record['skins'] = []
    return record

def json_copy(value):
    return json.loads(json.dumps(value))
SKIN_CODE = 68314416
IS_SKIN = 75018420
CHARACTER_OF_SKIN = 75046628
SKIN_FUNCTION_START = bytes.fromhex('fe57bea9')
CHARACTER_IDS = {'HELEN': 13, 'CHANCE': 11, 'RATCHET': 22, 'AVATAR': 16, 'JUYCEE': 23}

def new_skin_code(data):
    skins = [(record[4], record[1]) for record in new_skin_records()]
    if not skins:
        return
    if any((record[0] == 'Rivet' for record in new_skin_records())):
        skins.append((AVATAR_SKIN, 'AVATAR'))
    c = Code(SKIN_CODE + 4)
    c.label('is_skin')
    for skin, _ in skins:
        c.emit(a64.cmp_w_imm(0, skin))
        c.jump('b.eq', 'yes')
    c.emit(SKIN_FUNCTION_START)
    c.emit(a64.b(c.here(), IS_SKIN + 4))
    c.label('yes')
    c.emit(a64.movz_w(0, 1))
    c.emit(a64.RET)
    c.label('character')
    for skin, hero in skins:
        c.emit(a64.cmp_w_imm(0, skin))
        c.jump('b.eq', 'hero_' + hero)
    c.emit(SKIN_FUNCTION_START)
    c.emit(a64.b(c.here(), CHARACTER_OF_SKIN + 4))
    for hero in sorted({hero for _, hero in skins}):
        c.label('hero_' + hero)
        c.emit(a64.movz_w(0, CHARACTER_IDS[hero]))
        c.emit(a64.RET)
    rivet = (AVATAR_SKIN, 'AVATAR') in skins
    juycee = any((hero == 'JUYCEE' for _, hero in skins))
    heroes = ([AVATAR_SKIN] if rivet else []) + ([WENDY_SKIN] if 'Wendy' in hero_sources()[0] else []) + ([JUYCEE_SKIN] if juycee else [])
    pairs = ([(AVATAR_SKIN, CHARACTER_IDS['AVATAR'])] if rivet else []) + ([(skin, JUYCEE_CHARACTER) for skin in JUYCEE_SKINS] if juycee else [])
    if heroes:
        c.label('is_hero')
        for skin in heroes:
            c.emit(a64.cmp_w_imm(0, skin))
            c.jump('b.eq', 'yes')
        c.emit(SKIN_FUNCTION_START)
        c.emit(a64.b(c.here(), IS_HERO + 4))
    if pairs:
        c.label('rivet_table')
        for skin, character in pairs:
            c.emit(bytes.fromhex('a30240f9'))
            c.emit(bytes.fromhex('e00313aa'))
            c.emit(a64.movz_w(1, skin))
            c.emit(a64.movz_w(2, character))
            c.call(DICTIONARY_INT_ADD)
        c.emit(bytes.fromhex('880240f9'))
        c.emit(a64.b(c.here(), CHARACTER_TABLE_HOOK + 4))
    if juycee:
        c.label('stable_enum')
        c.emit(struct.pack('<I', 2843738112 | 124 << 15 | 19 << 10 | 31 << 5 | 30))
        c.emit(bytes.fromhex('f30301aa'))
        c.emit(struct.pack('<I', 3107979881))
        c.emit(struct.pack('<I', 3103790057))
        c.call(STABLE_ENUM_TRY_PARSE)
        c.emit(struct.pack('<I', 301989896))
        c.jump('cbnzw', 'stable_enum_done', 8)
        c.emit(struct.pack('<I', 3107984361))
        c.emit(struct.pack('<I', 3103785577))
        c.label('stable_enum_done')
        c.emit(struct.pack('<I', 2831155200 | 4 << 15 | 19 << 10 | 31 << 5 | 30))
        c.emit(a64.RET)
    code, entries = (c.build(), c.labels)
    if isinstance(code, tuple):
        code = code[0]
    if len(code) + 4 > 1128:
        raise SystemExit('plus de place pour les costumes ajoutes')
    at(data, SKIN_CODE, bytes(data[SKIN_CODE:SKIN_CODE + 4]), a64.RET)
    at(data, SKIN_CODE + 4, bytes(data[SKIN_CODE + 4:SKIN_CODE + 4 + len(code)]), code)
    at(data, IS_SKIN, SKIN_FUNCTION_START, a64.b(IS_SKIN, SKIN_CODE + 4 + entries['is_skin']))
    at(data, CHARACTER_OF_SKIN, SKIN_FUNCTION_START, a64.b(CHARACTER_OF_SKIN, SKIN_CODE + 4 + entries['character']))
    if pairs:
        at(data, CHARACTER_TABLE_HOOK, bytes.fromhex('880240f9'), a64.b(CHARACTER_TABLE_HOOK, SKIN_CODE + 4 + entries['rivet_table']))
    if heroes:
        at(data, IS_HERO, SKIN_FUNCTION_START, a64.b(IS_HERO, SKIN_CODE + 4 + entries['is_hero']))
    if juycee:
        at(data, STABLE_ENUM_CALL, a64.bl(STABLE_ENUM_CALL, STABLE_ENUM_TRY_PARSE), a64.bl(STABLE_ENUM_CALL, SKIN_CODE + 4 + entries['stable_enum']))
CHARACTER_TABLE_HOOK = 74998016
DICTIONARY_INT_ADD = 120384924
IS_HERO = 75038916
STABLE_ENUM_CALL = 110877252
STABLE_ENUM_TRY_PARSE = 85361292

def new_skin_texts(language):
    names = JUYCEE_TEXTS.get(language) or JUYCEE_TEXTS['EN']
    texts = {}
    for model, _, _, _, _, text, _ in new_skin_records():
        if text.startswith('SKIN.JUYCEE_'):
            name = names[int(text[-2:])]
            texts[text] = texts[text + '.DESCRIPTION'] = name
        elif text == 'SKIN.RIVET_00':
            texts[text], texts[text + '.DESCRIPTION'] = RIVET_TEXTS.get(language) or RIVET_TEXTS['EN']
    if any((record[0] == 'Rivet' for record in new_skin_records())):
        texts.update(RIVET_HERO_TEXTS.get(language) or RIVET_HERO_TEXTS['EN'])
    if 'Wendy' in hero_sources()[0]:
        texts.update(WENDY_HERO_TEXTS.get(language) or WENDY_HERO_TEXTS['EN'])
    if any((record[1] == 'JUYCEE' for record in new_skin_records())):
        texts.update(JUYCEE_HERO_TEXTS.get(language) or JUYCEE_HERO_TEXTS['EN'])
    return texts

def cdn_skins_present():
    return [skin for skin, _, _ in cdn_skin_bundles()]

def cdn_skin_edits(stream):
    info = hero_sources()[0]
    skins, edits = ([], [])
    for skin in cdn_skins_present():
        hero, number = skin.split('_Skin')
        record = f'SKIN_{hero.upper()}_SKIN{number}'.encode()
        if skin not in info or stream.count(struct.pack('<I', len(record)) + record) != 1:
            continue
        skins.append((struct.pack('<I', len(record)) + record, hero, info[skin]['guid']))
        start = stream.index(struct.pack('<I', len(record)) + record)
        description = stream.index(b'.DESCRIPTION', start) + len(b'.DESCRIPTION')
        availability = (description + 3 & ~3) + 8
        if struct.unpack_from('<i', stream, availability)[0] == 1:
            edits.append((availability, struct.pack('<i', 1), struct.pack('<i', 0)))
    return (model_reference_edits(stream, skins, heroes=False), edits)

def bot_edits(stream):
    edits = []
    for hero in ('Chance', 'Molly', 'Helen'):
        portrait = stream.index(b'ico_miniPortrait_' + hero.encode())
        name = hero.upper().encode()
        field = struct.pack('<I', len(name)) + name
        position = stream.index(field, portrait) + len(field) + 3 & ~3
        edits.append((position, b'\x01', b'\x00'))
    return edits

def patch_local_data(data):
    edits = level_edits() + hero_edits()
    if BOLT_RUSH and 'hero_models' in BUILD:
        offset, old, new = BR_LEVEL_NAME
        if len(old) != len(new):
            raise SystemExit('nom de carte de longueur differente')
        edits.append((offset, struct.pack('<I', len(old)) + old, struct.pack('<I', len(new)) + new))
    if 'hero_models' in BUILD:
        stream = bundle_stream(bytes(data))
        edits += model_reference_edits(stream) + bot_edits(stream)
        references, availability = cdn_skin_edits(stream)
        edits += references + availability
    records = new_skin_records()
    if not EVENTS and (not records):
        patch_bundle(data, edits)
        return
    table_change = characters_table_change(data, records) if records else None
    if not EVENTS:
        stream = bytearray(bundle_stream(bytes(data)))
        for position, old, new in edits:
            at(stream, position, old, new)
        table, count = evenements.LOCAL_DATA_OBJECTS
        grown = grow_objects(stream, table, count, dict([table_change]))
        replace_bundle_stream(data, stream, grown)
        return
    evenements.PICTURE = os.path.isfile(ZURKON_PICTURE)
    evenements.CARD = os.path.isfile(ZURKON_CARD)
    edits += evenements.card_event03_edits()
    stream = bytearray(bundle_stream(bytes(data)))
    if evenements.CARD:
        edits.append(event_tokens_sprite_edit(stream))
    edits.append(loot_box_sprite_edit(stream))
    for position, old, new in edits:
        at(stream, position, old, new)
    evenements.TOKEN_ON_GROUND = heavy_tools()
    object_id, start, size = evenements.EVENTS_META
    table, count = evenements.LOCAL_DATA_OBJECTS
    changes = {object_id: (start, size, evenements.events_meta)}
    if table_change:
        changes[table_change[0]] = table_change[1]
        print(f"fiches de costume ajoutees : {', '.join((record[0] for record in records))}")
    grown = grow_objects(stream, table, count, changes)
    copies = {old ^ evenements.COPY_KEY: (old, lambda raw, old=old: evenements.card_event04(old, raw)) for old in evenements.CARD_EVENT03_OBJECTS}
    copies.update(zurkon_copies(data))
    copies.update(zurkon_token_copies(data))
    stream, added = add_object_copies(stream, table, count, copies)
    replace_bundle_stream(data, stream, grown + added)
ZURKON_PICTURE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'zurkon', 'MmeZurkon.png')
ZURKON_CARD = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'zurkon', 'CarteZurkon.png')

def event_tokens_sprite_edit(stream):
    old = struct.pack('<iq', *evenements.EVENT_TOKENS_SPRITE)
    name = struct.pack('<I', 12) + b'EVENT_TOKENS'
    found = []
    position = stream.find(name)
    while position >= 0:
        if stream[position + 24:position + 36] == old:
            found.append(position + 24)
        position = stream.find(name, position + 1)
    if len(found) != 1:
        raise SystemExit(f"icone des jetons d'evenement introuvable ({len(found)})")
    return (found[0], old, struct.pack('<iq', 0, evenements.CARD_SPRITE))
LOOT_BOX_SPRITE = (3, 409375227192298523)

def loot_box_sprite_edit(stream):
    head = struct.pack('<I', 13) + b'Gadgetron Box' + bytes(3) + struct.pack('<Ii', 0, 1)
    old = head + struct.pack('<iq', 0, 0)
    position = stream.find(old)
    if position < 0 or stream.find(old, position + 1) >= 0:
        raise SystemExit('caisse de LootTypesTable introuvable')
    return (position, old, head + struct.pack('<iq', *LOOT_BOX_SPRITE))
GADGETOKEN_MESH = 3902941848072014239
GADGETOKEN_ROOT = 3785580914809293215
GADGETOKEN_MATERIALS = (-6533974315285689953, -7852664296860169825, 1205496896394217887, -2115532977086543457)

def zurkon_token_copies(data):
    if not heavy_tools():
        return {}
    import UnityPy
    from UnityPy.helpers import TypeTreeHelper
    from UnityPy.streams import EndianBinaryWriter
    local = list(UnityPy.load(bytes(data)).objects)
    pack = zipfile.ZipFile(os.path.join(xapk, 'UnityDataAssetPack.apk'))
    common_name = next((n for n in pack.namelist() if n.split('/')[-1].startswith('default_common_group_')))
    common = {o.path_id: o for o in UnityPy.load(pack.read(common_name)).objects}
    local_file, common_file = (local[0].assets_file, next(iter(common.values())).assets_file)
    found = [i + 1 for i, e in enumerate(local_file.externals) if common_file.name in e.path]
    if len(found) != 1:
        raise SystemExit(f'jeton de Mme Zurkon : {common_file.name} absent de local_data_managers')
    common_id = found[0]
    templates = {}
    for o in local:
        templates.setdefault(o.type.name, o)

    def written(kind, edit):
        template = templates[kind]
        node, assets = (template._get_typetree_node(), template.assets_file)

        def change(raw):
            tree = template.read_typetree()
            edit(tree)
            writer = EndianBinaryWriter(endian='<')
            TypeTreeHelper.write_typetree(tree, node, writer, assets)
            return writer.bytes
        return (template.path_id, change)

    def own(path_id):
        return {'m_FileID': 0, 'm_PathID': path_id}
    go, transform, mesh_filter, renderer = evenements.ZURKON_TOKEN_OBJECTS
    source_renderer = next((common[c['component']['m_PathID']].read_typetree() for c in common[GADGETOKEN_ROOT].read_typetree()['m_Component'] if common[c['component']['m_PathID']].type.name == 'MeshRenderer'))

    def game_object(tree):
        tree.update(m_Name='EventToken_Zurkon', m_Layer=0, m_Tag=0, m_IsActive=1, m_Component=[{'component': own(i)} for i in (transform, mesh_filter, renderer)])

    def transform_tree(tree):
        tree.update(m_GameObject=own(go), m_Father=own(0), m_Children=[], m_LocalPosition={'x': 0.0, 'y': 0.0, 'z': 0.0}, m_LocalRotation={'x': 0.0, 'y': 0.0, 'z': 0.0, 'w': 1.0}, m_LocalScale={'x': 0.7, 'y': 0.7, 'z': 0.7})

    def filter_tree(tree):
        tree.update(m_GameObject=own(go), m_Mesh={'m_FileID': common_id, 'm_PathID': GADGETOKEN_MESH})

    def renderer_tree(tree):
        tree.update({k: v for k, v in source_renderer.items() if k in tree})
        tree.update(m_GameObject=own(go), m_Enabled=1, m_Materials=[{'m_FileID': common_id, 'm_PathID': m} for m in GADGETOKEN_MATERIALS], m_ProbeAnchor=own(0), m_LightProbeVolumeOverride=own(0), m_StaticBatchRoot=own(0))
        for key in ('m_AdditionalVertexStreams', 'm_EnlightenVertexStream'):
            if key in tree:
                tree[key] = own(0)
    print('jeton de Mme Zurkon au sol : la piece Gadgetron de 1.1.0')
    return {go: written('GameObject', game_object), transform: written('Transform', transform_tree), mesh_filter: written('MeshFilter', filter_tree), renderer: written('MeshRenderer', renderer_tree)}

def zurkon_copies(data):
    if not evenements.PICTURE and (not evenements.CARD) or not heavy_tools():
        return {}
    import UnityPy
    from PIL import Image
    from UnityPy.helpers import TypeTreeHelper
    from UnityPy.streams import EndianBinaryReader, EndianBinaryWriter
    objects = {o.path_id: o for o in UnityPy.load(bytes(data)).objects}

    def rewrite(old_id, edit):
        obj = objects[old_id]
        node, assets = (obj._get_typetree_node(), obj.assets_file)

        def change(raw):
            tree = TypeTreeHelper.read_typetree(node, EndianBinaryReader(raw, endian='<'), as_dict=True, byte_size=len(raw), assetsfile=assets)
            edit(tree)
            writer = EndianBinaryWriter(endian='<')
            TypeTreeHelper.write_typetree(tree, node, writer, assets)
            return writer.bytes
        return change
    copies = {}
    if evenements.CARD:
        card = Image.open(ZURKON_CARD).convert('RGBA')

        def card_texture(tree):
            tree['m_Name'] = 'CardZurkon'
            rgba_texture(tree, card)

        def card_sprite(tree):
            tree['m_Name'] = 'CardZurkon'
            tree['m_RenderDataKey'][0]['data[0]'] ^= 746458005
            full_rect_sprite(tree, evenements.CARD_TEXTURE, *card.size)
        copies[evenements.CARD_TEXTURE] = (evenements.TEXTURE_TEMPLATE, rewrite(evenements.TEXTURE_TEMPLATE, card_texture))
        copies[evenements.CARD_SPRITE] = (evenements.SPRITE_TEMPLATE, rewrite(evenements.SPRITE_TEMPLATE, card_sprite))
        print(f"carte Zurkon : {card.size[0]} x {card.size[1]}, image des jetons d'evenement")
    if not evenements.PICTURE:
        return copies
    picture = Image.open(ZURKON_PICTURE).convert('RGBA')
    width, height = picture.size

    def texture(tree):
        tree['m_Name'] = 'MsZurkon_Event'
        rgba_texture(tree, picture)

    def sprite(tree):
        tree['m_Name'] = 'MsZurkon_Event'
        tree['m_RenderDataKey'][0]['data[0]'] ^= 1510768177
        full_rect_sprite(tree, evenements.ZURKON_TEXTURE, width, height)
    renamed = {old: old ^ evenements.ZURKON_KEY for old in evenements.MOPZ_ILLUSTRATION_OBJECTS}
    figure, figure_rect, figure_image = evenements.MOPZ_FIGURE

    def relink(value):
        if isinstance(value, dict):
            if set(value) == {'m_FileID', 'm_PathID'} and value['m_FileID'] == 0 and (value['m_PathID'] in renamed):
                value['m_PathID'] = renamed[value['m_PathID']]
            for item in value.values():
                relink(item)
        elif isinstance(value, list):
            for item in value:
                relink(item)

    def illustration(old_id):

        def edit(tree):
            relink(tree)
            if old_id == evenements.MOPZ_ILLUSTRATION:
                tree['m_Name'] = 'Illustration_EventZurkon'
            elif old_id == figure:
                tree['m_Name'] = 'MsZurkon'
            elif old_id == figure_rect:
                tree['m_SizeDelta'] = dict(zip('xy', evenements.ZURKON_FIGURE_SIZE))
                tree['m_AnchoredPosition'] = dict(zip('xy', evenements.ZURKON_FIGURE_OFFSET))
            elif old_id == figure_image:
                tree['m_Sprite'] = {'m_FileID': 0, 'm_PathID': evenements.ZURKON_SPRITE}
                tree['m_PreserveAspect'] = 1
                tree['m_Material'] = {'m_FileID': 0, 'm_PathID': 0}
        return rewrite(old_id, edit)
    copies.update({evenements.ZURKON_TEXTURE: (evenements.TEXTURE_TEMPLATE, rewrite(evenements.TEXTURE_TEMPLATE, texture)), evenements.ZURKON_SPRITE: (evenements.SPRITE_TEMPLATE, rewrite(evenements.SPRITE_TEMPLATE, sprite))})
    for old, new in renamed.items():
        copies[new] = (old, illustration(old))
    print(f'Mme Zurkon : image {width} x {height} et illustration ajoutees')
    return copies
RENAMED_FILES = {b'CAB-362daa32c55d2edb2ee260b161e8e33f': b'CAB-fefaa237ca08b3d094dadff5db545f76', b'CAB-486da8644fe5dca7369db9153d72fbf6': b'CAB-b00ca7a8a885dc2b23ea44c4388a4105', b'CAB-04de74b3c7c64036e7608340366c745c': b'CAB-6958b85330e8e987f0af28e9b9e03adf', b'CAB-dda31e6215934c6e34e476c72fcd26fa': b'CAB-718bb4c7469902c1c4dcc978dd716d84', b'CAB-aa319b2de83cf7027e416601fb60c3ae': b'CAB-b7bb29c43e97a57482540f25c56a0b03'}
HERO_MODELS = {'Chance': '966f2d8d9c7f95149a7cb4237fcdfd54', 'Molly': 'adcdb763f80f3894f81c197594889b6e', 'Helen': '777a95af41a038b409cd394e0ffb931d', 'Flare': '102bd3a17a4e39b479d896308773c0a8', 'Nakari': '2904978eddf9d4143befcc2778e457de', 'Terry': 'c52cf61167f55554da126cac604d17b6', 'Crumby': '57cadf1fb1a4aaa43988ed5f816d22d0'}
SPRITE_TYPE = 'UnityEngine.Sprite, UnityEngine.CoreModule, Version=0.0.0.0'
BUNDLE_BLOCK = 131072
EXTRA_MODELS = {'Juycee': '0e7a24019654c904aa852294fce5eb52'}

def hero_model_bundles(pack):
    found = []
    for hero in list(HERO_MODELS) + [name for name in EXTRA_MODELS if any((f'skins_character_{name.lower()}_assets_all_' in entry for entry in pack.namelist()))]:
        prefix = f'assets/aa/Android/skins_character_{hero.lower()}_assets_all_'
        path = next((name for name in pack.namelist() if name.startswith(prefix)))
        data = bytearray(pack.read(path))
        stream = bundle_stream(bytes(data))
        edits = []
        for old, new in RENAMED_FILES.items():
            edits += [(match.start(), old, new) for match in re.finditer(re.escape(old), stream)]
        patch_bundle(data, edits)
        found.append((hero, path, bytes(data)))
    return found
HEALTH_TALENT = 932205718080381358
AMMO_TALENT = 3261721121919404876
FIRE_RATE_TALENT = 806155625543343013
HERO_TALENTS = struct.pack('<6q', AMMO_TALENT, FIRE_RATE_TALENT, HEALTH_TALENT, AMMO_TALENT, FIRE_RATE_TALENT, HEALTH_TALENT)
HEROES_WITHOUT_TALENTS = {8164001146724866422: 32, -450373368699069825: 28, -3740259518235205799: 28, 4055337521773987031: 32, 1834682198767006603: 32, -8106055942199915665: 32, -986822564360228212: 32}

def patch_hero_talents(data):
    stream = bytearray(bundle_stream(bytes(data)))
    file_size, data_offset = struct.unpack('>QQ', stream[24:40])
    table, count = BUILD['hero_specs_table']
    objects = [struct.unpack_from('<qqIi', stream, table + i * 24) for i in range(count)]
    specs = sorted((o for o in objects if o[0] in HEROES_WITHOUT_TALENTS), key=lambda o: -o[1])
    if len(specs) != len(HEROES_WITHOUT_TALENTS):
        raise SystemExit('fiches de heros introuvables')
    for object_id, start, size, _ in specs:
        position = data_offset + start + size - HEROES_WITHOUT_TALENTS[object_id]
        if stream[position - 4:position + 4] != bytes(8):
            raise SystemExit(f'fiche inattendue : {object_id}')
        stream[position:position + 4] = struct.pack('<I', len(HERO_TALENTS) // 8)
        stream[position + 4:position + 4] = HERO_TALENTS
    starts = [o[1] for o in specs]
    for i, (object_id, start, size, kind) in enumerate(objects):
        moved = start + len(HERO_TALENTS) * sum((1 for s in starts if s < start))
        if object_id in HEROES_WITHOUT_TALENTS:
            size += len(HERO_TALENTS)
        struct.pack_into('<qqIi', stream, table + i * 24, object_id, moved, size, kind)
    struct.pack_into('>Q', stream, 24, file_size + len(HERO_TALENTS) * len(specs))
    if 'Rivet' in hero_sources()[0]:
        rivet_hero_specs(stream)
    if 'Wendy' in hero_sources()[0]:
        rivet_hero_specs(stream, WENDY_HERO_SPECS)
    if any((record[1] == 'JUYCEE' for record in new_skin_records())):
        juycee_hero_specs(stream, table, count)
    replace_bundle_stream(data, stream)
BOLT_RUSH = not COPIE and os.environ.get('RR_BOLT_RUSH', '1') == '1' and ('hero_models' in BUILD)
EVENTS = BOLT_RUSH and os.environ.get('RR_EVENEMENTS', '1') == '1'
BOLT_RUSH_EDITS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bolt_rush.json')))

def bolt_rush_data(path):

    def patch(data):
        patch_bundle(data, [(offset, bytes.fromhex(old), bytes.fromhex(new)) for offset, old, new in BOLT_RUSH_EDITS[path]])
    return patch
BOLT_RUSH_RENAMES = [(b'\x00QWARK_BALL\x00', b'\x00BOLT_RUSH\x00'), (b'\x00GAME_MODE_BOLT_RUSH_COOP_DEPRECATED\x00', b'\x00GAME_MODE_BOLT_RUSH\x00')]
BOLT_RUSH_GAME_MODE = 9
GAME_MODES_BUNDLE = 'assets/aa/Android/quantum_db_game_modes_assets_all_ce297b7193854380ca79aaddc5810ab1.bundle'
GAME_MODES_OBJECTS = (832524, 18219)
TUTORIAL_SPEC = (2716020363603892662, 3668960, 828)
TUTORIAL_TABLE_ENTRY = struct.pack('<iqqi', 5, 387317373446263462, 2540651079593046860, 0)
UI_ATLAS_FILE = 2
BOLT_RUSH_TEXTS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bolt_rush_textes.json'), encoding='utf-8'))
LOCALIZATION_FILE = 'assets/Data/Localization/{}/_DEFAULT.protobd'
LANGUAGES = ['AR', 'BR', 'CN', 'DE', 'EN', 'ES', 'FR', 'GD', 'IT', 'JP', 'KR', 'MY', 'NL', 'RU', 'TR', 'TW']
BOLT_RUSH_CARD = {'name': 'UI.GAME_MODE.BOLT_RUSH', 'description': 'UI.GAME_MODE.BOLT_RUSH_DESC', 'icon': 2472658898744702415, 'illustration': -81423715014193705, 'animated': 4212379821872507239, 'steps': [('UI.GAME_MODE.BOLT_KING.STEP_01', -2923374288120182764), ('UI.GAME_MODE.BOLT_RUSH_SOLO.STEP_02', 8644978053141830954), ('UI.GAME_MODE.BOLT_RUSH.STEP_03', -940617046196073270)], 'weapons': [1, 2, 14]}

def unity_string(text):
    raw = text.encode('utf-8')
    return struct.pack('<I', len(raw)) + raw + bytes(-len(raw) % 4)

def raw_text(key):
    return unity_string(key) + struct.pack('<i', 0)

def varint(value):
    out = bytearray()
    while True:
        out.append(value & 127 | (128 if value > 127 else 0))
        value >>= 7
        if not out[-1] & 128:
            return bytes(out)

def read_varint(data, position):
    value = shift = 0
    while True:
        byte = data[position]
        position += 1
        value |= (byte & 127) << shift
        shift += 7
        if byte < 128:
            return (value, position)

def proto_fields(data, start, end):
    position = start
    while position < end:
        first = position
        tag, position = read_varint(data, position)
        if tag & 7 != 2:
            raise SystemExit('fichier de langue inattendu')
        size, position = read_varint(data, position)
        yield (tag >> 3, first, position, position + size)
        position += size
CDN_SKIN_TEXTS = {'FR': {'Molly_Skin01': 'Molly Mystique', 'Molly_Skin02': 'Molly Robot', 'Molly_Skin03': 'Molly galactique'}, 'EN': {'Molly_Skin01': 'Mystic Molly', 'Molly_Skin02': 'Robo Molly', 'Molly_Skin03': 'Galaxy Molly'}}

def cdn_skin_texts(language):
    names = CDN_SKIN_TEXTS.get(language) or CDN_SKIN_TEXTS['EN']
    texts = {}
    for skin in cdn_skins_present():
        if skin in names:
            hero, number = skin.split('_Skin')
            key = f'SKIN.{hero.upper()}_{number}'
            texts[key] = texts[key + '.DESCRIPTION'] = names[skin]
    return texts

def patch_localization(language):
    texts = dict(BOLT_RUSH_TEXTS.get(language) or BOLT_RUSH_TEXTS['EN']) if BOLT_RUSH else {}
    if 'difficulty_row' in BUILD:
        texts.update(difficulty_texts(language))
    if 'flail_enhancements' in BUILD:
        texts.update(flail_enhancement_texts(language))
    if 'hero_models' in BUILD:
        texts.update(cdn_skin_texts(language))
        texts.update(new_skin_texts(language))
    if weapon_slots_build():
        texts.update(WEAPON_SLOTS_TEXTS.get(language) or WEAPON_SLOTS_TEXTS['EN'])
    if EVENTS:
        texts.update(ZURKON_TEXTS.get(language) or ZURKON_TEXTS['EN'])
        texts['UI.EVENT.ZURKON.RULES'] = ZURKON_RULES.get(language) or ZURKON_RULES['EN']

    def patch(data):
        source = bytes(data)
        (_, _, root_start, root_end), = list(proto_fields(source, 0, len(source)))
        inner = list(proto_fields(source, root_start, root_end))
        if inner[0][0] != 500:
            raise SystemExit(f'fichier de langue {language} inattendu')
        _, _, table_start, table_end = inner[0]
        entries = []
        for _, first, start, end in proto_fields(source, table_start, table_end):
            key = next((source[s:e] for f, _, s, e in proto_fields(source, start, end) if f == 1))
            entries.append((key, source[first:end]))
        known = {key for key, _ in entries}
        replaced = {key.encode() for key in list(RIVET_HERO_TEXTS['EN']) + list(WENDY_HERO_TEXTS['EN']) + list(WEAPON_SLOTS_TEXTS['EN'])}
        for key, text in texts.items():
            key, text = (key.encode(), text.encode('utf-8'))
            if key in known and key in replaced:
                entries = [entry for entry in entries if entry[0] != key]
            elif key in known:
                raise SystemExit(f'cle deja presente : {key}')
            body = b'\n' + varint(len(key)) + key + b'\x12' + varint(len(text)) + text
            entries.append((key, b'\n' + varint(len(body)) + body))
        entries.sort(key=lambda item: item[0])
        table = b''.join((raw for _, raw in entries))
        rest = source[inner[0][3]:root_end]
        table_field = varint(500 << 3 | 2) + varint(len(table)) + table
        root_body = table_field + rest
        data[:] = b'\n' + varint(len(root_body)) + root_body
    return patch

def bolt_rush_card_fields(card=BOLT_RUSH_CARD):
    out = raw_text(card['name']) + raw_text(card['description'])
    out += struct.pack('<iq', UI_ATLAS_FILE, card['icon']) + struct.pack('<iq', UI_ATLAS_FILE, card['illustration'])
    out += struct.pack('<iq', 0, card['animated'])
    out += bytes(4)
    out += struct.pack('<I', len(card['steps'])) + b''.join((raw_text(text) for text, _ in card['steps']))
    out += struct.pack('<I', len(card['steps'])) + b''.join((struct.pack('<iq', UI_ATLAS_FILE, sprite) for _, sprite in card['steps']))
    out += struct.pack(f"<I{len(card['weapons'])}i", len(card['weapons']), *card['weapons'])
    return out

def bolt_rush_spec(old):
    name = old.index(b'\x16\x00\x00\x00UI.GAME_MODE.BOLT_RUSH')
    fields_end = name + 120
    if old[fields_end - 12:fields_end] != bytes(12) or old[fields_end:fields_end + 4] != bytes(4):
        raise SystemExit('fiche du tutoriel inattendue')
    rest = bytearray(old[fields_end:])
    path = b'AddressablesAssets/QuantumDB/GameModes/Tutorial/TutorialGameModeSpec'
    guid = rest.index(path) + len(path) + -len(path) % 4
    if rest[guid:guid + 12] != struct.pack('<qi', 2540651079593046860, 5):
        raise SystemExit('identifiant du tutoriel inattendu')
    struct.pack_into('<i', rest, guid + 8, BOLT_RUSH_GAME_MODE)
    return bytes(old[:name]) + bolt_rush_card_fields() + bytes(rest)
RUSH_GAME_MODE = 5
RUSH_UNLOCKABLE = 68
GAME_MODES_TABLE = (1776920553094465429, 3431440, 360)
SHOWCASE_SPEC = (1362803872253417729, 3333856, 5044)
SHOWCASE_NAME = b'WeaponShowcaseGameModeSpecAsset'
EMPTY_CARD_FIELDS = 68
RUSH_CARD = {'name': 'UI.GAME_MODE.BOLT_RUSH_SOLO', 'description': 'UI.GAME_MODE.BOLT_RUSH_SOLO_DESC', 'icon': -259124548731543015, 'illustration': -5462325688452219777, 'animated': 5182684857234285510, 'steps': [('UI.GAME_MODE.BOLT_RUSH_SOLO.STEP_01', -2704024689692454975), ('UI.GAME_MODE.BOLT_RUSH_SOLO.STEP_02', 8644978053141830954), ('UI.GAME_MODE.BOLT_RUSH_SOLO.STEP_03', -940617046196073270)], 'weapons': [1, 2, 14]}
BR_GAME_MODE = 12
BR_UNLOCKABLE = 57
TRAINING_SPEC = (-6247403467424489942, 774432, 652)
BR_CARD = {'name': 'UI.GAME_MODE.BATTLE_ROYALE', 'description': 'UI.GAME_MODE.BATTLE_ROYALE_DESC', 'icon': -5414763684585856928, 'illustration': -2582128121011836959, 'animated': -7558087296450120770, 'steps': [('UI.GAME_MODE.BATTLE_ROYALE.STEP_01', 8197178227638723673), ('UI.GAME_MODE.ELIMINATION.STEP_02', -5877483458267625167), ('UI.GAME_MODE.BATTLE_ROYALE.STEP_03', 2879483247635462996)], 'weapons': [5, 10, 21]}
BR_MAPS = [b'q_EL_Prototype_01']
BR_LEVEL_NAME = (1053360, b'LEVEL.BK_MEGALOPOLIS_00.NAME', b'LEVEL.EL_BATTLE_ROYALE1.NAME')
BR_RANK_CHECK = 129624556
BR_WINNERS = 3
BR_RANK_CMP = bytes.fromhex('df06886b')
LEVEL_DESIGN_BUNDLE = 'assets/aa/Android/quantum_db_level_design_assets_all_af019ffc143dd4ebd6eb4386e0ad8819.bundle'
LEVEL_DESIGN_OBJECTS = (399548, 2336)
RUSH_GOLDEN_CONFIG = (-401457971097463861, 715200, 192)
RUSH_GOLDEN_GUID = 2129884193232906956
RUSH_GOLDEN_DELAYS = (60, 60, 120, 120)
RUSH_GOLDEN_BOLTS = 75
RUSH_GOLDEN_DROP = 1474560
RUSH_GOLDEN_HEIGHT = 1966080
RUSH_MAP_POINTS = {'assets/aa/Android/quantum_map_assets_q_bk_sargasso_01_assets_all_a40920a2717fdbf541b730ebc78f0ff1.bundle': ((97968, 7), (-8094758613156511176, 395808, 10940), 1124, [(-2621439, 589824, 2621440), (-131072, 196608, 0), (2621440, 589824, -2621440), (2146304, 786432, 2179071), (-2146304, 786432, -2179072)]), 'assets/aa/Android/quantum_map_assets_q_bk_torreniv_01_assets_all_80833395b99dd7f69dd57fd576e3e057.bundle': ((97968, 13), (-3114715822146110700, 576448, 11620), 1020, [(2686976, 786432, -2097152), (-2686976, 786432, 2097152), (0, 524288, 0), (-655360, 688128, -3866624), (655360, 688128, 3866624)]), 'assets/aa/Android/quantum_map_assets_q_bk_torreniv_02_assets_all_85d23b5e205308433d95349c0a02342a.bundle': ((97968, 13), (-1287192862409957299, 908080, 10724), 1020, [(0, 393216, 0), (-2555904, 753664, 1048576), (2555904, 753664, -1048576), (655360, 917504, 2097152), (-655360, 917504, -2097152)]), 'assets/aa/Android/quantum_map_assets_q_bk_ardolis_01_assets_all_9e50eadafc80e9a53e0b96483c49694b.bundle': ((97968, 7), (-9187427915300057292, 0, 4500), 912, [(-2402785, 655360, 1489868), (2402785, 655360, -1489868), (0, 196608, 0), (2664604, 557056, 2664604), (-2664604, 557056, -2664605)])}

def grow_objects(stream, table, count, changes, shrink=False, types=None):
    file_size, data_offset = struct.unpack('>QQ', stream[24:40])
    entries = [list(struct.unpack_from('<qqIi', stream, table + i * 24)) for i in range(count)]
    total = 0
    for object_id, (start, size, change) in sorted(changes.items(), key=lambda item: -item[1][0]):
        found = [e for e in entries if e[0] == object_id]
        if len(found) != 1 or found[0][1:3] != [start, size]:
            raise SystemExit(f'objet {object_id} introuvable')
        old = bytes(stream[data_offset + start:data_offset + start + size])
        new = change(old)
        if len(new) < size and (not shrink):
            raise SystemExit(f'objet {object_id} raccourci')
        grown = max(0, len(new) - size + 7 & ~7)
        stream[data_offset + start:data_offset + start + size] = new + bytes(size + grown - len(new))
        for e in entries:
            if e[0] == object_id:
                e[2] = len(new)
            elif e[1] > start:
                e[1] += grown
        total += grown
    for e in entries:
        if types and e[0] in types:
            e[3] = types[e[0]]
    for i, e in enumerate(entries):
        struct.pack_into('<qqIi', stream, table + i * 24, *e)
    struct.pack_into('>Q', stream, 24, file_size + total)
    return total

def add_object_copies(stream, table, count, copies, padding=3):
    meta_size = struct.unpack('>I', stream[20:24])[0]
    file_size, data_offset = struct.unpack('>QQ', stream[24:40])
    entries = [struct.unpack_from('<qqIi', stream, table + i * 24) for i in range(count)]
    by_id = {e[0]: e for e in entries}
    data = bytearray(stream[data_offset:file_size])
    for new_id, (old_id, change) in sorted(copies.items()):
        if new_id in by_id:
            raise SystemExit(f'objet {new_id} deja present')
        _, start, size, type_index = by_id[old_id]
        raw = change(bytes(data[start:start + size]))
        data += bytes(-len(data) % 8)
        by_id[new_id] = (new_id, len(data), len(raw), type_index)
        data += raw
    entries = sorted(by_id.values())
    added = len(entries) - count
    count_at = table - 4 - padding
    metadata = bytes(stream[48:count_at]) + struct.pack('<i', len(entries)) + bytes(stream[count_at + 4:table]) + b''.join((struct.pack('<qqIi', *e) for e in entries)) + bytes(stream[table + count * 24:48 + meta_size])
    if stream[count_at:count_at + 4] != struct.pack('<i', count) or len(metadata) != meta_size + added * 24:
        raise SystemExit("table d'objets inattendue")
    new_offset = 48 + len(metadata) + 15 & ~15
    head = bytearray(stream[:48])
    struct.pack_into('>I', head, 20, len(metadata))
    struct.pack_into('>QQ', head, 24, new_offset + len(data), new_offset)
    new_file = bytes(head) + metadata + bytes(new_offset - 48 - len(metadata)) + bytes(data)
    return (bytearray(new_file + bytes(stream[file_size:])), len(new_file) - file_size)

def game_modes_table(old):
    if old.count(TUTORIAL_TABLE_ENTRY) != 1:
        raise SystemExit('table des modes inattendue')
    first = old.index(TUTORIAL_TABLE_ENTRY)
    count, = struct.unpack_from('<i', old, first - 4)
    entries = [struct.unpack_from('<iqqi', old, first + i * 24) for i in range(count)]
    ids = [entry[0] for entry in entries]
    if count != 10 or ids.count(RUSH_GAME_MODE) != 1 or BOLT_RUSH_GAME_MODE in ids or (BR_GAME_MODE in ids):
        raise SystemExit('table des modes inattendue')
    bolt_king = next((entry for entry in entries if entry[0] == 3))
    showcase = next((entry for entry in entries if entry[0] == 6))
    training = next((entry for entry in entries if entry[0] == 7))
    elimination = next((entry for entry in entries if entry[0] == 11))
    new = bytearray(old)
    struct.pack_into('<i', new, first, BOLT_RUSH_GAME_MODE)
    added = [(RUSH_GAME_MODE, bolt_king[1], showcase[2], 0), (BR_GAME_MODE, elimination[1], training[2], 0)]
    struct.pack_into('<i', new, first - 4, count + len(added))
    end = first + count * 24
    new[end:end] = b''.join((struct.pack('<iqqi', *entry) for entry in added))
    return bytes(new)

def card_spec(name, card):

    def change(old):
        name_size, = struct.unpack_from('<I', old, 28)
        start = 32 + name_size + -name_size % 4
        if old[32:32 + name_size] != name or old[start:start + EMPTY_CARD_FIELDS] != bytes(EMPTY_CARD_FIELDS):
            raise SystemExit(f'fiche {name.decode()} inattendue')
        return old[:start] + bolt_rush_card_fields(card) + old[start + EMPTY_CARD_FIELDS:]
    return change

def patch_game_modes(data):
    stream = bytearray(bundle_stream(bytes(data)))
    for offset, old, new in BOLT_RUSH_EDITS[GAME_MODES_BUNDLE]:
        at(stream, offset, bytes.fromhex(old), bytes.fromhex(new))
    table, count = GAME_MODES_OBJECTS
    changes = {TUTORIAL_SPEC[0]: (TUTORIAL_SPEC[1], TUTORIAL_SPEC[2], bolt_rush_spec), GAME_MODES_TABLE[0]: (GAME_MODES_TABLE[1], GAME_MODES_TABLE[2], game_modes_table), SHOWCASE_SPEC[0]: (SHOWCASE_SPEC[1], SHOWCASE_SPEC[2], card_spec(SHOWCASE_NAME, RUSH_CARD)), TRAINING_SPEC[0]: (TRAINING_SPEC[1], TRAINING_SPEC[2], card_spec(b'TrainingGameModeSpec', BR_CARD))}
    replace_bundle_stream(data, stream, grow_objects(stream, table, count, changes))

def rush_golden_config(old):
    guid = old.index(struct.pack('<q', RUSH_GOLDEN_GUID))
    earned = guid + 16
    delays = earned + 4
    if old[earned:delays] != struct.pack('<HH', 100, 0) or old[delays:delays + 20] != struct.pack('<iqq', 0, 20 << 16, 25 << 16):
        raise SystemExit('boulon dore inattendu')
    times = struct.pack(f'<i{len(RUSH_GOLDEN_DELAYS)}q', len(RUSH_GOLDEN_DELAYS), *(s << 16 for s in RUSH_GOLDEN_DELAYS))
    return old[:earned] + struct.pack('<HH', RUSH_GOLDEN_BOLTS, 0) + times + struct.pack('<qq', RUSH_GOLDEN_DROP, RUSH_GOLDEN_HEIGHT) + old[delays + 20:]

def rush_map(path):
    (table, count), (object_id, start, size), at_offset, points = RUSH_MAP_POINTS[path]

    def add_points(old):
        if old[at_offset:at_offset + 4] != bytes(4):
            raise SystemExit('points du boulon dore inattendus')
        added = struct.pack('<i', len(points)) + b''.join((struct.pack('<3q', *point) for point in points))
        return old[:at_offset] + added + old[at_offset + 4:]

    def patch(data):
        stream = bytearray(bundle_stream(bytes(data)))
        for offset, old, new in BOLT_RUSH_EDITS.get(path, []):
            at(stream, offset, bytes.fromhex(old), bytes.fromhex(new))
        replace_bundle_stream(data, stream, grow_objects(stream, table, count, {object_id: (start, size, add_points)}))
    return patch

def patch_level_design(data):
    stream = bytearray(bundle_stream(bytes(data)))
    table, count = LEVEL_DESIGN_OBJECTS
    object_id, start, size = RUSH_GOLDEN_CONFIG
    replace_bundle_stream(data, stream, grow_objects(stream, table, count, {object_id: (start, size, rush_golden_config)}))
RUSH_CODE = 67934428
RUSH_CODE_END = RUSH_CODE + 1608
DISPLAY_CODE = 67932228
DISPLAY_CODE_END = DISPLAY_CODE + 1856
BOLT_RUSH_SWITCH = RUSH_CODE + 4
BOLT_KING_SPEC = 985954205684366378
FIND_ASSET = 128650348
SPEC_FIELDS = [(48, 8), (184, 8), (224, 8), (232, 8), (376, 8), (384, 8), (416, 8), (488, 8), (456, 8), (464, 8), (80, 4), (208, 4), (480, 4), (240, 1), (408, 1)]
BOLT_KING_VALUES = {48: 180 << 16, 184: 1944011347666261512, 224: 1299186242396030174, 232: 1067394776428191794, 376: 1522270081786856041, 384: 2304507479634667108, 416: 0, 488: 0, 80: 100, 208: 30, 480: 300, 240: 0, 408: 0, 456: 0, 464: 0}
BOLT_RUSH_POWER = 751619029107946806
KING_SCORE = int(os.environ.get('RR_KING_SCORE', '200'))
KING_GATHERER = 80969588127492484
SPEC_VALUES = {'solo': BOLT_KING_VALUES, 'coop': {**BOLT_KING_VALUES, 48: 150 << 16, 384: 4457707506713145229, 184: RUSH_GOLDEN_GUID, 416: 0, 80: 200, 480: 600, 240: 1, 408: 1}, 'rush': {**BOLT_KING_VALUES, 184: RUSH_GOLDEN_GUID, 488: 30 << 16, 384: KING_GATHERER, 480: KING_SCORE}, 'br': {**BOLT_KING_VALUES, 488: 1}}

def a64_ldst(base, size, rt, rn, offset):
    return struct.pack('<I', base | offset // size << 10 | rn << 5 | rt)

def a64_adr(rd, source, target):
    delta = target - source
    return struct.pack('<I', 268435456 | (delta & 3) << 29 | (delta >> 2 & 524287) << 5 | rd)

def a64_cb(base, rt, source, target):
    return struct.pack('<I', base | (target - source >> 2 & 524287) << 5 | rt)
LOADS = {8: 4181721088, 4: 3107979264, 1: 960495616}
STORES = {8: 4177526784, 4: 3103784960, 1: 956301312}

def spec_values_block(values):
    out = bytearray()
    for offset, size in SPEC_FIELDS:
        out += bytes(-len(out) % size) + values[offset].to_bytes(size, 'little', signed=values[offset] < 0)
    return bytes(out + bytes(-len(out) % 8))

def bolt_rush_switch(c):
    c.label('switch')
    c.emit(a64.stp_x_pre(19, 30, a64.SP, -16))
    c.emit(a64.movz_w(19, 1) + a64.cmp_x_imm(0, 1))
    c.jump('b.eq', 'switch_find')
    c.emit(a64.movz_w(19, 2) + a64.cmp_x_imm(0, 2))
    c.jump('b.eq', 'switch_find')
    c.emit(a64.movz_w(19, 3) + a64.cmp_x_imm(0, 3))
    c.jump('b.eq', 'switch_find')
    c.jump('adr', 'switch_key', 0)
    c.call(BUILD['string_new'])
    c.emit(a64.mov_x_zero(1))
    c.call(BUILD['prefs_get_string'])
    c.emit(a64.movz_w(19, 0))
    c.jump('cbz', 'switch_find', 0)
    c.emit(a64.ldr_w(8, 0, 16))
    c.jump('cbzw', 'switch_find', 8)
    c.emit(a64.movz_w(19, 1))
    c.emit(a64_ldst(2034237440, 2, 8, 0, 20))
    c.emit(a64.cmp_w_imm(8, ord('2')))
    c.jump('b.ne', 'switch_find')
    c.emit(a64.movz_w(19, 2))
    c.label('switch_find')
    c.jump('ldrlit', 'bolt_king_spec', 0)
    c.emit(a64.mov_x_zero(1))
    c.call(FIND_ASSET)
    c.jump('cbz', 'switch_end', 0)
    c.emit(a64.ldr_x(8, 0, 136))
    c.jump('cbz', 'switch_end', 8)
    c.jump('adr', 'values_solo', 9)
    c.jump('cbzw', 'switch_write', 19)
    c.jump('adr', 'values_coop', 9)
    c.emit(a64.cmp_w_imm(19, 1))
    c.jump('b.eq', 'switch_write')
    c.jump('adr', 'values_rush', 9)
    c.emit(a64.cmp_w_imm(19, 2))
    c.jump('b.eq', 'switch_write')
    c.jump('adr', 'values_br', 9)
    c.label('switch_write')
    position = 0
    for offset, size in SPEC_FIELDS:
        position += -position % size
        c.emit(a64_ldst(LOADS[size], size, 10, 9, position) + a64_ldst(STORES[size], size, 10, 8, offset))
        position += size
    c.label('switch_end')
    c.emit(a64.ldp_x_post(19, 30, a64.SP, 16))
    c.emit(a64.RET)

def bolt_rush_switch_data(c):
    for name in ('solo', 'coop', 'rush', 'br'):
        c.label('values_' + name)
        c.emit(spec_values_block(SPEC_VALUES[name]))
    c.label('switch_key')
    c.emit(b'rr_coop\x00')
SELECT_RANDOM_MAP_CALL = 66500760
SELECT_RANDOM_MAP = 66501224
BOLT_RUSH_MAPS = [b'q_BK_Sargasso_01', b'q_BK_Megalopolis_01C', b'q_BK_TorrenIV_01', b'q_BK_TorrenIV_02', b'q_BK_Ardolis_01']
RUSH_MAPS = [b'q_BK_Sargasso_01', b'q_BK_TorrenIV_01', b'q_BK_TorrenIV_02', b'q_BK_Ardolis_01']
MAP_NAME_SLOT = 24
TEAM_COUNTER_FLAG = 130603656
TITLE_KEY_LOAD = 131610760
TITLE_BOLT_KING = 'UI.GAME_MODE.BOLT_KING'
TITLE_ELIMINATION = 'UI.GAME_MODE.ELIMINATION'
ELIMINATION_GAME_MODE = 11
TITLE_OBJECT = 'GameModeTitle'
GET_GAME_OBJECT = 142923916
OBJECT_GET_NAME = 142970344
STRING_EQUALS = 123993740
CARD_MODE_ID = 67470960
TABLE_ENTRY_ID = 128564156
GET_QUANTUM_ID_FROM_UID = 66760824
GET_UID_FROM_QUANTUM_ID = 66763004
IS_GAME_MODE = 75039044
BOLT_RUSH_UNLOCKABLE = 114
SUB_SP_0X50 = bytes.fromhex('ff4301d1')
ID_SHORTCUTS = [(GET_QUANTUM_ID_FROM_UID, SUB_SP_0X50, [(BOLT_RUSH_UNLOCKABLE, BOLT_RUSH_GAME_MODE), (RUSH_UNLOCKABLE, RUSH_GAME_MODE), (BR_UNLOCKABLE, BR_GAME_MODE)]), (GET_UID_FROM_QUANTUM_ID, SUB_SP_0X50, [(BOLT_RUSH_GAME_MODE, BOLT_RUSH_UNLOCKABLE), (RUSH_GAME_MODE, RUSH_UNLOCKABLE), (BR_GAME_MODE, BR_UNLOCKABLE)]), (IS_GAME_MODE, a64.stp_x_pre(30, 21, a64.SP, -32), [(BOLT_RUSH_UNLOCKABLE, 1), (RUSH_UNLOCKABLE, 1), (BR_UNLOCKABLE, 1)])]
GET_COLLECTED_BOLTS = 129707120
RANKING_COLLECTED_BOLTS_CALL = 129621600
TEAM_COUNTER_CHECK = 129707280
BATTLE_RESULT_STORE = 129620860
ROW_DONE_CALL = 67584340
SET_IS_DEAD = 67573780
GET_MAIN_GAME = 66468776
GET_LOCAL_ENTITY = 66466828
GET_TEAM_ID = 130417996
GET_TEAM_BOLTS = 129708468
TMP_SET_COLOR = 140937804
TRY_GET_TEAM_ID = 130418572
TOP_PLAYERS_TEAM_CALLS = [67592020, 67593040]
MAX_COUNTER_CHECKS = [67350572, 67350784]
MAX_COUNTER_FORMAT_CALL = 67350704
STRING_FORMAT = 124008380
INT_TO_STRING = 125681772
STRING_CONCAT_4 = 124049648
ENEMY_TOTAL_LEAD = b'<size=65%>'
ENEMY_TOTAL_OPEN = b'\n<color=#FF5C52>vs '
GET_GAME_MODE_SPEC_ASSET = 128564732
EXPLANATION_SPEC_CALLS = [67519000, 67464784]
BIND_PLAYER = 67587544
BIND_PLAYER_CALL = 67587488
OWN_BOLTS_MARK = 8796023608539197463
ALLY_COLOR = (0.3, 0.72, 1.0, 1.0)
OPPONENT_COLOR = (1.0, 0.36, 0.32, 1.0)
COOP_BATTLE_CODE = 67926192

def mark_x(c, register):
    for shift in range(4):
        part = OWN_BOLTS_MARK >> 16 * shift & 65535
        base = 3531603968 if shift == 0 else 4068474880
        c.emit(struct.pack('<I', base | shift << 21 | part << 5 | register))

def coop_battle_code(at_address):
    c = Code(at_address)
    save = a64.stp_x_pre(29, 30, a64.SP, -80) + a64.stp_x(19, 20, a64.SP, 16) + a64.stp_x(21, 22, a64.SP, 32) + a64.stp_x(23, 24, a64.SP, 48)
    restore = a64.ldp_x(23, 24, a64.SP, 48) + a64.ldp_x(21, 22, a64.SP, 32) + a64.ldp_x(19, 20, a64.SP, 16) + a64.ldp_x_post(29, 30, a64.SP, 80)

    def frame_into_x22(fail):
        c.emit(a64.mov_x_zero(0))
        c.call(GET_MAIN_GAME)
        c.jump('cbz', fail, 0)
        c.emit(bytes.fromhex('f30300aa'))
        c.emit(a64.ldr_x(8, 0, 56))
        c.jump('cbz', fail, 8)
        c.emit(a64.ldr_x(22, 8, 16))
        c.jump('cbz', fail, 22)
    c.label('is_coop')
    c.emit(a64.stp_x_pre(29, 30, a64.SP, -16))
    c.jump('ldrlit', 'spec', 0)
    c.emit(a64.mov_x_zero(1))
    c.call(FIND_ASSET)
    c.jump('cbz', 'not_coop', 0)
    c.emit(a64.ldr_x(8, 0, 136))
    c.jump('cbz', 'not_coop', 8)
    c.emit(struct.pack('<I', 960495616 | 240 << 10 | 8 << 5))
    c.emit(a64.ldp_x_post(29, 30, a64.SP, 16))
    c.emit(a64.RET)
    c.label('not_coop')
    c.emit(a64.movz_w(0, 0))
    c.emit(a64.ldp_x_post(29, 30, a64.SP, 16))
    c.emit(a64.RET)
    c.label('own_bolts')
    c.emit(a64.stp_x_pre(29, 30, a64.SP, -32))
    c.emit(a64.str_x(23, a64.SP, 16))
    mark_x(c, 23)
    c.call(GET_COLLECTED_BOLTS)
    c.emit(a64.ldr_x(23, a64.SP, 16))
    c.emit(a64.ldp_x_post(29, 30, a64.SP, 32))
    c.emit(a64.RET)
    c.label('team_flag')
    c.emit(a64.ldr_w(0, 8, 4))
    mark_x(c, 9)
    c.emit(a64.cmp_x(23, 9))
    c.jump('b.ne', 'team_flag_done')
    c.emit(a64.movz_w(0, 0))
    c.label('team_flag_done')
    c.emit(a64.RET)
    c.label('result')
    c.emit(save)
    c.emit(a64.mov_w(21, 8))
    c.emit(bytes.fromhex('f80313aa'))
    c.jump('bl', 'is_coop')
    c.jump('cbzw', 'result_store', 0)
    frame_into_x22('result_store')
    c.emit(a64.mov_x_zero(2))
    c.emit(bytes.fromhex('e00316aa'))
    c.emit(bytes.fromhex('e10314aa'))
    c.call(GET_TEAM_ID)
    c.emit(a64.mov_w(23, 0))
    c.emit(bytes.fromhex('e00316aa'))
    c.emit(a64.mov_w(1, 23))
    c.emit(a64.mov_x_zero(2))
    c.call(GET_TEAM_BOLTS)
    c.emit(a64.mov_w(20, 0))
    c.emit(bytes.fromhex('e00316aa'))
    c.emit(struct.pack('<I', 1375731712 | 23 << 5 | 1))
    c.emit(a64.mov_x_zero(2))
    c.call(GET_TEAM_BOLTS)
    c.emit(a64.cmp_w(20, 0))
    c.jump('b.eq', 'result_store')
    c.emit(a64.movz_w(9, 1))
    c.emit(a64.movz_w(10, 2))
    c.emit(a64.csel_w(21, 9, 10, 'gt'))
    c.label('result_store')
    c.emit(struct.pack('<I', 3103784960 | 24 << 5 | 21))
    c.emit(restore)
    c.emit(a64.RET)
    c.label('row')
    c.emit(save)
    c.emit(bytes.fromhex('f40313aa'))
    c.emit(bytes.fromhex('f50300aa'))
    c.emit(a64.mov_w(24, 27))
    c.call(SET_IS_DEAD)
    c.jump('bl', 'is_coop')
    c.jump('cbzw', 'row_done', 0)
    frame_into_x22('row_done')
    c.emit(a64.ldr_x(8, 20, 104))
    c.jump('cbz', 'row_done', 8)
    c.emit(a64.ldr_w(9, 8, 24))
    c.emit(a64.cmp_w(24, 9))
    c.jump('b.hs', 'row_done')
    c.emit(bytes.fromhex('097f4093'))
    c.emit(bytes.fromhex('0815098b'))
    c.emit(a64.ldr_x(1, 8, 32))
    c.emit(bytes.fromhex('e00316aa'))
    c.emit(a64.mov_x_zero(2))
    c.call(GET_TEAM_ID)
    c.emit(a64.mov_w(23, 0))
    c.emit(bytes.fromhex('e00313aa'))
    c.emit(bytes.fromhex('e10316aa'))
    c.emit(a64.mov_x_zero(2))
    c.call(GET_LOCAL_ENTITY)
    c.emit(bytes.fromhex('e10300aa'))
    c.emit(bytes.fromhex('e00316aa'))
    c.emit(a64.mov_x_zero(2))
    c.call(GET_TEAM_ID)
    c.emit(a64.ldr_x(8, 21, 40))
    c.jump('cbz', 'row_done', 8)
    c.emit(a64.cmp_w(0, 23))
    c.jump('adr', 'ally', 9)
    c.jump('adr', 'opponent', 10)
    c.emit(struct.pack('<I', 2592079872 | 10 << 16 | 0 << 12 | 9 << 5 | 9))
    c.emit(struct.pack('<I', 759169024 | 1 << 10 | 9 << 5 | 0))
    c.emit(struct.pack('<I', 759169024 | 2 << 15 | 3 << 10 | 9 << 5 | 2))
    c.emit(bytes.fromhex('e00308aa'))
    c.emit(a64.mov_x_zero(1))
    c.call(TMP_SET_COLOR)
    c.label('row_done')
    c.emit(restore)
    c.emit(a64.RET)
    c.label('team_split')
    c.emit(a64.stp_x_pre(29, 30, a64.SP, -32))
    c.call(TRY_GET_TEAM_ID)
    c.emit(a64.str_x(0, a64.SP, 16))
    c.jump('bl', 'is_coop')
    c.emit(a64.mov_w(9, 0))
    c.emit(a64.ldr_x(0, a64.SP, 16))
    c.jump('cbzw', 'team_split_done', 9)
    c.emit(a64.movz_w(0, 0))
    c.label('team_split_done')
    c.emit(a64.ldp_x_post(29, 30, a64.SP, 32))
    c.emit(a64.RET)
    c.label('item_color')
    c.emit(save)
    c.emit(bytes.fromhex('f50300aa'))
    c.emit(bytes.fromhex('f40301aa'))
    c.call(BIND_PLAYER)
    c.jump('bl', 'is_coop')
    c.jump('cbzw', 'item_done', 0)
    frame_into_x22('item_done')
    c.emit(bytes.fromhex('e00316aa'))
    c.emit(bytes.fromhex('e10314aa'))
    c.emit(a64.mov_x_zero(2))
    c.call(GET_TEAM_ID)
    c.emit(a64.mov_w(23, 0))
    c.emit(bytes.fromhex('e00313aa'))
    c.emit(bytes.fromhex('e10316aa'))
    c.emit(a64.mov_x_zero(2))
    c.call(GET_LOCAL_ENTITY)
    c.emit(bytes.fromhex('f80300aa'))
    c.emit(a64.cmp_x(24, 20))
    c.jump('b.eq', 'item_done')
    c.emit(bytes.fromhex('e10318aa'))
    c.emit(bytes.fromhex('e00316aa'))
    c.emit(a64.mov_x_zero(2))
    c.call(GET_TEAM_ID)
    c.emit(a64.ldr_x(8, 21, 32))
    c.jump('cbz', 'item_done', 8)
    c.emit(a64.cmp_w(0, 23))
    c.jump('adr', 'ally', 9)
    c.jump('adr', 'opponent', 10)
    c.emit(struct.pack('<I', 2592079872 | 10 << 16 | 0 << 12 | 9 << 5 | 9))
    c.emit(struct.pack('<I', 759169024 | 1 << 10 | 9 << 5 | 0))
    c.emit(struct.pack('<I', 759169024 | 2 << 15 | 3 << 10 | 9 << 5 | 2))
    c.emit(bytes.fromhex('e00308aa'))
    c.emit(a64.mov_x_zero(1))
    c.call(TMP_SET_COLOR)
    c.label('item_done')
    c.emit(restore)
    c.emit(a64.RET)
    c.label('enemy_total')
    c.emit(save)
    c.jump('bl', 'is_coop')
    c.jump('cbzw', 'enemy_none', 0)
    frame_into_x22('enemy_none')
    c.emit(bytes.fromhex('e00313aa'))
    c.emit(bytes.fromhex('e10316aa'))
    c.emit(a64.mov_x_zero(2))
    c.call(GET_LOCAL_ENTITY)
    c.emit(bytes.fromhex('e10300aa'))
    c.emit(bytes.fromhex('e00316aa'))
    c.emit(a64.mov_x_zero(2))
    c.call(GET_TEAM_ID)
    c.emit(struct.pack('<I', 1375731712 | 0 << 5 | 1))
    c.emit(bytes.fromhex('e00316aa'))
    c.emit(a64.mov_x_zero(2))
    c.call(GET_TEAM_BOLTS)
    c.jump('b', 'enemy_done')
    c.label('enemy_none')
    c.emit(struct.pack('<I', 310378496))
    c.label('enemy_done')
    c.emit(restore)
    c.emit(a64.RET)
    c.label('max_key')
    c.emit(a64.stp_x_pre(29, 30, a64.SP, -32))
    c.emit(struct.pack('<I', 2034237440 | 42 // 2 << 10 | 8 << 5 | 8))
    c.emit(a64.str_x(8, a64.SP, 16))
    c.jump('bl', 'enemy_total')
    c.emit(a64.ldr_x(8, a64.SP, 16))
    c.emit(struct.pack('<I', 922746880 | 31 << 19 | 2 << 5 | 0))
    c.emit(struct.pack('<I', 704643072 | 0 << 22 | 0 << 16 | 16 << 10 | 8 << 5 | 8))
    c.emit(a64.ldp_x_post(29, 30, a64.SP, 32))
    c.emit(a64.RET)
    c.label('max_text')
    c.emit(a64.stp_x_pre(29, 30, a64.SP, -48))
    c.emit(a64.str_x(19, a64.SP, 16))
    c.call(STRING_FORMAT)
    c.emit(bytes.fromhex('f30300aa'))
    c.jump('bl', 'enemy_total')
    c.jump('tbnz31', 'max_text_done', 0)
    c.emit(struct.pack('<I', 3103784960 | 24 // 4 << 10 | 31 << 5 | 0))
    c.emit(bytes.fromhex('e0630091'))
    c.emit(a64.mov_x_zero(1))
    c.call(INT_TO_STRING)
    c.emit(a64.str_x(0, a64.SP, 32))
    c.jump('adr', 'vs_open', 0)
    c.call(BUILD['string_new'])
    c.emit(a64.str_x(0, a64.SP, 40))
    c.jump('adr', 'vs_lead', 0)
    c.call(BUILD['string_new'])
    c.emit(bytes.fromhex('e10313aa'))
    c.emit(a64.ldr_x(2, a64.SP, 40))
    c.emit(a64.ldr_x(3, a64.SP, 32))
    c.emit(a64.mov_x_zero(4))
    c.call(STRING_CONCAT_4)
    c.emit(bytes.fromhex('f30300aa'))
    c.label('max_text_done')
    c.emit(bytes.fromhex('e00313aa'))
    c.emit(a64.ldr_x(19, a64.SP, 16))
    c.emit(a64.ldp_x_post(29, 30, a64.SP, 48))
    c.emit(a64.RET)
    while len(c.code) % 8:
        c.emit(a64.NOP)
    c.label('spec')
    c.emit(struct.pack('<q', BOLT_KING_SPEC))
    c.label('ally')
    c.emit(struct.pack('<4f', *ALLY_COLOR))
    c.label('opponent')
    c.emit(struct.pack('<4f', *OPPONENT_COLOR))
    c.label('vs_lead')
    c.emit(ENEMY_TOTAL_LEAD + b'\x00')
    c.label('vs_open')
    c.emit(ENEMY_TOTAL_OPEN + b'\x00')
    return (c.build(), {name: at_address + c.labels[name] for name in ('is_coop', 'own_bolts', 'team_flag', 'result', 'row', 'team_split', 'item_color', 'max_key', 'max_text')})

def rush_code(at_address):
    c = Code(at_address)
    c.emit(a64.RET)
    bolt_rush_switch(c)
    c.label('select_map')
    c.emit(a64.cmp_w_imm(21, BOLT_RUSH_GAME_MODE))
    c.jump('b.eq', 'coop_map')
    c.emit(a64.cmp_w_imm(21, RUSH_GAME_MODE))
    c.jump('b.eq', 'rush_map')
    c.emit(a64.cmp_w_imm(21, BR_GAME_MODE))
    c.jump('b.eq', 'br_map')
    c.emit(a64.stp_x_pre(29, 30, a64.SP, -48))
    c.emit(a64.stp_x(0, 1, a64.SP, 16))
    c.emit(a64.str_x(2, a64.SP, 32))
    c.emit(a64.mov_x_zero(0))
    c.jump('bl', 'switch')
    c.emit(a64.ldp_x(0, 1, a64.SP, 16))
    c.emit(a64.ldr_x(2, a64.SP, 32))
    c.emit(a64.ldp_x_post(29, 30, a64.SP, 48))
    c.emit(a64.b(c.here(), SELECT_RANDOM_MAP))
    for mode, name, maps in ((1, 'coop', RUSH_MAPS), (2, 'rush', RUSH_MAPS), (3, 'br', BR_MAPS)):
        c.label(name + '_map')
        c.emit(a64.stp_x_pre(29, 30, a64.SP, -16))
        c.emit(a64.movz_x(0, mode))
        c.jump('bl', 'switch')
        c.emit(a64.mrs_counter(8))
        c.emit(a64.movz_x(9, len(maps)))
        c.emit(a64.udiv_x(10, 8, 9))
        c.emit(a64.msub_x(8, 10, 9, 8))
        c.emit(a64.movz_x(10, MAP_NAME_SLOT))
        c.jump('adr', name + '_maps', 9)
        c.emit(a64.madd_x(0, 8, 10, 9))
        c.call(BUILD['string_new'])
        c.emit(a64.ldp_x_post(29, 30, a64.SP, 16))
        c.emit(a64.RET)
    for function, first, pairs in ID_SHORTCUTS:
        c.label(f'shortcut_{function:x}')
        for given, answer in pairs:
            c.emit(a64.cmp_w_imm(0, given))
            c.jump('b.ne', f'shortcut_{function:x}_{given}')
            c.emit(a64.movz_w(0, answer))
            c.emit(a64.RET)
            c.label(f'shortcut_{function:x}_{given}')
        c.emit(first)
        c.emit(a64.b(c.here(), function + 4))
    c.label('is_rush')
    c.emit(a64.stp_x_pre(29, 30, a64.SP, -16))
    c.jump('ldrlit', 'bolt_king_spec', 0)
    c.emit(a64.mov_x_zero(1))
    c.call(FIND_ASSET)
    c.jump('cbz', 'not_rush', 0)
    c.emit(a64.ldr_x(8, 0, 136))
    c.jump('cbz', 'not_rush', 8)
    c.emit(a64.ldr_x(9, 8, 184))
    c.jump('ldrlit', 'rush_golden', 10)
    c.emit(a64.cmp_x(9, 10))
    c.jump('b.ne', 'not_rush')
    c.emit(a64_ldst(LOADS[1], 1, 9, 8, 240))
    c.emit(struct.pack('<I', 1895825727))
    c.emit(struct.pack('<I', 446633952))
    c.emit(a64.ldp_x_post(29, 30, a64.SP, 16))
    c.emit(a64.RET)
    c.label('not_rush')
    c.emit(a64.movz_w(0, 0))
    c.emit(a64.ldp_x_post(29, 30, a64.SP, 16))
    c.emit(a64.RET)
    c.label('team_counter_flag')
    c.emit(a64_ldst(LOADS[1], 1, 10, 19, 408))
    c.emit(a64_ldst(LOADS[1], 1, 11, 19, 240))
    c.emit(struct.pack('<I', 167772160 | 11 << 16 | 10 << 5 | 10))
    c.emit(a64.RET)
    while len(c.code) % 8:
        c.emit(a64.NOP)
    c.label('bolt_king_spec')
    c.emit(struct.pack('<q', BOLT_KING_SPEC))
    c.label('rush_golden')
    c.emit(struct.pack('<q', RUSH_GOLDEN_GUID))
    bolt_rush_switch_data(c)
    for name, maps in (('coop', RUSH_MAPS), ('rush', RUSH_MAPS), ('br', BR_MAPS)):
        c.label(name + '_maps')
        for map_name in maps:
            if len(map_name) >= MAP_NAME_SLOT:
                raise SystemExit(f'nom de carte trop long : {map_name}')
            c.emit(map_name.ljust(MAP_NAME_SLOT, b'\x00'))
    names = ['switch', 'select_map', 'team_counter_flag', 'is_rush']
    names += [f'shortcut_{function:x}' for function, _, _ in ID_SHORTCUTS]
    return (c.build(), {name: at_address + c.labels[name] for name in names})

def display_code(at_address, is_coop, is_rush):
    c = Code(at_address)
    c.emit(a64.RET)
    c.label('is_br')
    c.emit(a64.stp_x_pre(29, 30, a64.SP, -16))
    c.jump('ldrlit', 'bolt_king_spec', 0)
    c.emit(a64.mov_x_zero(1))
    c.call(FIND_ASSET)
    c.jump('cbz', 'not_br', 0)
    c.emit(a64.ldr_x(8, 0, 136))
    c.jump('cbz', 'not_br', 8)
    c.emit(a64.ldr_x(9, 8, 488))
    c.emit(a64.cmp_x_imm(9, 0))
    c.emit(struct.pack('<I', 446629856))
    c.emit(a64.ldp_x_post(29, 30, a64.SP, 16))
    c.emit(a64.RET)
    c.label('not_br')
    c.emit(a64.movz_w(0, 0))
    c.emit(a64.ldp_x_post(29, 30, a64.SP, 16))
    c.emit(a64.RET)
    c.label('explain_spec')
    c.emit(a64.stp_x_pre(29, 30, a64.SP, -48))
    c.emit(a64.stp_x(0, 1, a64.SP, 16))
    c.emit(a64.str_x(2, a64.SP, 32))
    c.call(is_coop)
    c.emit(a64_ldst(STORES[4], 4, 0, a64.SP, 40))
    c.call(is_rush)
    c.emit(a64_ldst(STORES[4], 4, 0, a64.SP, 44))
    c.jump('bl', 'is_br')
    c.emit(a64.mov_w(11, 0))
    c.emit(a64_ldst(LOADS[4], 4, 9, a64.SP, 40))
    c.emit(a64_ldst(LOADS[4], 4, 10, a64.SP, 44))
    c.emit(a64.ldp_x(0, 1, a64.SP, 16))
    c.emit(a64.ldr_x(2, a64.SP, 32))
    c.emit(a64.ldp_x_post(29, 30, a64.SP, 48))
    for flag, played, shown in ((9, 3, BOLT_RUSH_GAME_MODE), (10, 3, RUSH_GAME_MODE), (11, ELIMINATION_GAME_MODE, BR_GAME_MODE)):
        c.jump('cbzw', f'explain_next_{flag}', flag)
        c.emit(a64.cmp_w_imm(1, played))
        c.jump('b.ne', 'explain_call')
        c.emit(a64.movz_w(1, shown))
        c.jump('b', 'explain_call')
        c.label(f'explain_next_{flag}')
    c.label('explain_call')
    c.emit(a64.b(c.here(), GET_GAME_MODE_SPEC_ASSET))
    c.label('title_key')
    c.emit(a64.ldr_x(1, 19, 40))
    c.jump('cbz', 'title_done', 1)
    c.emit(a64.ldr_w(9, 1, 16))
    for kind, key in ((1, TITLE_BOLT_KING), (2, TITLE_ELIMINATION)):
        c.emit(a64.cmp_w_imm(9, len(key)))
        c.jump('b.ne', f'title_not_{kind}')
        c.emit(struct.pack('<I', 2432696320 | 20 << 10 | 1 << 5 | 10))
        c.jump('adr', f'title_utf16_{kind}', 11)
        c.emit(a64.movz_w(12, len(key) // 2))
        c.label(f'title_loop_{kind}')
        c.emit(struct.pack('<I', 3091219456 | 10 << 5 | 13))
        c.emit(struct.pack('<I', 3091219456 | 11 << 5 | 14))
        c.emit(a64.cmp_w(13, 14))
        c.jump('b.ne', f'title_not_{kind}')
        c.emit(struct.pack('<I', 1895826432 | 12 << 5 | 12))
        c.jump('b.ne', f'title_loop_{kind}')
        c.emit(a64.movz_w(15, kind))
        c.jump('b', 'title_match')
        c.label(f'title_not_{kind}')
    c.label('title_done')
    c.emit(a64.RET)
    c.label('title_match')
    c.emit(a64.stp_x_pre(29, 30, a64.SP, -48))
    c.emit(a64.stp_x(0, 1, a64.SP, 16))
    c.emit(a64.str_x(15, a64.SP, 32))
    c.emit(bytes.fromhex('e00313aa'))
    c.emit(a64.mov_x_zero(1))
    c.call(GET_GAME_OBJECT)
    c.jump('cbz', 'title_keep', 0)
    c.emit(a64.mov_x_zero(1))
    c.call(OBJECT_GET_NAME)
    c.jump('cbz', 'title_keep', 0)
    c.emit(a64.str_x(0, a64.SP, 40))
    c.jump('adr', 'title_object', 0)
    c.call(BUILD['string_new'])
    c.emit(bytes.fromhex('e10300aa'))
    c.emit(a64.ldr_x(0, a64.SP, 40))
    c.emit(a64.mov_x_zero(2))
    c.call(STRING_EQUALS)
    c.jump('cbzw', 'title_keep', 0)
    c.emit(a64.ldr_x(15, a64.SP, 32))
    c.emit(a64.cmp_w_imm(15, 1))
    c.jump('b.ne', 'title_elimination')
    c.call(is_coop)
    c.jump('cbzw', 'title_not_coop', 0)
    c.jump('adr', 'title_coop', 0)
    c.jump('b', 'title_new')
    c.label('title_not_coop')
    c.call(is_rush)
    c.jump('cbzw', 'title_keep', 0)
    c.jump('adr', 'title_rush', 0)
    c.jump('b', 'title_new')
    c.label('title_elimination')
    c.jump('bl', 'is_br')
    c.jump('cbzw', 'title_keep', 0)
    c.jump('adr', 'title_br', 0)
    c.label('title_new')
    c.call(BUILD['string_new'])
    c.emit(bytes.fromhex('e10300aa'))
    c.emit(a64.ldr_x(0, a64.SP, 16))
    c.emit(a64.ldp_x_post(29, 30, a64.SP, 48))
    c.emit(a64.RET)
    c.label('title_keep')
    c.emit(a64.ldp_x(0, 1, a64.SP, 16))
    c.emit(a64.ldp_x_post(29, 30, a64.SP, 48))
    c.emit(a64.RET)
    c.label('br_rank')
    c.emit(a64.stp_x_pre(29, 30, a64.SP, -32))
    c.emit(a64.str_x(8, a64.SP, 16))
    c.jump('bl', 'is_br')
    c.emit(a64.ldr_x(8, a64.SP, 16))
    c.jump('cbzw', 'br_rank_half', 0)
    c.emit(a64.ldp_x_post(29, 30, a64.SP, 32))
    c.emit(a64.cmp_w_imm(22, BR_WINNERS))
    c.emit(a64.RET)
    c.label('br_rank_half')
    c.emit(a64.ldp_x_post(29, 30, a64.SP, 32))
    c.emit(BR_RANK_CMP)
    c.emit(a64.RET)
    while len(c.code) % 8:
        c.emit(a64.NOP)
    c.label('bolt_king_spec')
    c.emit(struct.pack('<q', BOLT_KING_SPEC))
    for kind, key in ((1, TITLE_BOLT_KING), (2, TITLE_ELIMINATION)):
        while len(c.code) % 4:
            c.emit(b'\x00')
        c.label(f'title_utf16_{kind}')
        c.emit(key.encode('utf-16-le'))
    for name, key in (('title_coop', BOLT_RUSH_CARD['name']), ('title_rush', RUSH_CARD['name']), ('title_br', BR_CARD['name']), ('title_object', TITLE_OBJECT)):
        c.label(name)
        c.emit(key.encode() + b'\x00')
    return (c.build(), {name: at_address + c.labels[name] for name in ('explain_spec', 'title_key', 'br_rank')})
WEAPON_CODE = 67916132
WEAPON_CODE_END = WEAPON_CODE + 1656
ARENA_MAP_GUID = 3380846735053013127
POWERUP_START_CALL = 129778204
POWERUP_START = 130611340
OVERHEALTH_TYPE = 1
FRAME_GET_RNG = 130444020
RNG_NEXT = 128490436
RANDOM_WEAPON_GIVE = 129773692
PREWARM_CALL = 130016324
LOADOUT_PREWARM_WEAPON = 130016444
WEAPON_AMMO_INIT = 129918240
RESET_RELOAD_STORE = 130437032
START_RELOAD = 130436768
UPDATE_RELOADING = 129915640
GET_WEAPON_MAX_AMMO = 130077576
WEAPON_CREATED_SIGNAL_CALL = 130066548
WEAPON_ON_CREATED = 130512356
FLAG_MAIN_WEAPON = 456
FLAG_GIVEN_WEAPON = 464
AMMO_MARK = 131073
DEBUG_LOG = 142461444

def br_weapons_code(at_address):
    c = Code(at_address)
    c.emit(a64.RET)

    def mark(register):
        c.emit(struct.pack('<I', 3531603968 | (AMMO_MARK & 65535) << 5 | register))
        c.emit(struct.pack('<I', 4070572032 | AMMO_MARK >> 16 << 5 | register))

    def arena_check(frame, fail):
        c.jump('cbz', fail, frame)
        c.emit(a64.ldr_x(8, frame, 880))
        c.jump('cbz', fail, 8)
        c.emit(a64.ldr_x(8, 8, 24))
        c.jump('ldrlit', 'arena', 9)
        c.emit(a64.cmp_x(8, 9))
        c.jump('b.ne', fail)

    def bk_settings(fail):
        c.jump('ldrlit', 'bolt_king_spec', 0)
        c.emit(a64.mov_x_zero(1))
        c.call(FIND_ASSET)
        c.jump('cbz', fail, 0)
        c.emit(a64.ldr_x(8, 0, 136))
        c.jump('cbz', fail, 8)
    c.label('flag_store')
    c.emit(a64.stp_x_pre(29, 30, a64.SP, -32))
    c.emit(a64.stp_x(0, 1, a64.SP, 16))
    bk_settings('flag_store_done')
    c.emit(a64.ldp_x(9, 10, a64.SP, 16))
    c.emit(struct.pack('<I', 4162873344 | 9 << 16 | 8 << 5 | 10))
    c.label('flag_store_done')
    c.emit(a64.ldp_x_post(29, 30, a64.SP, 32))
    c.emit(a64.RET)
    c.label('flag_load')
    c.emit(a64.stp_x_pre(29, 30, a64.SP, -32))
    c.emit(a64.str_x(0, a64.SP, 16))
    bk_settings('flag_load_zero')
    c.emit(a64.ldr_x(9, a64.SP, 16))
    c.emit(struct.pack('<I', 4167067648 | 9 << 16 | 8 << 5 | 0))
    c.emit(a64.ldp_x_post(29, 30, a64.SP, 32))
    c.emit(a64.RET)
    c.label('flag_load_zero')
    c.emit(a64.mov_x_zero(0))
    c.emit(a64.ldp_x_post(29, 30, a64.SP, 32))
    c.emit(a64.RET)
    c.label('br_powerup')
    c.emit(a64.stp_x_pre(29, 30, a64.SP, -64))
    c.emit(a64.stp_x(0, 1, a64.SP, 16))
    c.emit(a64.stp_x(2, 3, a64.SP, 32))
    arena_check(1, 'powerup_original')
    c.emit(a64.ldr_x(8, 0, 0))
    c.emit(a64.ldp_x(9, 1, 8, 408))
    c.emit(struct.pack('<I', 3594453280))
    c.emit(a64.cmp_w_imm(0, OVERHEALTH_TYPE))
    c.jump('b.ne', 'powerup_original')
    c.emit(a64.ldr_x(0, a64.SP, 24))
    c.emit(a64.mov_x_zero(1))
    c.call(FRAME_GET_RNG)
    c.emit(a64.movz_w(1, 0) + a64.movz_w(2, 2) + a64.mov_x_zero(3))
    c.call(RNG_NEXT)
    if os.environ.get('RR_JOURNAL'):
        c.emit(a64.str_x(0, a64.SP, 48))
        c.jump('adr', 'log_shield', 0)
        c.call(BUILD['string_new'])
        c.emit(a64.mov_x_zero(1))
        c.call(DEBUG_LOG)
        c.emit(a64.ldr_x(0, a64.SP, 48))
    c.jump('cbzw', 'powerup_original', 0)
    if os.environ.get('RR_JOURNAL'):
        c.jump('adr', 'log_weapon', 0)
        c.call(BUILD['string_new'])
        c.emit(a64.mov_x_zero(1))
        c.call(DEBUG_LOG)
    c.emit(a64.movz_x(0, FLAG_GIVEN_WEAPON) + a64.movz_x(1, 1))
    c.jump('bl', 'flag_store')
    c.emit(a64.mov_x_zero(0))
    c.emit(a64.ldr_x(1, a64.SP, 24))
    c.emit(a64.ldr_x(2, a64.SP, 32))
    c.emit(a64.mov_x_zero(3))
    c.call(RANDOM_WEAPON_GIVE)
    c.emit(a64.movz_x(0, FLAG_GIVEN_WEAPON) + a64.mov_x_zero(1))
    c.jump('bl', 'flag_store')
    c.emit(a64.ldp_x_post(29, 30, a64.SP, 64))
    c.emit(a64.RET)
    c.label('powerup_original')
    c.emit(a64.ldp_x(0, 1, a64.SP, 16))
    c.emit(a64.ldp_x(2, 3, a64.SP, 32))
    c.emit(a64.ldp_x_post(29, 30, a64.SP, 64))
    c.emit(a64.b(c.here(), POWERUP_START))
    c.label('br_prewarm')
    c.jump('cbnzw', 'prewarm_plain', 3)
    arena_check(0, 'prewarm_plain')
    c.emit(a64.stp_x_pre(29, 30, a64.SP, -64))
    c.emit(a64.stp_x(0, 1, a64.SP, 16))
    c.emit(a64.stp_x(2, 3, a64.SP, 32))
    c.emit(a64.str_x(4, a64.SP, 48))
    c.emit(a64.movz_x(0, FLAG_MAIN_WEAPON) + a64.movz_x(1, 1))
    c.jump('bl', 'flag_store')
    c.emit(a64.ldp_x(0, 1, a64.SP, 16))
    c.emit(a64.ldp_x(2, 3, a64.SP, 32))
    c.emit(a64.ldr_x(4, a64.SP, 48))
    c.call(LOADOUT_PREWARM_WEAPON)
    c.emit(a64.movz_x(0, FLAG_MAIN_WEAPON) + a64.mov_x_zero(1))
    c.jump('bl', 'flag_store')
    c.emit(a64.ldp_x_post(29, 30, a64.SP, 64))
    c.emit(a64.RET)
    c.label('prewarm_plain')
    c.emit(a64.b(c.here(), LOADOUT_PREWARM_WEAPON))
    c.label('ammo_init')
    c.emit(a64.stp_x_pre(29, 30, a64.SP, -48))
    c.emit(a64.stp_x(0, 8, a64.SP, 16))
    c.emit(a64.movz_x(0, FLAG_MAIN_WEAPON))
    c.jump('bl', 'flag_load')
    c.jump('cbz', 'ammo_normal', 0)
    mark(9)
    c.emit(a64.str_x(9, 19, 120))
    c.emit(a64.movz_x(0, FLAG_GIVEN_WEAPON))
    c.jump('bl', 'flag_load')
    c.jump('cbz', 'ammo_empty', 0)
    c.emit(bytes.fromhex('e00313aa'))
    c.emit(a64.mov_x_zero(1))
    c.call(GET_WEAPON_MAX_AMMO)
    c.emit(struct.pack('<I', 3103793760))
    c.jump('b', 'ammo_done')
    c.label('ammo_empty')
    c.emit(struct.pack('<I', 3103793791))
    c.jump('b', 'ammo_done')
    c.label('ammo_normal')
    c.emit(a64.ldr_x(0, a64.SP, 16))
    c.emit(struct.pack('<I', 3103793760))
    c.label('ammo_done')
    c.emit(a64.ldp_x(0, 8, a64.SP, 16))
    c.emit(a64.ldp_x_post(29, 30, a64.SP, 48))
    c.emit(a64.RET)
    c.label('created')
    c.emit(a64.ldr_x(9, a64.SP, 64))
    c.jump('cbz', 'created_signal', 9)
    c.emit(a64.ldr_x(10, 9, 120))
    mark(11)
    c.emit(a64.cmp_x(10, 11))
    c.jump('b.ne', 'created_signal')
    c.emit(a64.stp_x_pre(29, 30, a64.SP, -64))
    c.emit(a64.stp_x(0, 1, a64.SP, 16))
    c.emit(a64.stp_x(2, 9, a64.SP, 32))
    c.emit(a64.movz_x(0, FLAG_GIVEN_WEAPON))
    c.jump('bl', 'flag_load')
    c.emit(a64.ldr_x(9, a64.SP, 40))
    c.jump('cbz', 'created_empty', 0)
    c.emit(bytes.fromhex('e00309aa'))
    c.emit(a64.mov_x_zero(1))
    c.call(GET_WEAPON_MAX_AMMO)
    c.emit(a64.ldr_x(9, a64.SP, 40))
    c.emit(struct.pack('<I', 3103793440))
    c.jump('b', 'created_back')
    c.label('created_empty')
    c.emit(struct.pack('<I', 3103793471))
    c.label('created_back')
    c.emit(a64.ldp_x(0, 1, a64.SP, 16))
    c.emit(a64.ldr_x(2, a64.SP, 32))
    c.emit(a64.ldp_x_post(29, 30, a64.SP, 64))
    c.label('created_signal')
    c.emit(a64.b(c.here(), WEAPON_ON_CREATED))
    c.label('reset_store')
    c.emit(a64.ldr_x(9, 20, 120))
    mark(10)
    c.emit(a64.cmp_x(9, 10))
    c.jump('b.eq', 'reset_skip')
    c.emit(struct.pack('<I', 3103793792))
    c.label('reset_skip')
    c.emit(a64.RET)
    for name, register, function, first in (('start_reload', 0, START_RELOAD, 'ff4305d1'), ('update_reloading', 1, UPDATE_RELOADING, 'fe67bca9')):
        c.label(name)
        c.jump('cbz', name + '_original', register)
        c.emit(a64.ldr_x(9, register, 120))
        mark(10)
        c.emit(a64.cmp_x(9, 10))
        c.jump('b.ne', name + '_original')
        c.emit(a64.RET)
        c.label(name + '_original')
        c.emit(bytes.fromhex(first))
        c.emit(a64.b(c.here(), function + 4))
    while len(c.code) % 8:
        c.emit(a64.NOP)
    c.label('arena')
    c.emit(struct.pack('<q', ARENA_MAP_GUID))
    c.label('bolt_king_spec')
    c.emit(struct.pack('<q', BOLT_KING_SPEC))
    c.label('log_shield')
    c.emit(b'RR BR: bonus ramasse, tirage (0 bouclier, 1 arme)\x00')
    c.label('log_weapon')
    c.emit(b'RR BR: arme au hasard donnee\x00')
    names = ('br_powerup', 'br_prewarm', 'ammo_init', 'created', 'reset_store', 'start_reload', 'update_reloading')
    return (c.build(), {name: at_address + c.labels[name] for name in names})
KING_CODE = 67942024 + 8
KING_CODE_END = 67942024 + 2768
KCC_SURFACE_RESET = 129863956
BOLT_COUNT_FINISH = 129627648
TRY_GET_BOLT_KING_SPEC = 129621176
TRY_GET_POINTER = 86997580
GATHERER_CLASS_SLOT = 153007848
POWER_UP_CLASS_SLOT = 153015088
TRY_FIND_ASSET = 82740980
INIT_RGCTX = 63636616
IS_ALIVE = 129762052
ADD_MAX_SPEED = 130351612
TRY_GET_WEAPON_USER = 130023848
SET_SCALE = 129851800
POWER_UP_START = 130611340
POWER_UP_FINISH = 130611976
SET_SHIELD_STATE = 130757268
BACK_AND_FORTH_TIME_SCALE = 129622232
FINISH_GAME_MODE = 129627828
IS_GAME_MODE_FINISHED = 129627676
SET_INVULNERABLE = 129721840
KING_CHASE = 20
KING_TIMER_CALL = 67359724
KING_TIMER_CODE = 72395584
KING_TIMER_END = 72395584 + 1868
KING_TIMER_TARGETS = {'ext_try_get_spec': TRY_GET_BOLT_KING_SPEC, 'ext_set_color': 140937804, 'ext_ceil_to_int': 128387256}
ONE_SECOND = 65536

def w32(value):
    return struct.pack('<I', value)

def cmp_x_one_second(register):
    return w32(4047503391 | 16 << 10 | register << 5)

def king_code(at_address):
    c = Code(at_address)

    def class_method(slot, method_register):
        adrp_ldr(c, 0, slot)
        c.jump('bl', 'rgctx')
        c.emit(w32(2852717536 | method_register))

    def overhealth(entity_register, finish):
        class_method(POWER_UP_CLASS_SLOT, 4)
        c.emit(a64.mov_x_zero(9))
        c.emit(a64.str_x(9, a64.SP, 104))
        c.emit(bytes.fromhex('e00313aa'))
        c.emit(a64.ldr_x(1, 22, 536))
        c.emit(a64.movz_w(2, 1))
        c.emit(w32(2432696320 | 104 << 10 | 31 << 5 | 3))
        c.call(TRY_FIND_ASSET)
        label = f'no_overhealth_{len(c.code)}'
        c.jump('cbzw', label, 0)
        c.emit(a64.ldr_x(0, a64.SP, 104))
        c.jump('cbz', label, 0)
        c.emit(bytes.fromhex('e10313aa'))
        c.emit(w32(2852127714 | entity_register << 16))
        c.emit(a64.mov_x_zero(3))
        if finish:
            c.emit(a64.mov_x_zero(4))
            c.call(POWER_UP_FINISH)
        else:
            c.call(POWER_UP_START)
        c.label(label)

    def damage(entity_register, king):
        c.emit(a64.mov_x_zero(9))
        c.emit(a64.str_x(9, a64.SP, 112))
        c.emit(bytes.fromhex('e00313aa'))
        c.emit(w32(2852127713 | entity_register << 16))
        c.emit(w32(2432696320 | 112 << 10 | 31 << 5 | 2))
        c.emit(a64.mov_x_zero(3))
        c.call(TRY_GET_WEAPON_USER)
        label = f'no_weapon_user_{len(c.code)}'
        c.jump('cbzw', label, 0)
        c.emit(a64.ldr_x(9, a64.SP, 112))
        c.jump('cbz', label, 9)
        c.emit(a64.ldr_x(10, 9, 96))
        if king:
            c.emit(a64.ldr_x(11, 22, 512))
            c.emit(w32(2601221450))
            c.emit(w32(2471558474))
        c.emit(a64.str_x(10, 9, 48))
        c.label(label)

    def speed(value_offset):
        c.emit(bytes.fromhex('e00315aa'))
        c.emit(bytes.fromhex('e10313aa'))
        c.emit(a64.movz_w(2, KING_CHASE))
        c.emit(a64.ldr_x(3, 22, value_offset))
        c.emit(a64.movz_x(4, 16384))
        c.emit(a64.movz_w(5, 1))
        c.emit(a64.mov_x_zero(6))
        c.call(ADD_MAX_SPEED)

    def scale(entity_register, from_spec):
        c.emit(bytes.fromhex('e00313aa'))
        c.emit(w32(2852127713 | entity_register << 16))
        if from_spec:
            c.emit(a64.ldr_x(2, 22, 520))
        else:
            c.emit(w32(3533701154))
        c.emit(a64.mov_x_zero(3))
        c.call(SET_SCALE)
    journal = bool(os.environ.get('RR_JOURNAL'))

    def log(label):
        if journal:
            c.jump('adr', label, 0)
            c.call(BUILD['string_new'])
            c.emit(a64.mov_x_zero(1))
            c.call(DEBUG_LOG)

    def is_alive(entity_register):
        c.emit(bytes.fromhex('e00313aa'))
        c.emit(w32(2852127713 | entity_register << 16))
        c.emit(a64.mov_x_zero(2))
        c.call(IS_ALIVE)
    c.label('rgctx')
    c.emit(a64.stp_x_pre(29, 30, a64.SP, -32))
    c.emit(a64.str_x(0, a64.SP, 16))
    c.emit(a64.ldr_x(9, 0, 0))
    c.emit(bytes.fromhex('2a014092'))
    c.jump('cbz', 'rgctx_slot_ready', 10)
    c.call(INIT_METADATA)
    c.label('rgctx_slot_ready')
    c.emit(a64.ldr_x(0, a64.SP, 16))
    c.emit(a64.ldr_x(10, 0, 0))
    c.emit(a64.ldr_x(8, 10, 56))
    c.jump('cbnzx', 'rgctx_ready', 8)
    c.emit(a64.str_x(10, a64.SP, 24))
    c.emit(bytes.fromhex('e0030aaa'))
    c.call(INIT_RGCTX)
    c.emit(a64.ldr_x(10, a64.SP, 24))
    c.emit(a64.ldr_x(8, 10, 56))
    c.label('rgctx_ready')
    c.emit(a64.ldr_x(9, 8, 8))
    c.emit(a64.ldp_x_post(29, 30, a64.SP, 32))
    c.emit(a64.RET)
    c.label('skip')
    c.emit(a64.ldr_x(9, 8, 488))
    c.emit(cmp_x_one_second(9))
    c.jump('b.lt', 'skip_normal')
    c.emit(w32(2432705502))
    c.emit(a64.RET)
    c.label('skip_normal')
    c.emit(bytes.fromhex('01ed40f9'))
    c.emit(a64.RET)
    c.label('tick')
    c.emit(a64.stp_x_pre(29, 30, a64.SP, -128))
    c.emit(a64.stp_x(19, 20, a64.SP, 16))
    c.emit(a64.stp_x(21, 22, a64.SP, 32))
    c.emit(a64.stp_x(23, 24, a64.SP, 48))
    c.emit(a64.stp_x(0, 1, a64.SP, 64))
    c.emit(a64.str_x(2, a64.SP, 80))
    c.emit(bytes.fromhex('f30301aa'))
    c.emit(a64.ldp_x(20, 21, 2, 0))
    c.jump('cbz', 'done', 21)
    c.jump('cbz', 'done', 19)
    c.emit(a64.mov_x_zero(9))
    c.emit(a64.str_x(9, a64.SP, 88))
    c.emit(bytes.fromhex('e00313aa'))
    c.emit(w32(2432696320 | 88 << 10 | 31 << 5 | 1))
    c.emit(a64.mov_x_zero(2))
    c.call(TRY_GET_BOLT_KING_SPEC)
    c.jump('cbzw', 'done', 0)
    c.emit(a64.ldr_x(22, a64.SP, 88))
    c.jump('cbz', 'done', 22)
    c.emit(a64.ldr_x(9, 22, 488))
    c.emit(cmp_x_one_second(9))
    c.jump('b.lt', 'done')
    c.emit(a64.ldr_w(9, 19, 28))
    c.emit(a64.ldr_w(10, 22, 468))
    c.emit(w32(1795817791))
    c.emit(w32(446674923))
    c.emit(w32(3103816683))
    c.jump('b.lt', 'state_known')
    c.emit(w32(3103785673 | 468 // 4 << 10))
    c.label('state_known')
    class_method(GATHERER_CLASS_SLOT, 3)
    c.emit(a64.mov_x_zero(9))
    c.emit(a64.str_x(9, a64.SP, 96))
    c.emit(a64.ldr_x(0, 19, 160))
    c.jump('cbz', 'done', 0)
    c.emit(bytes.fromhex('e10314aa'))
    c.emit(w32(2432696320 | 96 << 10 | 31 << 5 | 2))
    c.call(TRY_GET_POINTER)
    c.jump('cbzw', 'done', 0)
    c.emit(a64.ldr_x(23, a64.SP, 96))
    c.jump('cbz', 'done', 23)
    c.emit(a64.ldr_x(24, 22, 456))
    c.jump('cbz', 'no_king', 24)
    c.emit(a64.ldr_w(9, a64.SP, 120))
    c.jump('cbnzw', 'have_king', 9)
    c.emit(a64.ldr_w(9, 19, 28))
    c.emit(a64.ldr_w(10, 22, 464))
    c.emit(w32(1795817791))
    c.jump('b.lt', 'done')
    c.jump('b', 'have_king')
    c.label('no_king')
    c.emit(a64.ldr_w(9, a64.SP, 120))
    c.jump('cbzw', 'done', 9)
    c.emit(a64.ldr_w(9, 23, 0))
    c.emit(a64.cmp_w_imm(9, KING_SCORE))
    c.jump('b.lt', 'done')
    is_alive(20)
    c.jump('cbzw', 'done', 0)
    c.emit(a64.str_x(20, 22, 456))
    c.emit(a64.ldr_w(9, 19, 28))
    c.emit(w32(3103785673 | 464 // 4 << 10))
    scale(20, True)
    overhealth(20, False)
    c.emit(bytes.fromhex('e00313aa'))
    c.emit(bytes.fromhex('e10314aa'))
    c.emit(a64.movz_w(2, 2))
    c.emit(a64.mov_x_zero(3))
    c.call(SET_SHIELD_STATE)
    c.emit(bytes.fromhex('e00313aa'))
    c.emit(a64.ldr_x(1, 22, 96))
    c.emit(a64.ldr_x(2, 22, 88))
    c.emit(w32(2470575170))
    c.emit(a64.mov_x_zero(3))
    c.call(BACK_AND_FORTH_TIME_SCALE)
    log('log_new')
    c.emit(bytes.fromhex('f80314aa'))
    c.label('have_king')
    is_alive(24)
    c.jump('cbnzw', 'king_alive', 0)
    c.emit(a64.ldr_w(9, a64.SP, 120))
    c.jump('cbzw', 'done', 9)
    scale(24, False)
    damage(24, False)
    overhealth(24, True)
    c.emit(w32(4177526784 | 456 // 8 << 10 | 22 << 5 | 31))
    log('log_fallen')
    c.jump('b', 'done')
    c.label('king_alive')
    c.emit(a64.cmp_x(24, 20))
    c.jump('b.ne', 'chaser')
    speed(496)
    damage(20, True)
    c.emit(a64.ldr_x(8, 19, 0))
    c.emit(a64.ldr_x(9, 8, 584))
    c.emit(a64.ldr_x(1, 8, 592))
    c.emit(bytes.fromhex('e00313aa'))
    c.emit(w32(3594453280))
    c.emit(a64.ldr_w(9, 19, 28))
    c.emit(a64.ldr_w(10, 22, 464))
    c.emit(w32(1258946857))
    c.emit(w32(2470477097))
    c.emit(w32(2601090057))
    c.emit(a64.ldr_x(10, 22, 488))
    c.emit(a64.cmp_x(9, 10))
    c.jump('b.lt', 'done')
    c.emit(w32(3405775145))
    c.emit(a64.cmp_x(9, 10))
    c.jump('b.ge', 'won_again')
    c.emit(a64.ldr_w(9, 23, 0))
    c.emit(w32(285213993))
    c.emit(w32(3103785705))
    c.emit(bytes.fromhex('e00313aa'))
    c.emit(bytes.fromhex('e10314aa'))
    c.emit(a64.ldr_x(2, 22, 472))
    c.emit(a64.movz_w(3, 1))
    c.emit(a64.mov_x_zero(4))
    c.call(SET_INVULNERABLE)
    c.emit(bytes.fromhex('e00313aa'))
    c.emit(a64.ldr_x(1, 22, 472))
    c.emit(a64.mov_x_zero(2))
    c.call(FINISH_GAME_MODE)
    log('log_won')
    if journal:
        c.emit(bytes.fromhex('e00313aa'))
        c.emit(a64.mov_x_zero(1))
        c.call(IS_GAME_MODE_FINISHED)
        c.jump('cbnzw', 'finished_yes', 0)
        log('log_not_finished')
        c.jump('b', 'done')
        c.label('finished_yes')
        log('log_finished')
    c.jump('b', 'done')
    c.label('won_again')
    c.emit(bytes.fromhex('e00313aa'))
    c.emit(a64.ldr_x(1, 22, 472))
    c.emit(a64.mov_x_zero(2))
    c.call(FINISH_GAME_MODE)
    c.jump('b', 'done')
    c.label('chaser')
    speed(544)
    c.label('done')
    c.emit(a64.ldp_x(0, 1, a64.SP, 64))
    c.emit(a64.ldr_x(2, a64.SP, 80))
    c.emit(a64.ldp_x(23, 24, a64.SP, 48))
    c.emit(a64.ldp_x(21, 22, a64.SP, 32))
    c.emit(a64.ldp_x(19, 20, a64.SP, 16))
    c.emit(a64.ldp_x_post(29, 30, a64.SP, 128))
    c.emit(bytes.fromhex('480440f9'))
    c.emit(a64.b(c.here(), KCC_SURFACE_RESET + 4))
    if journal:
        for label, text in (('log_new', b'RR roi: nouveau roi'), ('log_fallen', b'RR roi: roi tombe'), ('log_won', b'RR roi: le roi gagne'), ('log_finished', b'RR roi: fin prevue'), ('log_not_finished', b'RR roi: fin PAS prevue')):
            c.label(label)
            c.emit(text + bytes(4 - len(text) % 4))
    return (c.build(), {name: at_address + c.labels[name] for name in ('skip', 'tick')})
CROWN_SCORE_LOAD = 67742824

def crown_code(at_address):
    c = Code(at_address)
    c.emit(w32(3108102154))
    c.emit(a64.ldr_x(12, 0, 488))
    c.emit(cmp_x_one_second(12))
    c.jump('b.lt', 'out')
    c.emit(w32(2034246636))
    c.emit(a64.cmp_w_imm(12, 1))
    c.jump('b.eq', 'out')
    c.emit(w32(289414442))
    c.label('out')
    c.emit(a64.RET)
    return c.build()
DIFFICULTY_MEDALS = {'0': 0, '1': 100, '2': 400, '3': 1100}
ULTRA_BOT_POWER = 15000
ULTRA_TALENT_LEVEL = 10

def difficulty_code(at_address):
    c = Code(at_address)
    for name, first, function in (('pve', 'fe4fbfa9', BUILD['difficulty'][0]), ('power', 'ffc300d1', BUILD['difficulty'][1])):
        c.label(name)
        c.emit(a64.stp_x_pre(29, 30, a64.SP, -32))
        c.emit(a64.stp_x(0, 3, a64.SP, 16))
        c.jump('bl', 'choose')
        if name == 'power':
            c.emit(a64.cmp_w_imm(0, 3))
            c.jump('b.eq', 'ultra_power')
        c.emit(a64.ldp_x(0, 3, a64.SP, 16))
        c.emit(a64.ldp_x_post(29, 30, a64.SP, 32))
        c.emit(bytes.fromhex(first))
        c.emit(a64.b(c.here(), function + 4))
    c.label('ultra_power')
    c.emit(a64.ldp_x(0, 3, a64.SP, 16))
    c.emit(a64.ldp_x_post(29, 30, a64.SP, 32))
    c.emit(a64.movz_w(0, ULTRA_BOT_POWER))
    c.emit(a64.RET)
    c.label('choose')
    c.emit(a64.stp_x_pre(29, 30, a64.SP, -16))
    c.jump('bl', 'level')
    c.jump('adr', 'medals', 8)
    c.emit(w32(3093321985))
    c.emit(a64.movz_w(2, 0))
    c.emit(a64.ldp_x_post(29, 30, a64.SP, 16))
    c.emit(a64.RET)
    c.label('level')
    c.emit(a64.stp_x_pre(29, 30, a64.SP, -16))
    c.jump('adr', 'key', 0)
    c.call(BUILD['string_new'])
    c.emit(a64.mov_x_zero(1))
    c.call(BUILD['prefs_get_string'])
    c.emit(a64.movz_w(9, 1))
    c.jump('cbz', 'level_done', 0)
    c.emit(a64.ldr_w(8, 0, 16))
    c.jump('cbzw', 'level_done', 8)
    c.emit(w32(2034247688))
    c.emit(w32(1359003912))
    c.emit(a64.cmp_w_imm(8, len(DIFFICULTY_MEDALS)))
    c.jump('b.hs', 'level_done')
    c.emit(a64.mov_w(9, 8))
    c.label('level_done')
    c.emit(a64.mov_w(0, 9))
    c.emit(a64.ldp_x_post(29, 30, a64.SP, 16))
    c.emit(a64.RET)
    if 'difficulty_row_code' in BUILD:
        row = BUILD['difficulty_row_code']

        def is_row(fail):
            c.emit(a64.ldr_x(9, 19, 48))
            c.jump('cbz', fail, 9)
            c.emit(a64.ldr_w(10, 9, 24))
            c.jump('cbzw', fail, 10)
            c.emit(a64.ldr_x(9, 9, 32))
            c.jump('cbz', fail, 9)
            c.emit(a64.ldr_w(10, 9, 16))
            c.emit(a64.cmp_w_imm(10, 2))
            c.jump('b.lt', fail)
            c.emit(w32(2034247978))
            c.emit(a64.cmp_w_imm(10, ord('R')))
            c.jump('b.ne', fail)
            c.emit(w32(2034249002))
            c.emit(a64.cmp_w_imm(10, ord('R')))
            c.jump('b.ne', fail)
        c.label('row_get')
        is_row('fov_get')
        c.emit(a64.stp_x_pre(29, 30, a64.SP, -16))
        c.jump('bl', 'level')
        c.emit(a64.ldp_x_post(29, 30, a64.SP, 16))
        c.emit(a64.RET)
        c.label('fov_get')
        c.emit(a64.b(c.here(), row['get']))
        c.label('row_set')
        is_row('fov_set')
        c.jump('adr', 'digits', 8)
        c.emit(w32(2334147840))
        c.call(BUILD['string_new'])
        c.emit(w32(2852127733))
        c.jump('adr', 'key', 0)
        c.call(BUILD['string_new'])
        c.emit(w32(2853503969))
        c.emit(a64.mov_x_zero(2))
        c.call(row['set_string'])
        c.emit(a64.mov_x_zero(0))
        c.call(row['save'])
        c.emit(a64.b(c.here(), row['done']))
        c.label('fov_set')
        c.emit(a64.b(c.here(), row['set']))
        c.label('bot_talent')
        c.emit(a64.ldr_x(9, 29, BUILD['ultra_bots']['runtime_config']))
        c.emit(a64.movz_w(10, 0))
        c.jump('cbz', 'talent_done', 9)
        c.emit(a64.ldr_w(11, 9, BUILD['ultra_bots']['bots_power']))
        c.emit(a64.movz_w(12, ULTRA_BOT_POWER))
        c.emit(a64.cmp_w(11, 12))
        c.jump('b.lt', 'talent_done')
        c.emit(a64.movz_w(10, ULTRA_TALENT_LEVEL))
        c.label('talent_done')
        c.emit(w32(3103794154))
        c.emit(a64.RET)
        c.label('digits')
        c.emit(b''.join((digit.encode() + b'\x00' for digit in DIFFICULTY_MEDALS)))
    c.label('key')
    c.emit(b'rr_difficulte\x00\x00\x00')
    c.label('medals')
    c.emit(struct.pack(f'<{len(DIFFICULTY_MEDALS)}I', *DIFFICULTY_MEDALS.values()))
    names = ('pve', 'power') + (('row_get', 'row_set', 'bot_talent') if 'difficulty_row_code' in BUILD else ())
    return (c.build(), {name: at_address + c.labels[name] for name in names})
PHASES_CODE = 72330704 + 3072
PHASES_CODE_END = 72330704 + 4864
PHASE_TICK_HOOK = 129750780
PHASE_SPAWNER_HOOK = 130898780
PHASE_SPAWNED_CALL = 130900140
PHASE_KILL_HOOK = 129622224
PHASE_TARGETS = {'ext_try_get_bolt_king_spec': TRY_GET_BOLT_KING_SPEC, 'ext_set_spawners_enabled': 130895384, 'ext_get_rng': 130444020, 'ext_rng_next': 128490436, 'ext_create_dynamic': 129888456, 'ext_try_get_handler': 129625380, 'ext_has_alive': 130231032, 'ext_debug_log': DEBUG_LOG, 'ext_on_spawned': 130482004, 'ext_has_type': 130872780, 'ext_set_need_update': 129789380, 'ext_back_tick': PHASE_TICK_HOOK + 4, 'ext_back_spawner': PHASE_SPAWNER_HOOK + 4}
ASSEMBLED_CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'code_assemble.json')

def assemble_source(name):
    import hashlib
    import shutil
    source = os.path.join(os.path.dirname(os.path.abspath(__file__)), name)
    digest = hashlib.sha256(open(source, 'rb').read()).hexdigest()
    cache = json.load(open(ASSEMBLED_CACHE)) if os.path.exists(ASSEMBLED_CACHE) else {}
    if not shutil.which('clang') or os.environ.get('RR_SANS_CLANG') == '1':
        entry = cache.get(name)
        if not entry or entry['sha256'] != digest:
            raise SystemExit(f'{name} : code assemble absent ou perime (construire une fois sur le Mac)')
        return (bytes.fromhex(entry['code']), [tuple(use) for use in entry['uses']], entry['labels'])
    code, uses, labels = assemble_with_clang(source)
    cache[name] = {'sha256': digest, 'code': code.hex(), 'uses': uses, 'labels': labels}
    with open(ASSEMBLED_CACHE, 'w') as handle:
        json.dump(cache, handle, indent=1, sort_keys=True)
    return (code, uses, labels)

def assemble_with_clang(source):
    import subprocess
    import tempfile
    obj = os.path.join(tempfile.mkdtemp(), 'code.o')
    subprocess.run(['clang', '-c', '-target', 'arm64-apple-macos', source, '-o', obj], check=True)
    lines = subprocess.run(['otool', '-s', '__TEXT', '__text', obj], capture_output=True, text=True, check=True).stdout
    code = b''.join((bytes.fromhex(word)[::-1] for line in lines.splitlines()[2:] for word in line.split()[1:]))
    relocs = subprocess.run(['objdump', '-d', '-r', obj], capture_output=True, text=True, check=True).stdout
    uses = []
    for line in relocs.splitlines():
        found = re.match('\\s*([0-9a-f]+):\\s+ARM64_RELOC_(\\w+)\\s+(\\S+)', line)
        if found and found.group(2) != 'PAGEOFF12':
            uses.append((int(found.group(1), 16), found.group(3)))
    labels = {}
    for line in subprocess.run(['nm', obj], capture_output=True, text=True, check=True).stdout.splitlines():
        parts = line.split()
        if len(parts) == 3:
            labels[parts[2]] = int(parts[0], 16)
    return (code, uses, labels)

def patch_bolt_rush_phases(data):
    at_address = PHASES_CODE
    code, uses, labels = assemble_source('phases_bolt_rush.s')
    targets = dict(PHASE_TARGETS, ext_string_new=BUILD['string_new'])
    if at_address + len(code) > PHASES_CODE_END:
        raise SystemExit('plus de place pour les phases de Bolt Rush')
    code = bytearray(code)
    if os.environ.get('RR_JOURNAL'):
        code[labels['journal']:labels['journal'] + 4] = struct.pack('<I', 1)
    place_assembled(data, at_address, bytes(code), uses, targets, None)
    at(data, PHASE_TICK_HOOK, bytes.fromhex('ff0301d1'), a64.b(PHASE_TICK_HOOK, at_address + labels['_phase_tick']))
    at(data, PHASE_SPAWNER_HOOK, bytes.fromhex('ffc306d1'), a64.b(PHASE_SPAWNER_HOOK, at_address + labels['_phase_spawner']))
    at(data, PHASE_SPAWNED_CALL, a64.bl(PHASE_SPAWNED_CALL, PHASE_TARGETS['ext_on_spawned']), a64.bl(PHASE_SPAWNED_CALL, at_address + labels['_phase_spawned']))
    at(data, PHASE_KILL_HOOK, bytes.fromhex('e2031faa'), a64.b(PHASE_KILL_HOOK, at_address + labels['_phase_kill']))
ACTOR_VIEW_UPDATE = 65870908
UPDATE_SCALE = 65804912
VIEW_CHARACTER = 80
APPLIED_KING = 281

def actor_growth_code(at_address):
    c = Code(at_address)
    c.emit(a64.stp_x_pre(29, 30, a64.SP, -64))
    c.emit(a64.stp_x(19, 20, a64.SP, 16))
    c.emit(a64.stp_x(0, 1, a64.SP, 32))
    c.emit(bytes.fromhex('f30300aa'))
    c.emit(a64.ldr_x(0, 19, VIEW_CHARACTER))
    c.jump('cbz', 'done', 0)
    c.jump('ldrlit', 'spec_guid', 0)
    c.emit(a64.mov_x_zero(1))
    c.call(FIND_ASSET)
    c.jump('cbz', 'done', 0)
    c.emit(a64.ldr_x(20, 0, 136))
    c.jump('cbz', 'done', 20)
    c.emit(a64.movz_w(10, 0))
    c.emit(a64.ldr_x(9, 20, 488))
    c.emit(cmp_x_one_second(9))
    c.jump('b.lt', 'compare')
    c.emit(a64.ldr_x(8, 19, 40))
    c.jump('cbz', 'compare', 8)
    c.emit(a64.ldr_x(8, 8, 40))
    c.emit(a64.ldr_x(9, 20, 456))
    c.emit(a64.cmp_x(8, 9))
    c.emit(w32(446633962))
    c.label('compare')
    c.emit(a64.ldr_x(0, 19, VIEW_CHARACTER))
    c.emit(bytes.fromhex('08644439'))
    c.emit(bytes.fromhex('1f010a6b'))
    c.jump('b.eq', 'done')
    c.emit(bytes.fromhex('0a640439'))
    c.emit(a64.ldr_x(9, 20, 520))
    c.emit(w32(2653028641))
    c.emit(w32(506335234))
    c.emit(w32(1386803211))
    c.emit(w32(505872739))
    c.emit(w32(505616417))
    label = 'grow'
    c.jump('cbnzw', label, 10)
    c.emit(w32(505485377))
    c.label(label)
    c.emit(bytes.fromhex('00d041bd'))
    c.emit(bytes.fromhex('0008211e'))
    c.emit(bytes.fromhex('00d001bd'))
    c.emit(bytes.fromhex('00d441bd'))
    c.emit(bytes.fromhex('01d841bd'))
    c.emit(bytes.fromhex('02dc41bd'))
    c.emit(a64.mov_x_zero(1))
    c.call(UPDATE_SCALE)
    c.label('done')
    c.emit(a64.ldp_x(0, 1, a64.SP, 32))
    c.emit(a64.ldp_x(19, 20, a64.SP, 16))
    c.emit(a64.ldp_x_post(29, 30, a64.SP, 64))
    c.emit(bytes.fromhex('ea0f19fc'))
    c.emit(a64.b(c.here(), ACTOR_VIEW_UPDATE + 4))
    while len(c.code) % 8:
        c.emit(a64.NOP)
    c.label('spec_guid')
    c.emit(struct.pack('<q', BOLT_KING_SPEC))
    return c.build()
SETUP_POWER_FLAG = 130604400
POWER_LEVEL_SIM_STORE = 129706692
POWER_VERIFIED_CHECK = 129706588

def power_debug_code(at_address):
    c = Code(at_address)

    def log(label, digit_register, index):
        c.jump('adr', label, 9)
        c.emit(a64.ldp_x(10, 11, 9, 0) + a64.stp_x(10, 11, a64.SP, 16))
        c.emit(a64.ldp_x(10, 11, 9, 16) + a64.stp_x(10, 11, a64.SP, 32))
        c.emit(struct.pack('<I', 285212672 | 48 << 10 | digit_register << 5 | 10))
        c.emit(struct.pack('<I', 956301312 | 16 + index << 10 | 31 << 5 | 10))
        c.emit(struct.pack('<I', 2432696320 | 16 << 10 | 31 << 5 | 0))
        c.call(BUILD['string_new'])
        c.emit(a64.mov_x_zero(1))
        c.call(DEBUG_LOG)
    c.label('setup_log')
    c.emit(a64.stp_x_pre(29, 30, a64.SP, -64))
    c.emit(bytes.fromhex('a8624639'))
    c.emit(a64.str_x(8, a64.SP, 48) if hasattr(a64, 'str_x') else bytes.fromhex('e81b00f9'))
    log('msg_setup', 8, 20)
    c.emit(bytes.fromhex('e81b40f9'))
    c.emit(a64.ldp_x_post(29, 30, a64.SP, 64))
    c.emit(a64.RET)
    c.label('sim_log')
    c.emit(bytes.fromhex('00010079'))
    c.emit(a64.stp_x_pre(29, 30, a64.SP, -64))
    c.emit(bytes.fromhex('e01b00f9'))
    log('msg_sim', 0, 24)
    c.emit(bytes.fromhex('e01b40f9'))
    c.emit(a64.ldp_x_post(29, 30, a64.SP, 64))
    c.emit(a64.RET)
    c.label('msg_setup')
    c.emit(b'RR puissance prevue 0'.ljust(32, b'\x00'))
    c.label('msg_sim')
    c.emit(b'RR puissance simulation 0'.ljust(32, b'\x00'))
    return (c.build(), {name: at_address + c.labels[name] for name in ('setup_log', 'sim_log')})

def patch_bolt_rush_code(data):
    for host in (67925936, RUSH_CODE, DISPLAY_CODE, WEAPON_CODE):
        at(data, host, bytes(data[host:host + 4]), a64.RET)
    battle, entries = coop_battle_code(COOP_BATTLE_CODE)
    if COOP_BATTLE_CODE + len(battle) > 67925936 + 1456:
        raise SystemExit('plus de place pour le code de partie Bolt Rush')
    at(data, COOP_BATTLE_CODE, bytes(data[COOP_BATTLE_CODE:COOP_BATTLE_CODE + len(battle)]), battle)
    at(data, RANKING_COLLECTED_BOLTS_CALL, a64.bl(RANKING_COLLECTED_BOLTS_CALL, GET_COLLECTED_BOLTS), a64.bl(RANKING_COLLECTED_BOLTS_CALL, entries['own_bolts']))
    at(data, TEAM_COUNTER_CHECK, bytes.fromhex('000540b9'), a64.bl(TEAM_COUNTER_CHECK, entries['team_flag']))
    at(data, BATTLE_RESULT_STORE, bytes.fromhex('680200b9'), a64.bl(BATTLE_RESULT_STORE, entries['result']))
    at(data, ROW_DONE_CALL, a64.bl(ROW_DONE_CALL, SET_IS_DEAD), a64.bl(ROW_DONE_CALL, entries['row']))
    for call in TOP_PLAYERS_TEAM_CALLS:
        at(data, call, a64.bl(call, TRY_GET_TEAM_ID), a64.bl(call, entries['team_split']))
    at(data, BIND_PLAYER_CALL, a64.bl(BIND_PLAYER_CALL, BIND_PLAYER), a64.bl(BIND_PLAYER_CALL, entries['item_color']))
    for check in MAX_COUNTER_CHECKS:
        at(data, check, bytes.fromhex('08554079'), a64.bl(check, entries['max_key']))
    at(data, MAX_COUNTER_FORMAT_CALL, a64.bl(MAX_COUNTER_FORMAT_CALL, STRING_FORMAT), a64.bl(MAX_COUNTER_FORMAT_CALL, entries['max_text']))
    code, rush = rush_code(RUSH_CODE)
    if RUSH_CODE + len(code) > RUSH_CODE_END:
        raise SystemExit('plus de place pour le code de Bolt Rush')
    if rush['switch'] != BOLT_RUSH_SWITCH:
        raise SystemExit('aiguillage de Bolt Rush mal place')
    at(data, RUSH_CODE + 4, bytes(data[RUSH_CODE + 4:RUSH_CODE + len(code)]), code[4:])
    shown, display = display_code(DISPLAY_CODE, entries['is_coop'], rush['is_rush'])
    if DISPLAY_CODE + len(shown) > DISPLAY_CODE_END:
        raise SystemExit("plus de place pour l'affichage des nouveaux modes")
    at(data, DISPLAY_CODE + 4, bytes(data[DISPLAY_CODE + 4:DISPLAY_CODE + len(shown)]), shown[4:])
    rush.update(display)
    king_at = KING_CODE
    king, king_entries = king_code(king_at)
    if king_at + len(king) > KING_CODE_END:
        raise SystemExit('plus de place pour le Roi de Bolt Rush')
    grow = actor_growth_code(0)
    grow_at = HERO_RETURN_CODE - len(grow) - 16 & ~15
    grow = actor_growth_code(grow_at)
    if grow_at < EVENTS_CODE + len(events_code(EVENTS_CODE)[0]) + 16:
        raise SystemExit('plus de place pour la taille du Roi')
    at(data, grow_at, bytes(data[grow_at:grow_at + len(grow)]), grow)
    at(data, ACTOR_VIEW_UPDATE, bytes.fromhex('ea0f19fc'), a64.b(ACTOR_VIEW_UPDATE, grow_at))
    at(data, king_at, bytes(data[king_at:king_at + len(king)]), king)
    crown_at = king_at + len(king) + 15 & ~15
    crown = crown_code(crown_at)
    if crown_at + len(crown) > KING_CODE_END:
        raise SystemExit('plus de place pour la couronne')
    at(data, crown_at, bytes(data[crown_at:crown_at + len(crown)]), crown)
    at(data, CROWN_SCORE_LOAD, w32(3108102154), a64.bl(CROWN_SCORE_LOAD, crown_at))
    difficulty_at = crown_at + len(crown) + 15 & ~15
    difficulty = b''
    if 'difficulty' in BUILD:
        difficulty, entries = difficulty_code(difficulty_at)
        if difficulty_at + len(difficulty) > KING_CODE_END:
            raise SystemExit('plus de place pour la difficulte')
        at(data, difficulty_at, bytes(data[difficulty_at:difficulty_at + len(difficulty)]), difficulty)
        pve, power = BUILD['difficulty']
        at(data, pve, bytes.fromhex('fe4fbfa9'), a64.b(pve, entries['pve']))
        at(data, power, bytes.fromhex('ffc300d1'), a64.b(power, entries['power']))
        if 'difficulty_row_code' in BUILD:
            row = BUILD['difficulty_row_code']
            for call in row['get_calls']:
                at(data, call, a64.bl(call, row['get']), a64.bl(call, entries['row_get']))
            at(data, row['set_call'], a64.bl(row['set_call'], row['set']), a64.bl(row['set_call'], entries['row_set']))
            at(data, row['done'], bytes.fromhex('e00313aa'), bytes.fromhex('e00313aa'))
            talent = BUILD['ultra_bots']['talent_store']
            at(data, talent, bytes.fromhex('ff2300b9'), a64.bl(talent, entries['bot_talent']))
    patch_bolt_rush_phases(data)
    at(data, KCC_SURFACE_RESET, bytes.fromhex('480440f9'), a64.b(KCC_SURFACE_RESET, king_entries['tick']))
    at(data, BOLT_COUNT_FINISH, bytes.fromhex('01ed40f9'), a64.bl(BOLT_COUNT_FINISH, king_entries['skip']))
    timer, timer_uses, timer_labels = assemble_source('chrono_roi.s')
    if KING_TIMER_CODE + len(timer) > KING_TIMER_END:
        raise SystemExit('plus de place pour le chrono du Roi')
    place_assembled(data, KING_TIMER_CODE, timer, timer_uses, KING_TIMER_TARGETS, None)
    at(data, KING_TIMER_CALL, a64.bl(KING_TIMER_CALL, KING_TIMER_TARGETS['ext_ceil_to_int']), a64.bl(KING_TIMER_CALL, KING_TIMER_CODE + timer_labels['_kt_timer'] - timer_labels['_kt_start']))
    print(f'chrono du Roi : {len(timer)} octets')
    at(data, POWER_VERIFIED_CHECK, bytes.fromhex('c8030034'), a64.NOP)
    if os.environ.get('RR_DIAG_PUISSANCE') and os.environ.get('RR_JOURNAL'):
        debug_at = difficulty_at + len(difficulty) + 15 & ~15
        debug, hooks = power_debug_code(debug_at)
        if debug_at + len(debug) > KING_CODE_END:
            raise SystemExit('plus de place pour le diagnostic de puissance')
        at(data, debug_at, bytes(data[debug_at:debug_at + len(debug)]), debug)
        at(data, SETUP_POWER_FLAG, bytes.fromhex('a8624639'), a64.bl(SETUP_POWER_FLAG, hooks['setup_log']))
        at(data, POWER_LEVEL_SIM_STORE, bytes.fromhex('00010079'), a64.bl(POWER_LEVEL_SIM_STORE, hooks['sim_log']))
    at(data, SELECT_RANDOM_MAP_CALL, a64.bl(SELECT_RANDOM_MAP_CALL, SELECT_RANDOM_MAP), a64.bl(SELECT_RANDOM_MAP_CALL, rush['select_map']))
    for function, first, _ in ID_SHORTCUTS:
        at(data, function, first, a64.b(function, rush[f'shortcut_{function:x}']))
    for call in EXPLANATION_SPEC_CALLS:
        at(data, call, a64.bl(call, GET_GAME_MODE_SPEC_ASSET), a64.bl(call, rush['explain_spec']))
    at(data, CARD_MODE_ID, bytes.fromhex('182340b9'), bytes.fromhex('f83340b9'))
    at(data, TABLE_ENTRY_ID, bytes.fromhex('082040b9'), bytes.fromhex('e81340b9'))
    at(data, TITLE_KEY_LOAD, bytes.fromhex('611640f9'), a64.bl(TITLE_KEY_LOAD, rush['title_key']))
    at(data, BR_RANK_CHECK, BR_RANK_CMP, a64.bl(BR_RANK_CHECK, rush['br_rank']))
    weapons, hooks = br_weapons_code(WEAPON_CODE)
    if WEAPON_CODE + len(weapons) > WEAPON_CODE_END:
        raise SystemExit('plus de place pour les armes du Battle Royale')
    at(data, WEAPON_CODE + 4, bytes(data[WEAPON_CODE + 4:WEAPON_CODE + len(weapons)]), weapons[4:])
    at(data, POWERUP_START_CALL, a64.bl(POWERUP_START_CALL, POWERUP_START), a64.bl(POWERUP_START_CALL, hooks['br_powerup']))
    at(data, PREWARM_CALL, a64.bl(PREWARM_CALL, LOADOUT_PREWARM_WEAPON), a64.bl(PREWARM_CALL, hooks['br_prewarm']))
    at(data, WEAPON_AMMO_INIT, bytes.fromhex('602200b9'), a64.bl(WEAPON_AMMO_INIT, hooks['ammo_init']))
    at(data, RESET_RELOAD_STORE, bytes.fromhex('802200b9'), a64.bl(RESET_RELOAD_STORE, hooks['reset_store']))
    at(data, WEAPON_CREATED_SIGNAL_CALL, a64.bl(WEAPON_CREATED_SIGNAL_CALL, WEAPON_ON_CREATED), a64.bl(WEAPON_CREATED_SIGNAL_CALL, hooks['created']))
    at(data, START_RELOAD, bytes.fromhex('ff4305d1'), a64.b(START_RELOAD, hooks['start_reload']))
    at(data, UPDATE_RELOADING, bytes.fromhex('fe67bca9'), a64.b(UPDATE_RELOADING, hooks['update_reloading']))
    at(data, 129619716, bytes.fromhex('1f050031'), bytes.fromhex('1f01086b'))
    at(data, TEAM_COUNTER_FLAG, bytes.fromhex('480a00b4'), a64.bl(TEAM_COUNTER_FLAG, rush['team_counter_flag']))
    at(data, 130603664, bytes.fromhex('170100b9'), bytes.fromhex('17290029'))
    at(data, 129706600, bytes.fromhex('480040f9'), bytes.fromhex('480840f9'))
    at(data, 129706620, bytes.fromhex('7d000094'), bytes.fromhex('000140b9'))
    cave = BUILD['free_code'][0] + len(bytes.fromhex(BUILD['free_code'][1]))
    counter = 67351280
    get_collected_bolts = 129707120

    def branch(opcode, source, target):
        return struct.pack('<I', opcode | target - source >> 2 & 67108863)
    code = bytes.fromhex('e07bbfa9') + bytes.fromhex('e00314aa') + bytes.fromhex('e10316aa') + bytes.fromhex('e2031faa') + branch(2483027968, cave + 16, get_collected_bolts) + bytes.fromhex('f503002a') + bytes.fromhex('e07bc1a8') + bytes.fromhex('c0035fd6')
    at(data, cave, bytes(data[cave:cave + len(code)]), code)
    at(data, counter, bytes.fromhex('f52340b9'), branch(2483027968, counter, cave))
WEAPON_LEVEL_CODE = 67924384 + 4
LOADOUT_ITEM_HERO_LEVEL = 69496144
MAIN_WEAPON_RETURN = 69495800
GET_HERO_LEVEL = 69496200
GET_WEAPON_QUANTUM_LEVEL = 69496756
GET_WEAPON_UPGRADE_QUANTUM_LEVEL = 69517804
GET_ECONOMY = 68364052
GET_BASE_SKIN = 75046328
GET_CHAR_DEF_BY_SKIN = 66636884
DEFAULT_WEAPON = 52
OPEN_WEAPON_INFO_POPUP = 67516704
GAME_FSM_INSTANCE = 70336780
WEAPON_LOADOUT_STATE = 5
CHARACTER_STATE = 20
USER_INSTANCE = 69480108
CAN_EQUIP_HERO_SKIN = 69488604
EQUIP_SKIN = 69488712
GET_AT_SLOT = 75099120
TO_CHARACTER_ID = 68390708
GET_DEFAULT_WEAPON_UID = 66646824
WEAPON_WIDGET_DEFAULT_WEAPON = 67270832
USER_EQUIPPED_SKINS = 392
USER_EQUIPPED_WEAPONS = 400
CHANGE_TO_STATE = bytes.fromhex('05915ca9')

def weapon_level_code(at_address):
    code = bytearray()
    labels, fixups = ({}, [])

    def here():
        return at_address + len(code)

    def emit(raw):
        code.extend(raw)

    def jump(kind, label, register=0):
        fixups.append((kind, len(code), label, register))
        code.extend(bytes(4))
    emit(a64.stp_x_pre(29, 30, a64.SP, -48))
    emit(a64.stp_x(23, 24, a64.SP, 16))
    emit(a64.str_x(25, a64.SP, 32))
    emit(a64.mov_w(23, 0))
    emit(a64.mov_x_zero(1))
    emit(a64.bl(here(), GET_HERO_LEVEL))
    emit(a64.mov_x_zero(1))
    emit(a64.bl(here(), GET_WEAPON_QUANTUM_LEVEL))
    emit(a64.mov_w(24, 0))
    emit(a64.ldr_x(9, a64.SP, 48))
    emit(a64.adrp_add(10, here(), MAIN_WEAPON_RETURN))
    emit(a64.cmp_x(9, 10))
    jump('b.ne', 'done')
    emit(a64.mov_w(0, 20))
    emit(a64.mov_x_zero(1))
    emit(a64.bl(here(), GET_WEAPON_UPGRADE_QUANTUM_LEVEL))
    emit(a64.mov_w(25, 0))
    emit(a64.mov_x_zero(0))
    emit(a64.bl(here(), GET_ECONOMY))
    jump('cbz', 'own', 0)
    emit(a64.ldr_x(0, 0, 32))
    jump('cbz', 'own', 0)
    emit(a64.str_x(0, a64.SP, 40))
    emit(a64.mov_w(0, 23))
    emit(a64.mov_x_zero(1))
    emit(a64.bl(here(), GET_BASE_SKIN))
    emit(a64.mov_w(1, 0))
    emit(a64.ldr_x(0, a64.SP, 40))
    emit(a64.mov_x_zero(2))
    emit(a64.bl(here(), GET_CHAR_DEF_BY_SKIN))
    jump('cbz', 'own', 0)
    emit(a64.ldr_w(8, 0, DEFAULT_WEAPON))
    emit(a64.cmp_w(8, 19))
    jump('b.ne', 'own')
    emit(a64.cmp_w(25, 24))
    emit(a64.csel_w(24, 25, 24, 'gt'))
    jump('b', 'done')
    labels['own'] = len(code)
    emit(a64.mov_w(24, 25))
    labels['done'] = len(code)
    emit(a64.mov_w(0, 24))
    emit(bytes.fromhex('f91340f9'))
    emit(a64.ldp_x(23, 24, a64.SP, 16))
    emit(a64.ldp_x_post(29, 30, a64.SP, 48))
    emit(a64.RET)
    for kind, position, label, register in fixups:
        source, target = (at_address + position, at_address + labels[label])
        if kind == 'b':
            raw = a64.b(source, target)
        elif kind == 'cbz':
            raw = a64.cbz_x(register, source, target)
        else:
            raw = a64.b_cond(kind[2:], source, target)
        code[position:position + 4] = raw
    return bytes(code)

class Code:

    def __init__(self, at_address):
        self.at = at_address
        self.code = bytearray()
        self.labels = {}
        self.fixups = []

    def here(self):
        return self.at + len(self.code)

    def emit(self, raw):
        self.code.extend(raw)

    def call(self, target):
        self.emit(a64.bl(self.here(), target))

    def jump(self, kind, label, register=0):
        self.fixups.append((kind, len(self.code), label, register))
        self.code.extend(bytes(4))

    def label(self, name):
        self.labels[name] = len(self.code)

    def change_state(self, state, restore):
        self.emit(a64.mov_x_zero(0))
        self.call(GAME_FSM_INSTANCE)
        self.jump('cbz', 'no_fsm', 0)
        self.emit(a64.ldr_x(8, 0, 0))
        self.emit(a64.movz_w(1, state))
        self.emit(bytes.fromhex('e2031f2a'))
        self.emit(a64.movz_w(3, 1))
        self.emit(CHANGE_TO_STATE)
        self.emit(restore)
        self.emit(a64.br(5))
        self.label('no_fsm')
        self.emit(restore)
        self.emit(a64.RET)

    def build(self):
        for kind, position, label, register in self.fixups:
            source, target = (self.at + position, self.at + self.labels[label])
            if kind == 'b':
                raw = a64.b(source, target)
            elif kind == 'cbz':
                raw = a64.cbz_x(register, source, target)
            elif kind == 'cbzw':
                raw = struct.pack('<I', 872415232 | (target - source >> 2 & 524287) << 5 | register)
            elif kind == 'adr':
                raw = a64_adr(register, source, target)
            elif kind == 'ldrlit':
                raw = a64_cb(1476395008, register, source, target)
            elif kind == 'ldrlit_s':
                raw = a64_cb(469762048, register, source, target)
            elif kind == 'cbnzw':
                raw = struct.pack('<I', 889192448 | (target - source >> 2 & 524287) << 5 | register)
            elif kind == 'cbnzx':
                raw = struct.pack('<I', 3036676096 | (target - source >> 2 & 524287) << 5 | register)
            elif kind == 'bl':
                raw = a64.bl(source, target)
            elif kind == 'tbz0':
                raw = struct.pack('<I', 905969664 | (target - source >> 2 & 16383) << 5 | register)
            elif kind == 'tbnz31':
                raw = struct.pack('<I', 922746880 | 31 << 19 | (target - source >> 2 & 16383) << 5 | register)
            else:
                raw = a64.b_cond(kind[2:], source, target)
            self.code[position:position + 4] = raw
        return bytes(self.code)

def open_arsenal_code(at_address):
    c = Code(at_address)
    restore = a64.ldr_x(19, a64.SP, 16) + a64.ldp_x_post(29, 30, a64.SP, 32)
    c.emit(a64.stp_x_pre(29, 30, a64.SP, -32))
    c.emit(a64.str_x(19, a64.SP, 16))
    c.emit(a64.mov_w(0, 0) and bytes.fromhex('f30300aa'))
    c.emit(a64.mov_x_zero(0))
    c.call(USER_INSTANCE)
    c.jump('cbz', 'open', 0)
    c.emit(a64.str_x(0, a64.SP, 24))
    c.emit(a64.ldr_w(1, 19, 32))
    c.emit(a64.mov_x_zero(2))
    c.call(CAN_EQUIP_HERO_SKIN)
    c.jump('cbzw', 'open', 0)
    c.emit(a64.ldr_x(0, a64.SP, 24))
    c.emit(bytes.fromhex('e1031f2a'))
    c.emit(a64.ldr_w(2, 19, 32))
    c.emit(a64.mov_x_zero(3))
    c.call(EQUIP_SKIN)
    c.label('open')
    c.change_state(WEAPON_LOADOUT_STATE, restore)
    return c.build()

def equip_and_return_code(at_address):
    return a64.b(at_address, HERO_RETURN_CODE)
INIT_METADATA = 63400440
MONO_SINGLETON_GET_INSTANCE = 103153532
COMPONENT_GET_COMPONENT = 80193396
HUD_CHARACTER_BIND_DATA = 67503256
SLOT_MONO_SINGLETON = 152477000
SLOT_GET_HUD_CHARACTER = 152479032
MAX_AMMO_ONCE = 68348696
GET_OBSERVED_GAME = 66468604
GAME_OBJECT_SEND_MESSAGE = 142939368
DONT_REQUIRE_RECEIVER = 1

def max_ammo_check_code(at_address):
    c = Code(at_address)
    c.emit(a64.ldr_w(9, 19, 220))
    c.emit(a64.cmp_w(9, 22))
    c.jump('b.eq', 'same')
    c.emit(w_store(22, 19, 220))
    c.emit(bytes.fromhex('7f660339'))
    c.emit(a64.stp_x_pre(29, 30, a64.SP, -32))
    c.emit(a64.stp_x(20, 21, a64.SP, 16))
    c.emit(a64.mov_x_zero(0))
    c.call(GET_OBSERVED_GAME)
    c.emit(bytes.fromhex('f40300aa'))
    c.jump('adr', 'name', 0)
    c.call(BUILD['string_new'])
    c.emit(bytes.fromhex('f50300aa'))
    c.emit(bytes.fromhex('e00313aa'))
    c.emit(a64.mov_x_zero(1))
    c.call(GET_GAME_OBJECT)
    c.jump('cbz', 'restore', 0)
    c.emit(bytes.fromhex('e10315aa'))
    c.emit(bytes.fromhex('e20314aa'))
    c.emit(a64.movz_w(3, DONT_REQUIRE_RECEIVER))
    c.emit(a64.mov_x_zero(4))
    c.call(GAME_OBJECT_SEND_MESSAGE)
    c.label('restore')
    c.emit(a64.ldp_x(20, 21, a64.SP, 16))
    c.emit(a64.ldp_x_post(29, 30, a64.SP, 32))
    c.label('same')
    c.emit(bytes.fromhex('68664339'))
    c.emit(a64.RET)
    c.label('name')
    c.emit(b'InitializeWidget\x00')
    return c.build()

def adrp_ldr(c, register, address):
    page = (address >> 12) - (c.here() + a64.TEXT_DELTA >> 12)
    c.emit(struct.pack('<I', 2415919104 | (page & 3) << 29 | (page >> 2 & 524287) << 5 | register))
    c.emit(a64.ldr_x(register, register, address & 4095))

def hero_return_code(at_address):
    c = Code(at_address)
    restore = a64.ldp_x(19, 20, a64.SP, 16) + a64.ldp_x_post(29, 30, a64.SP, 48)
    c.emit(a64.stp_x_pre(29, 30, a64.SP, -48))
    c.emit(a64.stp_x(19, 20, a64.SP, 16))
    c.call(BUILD['equip_selected'])
    for slot in (SLOT_GET_HUD_CHARACTER, SLOT_MONO_SINGLETON):
        adrp_ldr(c, 0, slot)
        c.call(INIT_METADATA)
    c.emit(a64.mov_x_zero(0))
    c.call(USER_INSTANCE)
    c.jump('cbz', 'go', 0)
    c.emit(a64.ldr_x(8, 0, USER_EQUIPPED_SKINS))
    c.emit(a64.str_x(8, a64.SP, 32))
    c.emit(bytes.fromhex('e0830091'))
    c.emit(bytes.fromhex('e1031f2a'))
    c.emit(a64.mov_x_zero(2))
    c.call(GET_AT_SLOT)
    c.emit(a64.mov_w(19, 0))
    adrp_ldr(c, 8, SLOT_MONO_SINGLETON)
    c.emit(a64.ldr_x(0, 8, 0))
    c.call(MONO_SINGLETON_GET_INSTANCE)
    c.jump('cbz', 'go', 0)
    c.emit(a64.ldr_x(0, 0, 160))
    c.jump('cbz', 'go', 0)
    adrp_ldr(c, 8, SLOT_GET_HUD_CHARACTER)
    c.emit(a64.ldr_x(1, 8, 0))
    c.call(COMPONENT_GET_COMPONENT)
    c.jump('cbz', 'go', 0)
    c.emit(a64.mov_w(1, 19))
    c.emit(a64.mov_x_zero(2))
    c.call(HUD_CHARACTER_BIND_DATA)
    c.label('go')
    c.change_state(CHARACTER_STATE, restore)
    return c.build()

def shown_weapon_code(at_address):
    c = Code(at_address)
    c.emit(a64.stp_x_pre(29, 30, a64.SP, -48))
    c.emit(a64.stp_x(20, 21, a64.SP, 16))
    c.emit(a64.str_x(22, a64.SP, 32))
    c.emit(a64.mov_x_zero(1))
    c.call(GET_DEFAULT_WEAPON_UID)
    c.emit(a64.mov_w(21, 0))
    c.emit(a64.mov_x_zero(0))
    c.call(USER_INSTANCE)
    c.jump('cbz', 'out', 0)
    c.emit(bytes.fromhex('f60300aa'))
    for field, then in ((USER_EQUIPPED_SKINS, 'hero'), (USER_EQUIPPED_WEAPONS, 'weapon')):
        c.emit(a64.ldr_x(8, 22, field))
        c.emit(a64.str_x(8, a64.SP, 40))
        c.emit(bytes.fromhex('e0a30091'))
        c.emit(bytes.fromhex('e1031f2a'))
        c.emit(a64.mov_x_zero(2))
        c.call(GET_AT_SLOT)
        if then == 'hero':
            c.emit(a64.mov_x_zero(1))
            c.call(TO_CHARACTER_ID)
            c.emit(a64.ldr_w(8, 19, 32))
            c.emit(a64.cmp_w(0, 8))
            c.jump('b.ne', 'out')
        else:
            c.jump('cbzw', 'out', 0)
            c.emit(a64.mov_w(21, 0))
    c.label('out')
    c.emit(a64.mov_w(0, 21))
    c.emit(bytes.fromhex('f61340f9'))
    c.emit(a64.ldp_x(20, 21, a64.SP, 16))
    c.emit(a64.ldp_x_post(29, 30, a64.SP, 48))
    c.emit(a64.RET)
    return c.build()

def patch_weapons_code(data):

    def place(at_address, code):
        at(data, at_address, bytes(data[at_address:at_address + len(code)]), code)
    place(WEAPON_LEVEL_CODE - 4, a64.RET)
    place(EVENTS_CODE, a64.RET)
    hero = hero_return_code(HERO_RETURN_CODE)
    place(HERO_RETURN_CODE, hero)
    check_at = HERO_RETURN_CODE + len(hero) + 15 & ~15
    check = max_ammo_check_code(check_at)
    if check_at + len(check) > EVENTS_CODE_END:
        raise SystemExit('plus de place pour le code du HUD des armes')
    place(check_at, check)
    at(data, MAX_AMMO_ONCE, bytes.fromhex('68664339'), a64.bl(MAX_AMMO_ONCE, check_at))
    level = weapon_level_code(WEAPON_LEVEL_CODE)
    place(WEAPON_LEVEL_CODE, level)
    at(data, LOADOUT_ITEM_HERO_LEVEL, bytes.fromhex('0e000094'), a64.bl(LOADOUT_ITEM_HERO_LEVEL, WEAPON_LEVEL_CODE))
    at(data, LOADOUT_ITEM_HERO_LEVEL + 4, bytes.fromhex('98000094'), a64.NOP)
    equip_at = WEAPON_LEVEL_CODE + len(level) + 15 & ~15
    equip = equip_and_return_code(equip_at)
    place(equip_at, equip)
    jump_at = BUILD['equip_button'] + 8
    at(data, jump_at, a64.b(jump_at, BUILD['equip_selected']), a64.b(jump_at, equip_at))
    shown_at = equip_at + len(equip) + 15 & ~15
    shown = shown_weapon_code(shown_at)
    if shown_at + len(shown) > LOADING_SCREEN_CODE:
        raise SystemExit('plus de place pour le code des armes')
    place(shown_at, shown)
    at(data, WEAPON_WIDGET_DEFAULT_WEAPON, a64.bl(WEAPON_WIDGET_DEFAULT_WEAPON, GET_DEFAULT_WEAPON_UID), a64.bl(WEAPON_WIDGET_DEFAULT_WEAPON, shown_at))
    place(OPEN_WEAPON_INFO_POPUP, open_arsenal_code(OPEN_WEAPON_INFO_POPUP))
LOADING_SCREEN_STATES = 70559104
DESTROY_LOADING_SCREEN = 70562932
LEVEL_INTRO_STATE = 5
LOADING_SCREEN_CODE = 67924384 + 1136 - 64

def loading_screen_code(at_address):
    c = Code(at_address)
    c.emit(a64.cmp_w_imm(24, LEVEL_INTRO_STATE))
    c.jump('b.le', 'done')
    c.emit(a64.ldr_x(0, 21, 0))
    c.jump('cbz', 'done', 0)
    c.emit(a64.stp_x_pre(29, 30, a64.SP, -16))
    c.call(DESTROY_LOADING_SCREEN)
    c.emit(a64.ldp_x_post(29, 30, a64.SP, 16))
    c.label('done')
    c.emit(a64.cmp_w_imm(24, 6))
    c.emit(a64.RET)
    return c.build()

def patch_loading_screen(data):
    host = 67924384
    at(data, host, bytes(data[host:host + 4]), a64.RET)
    code = loading_screen_code(LOADING_SCREEN_CODE)
    if LOADING_SCREEN_CODE + len(code) > host + 1136:
        raise SystemExit("plus de place pour le code de l'ecran de chargement")
    at(data, LOADING_SCREEN_CODE, bytes(data[LOADING_SCREEN_CODE:LOADING_SCREEN_CODE + len(code)]), code)
    at(data, LOADING_SCREEN_STATES, a64.cmp_w_imm(24, 6), a64.bl(LOADING_SCREEN_STATES, LOADING_SCREEN_CODE))
EVENTS_CODE = 67945436
EVENTS_CODE_END = EVENTS_CODE + 1632
HERO_RETURN_CODE = EVENTS_CODE_END - 384 & ~15
BIG_REWARD_POINTS = 64505468
ON_WIN_TOKENS = 64511260
ON_WIN_TOKENS_END = 64511272
STREAK_RESULT = 64484084
TRY_PUSH_SPECIFIC_LOOTBOX = 64604320
BATTLE_EVENT_CALL = 66481852
ACTIVE_EVENT_ID_OR_DEFAULT = 69557640
GET_EVENT_STATUS = 69478904
IS_EVENT_VALID = 69570952
ZURKON_EVENT = 1
RUNNING_STATUS = 2
LOOT_BOX_TYPE = 3
EVENT_LOOT_SOURCE = 8
TOKEN_DROP_CHECK = 129746068
TOKEN_DROP_SKIP = 56
BATTLE_MODIFIER_STORE = 66481892
RANDOM_SYSTEM_CHECK = 129773636
RANDOM_SYSTEM_SKIP = 28
RANDOM_PLAYER_INIT = (129773692, 'ffc300d1')
RANDOM_CHANGE = (129773956, 'ff0302d1')

def w_store(source, base, offset):
    return struct.pack('<I', 3103784960 | offset // 4 << 10 | base << 5 | source)

def w_add(destination, first, second):
    return struct.pack('<I', 184549376 | second << 16 | first << 5 | destination)

def w_sub_imm(destination, source, value):
    return struct.pack('<I', 1358954496 | value << 10 | source << 5 | destination)

def x_umaddl(destination, first, second, addend):
    return struct.pack('<I', 2610954240 | second << 16 | addend << 10 | first << 5 | destination)

def events_code(at_address):
    c = Code(at_address)
    c.emit(a64.RET)
    c.label('big_reward_points')
    c.emit(a64.ldr_x(8, a64.SP, 200))
    c.jump('cbz', 'points_done', 8)
    c.emit(a64.ldr_w(9, 8, 16))
    c.emit(a64.cmp_w_imm(9, ZURKON_EVENT))
    c.jump('b.ne', 'points_done')
    c.emit(a64.ldr_w(9, a64.SP, 96))
    c.emit(a64.ldr_w(13, 19, 0))
    c.emit(a64.movz_w(14, evenements.CARDS_PER_MISSION))
    c.emit(struct.pack('<I', 452984832 | 14 << 16 | 9 << 10 | 13 << 5 | 9))
    c.emit(a64.ldr_w(10, a64.SP, 100))
    c.emit(a64.ldr_x(11, 8, 48))
    c.jump('cbz', 'points_store', 11)
    c.emit(a64.ldr_w(12, 11, 24))
    c.emit(a64.cmp_w(10, 12))
    c.jump('b.ge', 'points_store')
    c.emit(a64.movz_w(12, 40))
    c.emit(x_umaddl(12, 10, 12, 11))
    c.emit(a64.ldr_w(12, 12, 56))
    c.emit(a64.cmp_w(9, 12))
    c.emit(a64.csel_w(9, 9, 12, 'lt'))
    c.label('points_store')
    c.emit(w_store(9, 19, 0))
    c.label('points_done')
    c.emit(a64.ldr_x(8, a64.SP, 200))
    c.emit(a64.RET)
    c.label('on_win_tokens')
    c.emit(a64.ldr_w(8, a64.SP, 192))
    c.emit(w_add(8, 8, 9))
    c.emit(w_store(8, a64.SP, 192))
    c.emit(a64.ldr_x(9, 20, 32))
    c.jump('cbz', 'win_done', 9)
    c.emit(a64.ldr_x(9, 9, 48))
    c.jump('cbz', 'win_done', 9)
    c.emit(a64.ldr_w(10, 9, 24))
    c.emit(a64.cmp_w(8, 10))
    c.jump('b.gt', 'win_done')
    c.emit(w_sub_imm(11, 8, 1))
    c.jump('tbnz31', 'win_done', 11)
    c.emit(a64.movz_w(12, 40))
    c.emit(x_umaddl(11, 11, 12, 9))
    c.emit(a64.ldr_w(12, 11, 32))
    c.emit(a64.cmp_w_imm(12, LOOT_BOX_TYPE))
    c.jump('b.ne', 'win_done')
    c.emit(a64.ldr_w(12, 11, 52))
    c.emit(a64.stp_x_pre(29, 30, a64.SP, -32))
    if os.environ.get('RR_JOURNAL'):
        c.emit(a64.str_x(12, a64.SP, 16))
        c.jump('adr', 'log_box', 0)
        c.call(BUILD['string_new'])
        c.emit(a64.mov_x_zero(1))
        c.call(DEBUG_LOG)
        c.emit(a64.ldr_x(12, a64.SP, 16))
    c.emit(a64.ldr_x(0, 20, 24))
    c.emit(a64.mov_w(1, 12))
    c.emit(struct.pack('<I', 3535798272 | EVENT_LOOT_SOURCE << 5 | 9))
    c.emit(struct.pack('<I', 2852716577))
    c.emit(a64.mov_x_zero(2))
    c.call(TRY_PUSH_SPECIFIC_LOOTBOX)
    c.emit(a64.ldp_x_post(29, 30, a64.SP, 32))
    c.label('win_done')
    c.emit(a64.RET)
    c.label('streak_result')
    c.emit(a64.ldr_x(8, a64.SP, 16))
    c.emit(a64.ldr_x(9, a64.SP, 40))
    c.jump('cbz', 'streak_original', 9)
    c.emit(a64.ldr_w(10, 9, 64))
    c.emit(a64.cmp_w_imm(10, 1))
    c.jump('b.lt', 'streak_original')
    c.emit(a64.ldr_w(11, 8, 4))
    c.emit(a64.cmp_w_imm(11, 1))
    c.jump('b.lt', 'streak_lost')
    c.emit(a64.cmp_w(11, 10))
    c.jump('b.gt', 'streak_lost')
    c.emit(a64.movz_w(8, 1))
    c.emit(a64.RET)
    c.label('streak_lost')
    c.emit(a64.movz_w(8, 0))
    c.emit(a64.RET)
    c.label('streak_original')
    c.emit(a64.ldr_w(8, 8, 0))
    c.emit(a64.RET)
    c.label('battle_event')
    c.emit(a64.stp_x_pre(29, 30, a64.SP, -32))
    c.emit(a64.str_x(19, a64.SP, 16))
    c.emit(bytes.fromhex('f30300aa'))
    c.emit(a64.ldr_w(8, 0, 96))
    c.jump('cbnzw', 'battle_default', 8)
    c.emit(a64.movz_w(1, ZURKON_EVENT) + a64.mov_x_zero(2))
    c.call(GET_EVENT_STATUS)
    c.emit(a64.cmp_w_imm(0, RUNNING_STATUS))
    c.jump('b.ne', 'battle_default')
    c.emit(bytes.fromhex('e00313aa'))
    c.emit(a64.movz_w(1, ZURKON_EVENT) + a64.mov_x_zero(2))
    c.call(IS_EVENT_VALID)
    c.jump('cbzw', 'battle_default', 0)
    c.emit(a64.movz_w(0, ZURKON_EVENT))
    c.jump('b', 'battle_done')
    c.label('battle_default')
    c.emit(bytes.fromhex('e00313aa'))
    c.emit(a64.mov_x_zero(1))
    c.call(ACTIVE_EVENT_ID_OR_DEFAULT)
    c.label('battle_done')
    c.emit(a64.ldr_x(19, a64.SP, 16))
    c.emit(a64.ldp_x_post(29, 30, a64.SP, 32))
    c.emit(a64.RET)
    names = ('big_reward_points', 'on_win_tokens', 'streak_result', 'battle_event')
    if os.environ.get('RR_JOURNAL'):
        c.label('token_log')
        c.jump('cbzw', 'token_skip', 0)
        c.emit(a64.stp_x_pre(29, 30, a64.SP, -16))
        c.jump('adr', 'log_token', 0)
        c.call(BUILD['string_new'])
        c.emit(a64.mov_x_zero(1))
        c.call(DEBUG_LOG)
        c.emit(a64.ldp_x_post(29, 30, a64.SP, 16))
        c.emit(a64.RET)
        c.label('token_skip')
        c.emit(struct.pack('<I', 2432696320 | TOKEN_DROP_SKIP << 10 | 30 << 5 | 30))
        c.emit(a64.RET)
        c.label('battle_log')
        c.emit(struct.pack('<I', 4177544832))
        c.emit(a64.stp_x_pre(29, 30, a64.SP, -64))
        c.emit(a64.stp_x(8, 0, a64.SP, 16))
        c.jump('adr', 'log_battle', 9)
        c.emit(a64.ldp_x(10, 11, 9, 0) + a64.stp_x(10, 11, a64.SP, 32))
        c.emit(a64.ldp_x(10, 11, 9, 16) + a64.stp_x(10, 11, a64.SP, 48))
        c.emit(struct.pack('<I', 285212672 | 48 << 10 | 22 << 5 | 10))
        c.emit(struct.pack('<I', 956301312 | 32 + 21 << 10 | 31 << 5 | 10))
        c.emit(struct.pack('<I', 285212672 | 48 << 10 | 0 << 5 | 10))
        c.emit(struct.pack('<I', 956301312 | 32 + 29 << 10 | 31 << 5 | 10))
        c.emit(struct.pack('<I', 2432696320 | 32 << 10 | 31 << 5 | 0))
        c.call(BUILD['string_new'])
        c.emit(a64.mov_x_zero(1))
        c.call(DEBUG_LOG)
        c.emit(a64.ldp_x(8, 0, a64.SP, 16))
        c.emit(a64.ldp_x_post(29, 30, a64.SP, 64))
        c.emit(a64.RET)

        def entry_log(name, first, message):
            c.label(name)
            c.emit(a64.stp_x_pre(29, 30, a64.SP, -64))
            c.emit(a64.stp_x(0, 1, a64.SP, 16) + a64.stp_x(2, 3, a64.SP, 32) + a64.str_x(4, a64.SP, 48))
            c.jump('adr', message, 0)
            c.call(BUILD['string_new'])
            c.emit(a64.mov_x_zero(1))
            c.call(DEBUG_LOG)
            c.emit(a64.ldp_x(0, 1, a64.SP, 16) + a64.ldp_x(2, 3, a64.SP, 32) + a64.ldr_x(4, a64.SP, 48))
            c.emit(a64.ldp_x_post(29, 30, a64.SP, 64))
            c.emit(bytes.fromhex(first[1]))
            c.jump('b', name + '_back')
        entry_log('player_init_log', RANDOM_PLAYER_INIT, 'log_player_init')
        entry_log('change_log', RANDOM_CHANGE, 'log_change')
        c.label('random_system_log')
        c.jump('cbzw', 'random_system_skip', 0)
        c.emit(a64.stp_x_pre(29, 30, a64.SP, -16))
        c.jump('adr', 'log_system', 0)
        c.call(BUILD['string_new'])
        c.emit(a64.mov_x_zero(1))
        c.call(DEBUG_LOG)
        c.emit(a64.ldp_x_post(29, 30, a64.SP, 16))
        c.emit(a64.RET)
        c.label('random_system_skip')
        c.emit(struct.pack('<I', 2432696320 | RANDOM_SYSTEM_SKIP << 10 | 30 << 5 | 30))
        c.emit(a64.RET)
        c.labels['player_init_log_back'] = RANDOM_PLAYER_INIT[0] + 4 - at_address
        c.labels['change_log_back'] = RANDOM_CHANGE[0] + 4 - at_address
        c.label('log_player_init')
        c.emit(b'RR arme aleatoire: joueur initialise par le systeme\x00')
        c.label('log_change')
        c.emit(b"RR arme aleatoire: changement d'arme\x00")
        c.label('log_system')
        c.emit(b'RR arme aleatoire: systeme active\x00')
        c.label('log_battle')
        c.emit(b'RR partie: evenement ? modif ?\x00\x00')
        c.label('log_token')
        c.emit('RR evenement: caisse avec jeton Zurkon (une chance sur deux)\x00'.encode())
        c.label('log_box')
        c.emit('RR evenement: coffre donne pour un top 5\x00'.encode())
        names += ('token_log', 'battle_log', 'player_init_log', 'change_log', 'random_system_log')
    return (c.build(), {name: at_address + c.labels[name] for name in names})
WEAPON_SLOTS_CODE = 72180780
WEAPON_SLOTS_END = WEAPON_SLOTS_CODE + 4632
SECONDARY_GADGETS = [(51, 2), (52, 3), (53, 4), (41, 5), (10, 6), (3, 8), (26, 9), (6, 10), (16, 14), (22, 15), (23, 17), (56, 22)]
WEAPON_SLOTS_TARGETS = {'ext_string_new': 63431916, 'ext_get_int': 142891136, 'ext_set_int': 142891048, 'ext_save': 142893956, 'slot_filter_key': 152488048 + 16384, 'ext_init_metadata': 63400440, 'ext_user_instance': 69480108, 'ext_get_at_slot': 75099120, 'ext_char_of_skin': 75046628, 'ext_weapon_uid': 66149436, 'ext_is_human': 130379140, 'ext_player_data': 130479552, 'ext_equip_weapon_body': 69489000 + 4, 'ext_equip_skin_body': 69488712 + 4, 'ext_get_economy': 68364052, 'ext_char_def_by_skin': 66636884, 'ext_default_weapon_uid': 66646824, 'ext_weapon_locked_body': 69520768 + 4, 'ext_is_available': 66150176, 'ext_is_ultimate': 66149824, 'ext_is_melee': 66150000, 'ext_slots_create': 67107728, 'ext_slots_null': 67109132, 'ext_slots_next': 67108512, 'ext_create_slots': 67106480, 'ext_refresh_slots': 67113108, 'ext_can_equip_skin': 69488604, 'ext_equip_skin': 69488712, 'ext_fsm_instance': 70336780, 'ext_weapon_is_unlocked': 69524776, 'ext_bin_weapon': 67125492, 'ext_refresh_body': 67126424 + 4, 'ext_refresh_if_body': 67126800 + 4, 'ext_slot_clicked_body': 67127028 + 4, 'ext_loadout_screen': 67125364, 'ext_loadout_in_state': 67116788, 'ext_dropdown_set_value': 140805172, 'slot_main_menu': 152460616 + 16384, 'ext_mono_instance': 103153532, 'slot_highlight_name': 152501432 + 16384, 'ext_animator_set_bool': 142218168}
WEAPON_SLOTS_HOOKS = [(69489000, 'ff0301d1', '_ws_equip_weapon', 'b'), (69488712, 'ff0301d1', '_ws_equip_skin', 'b'), (69520768, 'fe0f1ff8', '_ws_weapon_locked', 'b'), (69495296, 'f60300aa', '_ws_loadout_gadget', 'bl'), (67253876, '002c40f9', '_ws_sheet_gadget', 'bl'), (130011492, '610e40b9', '_ws_sim_key', 'bl'), (67107512, 'e00314aa', '_ws_slots_candidate', 'bl'), (67107724, '1a2c00b4', '_ws_slots_mode', 'b'), (67116012, 'c00240f9', '_ws_filter_changed', 'b'), (67516864, 'fe0f1df8', '_ws_open_secondary', 'b'), (67110416, 'c6350994', '_ws_weapon_unlocked', 'bl'), (67110452, 'bd350994', '_ws_weapon_unlocked', 'bl'), (67126424, 'fe0f1cf8', '_ws_slot_refresh', 'b'), (67126800, 'fe57bea9', '_ws_slot_refresh_if', 'b'), (67127028, 'ff8301d1', '_ws_slot_clicked', 'b')]
WEAPON_SLOTS_OPEN = [(67125664, 'd71c0994'), (67126484, '0a1c0994'), (67127232, '4f1b0994')]
MOV_W0_1 = bytes.fromhex('20008052')
WEAPON_SLOTS_FLAGS = [(11460026, b'LoadoutSlotWidget_0'), (10751530, b'LoadoutSlotWidget_1'), (10342094, b'BgLeft')]
WEAPON_SLOTS_SCENE_EDITS = [(23897584, struct.pack('<iii', 0, 101, 1), struct.pack('<iii', 0, 0, 1)), (19526416, struct.pack('<ff', -1.3498382568359375, -122.09344482421875), struct.pack('<ff', -1.3498382568359375, -334.2)), (19526348, struct.pack('<3f', 1, 1, 1), struct.pack('<3f', 1.25, 1.25, 1)), (24804368, struct.pack('<ff', 192.9499969482422, 139.60000610351562), struct.pack('<ff', 192.9499969482422, 160)), (18751528, struct.pack('<ff', 0, -185), struct.pack('<ff', 30, -164)), (25082356, struct.pack('<iii', 0, 91, 37), struct.pack('<iii', 0, 0, 37))]

def weapon_slots_flag_edits():
    edits = []
    for flag, name in WEAPON_SLOTS_FLAGS:
        pad = -len(name) % 4
        head = struct.pack('<i', len(name)) + name
        edits.append((flag - 2 - pad - len(head), head + bytes(pad + 3), head + bytes(pad + 2) + b'\x01'))
    return edits + WEAPON_SLOTS_SCENE_EDITS
WEAPON_SLOTS_TEXTS = {'FR': {'UI.WEAPON_FILTER.TYPE': 'Armes secondaires'}, 'EN': {'UI.WEAPON_FILTER.TYPE': 'Secondary weapons'}}

def weapon_slots_build():
    return BUILD is BUILDS['1.10.4'] and BOLT_RUSH
GADGET_DB_BUNDLE = 'assets/aa/Android/quantum_db_gagdet_assets_all_3f1e699b51cce3c6dfd60ba52c57442f.bundle'
GADGET_CARD_PICTURES = {GADGET_DB_BUNDLE: [('Q_DrillDash_MeleeWeapon_WeaponSpec', 'Q_DrillDash_GadgetSpec'), ('Q_LittleSpin_MeleeWeapon', 'Q_LittleSpin_GadgetSpec')], 'hero_specs': [('Q_WrenchThrow_WeaponSpec', 'Q_WrenchThrow_GadgetSpec')]}
GADGET_FINAL_VISUALS = {'Q_DrillDash_MeleeWeapon_WeaponSpec': ('CAB-e558baa0355476ff6a05bf24f0600558', -9011812752001224597), 'Q_WrenchThrow_WeaponSpec': ('CAB-53ec03604fbee74dd8dfe45ec46f104e', -3839807419143728885)}
GADGET_MENU_RENDER = {'Q_WrenchThrow_WeaponSpec': {'<menuRenderZRotateNeeded>k__BackingField': 0, '<menuRenderXRotationInDegrees>k__BackingField': 0}}

def external_index(env, cab):
    import copy
    files = [f for bundle in env.files.values() for name, f in getattr(bundle, 'files', {}).items() if name.startswith('CAB-') and hasattr(f, 'externals')]
    if len(files) != 1:
        raise SystemExit('paquet de fiches inattendu')
    externals = files[0].externals
    path = f'archive:/{cab}/{cab}'
    for index, external in enumerate(externals, 1):
        if external.path == path:
            return index
    model = next((e for e in externals if e.path.startswith('archive:/CAB-')))
    added = copy.copy(model)
    added.path = path
    externals.append(added)
    return len(externals)

def gadget_card_pictures(data, pairs):
    if not heavy_tools():
        return
    import UnityPy
    env = UnityPy.load(bytes(data))
    named = {o.peek_name(): o for o in env.objects if o.type.name == 'MonoBehaviour'}
    for weapon_name, gadget_name in pairs:
        gadget = named[gadget_name].read_typetree()
        icon = gadget['<ColoredIcon>k__BackingField']
        weapon = named[weapon_name]
        tree = weapon.read_typetree()
        for field in ('<spriteColored>k__BackingField', '<sprite3D>k__BackingField', '<spriteUI>k__BackingField', '<smallSpriteUI>k__BackingField'):
            if tree[field]['m_PathID'] == 0:
                tree[field] = dict(icon)
        for field, source in (('<LocalizedNameKey>k__BackingField', '<LocalizedName>k__BackingField'), ('<LocalizedDescriptionKey>k__BackingField', '<LocalizedDesc>k__BackingField')):
            if field in tree and gadget[source]['_value']:
                tree[field] = dict(gadget[source])
        if weapon_name in GADGET_FINAL_VISUALS:
            cab, model = GADGET_FINAL_VISUALS[weapon_name]
            tree['<finalVisual>k__BackingField'] = {'m_FileID': external_index(env, cab), 'm_PathID': model}
        for field, value in GADGET_MENU_RENDER.get(weapon_name, {}).items():
            if field not in tree:
                raise SystemExit(f'{weapon_name} : {field} introuvable')
            tree[field] = value
        weapon.save_typetree(tree)
    data[:] = env.file.save(packer='lz4')
    print(f"images des cartes de gadget : {', '.join((weapon for weapon, _ in pairs))}")

def patch_gadget_db(data):
    gadget_card_pictures(data, GADGET_CARD_PICTURES[GADGET_DB_BUNDLE])

def patch_hero_specs_bundle(data):
    patch_hero_talents(data)
    if weapon_slots_build():
        gadget_card_pictures(data, GADGET_CARD_PICTURES['hero_specs'])

def secondary_gadget_lists(characters):
    by_id = {c['uniqueID']['_value']: c for c in characters.values()}
    canon = []
    for weapon, owner in SECONDARY_GADGETS:
        record = by_id.get(owner)
        if not record or not record['gadgets']:
            raise SystemExit(f"gadget {weapon} : le heros {owner} n'en a pas")
        canon.append(json_copy(record['gadgets'][0]))
    for character in characters.values():
        if character['gadgets']:
            character['gadgets'] = [character['gadgets'][0]] + [json_copy(g) for g in canon]

def patch_weapon_slots(data):
    code, uses, labels = assemble_source('armes_secondaires.s')
    start = labels['_ws_start']
    if WEAPON_SLOTS_CODE + len(code) > WEAPON_SLOTS_END:
        raise SystemExit('plus de place pour les armes secondaires')
    ids = struct.unpack('<12I', code[labels['_ws_gadget_ids']:labels['_ws_gadget_ids'] + 48])
    owners = struct.unpack('<12I', code[labels['_ws_gadget_ids'] + 48:labels['_ws_gadget_ids'] + 96])
    if list(zip(ids, owners)) != SECONDARY_GADGETS:
        raise SystemExit("armes_secondaires.s et SECONDARY_GADGETS ne sont plus d'accord")
    place_assembled(data, WEAPON_SLOTS_CODE, code, uses, WEAPON_SLOTS_TARGETS, None)
    entry = {name: WEAPON_SLOTS_CODE + offset - start for name, offset in labels.items()}
    for address, old, name, kind in WEAPON_SLOTS_HOOKS:
        at(data, address, bytes.fromhex(old), (a64.bl if kind == 'bl' else a64.b)(address, entry[name]))
    at(data, 67107516, bytes.fromhex('e103172a'), struct.pack('<I', 905969664 | (67108512 - 67107516 >> 2 & 16383) << 5))
    at(data, 67107520, bytes.fromhex('e20316aa'), a64.b(67107520, 67107576))
    at(data, OPEN_WEAPON_INFO_POPUP, bytes(data[OPEN_WEAPON_INFO_POPUP:OPEN_WEAPON_INFO_POPUP + 4]), a64.b(OPEN_WEAPON_INFO_POPUP, entry['_ws_open_primary']))
    for address, old in WEAPON_SLOTS_OPEN:
        at(data, address, bytes.fromhex(old), MOV_W0_1)
    count = len(WEAPON_SLOTS_HOOKS) + len(WEAPON_SLOTS_OPEN) + 3
    print(f'armes principales et secondaires : {len(code)} octets, {count} retouches')
EVENT_ICON_CODE = 72307776
EVENT_META_CHECK = 67423364
EVENT_META_FAIL = 67423880
EVENT_META_STRUCT = 424
EVENT_GAUGE = 136
EVENT_ICON_EXTERNALS = {'get_transform': 142923708, 'find': 143030524, 'get_game_object': 142923916, 'get_component_by_name': 142935700, 'set_sprite': 144176752}

def event_icon_code(at_address):
    e = EVENT_ICON_EXTERNALS
    c = Code(at_address)
    c.jump('tbz0', 'fail', 0)
    c.emit(a64.stp_x_pre(29, 30, a64.SP, -48))
    c.emit(a64.stp_x(20, 21, a64.SP, 16))
    meta = 48 + EVENT_META_STRUCT
    c.emit(a64.ldr_w(8, a64.SP, meta))
    c.emit(a64.ldr_x(20, a64.SP, meta + 8))
    c.emit(a64.cmp_w_imm(8, ZURKON_EVENT))
    c.jump('b.ne', 'have')
    c.emit(a64.ldr_x(9, a64.SP, meta + 232))
    c.jump('cbz', 'have', 9)
    c.emit(struct.pack('<I', 2852717556))
    c.label('have')
    c.jump('cbz', 'done', 20)
    c.emit(a64.ldr_x(0, 19, EVENT_GAUGE))
    c.jump('cbz', 'done', 0)
    c.emit(a64.mov_x_zero(1))
    c.call(e['get_transform'])
    c.jump('cbz', 'done', 0)
    c.emit(struct.pack('<I', 2852127733))
    c.jump('adr', 's_icon', 0)
    c.call(BUILD['string_new'])
    c.emit(struct.pack('<I', 2852127713))
    c.emit(struct.pack('<I', 2853503968))
    c.emit(a64.mov_x_zero(2))
    c.call(e['find'])
    c.jump('cbz', 'done', 0)
    c.emit(a64.mov_x_zero(1))
    c.call(e['get_game_object'])
    c.jump('cbz', 'done', 0)
    c.emit(struct.pack('<I', 2852127733))
    c.jump('adr', 's_image', 0)
    c.call(BUILD['string_new'])
    c.emit(struct.pack('<I', 2852127713))
    c.emit(struct.pack('<I', 2853503968))
    c.emit(a64.mov_x_zero(2))
    c.call(e['get_component_by_name'])
    c.jump('cbz', 'done', 0)
    c.emit(struct.pack('<I', 2853438433))
    c.emit(a64.mov_x_zero(2))
    c.call(e['set_sprite'])
    c.label('done')
    c.emit(a64.ldp_x(20, 21, a64.SP, 16))
    c.emit(a64.ldp_x_post(29, 30, a64.SP, 48))
    c.emit(a64.b(c.here(), EVENT_META_CHECK + 4))
    c.label('fail')
    c.emit(a64.b(c.here(), EVENT_META_FAIL))
    c.label('s_icon')
    c.emit(b'EventIcon\x00\x00\x00')
    c.label('s_image')
    c.emit(b'Image\x00\x00\x00')
    return c.build()

def patch_events_code(data):
    icon = event_icon_code(EVENT_ICON_CODE)
    at(data, EVENT_ICON_CODE, bytes(data[EVENT_ICON_CODE:EVENT_ICON_CODE + len(icon)]), icon)
    tbz = struct.pack('<I', 905969664 | EVENT_META_FAIL - EVENT_META_CHECK >> 2 << 5)
    at(data, EVENT_META_CHECK, tbz, a64.b(EVENT_META_CHECK, EVENT_ICON_CODE))
    code, entries = events_code(EVENTS_CODE)
    if EVENTS_CODE + len(code) > HERO_RETURN_CODE:
        raise SystemExit('plus de place pour le code des evenements')
    at(data, EVENTS_CODE, bytes(data[EVENTS_CODE:EVENTS_CODE + len(code)]), code)
    at(data, BIG_REWARD_POINTS, bytes.fromhex('e86740f9'), a64.bl(BIG_REWARD_POINTS, entries['big_reward_points']))
    at(data, ON_WIN_TOKENS, bytes.fromhex('e8c340b9'), a64.bl(ON_WIN_TOKENS, entries['on_win_tokens']))
    at(data, ON_WIN_TOKENS + 4, bytes.fromhex('0801090b'), a64.b(ON_WIN_TOKENS + 4, ON_WIN_TOKENS_END))
    at(data, STREAK_RESULT, bytes.fromhex('e80b40f9'), a64.bl(STREAK_RESULT, entries['streak_result']))
    at(data, STREAK_RESULT + 4, bytes.fromhex('080140b9'), a64.NOP)
    at(data, BATTLE_EVENT_CALL, a64.bl(BATTLE_EVENT_CALL, ACTIVE_EVENT_ID_OR_DEFAULT), a64.bl(BATTLE_EVENT_CALL, entries['battle_event']))
    if os.environ.get('RR_JOURNAL'):
        at(data, TOKEN_DROP_CHECK, bytes.fromhex('e0010036'), a64.bl(TOKEN_DROP_CHECK, entries['token_log']))
        at(data, BATTLE_MODIFIER_STORE, bytes.fromhex('804600f9'), a64.bl(BATTLE_MODIFIER_STORE, entries['battle_log']))
        at(data, RANDOM_SYSTEM_CHECK, bytes.fromhex('00010036'), a64.bl(RANDOM_SYSTEM_CHECK, entries['random_system_log']))
        for (function, first), name in ((RANDOM_PLAYER_INIT, 'player_init_log'), (RANDOM_CHANGE, 'change_log')):
            at(data, function, bytes.fromhex(first), a64.b(function, entries[name]))
    if collect_screen_build():
        patch_collect_screen(data)
        patch_enemy_tokens(data)
        patch_podium_credits(data)
OLD_110_XAPK = os.environ.get('RR_JEU_110', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'ratchet-and-clank-ranger-rumble-1-1-0.xapk'))
COLLECT_SCREEN_FAMILIES = ('ui_atlases_', 'ui_bgs_', 'ui_animations_', 'fonts_', 'ui_materials_', 'fxmanager_', 'shared_textures_', 'default_common_group_', 'material_assets', 'ui_addressables_')
MONOSCRIPTS_BUNDLE = 'assets/aa/Android/913fdc02988c9f04b9d53c5645e34846_monoscripts_b5e55861ec07d2dfb6815884c7e4041c.bundle'
COLLECT_SCREEN_CODE = 72375620
COLLECT_SCREEN_END = COLLECT_SCREEN_CODE + 2884
COLLECT_SCREEN_TARGETS = {'ext_get_mm': 70368028, 'ext_get_updater_body': 70368092 + 4, 'ext_get_canvas_body': 70368176 + 4, 'ext_transition_body': 70368812 + 4, 'ext_init_metadata': 63400440, 'slot_v2_class': 152494672 + 16384, 'ext_string_new': 63431916, 'ext_get_component_by_name': 142935700, 'ext_get_transform': 142923708, 'ext_get_parent': 143014208, 'ext_find': 143030524, 'ext_get_gameobject': 142923916, 'ext_write_barrier': 63400356, 'ext_set_active': 142943076, 'ext_ctx_get': 79645172, 'slot_get_status': 152420880 + 16384, 'ext_ctx_set': 79652708, 'slot_set_status': 152420888 + 16384, 'ext_try_get_user_event': 75039796, 'ext_update_event': 75040200, 'ext_time_implicit': 127791080, 'ext_event_end_time': 64501204, 'ext_events_instance': 69478200, 'ext_try_get_user_event_sys': 69478580, 'ext_get_int': 142891136, 'ext_set_int': 142891048, 'ext_prefs_save': 142893956, 'ext_can_open_body': 75042084 + 4, 'slot_popup_instance': 152460456 + 16384, 'ext_singleton_instance': 103153532, 'ext_show_event_info': 67873744, 'ext_play_pressed_body': 67419032 + 4, 'slot_get_currencies': 152420104 + 16384, 'slot_set_currencies': 152420112 + 16384, 'ext_currencies_get': 79645460, 'ext_currencies_set': 79652888, 'ext_currencies_spend': 75015208}
COLLECT_SCREEN_INFO_CLICK = (67419032, 'fe4fbfa9')
COLLECT_SCREEN_POPUP = (75042084, 'fe0f1ff8')
COLLECT_SCREEN_NEVER_OPENED = (75041912, '08c04039')
COLLECT_SCREEN_EARN_TOKENS = (64504604, 'c0035fd6')
COLLECT_SCREEN_END_TIME = 67417968
COLLECT_SCREEN_HOOKS = [(70368092, 'fe4fbfa9', '_ec_get_updater'), (70368176, 'fe0f1ef8', '_ec_get_canvas'), (70368812, 'fe0f1ef8', '_ec_transition_finished')]
COLLECT_SCREEN_EVENT_READ = (67417244, '156040b9')
COLLECT_SCREEN_INFO_TEXT = (67406836, '60064da9')
ZURKON_TEXTS = {'FR': {'UI.EVENT.ZURKON.TITLE': 'Campagne de fidélité de Mme Zurkon', 'UI.EVENT.ZURKON.DESC': "Mme Zurkon organise une campagne de fidélité pour ses clients. Récupérez les jetons de fidélité qu'elle a cachés dans la galaxie pour recevoir des prix exclusifs."}, 'EN': {'UI.EVENT.ZURKON.TITLE': 'Mrs. Zurkon Loyalty Campaign', 'UI.EVENT.ZURKON.DESC': 'Mrs. Zurkon is organising a loyalty campaign for her customers. Collect the loyalty tokens she has hidden in the galaxy to receive exclusive prizes.'}, 'DE': {'UI.EVENT.ZURKON.TITLE': 'Frau Zurkon Treuekampagne', 'UI.EVENT.ZURKON.DESC': 'Frau Zurkon organisiert eine Treueaktion für ihre Kunden. Sammle die Treuemarken, die sie in der Galaxie versteckt hat, und erhalte exklusive Preise.'}, 'ES': {'UI.EVENT.ZURKON.TITLE': 'Campaña de lealtad de la Sra. Zurkon', 'UI.EVENT.ZURKON.DESC': 'La Sra. Zurkon está organizando una campaña de fidelización para sus clientes. Reúne las fichas de fidelidad que ha escondido en la galaxia para ganar premios exclusivos.'}, 'IT': {'UI.EVENT.ZURKON.TITLE': 'Campagna fedeltà della signora Zurkon', 'UI.EVENT.ZURKON.DESC': 'La signora Zurkon sta organizzando una campagna fedeltà per i suoi clienti. Raccogli i gettoni fedeltà che ha nascosto nella galassia per ricevere premi esclusivi.'}, 'BR': {'UI.EVENT.ZURKON.TITLE': 'Campanha de fidelidade da Sra. Zurkon', 'UI.EVENT.ZURKON.DESC': 'A Sra. Zurkon está organizando uma campanha de fidelidade para seus clientes. Colete os tokens de fidelidade que ela escondeu na galáxia para receber prêmios exclusivos.'}}
ZURKON_RULES = {'FR': "Du dimanche au mardi, Mme Zurkon cache ses jetons de fidélité dans les combats :\n- Casse des caisses : une chance sur deux d'y trouver un jeton.\n- Élimine des adversaires : eux aussi lâchent un jeton une fois sur deux.\n- Passe dessus pour le ramasser avant qu'il disparaisse.\nQuand tu as assez de jetons, appuie sur Récupérer : les récompenses se débloquent dans l'ordre.", 'EN': 'From Sunday to Tuesday, Mrs. Zurkon hides her loyalty tokens in battles:\n- Break crates: one chance in two to find a token.\n- Knock out opponents: they drop a token half of the time too.\n- Run over it to pick it up before it vanishes.\nWhen you have enough tokens, press Collect: the rewards unlock in order.'}
RIVET_LEGENDARY_CODE = COLLECT_SCREEN_CODE + 2816
RIVET_LEGENDARY_HOOKS = [(68081372, '9f920371', '_rv_rarity'), (67727076, '1f590071', '_rv_background')]

def patch_rivet_legendary(data):
    code, uses, labels = assemble_source('rivet_legendaire.s')
    if uses or RIVET_LEGENDARY_CODE + len(code) > COLLECT_SCREEN_END:
        raise SystemExit('code de Rivet legendaire inattendu')
    if collect_screen_build() and COLLECT_SCREEN_CODE + len(assemble_source('ecran_collecte.s')[0]) > RIVET_LEGENDARY_CODE:
        raise SystemExit("l'ecran de collecte deborde sur le code de Rivet")
    at(data, RIVET_LEGENDARY_CODE, bytes(data[RIVET_LEGENDARY_CODE:RIVET_LEGENDARY_CODE + len(code)]), code)
    start = labels['_rv_start']
    for address, old, name in RIVET_LEGENDARY_HOOKS:
        at(data, address, bytes.fromhex(old), a64.bl(address, RIVET_LEGENDARY_CODE + labels[name] - start))
    print('Rivet legendaire comme Ratchet')
ENEMY_TOKENS_CODE = COLLECT_SCREEN_CODE + 1536
ENEMY_TOKENS_ADDS = (130602840, 130603140)
QLIST_ADD = 106550964
ENEMY_TOKENS_NO_BOLT = (130602436, '40180037')
ENEMY_TOKENS_REPLACED = (130603296, 'ebffff17')
ENEMY_TOKENS_TARGETS = {'ext_qlist_add': QLIST_ADD, 'ext_try_get_pointer': 87003476, 'ext_alloc_list': 82442972, 'ext_list_ptr': 106555076, 'ext_set_specs': 130293508, 'ext_frame_add': 82420220, 'ext_setup_end': 130603212, 'slot_dropper_class': 152992432 + 16384, 'slot_alloc_list': 153023704 + 16384, 'slot_list_add': 152994096 + 16384, 'slot_list_ptr': 153002288 + 16384, 'slot_frame_add': 153023696 + 16384, 'ext_get_specs': 130293448, 'ext_resolve_list': 82491148, 'slot_resolve_list': 152994056 + 16384, 'ext_class_init': 63636616}
PODIUM_CREDITS_CODE = 72365488
PODIUM_CREDITS_END = 72365488 + 2248
PODIUM_CREDITS_HOOK = (64480916, 'fd7bbaa9')
PODIUM_CREDITS_TARGETS = {'ext_init_metadata': 63400440, 'slot_modify_pending': 152419288 + 16384, 'ext_ctx_modify': 79648976, 'ext_push_pending': 64542240, 'ext_impl_body': 64480916 + 4, 'ext_string_new': 63431916}

def patch_podium_credits(data):
    code, uses, labels = assemble_source('credits_podium.s')
    if PODIUM_CREDITS_CODE + len(code) > PODIUM_CREDITS_END:
        raise SystemExit('plus de place pour les credits du podium')
    code = bytearray(code)
    if os.environ.get('RR_JOURNAL'):
        code[labels['journal']:labels['journal'] + 4] = struct.pack('<I', 1)
        last = int(os.environ.get('RR_RANG_CREDITS', '3'))
        code[labels['last_paid_rank']:labels['last_paid_rank'] + 4] = struct.pack('<I', last)
        extra = int(os.environ.get('RR_KILLS_TEST', '0'))
        code[labels['test_kills']:labels['test_kills'] + 4] = struct.pack('<I', extra)
    if weapon_slots_build():
        _, _, slot_labels = assemble_source('armes_secondaires.s')
        plan_targets = WEAPON_SLOTS_CODE + slot_labels['_ws_plan_targets'] - slot_labels['_ws_start']
    else:
        code[labels['plan_targets_on']:labels['plan_targets_on'] + 4] = struct.pack('<I', 0)
        plan_targets = PODIUM_CREDITS_CODE
    targets = dict(PODIUM_CREDITS_TARGETS, ext_debug_log=DEBUG_LOG, ext_plan_targets=plan_targets)
    place_assembled(data, PODIUM_CREDITS_CODE, bytes(code), uses, targets, None)
    address, old = PODIUM_CREDITS_HOOK
    at(data, address, bytes.fromhex(old), a64.b(address, PODIUM_CREDITS_CODE + labels['_cp_battle_end'] - labels['_cp_start']))
    print(f'credits du podium : {len(code)} octets')

def patch_enemy_tokens(data):
    code, uses, labels = assemble_source('jetons_ennemis.s')
    if ENEMY_TOKENS_CODE + len(code) > RIVET_LEGENDARY_CODE:
        raise SystemExit('plus de place pour les jetons des ennemis')
    if COLLECT_SCREEN_CODE + len(assemble_source('ecran_collecte.s')[0]) > ENEMY_TOKENS_CODE:
        raise SystemExit("l'ecran de collecte deborde sur les jetons des ennemis")
    code = bytearray(code)
    if os.environ.get('RR_JOURNAL'):
        code[labels['journal']:labels['journal'] + 4] = struct.pack('<I', 1)
    place_assembled(data, ENEMY_TOKENS_CODE, bytes(code), uses, dict(ENEMY_TOKENS_TARGETS, ext_string_new=63431916, ext_debug_log=DEBUG_LOG), None)
    entry = ENEMY_TOKENS_CODE + labels['_tk_add'] - labels['_tk_start']
    for address in ENEMY_TOKENS_ADDS:
        at(data, address, a64.bl(address, QLIST_ADD), a64.bl(address, entry))
    address, old = ENEMY_TOKENS_NO_BOLT
    at(data, address, bytes.fromhex(old), a64.bl(address, ENEMY_TOKENS_CODE + labels['_tk_no_bolt'] - labels['_tk_start']))
    address, old = ENEMY_TOKENS_REPLACED
    at(data, address, bytes.fromhex(old), a64.b(address, ENEMY_TOKENS_CODE + labels['_tk_replaced'] - labels['_tk_start']))
    print('jetons de Mme Zurkon aussi sur les heros elimines')

def collect_screen_build():
    return EVENTS and BUILD is BUILDS['1.10.4'] and os.path.isfile(OLD_110_XAPK)

def patch_collect_screen(data):
    code, uses, labels = assemble_source('ecran_collecte.s')
    if COLLECT_SCREEN_CODE + len(code) > COLLECT_SCREEN_END:
        raise SystemExit("plus de place pour l'ecran de collecte")
    code = bytearray(code)
    if os.environ.get('RR_JOURNAL'):
        code[labels['journal']:labels['journal'] + 4] = struct.pack('<I', 1)
    place_assembled(data, COLLECT_SCREEN_CODE, bytes(code), uses, dict(COLLECT_SCREEN_TARGETS, ext_debug_log=DEBUG_LOG), None)
    start = labels['_ec_start']
    for address, old, name in COLLECT_SCREEN_HOOKS:
        at(data, address, bytes.fromhex(old), a64.b(address, COLLECT_SCREEN_CODE + labels[name] - start))
    address, old = COLLECT_SCREEN_EVENT_READ
    at(data, address, bytes.fromhex(old), a64.bl(address, COLLECT_SCREEN_CODE + labels['_ec_refresh_event'] - start))
    address, old = COLLECT_SCREEN_INFO_CLICK
    at(data, address, bytes.fromhex(old), a64.b(address, COLLECT_SCREEN_CODE + labels['_ec_info_clicked'] - start))
    address, old = COLLECT_SCREEN_INFO_TEXT
    at(data, address, bytes.fromhex(old), a64.bl(address, COLLECT_SCREEN_CODE + labels['_ec_info_text'] - start))
    address, old = COLLECT_SCREEN_EARN_TOKENS
    at(data, address, bytes.fromhex(old), a64.b(address, COLLECT_SCREEN_CODE + labels['_ec_earn_tokens'] - start))
    address, old = COLLECT_SCREEN_NEVER_OPENED
    at(data, address, bytes.fromhex(old), a64.b(address, COLLECT_SCREEN_CODE + labels['_ec_never_opened'] - start))
    address, old = COLLECT_SCREEN_POPUP
    at(data, address, bytes.fromhex(old), a64.b(address, COLLECT_SCREEN_CODE + labels['_ec_can_open_popup'] - start))
    address = COLLECT_SCREEN_END_TIME
    at(data, address, a64.bl(address, COLLECT_SCREEN_TARGETS['ext_time_implicit']), a64.bl(address, COLLECT_SCREEN_CODE + labels['_ec_end_time'] - start))
    print(f'ecran de collecte : {len(code)} octets')
_COLLECT_GRAFT = []

def collect_graft():
    if not _COLLECT_GRAFT:
        import greffe_evenement
        old_pack = zipfile.ZipFile(io.BytesIO(zipfile.ZipFile(OLD_110_XAPK).read('UnityDataAssetPack.apk')))
        new_pack = zipfile.ZipFile(os.path.join(xapk, 'UnityDataAssetPack.apk'))

        def bundles(pack, *prefixes):
            names = [n for n in pack.namelist() if n.startswith('assets/aa/Android/')]
            return {p: [pack.read(n) for n in names if n.split('/')[-1].startswith(p)] for p in prefixes}
        old = bundles(old_pack, 'scene_mainmenu_landscape_', '69b923348c4df9ad548573d6b86b9c62_monoscripts_', *COLLECT_SCREEN_FAMILIES)
        new = bundles(new_pack, *COLLECT_SCREEN_FAMILIES)
        graft = greffe_evenement.Graft(old['scene_mainmenu_landscape_'][0], old['69b923348c4df9ad548573d6b86b9c62_monoscripts_'][0], [b for p in COLLECT_SCREEN_FAMILIES for b in old[p]], [b for p in COLLECT_SCREEN_FAMILIES for b in new[p]], new_pack.read(MONOSCRIPTS_BUNDLE))
        graft.closure()
        _COLLECT_GRAFT.append(graft)
    return _COLLECT_GRAFT[0]

def patch_monoscripts(data):
    stream = bundle_stream(bytes(data))
    new = collect_graft().patch_monoscripts(stream)
    replace_bundle_stream(data, new)
FLAIL_SPIN_CODE = bytes.fromhex('ff0304d1e08708a9e28f09a9f3d30aa9f5db0ba9f7e30ca9f9eb0da9fdfb0ea9f30300aa230d00b4680c40f9e90f00581f0109eba10c0054570440f9770c00b4380840f9340040f9f80a00b400c30091e1031faa00000094600a0036f83640f964000094000a0035e82240b91f010071ad090054e00313aae10314aae2031faa0000009400090037691e40b9e80240b968000035e90200b9e803092a3901084b680240f9092541f9012941f9e00313aa20013fd6fa0300aa2a7f4093557d1a9bf82e40f94b000094e0010034681e40b9e81200b9ff2600b9ab021acbacfe50936bfd50939f010beb00070054e82240b908050051e82200b91f0100716c06005429000014a9090058bf0209ebeb050054e00313aae10314aae2031faa00000094e703002a2900a0d2ff7f01a9ff7f02a9ff7f03a9ffa703a9ff7f00a9e00313aa81070058e2430091e3a30091e40314aae5031faae6031faa00000094e02e00f9f90300aa00000090000040f9000000942900a0d2f4ff04a9e9ff05a9ffff06a9ffff07a903000090630040f9630040f9e00313aae10319aae2230191000000940a000014ff0200b9f82e40f9ff2e00f910000094a0000034e00313aae10318aae2031faa00000094e08748a9e28f49a9f3d34aa9f5db4ba9f7e34ca9f9eb4da9fdfb4ea9ff030491ffc301d100000014e0031f2a682e40b91f01186b29010054681e40f9e80000b4097f60d30871898b080540b909ff60d31f01096be0179f1ac0035fd61f2003d5151c102396a8c1355dba30b004960d1c6626000000000000')
FLAIL_SPIN_CALLS = {84: 130965704, 128: 129714756, 284: 130417996, 344: 129888084, 364: 63400440, 412: 82550228, 452: 131170080}
FLAIL_SPIN_BACK = 492
FLAIL_SPIN_SLOT = ((356, 0), (388, 3))
SLOT_SET_HIERARCHY = 153019016
FLAIL_VIEW_CODE = bytes.fromhex('ff0303d1e00705a9f35306a9f55b07a9f76308a9f96b09a9fd7b0aa9e8270b6df30300aa681240f9491c00581f0109eb01190054e00313aae1031faa00000094801800b4f40300aa001c001000000094e10300aae00314aae2031faa00000094801700b4e1031faa00000094201700b4f50300aa801b007000000094e10300aae00315aae2031faa00000094201600b4f50300aa001b001000000094e10300aae00314aae2031faa00000094f60300aa001c007000000094e10300aae00314aae2031faa00000094400000b5e00314aae1031faa00000094e007022de21b00bde0031faa00000094c00d00b4001c40f9800d00b4170c40f9570d00b400000090000040f9400000360000009408000090080140f9180140f9081f40f9680000b5e00318aa00000094081f40f9030540f9e05240f9600b00b4611640f9ff1b00f9e2c3009100000094c00a0036f91b40f9990a00b4383740f988000094c0010034e00318aae1031faa00000094a00900b4e1031faa00000094400900b4e1031faa00000094e007042de22b00bd1a00805224000014382f40f97800009420080034e00318aae1031faa00000094a00700b4e1031faa00000094400700b4e1031faa00000094e007042de22b00bde0031faa00000094210f001c0808211e0041201ee0031faa000000940940201e0041201ee0031faa00000094220e001c0008221e2909221ee313442d6328291ee52b40bda528201ee313042de52b00bd5a008052e00315aae1031faa00000094800100b4f90300aa6011003000000094e10300aae00319aae003271ec10b001cc20b001ce303271ee2031faa00000094e00315aa41008052e2031faa00000094e007422de21b40bde00315aa01008052e2031faa00000094e007442de22b40bde00315aa21008052e2031faa0000009406000014e00315aa01008052e2031faa000000943a008052f60400b4e00316aae1031faa00000094600400b45f030071e1079f1ae2031faa000000945f0b007101020054e003271ee103271ee203271e03102e1ee00316aae1031faa00000094e007442de22b40bd03102d1e2138231ee00316aae1031faa000000940e000014e003271ee103271ee203271ee00316aae1031faa00000094e003271ee103271ee203271e03102e1ee00316aae1031faa00000094e8274b6dfd7b4aa9f96b49a9f76348a9f55b47a9f35346a9e00745a9ff0303910828443900000014e0031f2ae82e40b91f01186b29010054e81e40f9e80000b4097f60d30871898b080540b909ff60d31f01096be0179f1ac0035fd61f2003d546b20890bafdc103abf4b4c1000040401888a73ff30435405046425f46585f57504e5f53636f7270696f6e466c61696c5f547261696c004c696e6552656e646572657200515f576561706f6e56697375616c5f53636f7270696f6e466c61696c2f53636f7270696f6e5f466c61696c2f53636f7270696f6e466c61696c5f42616c6c00515f576561706f6e56697375616c5f53636f7270696f6e466c61696c2f50726f6a656374696c654f726967696e005f436f6c6f724d756c74001f2003d5')
FLAIL_VIEW_USES = [(60, 'ext_get_transform'), (76, 'ext_string_new'), (92, 'ext_find'), (104, 'ext_get_gameobject'), (120, 'ext_string_new'), (136, 'ext_get_component_by_name'), (152, 'ext_string_new'), (168, 'ext_find'), (180, 'ext_string_new'), (196, 'ext_find'), (212, 'ext_get_position'), (228, 'ext_observed_game'), (252, 'slot'), (264, 'ext_init_metadata'), (268, 'slot'), (292, 'ext_init_rgctx'), (324, 'ext_try_get_pointer'), (360, 'ext_get_entity_view'), (372, 'ext_get_transform'), (384, 'ext_get_position'), (424, 'ext_get_entity_view'), (436, 'ext_get_transform'), (448, 'ext_get_position'), (464, 'ext_time'), (484, 'ext_cos'), (500, 'ext_sin'), (552, 'ext_get_material'), (568, 'ext_string_new'), (600, 'ext_set_color'), (616, 'ext_set_position_count'), (640, 'ext_line_set_position'), (664, 'ext_line_set_position'), (684, 'ext_set_position_count'), (704, 'ext_get_gameobject'), (724, 'ext_set_active'), (760, 'ext_set_rotation'), (788, 'ext_set_position'), (816, 'ext_set_local_position'), (844, 'ext_set_local_rotation'), (884, 'ext_back')]
FLAIL_VIEW_TARGETS = {'ext_get_transform': 142923708, 'ext_string_new': 63431916, 'ext_find': 143030524, 'ext_get_gameobject': 142923916, 'ext_get_component_by_name': 142935700, 'ext_get_position': 143014424, 'ext_observed_game': 66468604, 'ext_init_metadata': 63400440, 'ext_init_rgctx': 63636616, 'ext_try_get_pointer': 87024380, 'slot': 153002032, 'ext_get_entity_view': 66468228, 'ext_time': 142998892, 'ext_cos': 142867152, 'ext_sin': 142867052, 'ext_set_position_count': 142549188, 'ext_line_set_position': 142552548, 'ext_set_active': 142943076, 'ext_set_rotation': 143015944, 'ext_set_position': 143014636, 'ext_set_local_position': 143009856, 'ext_set_local_rotation': 143016380, 'ext_get_material': 142570704, 'ext_set_color': 142635424}

def place_assembled(data, at_address, code, uses, targets, back):
    code = bytearray(code)
    for offset, name in uses:
        if name.startswith('slot'):
            c = Code(at_address + offset)
            adrp_ldr(c, struct.unpack('<I', code[offset + 4:offset + 8])[0] & 31, targets[name])
            code[offset:offset + 8] = c.build()
            continue
        target = back if name.endswith('_back') else targets[name]
        word = struct.unpack('<I', code[offset:offset + 4])[0]
        code[offset:offset + 4] = (a64.bl if word >> 26 == 37 else a64.b)(at_address + offset, target)
    at(data, at_address, bytes(data[at_address:at_address + len(code)]), bytes(code))
FLAIL_ENHANCEMENTS_CODE = 72330704 + 4864
FLAIL_ENHANCEMENTS_END = 72330704 + 5660
FLAIL_ENHANCEMENTS_TARGETS = {'ext_init_metadata': 63400440, 'ext_class_init': 63636616, 'ext_try_get_pointer': 86994632, 'slot_loadout': 153006760, 'slot_aoe': 153007576, 'slot_pusher': 153007680}

def patch_flail_spin(data):
    hook, cave = BUILD['flail_spin']
    if 'flail_enhancements' in BUILD:
        code, uses, labels = assemble_source('fleau_ameliorations.s')
        if FLAIL_ENHANCEMENTS_CODE + len(code) > FLAIL_ENHANCEMENTS_END:
            raise SystemExit('plus de place pour les ameliorations du fleau')
        code = bytearray(code)
        code[labels['mega_gain']:labels['mega_gain'] + 8] = fp(FLAIL_MEGASPIN_RADIUS / FLAIL_SPIN_RANGE)
        code[labels['torque_pusher']:labels['torque_pusher'] + 8] = struct.pack('<q', BUILD['flail_enhancements']['torque_pusher'][3])
        if os.environ.get('RR_JOURNAL'):
            code[labels['journal']:labels['journal'] + 4] = struct.pack('<I', 1)
        place_assembled(data, FLAIL_ENHANCEMENTS_CODE, bytes(code), uses, dict(FLAIL_ENHANCEMENTS_TARGETS, ext_string_new=BUILD['string_new'], ext_debug_log=DEBUG_LOG), None)
        code, uses, labels = assemble_source('fleau_toupie.s')
        if cave + len(code) > BUILD['flail_view'][1]:
            raise SystemExit('plus de place pour le tourbillon du fleau')
        targets = {'ext%d_%s' % (i, name): address for i, (name, address) in enumerate((('button_is_down', 130965704), ('is_dead', 129714756), ('team_id', 130417996), ('create_dynamic', 129888084), ('init_metadata', 63400440), ('set_hierarchy', 82550228), ('destroy', 131170080)))}
        targets.update(ext8_enhancements=FLAIL_ENHANCEMENTS_CODE, slot=SLOT_SET_HIERARCHY)
        place_assembled(data, cave, code, uses, targets, hook + 4)
    else:
        code = bytearray(FLAIL_SPIN_CODE)
        for offset, target in FLAIL_SPIN_CALLS.items():
            code[offset:offset + 4] = a64.bl(cave + offset, target)
        code[FLAIL_SPIN_BACK:FLAIL_SPIN_BACK + 4] = a64.b(cave + FLAIL_SPIN_BACK, hook + 4)
        for offset, register in FLAIL_SPIN_SLOT:
            c = Code(cave + offset)
            adrp_ldr(c, register, SLOT_SET_HIERARCHY)
            code[offset:offset + 8] = c.build()
        at(data, cave, bytes(data[cave:cave + len(code)]), bytes(code))
    at(data, hook, bytes.fromhex('ffc301d1'), a64.b(hook, cave))
    view_hook, view_cave = BUILD['flail_view']
    if 'flail_enhancements' in BUILD:
        code, uses, _ = assemble_source('fleau_vue.s')
        if view_cave + len(code) > BUILD['flail_auto'][2]:
            raise SystemExit('plus de place pour la vue du fleau')
        place_assembled(data, view_cave, code, uses, dict(FLAIL_VIEW_TARGETS, slot_aoe=FLAIL_ENHANCEMENTS_TARGETS['slot_aoe']), view_hook + 4)
    else:
        place_assembled(data, view_cave, FLAIL_VIEW_CODE, FLAIL_VIEW_USES, FLAIL_VIEW_TARGETS, view_hook + 4)
    at(data, view_hook, bytes.fromhex('08284439'), a64.b(view_hook, view_cave))

def try_fix_code(at_address, back, skip):
    c = Code(at_address)
    c.jump('cbz', 'no_screen', 0)
    c.emit(bytes.fromhex('e80240f9'))
    c.emit(a64.b(c.here(), back))
    c.label('no_screen')
    c.emit(a64.mov_x_zero(22))
    c.emit(a64.b(c.here(), skip))
    return c.build()

def patch_try_fix(data):
    hook, skip, cave = BUILD['try_fix']
    code = try_fix_code(cave, hook + 4, skip)
    at(data, cave, bytes(data[cave:cave + len(code)]), code)
    at(data, hook, bytes.fromhex('e80240f9'), a64.b(hook, cave))
FLAIL_BLUEPRINT_SCALE = 0.85
IMAGE_SET_SPRITE = 144176752
GRAPHIC_GET_RECT_TRANSFORM = 144211324
RECT_TRANSFORM_GET_RECT = 143007464
RECT_TRANSFORM_GET_SIZE_DELTA = 143008836
RECT_TRANSFORM_SET_SIZE_DELTA = 143009032

def flail_blueprint_code(at_address):
    c = Code(at_address)
    c.emit(a64.stp_x_pre(29, 30, a64.SP, -48))
    c.emit(a64.stp_x(0, 1, a64.SP, 16))
    c.emit(a64.str_x(2, a64.SP, 32))
    c.call(IMAGE_SET_SPRITE)
    c.emit(a64.ldr_x(9, 22, 24))
    c.jump('ldrlit', 'guid', 10)
    c.emit(a64.cmp_x(9, 10))
    c.emit(w32(446633963))
    c.emit(w32(960579212))
    c.emit(w32(1795948927))
    c.jump('b.eq', 'done')
    c.emit(w32(956384907))
    c.emit(w32(3103796203))
    c.emit(a64.ldr_x(0, a64.SP, 16))
    c.emit(a64.mov_x_zero(1))
    c.call(GRAPHIC_GET_RECT_TRANSFORM)
    c.jump('cbz', 'done', 0)
    c.emit(a64.str_x(0, a64.SP, 24))
    c.emit(a64.mov_x_zero(1))
    c.call(RECT_TRANSFORM_GET_RECT)
    c.emit(w32(755240930))
    c.emit(a64.ldr_x(0, a64.SP, 24))
    c.emit(a64.mov_x_zero(1))
    c.call(RECT_TRANSFORM_GET_SIZE_DELTA)
    c.emit(w32(759435234))
    c.emit(w32(3107990507))
    c.jump('cbnzw', 'shrink', 11)
    c.jump('ldrlit_s', 'grow_k', 4)
    c.emit(w32(505677893))
    c.emit(w32(505677926))
    c.emit(w32(505751552))
    c.emit(w32(505817121))
    c.jump('b', 'apply')
    c.label('shrink')
    c.jump('ldrlit_s', 'shrink_k', 4)
    c.emit(w32(505677893))
    c.emit(w32(505677926))
    c.emit(w32(505755648))
    c.emit(w32(505821217))
    c.label('apply')
    c.emit(a64.ldr_x(0, a64.SP, 24))
    c.emit(a64.mov_x_zero(1))
    c.call(RECT_TRANSFORM_SET_SIZE_DELTA)
    c.label('done')
    c.emit(a64.ldp_x_post(29, 30, a64.SP, 48))
    c.emit(a64.RET)
    while len(c.code) % 8:
        c.emit(a64.NOP)
    c.label('guid')
    c.emit(struct.pack('<q', FLAIL_SPEC_GUID))
    c.label('shrink_k')
    c.emit(struct.pack('<f', 1 - FLAIL_BLUEPRINT_SCALE))
    c.label('grow_k')
    c.emit(struct.pack('<f', 1 / FLAIL_BLUEPRINT_SCALE - 1))
    return c.build()

def patch_flail_blueprint(data):
    hook, cave = BUILD['flail_blueprint']
    code = flail_blueprint_code(cave)
    at(data, cave, bytes(data[cave:cave + len(code)]), code)
    at(data, hook, a64.bl(hook, IMAGE_SET_SPRITE), a64.bl(hook, cave))

def patch_flail_auto(data):
    widget, fetch, cave, cave_end, delta_time, component = BUILD['flail_auto']
    code, entries = flail_auto_code(cave, delta_time, component)
    if cave + len(code) > cave_end:
        raise SystemExit('plus de place pour le tir automatique du fleau')
    at(data, cave, bytes(data[cave:cave + len(code)]), code)
    if widget:
        at(data, widget, bytes.fromhex('08bd4639'), a64.bl(widget, entries['widget']))
    at(data, fetch, bytes.fromhex('e8b79f1a'), a64.bl(fetch, entries['input']))
FLAIL_AUTO_PRESS, FLAIL_AUTO_GAP = (0.08, 0.15)
FLAIL_SPEC_GUID = 3873562517302156309

def flail_auto_code(at_address, delta_time, component):
    c = Code(at_address)
    journal = bool(os.environ.get('RR_JOURNAL')) and os.environ.get('RR_VERSION') != '1.10.3'
    c.label('widget')
    c.emit(a64.ldr_x(9, 8, 24))
    c.jump('ldrlit', 'guid', 10)
    c.emit(bytes.fromhex('08bd4639'))
    c.emit(a64.cmp_x(9, 10))
    c.emit(w32(445121512))
    c.emit(a64.RET)
    c.label('input')
    c.emit(w32(446674920))
    c.emit(a64.ldr_x(9, a64.SP, component))
    c.jump('cbz', 'out', 9)
    c.emit(a64.ldr_x(9, 9, 112))
    c.jump('cbz', 'out', 9)
    c.emit(a64.ldr_x(9, 9, 24))
    c.jump('ldrlit', 'guid', 10)
    c.emit(a64.cmp_x(9, 10))
    c.jump('b.ne', 'out')
    c.emit(w32(505946400))
    c.jump('b.lt', 'counted')
    c.emit(a64.stp_x_pre(29, 30, a64.SP, -16))
    c.call(delta_time)
    c.emit(a64.ldp_x_post(29, 30, a64.SP, 16))
    c.emit(w32(505424169))
    c.label('counted')
    c.emit(w32(3170987625))
    c.emit(a64.movz_w(8, 0))
    c.emit(w32(505422120))
    c.jump('b.lt', 'manual')
    c.jump('ldrlit_s', 'press', 1)
    c.emit(w32(505487648))
    c.jump('b.ge', 'release')
    c.emit(a64.movz_w(8, 1))
    c.jump('b', 'manual')
    c.label('release')
    c.jump('ldrlit_s', 'gap', 1)
    c.emit(w32(505495584))
    c.emit(w32(3170987616))
    if journal:
        c.emit(a64.stp_x_pre(29, 30, a64.SP, -16))
        c.jump('adr', 'log_tap', 0)
        c.call(BUILD['string_new'])
        c.emit(a64.mov_x_zero(1))
        c.call(DEBUG_LOG)
        c.emit(a64.ldp_x_post(29, 30, a64.SP, 16))
    c.emit(a64.movz_w(8, 0))
    c.label('manual')
    c.emit(w32(960787049))
    c.emit(w32(705233160))
    c.label('out')
    c.emit(a64.RET)
    while len(c.code) % 8:
        c.emit(a64.NOP)
    c.label('guid')
    c.emit(struct.pack('<q', FLAIL_SPEC_GUID))
    c.label('press')
    c.emit(struct.pack('<f', FLAIL_AUTO_PRESS))
    c.label('gap')
    c.emit(struct.pack('<f', FLAIL_AUTO_GAP))
    if journal:
        c.label('log_tap')
        c.emit(b'RR fleau: tape auto\x00\x00\x00\x00')
    return (c.build(), {name: at_address + c.labels[name] for name in ('widget', 'input')})

def patch_flail(data):
    cave = BUILD['flail_cave']
    for hook, add, pair in BUILD['flail_tables']:
        code = (bytes.fromhex('a30240f9') if pair else bytes.fromhex('a20240f9')) + bytes.fromhex('e00313aa') + bytes.fromhex('21018052') + (bytes.fromhex('22018052') if pair else b'')
        code += a64.bl(cave + len(code), add)
        code += bytes.fromhex('880240f9')
        code += a64.b(cave + len(code), hook + 4)
        at(data, cave, bytes(data[cave:cave + len(code)]), code)
        at(data, hook, bytes.fromhex('880240f9'), a64.b(hook, cave))
        cave += len(code)
    if cave > BUILD['disable_feature'] + 192:
        raise SystemExit('code du fleau trop long')
FLAIL_CARD_SPRITE = struct.pack('<iq', 2, -892389288878691980)
FLAIL_SMALL_SPRITE = struct.pack('<iq', 2, -7903905403463771795)
FLAIL_MAX_AMMO, FLAIL_AMMO_PER_THROW = (8, 1)
FLAIL_DAMAGE_FACTORS = (2.5, 4.0)
FLAIL_SPIN_UP, FLAIL_SPIN_RANGE = (0.15, 3.5)
FLAIL_SPIN_AMMO_PER_SECOND = 1
FLAIL_FIRE_RATE = 2.5
FLAIL_PROJECTILE_SPEED = 45.0
FLAIL_HOMING = 30.0
FLAIL_WIND_UP = 0.08

def fp(value):
    return struct.pack('<q', round(value * 65536))

def flail_tuning(data):
    stream = bundle_stream(bytes(data))
    edits = []
    for (base, levels), factor in zip(BUILD['flail_damage'], FLAIL_DAMAGE_FACTORS, strict=True):
        old = stream[base:base + 8]
        edits.append((base, old, struct.pack('<q', round(struct.unpack('<q', old)[0] * factor))))
        if struct.unpack('<i', stream[levels:levels + 4])[0] != 10:
            raise SystemExit('degats du fleau introuvables')
        old = stream[levels + 4:levels + 84]
        new = b''.join((struct.pack('<q', round(value * factor)) for value in struct.unpack('<10q', old)))
        edits.append((levels + 4, old, new))
    if 'flail_spin_spec' in BUILD:
        spin = BUILD['flail_spin_spec']
        edits.append((spin, struct.pack('<qq', 26214, 98304), fp(FLAIL_SPIN_UP) + fp(FLAIL_SPIN_RANGE)))
        edits.append((spin + 24, struct.pack('<I', 2), struct.pack('<I', FLAIL_SPIN_AMMO_PER_SECOND)))
    return edits
FLAIL_ENHANCEMENT_ICON_FILE = 14
FLAIL_MEGASPIN = ('UI.WEAPON_ENHANCEMENT.SCORPIONFLAIL_MEGASPIN', 'UI.WEAPON_ENHANCEMENT_DESC.SCORPIONFLAIL_MEGASPIN', -2661239679859494153)
FLAIL_TORQUE = ('UI.WEAPON_ENHANCEMENT.SCORPIONFLAIL_TORQUE', 'UI.WEAPON_ENHANCEMENT_DESC.SCORPIONFLAIL_TORQUE', 7827935356404167415)
FLAIL_TORQUE_PUSH = 1.5
FLAIL_MEGASPIN_RADIUS = 1.0
FLAIL_ENHANCEMENT_TEXTS = {'EN': ('Mega Spin', 'After 2 seconds of spinning, the spin grows 1 m wider.', 'Torque Impact', 'After 2 seconds of spinning, the spin pushes enemies 50% harder.'), 'FR': ('Méga toupie', "Après 2 secondes de tourbillon, il s'élargit d'un mètre.", 'Impact de couple', 'Après 2 secondes de tourbillon, il repousse les ennemis 50 % plus fort.')}

def flail_enhancement_texts(language):
    mega, mega_desc, torque, torque_desc = FLAIL_ENHANCEMENT_TEXTS.get(language) or FLAIL_ENHANCEMENT_TEXTS['EN']
    return {FLAIL_MEGASPIN[0]: mega, FLAIL_MEGASPIN[1]: mega_desc, FLAIL_TORQUE[0]: torque, FLAIL_TORQUE[1]: torque_desc}

def read_unity_string(raw, position):
    size, = struct.unpack_from('<I', raw, position)
    end = position + 4 + size
    return (raw[position + 4:end].decode(), end + -size % 4)

def flail_enhancement_spec(texts):
    name_key, description_key, icon = texts

    def change(old):
        _, position = read_unity_string(old, 28)
        head = old[:position]
        _, position = read_unity_string(old, position)
        position += 4 + 12
        _, position = read_unity_string(old, position)
        position += 4
        path, end = read_unity_string(old, position)
        identifier = old[position:end + 8]
        position = end + 8
        modifiers, = struct.unpack_from('<I', old, position)
        position += 4 + modifiers * 16
        apply_to, weapon, slot, inner = struct.unpack_from('<4I', old, position)
        if apply_to != 0 or slot != 0 or len(old) != position + 16 + inner * 8 or ('/Enhancements/' not in path):
            raise SystemExit('amelioration reprise inattendue')
        return head + raw_text(name_key) + struct.pack('<iq', FLAIL_ENHANCEMENT_ICON_FILE, icon) + raw_text(description_key) + identifier + struct.pack('<5I', 0, 0, 9, 0, 0)
    return change

def flail_torque_pusher(spin, guid):

    def change(old):
        _, position = read_unity_string(old, 28)
        _, position = read_unity_string(old, position)
        _, position = read_unity_string(old, position + 4 + 12)
        identifier_start = position + 4
        _, identifier_end = read_unity_string(old, identifier_start)
        if struct.unpack_from('<q', old, identifier_end)[0] != guid:
            raise SystemExit('poussee reprise inattendue')
        identifier = old[identifier_start:identifier_end + 8]
        _, position = read_unity_string(spin, 28)
        _, spin_end = read_unity_string(spin, position)
        forces = spin_end + 8 + 8
        count, = struct.unpack_from('<I', spin, forces + 16)
        values = struct.unpack_from(f'<q8xI{count}q', spin, forces)
        if count != 10 or values[1] != count:
            raise SystemExit('poussee du tourbillon inattendue')
        stronger = [round(value * FLAIL_TORQUE_PUSH) for value in (values[0], *values[2:])]
        return spin[:28] + unity_string('Q_ScorpionFlail_TorqueImpact_PusherSpec') + identifier + spin[spin_end + 8:forces] + struct.pack('<q', stronger[0]) + spin[forces + 8:forces + 20] + struct.pack(f'<{count}q', *stronger[1:]) + spin[forces + 20 + count * 8:]
    return change

def flail_enhancement_objects(stream):
    enh = BUILD['flail_enhancements']
    table, count = enh['table']
    data_offset = struct.unpack_from('>Q', stream, 32)[0]
    if struct.unpack_from('<i', stream, table - 4)[0] != count:
        raise SystemExit('table des armes inattendue')
    spin_id, spin_start, spin_size = enh['spin_pusher']
    spin = bytes(stream[data_offset + spin_start:data_offset + spin_start + spin_size])
    pusher_type, pusher_script = enh['pusher_type']
    if spin[16:28] != struct.pack('<iq', 1, pusher_script):
        raise SystemExit('poussee du tourbillon introuvable')
    mega_id, mega_start, mega_size, mega_guid = enh['mega']
    torque_id, torque_start, torque_size, torque_guid = enh['torque']
    pusher_id, pusher_start, pusher_size, pusher_guid = enh['torque_pusher']
    spec_id, spec_start, spec_size = enh['weapon_spec']

    def upgrades_list(old):
        tail = len(old) - 24
        if old[tail:] != struct.pack('<iiqq', 0, 0, 98304, 196608):
            raise SystemExit('fiche du fleau inattendue')
        return old[:tail] + struct.pack('<iqq', 2, mega_guid, torque_guid) + old[tail + 4:]

    def torque_pusher(old):
        return spin[:16] + struct.pack('<iq', 1, pusher_script) + flail_torque_pusher(spin, pusher_guid)(old)[28:]
    return grow_objects(stream, table, count, {spec_id: (spec_start, spec_size, upgrades_list), mega_id: (mega_start, mega_size, flail_enhancement_spec(FLAIL_MEGASPIN)), torque_id: (torque_start, torque_size, flail_enhancement_spec(FLAIL_TORQUE)), pusher_id: (pusher_start, pusher_size, torque_pusher)}, shrink=True, types={pusher_id: pusher_type})

def patch_flail_spec(data):
    colored, model, small = BUILD['flail_sprites']
    empty = bytes(12)
    edits = flail_tuning(data) + [(BUILD['flail_spec'][1], struct.pack('<i', 2), struct.pack('<i', 0)), (colored, empty, FLAIL_CARD_SPRITE), (model, empty, FLAIL_CARD_SPRITE), (small, empty, FLAIL_SMALL_SPRITE), (BUILD['flail_reload'], struct.pack('<i', 0), struct.pack('<i', 1)), (BUILD['flail_ammo'], struct.pack('<II', 12, 4), struct.pack('<II', FLAIL_MAX_AMMO, FLAIL_AMMO_PER_THROW)), (BUILD['flail_fire_button'], struct.pack('<i', 0), struct.pack('<i', 1)), *([] if 'flail_auto' in BUILD else [(BUILD['flail_autoshoot'], struct.pack('<i', 1), struct.pack('<i', 0))]), *flail_spin_aoe_edits(), *([(BUILD['flail_fire_rate'], struct.pack('<q', 93623), fp(FLAIL_FIRE_RATE))] if 'flail_fire_rate' in BUILD else []), *([(BUILD['flail_projectile_speed'], fp(20.0), fp(FLAIL_PROJECTILE_SPEED))] if 'flail_projectile_speed' in BUILD else []), *([(BUILD['flail_homing'], fp(10.0), fp(FLAIL_HOMING))] if 'flail_homing' in BUILD else []), *([(BUILD['flail_anticipation'], fp(0.25), fp(FLAIL_WIND_UP))] if 'flail_anticipation' in BUILD else [])]
    if 'flail_enhancements' not in BUILD:
        patch_bundle(data, edits)
        return
    stream = bytearray(bundle_stream(bytes(data)))
    limit = BUILD['flail_enhancements']['limit_scale']
    edits.append((limit - 4, struct.pack('<ii', 9, 1), struct.pack('<ii', 9, 0)))
    for offset, old, new in edits:
        at(stream, offset, old, new)
    replace_bundle_stream(data, stream, flail_enhancement_objects(stream))

def flail_spin_aoe_edits():
    if 'flail_spin_aoe' not in BUILD:
        return []
    radius, starts, infinite, duration = BUILD['flail_spin_aoe']
    release = BUILD['flail_fire_button'] - 16
    return [(radius, fp(1.0), fp(FLAIL_SPIN_RANGE)), (starts, struct.pack('<i', 0), struct.pack('<i', 1)), (infinite, struct.pack('<i', 1), struct.pack('<i', 0)), (duration, fp(0.0), fp(1.0)), (release, struct.pack('<i', 0) + fp(1.0), struct.pack('<i', 1) + fp(0.05))]
if os.environ.get('RR_VERSION') == '1.10.3':
    WEAPON_LEVEL_CODE = 67876648 + 4
    LOADING_SCREEN_CODE = 67876648 + 1136 - 64
    EVENTS_CODE = 67897656
    EVENTS_CODE_END = EVENTS_CODE + 1632
    HERO_RETURN_CODE = EVENTS_CODE_END - 384 & ~15
    LOADOUT_ITEM_HERO_LEVEL = 69421412
    MAIN_WEAPON_RETURN = 69421068
    GET_HERO_LEVEL = 69421468
    GET_WEAPON_QUANTUM_LEVEL = 69422024
    GET_WEAPON_UPGRADE_QUANTUM_LEVEL = 69442952
    GET_ECONOMY = 68304696
    GET_BASE_SKIN = 74923360
    GET_CHAR_DEF_BY_SKIN = 66589572
    OPEN_WEAPON_INFO_POPUP = 67469468
    GAME_FSM_INSTANCE = 70281940
    USER_INSTANCE = 69405360
    CAN_EQUIP_HERO_SKIN = 69413856
    EQUIP_SKIN = 69413964
    GET_AT_SLOT = 74975776
    TO_CHARACTER_ID = 68351700
    GET_DEFAULT_WEAPON_UID = 66599424
    WEAPON_WIDGET_DEFAULT_WEAPON = 67225296
    INIT_METADATA = 63350700
    MONO_SINGLETON_GET_INSTANCE = 103000756
    COMPONENT_GET_COMPONENT = 80028860
    HUD_CHARACTER_BIND_DATA = 67455868
    SLOT_MONO_SINGLETON = 152346728
    SLOT_GET_HUD_CHARACTER = 152348712
    MAX_AMMO_ONCE = 68309856
    GET_OBSERVED_GAME = 66422708
    GAME_OBJECT_SEND_MESSAGE = 142816984
    GET_GAME_OBJECT = 142801532

def patch_library(data):
    patch_code(data)
    if 'hero_models' in BUILD:
        patch_loading_screen(data)
    if 'flail_tables' in BUILD:
        patch_flail(data)
    if 'flail_spin' in BUILD:
        patch_flail_spin(data)
    if 'flail_auto' in BUILD:
        patch_flail_auto(data)
    if 'try_fix' in BUILD:
        patch_try_fix(data)
    if 'outline_silhouette' in BUILD:
        offset, old, new = BUILD['outline_silhouette']
        at(data, offset, bytes.fromhex(old), bytes.fromhex(new))
    if 'flail_blueprint' in BUILD:
        patch_flail_blueprint(data)
    if BOLT_RUSH:
        patch_bolt_rush_code(data)
    if BOLT_RUSH or os.environ.get('RR_VERSION') == '1.10.3':
        patch_weapons_code(data)
    if weapon_slots_build():
        patch_weapon_slots(data)
    if EVENTS:
        patch_events_code(data)
    if 'hero_models' in BUILD:
        new_skin_code(data)
        if 'Rivet' in hero_sources()[0] and os.environ.get('RR_VERSION', '1.10.4') == '1.10.4':
            patch_rivet_legendary(data)
HEROES_RESOURCES = os.environ.get('RR_HEROS_DOSSIER') or os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'appli_patch', 'ressources', 'heros')
_hero_sources = []
CDN_SKINS = ['Molly_Skin01', 'Molly_Skin02', 'Molly_Skin03', 'Molly_Skin05', 'Terry_Skin01', 'Terry_Skin02', 'Terry_Skin04', 'Helen_Skin01', 'Juycee_Skin01', 'Juycee_Skin02', 'Juycee_Skin03', 'Juycee_Skin04']
COSTUMES = os.environ.get('RR_COSTUMES') or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'costumes_cdn')

def relinked(data):
    data = bytearray(data)
    stream = bundle_stream(bytes(data))
    edits = []
    for old, new in RENAMED_FILES.items():
        edits += [(match.start(), old, new) for match in re.finditer(re.escape(old), stream)]
    patch_bundle(data, edits)
    return bytes(data)

def readable_meshes(data):
    try:
        import UnityPy
    except ImportError:
        return data
    env = UnityPy.load(data)
    changed = False
    for obj in env.objects:
        if obj.type.name == 'Mesh':
            tree = obj.read_typetree()
            if not tree.get('m_IsReadable', True):
                tree['m_IsReadable'] = True
                obj.save_typetree(tree)
                changed = True
    return env.file.save(packer='lz4') if changed else data
HELEN_BODY_MATERIAL = -6441128803313224469
HELEN_MOSS_MESH = 'Warbot_Helen_00_Grass'
DIMENSIONAL_MATERIAL = -2648583136596989548
DIMENSIONAL_BUNDLE = 'skins_character_helen_skin01rr_assets_all_5d1f0c3a9e7b4268a1c2e3f405162738.bundle'
DIMENSIONAL_CAB = 'CAB-5d1f0c3a9e7b4268a1c2e3f405162738'

def dimensional_helen(base, costume):
    import copy
    import UnityPy
    costume_env = UnityPy.load(costume)
    costume_cab = next((name for name in costume_env.file.files if not name.endswith('.resS')))
    env = UnityPy.load(base)
    old_cab = next((name for name in env.file.files if not name.endswith('.resS')))
    serialized = env.file.files[old_cab]
    renamed = {}
    for name, item in env.file.files.items():
        renamed[name.replace(old_cab, DIMENSIONAL_CAB)] = item
    env.file.files = renamed
    serialized.name = DIMENSIONAL_CAB
    link = copy.copy(serialized.externals[0])
    link.path = f'archive:/{costume_cab}/{costume_cab}'
    serialized.externals.append(link)
    costume_file = len(serialized.externals)
    meshes = {}
    for obj in serialized.objects.values():
        if obj.type.name == 'Mesh':
            meshes[obj.path_id] = obj.read_typetree()['m_Name']
    for obj in list(serialized.objects.values()):
        kind = obj.type.name
        if kind in ('Texture2D', 'Mesh'):
            tree = obj.read_typetree()
            if tree['m_StreamData']['path']:
                tree['m_StreamData']['path'] = tree['m_StreamData']['path'].replace(old_cab, DIMENSIONAL_CAB)
                obj.save_typetree(tree)
        elif kind == 'SkinnedMeshRenderer':
            tree = obj.read_typetree()
            if tree['m_Mesh']['m_FileID'] == 0 and meshes.get(tree['m_Mesh']['m_PathID']) == HELEN_MOSS_MESH:
                tree['m_Enabled'] = 0
            for material in tree['m_Materials']:
                if material['m_FileID'] == 0 and material['m_PathID'] == HELEN_BODY_MATERIAL:
                    material['m_FileID'], material['m_PathID'] = (costume_file, DIMENSIONAL_MATERIAL)
            obj.save_typetree(tree)
        elif kind == 'AssetBundle':
            tree = obj.read_typetree()
            name = DIMENSIONAL_BUNDLE.replace('.bundle', '')
            tree['m_Name'] = tree['m_AssetBundleName'] = name
            tree['m_Container'] = [(path.replace('Character_Helen.prefab', 'Character_Helen_Skin01.prefab'), info) for path, info in tree['m_Container']]
            obj.save_typetree(tree)
    return env.file.save(packer='lz4')
RIVET_BUNDLE = 'skins_character_rivet_assets_all_9a6c1e2f4b8d7035e1f2a3b4c5d6e7f8.bundle'
RIVET_CAB = 'CAB-9a6c1e2f4b8d7035e1f2a3b4c5d6e7f8'
RIVET_MODEL_BUNDLE = 'legacy_character_rivetrr_assets_all_3e7b9d1c5a2f4e6081b3c5d7e9f1a2b4.bundle'
RIVET_MODEL_CAB = 'CAB-3e7b9d1c5a2f4e6081b3c5d7e9f1a2b4'
RIVET_GUID = '7c1e5a9f3b2d4e8f9a0b1c2d3e4f5a6b'
PLAYABLE_RATCHET_GUID = 'a912ebcc145a6144cba7b5bcc6f50a71'
RIVET_HEAD_SCALE = 0.88
CINEMATIC_HEROES = {'Rivet': {'source': 'legacy_character_rivet_assets_all', 'bundle': RIVET_BUNDLE, 'cab': RIVET_CAB, 'model_bundle': RIVET_MODEL_BUNDLE, 'model_cab': RIVET_MODEL_CAB, 'guid': RIVET_GUID, 'renderers': {'Legacy_Ratchet_00': 'Legacy_Rivet_00', 'Lombax_Sandy_face_blendshapes': 'Legacy_Rivet_00_Head'}, 'stand_ins': {'B_jaw': 'B_Head', 'B_Hair': 'B_Head'}, 'head_bones': ['B_Head', 'B_head-scale'], 'head_scale': RIVET_HEAD_SCALE, 'body_scale': 1.15}, 'Wendy': {'source': 'legacy_character_none_assets_all', 'bundle': 'skins_character_wendy_assets_all_4b7d2e9a1c6f3058e2d4a6b8c0e1f3a5.bundle', 'cab': 'CAB-4b7d2e9a1c6f3058e2d4a6b8c0e1f3a5', 'model_bundle': 'legacy_character_wendyrr_assets_all_8e2c4a6b1d3f5e7092a4c6e8b0d2f4a6.bundle', 'model_cab': 'CAB-8e2c4a6b1d3f5e7092a4c6e8b0d2f4a6', 'guid': '5d8f2b6e9a1c4d7e8f0a2b4c6d8e0f13', 'renderers': {'Legacy_Ratchet_00': 'Wendy_01', 'Lombax_Sandy_face_blendshapes': 'Wendy_Face_01', 'Clank_Backpack': 'Wendy_Good_01', 'Clank_Backpack_UpperEyelid': 'Wendy_01a', 'Clank_Backpack_LowerEyelid': None}, 'stand_ins': {'B_head': 'B_head-scale', 'B_jaw': 'B_head-scale', 'B_glasses': 'B_head-scale'}, 'head_bones': ['B_head'], 'head_scale': RIVET_HEAD_SCALE}}

def asset_pack_bundle(family):
    for name in sorted(os.listdir(xapk)):
        if name.endswith('.apk'):
            pack = zipfile.ZipFile(os.path.join(xapk, name))
            for entry in pack.namelist():
                if entry.endswith('.bundle') and bundle_family_of(entry) == family:
                    return (entry, pack.read(entry))
    return (None, None)

def bundle_family_of(path):
    return re.sub('_[0-9a-f]{32}\\.bundle$', '', os.path.basename(path))

def playable_ratchet_families():
    for name in sorted(os.listdir(xapk)):
        if name.endswith('.apk'):
            pack = zipfile.ZipFile(os.path.join(xapk, name))
            if 'assets/aa/catalog.bin' in pack.namelist():
                catalog = heros_caches.Catalog(pack.read('assets/aa/catalog.bin'))
                for _, key, locations in catalog.entries():
                    if str(key) == PLAYABLE_RATCHET_GUID and locations:
                        return [heros_caches.bundle_family(catalog.string(catalog.location(offset)[0])) for offset in catalog.array(catalog.location(locations[0])[3])]
    return []

def renamed_bundle(data, new_cab):
    import UnityPy
    env = UnityPy.load(data)
    old_cab = next((name for name in env.file.files if not name.endswith('.resS')))
    serialized = env.file.files[old_cab]
    env.file.files = {name.replace(old_cab, new_cab): item for name, item in env.file.files.items()}
    serialized.name = new_cab
    for obj in list(serialized.objects.values()):
        if obj.type.name in ('Texture2D', 'Mesh'):
            tree = obj.read_typetree()
            if tree['m_StreamData']['path']:
                tree['m_StreamData']['path'] = tree['m_StreamData']['path'].replace(old_cab, new_cab)
                obj.save_typetree(tree)
    return (env, serialized)

def matrix(pose):
    import numpy
    return numpy.array([[pose[f'e{r}{c}'] for c in range(4)] for r in range(4)], dtype=float)

def pose(values):
    return {f'e{r}{c}': float(values[r][c]) for r in range(4) for c in range(4)}

def cinematic_hero_bundles(key):
    if not heavy_tools():
        return []
    import copy
    import numpy
    spec = CINEMATIC_HEROES[key]
    _, ratchet = asset_pack_bundle('skins_character_ratchet_00_playable_assets_all')
    _, source = asset_pack_bundle(spec['source'])
    if not ratchet or not source:
        return []
    env, playable = renamed_bundle(ratchet, spec['cab'])
    model_env, model = renamed_bundle(source, spec['model_cab'])

    def transform_name(objects, transform):
        game_object = objects[transform].read_typetree()['m_GameObject']['m_PathID']
        return objects[game_object].read_typetree()['m_Name']

    def renderers(objects):
        for obj in objects.values():
            if obj.type.name == 'SkinnedMeshRenderer':
                tree = obj.read_typetree()
                yield (obj, tree, objects[tree['m_GameObject']['m_PathID']].read_typetree()['m_Name'])
    body = next((tree for _, tree, name in renderers(playable.objects) if name == 'Legacy_Ratchet_00'))
    his = {transform_name(playable.objects, bone['m_PathID']): bone['m_PathID'] for bone in body['m_Bones']}
    fallback = transform_name(playable.objects, body['m_Bones'][0]['m_PathID'])
    wanted = {mesh for mesh in spec['renderers'].values() if mesh}
    hers = {}
    for _, tree, name in renderers(model.objects):
        if name in wanted and (name not in hers or len(tree['m_Materials']) > len(hers[name]['m_Materials'])):
            hers[name] = tree
    if set(hers) != wanted:
        raise SystemExit(f'modele de {key} inattendu')

    def descendants(transform):
        found = [transform]
        for child in model.objects[transform].read_typetree()['m_Children']:
            found += descendants(child['m_PathID'])
        return found
    replaced, bones_of, shrink_of = ({}, {}, {})
    for mesh_name, tree in hers.items():
        her_bones = [bone['m_PathID'] for bone in tree['m_Bones']]
        her_names = [transform_name(model.objects, bone) for bone in her_bones]

        def stand_in(index):
            name = her_names[index]
            if name in his:
                return name
            if spec['stand_ins'].get(name) in his:
                return spec['stand_ins'][name]
            if name.startswith('B_f_ring.') and name.replace('ring', 'middle') in his:
                return name.replace('ring', 'middle')
            transform = her_bones[index]
            while transform:
                transform = model.objects[transform].read_typetree()['m_Father']['m_PathID']
                if not transform:
                    break
                parent = transform_name(model.objects, transform)
                if parent in his:
                    return parent
                if spec['stand_ins'].get(parent) in his:
                    return spec['stand_ins'][parent]
            if 'ik' in name.lower():
                return fallback
            raise SystemExit(f'os de {key} sans equivalent : {name}')
        names = [stand_in(i) for i in range(len(her_names))]
        replaced.update({her_names[i]: names[i] for i in range(len(names)) if names[i] != her_names[i]})
        in_head = set()
        for bone, bone_name in zip(her_bones, her_names):
            if bone_name in spec['head_bones']:
                in_head |= set(descendants(bone))
        bones_of[mesh_name] = (names, her_names, [b in in_head for b in her_bones])
    meshes = {}
    for obj in model.objects.values():
        if obj.type.name == 'Mesh':
            tree = obj.read_typetree()
            meshes[tree['m_Name']] = obj.path_id
            if tree['m_Name'] not in bones_of:
                continue
            names, her_names, in_head = bones_of[tree['m_Name']]
            if len(tree['m_BindPose']) != len(her_names):
                raise SystemExit(f'maillage de {key} inattendu')
            poses = [copy.deepcopy(p) for p in tree['m_BindPose']]

            def her_twin(target):
                if target in her_names:
                    return her_names.index(target)
                return next((j for j, n in enumerate(her_names) if spec['stand_ins'].get(n) == target))
            for i, name in enumerate(names):
                if name != her_names[i]:
                    tree['m_BindPose'][i] = copy.deepcopy(poses[her_twin(name)])
            scale = spec.get('head_scale', 1.0)
            if scale != 1.0 and spec['head_bones'][0] in her_names:
                h = numpy.linalg.inv(matrix(poses[her_names.index(spec['head_bones'][0])]))[:3, 3]
                shrink = numpy.eye(4)
                shrink[:3, :3] *= scale
                shrink[:3, 3] = h - scale * h
                for i, flag in enumerate(in_head):
                    if flag:
                        tree['m_BindPose'][i] = pose(matrix(tree['m_BindPose'][i]) @ shrink)
            obj.save_typetree(tree)
        elif obj.type.name == 'AssetBundle':
            tree = obj.read_typetree()
            tree['m_Name'] = tree['m_AssetBundleName'] = spec['model_bundle'][:-len('.bundle')]
            obj.save_typetree(tree)
    link = copy.copy(playable.externals[0])
    link.path = f"archive:/{spec['model_cab']}/{spec['model_cab']}"
    playable.externals.append(link)
    model_file = len(playable.externals)
    root = body['m_RootBone']
    for obj, tree, name in list(renderers(playable.objects)):
        if name not in spec['renderers']:
            continue
        mesh_name = spec['renderers'][name]
        if mesh_name is None:
            tree['m_Enabled'] = 0
            obj.save_typetree(tree)
            continue
        her = hers[mesh_name]
        tree['m_Mesh'] = {'m_FileID': model_file, 'm_PathID': meshes[mesh_name]}
        tree['m_Materials'] = [{'m_FileID': model_file, 'm_PathID': material['m_PathID']} for material in her['m_Materials']]
        tree['m_Bones'] = [{'m_FileID': 0, 'm_PathID': his[bone]} for bone in bones_of[mesh_name][0]]
        tree['m_RootBone'] = dict(root)
        tree['m_BlendShapeWeights'] = list(her['m_BlendShapeWeights'])
        tree['m_AABB'] = copy.deepcopy(her['m_AABB'])
        tree['m_Enabled'] = 1
        obj.save_typetree(tree)
    if spec.get('body_scale', 1.0) != 1.0:
        model_root = next((obj for obj in playable.objects.values() if obj.type.name == 'Transform' and transform_name(playable.objects, obj.path_id) == 'Legacy_Ratchet_00_Playable'))
        tree = model_root.read_typetree()
        tree['m_LocalScale'] = {axis: spec['body_scale'] for axis in 'xyz'}
        model_root.save_typetree(tree)
    for obj in playable.objects.values():
        if obj.type.name == 'AssetBundle':
            tree = obj.read_typetree()
            tree['m_Name'] = tree['m_AssetBundleName'] = spec['bundle'][:-len('.bundle')]
            tree['m_Container'] = [(path.replace('Character_Ratchet_00_Playable.prefab', f'Character_{key}.prefab'), entry) for path, entry in tree['m_Container']]
            obj.save_typetree(tree)
    common = len(bones_of[spec['renderers']['Legacy_Ratchet_00']][0]) - sum((1 for n, h in zip(*bones_of[spec['renderers']['Legacy_Ratchet_00']][:2]) if n != h))
    print(f"{key} : sur le squelette de Ratchet, {common} os en commun, {len(replaced)} rattaches ({', '.join((f'{a}>{b}' for a, b in sorted(replaced.items())))})")
    return [(key, 'assets/aa/Android/' + spec['bundle'], env.file.save(packer='lz4')), (f'{key} (modele)', 'assets/aa/Android/' + spec['model_bundle'], model_env.file.save(packer='lz4'))]

def rivet_bundles():
    return cinematic_hero_bundles('Rivet')

def cinematic_hero_info(key):
    spec = CINEMATIC_HEROES[key]
    own = [{'own': bundle, 'hash': cab[4:], 'internal': bundle[:-len('.bundle')]} for bundle, cab in ((spec['bundle'], spec['cab']), (spec['model_bundle'], spec['model_cab']))]
    families = [{'family': family} for family in playable_ratchet_families() if family != 'skins_character_ratchet_00_playable_assets_all']
    return {'guid': spec['guid'], 'dependencies': own + families}

def rivet_info():
    return cinematic_hero_info('Rivet')

def cdn_skin_bundles():
    files = {}
    if os.path.isdir(COSTUMES):
        for name in os.listdir(COSTUMES):
            match = re.match('(skins_character_[a-z]+_skin\\d+)_assets_all_[0-9a-f]{32}\\.bundle$', name)
            if match:
                files[match.group(1)] = name
    found = []
    for skin in CDN_SKINS:
        name = files.get(f'skins_character_{skin.lower()}')
        if name:
            with open(os.path.join(COSTUMES, name), 'rb') as handle:
                found.append((skin, 'assets/aa/Android/' + name, readable_meshes(relinked(handle.read()))))
    return found

def hero_sources():
    if _hero_sources:
        return _hero_sources[0]
    old_path = os.path.join(xapk, '..', 'v1103', 'split_UnityDataAssetPack.apk')
    index_path = os.path.join(HEROES_RESOURCES, 'heros.json')
    if os.path.exists(old_path):
        pack = zipfile.ZipFile(old_path)
        bundles = hero_model_bundles(pack)
        info = heros_caches.old_hero_info(pack.read('assets/aa/catalog.bin'), [hero for hero, _, _ in bundles])
        os.makedirs(HEROES_RESOURCES, exist_ok=True)
        for _, path, bundle in bundles:
            with open(os.path.join(HEROES_RESOURCES, os.path.basename(path)), 'wb') as handle:
                handle.write(bundle)
        with open(index_path, 'w') as handle:
            json.dump({'info': info, 'bundles': [[hero, path] for hero, path, _ in bundles]}, handle, indent=1)
    else:
        if not os.path.exists(index_path):
            raise SystemExit('Il faut aussi le jeu officiel en version 1.10.3 (fichier .apkm ou .xapk) : il contient les 7 héros jamais sortis.')
        index = json.load(open(index_path))
        info = index['info']
        bundles = [(hero, path, open(os.path.join(HEROES_RESOURCES, os.path.basename(path)), 'rb').read()) for hero, path in index['bundles']]
    costumes = [entry for entry in cdn_skin_bundles() if os.path.exists(old_path) or entry[0] in info]
    if costumes and os.path.exists(old_path):
        info.update(heros_caches.old_hero_info(zipfile.ZipFile(old_path).read('assets/aa/catalog.bin'), [skin for skin, _, _ in costumes]))
        index = json.load(open(index_path))
        index['info'] = info
        with open(index_path, 'w') as handle:
            json.dump(index, handle, indent=1)
    bundles += costumes
    costume = next((entry for entry in costumes if entry[0] == 'Helen_Skin01'), None)
    helen = next((entry for entry in bundles if entry[0] == 'Helen'), None)
    if costume and helen and ('Helen_Skin01' in info):
        bundles.append(('Helen_Skin01 (modele)', 'assets/aa/Android/' + DIMENSIONAL_BUNDLE, dimensional_helen(helen[2], costume[2])))
        dependencies = info['Helen_Skin01']['dependencies']
        if not any((d.get('own') == DIMENSIONAL_BUNDLE for d in dependencies)):
            dependencies.insert(0, {'own': DIMENSIONAL_BUNDLE, 'hash': DIMENSIONAL_CAB[4:], 'internal': DIMENSIONAL_BUNDLE[:-len('.bundle')]})
    if costumes:
        print(f"costumes du CDN : {', '.join((skin for skin, _, _ in costumes))}")
    if os.environ.get('RR_VERSION', '1.10.4') == '1.10.4':
        for key in CINEMATIC_HEROES:
            made = cinematic_hero_bundles(key)
            if made:
                bundles += made
                info[key] = cinematic_hero_info(key)
    if not heavy_tools():
        needing = {record[0] for record in NEW_SKIN_RECORDS}
        bundles = [entry for entry in bundles if entry[0] not in needing]
        for name in needing:
            info.pop(name, None)
    _hero_sources.append((info, bundles))
    return (info, bundles)

def patch_catalog(data):
    info, bundles = hero_sources()
    sizes = {hero: len(bundle) for hero, _, bundle in bundles if hero in info}
    data[:] = heros_caches.add_heroes_from_info(data, info, sizes)

def patch_init_scene(data):
    patch_bundle(data, [(BUILD['init_host'], OLD_HOST, NEW_HOST)])
PHOTON_SETTINGS = 'assets/bin/Data/3df92cddd091603488eec50366992dc0'
PHOTON_APP_ID = b'060ff4b3-f6dd-4228-86f0-7935da3bd27e'

def patch_photon_settings(data):
    host = os.environ['RR_PHOTON'].encode()
    if bytes(data[264:300]) != PHOTON_APP_ID or len(data) != 372:
        raise SystemExit('PhotonServerSettings inattendu')
    if struct.unpack_from('>Q', data, 24)[0] != 372 or struct.unpack_from('<I', data, 128)[0] != 164:
        raise SystemExit('PhotonServerSettings : en-tete inattendu')
    server = 332
    if struct.unpack_from('<I', data, server)[0] != 0:
        raise SystemExit('PhotonServerSettings : champ Server deja rempli')
    text = struct.pack('<I', len(host)) + host
    text += bytes(-len(text) % 4)
    grown = len(text) - 4
    data[server:server + 4] = text
    struct.pack_into('<I', data, 344 + grown, 1)
    struct.pack_into('<I', data, 128, 164 + grown)
    struct.pack_into('>Q', data, 24, 372 + grown)
PATCHES = {'com.playstation.rattlesnake.apk': {'assets/bin/Data/Managed/Metadata/global-metadata.dat': patch_metadata, 'assets/bin/Data/globalgamemanagers': patch_player_settings}, 'UnityDataAssetPack.apk': {'assets/bin/Data/1bf6573aa4de63f4ab5f6bce63d9c51e': patch_host, **({PHOTON_SETTINGS: patch_photon_settings} if os.environ.get('RR_PHOTON') else {}), BUILD['menu_bundle']: patch_main_menu, **({BUILD['init_bundle']: patch_init_scene} if 'init_bundle' in BUILD else {}), **({BUILD['heroes_bundle']: patch_local_data} if 'heroes_bundle' in BUILD else {}), **({BUILD['flail_spec'][0]: patch_flail_spec} if 'flail_spec' in BUILD else {}), **({'assets/aa/catalog.bin': patch_catalog} if 'hero_models' in BUILD else {}), **({BUILD['hero_specs_bundle']: patch_hero_specs_bundle} if 'hero_specs_bundle' in BUILD else {}), **({GADGET_DB_BUNDLE: patch_gadget_db} if weapon_slots_build() else {}), **({MONOSCRIPTS_BUNDLE: patch_monoscripts} if collect_screen_build() else {}), **({PORTRAITS_BUNDLE: patch_rivet_portrait} if 'hero_models' in BUILD and os.environ.get('RR_VERSION', '1.10.4') == '1.10.4' else {}), **({path: bolt_rush_data(path) for path in BOLT_RUSH_EDITS} if BOLT_RUSH else {}), **({path: rush_map(path) for path in RUSH_MAP_POINTS} if BOLT_RUSH else {}), **({GAME_MODES_BUNDLE: patch_game_modes} if BOLT_RUSH else {}), **({LEVEL_DESIGN_BUNDLE: patch_level_design} if BOLT_RUSH else {}), **({LOCALIZATION_FILE.format(lang): patch_localization(lang) for lang in LANGUAGES} if BOLT_RUSH or 'difficulty_row' in BUILD or 'hero_models' in BUILD else {})}, 'config.arm64_v8a.apk': {'lib/arm64-v8a/libil2cpp.so': patch_library}}

def patch_copy_library(data):
    at(data, BUILD['play_available'], bytes.fromhex('fe0f1ef8f44f01a9'), RETURN_FALSE)
    at(data, BUILD['play_autologin'], bytes.fromhex('fe57bea9f44f01a9'), RETURN_FALSE)
if COPIE:
    PATCHES = {'com.playstation.rattlesnake.apk': {'assets/bin/Data/Managed/Metadata/global-metadata.dat': patch_metadata, 'assets/bin/Data/globalgamemanagers': patch_player_settings}, 'UnityDataAssetPack.apk': {'assets/bin/Data/1bf6573aa4de63f4ab5f6bce63d9c51e': patch_host, PHOTON_SETTINGS: patch_photon_settings}, 'config.arm64_v8a.apk': {'lib/arm64-v8a/libil2cpp.so': patch_copy_library}}
for apk, changes in PATCHES.items():
    source = zipfile.ZipFile(os.path.join(xapk, apk))
    target_path = os.path.join(out, apk)
    done = set()
    with zipfile.ZipFile(target_path, 'w', allowZip64=True) as target:
        for info in source.infolist():
            name = info.filename
            if name.startswith('META-INF/') or name == 'stamp-cert-sha256':
                continue
            entry = zipfile.ZipInfo(name, date_time=(1981, 1, 1, 1, 1, 0))
            entry.compress_type = info.compress_type
            entry.external_attr = info.external_attr
            data = source.read(name)
            if name in changes:
                data = bytearray(data)
                changes[name](data)
                data = bytes(data)
                done.add(name)
            target.writestr(entry, data)
        if apk == 'UnityDataAssetPack.apk' and 'hero_models' in BUILD and (not COPIE):
            for _, path, bundle in hero_sources()[1]:
                entry = zipfile.ZipInfo(path, date_time=(1981, 1, 1, 1, 1, 0))
                target.writestr(entry, bundle)
    missing = set(changes) - done
    if missing:
        raise SystemExit(f'fichiers non trouves : {missing}')
    print(f'{apk} : {len(done)} fichier(s) modifie(s)')
