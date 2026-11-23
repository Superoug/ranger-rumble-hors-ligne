import io
import UnityPy
from UnityPy.enums import ClassIDType
from fichiers_unity import local_ref
from greffe_evenement import add_copy, void_call
from menu_artbook import _Scene, _button_objects, _relinked
NAME = 'Button_CheckUpdate'
ICON_BUNDLE = 'CAB-e95ed0243d9b9a50a7c76431b4705d22'
ICON = 6091256297870649931
SHIFT = 0.07
BACKGROUND = {'r': 0.07, 'g': 0.33, 'b': 0.4, 'a': 1.0}
ICON_SCALE = 1.3

def update_button(scene_bytes, log=print):
    env = UnityPy.load(io.BytesIO(bytes(scene_bytes)))
    f = env.file
    objects = f.objects
    scene = _Scene(objects)
    if any((o.type == ClassIDType.GameObject and o.peek_name() == NAME for o in objects.values())):
        raise SystemExit('boite de reception : bouton de mise a jour deja la')
    inbox = scene.game_object('HUD_Inbox')
    bins = [g for g in scene.below(inbox) if scene.tree(g)['m_Name'] == 'DeleteAllButton']
    if len(bins) != 1:
        raise SystemExit('boite de reception : bouton Tout supprimer introuvable')
    bin_button = bins[0]
    popup = scene.scripts_with(scene.game_object('SocialMediaPopup'), 'tiktokButton')
    if len(popup) != 1:
        raise SystemExit('boite de reception : pas de SocialMediaPopup')
    externals = [e.path.split('/')[-1] for e in f.externals]
    if ICON_BUNDLE not in externals:
        raise SystemExit("boite de reception : textures de l'interface absentes de la scene")
    icon = {'m_FileID': externals.index(ICON_BUNDLE) + 1, 'm_PathID': ICON}
    kept = _button_objects(scene, bin_button)
    next_id = max(objects) + 1
    new_id = {pid: next_id + i for i, pid in enumerate(kept)}
    changed = {'button': 0, 'icon': 0, 'place': 0}
    for old in kept:
        o = objects[old]
        t = _relinked(scene.tree(old), new_id)
        if old == bin_button:
            t['m_Name'] = NAME
        if o.type == ClassIDType.GameObject:
            t['m_Component'] = [c for c in t['m_Component'] if c['component']['m_PathID'] in new_id.values()]
        if old == scene.transform(bin_button):
            t['m_AnchorMin']['x'] -= SHIFT
            t['m_AnchorMax']['x'] -= SHIFT
            changed['place'] += 1
        if 'm_OnClick' in t:
            calls = t['m_OnClick']['m_PersistentCalls']['m_Calls']
            if len(calls) != 1:
                raise SystemExit('boite de reception : appel du bouton inattendu')
            call = void_call(calls[0], popup[0], 'SocialMediaPopup, Assembly-CSharp', 'OpenTikTok')
            call['m_Arguments']['m_ObjectArgumentAssemblyTypeName'] = ''
            t['m_OnClick']['m_PersistentCalls']['m_Calls'] = [call]
            changed['button'] += 1
        holder = scene.tree(scene.tree(old)['m_GameObject']['m_PathID'])['m_Name'] if 'm_GameObject' in t else ''
        if 'm_Sprite' in t and o.type == ClassIDType.MonoBehaviour and (holder == 'TargetGraphic'):
            t['m_Color'] = dict(BACKGROUND)
        if o.type == ClassIDType.RectTransform and holder == 'Image':
            t['m_SizeDelta'] = {k: v * ICON_SCALE for k, v in t['m_SizeDelta'].items()}
        if 'm_Sprite' in t and o.type == ClassIDType.MonoBehaviour and (holder == 'Image'):
            t['m_Sprite'] = icon
            t['m_Color'] = {'r': 1.0, 'g': 1.0, 'b': 1.0, 'a': 1.0}
            t['m_PreserveAspect'] = 1
            changed['icon'] += 1
        add_copy(objects, o, new_id[old], t)
    if changed != {'button': 1, 'icon': 1, 'place': 1}:
        raise SystemExit(f'boite de reception : copie inattendue {changed}')
    parent_rt = scene.tree(scene.transform(bin_button))['m_Father']['m_PathID']
    parent = scene.tree(parent_rt)
    at = next((i for i, c in enumerate(parent['m_Children']) if c['m_PathID'] == scene.transform(bin_button))) + 1
    parent['m_Children'].insert(at, local_ref(new_id[scene.transform(bin_button)]))
    objects[parent_rt].save_typetree(parent)
    tiktok = scene.game_object('Button_TIKTOK')
    tree = scene.tree(tiktok)
    tree['m_IsActive'] = False
    objects[tiktok].save_typetree(tree)
    log(f'inbox: update check button ({len(kept)} objects copied)')
    return f.save()
