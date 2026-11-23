import io
import UnityPy
from UnityPy.enums import ClassIDType
from UnityPy.exceptions import TypeTreeError
from fichiers_unity import local_ref
from greffe_evenement import add_copy
NAME = 'KingCrown'
ATLAS_CAB = 'cab-eb81065746cc034320560818911bbc9f'
CROWN = 1276451307963928147
COUNTDOWN_PLACE = ((-240.0, 10.0), (150.0, 120.0))
MARK_ROOT = 'CanvasMark_Damageable_Player'
MARK_PLACE = ((0.0, 165.0), (100.0, 80.0))
MARK_CHILDREN = 2
IMAGE_OBJECT = [ClassIDType.RectTransform, ClassIDType.CanvasRenderer, ClassIDType.MonoBehaviour]

def model_image(f, models):
    objects = f.objects
    for pid, o in objects.items():
        if o.type == ClassIDType.GameObject and o.peek_name() in models:
            parts = [c['component']['m_PathID'] for c in o.read_typetree()['m_Component']]
            kinds = [objects[c].type for c in parts if c in objects]
            if kinds == IMAGE_OBJECT and 'm_Sprite' in objects[parts[2]].read_typetree():
                return (pid, parts)
    raise SystemExit("couronne : pas d'image modele")

def add_crown(f, parent_rt, place, models):
    objects = f.objects
    atlas = [i for i, e in enumerate(f.externals, 1) if ATLAS_CAB in e.path.lower()]
    if len(atlas) != 1:
        raise SystemExit('couronne : atlas absent du fichier')
    go, (rt, renderer, image) = model_image(f, models)
    next_id = max(objects) + 1
    ids = {old: next_id + i for i, old in enumerate((go, rt, renderer, image))}

    def add(old, **fields):
        tree = objects[old].read_typetree()
        tree.update(fields)
        add_copy(objects, objects[old], ids[old], tree)
    (x, y), (width, height) = place
    add(go, m_Component=[{'component': local_ref(ids[old])} for old in (rt, renderer, image)], m_Name=NAME, m_IsActive=False)
    add(rt, m_GameObject=local_ref(ids[go]), m_Father=local_ref(parent_rt), m_Children=[], m_LocalRotation={'x': 0.0, 'y': 0.0, 'z': 0.0, 'w': 1.0}, m_LocalPosition={'x': x, 'y': y, 'z': 0.0}, m_LocalScale={'x': 1.0, 'y': 1.0, 'z': 1.0}, m_AnchorMin={'x': 0.5, 'y': 0.5}, m_AnchorMax={'x': 0.5, 'y': 0.5}, m_AnchoredPosition={'x': x, 'y': y}, m_SizeDelta={'x': width, 'y': height}, m_Pivot={'x': 0.5, 'y': 0.5})
    add(renderer, m_GameObject=local_ref(ids[go]))
    add(image, m_GameObject=local_ref(ids[go]), m_Enabled=1, m_Material=local_ref(0), m_Color={'r': 1.0, 'g': 1.0, 'b': 1.0, 'a': 1.0}, m_RaycastTarget=False, m_Sprite={'m_FileID': atlas[0], 'm_PathID': CROWN}, m_Type=0, m_PreserveAspect=True)
    parent = objects[parent_rt].read_typetree()
    parent['m_Children'] = parent['m_Children'] + [local_ref(ids[rt])]
    objects[parent_rt].save_typetree(parent)

def king_crown(bundle_bytes, log=print):
    env = UnityPy.load(io.BytesIO(bytes(bundle_bytes)))
    scenes = [f for name, f in env.file.files.items() if hasattr(f, 'objects') and (not name.endswith('.sharedAssets'))]
    if len(scenes) != 1:
        raise SystemExit('couronne : scene introuvable')
    f = scenes[0]
    objects = f.objects
    widgets = []
    for o in objects.values():
        if o.type == ClassIDType.MonoBehaviour:
            try:
                t = o.read_typetree()
            except (TypeTreeError, ValueError):
                continue
            if 'lastSecondsText' in t and 'timerText' in t:
                widgets.append(t)
    if len(widgets) != 1:
        raise SystemExit(f'couronne : {len(widgets)} minuteurs')
    text_go = objects[widgets[0]['lastSecondsText']['m_PathID']].read_typetree()['m_GameObject']['m_PathID']
    text_rt = objects[text_go].read_typetree()['m_Component'][0]['component']['m_PathID']
    if objects[text_rt].read_typetree()['m_Children']:
        raise SystemExit('couronne : le grand chiffre a deja des enfants')
    add_crown(f, text_rt, COUNTDOWN_PLACE, {'Hexagon'})
    log(f"King's crown beside the big number ({f.name})")
    return env.file.save(packer='lz4')

def mark_crown(bundle_bytes, log=print):
    env = UnityPy.load(io.BytesIO(bytes(bundle_bytes)))
    f = env.assets[0]
    objects = f.objects
    roots = []
    for pid, o in objects.items():
        if o.type == ClassIDType.RectTransform:
            t = o.read_typetree()
            holder = objects.get(t['m_GameObject']['m_PathID'])
            if holder is not None and holder.peek_name() == MARK_ROOT and (not t['m_Father']['m_PathID']):
                roots.append((pid, t))
    if len(roots) != 1:
        raise SystemExit(f'couronne : {len(roots)} reperes de joueur')
    root, tree = roots[0]
    if len(tree['m_Children']) != MARK_CHILDREN:
        raise SystemExit('couronne : repere de joueur inattendu')
    add_crown(f, root, MARK_PLACE, {'Icon'})
    log("King's crown over his head (players' marker)")
    return env.file.save(packer='lz4')
