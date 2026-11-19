def decompress(source, uncompressed_size=-1, return_bytearray=False, dict=None):
    source = memoryview(source)
    if uncompressed_size < 0:
        uncompressed_size = int.from_bytes(source[:4], 'little')
        source = source[4:]
    out = bytearray()
    i, end = (0, len(source))
    while i < end:
        token = source[i]
        i += 1
        count = token >> 4
        if count == 15:
            while True:
                extra = source[i]
                i += 1
                count += extra
                if extra != 255:
                    break
        out += source[i:i + count]
        i += count
        if i >= end:
            break
        distance = source[i] | source[i + 1] << 8
        i += 2
        count = token & 15
        if count == 15:
            while True:
                extra = source[i]
                i += 1
                count += extra
                if extra != 255:
                    break
        count += 4
        start = len(out) - distance
        if distance <= 0 or start < 0:
            raise ValueError('bloc LZ4 abime')
        if distance >= count:
            out += out[start:start + count]
        else:
            out += (out[start:] * (count // distance + 1))[:count]
    if len(out) != uncompressed_size:
        raise ValueError('bloc LZ4 de taille inattendue')
    return out if return_bytearray else bytes(out)

def compress(source, mode='default', acceleration=1, compression=0, store_size=True, return_bytearray=False, dict=None):
    source = bytes(source)
    size = len(source)
    out = bytearray(size.to_bytes(4, 'little') if store_size else b'')
    if size < 15:
        out.append(size << 4)
    else:
        out.append(240)
        rest = size - 15
        out += b'\xff' * (rest // 255)
        out.append(rest % 255)
    out += source
    return out if return_bytearray else bytes(out)
