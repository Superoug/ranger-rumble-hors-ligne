import copy
import math
import numpy as np
from PIL import Image, ImageDraw
SIZE = 512
SEGMENTS = 20
FINISHES = {'panneau': ((84, 90, 104), 0.35, 0.6, None), 'plaque': ((72, 78, 92), 0.4, 0.7, None), 'rainure': ((40, 44, 54), 0.3, 0.4, None), 'acier': ((176, 184, 198), 0.4, 0.78, None), 'argent': ((204, 210, 218), 0.45, 0.82, None), 'bleu': ((44, 56, 82), 0.35, 0.82, None), 'caoutchouc': ((30, 32, 38), 0.0, 0.25, None), 'cyan': ((110, 236, 255), 0.0, 0.9, (70, 220, 255)), 'orange': ((255, 170, 70), 0.0, 0.9, (255, 140, 40)), 'fenetre': ((40, 110, 170), 0.1, 0.9, (20, 90, 150)), 'cuivre': ((190, 104, 64), 0.35, 0.7, None), 'bleu_vif': ((70, 150, 255), 0.0, 0.9, (40, 120, 255))}
VERTEX_COLOUR = (0, 85, 174, 255)
R = 0.29
HEAD_SIZE = 0.81
DESIGN_Y = 1.25 - R
TIP = 1.12
HEAD_Y = TIP - R * HEAD_SIZE
BODY_Y = DESIGN_Y - 0.02
BODY_R = 0.205
MARGIN = 8
HANDLE_END = -0.15

def _blocks():
    return {name: (i % 4 * 128, i // 4 * 128, 128) for i, name in enumerate(FINISHES)}

def _basis(axis):
    return {'x': ((0, 1, 0), (0, 0, 1), (1, 0, 0)), 'y': ((1, 0, 0), (0, 0, 1), (0, 1, 0)), 'z': ((1, 0, 0), (0, 1, 0), (0, 0, 1))}[axis]

class Builder:

    def __init__(self):
        self.vertices, self.normals, self.tangents, self.uvs, self.triangles = ([], [], [], [], [])
        self.blocks = _blocks()

    def _band(self, ring0, ring1, finish):
        u0, v0, size = self.blocks[finish]
        base = len(self.vertices)
        count = len(ring0)
        for k in range(count):
            for (p, n, tg), t in ((ring0[k], 0.0), (ring1[k], 1.0)):
                self.vertices.append(tuple(p))
                norm = math.sqrt(sum((x * x for x in n))) or 1.0
                self.normals.append(tuple((x / norm for x in n)))
                self.tangents.append(tuple(tg) + (1.0,))
                self.uvs.append(((u0 + MARGIN + (size - 2 * MARGIN) * k / (count - 1)) / SIZE, 1.0 - (v0 + MARGIN + (size - 2 * MARGIN) * t) / SIZE))
        for k in range(count - 1):
            a, b, c, d = (base + 2 * k, base + 2 * k + 1, base + 2 * (k + 1), base + 2 * (k + 1) + 1)
            self.triangles += [(a, c, b), (b, c, d)]

    def extrude(self, shape, profile, axis, centre, finish_of):
        e1, e2, ea = (np.array(v, float) for v in _basis(axis))
        c = np.array(centre, float)
        for i in range(len(profile) - 1):
            (s0, h0), (s1, h1) = (profile[i], profile[i + 1])
            if s0 == s1 == 0 or (s0 == s1 and h0 == h1):
                continue
            ds, dh = (s1 - s0, h1 - h0)
            rings = []
            for s, h in ((s0, h0), (s1, h1)):
                ring = []
                for (px, py), (nx, ny) in shape:
                    point = c + e1 * (s * px) + e2 * (s * py) + ea * h
                    normal = e1 * (nx * dh) + e2 * (ny * dh) + ea * (-ds * (nx * px + ny * py))
                    tangent = e1 * -ny + e2 * nx
                    ring.append((point, normal, tangent))
                rings.append(ring)
            self._band(rings[0], rings[1], finish_of(i))

    def lathe(self, profile, axis, centre, finish_of, segments=SEGMENTS):
        circle = [((math.cos(2 * math.pi * k / segments), math.sin(2 * math.pi * k / segments)), (math.cos(2 * math.pi * k / segments), math.sin(2 * math.pi * k / segments))) for k in range(segments + 1)]
        self.extrude(circle, profile, axis, centre, finish_of)

    def place_since(self, start, design, factor, centre):
        d, c = (np.array(design, float), np.array(centre, float))
        for i in range(start, len(self.vertices)):
            self.vertices[i] = tuple(c + (np.array(self.vertices[i]) - d) * factor)

    def quad(self, p0, p1, p2, p3, outward, finish):
        p0, p1, p2, p3 = (np.array(p, float) for p in (p0, p1, p2, p3))
        n = np.cross(p1 - p0, p3 - p0)
        n /= np.linalg.norm(n) or 1.0
        if n @ (np.array(outward, float) - (p0 + p1 + p2 + p3) / 4) > 0:
            n = -n
        t = (p1 - p0) / (np.linalg.norm(p1 - p0) or 1.0)
        self._band([(p0, n, t), (p1, n, t)], [(p3, n, t), (p2, n, t)], finish)

    def tab(self, hub, side, angle, outer=0.112, inner=0.034, base=(0.236, 0.206), height=0.014, half_base=0.029, half_top=0.018):
        u = np.array([0.0, math.cos(angle), math.sin(angle)])
        v = np.array([0.0, -math.sin(angle), math.cos(angle)])
        c = np.array(hub, float)

        def point(r, w, x):
            return c + u * r + v * w + np.array([side * x, 0.0, 0.0])
        bo, bi = base
        end = inner + 0.01
        corners = {'obl': point(outer, -half_base, bo), 'obr': point(outer, half_base, bo), 'otl': point(outer, -half_top, bo + height), 'otr': point(outer, half_top, bo + height), 'ibl': point(inner, -half_base, bi), 'ibr': point(inner, half_base, bi), 'itl': point(end, -half_top, bi + height), 'itr': point(end, half_top, bi + height)}
        middle = point((outer + inner) / 2, 0.0, (bo + bi) / 2 - 0.05)
        k = corners
        self.quad(k['otl'], k['otr'], k['itr'], k['itl'], middle, 'acier')
        self.quad(k['obl'], k['otl'], k['itl'], k['ibl'], middle, 'acier')
        self.quad(k['otr'], k['obr'], k['ibr'], k['itr'], middle, 'acier')
        self.quad(k['itl'], k['itr'], k['ibr'], k['ibl'], middle, 'acier')
        self.quad(k['obl'], k['obr'], k['otr'], k['otl'], middle, 'rainure')

    def tube(self, path, radius, finish, sides=8):
        points = [np.array(p, float) for p in path]
        rings = []
        for i, p in enumerate(points):
            t = points[min(i + 1, len(points) - 1)] - points[max(i - 1, 0)]
            t /= np.linalg.norm(t)
            u = np.cross(t, (1.0, 0.0, 0.0) if abs(t[0]) < 0.9 else (0.0, 1.0, 0.0))
            u /= np.linalg.norm(u)
            v = np.cross(t, u)
            ring = []
            for k in range(sides + 1):
                a = 2 * math.pi * k / sides
                n = u * math.cos(a) + v * math.sin(a)
                ring.append((p + n * radius, n, t))
            rings.append(ring)
        for ring0, ring1 in zip(rings, rings[1:]):
            self._band(ring0, ring1, finish)

    def prism(self, polygon, axis, low, high, centre, finish, turn=0.0):
        e1, e2, ea = (np.array(v, float) for v in _basis(axis))
        c = np.array(centre, float)
        ct, st = (math.cos(turn), math.sin(turn))
        pts = [(a * ct - b * st, a * st + b * ct) for a, b in polygon]

        def world(a, b, h):
            return c + e1 * a + e2 * b + ea * h
        for k in range(len(pts)):
            (a0, b0), (a1, b1) = (pts[k], pts[(k + 1) % len(pts)])
            n2 = np.array([b1 - b0, -(a1 - a0)])
            normal = e1 * n2[0] + e2 * n2[1]
            tangent = e1 * (a1 - a0) + e2 * (b1 - b0)
            self._band([(world(a0, b0, low), normal, tangent), (world(a1, b1, low), normal, tangent)], [(world(a0, b0, high), normal, tangent), (world(a1, b1, high), normal, tangent)], finish)
        for h, sign in ((low, -1.0), (high, 1.0)):
            ca = sum((a for a, _ in pts)) / len(pts)
            cb = sum((b for _, b in pts)) / len(pts)
            ring0 = [(world(ca, cb, h), ea * sign, e1)] * len(pts) + [(world(ca, cb, h), ea * sign, e1)]
            ring1 = [(world(a, b, h), ea * sign, e1) for a, b in pts] + [(world(*pts[0], h), ea * sign, e1)]
            self._band(ring0, ring1, finish)

def _with_normals(points, count):
    shape = []
    for k in range(count + 1):
        a, b = (points[(k - 1) % count], points[(k + 1) % count])
        tx, ty = (b[0] - a[0], b[1] - a[1])
        length = math.hypot(tx, ty) or 1.0
        shape.append((points[k], (ty / length, -tx / length)))
    return shape

def plated_circle(radius, plates=8, depth=0.02, width=0.07, count=160):
    points = []
    half = math.pi / plates
    for k in range(count + 1):
        a = 2 * math.pi * k / count
        phase = a * plates / (2 * math.pi) % 1.0
        offset = a % (2 * half) - half
        flat = math.cos(half) / math.cos(offset)
        r = radius * (0.55 + 0.45 * flat) / (0.55 + 0.45 * 1.0)
        if min(phase, 1 - phase) < width / 2:
            r -= depth
        points.append((r * math.cos(a + half), r * math.sin(a + half)))
    return _with_normals(points, count)

def crescent(inner, outer, start, end, count=24):
    angles = [start + (end - start) * k / count for k in range(count + 1)]
    points = [(outer * math.cos(a), outer * math.sin(a)) for a in angles]
    points += [(inner * math.cos(a), inner * math.sin(a)) for a in reversed(angles)]
    points.append(points[0])
    return _with_normals(points, len(points) - 1)

def marked(points):
    return ([(a, h) for a, h, _ in points], lambda i: points[i][2])

def build():
    b = Builder()
    origin = (0.0, 0.0, 0.0)
    head = (0.0, DESIGN_Y, 0.0)

    def placed(y):
        return HEAD_Y + (y - DESIGN_Y) * HEAD_SIZE
    p = HANDLE_END - 0.04
    b.lathe([(r, y + p) for r, y in [(0.0, 0.04), (0.05, 0.04), (0.062, 0.044), (0.074, 0.052), (0.076, 0.062), (0.068, 0.07), (0.052, 0.078), (0.048, 0.1), (0.05, 0.114), (0.062, 0.12)]], 'y', origin, lambda i: 'orange' if i == 0 else 'rainure' if i == 7 else 'argent')
    grip, y0, y1, ribs = ([(0.062, 0.12 + p), (0.058, 0.128 + p)], 0.128 + p, 0.572, 15)
    step = (y1 - y0) / ribs
    for k in range(ribs):
        y = y0 + k * step
        grip += [(0.052, y + step * 0.08), (0.066, y + step * 0.32), (0.066, y + step * 0.68), (0.052, y + step * 0.92)]
    grip += [(0.058, 0.58)]
    b.lathe(grip, 'y', origin, lambda i: 'caoutchouc')
    b.lathe([(0.058, 0.58), (0.068, 0.584), (0.068, 0.596), (0.036, 0.602), (0.036, placed(0.548))], 'y', origin, lambda i: 'argent')
    head_start = len(b.vertices)
    profile, finish_of = marked([(0.036, 0.53, 'argent'), (0.072, 0.54, 'argent'), (0.078, 0.548, 'argent'), (0.078, 0.566, 'argent'), (0.058, 0.572, 'rainure'), (0.058, 0.6, 'acier'), (0.065, 0.604, 'acier'), (0.065, 0.614, 'rainure'), (0.058, 0.618, 'rainure'), (0.058, 0.63, 'acier'), (0.065, 0.634, 'acier'), (0.065, 0.644, 'rainure'), (0.058, 0.648, 'rainure'), (0.058, 0.664, 'acier'), (0.065, 0.668, 'acier'), (0.092, 0.674, 'acier'), (0.092, 0.698, 'rainure'), (0.08, 0.704, 'rainure'), (0.08, 0.78, None)])
    b.lathe(profile, 'y', origin, finish_of)
    block = plated_circle(R, plates=8, depth=0.022, width=0.07, count=160)
    profile, finish_of = marked([(0.7, -0.428, 'acier'), (0.82, -0.428, 'acier'), (0.92, -0.423, 'acier'), (0.97, -0.415, 'acier'), (1.0, -0.401, 'plaque'), (1.0, -0.367, 'rainure'), (0.92, -0.361, 'rainure'), (0.92, -0.347, 'rainure'), (1.0, -0.341, 'plaque'), (1.0, -0.12, 'acier'), (0.97, -0.104, 'acier'), (0.92, -0.094, 'rainure'), (0.0, -0.094, None)])
    b.extrude(block, profile, 'z', head, finish_of)
    profile, finish_of = marked([(0.0, -0.443, 'cyan'), (0.094, -0.443, 'cyan'), (0.102, -0.439, 'acier'), (0.106, -0.433, 'acier'), (0.118, -0.438, 'acier'), (0.132, -0.438, 'acier'), (0.138, -0.431, 'rainure'), (0.14, -0.407, 'rainure'), (0.192, -0.407, 'rainure'), (0.196, -0.428, 'acier'), (0.203, -0.428, None)])
    b.lathe(profile, 'z', head, finish_of, segments=40)
    body = (0.0, BODY_Y, 0.0)
    r = BODY_R
    profile, finish_of = marked([(r * 0.9, -0.1, 'acier'), (r + 0.007, -0.092, 'acier'), (r + 0.007, -0.062, 'rainure'), (r - 0.016, -0.056, 'rainure'), (r - 0.016, -0.044, 'rainure'), (r, -0.038, 'bleu'), (r, 0.272, 'acier'), (r + 0.008, 0.278, 'acier'), (r + 0.008, 0.3, 'acier'), (r, 0.306, 'rainure'), (0.174, 0.31, 'bleu'), (0.174, 0.37, 'acier'), (0.165, 0.388, 'acier'), (0.14, 0.402, 'acier'), (0.1, 0.41, 'rainure'), (0.092, 0.402, 'acier'), (0.0, 0.402, None)])
    b.lathe(profile, 'z', body, finish_of, segments=32)
    for side in (-1.0, 1.0):
        for dy in (-0.045, 0.0, 0.045):
            b.prism([(dy - 0.006, 0.322), (dy + 0.006, 0.322), (dy + 0.006, 0.356), (dy - 0.006, 0.356)], 'x', min(side * 0.16, side * 0.178), max(side * 0.16, side * 0.178), body, 'rainure')
    hub = (0.0, DESIGN_Y - 0.005, 0.138)
    for side in (-1.0, 1.0):
        profile, finish_of = marked([(0.15, side * 0.09, 'bleu'), (0.153, side * 0.232, 'bleu'), (0.15, side * 0.244, 'bleu'), (0.112, side * 0.246, 'acier'), (0.108, side * 0.251, 'acier'), (0.102, side * 0.248, 'rainure'), (0.1, side * 0.226, 'bleu_vif'), (0.09, side * 0.214, 'bleu_vif'), (0.05, side * 0.208, 'bleu_vif'), (0.0, side * 0.207, None)])
        b.lathe(profile, 'x', hub, finish_of, segments=56)
        for k in range(3):
            b.tab(hub, side, math.pi / 2 + 2 * math.pi * k / 3 + math.pi / 6)
        for k in range(8):
            a = 2 * math.pi * k / 8 + math.pi / 8
            bolt = (side * 0.245, hub[1] + 0.131 * math.cos(a), hub[2] + 0.131 * math.sin(a))
            b.lathe([(0.0, side * 0.008), (0.006, side * 0.008), (0.01, side * 0.005), (0.011, 0.0)], 'x', bolt, lambda i: 'acier', segments=8)
    scoop = crescent(r + 0.004, r + 0.02, math.radians(60), math.radians(120))
    b.extrude(scoop, [(1.0, 0.06), (1.0, 0.29), (1.04, 0.35), (1.11, 0.4)], 'z', body, lambda i: 'bleu')
    for side in (-1.0, 1.0):
        for z in (0.045, 0.144):
            profile, finish_of = marked([(0.04, side * 0.05, 'argent'), (0.04, side * 0.15, 'argent'), (0.036, side * 0.158, 'argent'), (0.029, side * 0.158, 'rainure'), (0.027, side * 0.146, 'orange'), (0.0, side * 0.146, None)])
            b.lathe(profile, 'x', (0.0, 0.745, z), finish_of, segments=16)
    b.place_since(head_start, head, HEAD_SIZE, (0.0, HEAD_Y, 0.0))
    b.tube([(0.0, placed(0.69), 0.088 * HEAD_SIZE), (0.0, placed(0.62), 0.1 * HEAD_SIZE), (0.0, 0.68, 0.068), (0.0, 0.62, 0.055), (0.0, 0.585, 0.05)], 0.011, 'cuivre')
    vertices, normals = (np.array(b.vertices), np.array(b.normals))
    triangles = []
    for i, j, k in b.triangles:
        face = np.cross(vertices[j] - vertices[i], vertices[k] - vertices[i])
        if np.linalg.norm(face) < 1e-12:
            continue
        triangles.append((i, j, k) if face @ (normals[i] + normals[j] + normals[k]) > 0 else (i, k, j))
    geometry = {'vertices': np.array(b.vertices, np.float32), 'normals': np.array(b.normals, np.float32), 'tangents': np.array(b.tangents, np.float32), 'uvs': np.array(b.uvs, np.float32), 'triangles': np.array(triangles, np.uint16)}
    return (geometry, textures(b.blocks))

def textures(blocks):
    albedo = Image.new('RGBA', (SIZE, SIZE), (128, 128, 128, 255))
    msao = Image.new('RGBA', (SIZE, SIZE), (0, 128, 255, 255))
    emission = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 255))
    normal = Image.new('RGBA', (SIZE, SIZE), (128, 128, 128, 128))
    da, dm, de = (ImageDraw.Draw(albedo), ImageDraw.Draw(msao), ImageDraw.Draw(emission))
    for name, (u0, v0, size) in blocks.items():
        rgb, metal, smooth, glow = FINISHES[name]
        for row in range(size):
            t = row / (size - 1)
            shade = 0.86 + 0.18 * math.sin(math.pi * t)
            colour = tuple((min(255, int(c * shade)) for c in rgb)) + (255,)
            da.line([(u0, v0 + row), (u0 + size - 1, v0 + row)], fill=colour)
        if name == 'plaque':
            for col in range(size):
                p = (col - 8) / (size - 16) * 8 % 1.0
                edge = min(p, 1 - p)
                if edge < 0.035:
                    rgb2 = FINISHES['rainure'][0]
                elif edge < 0.09:
                    rgb2 = FINISHES['acier'][0]
                else:
                    continue
                for row in range(size):
                    shade = 0.86 + 0.18 * math.sin(math.pi * row / (size - 1))
                    albedo.putpixel((u0 + col, v0 + row), tuple((min(255, int(c * shade)) for c in rgb2)) + (255,))
        dm.rectangle([u0, v0, u0 + size - 1, v0 + size - 1], fill=(int(255 * metal), int(255 * smooth), 255, 255))
        if glow:
            de.rectangle([u0, v0, u0 + size - 1, v0 + size - 1], fill=glow + (255,))
    return {'ALB': albedo, 'MSAO': msao, 'E': emission, 'NRM': normal}
VERTEX_LAYOUT = np.dtype([('position', '<f4', 3), ('normal', '<f4', 3), ('tangent', '<f4', 4), ('colour', 'u1', 4), ('uv', '<f4', 2)])

def unity_mesh(tree, geometry):
    v, n, tg, uv, tri = (geometry[k] for k in ('vertices', 'normals', 'tangents', 'uvs', 'triangles'))
    count = len(v)
    channels = [{'stream': 0, 'offset': 0, 'format': 0, 'dimension': 0} for _ in range(14)]
    channels[0] = {'stream': 0, 'offset': 0, 'format': 0, 'dimension': 3}
    channels[1] = {'stream': 0, 'offset': 12, 'format': 0, 'dimension': 3}
    channels[2] = {'stream': 0, 'offset': 24, 'format': 0, 'dimension': 4}
    channels[3] = {'stream': 0, 'offset': 40, 'format': 2, 'dimension': 4}
    channels[4] = {'stream': 0, 'offset': 44, 'format': 0, 'dimension': 2}
    stream = np.empty(count, VERTEX_LAYOUT)
    stream['position'], stream['normal'], stream['tangent'], stream['uv'] = (v, n, tg, uv)
    stream['colour'] = VERTEX_COLOUR
    lo, hi = (v.min(0), v.max(0))
    centre, extent = ((lo + hi) / 2, (hi - lo) / 2)
    aabb = {'m_Center': {'x': float(centre[0]), 'y': float(centre[1]), 'z': float(centre[2])}, 'm_Extent': {'x': float(extent[0]), 'y': float(extent[1]), 'z': float(extent[2])}}
    tree['m_SubMeshes'] = [{'firstByte': 0, 'indexCount': int(tri.size), 'topology': 0, 'baseVertex': 0, 'firstVertex': 0, 'vertexCount': count, 'localAABB': aabb}]
    tree['m_MeshCompression'] = 0
    tree['m_IsReadable'] = True
    tree['m_KeepVertices'] = True
    tree['m_KeepIndices'] = True
    tree['m_IndexFormat'] = 0
    tree['m_IndexBuffer'] = list(tri.astype('<u2').tobytes())
    tree['m_VertexData']['m_VertexCount'] = count
    tree['m_VertexData']['m_Channels'] = channels
    tree['m_VertexData']['m_DataSize'] = stream.tobytes()
    for key, packed in tree['m_CompressedMesh'].items():
        if isinstance(packed, dict) and 'm_NumItems' in packed:
            packed['m_NumItems'] = 0
            packed['m_Data'] = [] if isinstance(packed['m_Data'], list) else b''
            if 'm_BitSize' in packed:
                packed['m_BitSize'] = 0
            if 'm_Range' in packed:
                packed['m_Range'] = 0.0
                packed['m_Start'] = 0.0
        elif key == 'm_UVInfo':
            tree['m_CompressedMesh'][key] = 0
    tree['m_LocalAABB'] = aabb
    tree['m_MeshMetrics[0]'] = 1.0
    tree['m_MeshMetrics[1]'] = 1.0
    tree['m_StreamData'] = {'offset': 0, 'size': 0, 'path': ''}
    if 'm_BakedConvexCollisionMesh' in tree:
        tree['m_BakedConvexCollisionMesh'] = []
        tree['m_BakedTriangleCollisionMesh'] = []
    if 'm_MeshLodInfo' in tree:
        tree['m_MeshLodInfo']['m_NumLevels'] = 1
        tree['m_MeshLodInfo']['m_SubMeshes'] = [{'m_Levels': [{'m_IndexStart': 0, 'm_IndexCount': 0}]}]
    return tree
STEELJAW_MELEE_SPEC = -8982514171037163857
WRENCH_SPEC, HAMMER_SPEC = ('Q_WrenchMelee_WeaponSpec', 'Q_SteeljawMelee_WeaponSpec')
RIVET_CHARACTER, HAMMER_WEAPON_ID = (16, 37)
NAME_KEY, DESCRIPTION_KEY = ('UI.WEAPONS.MELEE.RIVET', 'UI.WEAPON_DESCRIPTION.MELEE.RIVET')
WRENCH_HOLD = {'m_LocalPosition': {'x': 0.0, 'y': 0.005, 'z': 0.0}, 'm_LocalRotation': {'x': 0.0, 'y': -0.70710677, 'z': 0.0, 'w': 0.70710677}, 'm_LocalScale': {'x': 1.16, 'y': 1.16, 'z': 1.16}}
TRAIL_HEIGHT = HEAD_Y * 1.16 * 0.86
FX_FACTOR = HEAD_Y * 1.16 / 0.7
OBJECT_FIELDS = {'m_GameObject', 'm_Enabled', 'm_Script', 'm_Name'}
SPEC_KEEP = OBJECT_FIELDS | {'<enumName>k__BackingField', '<finalVisual>k__BackingField'}

def copy_spec(target, source, keep):
    for key in target:
        if key in keep:
            continue
        if key == 'Settings':
            for field in target['Settings']:
                if field != 'Identifier':
                    target['Settings'][field] = copy.deepcopy(source['Settings'][field])
        elif key in source:
            target[key] = copy.deepcopy(source[key])

def has_pointer(value):
    if isinstance(value, dict):
        return 'm_PathID' in value or any((has_pointer(v) for v in value.values()))
    if isinstance(value, list):
        return any((has_pointer(v) for v in value))
    return False

def copy_values(target, source):
    for key in target:
        if key in source and (not has_pointer(target[key])) and (not has_pointer(source[key])):
            target[key] = copy.deepcopy(source[key])

def patch_weapon_bundle(data, wrench_data):
    import UnityPy
    env, wrench = (UnityPy.load(bytes(data)), UnityPy.load(bytes(wrench_data)))
    geometry, images = build()
    wrench_view = next((o.read_typetree() for o in wrench.objects if o.type.name == 'MonoBehaviour' and 'wrenchFXs' in o.read_typetree()))
    wrench_trail = next((o.read_typetree() for o in wrench.objects if o.type.name == 'TrailRenderer'))
    names = {o.path_id: o.read_typetree()['m_Name'] for o in env.objects if o.type.name == 'GameObject'}
    done = {'mesh': 0, 'textures': 0, 'places': 0}
    for obj in env.objects:
        kind = obj.type.name
        if kind == 'Mesh':
            obj.save_typetree(unity_mesh(obj.read_typetree(), geometry))
            done['mesh'] += 1
        elif kind == 'Texture2D':
            texture = obj.read()
            suffix = texture.m_Name.rsplit('_', 1)[-1]
            if suffix in images:
                texture.set_image(images[suffix].convert('RGBA'), target_format=4, mipmap_count=1)
                texture.save()
                done['textures'] += 1
        elif kind == 'Transform':
            tree = obj.read_typetree()
            name = names.get(tree['m_GameObject']['m_PathID'], '')
            if name.startswith('WPN_'):
                tree.update({k: dict(v) for k, v in WRENCH_HOLD.items()})
            elif name == 'WrenchTrail':
                tree['m_LocalPosition'] = {'x': 0.0, 'y': TRAIL_HEIGHT, 'z': 0.0}
            else:
                continue
            obj.save_typetree(tree)
            done['places'] += 1
        elif kind == 'MonoBehaviour':
            tree = obj.read_typetree()
            if 'wrenchFXs' in tree:
                copy_values(tree, wrench_view)
                tree['wrenchFXs'] = [dict(fx) for fx in wrench_view['wrenchFXs']]
                for fx in tree['wrenchFXs']:
                    offset = fx['Fx']['PositionOffset']
                    fx['Fx']['PositionOffset'] = dict(offset, y=offset['y'] * FX_FACTOR)
                obj.save_typetree(tree)
        elif kind == 'TrailRenderer':
            tree = obj.read_typetree()
            copy_values(tree, wrench_trail)
            obj.save_typetree(tree)
    if done['mesh'] != 1 or done['textures'] != 4:
        raise SystemExit(f'marteau de Rivet : arme de Steeljaw inattendue {done}')
    data[:] = env.file.save(packer='lz4')
    return done

def patch_melee_db(data):
    import UnityPy
    env = UnityPy.load(bytes(data))
    specs = {o.peek_name(): o for o in env.objects if o.type.name == 'MonoBehaviour'}
    wrench = specs[WRENCH_SPEC].read_typetree()
    hammer_obj = specs[HAMMER_SPEC]
    if hammer_obj.path_id != STEELJAW_MELEE_SPEC:
        raise SystemExit('marteau de Rivet : fiche de Steeljaw inattendue')
    hammer = hammer_obj.read_typetree()
    copy_spec(hammer, wrench, SPEC_KEEP)
    hammer['<LocalizedNameKey>k__BackingField'] = {'_value': NAME_KEY, '_mode': 0}
    hammer['<LocalizedDescriptionKey>k__BackingField'] = {'_value': DESCRIPTION_KEY, '_mode': 0}
    hammer_obj.save_typetree(hammer)
    table_obj = specs['SimulationMeleeWeaponsTable']
    table = table_obj.read_typetree()
    rows = [d for d in table['Settings']['definitions'] if d['characterId'] == RIVET_CHARACTER]
    if len(rows) != 1:
        raise SystemExit('marteau de Rivet : table des armes de corps a corps inattendue')
    rows[0]['id'] = HAMMER_WEAPON_ID
    table_obj.save_typetree(table)
    data[:] = env.file.save(packer='lz4')
JUMP_TALENT = 'Q_Sandy_Imp2_MeleeJump_CompoundHeroImprovementSpec'
JUMP_NAME_KEY, JUMP_DESCRIPTION_KEY = ('UI.HERO_IMPROVEMENT.NAME.RIVET_SLAM', 'UI.HERO_IMPROVEMENT.DESC.RIVET_SLAM')

def patch_hero_specs(data):
    import UnityPy
    env = UnityPy.load(bytes(data))
    specs = {o.peek_name(): o for o in env.objects if o.type.name == 'MonoBehaviour'}
    ratchet = specs['Q_Ratchet_HeroSpec'].read_typetree()
    avatar_obj, jump_obj = (specs['HeroSpec_Avatar'], specs[JUMP_TALENT])
    avatar, jump = (avatar_obj.read_typetree(), jump_obj.read_typetree())
    copy_spec(avatar, ratchet, OBJECT_FIELDS)
    talents = ratchet['Settings']['TalentsInUnlockOrder']
    slam = {'Id': {'Value': jump['Settings']['Identifier']['Guid']['Value']}}
    avatar['Settings']['TalentsInUnlockOrder'] = [slam] + copy.deepcopy(talents[:5])
    avatar_obj.save_typetree(avatar)
    jump['<DisplayNameLocaKey>k__BackingField'] = {'_value': JUMP_NAME_KEY, '_mode': 0}
    jump['<DescriptionLocaKey>k__BackingField'] = {'_value': JUMP_DESCRIPTION_KEY, '_mode': 0}
    jump_obj.save_typetree(jump)
    data[:] = env.file.save(packer='lz4')
if __name__ == '__main__':
    geometry, images = build()
    print({k: v.shape for k, v in geometry.items()})
    print('hauteur', geometry['vertices'][:, 1].min(), geometry['vertices'][:, 1].max(), 'largeur Z', geometry['vertices'][:, 2].min(), geometry['vertices'][:, 2].max())
