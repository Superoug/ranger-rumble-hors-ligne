import datetime
import hashlib
import os
import struct
import zipfile
try:
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding, rsa
    from cryptography.hazmat.primitives.serialization import pkcs12
    from cryptography.x509.oid import NameOID
except ImportError:
    x509 = None
CHUNK = 1 << 20
RSA_PKCS1_SHA256 = 259
V2_BLOCK_ID = 1896449818
MAGIC = b'APK Sig Block 42'
ALIGNMENT_EXTRA = 55605

class AlignedZip:

    def __init__(self, path):
        self.zip = zipfile.ZipFile(path, 'w', allowZip64=True)

    def add(self, name, content, compress):
        info = zipfile.ZipInfo(name, date_time=(1981, 1, 1, 1, 1, 0))
        info.compress_type = compress
        if compress == zipfile.ZIP_STORED:
            alignment = 4096 if name.endswith('.so') else 4
            offset = self.zip.fp.tell() + 30 + len(name.encode('utf-8'))
            pad = -(offset + 6) % alignment
            info.extra = struct.pack('<HHH', ALIGNMENT_EXTRA, 2 + pad, alignment) + bytes(pad)
        self.zip.writestr(info, content)

    def close(self):
        self.zip.close()

def load_or_make_key(folder, name='cle_apk.p12'):
    path = os.path.join(folder, name)
    if os.path.exists(path):
        key, cert, _ = pkcs12.load_key_and_certificates(open(path, 'rb').read(), None)
        return (key, cert)
    os.makedirs(folder, exist_ok=True)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'Ranger Rumble hors ligne')])
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = x509.CertificateBuilder().subject_name(subject).issuer_name(subject).public_key(key.public_key()).serial_number(x509.random_serial_number()).not_valid_before(now - datetime.timedelta(days=1)).not_valid_after(now + datetime.timedelta(days=365 * 50)).sign(key, hashes.SHA256())
    blob = pkcs12.serialize_key_and_certificates(b'rr', key, cert, None, serialization.NoEncryption())
    with open(path, 'wb') as handle:
        handle.write(blob)
    return (key, cert)

def load_key(path, password):
    key, cert, _ = pkcs12.load_key_and_certificates(open(path, 'rb').read(), password.encode() if password else None)
    return (key, cert)

def _prefixed(blob):
    return struct.pack('<I', len(blob)) + blob

def _sequence(blobs):
    return _prefixed(b''.join((_prefixed(b) for b in blobs)))

def _find_end(handle, size):
    handle.seek(max(0, size - 65557))
    tail = handle.read()
    position = tail.rfind(b'PK\x05\x06')
    if position < 0:
        raise SystemExit('fin de zip introuvable')
    eocd = tail[position:]
    cd_size, cd_offset = struct.unpack_from('<II', eocd, 12)
    return (size - len(tail) + position, eocd, cd_offset, cd_size)

def _digest(handle, sections):
    digests = []
    for start, length in sections:
        handle.seek(start)
        while length > 0:
            chunk = handle.read(min(CHUNK, length))
            length -= len(chunk)
            digests.append(hashlib.sha256(b'\xa5' + struct.pack('<I', len(chunk)) + chunk).digest())
    return digests

def sign(path, key, cert):
    size = os.path.getsize(path)
    with open(path, 'rb') as handle:
        eocd_offset, eocd, cd_offset, cd_size = _find_end(handle, size)
        if cd_offset + cd_size != eocd_offset:
            raise SystemExit('zip inattendu (deja signe ?)')
        chunks = _digest(handle, [(0, cd_offset), (cd_offset, cd_size)])
        chunks += [hashlib.sha256(b'\xa5' + struct.pack('<I', len(eocd)) + eocd).digest()]
        handle.seek(0)
    top = hashlib.sha256(b'Z' + struct.pack('<I', len(chunks)) + b''.join(chunks)).digest()
    certificate = cert.public_bytes(serialization.Encoding.DER)
    signed_data = _sequence([struct.pack('<I', RSA_PKCS1_SHA256) + _prefixed(top)]) + _sequence([certificate]) + _prefixed(b'')
    signature = key.sign(signed_data, padding.PKCS1v15(), hashes.SHA256())
    public_key = key.public_key().public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
    signer = _prefixed(signed_data) + _sequence([struct.pack('<I', RSA_PKCS1_SHA256) + _prefixed(signature)]) + _prefixed(public_key)
    v2 = _sequence([signer])
    pair = struct.pack('<QI', 4 + len(v2), V2_BLOCK_ID) + v2
    block_size = len(pair) + 8 + 16
    block = struct.pack('<Q', block_size) + pair + struct.pack('<Q', block_size) + MAGIC
    new_eocd = eocd[:16] + struct.pack('<I', cd_offset + len(block)) + eocd[20:]
    tmp = path + '.tmp'
    with open(path, 'rb') as source, open(tmp, 'wb') as target:
        remaining = cd_offset
        while remaining:
            chunk = source.read(min(CHUNK * 8, remaining))
            target.write(chunk)
            remaining -= len(chunk)
        target.write(block)
        target.write(source.read(cd_size))
        target.write(new_eocd)
    os.replace(tmp, path)
