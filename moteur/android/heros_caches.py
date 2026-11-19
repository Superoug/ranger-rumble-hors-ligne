import re
import struct
NONE = 4294967295
OFFSET_MASK = 1073741823
DYNAMIC_STRING = 1073741824
UTF16_STRING = 2147483648
KEYS_OFFSET_POSITION = 8
PREFAB = 'Character_{}.prefab|Characters|Assets/Prefabs'
TEMPLATE_HERO = 'Celeste'

def bundle_family(name):
    return re.sub('_[0-9a-f]{32}\\.bundle$', '', name)

class Catalog:

    def __init__(self, data):
        self.data = data
        self.keys_offset = self.u32(KEYS_OFFSET_POSITION)

    def u32(self, offset):
        return struct.unpack_from('<I', self.data, offset)[0]

    def string(self, offset):
        if offset == NONE:
            return None
        position = offset & OFFSET_MASK
        if offset & DYNAMIC_STRING:
            parts = []
            while position != NONE:
                parts.append(str(self.string(self.u32(position))))
                position = self.u32(position + 4)
            return '|'.join(parts)
        raw = self.data[position:position + self.u32(position - 4)]
        return raw.decode('utf-16-le' if offset & UTF16_STRING else 'latin1')

    def array(self, offset):
        if offset == NONE:
            return []
        return [self.u32(offset + i * 4) for i in range(self.u32(offset - 4) // 4)]

    def location(self, offset):
        return struct.unpack_from('<7I', self.data, offset)

    def entries(self):
        for i in range(self.u32(self.keys_offset - 4) // 8):
            key = self.u32(self.keys_offset + i * 8)
            locations = self.u32(self.keys_offset + i * 8 + 4)
            yield (key, self.string(self.u32(self.u32(key + 4))), self.array(locations))

    def bundles(self):
        found = {}
        for _, _, locations in self.entries():
            for offset in locations:
                name = self.string(self.location(offset)[0])
                if name and name.endswith('.bundle'):
                    found[bundle_family(name)] = offset
        return found

def old_hero_info(old_data, heroes):
    old = Catalog(bytes(old_data))
    old_entries = {}
    old_prefabs = {}
    for _, name, locations in old.entries():
        old_entries.setdefault(locations[0] if locations else None, []).append(name)
        old_prefabs[name] = locations
    info = {}
    for hero in heroes:
        old_location = old_prefabs[PREFAB.format(hero)][0]
        family = f'skins_character_{hero.lower()}_assets_all'
        dependencies = []
        for offset in old.array(old.location(old_location)[3]):
            fields = old.location(offset)
            name = old.string(fields[0])
            if bundle_family(name) == family:
                options = old.u32(fields[5] + 4)
                dependencies.append({'own': name, 'hash': old.data[old.u32(options):old.u32(options) + 16].hex(), 'internal': old.string(old.u32(options + 4))})
            else:
                dependencies.append({'family': bundle_family(name)})
        guid = next((name for name in old_entries[old_location] if re.fullmatch('[0-9a-f]{32}', str(name))))
        info[hero] = {'guid': guid, 'dependencies': dependencies}
    return info

def add_heroes_from_info(new_data, info, heroes):
    new = Catalog(bytes(new_data))
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
    entries = {name: (key, locations) for key, name, locations in new.entries()}
    template_key, template_locations = entries[PREFAB.format(TEMPLATE_HERO)]
    prefab_template = new.location(template_locations[0])
    prefab_folder = new.u32((prefab_template[1] & OFFSET_MASK) + 4)
    key_type = new.u32(template_key)
    key_separator = new.u32(new.u32(template_key + 4) + 4)
    bundles = new.bundles()
    bundle_template = new.location(bundles['skins_character_celeste_assets_all'])
    bundle_folder = new.u32((bundle_template[1] & OFFSET_MASK) + 4)
    options_type = new.u32(bundle_template[5])
    common_options = new.u32(new.u32(bundle_template[5] + 4) + 16)
    new_keys = []

    def add_key(string_offset, location):
        record = append(struct.pack('<II', string_offset, key_separator))
        key = append(struct.pack('<II', key_type, record))
        new_keys.append((key, append_array([location])))
    for hero, size in heroes.items():
        dependencies = []
        for dependency in info[hero]['dependencies']:
            if 'own' in dependency:
                file_name = append_string(dependency['own'])
                folder = append(struct.pack('<II', file_name, bundle_folder))
                hash_offset = append(bytes.fromhex(dependency['hash']))
                name_offset = append_string(dependency['internal'])
                record = append(struct.pack('<5I', hash_offset, name_offset, 0, size, common_options))
                extra = append(struct.pack('<II', options_type, record))
                own = append(struct.pack('<7I', file_name, folder | DYNAMIC_STRING, bundle_template[2], NONE, 0, extra, bundle_template[6]))
                dependencies.append(own)
                bundles[bundle_family(dependency['own'])] = own
            elif dependency['family'] in bundles:
                dependencies.append(bundles[dependency['family']])
        prefab_name = append_string(f'Character_{hero}.prefab')
        prefab_path = append(struct.pack('<II', prefab_name, prefab_folder)) | DYNAMIC_STRING
        location = append(struct.pack('<7I', prefab_path, prefab_path, prefab_template[2], append_array(dependencies), 0, NONE, prefab_template[6]))
        add_key(prefab_path, location)
        add_key(append_string(info[hero]['guid']), location)
    old_table = bytes(out[new.keys_offset:new.keys_offset + new.u32(new.keys_offset - 4)])
    extra_table = b''.join((struct.pack('<II', *pair) for pair in new_keys))
    append(struct.pack('<I', len(old_table) + len(extra_table)))
    struct.pack_into('<I', out, KEYS_OFFSET_POSITION, append(old_table + extra_table))
    return bytes(out)
