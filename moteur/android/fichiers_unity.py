import copy
import json
import struct

def at(data, offset, old, new):
    if len(old) != len(new):
        raise SystemExit('longueurs differentes')
    if data[offset:offset + len(old)] != old:
        raise SystemExit(f'octets inattendus a {offset:#x} : {bytes(data[offset:offset + len(old)]).hex()}')
    data[offset:offset + len(new)] = new

def place(data, address, code):
    at(data, address, bytes(data[address:address + len(code)]), code)

def replace_once(data, old, new, message):
    source = bytes(data)
    if source.count(old) != 1:
        raise SystemExit(message)
    at(data, source.index(old), old, new)
BUNDLE_BLOCK = 131072
COMPRESSION = 63
LZ4HC = 3
BLOCKS_INFO_AT_END = 128
BLOCKS_INFO_PADDED = 512
BLOCKS_AT = 20
BLOCK_ENTRY = struct.Struct('>IIH')
NODE_ENTRY = struct.Struct('>qqI')

def _align16(position):
    return position + 15 & ~15

def _lz4_length(source, position, count):
    if count == 15:
        while True:
            extra = source[position]
            position += 1
            count += extra
            if extra != 255:
                break
    return (count, position)

def lz4_decompress(source, size):
    out = bytearray()
    i = 0
    while True:
        token = source[i]
        count, i = _lz4_length(source, i + 1, token >> 4)
        out += source[i:i + count]
        i += count
        if i >= len(source):
            break
        distance = source[i] | source[i + 1] << 8
        count, i = _lz4_length(source, i + 2, token & 15)
        count += 4
        start = len(out) - distance
        if distance >= count:
            out += out[start:start + count]
        else:
            out += (out[start:] * (count // distance + 1))[:count]
    if len(out) != size:
        raise SystemExit('bloc LZ4 de taille inattendue')
    return out

class _Layout:

    def __init__(self, source):
        position = source.index(b'\x00') + 1 + 4
        position = source.index(b'\x00', position) + 1
        position = source.index(b'\x00', position) + 1
        self.header_end = position
        _, packed_size, info_size, self.flags = struct.unpack('>qIII', source[position:position + 20])
        if self.flags & COMPRESSION != LZ4HC or self.flags & BLOCKS_INFO_AT_END or (not self.flags & BLOCKS_INFO_PADDED):
            raise SystemExit('format de paquet inattendu')
        self.info_start = _align16(position + 20)
        self.info = lz4_decompress(source[self.info_start:self.info_start + packed_size], info_size)
        self.blocks, = struct.unpack('>i', self.info[16:BLOCKS_AT])
        self.data_start = _align16(self.info_start + packed_size)

    def block(self, index):
        entry = BLOCKS_AT + index * BLOCK_ENTRY.size
        return (BLOCK_ENTRY.unpack(self.info[entry:entry + BLOCK_ENTRY.size]), entry)

    def nodes(self):
        return self.info[BLOCKS_AT + self.blocks * BLOCK_ENTRY.size:]

    def write(self, data, source, info, payload):
        data_start = _align16(self.info_start + len(info))
        total = data_start + len(payload)
        head = source[:self.header_end] + struct.pack('>qIII', total, len(info), len(info), self.flags & ~COMPRESSION)
        head = head.ljust(self.info_start, b'\x00') + bytes(info)
        data[:] = head.ljust(data_start, b'\x00') + payload

def _nodes(nodes):
    count, = struct.unpack('>i', nodes[:4])
    position = 4
    for _ in range(count):
        offset, size, flags = NODE_ENTRY.unpack(nodes[position:position + NODE_ENTRY.size])
        end = nodes.index(b'\x00', position + NODE_ENTRY.size) + 1
        yield (offset, size, flags, position, end)
        position = end

def bundle_stream(source):
    layout = _Layout(source)
    stream = bytearray()
    start = layout.data_start
    for index in range(layout.blocks):
        (plain, packed, block_flags), _ = layout.block(index)
        piece = source[start:start + packed]
        start += packed
        stream += lz4_decompress(piece, plain) if block_flags & COMPRESSION else piece
    return bytes(stream)

def write_bundle(data, stream, node_place):
    source = bytes(data)
    layout = _Layout(source)
    block_flags = BLOCK_ENTRY.unpack(layout.info[BLOCKS_AT:BLOCKS_AT + BLOCK_ENTRY.size])[2] & ~COMPRESSION
    nodes = layout.nodes()
    blocks = [stream[i:i + BUNDLE_BLOCK] for i in range(0, len(stream), BUNDLE_BLOCK)]
    new_info = bytes(layout.info[:16]) + struct.pack('>i', len(blocks))
    new_info += b''.join((BLOCK_ENTRY.pack(len(b), len(b), block_flags) for b in blocks))
    new_nodes = bytearray(nodes[:4])
    end = 4
    for offset, size, node_flags, start, end in _nodes(nodes):
        new_nodes += NODE_ENTRY.pack(*node_place(offset, size), node_flags) + nodes[start + NODE_ENTRY.size:end]
    new_info += bytes(new_nodes) + bytes(nodes[end:])
    layout.write(data, source, new_info, bytes(stream))

def bundle_node_count(data):
    return struct.unpack('>i', _Layout(bytes(data)).nodes()[:4])[0]

def replace_bundle_stream(data, stream, grown=0, node=0):
    single = bundle_node_count(data) == 1
    if not single and (not grown):
        raise SystemExit('paquet a plusieurs fichiers')

    def node_place(offset, size):
        if single:
            return (offset, len(stream))
        if offset == node:
            return (offset, size + grown)
        return (offset + grown if offset > node else offset, size)
    write_bundle(data, stream, node_place)

def bundle_node_sizes(data):
    sizes, expected = ([], 0)
    for offset, size, _, _, _ in _nodes(_Layout(bytes(data)).nodes()):
        if offset != expected:
            raise SystemExit('fichiers du paquet non contigus')
        sizes.append(size)
        expected += size
    return sizes

def replace_bundle_nodes(data, stream, sizes):
    if bundle_node_count(data) != len(sizes) or sum(sizes) != len(stream):
        raise SystemExit('tailles de fichiers du paquet incoherentes')
    starts = iter([sum(sizes[:index]) for index in range(len(sizes))])
    sizes_left = iter(sizes)
    write_bundle(data, stream, lambda offset, size: (next(starts), next(sizes_left)))

def patch_bundle(data, edits):
    source = bytes(data)
    layout = _Layout(source)
    info = layout.info
    start = layout.data_start
    stream = 0
    pieces = []
    for index in range(layout.blocks):
        (plain, packed, block_flags), entry = layout.block(index)
        piece = source[start:start + packed]
        start += packed
        here = [edit for edit in edits if stream <= edit[0] < stream + plain]
        if here:
            block = lz4_decompress(piece, plain)
            for offset, old, new in here:
                at(block, offset - stream, old, new)
            piece = bytes(block)
            info[entry:entry + BLOCK_ENTRY.size] = BLOCK_ENTRY.pack(plain, plain, block_flags & ~COMPRESSION)
        pieces.append(piece)
        stream += plain
    if start != len(source):
        raise SystemExit('paquet mal lu')
    layout.write(data, source, info, b''.join(pieces))
HEADER_SIZE = 48
OBJECT_ENTRY = struct.Struct('<qqIi')

def serialized_sizes(stream):
    return struct.unpack('>QQ', stream[24:40])

def object_entries(stream, table, count):
    return [OBJECT_ENTRY.unpack_from(stream, table + i * OBJECT_ENTRY.size) for i in range(count)]

def grow_objects(stream, table, count, changes, shrink=False, types=None):
    file_size, data_offset = serialized_sizes(stream)
    entries = [list(entry) for entry in object_entries(stream, table, count)]
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
        OBJECT_ENTRY.pack_into(stream, table + i * OBJECT_ENTRY.size, *e)
    struct.pack_into('>Q', stream, 24, file_size + total)
    return total

def add_object_copies(stream, table, count, copies, padding=3):
    meta_size = struct.unpack('>I', stream[20:24])[0]
    file_size, data_offset = serialized_sizes(stream)
    by_id = {e[0]: e for e in object_entries(stream, table, count)}
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
    metadata = bytes(stream[HEADER_SIZE:count_at]) + struct.pack('<i', len(entries)) + bytes(stream[count_at + 4:table]) + b''.join((OBJECT_ENTRY.pack(*e) for e in entries)) + bytes(stream[table + count * OBJECT_ENTRY.size:HEADER_SIZE + meta_size])
    if stream[count_at:count_at + 4] != struct.pack('<i', count) or len(metadata) != meta_size + added * OBJECT_ENTRY.size:
        raise SystemExit("table d'objets inattendue")
    new_offset = _align16(HEADER_SIZE + len(metadata))
    head = bytearray(stream[:HEADER_SIZE])
    struct.pack_into('>I', head, 20, len(metadata))
    struct.pack_into('>QQ', head, 24, new_offset + len(data), new_offset)
    new_file = bytes(head) + metadata + bytes(new_offset - HEADER_SIZE - len(metadata)) + bytes(data)
    return (bytearray(new_file + bytes(stream[file_size:])), len(new_file) - file_size)
PPTR = struct.Struct('<iq')

def unity_string(text):
    raw = text.encode('utf-8')
    return struct.pack('<I', len(raw)) + raw + bytes(-len(raw) % 4)

def read_unity_string(raw, position):
    size, = struct.unpack_from('<I', raw, position)
    end = position + 4 + size
    return (raw[position + 4:end].decode(), end + -size % 4)

def raw_text(key):
    return unity_string(key) + struct.pack('<i', 0)

def persistent_call(target, type_name, method, mode, flag=0):
    return PPTR.pack(0, target) + unity_string(type_name) + unity_string(method) + struct.pack('<i', mode) + PPTR.pack(0, 0) + unity_string('UnityEngine.Object, UnityEngine') + struct.pack('<if', 0, 0.0) + unity_string('') + bytes([flag, 0, 0, 0]) + struct.pack('<i', 2)

def relink_local(raw, ids):
    for offset in range(0, len(raw) - 11, 4):
        file_id, path_id = PPTR.unpack_from(raw, offset)
        if file_id == 0 and path_id in ids:
            PPTR.pack_into(raw, offset, 0, ids[path_id])
RECT_CHILDREN = 52

def _children_end(raw):
    return RECT_CHILDREN + 4 + PPTR.size * struct.unpack_from('<i', raw, RECT_CHILDREN)[0]

def rect_child_references(raw):
    count, = struct.unpack_from('<i', raw, RECT_CHILDREN)
    return [PPTR.unpack_from(raw, RECT_CHILDREN + 4 + i * PPTR.size) for i in range(count)]

def rect_children(raw):
    return [path_id for _, path_id in rect_child_references(raw)]

def rect_father(raw):
    return PPTR.unpack_from(raw, _children_end(raw))[1]

def with_children(raw, children):
    return raw[:RECT_CHILDREN] + struct.pack('<i', len(children)) + b''.join((PPTR.pack(0, c) for c in children)) + raw[_children_end(raw):]

def with_added_children(raw, added):
    end = _children_end(raw)
    count, = struct.unpack_from('<i', raw, RECT_CHILDREN)
    return raw[:RECT_CHILDREN] + struct.pack('<i', count + len(added)) + raw[RECT_CHILDREN + 4:end] + b''.join((PPTR.pack(0, a) for a in added)) + raw[end:]

def with_father(raw, father):
    end = _children_end(raw)
    return raw[:end] + PPTR.pack(0, father) + raw[end + PPTR.size:]
LENGTH_DELIMITED = 2
ENTRIES_FIELD = 500

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
        if tag & 7 != LENGTH_DELIMITED:
            raise SystemExit('fichier de langue inattendu')
        size, position = read_varint(data, position)
        yield (tag >> 3, first, position, position + size)
        position += size

def localization_entries(source, error):
    (_, _, root_start, root_end), = list(proto_fields(source, 0, len(source)))
    inner = list(proto_fields(source, root_start, root_end))
    if inner[0][0] != ENTRIES_FIELD:
        raise SystemExit(error)
    _, _, table_start, table_end = inner[0]
    entries = []
    for _, first, start, end in proto_fields(source, table_start, table_end):
        key = next((source[s:e] for f, _, s, e in proto_fields(source, start, end) if f == 1))
        entries.append((key, source[first:end]))
    return (entries, source[table_end:root_end])

def localization_entry(key, text):
    value = text.encode('utf-8')
    body = b'\n' + varint(len(key)) + key + b'\x12' + varint(len(value)) + value
    return b'\n' + varint(len(body)) + body

def localization_file(entries, rest):
    table = b''.join((raw for _, raw in entries))
    root_body = varint(ENTRIES_FIELD << 3 | LENGTH_DELIMITED) + varint(len(table)) + table + rest
    return b'\n' + varint(len(root_body)) + root_body
RGBA32 = 4
TIGHT_MESH = 64

def local_ref(path_id):
    return {'m_FileID': 0, 'm_PathID': path_id}

def is_pptr(value):
    return isinstance(value, dict) and set(value) == {'m_FileID', 'm_PathID'}

def json_copy(value):
    return json.loads(json.dumps(value))

def typetree_change(obj, edit):
    from UnityPy.helpers import TypeTreeHelper
    from UnityPy.streams import EndianBinaryReader, EndianBinaryWriter
    node, assets = (obj._get_typetree_node(), obj.assets_file)

    def change(raw):
        tree = TypeTreeHelper.read_typetree(node, EndianBinaryReader(raw, endian='<'), as_dict=True, byte_size=len(raw), assetsfile=assets)
        edit(tree)
        writer = EndianBinaryWriter(endian='<')
        TypeTreeHelper.write_typetree(tree, node, writer, assets)
        return writer.bytes
    return change

def full_rect_sprite(tree, texture_id, width, height):
    units = tree['m_PixelsToUnits']
    old_count = tree['m_RD']['m_VertexData']['m_VertexCount']
    if len(tree['m_RD']['m_VertexData']['m_DataSize']) != (old_count * 12 + 15 & ~15) + old_count * 8:
        raise SystemExit('maillage de sprite inattendu')
    rect = {'x': 0.0, 'y': 0.0, 'width': float(width), 'height': float(height)}
    tree['m_Rect'] = dict(rect)
    tree['m_PhysicsShape'] = []
    render = tree['m_RD']
    render['texture'] = local_ref(texture_id)
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
    render['settingsRaw'] &= ~TIGHT_MESH

def rgba_texture(tree, picture):
    from PIL import Image
    pixels = picture.transpose(Image.FLIP_TOP_BOTTOM).tobytes()
    tree['m_Width'], tree['m_Height'] = picture.size
    tree['m_CompleteImageSize'] = len(pixels)
    tree['m_TextureFormat'] = RGBA32
    tree['m_MipCount'] = 1
    tree['image data'] = pixels
    tree['m_StreamData'] = {'offset': 0, 'size': 0, 'path': ''}

def external_index(env, cab):
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
