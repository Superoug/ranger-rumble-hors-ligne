import collections
import copy
import io
import struct
import UnityPy
from UnityPy.enums import ClassIDType
from UnityPy.exceptions import TypeTreeError
from UnityPy.helpers import TypeTreeHelper
from UnityPy.streams import EndianBinaryWriter
from fichiers_unity import is_pptr, local_ref
SCENE_CAB = 'CAB-8281d924e49aa328c1445f8f7e5b67cc'
SHARED_CAB = SCENE_CAB + '.sharedAssets'
ROOT_NAME = 'HUD_EventScreen'
PARENT_NAME = 'HUD_RootCanvas'
AFTER_NAME = 'HUD_Event'
HOLDER_NAME = 'ModelesEvenement'
INFO_NAME = 'Button_Info'
INFO_METHOD = 'OnActiveEventPlayButtonPressed'
UNITY_DEFAULT = 'unity default resources'
ADDED_SPRITES = {('Sprite', 'S_DialoguePortrait_MsZurkon_04')}
ADDED_IDS = 7700001
RGBA32 = 4
TIGHT_MESH = 64
SPRITE_FIXES = {'HUD_EventScreen/Header/AnimBackButton/BackButton/Image': ('Sprite', 'ico_backBtnGreen'), 'HUD_EventScreen/Layout/Header/AnimBackButton/BackButton/Image': ('Sprite', 'ico_backBtnGreen'), 'HUD_EventScreen/Layout/Header/Button_Back/Image': ('Sprite', 'ico_backBtnGreen'), 'EventRewardTrackItem/Current/Icon/ArrowBounce/Scale/AnimArrow': ('Sprite', 'arrow_02'), 'EventRewardTrackGridItem/Current/Icon/ArrowBounce/Scale/AnimArrow': ('Sprite', 'arrow_02')}
TRANSFORMS = (ClassIDType.Transform, ClassIDType.RectTransform)
UNNAMED_TYPES = (ClassIDType.GameObject, ClassIDType.Transform, ClassIDType.RectTransform, ClassIDType.AssetBundle, ClassIDType.CanvasRenderer)

def md4(message):

    def rol(v, n):
        v &= 4294967295
        return (v << n | v >> 32 - n) & 4294967295
    length = len(message) * 8
    message += b'\x80' + bytes((56 - (len(message) + 1) % 64) % 64) + struct.pack('<Q', length)
    a, b, c, d = (1732584193, 4023233417, 2562383102, 271733878)
    for i in range(0, len(message), 64):
        x = struct.unpack('<16I', message[i:i + 64])
        aa, bb, cc, dd = (a, b, c, d)
        for k, n in zip(range(16), [3, 7, 11, 19] * 4):
            a, b, c, d = (d, rol(a + (b & c | ~b & d) + x[k], n), b, c)
        for k, n in zip([0, 4, 8, 12, 1, 5, 9, 13, 2, 6, 10, 14, 3, 7, 11, 15], [3, 5, 9, 13] * 4):
            a, b, c, d = (d, rol(a + (b & c | b & d | c & d) + x[k] + 1518500249, n), b, c)
        for k, n in zip([0, 8, 4, 12, 2, 10, 6, 14, 1, 9, 5, 13, 3, 11, 7, 15], [3, 9, 11, 15] * 4):
            a, b, c, d = (d, rol(a + (b ^ c ^ d) + x[k] + 1859775393, n), b, c)
        a, b, c, d = (a + aa & 4294967295, b + bb & 4294967295, c + cc & 4294967295, d + dd & 4294967295)
    return struct.pack('<4I', a, b, c, d)

def unity6_assembly(name):
    return name[:-4] if name.endswith('.dll') else name

def script_id(script):
    return md4((script['m_ClassName'] + script['m_Namespace'] + unity6_assembly(script['m_AssemblyName'])).encode())

def write(value, node):
    w = EndianBinaryWriter(endian='<')
    TypeTreeHelper.write_typetree(value, node, w)
    return w.bytes

def add_copy(objects, template, path_id, tree):
    copied = copy.copy(template)
    copied.path_id = path_id
    copied.data = write(tree, template.serialized_type.node)
    objects[path_id] = copied
    return copied

def void_call(model, target, type_name, method):
    call = copy.deepcopy(model)
    call.update(m_Target=local_ref(target), m_TargetAssemblyTypeName=type_name, m_MethodName=method, m_Mode=1, m_CallState=2)
    call['m_Arguments'].update(m_ObjectArgument=local_ref(0), m_IntArgument=0, m_FloatArgument=0.0, m_StringArgument='', m_BoolArgument=False)
    return call

def _load(*blobs):
    env = UnityPy.load(*[io.BytesIO(b) if isinstance(b, (bytes, bytearray)) else b for b in blobs])
    files = {}
    for top in env.files.values():
        for name, f in getattr(top, 'files', {top.name: top}).items():
            if hasattr(f, 'objects'):
                files[name] = f
    return (env, files)

def _scripts(files):
    return {o.path_id: o.read_typetree() for f in files.values() for o in f.objects.values() if o.type == ClassIDType.MonoScript}

def _refs(v):
    if isinstance(v, dict):
        if is_pptr(v):
            yield v
            return
        for x in v.values():
            yield from _refs(x)
    elif isinstance(v, list):
        for x in v:
            yield from _refs(x)

def _is_array(node):
    return bool(node.m_Children) and node.m_Children[0].m_Type == 'Array'

def default(node):
    t = node.m_Type
    if t in ('float', 'double'):
        return 0.0
    if t == 'bool':
        return False
    if t == 'string':
        return ''
    if t == 'TypelessData':
        return b''
    if t in TypeTreeHelper.FUNCTION_READ_MAP:
        return 0
    if _is_array(node):
        return []
    if t == 'pair':
        return (default(node.m_Children[0]), default(node.m_Children[1]))
    return {c.m_Name: default(c) for c in node.m_Children}

def merge(src, node, tmpl):
    t = node.m_Type
    if t in TypeTreeHelper.FUNCTION_READ_MAP:
        if src is None:
            return tmpl if tmpl is not None else default(node)
        if t in ('float', 'double'):
            return float(src)
        if t == 'bool':
            return bool(src)
        if t == 'string':
            return src if isinstance(src, str) else ''
        if t == 'TypelessData':
            return src
        return int(src)
    if _is_array(node):
        if src is None:
            return tmpl if tmpl is not None else []
        if isinstance(src, (bytes, bytearray)):
            return src
        item = node.m_Children[0].m_Children[1]
        item_tmpl = tmpl[0] if isinstance(tmpl, (list, tuple)) and len(tmpl) else None
        return [merge(x, item, item_tmpl) for x in src]
    if t == 'pair':
        a, b = src if src is not None else (None, None)
        ta, tb = tmpl if tmpl is not None else (None, None)
        return (merge(a, node.m_Children[0], ta), merge(b, node.m_Children[1], tb))
    out = {}
    for c in node.m_Children:
        tv = tmpl.get(c.m_Name) if isinstance(tmpl, dict) else None
        if isinstance(src, dict) and c.m_Name in src:
            out[c.m_Name] = merge(src[c.m_Name], c, tv)
        else:
            out[c.m_Name] = tv if tv is not None else default(c)
    return out

def full_rect_sprite(tree, texture_id, width, height):
    units = tree['m_PixelsToUnits']
    rect = {'x': 0.0, 'y': 0.0, 'width': float(width), 'height': float(height)}
    tree['m_Rect'] = dict(rect)
    tree['m_Offset'] = {'x': 0.0, 'y': 0.0}
    tree['m_Border'] = {'x': 0.0, 'y': 0.0, 'z': 0.0, 'w': 0.0}
    tree['m_Pivot'] = {'x': 0.5, 'y': 0.5}
    tree['m_PhysicsShape'] = []
    tree['m_AtlasTags'] = []
    tree['m_SpriteAtlas'] = local_ref(0)
    render = tree['m_RD']
    render['texture'] = local_ref(texture_id)
    render['alphaTexture'] = local_ref(0)
    render['secondaryTextures'] = []
    render['textureRect'] = dict(rect)
    render['textureRectOffset'] = {'x': 0.0, 'y': 0.0}
    render['atlasRectOffset'] = {'x': -1.0, 'y': -1.0}
    render['uvTransform'] = {'x': units, 'y': width / 2, 'z': units, 'w': height / 2}
    half_x, half_y = (width / 2 / units, height / 2 / units)
    corners = [(-half_x, half_y, 0.0, 1.0), (half_x, half_y, 1.0, 1.0), (-half_x, -half_y, 0.0, 0.0), (half_x, -half_y, 1.0, 0.0)]
    positions = b''.join((struct.pack('<3f', x, y, 0.0) for x, y, _, _ in corners))
    positions += bytes(-len(positions) % 16)
    vertex = render['m_VertexData']
    old_count = vertex['m_VertexCount']
    if len(vertex['m_DataSize']) != (old_count * 12 + 15 & ~15) + old_count * 8:
        raise SystemExit('greffe : maillage du sprite modele inattendu')
    vertex['m_VertexCount'] = 4
    vertex['m_DataSize'] = positions + b''.join((struct.pack('<2f', u, v) for _, _, u, v in corners))
    render['m_IndexBuffer'] = list(struct.pack('<6H', 0, 1, 2, 2, 1, 3))
    submesh = render['m_SubMeshes'][0]
    submesh.update(firstByte=0, indexCount=6, baseVertex=0, firstVertex=0, vertexCount=4)
    submesh['localAABB'] = {'m_Center': {'x': 0.0, 'y': 0.0, 'z': 0.0}, 'm_Extent': {'x': half_x, 'y': half_y, 'z': 0.0}}
    render['settingsRaw'] &= ~TIGHT_MESH

def asset_name(o):
    tree = o.read_typetree()
    if o.type == ClassIDType.MonoBehaviour and (not tree.get('m_Name')):
        go = tree['m_GameObject']
        gname = ''
        if go['m_FileID'] == 0 and go['m_PathID'] in o.assets_file.objects:
            gname = o.assets_file.objects[go['m_PathID']].read_typetree()['m_Name']
        return ('MonoBehaviour', (tree['m_Script']['m_PathID'], gname))
    return (o.type.name, tree.get('m_Name', ''))

def asset_index(blobs):
    index = collections.defaultdict(list)
    by_key = {}
    for blob in blobs:
        _, files = _load(blob)
        for cab, f in files.items():
            for pid, o in f.objects.items():
                if o.type in UNNAMED_TYPES:
                    continue
                try:
                    key = asset_name(o)
                except (TypeTreeError, ValueError):
                    continue
                index[key].append((cab, pid))
                by_key[cab, pid] = key
    return (index, by_key)

class _Scene:

    def __init__(self, scene_bytes, mono_cab, scripts):
        self.env = UnityPy.load(io.BytesIO(bytes(scene_bytes)))
        self.file = self.env.file
        self.objects = self.file.objects
        self.externals = {e.path.split('/')[-1]: i + 1 for i, e in enumerate(self.file.externals)}
        self.mono_fid = self.externals[mono_cab]
        self.script_type = {}
        self.class_type = {}
        for i, t in enumerate(self.file.types):
            if t.class_id == ClassIDType.MonoBehaviour and t.script_type_index >= 0:
                st = self.file.script_types[t.script_type_index]
                name = scripts.get(st.local_identifier_in_file, {}).get('m_ClassName')
                if name and st.local_serialized_file_index == self.mono_fid:
                    self.script_type.setdefault(name, i)
            elif t.class_id != ClassIDType.MonoBehaviour:
                self.class_type.setdefault(t.class_id, i)
        self.first_of_type = {}
        for o in self.objects.values():
            self.first_of_type.setdefault(o.type_id, o)
        self._templates = {}

    def template(self, type_id):
        if type_id not in self._templates:
            o = self.first_of_type.get(type_id)
            self._templates[type_id] = o.read_typetree() if o is not None else None
        return self._templates[type_id]

    def file_id(self, cab):
        if cab not in self.externals:
            raise SystemExit(f'greffe : la scene 1.10.4 ne depend pas de {cab}')
        return self.externals[cab]

    def game_objects(self, *names):
        found = {}
        for pid, o in self.objects.items():
            if o.type == ClassIDType.GameObject:
                found.setdefault(o.read_typetree()['m_Name'], pid)
        missing = [name for name in names if name not in found]
        if missing:
            raise SystemExit(f'greffe : pas de {missing[0]} dans la scene 1.10.4')
        return [found[name] for name in names]

    def transform(self, go):
        for c in self.objects[go].read_typetree()['m_Component']:
            if self.objects[c['component']['m_PathID']].type in TRANSFORMS:
                return c['component']['m_PathID']
        return None

    def add_script_type(self, old_type, script, script_hash):
        script_type = copy.copy(self.file.script_types[0])
        script_type.local_serialized_file_index = self.mono_fid
        script_type.local_identifier_in_file = script
        self.file.script_types.append(script_type)
        new_type = copy.copy(old_type)
        new_type.script_type_index = len(self.file.script_types) - 1
        new_type.script_id = script_hash
        self.file.types.append(new_type)
        return len(self.file.types) - 1

    def add(self, pid, type_id, data, like):
        obj = copy.copy(like)
        obj.path_id = pid
        obj.type_id = type_id
        obj.serialized_type = self.file.types[type_id]
        obj.class_id = obj.serialized_type.class_id
        known = obj.class_id in ClassIDType._value2member_map_
        obj.type = ClassIDType(obj.class_id) if known else ClassIDType.UnknownType
        obj.data = data
        self.objects[pid] = obj

class Graft:

    def __init__(self, old_scene_bundle, old_mono_bundle, old_asset_bundles, new_asset_bundles, new_mono_bundle, log=print):
        self.log = log
        _, self.old_files = _load(old_scene_bundle)
        self.scene = self.old_files[SCENE_CAB]
        self.shared = self.old_files[SHARED_CAB]
        _, old_mono_files = _load(old_mono_bundle)
        self.old_scripts = _scripts(old_mono_files)
        self.old_mono_cab = next(iter(old_mono_files))
        _, mono_files = _load(new_mono_bundle)
        self.new_mono_cab = next(iter(mono_files))
        self.new_scripts = _scripts(mono_files)
        self.old_index, self.old_keys = asset_index(old_asset_bundles + [old_scene_bundle])
        self.new_index, _ = asset_index(new_asset_bundles)
        self.missing_scripts = {}
        self.old_asset_bundles = old_asset_bundles
        self.added = {}
        self._trees = {}

    def _file(self, where):
        return self.scene if where == 'scene' else self.shared

    def _tree(self, key):
        if key not in self._trees:
            self._trees[key] = self._file(key[0]).objects[key[1]].read_typetree()
        return self._trees[key]

    def _obj(self, key):
        return self._file(key[0]).objects[key[1]]

    def _script_name(self, key):
        return self.old_scripts[self._tree(key)['m_Script']['m_PathID']]['m_ClassName']

    def _where(self, f, fid):
        if fid == 0:
            return 'scene' if f is self.scene else 'shared'
        path = f.externals[fid - 1].path
        if path.endswith('/' + SCENE_CAB) or path == SCENE_CAB:
            return 'scene'
        if path.endswith(SHARED_CAB):
            return 'shared'
        return None

    def _transform(self, gokey):
        for c in self._tree(gokey)['m_Component']:
            k = (gokey[0], c['component']['m_PathID'])
            if self._obj(k).type in TRANSFORMS:
                return k
        return None

    def _game_object(self, key):
        return (key[0], self._tree(key)['m_GameObject']['m_PathID'])

    def _hierarchy(self, gokey):
        out, stack = ([], [gokey])
        while stack:
            g = stack.pop()
            out.append(g)
            for c in self._tree(g)['m_Component']:
                out.append((g[0], c['component']['m_PathID']))
            for ch in self._tree(self._transform(g))['m_Children']:
                stack.append(self._game_object((g[0], ch['m_PathID'])))
        return out

    def _father(self, gokey):
        father = self._tree(self._transform(gokey))['m_Father']['m_PathID']
        return self._game_object((gokey[0], father)) if father else None

    def _prefab_root(self, gokey):
        while (father := self._father(gokey)) is not None:
            gokey = father
        return gokey

    def _go_path(self, gokey):
        parts = []
        while gokey:
            parts.append(self._tree(gokey)['m_Name'])
            if gokey == self.root:
                break
            gokey = self._father(gokey)
        return '/'.join(reversed(parts))

    def _used_model_object(self, f, ref, chosen):
        if not ref['m_PathID']:
            return None
        where = self._where(f, ref['m_FileID'])
        key = (where, ref['m_PathID'])
        if where is None or key in chosen:
            return None
        if ref['m_PathID'] not in self._file(where).objects or where == 'scene':
            return None
        if self._obj(key).type == ClassIDType.GameObject:
            return key
        tree = self._tree(key)
        if isinstance(tree.get('m_GameObject'), dict):
            return self._game_object(key)
        return None

    def closure(self):
        self.root = next((('scene', p) for p, o in self.scene.objects.items() if o.type == ClassIDType.GameObject and o.read_typetree()['m_Name'] == ROOT_NAME))
        chosen = set(self._hierarchy(self.root))
        self.prefabs = []
        todo = sorted(chosen)
        while todo:
            key = todo.pop()
            f = self._file(key[0])
            for ref in _refs(self._tree(key)):
                go = self._used_model_object(f, ref, chosen)
                if go is None:
                    continue
                prefab = self._prefab_root(go)
                new = [x for x in self._hierarchy(prefab) if x not in chosen]
                chosen.update(new)
                todo.extend(new)
                self.prefabs.append(prefab)
        self.chosen = sorted(chosen)
        names = {s.get('m_ClassName') for s in self.new_scripts.values()}
        for key in self.chosen:
            if self._obj(key).type == ClassIDType.MonoBehaviour:
                script = self._tree(key)['m_Script']['m_PathID']
                if self.old_scripts[script]['m_ClassName'] not in names:
                    self.missing_scripts[script] = self.old_scripts[script]
        models = [self._tree(p)['m_Name'] for p in self.prefabs]
        self.log(f'greffe : {len(self.chosen)} objets 1.1.0, modeles {models}')

    def _added_sprite(self, key, cab, pid):
        if key not in self.added:
            ids = ADDED_IDS + 2 * len(self.added)
            self.added[key] = (ids, ids + 1, cab, pid)
        return self.added[key][1]

    def graft(self, scene_bytes):
        if not hasattr(self, 'chosen'):
            self.closure()
        target = _Scene(scene_bytes, self.new_mono_cab, self.new_scripts)
        grafting = _Grafting(self, target)
        grafting.copy_chosen()
        grafting.add_holder()
        grafting.add_info_button()
        grafting.insert_screen()
        grafting.report()
        return target.file.save()

    def patch_preload(self, shared_bytes):
        env = UnityPy.load(io.BytesIO(bytes(shared_bytes)))
        f = env.file
        fids = {e.path.split('/')[-1]: i + 1 for i, e in enumerate(f.externals)}
        self._add_sprites(f)
        fids[SHARED_CAB] = 0
        data = next((o for o in f.objects.values() if o.type == ClassIDType.PreloadData))
        tree = data.read_typetree()
        have = {(a['m_FileID'], a['m_PathID']) for a in tree['m_Assets']}
        added = 0
        for cab, pid in sorted(self.preload, key=str):
            if cab not in fids:
                raise SystemExit(f'greffe : les sharedAssets de la scene ne connaissent pas {cab}')
            key = (fids[cab], pid)
            if key not in have:
                tree['m_Assets'].append({'m_FileID': key[0], 'm_PathID': key[1]})
                have.add(key)
                added += 1
        data.save_typetree(tree)
        self.log(f'greffe : {added} ressources ajoutees au prechargement de la scene')
        return f.save()

    def _add_sprites(self, f):
        if not self.added:
            return
        from PIL import Image
        tex_like = next((o for o in f.objects.values() if o.type == ClassIDType.Texture2D))
        spr_like = next((o for o in f.objects.values() if o.type == ClassIDType.Sprite))
        old = {}
        for blob in self.old_asset_bundles:
            for name, sf in _load(blob)[1].items():
                for _, _, cab, pid in self.added.values():
                    if name == cab and pid in sf.objects:
                        old[cab, pid] = sf.objects[pid].read().image.convert('RGBA')
        for key, (tid, sid, cab, pid) in self.added.items():
            picture = old[cab, pid]
            if tid in f.objects or sid in f.objects:
                raise SystemExit("greffe : ids d'images deja pris")
            tree = tex_like.read_typetree()
            tree['m_Name'] = key[1]
            pixels = picture.transpose(Image.FLIP_TOP_BOTTOM).tobytes()
            tree['m_Width'], tree['m_Height'] = picture.size
            tree['m_CompleteImageSize'] = len(pixels)
            tree['m_TextureFormat'] = RGBA32
            tree['m_MipCount'] = 1
            tree['image data'] = pixels
            tree['m_StreamData'] = {'offset': 0, 'size': 0, 'path': ''}
            add_copy(f.objects, tex_like, tid, tree)
            tree = spr_like.read_typetree()
            tree['m_Name'] = key[1]
            full_rect_sprite(tree, tid, *picture.size)
            add_copy(f.objects, spr_like, sid, tree)
            self.preload.add((SHARED_CAB, tid))
            self.log(f'greffe : image {key[1]} {picture.size} ajoutee aux sharedAssets')

    def patch_monoscripts(self, mono_file_bytes):
        env = UnityPy.load(io.BytesIO(bytes(mono_file_bytes)))
        f = env.file
        like = next((o for o in f.objects.values() if o.type == ClassIDType.MonoScript))
        node = like.serialized_type.node
        tmpl = like.read_typetree()
        for pid, tree in sorted(self.missing_scripts.items()):
            if pid in f.objects:
                raise SystemExit(f'greffe : MonoScript {pid} deja present')
            tree = dict(tree)
            if not tmpl['m_AssemblyName'].endswith('.dll'):
                tree['m_AssemblyName'] = unity6_assembly(tree['m_AssemblyName'])
            add_copy(f.objects, like, pid, merge(tree, node, tmpl))
        return f.save()

class _Grafting:

    def __init__(self, graft, target):
        self.graft, self.target = (graft, target)
        next_id = max(target.objects) + 1
        self.new_id = {key: next_id + i for i, key in enumerate(graft.chosen)}
        next_id += len(graft.chosen)
        self.holder_go, self.holder_rt = (next_id, next_id + 1)
        info_gos = [k for k in graft.chosen if graft._obj(k).type == ClassIDType.GameObject and graft._tree(k)['m_Name'] == INFO_NAME]
        if len(info_gos) != 1:
            raise SystemExit(f'greffe : {len(info_gos)} objets {INFO_NAME}')
        self.info_go = info_gos[0]
        self.info_image = next(((self.info_go[0], c['component']['m_PathID']) for c in graft._tree(self.info_go)['m_Component'] if graft._obj((self.info_go[0], c['component']['m_PathID'])).type == ClassIDType.MonoBehaviour))
        self.info_button = next_id + 2
        parent_go, after_go = target.game_objects(PARENT_NAME, AFTER_NAME)
        self.parent_rt, self.after_rt = (target.transform(parent_go), target.transform(after_go))
        self.root_rt = graft._transform(graft.root)
        self.old_father = graft._tree(self.root_rt)['m_Father']['m_PathID']
        self.prefab_rts = [self.new_id[graft._transform(p)] for p in graft.prefabs]
        self.unresolved = collections.Counter()
        self.added_types = {}
        graft.preload = set()

    def relink(self, value, f):
        if isinstance(value, dict):
            if is_pptr(value):
                return self._reference(value, f)
            return {k: self.relink(v, f) for k, v in value.items()}
        if isinstance(value, list):
            return [self.relink(v, f) for v in value]
        if isinstance(value, tuple):
            return tuple((self.relink(v, f) for v in value))
        return value

    def _reference(self, ref, f):
        graft, target = (self.graft, self.target)
        fid, pid = (ref['m_FileID'], ref['m_PathID'])
        if not pid:
            return local_ref(0)
        where = graft._where(f, fid)
        if where is not None:
            key = (where, pid)
            if key in self.new_id:
                return local_ref(self.new_id[key])
            if where == 'scene' and pid == self.old_father:
                return local_ref(self.parent_rt)
            cab = SHARED_CAB
        else:
            cab = f.externals[fid - 1].path.split('/')[-1]
        if cab == graft.old_mono_cab:
            graft.preload.add((graft.new_mono_cab, pid))
            return {'m_FileID': target.mono_fid, 'm_PathID': pid}
        if cab == UNITY_DEFAULT:
            graft.preload.add((UNITY_DEFAULT, pid))
            return {'m_FileID': target.file_id(UNITY_DEFAULT), 'm_PathID': pid}
        key = graft.old_keys.get((cab, pid))
        if key in ADDED_SPRITES:
            sprite = graft._added_sprite(key, cab, pid)
            graft.preload.add((SHARED_CAB, sprite))
            return {'m_FileID': target.file_id(SHARED_CAB), 'm_PathID': sprite}
        candidates = [c for c in (graft.new_index.get(key, []) if key else []) if c[0] in target.externals]
        candidates = [c for c in candidates if c[1] == pid] + [c for c in candidates if c[1] != pid]
        if candidates:
            new_cab, new_pid = candidates[0]
            graft.preload.add((new_cab, new_pid))
            return {'m_FileID': target.file_id(new_cab), 'm_PathID': new_pid}
        self.unresolved[cab, key] += 1
        return local_ref(0)

    def type_of(self, o, tree):
        graft, target = (self.graft, self.target)
        if o.class_id != ClassIDType.MonoBehaviour:
            i = target.class_type.get(o.class_id)
            if i is None:
                raise SystemExit(f'greffe : classe {o.class_id} absente de la scene 1.10.4')
            return (i, target.file.types[i].node, target.template(i))
        script = tree['m_Script']['m_PathID']
        name = graft.old_scripts[script]['m_ClassName']
        if name in target.script_type:
            i = target.script_type[name]
            return (i, target.file.types[i].node, target.template(i))
        if name not in self.added_types:
            self.added_types[name] = target.add_script_type(o.serialized_type, script, script_id(graft.old_scripts[script]))
        return (self.added_types[name], o.serialized_type.node, None)

    def copy_chosen(self):
        graft, target = (self.graft, self.target)
        for key in graft.chosen:
            o = graft._obj(key)
            tree = self.relink(graft._tree(key), graft._file(key[0]))
            if key == self.info_go:
                tree['m_Component'].append({'component': local_ref(self.info_button)})
            if key == self.info_image:
                tree['m_RaycastTarget'] = True
            if o.type == ClassIDType.MonoBehaviour and 'm_Sprite' in tree:
                fix = SPRITE_FIXES.get(graft._go_path(graft._game_object(key)))
                candidates = [c for c in graft.new_index.get(fix, []) if c[0] in target.externals] if fix else []
                if candidates:
                    tree['m_Sprite'] = {'m_FileID': target.file_id(candidates[0][0]), 'm_PathID': candidates[0][1]}
                    graft.preload.add(candidates[0])
            if o.type in TRANSFORMS and self.new_id[key] in self.prefab_rts:
                tree['m_Father'] = local_ref(self.holder_rt)
            if key == self.root_rt:
                tree['m_Children'].append(local_ref(self.holder_rt))
            type_id, node, template = self.type_of(o, graft._tree(key))
            value = merge(tree, node, template) if template is not None else tree
            like = target.first_of_type.get(type_id) or next(iter(target.objects.values()))
            target.add(self.new_id[key], type_id, write(value, node), like)

    def add_holder(self):
        target = self.target
        go_type = target.class_type[ClassIDType.GameObject]
        go_node = target.file.types[go_type].node
        go_tree = merge({'m_Component': [{'component': local_ref(self.holder_rt)}], 'm_Layer': 5, 'm_Name': HOLDER_NAME, 'm_Tag': 0, 'm_IsActive': False}, go_node, target.template(go_type))
        target.add(self.holder_go, go_type, write(go_tree, go_node), target.first_of_type[go_type])
        rt_type = target.class_type[ClassIDType.RectTransform]
        rt_node = target.file.types[rt_type].node
        rt_tree = merge({'m_GameObject': local_ref(self.holder_go), 'm_LocalRotation': {'x': 0.0, 'y': 0.0, 'z': 0.0, 'w': 1.0}, 'm_LocalPosition': {'x': 0.0, 'y': 0.0, 'z': 0.0}, 'm_LocalScale': {'x': 1.0, 'y': 1.0, 'z': 1.0}, 'm_Children': [local_ref(p) for p in self.prefab_rts], 'm_Father': local_ref(self.new_id[self.root_rt]), 'm_AnchorMin': {'x': 0.5, 'y': 0.5}, 'm_AnchorMax': {'x': 0.5, 'y': 0.5}, 'm_AnchoredPosition': {'x': 0.0, 'y': 0.0}, 'm_SizeDelta': {'x': 100.0, 'y': 100.0}, 'm_Pivot': {'x': 0.5, 'y': 0.5}}, rt_node, target.template(rt_type))
        target.add(self.holder_rt, rt_type, write(rt_tree, rt_node), target.first_of_type[rt_type])

    def add_info_button(self):
        graft, target = (self.graft, self.target)
        button_type = target.script_type.get('Button')
        updaters = []
        for c in graft._tree(graft.root)['m_Component']:
            key = ('scene', c['component']['m_PathID'])
            if graft._obj(key).type == ClassIDType.MonoBehaviour and graft._script_name(key) == 'EventScreenUpdater':
                updaters.append(key)
        if button_type is None or len(updaters) != 1:
            raise SystemExit("greffe : pas de Button dans la scene 1.10.4 ou d'EventScreenUpdater sur l'ecran")
        model, like = (None, None)
        for o in target.objects.values():
            if o.type_id == button_type:
                tree = o.read_typetree()
                if tree['m_OnClick']['m_PersistentCalls']['m_Calls']:
                    model, like = (tree, o)
                    break
        if model is None:
            raise SystemExit('greffe : aucun Button modele avec un appel')
        call = void_call(model['m_OnClick']['m_PersistentCalls']['m_Calls'][0], self.new_id[updaters[0]], 'EventScreenUpdater, Assembly-CSharp', INFO_METHOD)
        button = copy.deepcopy(model)
        button.update(m_GameObject=local_ref(self.new_id[self.info_go]), m_Enabled=1, m_Interactable=True, m_TargetGraphic=local_ref(self.new_id[self.info_image]), m_Name='')
        for k in ('m_SelectOnUp', 'm_SelectOnDown', 'm_SelectOnLeft', 'm_SelectOnRight'):
            if k in button.get('m_Navigation', {}):
                button['m_Navigation'][k] = local_ref(0)
        button['m_OnClick']['m_PersistentCalls']['m_Calls'] = [call]
        target.add(self.info_button, button_type, write(button, target.file.types[button_type].node), like)

    def insert_screen(self):
        parent = self.target.objects[self.parent_rt]
        tree = parent.read_typetree()
        children = tree['m_Children']
        at = next((i for i, c in enumerate(children) if c['m_PathID'] == self.after_rt)) + 1
        children.insert(at, local_ref(self.new_id[self.root_rt]))
        parent.save_typetree(tree)

    def report(self):
        log = self.graft.log
        for (_, key), n in sorted(self.unresolved.items(), key=str):
            log(f'greffe : sans equivalent en 1.10.4 : {key} ({n})')
        log(f'greffe : {len(self.added_types)} types de scripts ajoutes {sorted(self.added_types)}, {len(self.graft.missing_scripts)} MonoScript a ajouter')
