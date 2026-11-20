import re
import struct
NONE = 4294967295
OFFSET_MASK = 1073741823
DYNAMIC_STRING = 1073741824
UTF16_STRING = 2147483648
KEYS_OFFSET_POSITION = 8
PREFAB = 'Character_{}.prefab|Characters|Assets/Prefabs'
TEMPLATE_HERO = 'Celeste'
TEMPLATE_BUNDLE = 'skins_character_celeste_assets_all'
PRIMARY_KEY, INTERNAL_ID, PROVIDER, DEPENDENCIES, EXTRA_DATA, RESOURCE_TYPE = (0, 1, 2, 3, 5, 6)
HASH_SIZE = 16
BUNDLE_HASH_SUFFIX = re.compile('_[0-9a-f]{32}\\.bundle$')
GUID = re.compile('[0-9a-f]{32}')

def bundle_family(name):
    return BUNDLE_HASH_SUFFIX.sub('', name)

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

    def tail(self, dynamic_string):
        return self.u32((dynamic_string & OFFSET_MASK) + 4)

    def key_separator(self, key):
        return self.u32(self.u32(key + 4) + 4)

    def bundle_options(self, location):
        return self.u32(location[EXTRA_DATA] + 4)

    def entries(self):
        for i in range(self.u32(self.keys_offset - 4) // 8):
            key = self.u32(self.keys_offset + i * 8)
            locations = self.u32(self.keys_offset + i * 8 + 4)
            yield (key, self.string(self.u32(self.u32(key + 4))), self.array(locations))

    def bundles(self):
        found = {}
        for _, _, locations in self.entries():
            for offset in locations:
                name = self.string(self.location(offset)[PRIMARY_KEY])
                if name and name.endswith('.bundle'):
                    found[bundle_family(name)] = offset
        return found

class CatalogWriter:

    def __init__(self, catalog):
        self.catalog = catalog
        self.out = bytearray(catalog.data)
        self.keys = []
        self.bundles = catalog.bundles()
        self.bundle_template = catalog.location(self.bundles[TEMPLATE_BUNDLE])
        self.bundle_folder = catalog.tail(self.bundle_template[INTERNAL_ID])
        self.options_type = catalog.u32(self.bundle_template[EXTRA_DATA])
        self.common_options = catalog.u32(catalog.bundle_options(self.bundle_template) + 16)

    def append(self, raw):
        offset = len(self.out)
        self.out.extend(raw)
        return offset

    def append_string(self, text):
        self.append(struct.pack('<I', len(text)))
        return self.append(text.encode('ascii'))

    def append_array(self, values):
        self.append(struct.pack('<I', len(values) * 4))
        return self.append(struct.pack(f'<{len(values)}I', *values))

    def append_dynamic(self, first, tail):
        return self.append(struct.pack('<II', first, tail)) | DYNAMIC_STRING

    def add_bundle(self, file_name, hash_hex, internal, size):
        name = self.append_string(file_name)
        path = self.append_dynamic(name, self.bundle_folder)
        hash_offset = self.append(bytes.fromhex(hash_hex))
        internal_offset = self.append_string(internal)
        options = self.append(struct.pack('<5I', hash_offset, internal_offset, 0, size, self.common_options))
        extra = self.append(struct.pack('<II', self.options_type, options))
        template = self.bundle_template
        return self.append(struct.pack('<7I', name, path, template[PROVIDER], NONE, 0, extra, template[RESOURCE_TYPE]))

    def add_location(self, primary, internal, template, dependencies):
        return self.append(struct.pack('<7I', primary, internal, template[PROVIDER], self.append_array(dependencies), 0, NONE, template[RESOURCE_TYPE]))

    def add_key(self, key_type, string, separator, location):
        record = self.append(struct.pack('<II', string, separator))
        key = self.append(struct.pack('<II', key_type, record))
        self.keys.append((key, self.append_array([location])))

    def finish(self):
        start = self.catalog.keys_offset
        old_table = bytes(self.out[start:start + self.catalog.u32(start - 4)])
        extra_table = b''.join((struct.pack('<II', *pair) for pair in self.keys))
        self.append(struct.pack('<I', len(old_table) + len(extra_table)))
        struct.pack_into('<I', self.out, KEYS_OFFSET_POSITION, self.append(old_table + extra_table))
        return bytes(self.out)

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
        for offset in old.array(old.location(old_location)[DEPENDENCIES]):
            fields = old.location(offset)
            name = old.string(fields[PRIMARY_KEY])
            if bundle_family(name) == family:
                options = old.bundle_options(fields)
                hash_offset = old.u32(options)
                dependencies.append({'own': name, 'hash': old.data[hash_offset:hash_offset + HASH_SIZE].hex(), 'internal': old.string(old.u32(options + 4))})
            else:
                dependencies.append({'family': bundle_family(name)})
        guid = next((name for name in old_entries[old_location] if GUID.fullmatch(str(name))))
        info[hero] = {'guid': guid, 'dependencies': dependencies}
    return info

def add_heroes_from_info(new_data, info, heroes):
    new = Catalog(bytes(new_data))
    writer = CatalogWriter(new)
    entries = {name: (key, locations) for key, name, locations in new.entries()}
    template_key, template_locations = entries[PREFAB.format(TEMPLATE_HERO)]
    prefab_template = new.location(template_locations[0])
    prefab_folder = new.tail(prefab_template[INTERNAL_ID])
    key_type = new.u32(template_key)
    separator = new.key_separator(template_key)
    for hero, size in heroes.items():
        dependencies = []
        for dependency in info[hero]['dependencies']:
            if 'own' in dependency:
                own = writer.add_bundle(dependency['own'], dependency['hash'], dependency['internal'], size)
                dependencies.append(own)
                writer.bundles[bundle_family(dependency['own'])] = own
            elif dependency['family'] in writer.bundles:
                dependencies.append(writer.bundles[dependency['family']])
        prefab_path = writer.append_dynamic(writer.append_string(f'Character_{hero}.prefab'), prefab_folder)
        location = writer.add_location(prefab_path, prefab_path, prefab_template, dependencies)
        writer.add_key(key_type, prefab_path, separator, location)
        writer.add_key(key_type, writer.append_string(info[hero]['guid']), separator, location)
    return writer.finish()
