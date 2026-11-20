import asyncio
import base64
import datetime
import gzip
import hashlib
import ipaddress
import secrets
import socket
import ssl
import types
import weakref
import zlib
BOOLEAN, INTEGER, BIT_STRING, OCTET_STRING, OBJECT_ID, UTF8_STRING = (1, 2, 3, 4, 6, 12)
UTC_TIME, GENERALIZED_TIME, SEQUENCE, SET = (23, 24, 48, 49)
NULL = b'\x05\x00'
TRUE = bytes([BOOLEAN, 1, 255])

def _length(n):
    if n < 128:
        return bytes([n])
    raw = n.to_bytes((n.bit_length() + 7) // 8, 'big')
    return bytes([128 | len(raw)]) + raw

def tlv(tag, content):
    return bytes([tag]) + _length(len(content)) + content

def seq(*items):
    return tlv(SEQUENCE, b''.join(items))

def integer(n):
    return tlv(INTEGER, n.to_bytes(n.bit_length() // 8 + 1, 'big'))

def oid(dotted):
    parts = [int(p) for p in dotted.split('.')]
    out = bytearray([parts[0] * 40 + parts[1]])
    for part in parts[2:]:
        chunk = [part & 127]
        part >>= 7
        while part:
            chunk.append(128 | part & 127)
            part >>= 7
        out += bytes(reversed(chunk))
    return tlv(OBJECT_ID, bytes(out))

def bits(data, unused=0):
    return tlv(BIT_STRING, bytes([unused]) + data)

def octets(data):
    return tlv(OCTET_STRING, data)

def explicit(number, content):
    return tlv(160 + number, content)

def _time(moment):
    if moment.year < 2050:
        return tlv(UTC_TIME, moment.strftime('%y%m%d%H%M%SZ').encode())
    return tlv(GENERALIZED_TIME, moment.strftime('%Y%m%d%H%M%SZ').encode())

def parse(data, at=0):
    tag = data[at]
    size = data[at + 1]
    at += 2
    if size & 128:
        count = size & 127
        size = int.from_bytes(data[at:at + count], 'big')
        at += count
    return (tag, data[at:at + size], at + size)

def children(content):
    out, at = ([], 0)
    while at < len(content):
        tag, inner, at = parse(content, at)
        out.append((tag, inner))
    return out
RSA = seq(oid('1.2.840.113549.1.1.1'), NULL)
SHA256_RSA = seq(oid('1.2.840.113549.1.1.11'), NULL)
SHA256_INFO = bytes.fromhex('3031300d060960864801650304020105000420')
COMMON_NAME = oid('2.5.4.3')
ORGANIZATION = oid('2.5.4.10')
BASIC_CONSTRAINTS = '2.5.29.19'
KEY_USAGE = '2.5.29.15'
EXTENDED_KEY_USAGE = '2.5.29.37'
SUBJECT_ALT_NAME = '2.5.29.17'
SUBJECT_KEY_ID = '2.5.29.14'
AUTHORITY_KEY_ID = '2.5.29.35'
SERVER_AUTH = oid('1.3.6.1.5.5.7.3.1')
_SMALL = [p for p in range(3, 2000, 2) if all((p % d for d in range(3, int(p ** 0.5) + 1, 2)))]

def _probable_prime(n, rounds=24):
    if any((n % p == 0 for p in _SMALL)):
        return n in _SMALL
    d, s = (n - 1, 0)
    while not d & 1:
        d >>= 1
        s += 1
    for _ in range(rounds):
        x = pow(secrets.randbelow(n - 3) + 2, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True

def _prime(bits_count):
    while True:
        n = secrets.randbits(bits_count) | 3 << bits_count - 2 | 1
        if _probable_prime(n):
            return n

class Key:

    def __init__(self, n, e, d, p, q):
        self.n, self.e, self.d, self.p, self.q = (n, e, d, p, q)
        self.dp, self.dq, self.qinv = (d % (p - 1), d % (q - 1), pow(q, -1, p))

    @classmethod
    def generate(cls, size=2048):
        e = 65537
        while True:
            p, q = (_prime(size // 2), _prime(size // 2))
            if p == q:
                continue
            phi = (p - 1) * (q - 1)
            if phi % e:
                n = p * q
                if n.bit_length() == size:
                    return cls(n, e, pow(e, -1, phi), max(p, q), min(p, q))

    @classmethod
    def from_der(cls, der):
        _, content, _ = parse(der)
        fields = children(content)
        if len(fields) == 3 and fields[1][0] == SEQUENCE:
            return cls.from_der(fields[2][1])
        _, n, e, d, p, q = [int.from_bytes(value, 'big') for _, value in fields][:6]
        return cls(n, e, d, p, q)

    def public_der(self):
        return seq(integer(self.n), integer(self.e))

    def private_pem(self):
        der = seq(integer(0), integer(self.n), integer(self.e), integer(self.d), integer(self.p), integer(self.q), integer(self.dp), integer(self.dq), integer(self.qinv))
        return pem_encode('RSA PRIVATE KEY', der)

    def sign(self, data):
        size = (self.n.bit_length() + 7) // 8
        digest = SHA256_INFO + hashlib.sha256(data).digest()
        block = int.from_bytes(b'\x00\x01' + b'\xff' * (size - len(digest) - 3) + b'\x00' + digest, 'big')
        m1, m2 = (pow(block, self.dp, self.p), pow(block, self.dq, self.q))
        h = self.qinv * (m1 - m2) % self.p
        return (m2 + h * self.q).to_bytes(size, 'big')

def pem_encode(label, der):
    body = base64.b64encode(der).decode()
    lines = '\n'.join((body[i:i + 64] for i in range(0, len(body), 64)))
    return f'-----BEGIN {label}-----\n{lines}\n-----END {label}-----\n'.encode()

def pem_decode(data, label):
    text = data.decode() if isinstance(data, bytes) else data
    begin = f'-----BEGIN {label}-----'
    if begin not in text:
        return None
    body = text.split(begin, 1)[1].split(f'-----END {label}-----', 1)[0]
    return base64.b64decode(''.join(body.split()))

def _name(common, organization):
    return seq(tlv(SET, seq(COMMON_NAME, tlv(UTF8_STRING, common.encode()))), tlv(SET, seq(ORGANIZATION, tlv(UTF8_STRING, organization.encode()))))

def _extension(dotted, value, critical=False):
    return seq(oid(dotted), *([TRUE] if critical else []), octets(value))

def _certificate(issuer_key, issuer_name, subject_key, subject_name, days, extensions):
    now = datetime.datetime.now(datetime.timezone.utc)
    tbs = seq(explicit(0, integer(2)), integer(secrets.randbits(63) | 1), SHA256_RSA, issuer_name, seq(_time(now - datetime.timedelta(days=2)), _time(now + datetime.timedelta(days=days))), subject_name, seq(RSA, bits(subject_key.public_der())), explicit(3, seq(*extensions)))
    return seq(tbs, SHA256_RSA, bits(issuer_key.sign(tbs)))

def key_id(key):
    return hashlib.sha1(key.public_der()).digest()

def common_name(cert_der):
    _, cert, _ = parse(cert_der)
    _, tbs, _ = parse(cert)
    fields = children(tbs)
    subject = fields[5][1] if fields[0][0] == 160 else fields[4][1]
    for _, rdn in children(subject):
        for _, attribute in children(rdn):
            parts = children(attribute)
            if parts[0][1] == COMMON_NAME[2:]:
                return parts[1][1].decode()
    return None

class Authority:

    def __init__(self, folder, name):
        self.folder, self.name = (folder, name)
        self.contexts = {}
        both = (folder / 'mitmproxy-ca.pem').read_bytes()
        self.key = Key.from_der(pem_decode(both, 'RSA PRIVATE KEY') or pem_decode(both, 'PRIVATE KEY'))
        self.cert = pem_decode(both, 'CERTIFICATE')
        self.subject = _name(name, name)
        leaf = folder / 'feuille-cle.pem'
        if not leaf.exists():
            leaf.write_bytes(Key.generate().private_pem())
        self.leaf_key = Key.from_der(pem_decode(leaf.read_bytes(), 'RSA PRIVATE KEY'))
        self.leaves = folder / 'feuilles'
        self.leaves.mkdir(exist_ok=True)

    @staticmethod
    def create(folder, name):
        key = Key.generate()
        subject = _name(name, name)
        cert = _certificate(key, subject, key, subject, 3650, [_extension(BASIC_CONSTRAINTS, seq(TRUE), critical=True), _extension(KEY_USAGE, bits(b'\x86', 1), critical=True), _extension(SUBJECT_KEY_ID, octets(key_id(key)))])
        for old in folder.glob('mitmproxy-ca*'):
            old.unlink()
        (folder / 'mitmproxy-ca.pem').write_bytes(key.private_pem() + pem_encode('CERTIFICATE', cert))
        (folder / 'mitmproxy-ca-cert.pem').write_bytes(pem_encode('CERTIFICATE', cert))
        (folder / 'feuille-cle.pem').unlink(missing_ok=True)

    def leaf(self, names, ips=()):
        alt = b''.join([tlv(130, n.encode()) for n in names] + [tlv(135, ipaddress.ip_address(i).packed) for i in ips])
        cert = _certificate(self.key, self.subject, self.leaf_key, _name(names[0], self.name), 365, [_extension(BASIC_CONSTRAINTS, seq()), _extension(KEY_USAGE, bits(b'\xa0', 5), critical=True), _extension(EXTENDED_KEY_USAGE, seq(SERVER_AUTH)), _extension(SUBJECT_ALT_NAME, seq(alt)), _extension(AUTHORITY_KEY_ID, seq(tlv(128, key_id(self.key)))), _extension(SUBJECT_KEY_ID, octets(key_id(self.leaf_key)))])
        path = self.leaves / (hashlib.sha1('|'.join([*names, *ips]).encode()).hexdigest() + '.pem')
        path.write_bytes(pem_encode('CERTIFICATE', cert) + pem_encode('CERTIFICATE', self.cert) + self.leaf_key.private_pem())
        return path

    def context(self, names, ips=(), alpn=('http/1.1',)):
        index = (tuple(names), tuple(ips))
        if index not in self.contexts:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.minimum_version = ssl.TLSVersion.TLSv1_2
            context.load_cert_chain(str(self.leaf(list(names), ips)))
            if alpn:
                context.set_alpn_protocols(list(alpn))
            self.contexts[index] = context
        return self.contexts[index]

    def server_context(self, fallback):
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(str(self.leaf([fallback])))
        context.set_alpn_protocols(['http/1.1'])
        asked = AskedNames()

        def by_name(ssl_object, name, _):
            if name:
                asked.add(ssl_object, name.lower())
                ssl_object.context = self.context([name.lower()])
        context.sni_callback = by_name
        return (context, asked)

class AskedNames:

    def __init__(self):
        self.by_object = weakref.WeakKeyDictionary()
        self.last = ''

    def add(self, ssl_object, name):
        self.by_object[ssl_object] = self.last = name

    def pop(self, ssl_object):
        return self.by_object.pop(ssl_object, '') if ssl_object is not None else ''
DNS_A, DNS_AAAA = (1, 28)

def dns_question(query):
    labels, at = ([], 12)
    while query[at]:
        size = query[at]
        labels.append(query[at + 1:at + 1 + size].decode('ascii', 'replace'))
        at += 1 + size
    kind = int.from_bytes(query[at + 1:at + 3], 'big')
    return ('.'.join(labels).lower(), kind, at + 5)

def dns_reply(query, addresses):
    _, kind, end = dns_question(query)
    records = []
    for address, ttl in addresses:
        ip = ipaddress.ip_address(address.split('%')[0])
        if kind == DNS_A and ip.version == 4 or (kind == DNS_AAAA and ip.version == 6):
            records.append(b'\xc0\x0c' + kind.to_bytes(2, 'big') + b'\x00\x01' + ttl.to_bytes(4, 'big') + len(ip.packed).to_bytes(2, 'big') + ip.packed)
    head = query[:2] + b'\x81\x80' + b'\x00\x01' + len(records).to_bytes(2, 'big') + b'\x00\x00\x00\x00'
    return head + query[12:end] + b''.join(records)

def resolve(name, kind):
    family = socket.AF_INET if kind == DNS_A else socket.AF_INET6
    try:
        found = socket.getaddrinfo(name, None, family=family, type=socket.SOCK_STREAM)
    except OSError:
        return []
    return list(dict.fromkeys((item[4][0] for item in found)))

class Headers:

    def __init__(self, pairs):
        self.pairs = pairs

    def get(self, name, default=None):
        name = name.lower()
        return next((value for key, value in self.pairs if key.lower() == name), default)

    def items(self):
        return list(self.pairs)

    def __contains__(self, name):
        return self.get(name) is not None

    def mentions(self, name, word):
        return word in (self.get(name) or '').lower()

class Request:

    def __init__(self, method, path, host, port, headers, content):
        self.method, self.path, self.host, self.port = (method, path, host, port)
        self.headers, self.content = (headers, content)
        self.host_header = headers.get('host', host)
        self.pretty_host = host

    @property
    def url(self):
        return f'https://{self.host}:{self.port}{self.path}'

    def copy(self):
        twin = Request(self.method, self.path, self.host, self.port, Headers(self.headers.items()), self.content)
        twin.host_header = self.host_header
        return twin

class Response:

    def __init__(self, status_code, headers, content):
        self.status_code, self.headers, self.content = (status_code, headers, content)

class Flow:

    def __init__(self, request):
        self.request, self.response, self.metadata = (request, None, {})

def _decoded(headers, body):
    coding = (headers.get('content-encoding') or '').lower()
    try:
        if coding == 'gzip':
            return gzip.decompress(body)
        if coding == 'deflate':
            try:
                return zlib.decompress(body)
            except zlib.error:
                return zlib.decompress(body, -15)
    except (OSError, EOFError, zlib.error):
        pass
    return body

async def _head(reader):
    try:
        return await reader.readuntil(b'\r\n\r\n')
    except asyncio.IncompleteReadError as end:
        if end.partial.strip():
            raise
        return b''

def _parse_head(head):
    lines = head.decode('latin-1').split('\r\n')
    first = lines[0].split(' ', 2)
    pairs = []
    for line in lines[1:]:
        if ':' in line:
            key, value = line.split(':', 1)
            pairs.append((key.strip(), value.strip()))
    return (first, Headers(pairs))

async def _body(reader, headers, until_end=False):
    if headers.mentions('transfer-encoding', 'chunked'):
        return await _chunked_body(reader)
    length = headers.get('content-length')
    if length is not None:
        data = await reader.readexactly(int(length))
        return (data, data)
    if until_end:
        data = await reader.read()
        return (data, data)
    return (b'', b'')

async def _chunked_body(reader):
    raw, body = (bytearray(), bytearray())
    while True:
        line = await reader.readuntil(b'\r\n')
        raw += line
        size = int(line.split(b';')[0].strip() or b'0', 16)
        if size == 0:
            while True:
                line = await reader.readuntil(b'\r\n')
                raw += line
                if line == b'\r\n':
                    return (bytes(raw), bytes(body))
        chunk = await reader.readexactly(size + 2)
        raw += chunk
        body += chunk[:-2]

def _close(writer):
    try:
        writer.close()
    except (OSError, RuntimeError):
        pass

async def _pipe(reader, writer):
    try:
        while (data := (await reader.read(65536))):
            writer.write(data)
            await writer.drain()
    except OSError:
        pass
    finally:
        _close(writer)

async def _pipe_both(reader, writer, far_reader, far_writer):
    await asyncio.gather(_pipe(reader, far_writer), _pipe(far_reader, writer))

async def tunnel(reader, writer, host, port, first=b''):
    try:
        far_reader, far_writer = await asyncio.wait_for(asyncio.open_connection(host, port), 15)
    except (OSError, TimeoutError):
        writer.close()
        return
    if first:
        far_writer.write(first)
    await _pipe_both(reader, writer, far_reader, far_writer)

class Upstream:

    def __init__(self, context):
        self.context = context
        self.target = None
        self.reader = self.writer = None

    async def to(self, host, port, server_name):
        if self.target != (host, port):
            self.close()
            self.reader, self.writer = await asyncio.wait_for(asyncio.open_connection(host, port, ssl=self.context, server_hostname=server_name), 20)
            self.target = (host, port)
        return (self.reader, self.writer)

    def close(self):
        if self.writer is not None:
            self.writer.close()
        self.target = None
        self.reader = self.writer = None

async def _final_answer_head(far_reader, writer):
    while True:
        answer = await _head(far_reader)
        if not answer:
            raise ConnectionError('the server closed')
        (_, status, *_), headers = _parse_head(answer)
        status = int(status)
        if not 100 <= status < 200 or status == 101:
            return (answer, status, headers)
        writer.write(answer)
        await writer.drain()
READ_LIMIT = 1 << 20
RELAY_ERRORS = (OSError, asyncio.IncompleteReadError, asyncio.LimitOverrunError, ValueError)

class Proxy:

    def __init__(self, authority, recorder, game, insecure_upstream=False):
        self.authority, self.recorder, self.game = (authority, recorder, game)
        self.upstream = ssl._create_unverified_context() if insecure_upstream else ssl.create_default_context()
        self.servers = []
        self.tasks = set()
        self.stopped = asyncio.Event()

    def shutdown(self):
        self.stopped.set()

    def _connected(self, writer):
        peer = writer.get_extra_info('peername') or ('?',)
        self.recorder.client_connected(types.SimpleNamespace(peername=peer))

    async def _start_tls(self, writer, context, host_of):
        try:
            await asyncio.wait_for(writer.start_tls(context), 20)
        except OSError as error:
            self.recorder.tls_refused(host_of(), str(error) or type(error).__name__)
            writer.close()
            return False
        return True

    async def manual(self, reader, writer):
        self._connected(writer)
        try:
            head = await _head(reader)
        except (OSError, asyncio.IncompleteReadError, asyncio.LimitOverrunError):
            head = b''
        if not head:
            writer.close()
            return
        (method, target, *_), _ = _parse_head(head)
        if method.upper() != 'CONNECT':
            host_port, _, path = target.split('://', 1)[-1].partition('/')
            host, _, port = host_port.partition(':')
            first = head.replace(target.encode('latin-1'), ('/' + path).encode('latin-1'), 1)
            await tunnel(reader, writer, host, int(port or 80), first)
            return
        host, _, port = target.rpartition(':')
        host, port = (host.strip('[]').lower(), int(port or 443))
        writer.write(b'HTTP/1.1 200 Connection Established\r\n\r\n')
        await writer.drain()
        if not self.game(host):
            await tunnel(reader, writer, host, port)
            return
        if await self._start_tls(writer, self.authority.context([host]), lambda: host):
            self.recorder.tls_ok(host)
            await self.relay(reader, writer, host, port)

    async def direct(self, reader, writer, context, asked):
        self._connected(writer)
        if not await self._start_tls(writer, context, lambda: asked.last):
            return
        ssl_object = writer.get_extra_info('ssl_object')
        host = asked.pop(ssl_object)
        if not host or not self.game(host):
            writer.close()
            return
        self.recorder.tls_ok(host)
        await self.relay(reader, writer, host, 443)

    async def relay(self, reader, writer, host, port):
        upstream = Upstream(self.upstream)
        try:
            while not self.stopped.is_set():
                head = await _head(reader)
                if not head:
                    break
                (method, path, *_), headers = _parse_head(head)
                raw, body = await _body(reader, headers)
                flow = Flow(Request(method, path, host, port, headers, _decoded(headers, body)))
                self.recorder.request(flow)
                request = flow.request
                far_reader, far_writer = await upstream.to(request.host, request.port, request.host_header.split(':')[0])
                far_writer.write(head + raw)
                await far_writer.drain()
                answer, status, answer_headers = await _final_answer_head(far_reader, writer)
                closing = answer_headers.mentions('connection', 'close')
                if method.upper() == 'HEAD' or status in (101, 204, 304):
                    answer_raw = answer_body = b''
                else:
                    framed = answer_headers.get('content-length') is not None or answer_headers.mentions('transfer-encoding', 'chunked')
                    answer_raw, answer_body = await _body(far_reader, answer_headers, until_end=closing or not framed)
                writer.write(answer + answer_raw)
                await writer.drain()
                flow.response = Response(status, answer_headers, _decoded(answer_headers, answer_body))
                self._record(flow)
                if status == 101:
                    await _pipe_both(reader, writer, far_reader, far_writer)
                    return
                if closing or headers.mentions('connection', 'close'):
                    break
        except RELAY_ERRORS:
            pass
        finally:
            upstream.close()
            writer.close()

    def _record(self, flow):
        try:
            self.recorder.response(flow)
        except Exception as error:
            print(f'copie : {error!r}', flush=True)

    def _tracked(self, handler):

        async def run(reader, writer):
            task = asyncio.current_task()
            self.tasks.add(task)
            try:
                await handler(reader, writer)
            finally:
                self.tasks.discard(task)
                writer.close()
        return run

    async def start(self, proxy_port, https_port=None, fallback_host='obb.cloud'):
        try:
            self.servers.append(await asyncio.start_server(self._tracked(self.manual), '0.0.0.0', proxy_port, limit=READ_LIMIT))
            if https_port:
                context, asked = self.authority.server_context(fallback_host)
                self.servers.append(await asyncio.start_server(self._tracked(lambda r, w: self.direct(r, w, context, asked)), '0.0.0.0', https_port, limit=READ_LIMIT))
        except BaseException:
            for server in self.servers:
                server.close()
            raise

    async def wait(self):
        await self.stopped.wait()
        for server in self.servers:
            server.close()
        for task in list(self.tasks):
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)
        for server in self.servers:
            try:
                await asyncio.wait_for(server.wait_closed(), 3)
            except TimeoutError:
                pass
        await asyncio.sleep(0.2)

def make_authority(folder, name):
    if not (folder / 'mitmproxy-ca.pem').exists():
        Authority.create(folder, name)
    return Authority(folder, name)

def authority_name(folder):
    try:
        return common_name(pem_decode((folder / 'mitmproxy-ca-cert.pem').read_bytes(), 'CERTIFICATE'))
    except (OSError, ValueError, IndexError, TypeError):
        return None

def dns_context(authority, name, address):
    return authority.context([name], [address], alpn=())

def new_authority(folder, name):
    Authority.create(folder, name)
