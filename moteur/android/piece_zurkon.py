import math
import struct
SPRITE_SIZE = (268, 214)
OUTLINE = ((36.1, 103.1), (30.3, 92.7), (28.7, 87.1), (31.0, 84.0), (41.3, 79.3), (42.0, 57.0), (43.6, 52.6), (128.0, 4.0), (135.1, 1.1), (139.0, 2.0), (225.9, 53.1), (228.0, 59.0), (228.4, 74.6), (239.4, 81.6), (240.7, 84.0), (230.6, 101.7), (236.3, 100.8), (242.0, 100.6), (247.7, 101.6), (253.0, 103.8), (257.7, 107.0), (261.7, 111.1), (264.7, 116.0), (266.6, 121.4), (267.4, 127.1), (267.0, 132.8), (265.4, 138.3), (262.7, 143.3), (259.0, 147.7), (254.4, 151.2), (249.3, 153.6), (243.7, 155.0), (238.0, 155.0), (228.3, 152.9), (226.7, 160.7), (224.0, 164.0), (134.0, 213.0), (130.0, 212.0), (46.0, 163.0), (43.9, 161.1), (41.7, 153.6), (27.3, 156.7), (21.5, 156.0), (16.0, 154.0), (11.1, 150.9), (6.9, 146.9), (3.7, 142.0), (1.6, 136.6), (0.7, 130.8), (1.0, 125.0), (2.6, 119.4), (5.3, 114.2), (9.0, 109.7), (13.6, 106.1), (18.9, 103.6), (24.6, 102.3), (30.4, 102.1))
EDGE_PIXEL = (25, 140)
WIDTH = 1.6
THICKNESS = 0.2
SMOOTH_EDGE = math.radians(40)
VERTEX = struct.Struct('<8f')
CHANNELS = {0: (0, 0, 0, 3), 1: (0, 12, 0, 3), 4: (0, 24, 0, 2)}

def _area(points):
    return sum((x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(points, points[1:] + points[:1]))) / 2

def _inside(p, a, b, c):

    def side(u, v, w):
        return (v[0] - u[0]) * (w[1] - u[1]) - (v[1] - u[1]) * (w[0] - u[0])
    return side(a, b, p) >= 0 and side(b, c, p) >= 0 and (side(c, a, p) >= 0)

def triangulate(points):
    left = list(range(len(points)))
    triangles = []
    while len(left) > 3:
        for k, i in enumerate(left):
            a, b, c = (points[left[k - 1]], points[i], points[left[(k + 1) % len(left)]])
            if (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]) <= 0:
                continue
            if any((_inside(points[j], a, b, c) for j in left if j not in (left[k - 1], i, left[(k + 1) % len(left)]))):
                continue
            triangles.append((left[k - 1], i, left[(k + 1) % len(left)]))
            del left[k]
            break
        else:
            raise SystemExit('piece de Mme Zurkon : contour impossible a decouper')
    triangles.append(tuple(left))
    return triangles

def _facing(a, b, c, normal):
    u = [b[i] - a[i] for i in range(3)]
    v = [c[i] - a[i] for i in range(3)]
    cross = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
    return sum((cross[i] * normal[i] for i in range(3))) >= 0

def _normalised(x, y):
    length = math.hypot(x, y)
    return (x / length, y / length)

def coin(rect, atlas_size):
    width, height = SPRITE_SIZE
    scale = WIDTH / width
    atlas_width, atlas_height = atlas_size

    def uv(px, py):
        return ((rect[0] + px * rect[2] / width) / atlas_width, (rect[1] + (height - py) * rect[3] / height) / atlas_height)
    flat = [((x - width / 2) * scale, (height / 2 - y) * scale) for x, y in OUTLINE]
    pixels = list(OUTLINE)
    if _area(flat) < 0:
        flat.reverse()
        pixels.reverse()
    half = THICKNESS / 2
    vertices, indices = ([], [])

    def face(z, normal_z, mirrored):
        first = len(vertices)
        for (x, y), (px, py) in zip(flat, pixels):
            vertices.append((x, y, z, 0.0, 0.0, normal_z) + uv(width - px if mirrored else px, py))
        for a, b, c in triangulate(flat):
            corners = [vertices[first + i][:3] for i in (a, b, c)]
            if not _facing(*corners, (0, 0, normal_z)):
                b, c = (c, b)
            indices.extend((first + a, first + b, first + c))
    face(-half, -1.0, False)
    face(half, 1.0, True)
    count = len(flat)
    outward = []
    for i in range(count):
        (x0, y0), (x1, y1) = (flat[i], flat[(i + 1) % count])
        outward.append(_normalised(y1 - y0, x0 - x1))

    def corner_normal(side, corner):
        other = outward[(side - 1) % count] if corner == side else outward[(side + 1) % count]
        own = outward[side]
        if math.acos(max(-1.0, min(1.0, own[0] * other[0] + own[1] * other[1]))) < SMOOTH_EDGE:
            return _normalised(own[0] + other[0], own[1] + other[1])
        return own
    edge_uv = uv(*EDGE_PIXEL)
    for i in range(count):
        j = (i + 1) % count
        first = len(vertices)
        for point, corner, z in ((i, i, -half), (j, j, -half), (j, j, half), (i, i, half)):
            nx, ny = corner_normal(i, corner)
            vertices.append((flat[point][0], flat[point][1], z, nx, ny, 0.0) + edge_uv)
        normal = outward[i] + (0.0,)
        for a, b, c in ((0, 1, 2), (0, 2, 3)):
            corners = [vertices[first + k][:3] for k in (a, b, c)]
            if not _facing(*corners, normal):
                b, c = (c, b)
            indices.extend((first + a, first + b, first + c))
    xs = [v[0] for v in vertices]
    ys = [v[1] for v in vertices]
    centre = ((max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2, 0.0)
    extent = ((max(xs) - min(xs)) / 2, (max(ys) - min(ys)) / 2, half)
    return (b''.join((VERTEX.pack(*v) for v in vertices)), struct.pack(f'<{len(indices)}H', *indices), len(vertices), len(indices), (centre, extent))
