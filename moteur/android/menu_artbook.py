import copy
import io
import UnityPy
from UnityPy.enums import ClassIDType
from greffe_evenement import write, _pptr
NAME = 'Button_Artbook'
LABEL = 'artbook'
SPACING = 12.0

def artbook_menu(scene_bytes, log=print):
    env = UnityPy.load(io.BytesIO(bytes(scene_bytes)))
    f = env.file
    objects = f.objects

    def tree(pid):
        return objects[pid].read_typetree()

    def own(pid):
        return {'m_FileID': 0, 'm_PathID': pid}

    def go_named(name):
        found = [p for p, o in objects.items() if o.type == ClassIDType.GameObject and o.peek_name() == name]
        if len(found) != 1:
            raise SystemExit(f'menu : {len(found)} objets {name}')
        return found[0]

    def components(go):
        return [c['component']['m_PathID'] for c in tree(go)['m_Component']]

    def transform(go):
        return components(go)[0]

    def children(go):
        return [tree(c['m_PathID'])['m_GameObject']['m_PathID'] for c in tree(transform(go))['m_Children']]
    social = go_named('Button_SocialMedia')
    if any((o.type == ClassIDType.GameObject and o.peek_name() == NAME for o in objects.values())):
        raise SystemExit('menu : bouton artbook deja la')
    instagram = go_named('Button_INSTAGRAM')
    popup = go_named('SocialMediaPopup')
    popup_script = [c for c in components(popup) if objects[c].type == ClassIDType.MonoBehaviour and 'instagramButton' in tree(c)]
    if len(popup_script) != 1:
        raise SystemExit('menu : pas de SocialMediaPopup')
    grid_rt = tree(transform(social))['m_Father']['m_PathID']
    grid = tree(grid_rt)['m_GameObject']['m_PathID']
    layout = [c for c in components(grid) if objects[c].type == ClassIDType.MonoBehaviour and 'm_CellSize' in tree(c)]
    if len(layout) != 1:
        raise SystemExit('menu : pas de grille')

    def skipped(pid):
        t = tree(pid)
        return 'stateID' in t or '_key' in t
    gos, stack = ([], [social])
    while stack:
        go = stack.pop()
        gos.append(go)
        stack += children(go)
    kept = []
    for go in gos:
        kept.append(go)
        kept += [c for c in components(go) if not skipped(c)]
    next_id = max(objects) + 1
    new_id = {}
    for pid in kept:
        new_id[pid] = next_id
        next_id += 1

    def relink(value):
        if isinstance(value, dict):
            if _pptr(value):
                if value['m_FileID'] == 0 and value['m_PathID'] in new_id:
                    return own(new_id[value['m_PathID']])
                return value
            return {k: relink(v) for k, v in value.items()}
        if isinstance(value, list):
            return [relink(v) for v in value]
        return value
    mailbox = go_named('Button_Mailbox')

    def all_gos(go):
        out, stack = ([], [go])
        while stack:
            g = stack.pop()
            out.append(g)
            stack += children(g)
        return out
    letter_icons = [tree(c)['m_Sprite'] for g in all_gos(mailbox) for c in components(g) if objects[c].type == ClassIDType.MonoBehaviour and 'm_Sprite' in tree(c) and (tree(g)['m_Name'] == 'Icon') and tree(g)['m_IsActive']]
    social_icons = [c for g in all_gos(social) for c in components(g) if objects[c].type == ClassIDType.MonoBehaviour and 'm_Sprite' in tree(c) and (tree(g)['m_Name'] == 'Icon') and tree(g)['m_IsActive']]
    if len(letter_icons) != 1 or len(social_icons) != 1:
        raise SystemExit('menu : icones inattendues')
    changed = {'label': 0, 'button': 0}
    for old in kept:
        o = objects[old]
        t = relink(tree(old))
        if old == social:
            t['m_Name'] = NAME
        if o.type == ClassIDType.GameObject:
            t['m_Component'] = [c for c in t['m_Component'] if c['component']['m_PathID'] in new_id.values()]
        if 'm_text' in t and isinstance(t['m_text'], str):
            if t['m_text'] != 'social media':
                raise SystemExit(f"menu : texte inattendu {t['m_text']!r}")
            t['m_text'] = LABEL
            changed['label'] += 1
        if 'm_OnClick' in t:
            calls = t['m_OnClick']['m_PersistentCalls']['m_Calls']
            if len(calls) != 1:
                raise SystemExit('menu : appel du bouton inattendu')
            call = copy.deepcopy(calls[0])
            call.update(m_Target=own(popup_script[0]), m_TargetAssemblyTypeName='SocialMediaPopup, Assembly-CSharp', m_MethodName='OpenInstagram', m_Mode=1, m_CallState=2)
            call['m_Arguments'].update(m_ObjectArgument=own(0), m_ObjectArgumentAssemblyTypeName='', m_IntArgument=0, m_FloatArgument=0.0, m_StringArgument='', m_BoolArgument=False)
            t['m_OnClick']['m_PersistentCalls']['m_Calls'] = [call]
            changed['button'] += 1
        if old == social_icons[0]:
            t['m_Sprite'] = letter_icons[0]
        copy_of = copy.copy(o)
        copy_of.path_id = new_id[old]
        copy_of.data = write(t, o.serialized_type.node)
        objects[new_id[old]] = copy_of
    if changed != {'label': 1, 'button': 1}:
        raise SystemExit(f'menu : copie inattendue {changed}')
    grid_tree = tree(grid_rt)
    at = next((i for i, c in enumerate(grid_tree['m_Children']) if c['m_PathID'] == transform(social))) + 1
    grid_tree['m_Children'].insert(at, own(new_id[transform(social)]))
    objects[grid_rt].save_typetree(grid_tree)
    spacing = tree(layout[0])
    spacing['m_Spacing']['y'] = SPACING
    objects[layout[0]].save_typetree(spacing)
    insta = tree(instagram)
    insta['m_IsActive'] = False
    objects[instagram].save_typetree(insta)
    log(f'menu : bouton ARTBOOK dans le menu des 3 traits ({len(kept)} objets copies)')
    return f.save()
