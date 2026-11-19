import copy
import json
import os
import re
import struct
import langues
from langues import tr
HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = json.load(open(os.path.join(HERE, 'ressources', 'schema.json'), encoding='utf-8'))
NAMES = json.load(open(os.path.join(HERE, 'ressources', 'noms.json'), encoding='utf-8'))

class F32(float):
    pass

class Ext:

    def __init__(self, code, data):
        self.code, self.data = (code, data)

    def __eq__(self, other):
        return isinstance(other, Ext) and (self.code, self.data) == (other.code, other.data)

class Reader:

    def __init__(self, data):
        self.data, self.at = (data, 0)

    def take(self, n):
        if self.at + n > len(self.data):
            raise ValueError(tr('sauvegarde tronquée'))
        chunk = self.data[self.at:self.at + n]
        self.at += n
        return chunk

    def unpack(self, fmt):
        return struct.unpack('>' + fmt, self.take(struct.calcsize(fmt)))[0]

    def value(self):
        b = self.take(1)[0]
        if b <= 127:
            return b
        if b >= 224:
            return b - 256
        if 128 <= b <= 143:
            return self.map(b & 15)
        if 144 <= b <= 159:
            return [self.value() for _ in range(b & 15)]
        if 160 <= b <= 191:
            return self.take(b & 31).decode('utf-8')
        simple = {192: None, 194: False, 195: True}
        if b in simple:
            return simple[b]
        if b in (196, 197, 198):
            return bytes(self.take(self.unpack('BHI'[b - 196])))
        if b in (199, 200, 201):
            size = self.unpack('BHI'[b - 199])
            return Ext(self.unpack('b'), bytes(self.take(size)))
        if b == 202:
            return F32(self.unpack('f'))
        if b == 203:
            return self.unpack('d')
        if 204 <= b <= 207:
            return self.unpack('BHIQ'[b - 204])
        if 208 <= b <= 211:
            return self.unpack('bhiq'[b - 208])
        if 212 <= b <= 216:
            code = self.unpack('b')
            return Ext(code, bytes(self.take(1 << b - 212)))
        if b in (217, 218, 219):
            return self.take(self.unpack('BHI'[b - 217])).decode('utf-8')
        if b in (220, 221):
            return [self.value() for _ in range(self.unpack('HI'[b - 220]))]
        if b in (222, 223):
            return self.map(self.unpack('HI'[b - 222]))
        raise ValueError(tr('octet msgpack inconnu {b:#x}', b=b))

    def map(self, n):
        out = {}
        for _ in range(n):
            key = self.value()
            out[key] = self.value()
        return out

def loads(data):
    reader = Reader(bytes(data))
    value = reader.value()
    if reader.at != len(reader.data):
        raise ValueError(tr('données en trop après la sauvegarde'))
    return value

def dumps(value):
    out = bytearray()
    write(value, out)
    return bytes(out)

def write(value, out):
    if value is None:
        out.append(192)
    elif value is True:
        out.append(195)
    elif value is False:
        out.append(194)
    elif isinstance(value, int):
        write_int(value, out)
    elif isinstance(value, F32):
        out += b'\xca' + struct.pack('>f', value)
    elif isinstance(value, float):
        out += b'\xcb' + struct.pack('>d', value)
    elif isinstance(value, str):
        raw = value.encode('utf-8')
        n = len(raw)
        if n < 32:
            out.append(160 | n)
        elif n < 256:
            out += bytes((217, n))
        elif n < 65536:
            out += b'\xda' + struct.pack('>H', n)
        else:
            out += b'\xdb' + struct.pack('>I', n)
        out += raw
    elif isinstance(value, (bytes, bytearray)):
        n = len(value)
        if n < 256:
            out += bytes((196, n))
        elif n < 65536:
            out += b'\xc5' + struct.pack('>H', n)
        else:
            out += b'\xc6' + struct.pack('>I', n)
        out += value
    elif isinstance(value, (list, tuple)):
        header(len(value), 144, 220, out)
        for item in value:
            write(item, out)
    elif isinstance(value, dict):
        header(len(value), 128, 222, out)
        for key, item in value.items():
            write(key, out)
            write(item, out)
    elif isinstance(value, Ext):
        n = len(value.data)
        fixed = {1: 212, 2: 213, 4: 214, 8: 215, 16: 216}
        if n in fixed:
            out.append(fixed[n])
        elif n < 256:
            out += bytes((199, n))
        elif n < 65536:
            out += b'\xc8' + struct.pack('>H', n)
        else:
            out += b'\xc9' + struct.pack('>I', n)
        out += struct.pack('>b', value.code) + value.data
    else:
        raise TypeError(tr('valeur impossible à écrire : {value!r}', value=value))

def header(n, fix, wide, out):
    if n < 16:
        out.append(fix | n)
    elif n < 65536:
        out += bytes((wide,)) + struct.pack('>H', n)
    else:
        out += bytes((wide + 1,)) + struct.pack('>I', n)

def write_int(n, out):
    if 0 <= n < 128:
        out.append(n)
    elif -32 <= n < 0:
        out.append(n & 255)
    elif 0 <= n < 256:
        out += bytes((204, n))
    elif 0 <= n < 65536:
        out += b'\xcd' + struct.pack('>H', n)
    elif 0 <= n < 4294967296:
        out += b'\xce' + struct.pack('>I', n)
    elif n >= 0:
        out += b'\xcf' + struct.pack('>Q', n)
    elif n >= -128:
        out += b'\xd0' + struct.pack('>b', n)
    elif n >= -32768:
        out += b'\xd1' + struct.pack('>h', n)
    elif n >= -2147483648:
        out += b'\xd2' + struct.pack('>i', n)
    else:
        out += b'\xd3' + struct.pack('>q', n)
INTS = {'int': (-2 ** 31, 2 ** 31 - 1), 'Int32': (-2 ** 31, 2 ** 31 - 1), 'uint': (0, 2 ** 32 - 1), 'UInt32': (0, 2 ** 32 - 1), 'long': (-2 ** 63, 2 ** 63 - 1), 'Int64': (-2 ** 63, 2 ** 63 - 1), 'ulong': (0, 2 ** 64 - 1), 'UInt64': (0, 2 ** 64 - 1), 'short': (-2 ** 15, 2 ** 15 - 1), 'Int16': (-2 ** 15, 2 ** 15 - 1), 'ushort': (0, 2 ** 16 - 1), 'UInt16': (0, 2 ** 16 - 1), 'byte': (0, 255), 'Byte': (0, 255), 'sbyte': (-128, 127), 'SByte': (-128, 127)}
FLOATS = {'float', 'Single', 'double', 'Double'}
BOOLS = {'bool', 'Boolean'}
STRINGS = {'string', 'String'}
LISTS = ('List', 'HashSet', 'Queue', 'IList', 'ICollection', 'IEnumerable')
MAPS = ('Dictionary', 'SortedDictionary', 'IDictionary', 'IReadOnlyDictionary')

def split_generic(kind):
    if '<' not in kind:
        return (kind, [])
    name, inner = kind.split('<', 1)
    inner = inner[:inner.rindex('>')]
    args, depth, start = ([], 0, 0)
    for i, char in enumerate(inner):
        if char == '<':
            depth += 1
        elif char == '>':
            depth -= 1
        elif char == ',' and depth == 0:
            args.append(inner[start:i].strip())
            start = i + 1
    args.append(inner[start:].strip())
    return (name.strip(), args)

def describe(kind):
    kind = kind.strip()
    if kind.endswith('?'):
        return describe(kind[:-1])
    if kind.endswith('[]'):
        inner = kind[:-2]
        return ('bytes', None) if inner in ('Byte', 'byte') else ('list', inner)
    name, args = split_generic(kind)
    if name == 'Nullable' and args:
        return describe(args[0])
    if name in LISTS and args:
        return ('list', args[0])
    if name in MAPS and len(args) == 2:
        return ('map', (args[0], args[1]))
    if kind in INTS:
        return ('int', INTS[kind])
    if kind in FLOATS:
        return ('float', kind)
    if kind in BOOLS:
        return ('bool', None)
    if kind in STRINGS:
        return ('string', None)
    if kind in SCHEMA['enums']:
        return ('enum', kind)
    if kind in SCHEMA['types']:
        return ('object', kind)
    return ('unknown', kind)

def fields(type_name):
    return sorted(SCHEMA['types'][type_name]['fields'], key=lambda f: (isinstance(f[0], str), f[0]))

def default(kind):
    what, detail = describe(kind)
    if what == 'int' or what == 'enum':
        return 0
    if what == 'float':
        return F32(0.0) if detail in ('float', 'Single') else 0.0
    if what == 'bool':
        return False
    if what == 'string':
        return ''
    if what == 'bytes':
        return b''
    if what == 'list':
        return []
    if what == 'map':
        return {}
    if what == 'object':
        keys = fields(detail)
        if keys and all((isinstance(k, int) for k, _, _ in keys)):
            out = [None] * (max((k for k, _, _ in keys)) + 1)
            for key, _, field_kind in keys:
                out[key] = default(field_kind)
            return out
        return {k: default(t) for k, _, t in keys}
    return None

def enum_label(enum, value):
    return SCHEMA['enums'].get(enum, {}).get(str(value))

def enum_values(enum):
    return [(int(v), label) for v, label in SCHEMA['enums'].get(enum, {}).items()]

def name_of(enum, value, lang=None):
    table = NAMES.get(enum, {})
    entry = table.get(str(value))
    if entry:
        lang = lang or langues.names_language()
        return entry.get(lang) or entry.get('en') or next(iter(entry.values()))
    label = enum_label(enum, value)
    return label if label is not None else str(value)

class Save:

    def __init__(self, raw):
        self.root = loads(raw)
        if not isinstance(self.root, dict) or not isinstance(self.root.get('save'), dict):
            raise ValueError(tr("ce fichier n'est pas une sauvegarde de Ranger Rumble"))
        self.values = {}
        for name, part in self.root['save'].items():
            if isinstance(part, dict) and isinstance(part.get('bytes'), (bytes, bytearray)):
                self.values[name] = loads(part['bytes'])
        self.original = {name: dumps(value) for name, value in self.values.items()}

    def part_type(self, name):
        versions = SCHEMA['parts'].get(name, {})
        version = str(self.root['save'][name].get('version', 0))
        return versions.get(version) or (versions[max(versions)] if versions else None)

    def changed(self):
        return [name for name, value in self.values.items() if dumps(value) != self.original[name]]

    def to_bytes(self):
        root = copy.copy(self.root)
        root['save'] = dict(self.root['save'])
        for name in self.changed():
            part = dict(root['save'][name])
            part['bytes'] = dumps(self.values[name])
            root['save'][name] = part
        return dumps(root)

    def write(self, path):
        data = self.to_bytes()
        Save(data)
        temporary = path + '.tmp'
        with open(temporary, 'wb') as handle:
            handle.write(data)
        os.replace(temporary, path)

    def part(self, name, create=True):
        if name not in self.values:
            if not create:
                return None
            versions = SCHEMA['parts'][name]
            version = max(versions, key=int)
            self.values[name] = default(versions[version])
            self.root['save'][name] = {'className': '', 'version': int(version), 'bytes': b'', 'jsonDump': '', 'overlayClassName': '', 'overlayVersion': 0, 'bytesOverlay': None, 'overlayJsonDump': '', 'isPublic': False}
            self.original[name] = b''
        return self.values[name]

    def collection(self, name):
        value = self.part(name)
        if self.root['save'][name].get('version', 0) >= 1:
            if value[0] is None:
                value[0] = [[]]
            if value[0][0] is None:
                value[0][0] = []
            return value[0][0]
        if value[0] is None:
            value[0] = []
        return value[0]
CHARACTERS = {int(v): k for v, k in SCHEMA['enums']['CHARACTER_ID'].items() if k not in ('NONE',)}

def hero_unlockable(character):
    label = SCHEMA['enums']['CHARACTER_ID'].get(str(character))
    if label is None:
        return NAMES.get('heros_extra', {}).get(str(character), {}).get('unlockable')
    wanted = f'SKIN_{label}_SKIN00'
    for value, name in SCHEMA['enums']['UNLOCKABLE_ID'].items():
        if name == wanted:
            return int(value)
    return None

def weapons():
    return [(int(v), n) for v, n in SCHEMA['enums']['UNLOCKABLE_ID'].items() if n.startswith('WP_') and (not n.endswith('_DEPRECATED'))]

def skins_of(character):
    label = SCHEMA['enums']['CHARACTER_ID'].get(str(character))
    if label is None:
        return []
    pattern = re.compile(f'^SKIN_{label}_SKIN\\d\\d$')
    return [(int(v), n) for v, n in SCHEMA['enums']['UNLOCKABLE_ID'].items() if pattern.match(n)]
