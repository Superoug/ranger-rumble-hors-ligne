from axml import ANDROID, TYPE_REFERENCE, Document, attribute, element
NAME, LABEL, THEME, EXPORTED, PROCESS = (16842755, 16842753, 16842752, 16842768, 16842769)
AUTHORITIES, INIT_ORDER, CLEARTEXT = (16842776, 16842778, 16844012)
ORIENTATION, CONFIG_CHANGES, SCHEME = (16842782, 16842783, 16842791)
SENSOR_LANDSCAPE, ROTATION_CHANGES = (6, 1440)
THEME_FULLSCREEN = 16974122
SPLIT_META = ('com.android.vending.splits.required', 'com.android.vending.splits', 'com.android.vending.derived.apk.id')

def _name(event):
    return next((a['value'] for a in event[3] if a['ns'] == ANDROID and a['name'] == 'name'), None)

def modify(data):
    doc = Document(data)
    manifest = doc.first('manifest')
    before = len(manifest[3])
    manifest[3][:] = [a for a in manifest[3] if a['name'] not in ('requiredSplitTypes', 'splitTypes')]
    split = before - len(manifest[3])
    if split not in (0, 2):
        raise SystemExit('manifeste inattendu : attributs des morceaux')
    removed = doc.remove_element(lambda event: event[2] == 'meta-data' and (_name(event) in SPLIT_META or (_name(event) or '').startswith('com.android.stamp.')))
    if split and removed < 3:
        raise SystemExit('manifeste inattendu : meta-data des morceaux')
    application = doc.first('application')
    application[3][:] = [a for a in application[3] if a['name'] != 'isSplitRequired']
    if any((a['name'] == 'usesCleartextTraffic' for a in application[3])):
        raise SystemExit('manifeste inattendu : usesCleartextTraffic')
    application[3].append(attribute('usesCleartextTraffic', CLEARTEXT, True))
    provider = element('provider', [attribute('name', NAME, 'rr.offline.Demarrage'), attribute('authorities', AUTHORITIES, 'com.playstation.rattlesnake.rroffline'), attribute('exported', EXPORTED, False), attribute('initOrder', INIT_ORDER, 1000)])
    gallery = element('activity', [attribute('name', NAME, 'rr.offline.Galerie'), attribute('label', LABEL, 'Artworks'), attribute('exported', EXPORTED, True), attribute('process', PROCESS, ':galerie'), attribute('theme', THEME, THEME_FULLSCREEN, TYPE_REFERENCE), attribute('screenOrientation', ORIENTATION, SENSOR_LANDSCAPE), attribute('configChanges', CONFIG_CHANGES, ROTATION_CHANGES)], [element('intent-filter', [], [element('action', [attribute('name', NAME, 'android.intent.action.VIEW')]), element('category', [attribute('name', NAME, 'android.intent.category.DEFAULT')]), element('category', [attribute('name', NAME, 'android.intent.category.BROWSABLE')]), element('data', [attribute('scheme', SCHEME, 'rrgalerie')])])])
    doc.insert_before_end('application', provider + gallery)
    doc.insert_before_end('manifest', element('uses-permission', [attribute('name', NAME, 'android.permission.CHANGE_WIFI_MULTICAST_STATE')]))
    return doc.to_bytes()
if __name__ == '__main__':
    import sys
    source, target = sys.argv[1:3]
    open(target, 'wb').write(modify(open(source, 'rb').read()))
