import struct
RES_XML = 3
STRING_POOL = 1
RESOURCE_MAP = 384
NS_START, NS_END, ELEMENT_START, ELEMENT_END, CDATA = (256, 257, 258, 259, 260)
UTF8 = 256
NO_INDEX = 4294967295
SPECIAL_ATTRIBUTES = ('id', 'class', 'style')
TYPE_REFERENCE, TYPE_STRING, TYPE_INT_DEC, TYPE_INT_BOOLEAN = (1, 3, 16, 18)
ANDROID = 'http://schemas.android.com/apk/res/android'

def _read_utf8(data: bytes, position: int) -> str:
    length = data[position]
    position += 2 if length & 128 else 1
    size = data[position]
    if size & 128:
        size = (size & 127) << 8 | data[position + 1]
        position += 2
    else:
        position += 1
    return data[position:position + size].decode('utf-8')

def _read_utf16(data: bytes, position: int) -> str:
    length, = struct.unpack_from('<H', data, position)
    position += 2
    if length & 32768:
        low, = struct.unpack_from('<H', data, position)
        length = (length & 32767) << 16 | low
        position += 2
    return data[position:position + length * 2].decode('utf-16-le')

def _read_pool(data: bytes, start: int) -> list[str]:
    _, header_size, _, count, _, flags, strings_start, _ = struct.unpack_from('<HHIIIIII', data, start)
    offsets = struct.unpack_from(f'<{count}I', data, start + header_size)
    read = _read_utf8 if flags & UTF8 else _read_utf16
    return [read(data, start + strings_start + offset) for offset in offsets]

class Document:

    def __init__(self, data: bytes):
        if struct.unpack_from('<H', data, 0)[0] != RES_XML:
            raise ValueError('pas un XML binaire Android')
        position = struct.unpack_from('<H', data, 2)[0]
        strings, resource_ids, self.events = ([], [], [])

        def text(index):
            return None if index == NO_INDEX else strings[index]
        while position < len(data):
            kind, header_size, size = struct.unpack_from('<HHI', data, position)
            body = position + header_size
            if kind == STRING_POOL:
                strings = _read_pool(data, position)
            elif kind == RESOURCE_MAP:
                resource_ids = list(struct.unpack_from(f'<{(size - header_size) // 4}I', data, body))
            elif kind in (NS_START, NS_END):
                prefix, uri = struct.unpack_from('<II', data, body)
                self.events.append(('ns_start' if kind == NS_START else 'ns_end', text(prefix), text(uri)))
            elif kind == ELEMENT_START:
                ns, name, attr_start, attr_size, count = struct.unpack_from('<IIHHH', data, body)
                attributes = []
                for i in range(count):
                    a_ns, a_name, raw, _, _, value_type, value = struct.unpack_from('<IIIHBBI', data, body + attr_start + i * attr_size)
                    attributes.append({'ns': text(a_ns), 'name': strings[a_name], 'res': resource_ids[a_name] if a_name < len(resource_ids) else None, 'raw': text(raw), 'type': value_type, 'value': strings[value] if value_type == TYPE_STRING else value})
                self.events.append(('start', text(ns), strings[name], attributes))
            elif kind == ELEMENT_END:
                ns, name = struct.unpack_from('<II', data, body)
                self.events.append(('end', text(ns), strings[name]))
            elif kind == CDATA:
                value, _, _, value_type, typed = struct.unpack_from('<IHBBI', data, body)
                self.events.append(('cdata', strings[value], value_type, typed))
            else:
                raise ValueError(f'morceau XML inconnu {kind:#x}')
            position += size

    def _elements(self):
        stack = []
        for index, event in enumerate(self.events):
            if event[0] == 'start':
                stack.append(index)
            elif event[0] == 'end':
                begin = stack.pop()
                yield (begin, index, len(stack), event[2])

    def element_ranges(self, name: str, depth: int | None=None) -> list[tuple[int, int]]:
        return [(begin, end) for begin, end, level, found in self._elements() if found == name and (depth is None or level == depth)]

    def element_ranges_all(self) -> list[tuple[int, int]]:
        return sorted(((begin, end) for begin, end, _, _ in self._elements()))

    def first(self, name: str):
        for event in self.events:
            if event[0] == 'start' and event[2] == name:
                return event
        raise KeyError(name)

    def remove_element(self, predicate) -> int:
        removed = 0
        while True:
            match = next(((begin, end) for begin, end in self.element_ranges_all() if predicate(self.events[begin])), None)
            if match is None:
                return removed
            del self.events[match[0]:match[1] + 1]
            removed += 1

    def insert_before_end(self, name: str, events: list) -> None:
        ranges = self.element_ranges(name)
        if not ranges:
            raise KeyError(name)
        end = ranges[0][1]
        self.events[end:end] = events

    def _strings(self) -> tuple[list[str], list[int]]:
        resource_names, others = ({}, [])

        def note(string):
            if string is not None and string not in others:
                others.append(string)
        for event in self.events:
            if event[0] in ('ns_start', 'ns_end', 'end'):
                note(event[1])
                note(event[2])
            elif event[0] == 'start':
                note(event[1])
                note(event[2])
                for attribute in event[3]:
                    note(attribute['ns'])
                    if attribute['res'] is not None:
                        resource_names.setdefault(attribute['name'], attribute['res'])
                    else:
                        note(attribute['name'])
                    note(attribute['raw'])
                    if attribute['type'] == TYPE_STRING:
                        note(attribute['value'])
            elif event[0] == 'cdata':
                note(event[1])
        mapped = sorted(resource_names.items(), key=lambda item: item[1])
        strings = [name for name, _ in mapped] + [s for s in others if s not in resource_names]
        return (strings, [res for _, res in mapped])

    def to_bytes(self) -> bytes:
        strings, ids = self._strings()
        index = {s: i for i, s in enumerate(strings)}

        def ref(string):
            return NO_INDEX if string is None else index[string]
        chunks = [self._pool(strings), struct.pack('<HHI', RESOURCE_MAP, 8, 8 + 4 * len(ids)) + struct.pack(f'<{len(ids)}I', *ids)]
        line = 1
        for event in self.events:
            if event[0] in ('ns_start', 'ns_end'):
                kind = NS_START if event[0] == 'ns_start' else NS_END
                chunks.append(struct.pack('<HHIIIII', kind, 16, 24, line, NO_INDEX, ref(event[1]), ref(event[2])))
            elif event[0] == 'start':
                chunks.append(self._element_start(event, line, ref, index))
                line += 1
            elif event[0] == 'end':
                chunks.append(struct.pack('<HHIIIII', ELEMENT_END, 16, 24, line, NO_INDEX, ref(event[1]), ref(event[2])))
            elif event[0] == 'cdata':
                chunks.append(struct.pack('<HHIIIIHBBI', CDATA, 16, 28, line, NO_INDEX, ref(event[1]), 8, 0, event[2], event[3]))
        content = b''.join(chunks)
        return struct.pack('<HHI', RES_XML, 8, 8 + len(content)) + content

    @staticmethod
    def _element_start(event, line: int, ref, index: dict) -> bytes:
        attributes = sorted(event[3], key=lambda a: (a['res'] is None, a['res'] or 0, a['name']))
        body = b''.join((struct.pack('<IIIHBBI', ref(a['ns']), ref(a['name']), ref(a['raw']), 8, 0, a['type'], index[a['value']] if a['type'] == TYPE_STRING else a['value'] & 4294967295) for a in attributes))
        special = [0, 0, 0]
        for i, a in enumerate(attributes):
            if a['ns'] is None and a['name'] in SPECIAL_ATTRIBUTES:
                special[SPECIAL_ATTRIBUTES.index(a['name'])] = i + 1
        head = struct.pack('<IIHHHHHH', ref(event[1]), ref(event[2]), 20, 20, len(attributes), *special)
        size = 16 + len(head) + len(body)
        return struct.pack('<HHIII', ELEMENT_START, 16, size, line, NO_INDEX) + head + body

    @staticmethod
    def _pool(strings: list[str]) -> bytes:
        encoded, offsets = (bytearray(), [])
        for string in strings:
            offsets.append(len(encoded))
            units = string.encode('utf-16-le')
            length = len(units) // 2
            if length > 32767:
                encoded += struct.pack('<HH', 32768 | length >> 16, length & 65535)
            else:
                encoded += struct.pack('<H', length)
            encoded += units + b'\x00\x00'
        encoded += bytes(-len(encoded) % 4)
        header = 28
        strings_start = header + 4 * len(strings)
        size = strings_start + len(encoded)
        return struct.pack('<HHIIIIII', STRING_POOL, header, size, len(strings), 0, 0, strings_start, 0) + struct.pack(f'<{len(strings)}I', *offsets) + bytes(encoded)

def attribute(name: str, res: int, value, kind: int | None=None) -> dict:
    if kind is None:
        kind = TYPE_INT_BOOLEAN if isinstance(value, bool) else TYPE_STRING if isinstance(value, str) else TYPE_INT_DEC
    if kind == TYPE_INT_BOOLEAN:
        value = 4294967295 if value else 0
    return {'ns': ANDROID, 'name': name, 'res': res, 'raw': value if kind == TYPE_STRING else None, 'type': kind, 'value': value}

def element(name: str, attributes, children=()) -> list:
    events = [('start', None, name, list(attributes))]
    for child in children:
        events += child
    events.append(('end', None, name))
    return events
