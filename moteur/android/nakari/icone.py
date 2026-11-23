import os
import struct
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import fichiers_unity as unity
PICTURE = os.path.join(HERE, 'Nakari_vortex.png')
PREVIEW = os.path.join(HERE, 'apercu.png')
KEY = 5638870952370069334
SABRE_SPEC = 4141802964977538426
SPIN_SPRITE = 7928860491325724238
TEXTURE_TEMPLATE = 5824910597922005294
SPEC_COPY = SABRE_SPEC ^ KEY
SPRITE = SPIN_SPRITE ^ KEY
TEXTURE = TEXTURE_TEMPLATE ^ KEY
ATLASES_CAB = 'CAB-eb81065746cc034320560818911bbc9f'
SPEC_NAME = 'Q_Sabre_UltimateWeaponSpec_Nakari'
SPRITE_NAME = 'WeaponIcon_Spin_Nakari'
SPIN_NAME, FACE_NAME = ('WeaponIcon_Spin', 'ico_miniPortrait_Nakari')
SIZE = 256
DATA_OFFSET_AT = 32
OBJECT_ENTRY_SIZE = 24
FACE_SCALE = 1.1
FACE_SHIFT = (0, -6)
OUTLINE_LIGHTNESS = 70
HOLE_MARGIN = 3
CENTRE_RADIUS = (70, 92)

def sprite_canvas(bundle, name):
    import UnityPy
    from PIL import Image
    obj = next((o for o in UnityPy.load(bundle).objects if o.type.name == 'Sprite' and o.peek_name() == name), None)
    if obj is None:
        raise SystemExit(f'icone de Nakari : sprite {name} introuvable')
    tree = obj.read_typetree()
    image = obj.read().image.convert('RGBA')
    width, height = (int(tree['m_Rect']['width']), int(tree['m_Rect']['height']))
    offset = tree['m_RD']['textureRectOffset']
    canvas = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    canvas.paste(image, (round(offset['x']), round(height - offset['y'] - image.height)))
    return canvas

def grow(mask, steps=1):
    for _ in range(steps):
        out = mask.copy()
        out[1:] |= mask[:-1]
        out[:-1] |= mask[1:]
        out[:, 1:] |= mask[:, :-1]
        out[:, :-1] |= mask[:, 1:]
        mask = out
    return mask

def head_mask(rgba):
    import numpy as np
    lightness = (rgba[..., 0] * 299 + rgba[..., 1] * 587 + rgba[..., 2] * 114) / 1000
    wall = np.pad((lightness < OUTLINE_LIGHTNESS) & (rgba[..., 3] > 128), 1)
    outside = np.zeros_like(wall)
    outside[0, :] = outside[-1, :] = outside[:, 0] = outside[:, -1] = True
    outside &= ~wall
    while True:
        reached = grow(outside) & ~wall
        if (reached == outside).all():
            return ~outside[1:-1, 1:-1]
        outside = reached

def swirl_center(rgba, hole):
    import numpy as np
    r, g, b, a = (rgba[..., i] for i in range(4))
    cream = (r > 220) & (g > 150) & (b > 90) & (a > 200)
    edge = cream & grow(~cream) & ~grow(hole, 3)
    ys, xs = np.nonzero(edge)
    if len(xs) < 50:
        raise SystemExit('icone de Nakari : tourbillon introuvable')
    m = np.stack([2 * xs, 2 * ys, np.ones_like(xs)], 1).astype(float)
    cx, cy, _ = np.linalg.lstsq(m, (xs ** 2 + ys ** 2).astype(float), rcond=None)[0]
    return ((cx, cy), tuple(np.median(rgba[cream & ~grow(hole, 3)][:, :3], 0)))

def polar_fill(rgba, hole, center, centre_colour):
    import numpy as np
    cx, cy = center
    ys, xs = np.nonzero(hole)
    step, count = (0.5, 1440)
    radius = int(np.hypot(xs - cx, ys - cy).max()) + 3
    angles = np.linspace(0, 2 * np.pi, count, endpoint=False)
    radii = np.arange(0, radius, step)
    px = cx + radii[:, None] * np.cos(angles)[None]
    py = cy + radii[:, None] * np.sin(angles)[None]
    colours = rgba.astype(float)
    colours[..., :3] *= colours[..., 3:] / 255
    grid = bilinear(colours, px, py)
    known = bilinear((~hole).astype(float)[..., None], px, py)[..., 0] > 0.99
    filled = grid.copy()
    done = np.zeros(len(radii), bool)
    for row in range(len(radii)):
        good = known[row]
        if good.sum() < 2:
            continue
        for channel in range(4):
            filled[row, ~good, channel] = np.interp(angles[~good], angles[good], grid[row, good, channel], period=2 * np.pi)
        done[row] = True
    if not done.any():
        raise SystemExit('icone de Nakari : tourbillon cache')
    rows = np.flatnonzero(done)
    nearest = rows[np.abs(np.arange(len(radii))[:, None] - rows[None]).argmin(1)]
    filled = filled[nearest]
    full, none = CENTRE_RADIUS
    cream = np.clip((none - radii) / (none - full), 0, 1)[:, None, None] * np.array([*centre_colour, 255.0])
    filled += cream * (1 - filled[..., 3:] / 255)
    r = np.hypot(xs - cx, ys - cy) / step
    t = np.arctan2(ys - cy, xs - cx) % (2 * np.pi) / (2 * np.pi) * count
    values = bilinear(filled, t, r, wrap=True)
    out = colours.copy()
    out[ys, xs] = values
    alpha = out[..., 3:]
    out[..., :3] = np.where(alpha > 0, out[..., :3] * 255 / np.maximum(alpha, 1e-06), 0)
    return np.clip(out + 0.5, 0, 255).astype(np.uint8)

def bilinear(image, x, y, wrap=False):
    import numpy as np
    rows, columns = image.shape[:2]
    x0, y0 = (np.floor(x).astype(int), np.floor(y).astype(int))
    fx, fy = ((x - x0)[..., None], (y - y0)[..., None])

    def at(xi, yi):
        xi = xi % columns if wrap else np.clip(xi, 0, columns - 1)
        return image[np.clip(yi, 0, rows - 1), xi]
    top = at(x0, y0) * (1 - fx) + at(x0 + 1, y0) * fx
    bottom = at(x0, y0 + 1) * (1 - fx) + at(x0 + 1, y0 + 1) * fx
    return top * (1 - fy) + bottom * fy

def make_picture(atlases, portraits):
    import numpy as np
    from PIL import Image
    icon = np.asarray(sprite_canvas(atlases, SPIN_NAME)).astype(np.int32)
    face = sprite_canvas(portraits, FACE_NAME)
    if icon.shape[:2] != (SIZE, SIZE):
        raise SystemExit('icone de Nakari : WeaponIcon_Spin inattendu')
    head = head_mask(icon)
    hole = grow(head, HOLE_MARGIN)
    background = Image.fromarray(polar_fill(icon, hole, *swirl_center(icon, hole)))
    face = face.crop(face.getbbox())
    face_alpha = np.asarray(face)[..., 3] > 128
    scale = FACE_SCALE * (head.sum() / face_alpha.sum()) ** 0.5
    face = face.resize((round(face.width * scale), round(face.height * scale)), Image.LANCZOS)
    ys, xs = np.nonzero(head)
    fys, fxs = np.nonzero(np.asarray(face)[..., 3] > 128)
    place = (round(xs.mean() - fxs.mean() + FACE_SHIFT[0]), round(ys.mean() - fys.mean() + FACE_SHIFT[1]))
    background.alpha_composite(face, place)
    return background

def nakari_picture(atlases, portraits=None):
    from PIL import Image
    if os.path.isfile(PICTURE):
        picture = Image.open(PICTURE).convert('RGBA')
        if picture.size != (SIZE, SIZE):
            raise SystemExit(f"icone de Nakari : {PICTURE} n'est pas {SIZE} x {SIZE}")
        return picture
    if portraits is None:
        return None
    return make_picture(atlases, portraits)

def serialized(env):
    files = [f for bundle in env.files.values() for name, f in getattr(bundle, 'files', {}).items() if name.startswith('CAB-') and hasattr(f, 'objects')]
    if len(files) != 1:
        raise SystemExit('icone de Nakari : paquet inattendu')
    return files[0]

def object_table(stream, env):
    file = serialized(env)
    objects = list(file.objects.values())
    data_offset = struct.unpack_from('>Q', stream, DATA_OFFSET_AT)[0]

    def entry(obj):
        return struct.pack('<qqI', obj.path_id, obj.byte_start - data_offset, obj.byte_size)
    head = bytes(stream[:data_offset])
    first, last = (entry(objects[0]), entry(objects[-1]))
    table = head.find(first)
    count = len(objects)
    if table < 0 or head.count(first) != 1 or head[table + (count - 1) * OBJECT_ENTRY_SIZE:][:len(last)] != last:
        raise SystemExit("icone de Nakari : table d'objets introuvable")
    for padding in range(4):
        if struct.unpack_from('<i', stream, table - 4 - padding)[0] == count and (not any(stream[table - padding:table])):
            return (table, count, padding)
    raise SystemExit("icone de Nakari : nombre d'objets introuvable")

def add_copies(data, env, copies):
    import UnityPy
    objects = {o.path_id: o for o in env.objects}
    stream = bytearray(unity.bundle_stream(bytes(data)))
    table, count, padding = object_table(stream, env)
    changes = {new: (old, unity.typetree_change(objects[old], edit)) for new, (old, edit) in copies.items()}
    stream, grown = unity.add_object_copies(stream, table, count, changes, padding)
    unity.replace_bundle_stream(data, stream, grown)
    data[:] = UnityPy.load(bytes(data)).file.save(packer='lz4')

def patch_atlases(data, portraits=None):
    import UnityPy
    picture = nakari_picture(bytes(data), portraits)
    if picture is None:
        print('Nakari icon: picture missing, skipped')
        return False
    env = UnityPy.load(bytes(data))
    objects = {o.path_id: o for o in env.objects}
    sprite, texture = (objects.get(SPIN_SPRITE), objects.get(TEXTURE_TEMPLATE))
    if not sprite or sprite.peek_name() != SPIN_NAME or (not texture) or (texture.type.name != 'Texture2D'):
        raise SystemExit('icone de Nakari : ui_atlases inattendu')

    def texture_edit(tree):
        tree['m_Name'] = SPRITE_NAME
        unity.rgba_texture(tree, picture)

    def sprite_edit(tree):
        tree['m_Name'] = SPRITE_NAME
        tree['m_RenderDataKey'][0]['data[0]'] ^= KEY & 4294967295
        tree['m_AtlasTags'] = []
        tree['m_SpriteAtlas'] = {'m_FileID': 0, 'm_PathID': 0}
        unity.full_rect_sprite(tree, TEXTURE, *picture.size)
    add_copies(data, env, {TEXTURE: (TEXTURE_TEMPLATE, texture_edit), SPRITE: (SPIN_SPRITE, sprite_edit)})
    print(f'Nakari icon: picture {picture.size[0]} x {picture.size[1]} in ui_atlases')
    return True

def patch_ultimates(data):
    import UnityPy
    env = UnityPy.load(bytes(data))
    spec = next((o for o in env.objects if o.path_id == SABRE_SPEC), None)
    if spec is None or spec.peek_name() != 'Q_Sabre_UltimateWeaponSpec':
        raise SystemExit('icone de Nakari : fiche de Vortex introuvable')
    externals = serialized(env).externals
    before = len(externals)
    atlases = unity.external_index(env, ATLASES_CAB)
    if len(externals) != before:
        raise SystemExit('icone de Nakari : ui_atlases absent des dependances de quantum_db_ultimates')
    original = {'m_FileID': atlases, 'm_PathID': SPIN_SPRITE}

    def spec_edit(tree):
        if tree['UltimateAbilityIcon'] != original:
            raise SystemExit('icone de Nakari : icone de Vortex inattendue')
        tree['m_Name'] = SPEC_NAME
        for field in ('UltimateAbilityIcon', 'UltimateAbilityIcon_Small'):
            tree[field] = {'m_FileID': atlases, 'm_PathID': SPRITE}
    add_copies(data, env, {SPEC_COPY: (SABRE_SPEC, spec_edit)})
    print(f'Nakari icon: copy of Q_Sabre_UltimateWeaponSpec ({SPEC_COPY})')
    return True

def nakari_ultimate(characters):
    field = '<UltimateSpec>k__BackingField'
    nakari, lil_ann = (characters.get('NAKARI'), characters.get('LIL_ANN'))
    if not nakari or not lil_ann or (not nakari['ultimates']) or (not lil_ann['ultimates']):
        raise SystemExit("icone de Nakari : fiches de Nakari ou de Lil'Ann introuvables")
    ref, original = (nakari['ultimates'][0][field], lil_ann['ultimates'][0][field])
    if ref != original or ref['m_PathID'] != SABRE_SPEC:
        raise SystemExit("icone de Nakari : son ultime n'est pas Vortex (HERO_ULTIMATES)")
    nakari['ultimates'][0] = dict(nakari['ultimates'][0], **{field: {'m_FileID': ref['m_FileID'], 'm_PathID': SPEC_COPY}})

def preview(original, picture, path=PREVIEW):
    from PIL import Image
    gap = 16
    sheet = Image.new('RGBA', (2 * SIZE + 3 * gap, 2 * SIZE + 3 * gap), (255, 255, 255, 255))
    for row, ground in enumerate(((38, 34, 58, 255), (236, 232, 226, 255))):
        for column, image in enumerate((original, picture)):
            tile = Image.new('RGBA', (SIZE, SIZE), ground)
            tile.alpha_composite(image)
            sheet.paste(tile, (gap + column * (SIZE + gap), gap + row * (SIZE + gap)))
    sheet.convert('RGB').save(path)
if __name__ == '__main__':
    atlases_path, portraits_path = sys.argv[1:3]
    with open(atlases_path, 'rb') as f:
        atlases_bytes = f.read()
    with open(portraits_path, 'rb') as f:
        portraits_bytes = f.read()
    made = make_picture(atlases_bytes, portraits_bytes)
    made.save(PICTURE)
    preview(sprite_canvas(atlases_bytes, SPIN_NAME), made)
    print(PICTURE, PREVIEW)
