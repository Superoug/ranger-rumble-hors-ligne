import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import heros_caches as hc
TEMPLATES = {'scene': 'q_FFA_Ardolis_01', 'asset': 'q_FFA_Ardolis_01.asset|Resources/DB/Maps|Assets', 'minimap': 'q_FFA_Ardolis_01_minimap.png|UI/Minimap|Textures|Assets'}

def file_name(internal):
    return internal.split('|')[0]

def add_maps(new_data, info, sizes):
    new = hc.Catalog(bytes(new_data))
    writer = hc.CatalogWriter(new)
    entries = {}
    for key, name, locations in new.entries():
        entries.setdefault(name, (key, locations))
    template_key, _ = entries[TEMPLATES['scene']]
    key_type = new.u32(template_key)
    plain_separator = new.key_separator(template_key)
    path_key, _ = entries[TEMPLATES['asset']]
    path_separator = new.key_separator(path_key)
    if new.u32(path_key) != key_type:
        raise SystemExit('catalogue : types de cles inattendus')
    templates = {kind: new.location(entries[name][1][0]) for kind, name in TEMPLATES.items()}

    def add_key(string, location):
        separator = path_separator if string & hc.DYNAMIC_STRING else plain_separator
        writer.add_key(key_type, string, separator, location)
    own = {}
    for bundle in info['bundles']:
        own[bundle['file']] = writer.add_bundle(bundle['file'], bundle['hash'], bundle['internal'], sizes[bundle['file']])
    added = 0
    for data in info['maps'].values():
        for entry in data['locations']:
            template = templates[entry['kind']]
            dependencies = [own[f] for f in entry['own'] if f in own]
            dependencies += [writer.bundles[f] for f in entry['families'] if f in writer.bundles]

            def chained(name, field):
                return writer.append_dynamic(writer.append_string(name), new.tail(template[field]))
            name = file_name(entry['internal'])
            if entry['kind'] == 'scene':
                primary = writer.append_string(name)
                internal = chained(name + '.unity', hc.INTERNAL_ID)
            else:
                primary = chained(name, hc.PRIMARY_KEY)
                internal = chained(name, hc.INTERNAL_ID)
            location = writer.add_location(primary, internal, template, dependencies)
            for key in entry['keys']:
                if '|' in key:
                    add_key(primary, location)
                else:
                    add_key(writer.append_string(key), location)
            added += 1
    return (writer.finish(), added)
