import collections
import copy
import io
import struct
import UnityPy
from UnityPy.enums import ClassIDType
from UnityPy.helpers import TypeTreeHelper
from UnityPy.streams import EndianBinaryWriter
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
SPRITE_FIXES = {'HUD_EventScreen/Header/AnimBackButton/BackButton/Image': ('Sprite', 'ico_backBtnGreen'), 'HUD_EventScreen/Layout/Header/AnimBackButton/BackButton/Image': ('Sprite', 'ico_backBtnGreen'), 'HUD_EventScreen/Layout/Header/Button_Back/Image': ('Sprite', 'ico_backBtnGreen'), 'EventRewardTrackItem/Current/Icon/ArrowBounce/Scale/AnimArrow': ('Sprite', 'arrow_02'), 'EventRewardTrackGridItem/Current/Icon/ArrowBounce/Scale/AnimArrow': ('Sprite', 'arrow_02')}

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

def _load(*blobs):
    env = UnityPy.load(*[io.BytesIO(b) if isinstance(b, (bytes, bytearray)) else b for b in blobs])
    files = {}
    for top in env.files.values():
        for name, f in getattr(top, 'files', {top.name: top}).items():
            if hasattr(f, 'objects'):
                files[name] = f
    return (env, files)

def _scripts(files):
    out = {}
    for f in files.values():
        for o in f.objects.values():
            if o.type == ClassIDType.MonoScript:
                out[o.path_id] = o.read_typetree()
    return out

def _pptr(v):
    return isinstance(v, dict) and set(v) == {'m_FileID', 'm_PathID'}

def _refs(v):
    if isinstance(v, dict):
        if _pptr(v):
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
        sub = node.m_Children[0].m_Children[1]
        elt = tmpl[0] if isinstance(tmpl, (list, tuple)) and len(tmpl) else None
        return [merge(x, sub, elt) for x in src]
    if t == 'pair':
        a, b = src if src is not None else (None, None)
        ta, tb = tmpl if tmpl is not None else (None, None)
        return (merge(a, node.m_Children[0], ta), merge(b, node.m_Children[1], tb))
    out = {}
    for c in node.m_Children:
        sv = src.get(c.m_Name) if isinstance(src, dict) else None
        tv = tmpl.get(c.m_Name) if isinstance(tmpl, dict) else None
        if isinstance(src, dict) and c.m_Name in src:
            out[c.m_Name] = merge(sv, c, tv)
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
    tree['m_SpriteAtlas'] = {'m_FileID': 0, 'm_PathID': 0}
    render = tree['m_RD']
    render['texture'] = {'m_FileID': 0, 'm_PathID': texture_id}
    render['alphaTexture'] = {'m_FileID': 0, 'm_PathID': 0}
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
    render['settingsRaw'] &= ~64

def write(value, node):
    w = EndianBinaryWriter(endian='<')
    TypeTreeHelper.write_typetree(value, node, w)
    return w.bytes

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
                if o.type in (ClassIDType.GameObject, ClassIDType.Transform, ClassIDType.RectTransform, ClassIDType.AssetBundle, ClassIDType.CanvasRenderer):
                    continue
                try:
                    key = asset_name(o)
                except Exception:
                    continue
                index[key].append((cab, pid))
                by_key[cab, pid] = key
    return (index, by_key)

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

    def _file(self, where):
        return self.scene if where == 'scene' else self.shared

    def _tree(self, key):
        if key not in self._trees:
            self._trees[key] = self._file(key[0]).objects[key[1]].read_typetree()
        return self._trees[key]

    def _obj(self, key):
        return self._file(key[0]).objects[key[1]]

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
            if self._obj(k).type in (ClassIDType.Transform, ClassIDType.RectTransform):
                return k

    def _hierarchy(self, gokey):
        out, stack = ([], [gokey])
        while stack:
            g = stack.pop()
            out.append(g)
            for c in self._tree(g)['m_Component']:
                out.append((g[0], c['component']['m_PathID']))
            for ch in self._tree(self._transform(g))['m_Children']:
                stack.append((g[0], self._tree((g[0], ch['m_PathID']))['m_GameObject']['m_PathID']))
        return out

    def _prefab_root(self, gokey):
        while True:
            father = self._tree(self._transform(gokey))['m_Father']['m_PathID']
            if not father:
                return gokey
            gokey = (gokey[0], self._tree((gokey[0], father))['m_GameObject']['m_PathID'])

    def _go_path(self, gokey):
        parts = []
        while gokey:
            parts.append(self._tree(gokey)['m_Name'])
            if gokey == self.root:
                break
            father = self._tree(self._transform(gokey))['m_Father']['m_PathID']
            gokey = (gokey[0], self._tree((gokey[0], father))['m_GameObject']['m_PathID']) if father else None
        return '/'.join(reversed(parts))

    def closure(self):
        self._trees = {}
        root = next((('scene', p) for p, o in self.scene.objects.items() if o.type == ClassIDType.GameObject and o.read_typetree()['m_Name'] == ROOT_NAME))
        self.root = root
        chosen = set(self._hierarchy(root))
        self.prefabs = []
        todo = list(chosen)
        while todo:
            k = todo.pop()
            f = self._file(k[0])
            for r in _refs(self._tree(k)):
                if not r['m_PathID']:
                    continue
                where = self._where(f, r['m_FileID'])
                if where is None or (where, r['m_PathID']) in chosen:
                    continue
                key = (where, r['m_PathID'])
                o = self._obj(key) if r['m_PathID'] in self._file(where).objects else None
                if o is None or where == 'scene':
                    continue
                tree = self._tree(key)
                go = key if o.type == ClassIDType.GameObject else (where, tree['m_GameObject']['m_PathID']) if isinstance(tree.get('m_GameObject'), dict) else None
                if go is None:
                    continue
                pr = self._prefab_root(go)
                new = [x for x in self._hierarchy(pr) if x not in chosen]
                chosen.update(new)
                todo.extend(new)
                self.prefabs.append(pr)
        self.chosen = sorted(chosen)
        names = {s.get('m_ClassName') for s in self.new_scripts.values()}
        for key in self.chosen:
            if self._obj(key).type == ClassIDType.MonoBehaviour:
                sp = self._tree(key)['m_Script']['m_PathID']
                if self.old_scripts[sp]['m_ClassName'] not in names:
                    self.missing_scripts[sp] = self.old_scripts[sp]
        models = [self._tree(p)['m_Name'] for p in self.prefabs]
        self.log(f'greffe : {len(self.chosen)} objets 1.1.0, modeles {models}')

    def graft(self, scene_bytes):
        if not hasattr(self, 'chosen'):
            self.closure()
        env = UnityPy.load(io.BytesIO(bytes(scene_bytes)))
        dst = env.file
        dst_ext = {e.path.split('/')[-1]: i + 1 for i, e in enumerate(dst.externals)}
        mono_fid = dst_ext[self.new_mono_cab]
        objects = dst.objects
        script_type = {}
        class_type = {}
        for i, t in enumerate(dst.types):
            if t.class_id == 114 and t.script_type_index >= 0:
                st = dst.script_types[t.script_type_index]
                name = self.new_scripts.get(st.local_identifier_in_file, {}).get('m_ClassName')
                if name and st.local_serialized_file_index == mono_fid:
                    script_type.setdefault(name, i)
            elif t.class_id != 114:
                class_type.setdefault(t.class_id, i)
        any_obj = {}
        for o in objects.values():
            any_obj.setdefault(o.type_id, o)
        tmpl_tree = {}

        def template(type_id):
            if type_id not in tmpl_tree:
                o = any_obj.get(type_id)
                tmpl_tree[type_id] = o.read_typetree() if o is not None else None
            return tmpl_tree[type_id]
        next_id = max(objects) + 1
        new_id = {}
        for key in self.chosen:
            new_id[key] = next_id
            next_id += 1
        holder_go, holder_rt = (next_id, next_id + 1)
        next_id += 2
        info_gos = [k for k in self.chosen if self._obj(k).type == ClassIDType.GameObject and self._tree(k)['m_Name'] == INFO_NAME]
        if len(info_gos) != 1:
            raise SystemExit(f'greffe : {len(info_gos)} objets {INFO_NAME}')
        info_go = info_gos[0]
        info_image = next(((info_go[0], c['component']['m_PathID']) for c in self._tree(info_go)['m_Component'] if self._obj((info_go[0], c['component']['m_PathID'])).type == ClassIDType.MonoBehaviour))
        info_button = next_id
        next_id += 1
        names = {p: o.read_typetree()['m_Name'] for p, o in objects.items() if o.type == ClassIDType.GameObject}
        parent_go = next((p for p, n in names.items() if n == PARENT_NAME))
        after_go = next((p for p, n in names.items() if n == AFTER_NAME))

        def rt_of(go):
            for c in objects[go].read_typetree()['m_Component']:
                if objects[c['component']['m_PathID']].type in (ClassIDType.RectTransform, ClassIDType.Transform):
                    return c['component']['m_PathID']
        parent_rt, after_rt = (rt_of(parent_go), rt_of(after_go))
        root_rt_old = self._transform(self.root)
        old_father = self._tree(root_rt_old)['m_Father']['m_PathID']
        unresolved = collections.Counter()
        self.preload = set()

        def ext_fid(cab):
            if cab not in dst_ext:
                raise SystemExit(f'greffe : la scene 1.10.4 ne depend pas de {cab}')
            return dst_ext[cab]

        def relink(value, f):
            if isinstance(value, dict):
                if _pptr(value):
                    fid, pid = (value['m_FileID'], value['m_PathID'])
                    if not pid:
                        return {'m_FileID': 0, 'm_PathID': 0}
                    where = self._where(f, fid)
                    if where is not None:
                        key = (where, pid)
                        if key in new_id:
                            return {'m_FileID': 0, 'm_PathID': new_id[key]}
                        if where == 'scene' and pid == old_father:
                            return {'m_FileID': 0, 'm_PathID': parent_rt}
                        cab = SHARED_CAB
                    else:
                        cab = f.externals[fid - 1].path.split('/')[-1]
                    if cab == self.old_mono_cab:
                        self.preload.add((self.new_mono_cab, pid))
                        return {'m_FileID': mono_fid, 'm_PathID': pid}
                    if cab == UNITY_DEFAULT:
                        self.preload.add((UNITY_DEFAULT, pid))
                        return {'m_FileID': ext_fid(UNITY_DEFAULT), 'm_PathID': pid}
                    key = self.old_keys.get((cab, pid))
                    if key in ADDED_SPRITES:
                        if key not in self.added:
                            ids = ADDED_IDS + 2 * len(self.added)
                            self.added[key] = (ids, ids + 1, cab, pid)
                        self.preload.add((SHARED_CAB, self.added[key][1]))
                        return {'m_FileID': ext_fid(SHARED_CAB), 'm_PathID': self.added[key][1]}
                    cands = [c for c in (self.new_index.get(key, []) if key else []) if c[0] in dst_ext]
                    cands = [c for c in cands if c[1] == pid] + [c for c in cands if c[1] != pid]
                    if cands:
                        ncab, npid = cands[0]
                        self.preload.add((ncab, npid))
                        return {'m_FileID': ext_fid(ncab), 'm_PathID': npid}
                    unresolved[cab, key] += 1
                    return {'m_FileID': 0, 'm_PathID': 0}
                return {k: relink(v, f) for k, v in value.items()}
            if isinstance(value, list):
                return [relink(v, f) for v in value]
            if isinstance(value, tuple):
                return tuple((relink(v, f) for v in value))
            return value
        added_types = {}

        def type_for(o, tree):
            if o.class_id != 114:
                i = class_type.get(o.class_id)
                if i is None:
                    raise SystemExit(f'greffe : classe {o.class_id} absente de la scene 1.10.4')
                return (i, dst.types[i].node, template(i))
            sp = tree['m_Script']['m_PathID']
            name = self.old_scripts[sp]['m_ClassName']
            if name in script_type:
                i = script_type[name]
                return (i, dst.types[i].node, template(i))
            if name not in added_types:
                st = copy.copy(dst.script_types[0])
                st.local_serialized_file_index = mono_fid
                st.local_identifier_in_file = sp
                dst.script_types.append(st)
                t = copy.copy(o.serialized_type)
                t.script_type_index = len(dst.script_types) - 1
                t.script_id = script_id(self.old_scripts[sp])
                dst.types.append(t)
                added_types[name] = len(dst.types) - 1
            return (added_types[name], o.serialized_type.node, None)

        def add(pid, type_id, data, like):
            obj = copy.copy(like)
            obj.path_id = pid
            obj.type_id = type_id
            obj.serialized_type = dst.types[type_id]
            obj.class_id = dst.types[type_id].class_id
            obj.type = ClassIDType(obj.class_id) if obj.class_id in ClassIDType._value2member_map_ else ClassIDType.UnknownType
            obj.data = data
            objects[pid] = obj
        holder_father = new_id[root_rt_old]
        prefab_rts = [new_id[self._transform(p)] for p in self.prefabs]
        for key in self.chosen:
            o = self._obj(key)
            tree = relink(self._tree(key), self._file(key[0]))
            if key == info_go:
                tree['m_Component'].append({'component': {'m_FileID': 0, 'm_PathID': info_button}})
            if key == info_image:
                tree['m_RaycastTarget'] = True
            if o.type == ClassIDType.MonoBehaviour and 'm_Sprite' in tree:
                fix = SPRITE_FIXES.get(self._go_path((key[0], self._tree(key)['m_GameObject']['m_PathID'])))
                cands = [c for c in self.new_index.get(fix, []) if c[0] in dst_ext] if fix else []
                if cands:
                    tree['m_Sprite'] = {'m_FileID': ext_fid(cands[0][0]), 'm_PathID': cands[0][1]}
                    self.preload.add(cands[0])
            if o.type in (ClassIDType.Transform, ClassIDType.RectTransform) and new_id[key] in prefab_rts:
                tree['m_Father'] = {'m_FileID': 0, 'm_PathID': holder_rt}
            if key == root_rt_old:
                tree['m_Children'].append({'m_FileID': 0, 'm_PathID': holder_rt})
            type_id, node, tmpl = type_for(o, self._tree(key))
            value = merge(tree, node, tmpl) if tmpl is not None else tree
            like = any_obj.get(type_id) or next(iter(objects.values()))
            add(new_id[key], type_id, write(value, node), like)
        go_type = class_type[1]
        go_tree = merge({'m_Component': [{'component': {'m_FileID': 0, 'm_PathID': holder_rt}}], 'm_Layer': 5, 'm_Name': HOLDER_NAME, 'm_Tag': 0, 'm_IsActive': False}, dst.types[go_type].node, template(go_type))
        add(holder_go, go_type, write(go_tree, dst.types[go_type].node), any_obj[go_type])
        rt_type = class_type[224]
        rt_tmpl = template(rt_type)
        rt_tree = merge({'m_GameObject': {'m_FileID': 0, 'm_PathID': holder_go}, 'm_LocalRotation': {'x': 0.0, 'y': 0.0, 'z': 0.0, 'w': 1.0}, 'm_LocalPosition': {'x': 0.0, 'y': 0.0, 'z': 0.0}, 'm_LocalScale': {'x': 1.0, 'y': 1.0, 'z': 1.0}, 'm_Children': [{'m_FileID': 0, 'm_PathID': p} for p in prefab_rts], 'm_Father': {'m_FileID': 0, 'm_PathID': holder_father}, 'm_AnchorMin': {'x': 0.5, 'y': 0.5}, 'm_AnchorMax': {'x': 0.5, 'y': 0.5}, 'm_AnchoredPosition': {'x': 0.0, 'y': 0.0}, 'm_SizeDelta': {'x': 100.0, 'y': 100.0}, 'm_Pivot': {'x': 0.5, 'y': 0.5}}, dst.types[rt_type].node, rt_tmpl)
        add(holder_rt, rt_type, write(rt_tree, dst.types[rt_type].node), any_obj[rt_type])
        button_type = script_type.get('Button')
        updaters = [c['component']['m_PathID'] for c in self._tree(self.root)['m_Component'] if self._obj(('scene', c['component']['m_PathID'])).type == ClassIDType.MonoBehaviour and self.old_scripts[self._tree(('scene', c['component']['m_PathID']))['m_Script']['m_PathID']]['m_ClassName'] == 'EventScreenUpdater']
        if button_type is None or len(updaters) != 1:
            raise SystemExit("greffe : pas de Button dans la scene 1.10.4 ou d'EventScreenUpdater sur l'ecran")

        def own(pid):
            return {'m_FileID': 0, 'm_PathID': pid}
        model, like_button = (None, None)
        for o in objects.values():
            if o.type_id == button_type:
                t = o.read_typetree()
                if t['m_OnClick']['m_PersistentCalls']['m_Calls']:
                    model, like_button = (t, o)
                    break
        if model is None:
            raise SystemExit('greffe : aucun Button modele avec un appel')
        call = copy.deepcopy(model['m_OnClick']['m_PersistentCalls']['m_Calls'][0])
        call.update(m_Target=own(new_id['scene', updaters[0]]), m_TargetAssemblyTypeName='EventScreenUpdater, Assembly-CSharp', m_MethodName=INFO_METHOD, m_Mode=1, m_CallState=2)
        call['m_Arguments'].update(m_ObjectArgument=own(0), m_IntArgument=0, m_FloatArgument=0.0, m_StringArgument='', m_BoolArgument=False)
        button = copy.deepcopy(model)
        button.update(m_GameObject=own(new_id[info_go]), m_Enabled=1, m_Interactable=True, m_TargetGraphic=own(new_id[info_image]), m_Name='')
        for k in ('m_SelectOnUp', 'm_SelectOnDown', 'm_SelectOnLeft', 'm_SelectOnRight'):
            if k in button.get('m_Navigation', {}):
                button['m_Navigation'][k] = own(0)
        button['m_OnClick']['m_PersistentCalls']['m_Calls'] = [call]
        add(info_button, button_type, write(button, dst.types[button_type].node), like_button)
        parent = objects[parent_rt]
        ptree = parent.read_typetree()
        children = ptree['m_Children']
        at = next((i for i, c in enumerate(children) if c['m_PathID'] == after_rt)) + 1
        children.insert(at, {'m_FileID': 0, 'm_PathID': new_id[root_rt_old]})
        parent.save_typetree(ptree)
        for (cab, key), n in sorted(unresolved.items(), key=str):
            self.log(f'greffe : sans equivalent en 1.10.4 : {key} ({n})')
        self.log(f'greffe : {len(added_types)} types de scripts ajoutes {sorted(added_types)}, {len(self.missing_scripts)} MonoScript a ajouter')
        return dst.save()

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
                for (_, _), (tid, sid, cab, pid) in self.added.items():
                    if name == cab and pid in sf.objects:
                        old[cab, pid] = sf.objects[pid].read().image.convert('RGBA')
        for key, (tid, sid, cab, pid) in self.added.items():
            picture = old[cab, pid]
            if tid in f.objects or sid in f.objects:
                raise SystemExit("greffe : ids d'images deja pris")
            tex = copy.copy(tex_like)
            tex.path_id = tid
            tree = tex_like.read_typetree()
            tree['m_Name'] = key[1]
            pixels = picture.transpose(Image.FLIP_TOP_BOTTOM).tobytes()
            tree['m_Width'], tree['m_Height'] = picture.size
            tree['m_CompleteImageSize'] = len(pixels)
            tree['m_TextureFormat'] = 4
            tree['m_MipCount'] = 1
            tree['image data'] = pixels
            tree['m_StreamData'] = {'offset': 0, 'size': 0, 'path': ''}
            tex.data = write(tree, tex_like.serialized_type.node)
            f.objects[tid] = tex
            spr = copy.copy(spr_like)
            spr.path_id = sid
            tree = spr_like.read_typetree()
            tree['m_Name'] = key[1]
            full_rect_sprite(tree, tid, *picture.size)
            spr.data = write(tree, spr_like.serialized_type.node)
            f.objects[sid] = spr
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
            obj = copy.copy(like)
            obj.path_id = pid
            obj.data = write(merge(tree, node, tmpl), node)
            f.objects[pid] = obj
        return f.save()
