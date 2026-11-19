import os
import struct
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import heros_caches as hc
TEMPLATES = {'scene': 'q_FFA_Ardolis_01', 'asset': 'q_FFA_Ardolis_01.asset|Resources/DB/Maps|Assets', 'minimap': 'q_FFA_Ardolis_01_minimap.png|UI/Minimap|Textures|Assets'}
TEMPLATE_BUNDLE = 'skins_character_celeste_assets_all'

def file_name(internal):
    return internal.split('|')[0]

def add_maps(new_data, info, sizes):
    new = hc.Catalog(bytes(new_data))
    out = bytearray(new_data)

    def append(raw):
        offset = len(out)
        out.extend(raw)
        return offset

    def append_string(text):
        append(struct.pack('<I', len(text)))
        return append(text.encode('ascii'))

    def append_array(values):
        append(struct.pack('<I', len(values) * 4))
        return append(struct.pack(f'<{len(values)}I', *values))
    entries = {}
    for key, name, locations in new.entries():
        entries.setdefault(name, (key, locations))
    template_key, _ = entries[TEMPLATES['scene']]
    key_type = new.u32(template_key)
    plain_separator = new.u32(new.u32(template_key + 4) + 4)
    path_key, _ = entries[TEMPLATES['asset']]
    path_separator = new.u32(new.u32(path_key + 4) + 4)
    if new.u32(path_key) != key_type:
        raise SystemExit('catalogue : types de cles inattendus')
    templates = {kind: new.location(entries[name][1][0]) for kind, name in TEMPLATES.items()}
    bundles = new.bundles()
    bundle_template = new.location(bundles[TEMPLATE_BUNDLE])
    bundle_folder = new.u32((bundle_template[1] & hc.OFFSET_MASK) + 4)
    options_type = new.u32(bundle_template[5])
    common_options = new.u32(new.u32(bundle_template[5] + 4) + 16)
    new_keys = []

    def add_key(string_offset, location):
        separator = path_separator if string_offset & hc.DYNAMIC_STRING else plain_separator
        record = append(struct.pack('<II', string_offset, separator))
        key = append(struct.pack('<II', key_type, record))
        new_keys.append((key, append_array([location])))
    own = {}
    for bundle in info['bundles']:
        name = append_string(bundle['file'])
        folder = append(struct.pack('<II', name, bundle_folder))
        hash_offset = append(bytes.fromhex(bundle['hash']))
        internal = append_string(bundle['internal'])
        record = append(struct.pack('<5I', hash_offset, internal, 0, sizes[bundle['file']], common_options))
        extra = append(struct.pack('<II', options_type, record))
        own[bundle['file']] = append(struct.pack('<7I', name, folder | hc.DYNAMIC_STRING, bundle_template[2], hc.NONE, 0, extra, bundle_template[6]))
    added = 0
    for data in info['maps'].values():
        for entry in data['locations']:
            template = templates[entry['kind']]
            dependencies = [own[f] for f in entry['own'] if f in own]
            dependencies += [bundles[f] for f in entry['families'] if f in bundles]

            def chained(name, field):
                folder = new.u32((template[field] & hc.OFFSET_MASK) + 4)
                return append(struct.pack('<II', append_string(name), folder)) | hc.DYNAMIC_STRING
            name = file_name(entry['internal'])
            if entry['kind'] == 'scene':
                primary = append_string(name)
                internal = chained(name + '.unity', 1)
            else:
                primary = chained(name, 0)
                internal = chained(name, 1)
            location = append(struct.pack('<7I', primary, internal, template[2], append_array(dependencies), 0, hc.NONE, template[6]))
            for key in entry['keys']:
                if '|' in key:
                    add_key(primary, location)
                else:
                    add_key(append_string(key), location)
            added += 1
    old_table = bytes(out[new.keys_offset:new.keys_offset + new.u32(new.keys_offset - 4)])
    extra_table = b''.join((struct.pack('<II', *pair) for pair in new_keys))
    append(struct.pack('<I', len(old_table) + len(extra_table)))
    struct.pack_into('<I', out, hc.KEYS_OFFSET_POSITION, append(old_table + extra_table))
    return (bytes(out), added)
