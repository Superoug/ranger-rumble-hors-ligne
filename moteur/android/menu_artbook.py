import io
import UnityPy
from UnityPy.enums import ClassIDType
from fichiers_unity import is_pptr, local_ref
from greffe_evenement import add_copy, void_call
NAME = 'Button_Artbook'
LABEL = 'artbook'
SPACING = 12.0

class _Scene:

    def __init__(self, objects):
        self.objects = objects

    def tree(self, pid):
        return self.objects[pid].read_typetree()

    def game_object(self, name):
        found = [p for p, o in self.objects.items() if o.type == ClassIDType.GameObject and o.peek_name() == name]
        if len(found) != 1:
            raise SystemExit(f'menu : {len(found)} objets {name}')
        return found[0]

    def components(self, go):
        return [c['component']['m_PathID'] for c in self.tree(go)['m_Component']]

    def transform(self, go):
        return self.components(go)[0]

    def children(self, go):
        return [self.tree(c['m_PathID'])['m_GameObject']['m_PathID'] for c in self.tree(self.transform(go))['m_Children']]

    def below(self, go):
        out, stack = ([], [go])
        while stack:
            g = stack.pop()
            out.append(g)
            stack += self.children(g)
        return out

    def scripts_with(self, go, field):
        return [c for c in self.components(go) if self.objects[c].type == ClassIDType.MonoBehaviour and field in self.tree(c)]

    def visible_icons(self, go):
        return [c for g in self.below(go) for c in self.scripts_with(g, 'm_Sprite') if self.tree(g)['m_Name'] == 'Icon' and self.tree(g)['m_IsActive']]

def _relinked(value, new_id):
    if isinstance(value, dict):
        if is_pptr(value):
            if value['m_FileID'] == 0 and value['m_PathID'] in new_id:
                return local_ref(new_id[value['m_PathID']])
            return value
        return {k: _relinked(v, new_id) for k, v in value.items()}
    if isinstance(value, list):
        return [_relinked(v, new_id) for v in value]
    return value

def _button_objects(scene, button):

    def skipped(pid):
        t = scene.tree(pid)
        return 'stateID' in t or '_key' in t
    kept = []
    for go in scene.below(button):
        kept.append(go)
        kept += [c for c in scene.components(go) if not skipped(c)]
    return kept

def artbook_menu(scene_bytes, log=print):
    env = UnityPy.load(io.BytesIO(bytes(scene_bytes)))
    f = env.file
    objects = f.objects
    scene = _Scene(objects)
    social = scene.game_object('Button_SocialMedia')
    if any((o.type == ClassIDType.GameObject and o.peek_name() == NAME for o in objects.values())):
        raise SystemExit('menu : bouton artbook deja la')
    instagram = scene.game_object('Button_INSTAGRAM')
    popup_script = scene.scripts_with(scene.game_object('SocialMediaPopup'), 'instagramButton')
    if len(popup_script) != 1:
        raise SystemExit('menu : pas de SocialMediaPopup')
    grid_rt = scene.tree(scene.transform(social))['m_Father']['m_PathID']
    layout = scene.scripts_with(scene.tree(grid_rt)['m_GameObject']['m_PathID'], 'm_CellSize')
    if len(layout) != 1:
        raise SystemExit('menu : pas de grille')
    kept = _button_objects(scene, social)
    next_id = max(objects) + 1
    new_id = {pid: next_id + i for i, pid in enumerate(kept)}
    letter_icons = [scene.tree(c)['m_Sprite'] for c in scene.visible_icons(scene.game_object('Button_Mailbox'))]
    social_icons = scene.visible_icons(social)
    if len(letter_icons) != 1 or len(social_icons) != 1:
        raise SystemExit('menu : icones inattendues')
    changed = {'label': 0, 'button': 0}
    for old in kept:
        o = objects[old]
        t = _relinked(scene.tree(old), new_id)
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
            call = void_call(calls[0], popup_script[0], 'SocialMediaPopup, Assembly-CSharp', 'OpenInstagram')
            call['m_Arguments']['m_ObjectArgumentAssemblyTypeName'] = ''
            t['m_OnClick']['m_PersistentCalls']['m_Calls'] = [call]
            changed['button'] += 1
        if old == social_icons[0]:
            t['m_Sprite'] = letter_icons[0]
        add_copy(objects, o, new_id[old], t)
    if changed != {'label': 1, 'button': 1}:
        raise SystemExit(f'menu : copie inattendue {changed}')
    grid_tree = scene.tree(grid_rt)
    at = next((i for i, c in enumerate(grid_tree['m_Children']) if c['m_PathID'] == scene.transform(social))) + 1
    grid_tree['m_Children'].insert(at, local_ref(new_id[scene.transform(social)]))
    objects[grid_rt].save_typetree(grid_tree)
    spacing = scene.tree(layout[0])
    spacing['m_Spacing']['y'] = SPACING
    objects[layout[0]].save_typetree(spacing)
    insta = scene.tree(instagram)
    insta['m_IsActive'] = False
    objects[instagram].save_typetree(insta)
    log(f'menu : bouton ARTBOOK dans le menu des 3 traits ({len(kept)} objets copies)')
    return f.save()
