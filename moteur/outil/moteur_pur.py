import asyncio
import base64
import datetime
import gzip
import hashlib
import ipaddress
import secrets
import socket
import ssl
import zlib

def _length(n):
    if n < 128:
        return bytes([n])
    raw = n.to_bytes((n.bit_length() + 7) // 8, 'big')
    return bytes([128 | len(raw)]) + raw

def tlv(tag, content):
    return bytes([tag]) + _length(len(content)) + content

def seq(*items):
    return tlv(48, b''.join(items))

def integer(n):
    return tlv(2, n.to_bytes(n.bit_length() // 8 + 1, 'big'))

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
    return tlv(6, bytes(out))

def bits(data, unused=0):
    return tlv(3, bytes([unused]) + data)

def octets(data):
    return tlv(4, data)

def explicit(number, content):
    return tlv(160 + number, content)

def _time(moment):
    if moment.year < 2050:
        return tlv(23, moment.strftime('%y%m%d%H%M%SZ').encode())
    return tlv(24, moment.strftime('%Y%m%d%H%M%SZ').encode())

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
NULL = b'\x05\x00'
RSA = seq(oid('1.2.840.113549.1.1.1'), NULL)
SHA256_RSA = seq(oid('1.2.840.113549.1.1.11'), NULL)
SHA256_INFO = bytes.fromhex('3031300d060960864801650304020105000420')
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

    def public_der(self):
        return seq(integer(self.n), integer(self.e))

    def pem(self):
        der = seq(integer(0), integer(self.n), integer(self.e), integer(self.d), integer(self.p), integer(self.q), integer(self.dp), integer(self.dq), integer(self.qinv))
        return pem('RSA PRIVATE KEY', der)

    @classmethod
    def from_der(cls, der):
        _, content, _ = parse(der)
        fields = children(content)
        if len(fields) == 3 and fields[1][0] == 48:
            return cls.from_der(fields[2][1])
        numbers = [int.from_bytes(value, 'big') for _, value in fields]
        _, n, e, d, p, q = numbers[:6]
        return cls(n, e, d, p, q)

    def sign(self, data):
        size = (self.n.bit_length() + 7) // 8
        digest = SHA256_INFO + hashlib.sha256(data).digest()
        block = int.from_bytes(b'\x00\x01' + b'\xff' * (size - len(digest) - 3) + b'\x00' + digest, 'big')
        m1, m2 = (pow(block, self.dp, self.p), pow(block, self.dq, self.q))
        h = self.qinv * (m1 - m2) % self.p
        return (m2 + h * self.q).to_bytes(size, 'big')

def pem(label, der):
    body = base64.b64encode(der).decode()
    lines = '\n'.join((body[i:i + 64] for i in range(0, len(body), 64)))
    return f'-----BEGIN {label}-----\n{lines}\n-----END {label}-----\n'.encode()

def from_pem(data, label):
    text = data.decode() if isinstance(data, bytes) else data
    begin = f'-----BEGIN {label}-----'
    if begin not in text:
        return None
    body = text.split(begin, 1)[1].split(f'-----END {label}-----', 1)[0]
    return base64.b64decode(''.join(body.split()))

def _name(common, organization):
    return seq(tlv(49, seq(oid('2.5.4.3'), tlv(12, common.encode()))), tlv(49, seq(oid('2.5.4.10'), tlv(12, organization.encode()))))

def _extension(dotted, value, critical=False):
    return seq(oid(dotted), *([tlv(1, b'\xff')] if critical else []), octets(value))

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
            if parts[0][1] == oid('2.5.4.3')[2:]:
                return parts[1][1].decode()
    return None

class Authority:

    def __init__(self, folder, name):
        self.folder, self.name = (folder, name)
        self.contexts = {}
        both = (folder / 'mitmproxy-ca.pem').read_bytes()
        self.key = Key.from_der(from_pem(both, 'RSA PRIVATE KEY') or from_pem(both, 'PRIVATE KEY'))
        self.cert = from_pem(both, 'CERTIFICATE')
        self.subject = _name(name, name)
        leaf = folder / 'feuille-cle.pem'
        if not leaf.exists():
            leaf.write_bytes(Key.generate().pem())
        self.leaf_key = Key.from_der(from_pem(leaf.read_bytes(), 'RSA PRIVATE KEY'))
        self.leaves = folder / 'feuilles'
        self.leaves.mkdir(exist_ok=True)

    @staticmethod
    def create(folder, name):
        key = Key.generate()
        subject = _name(name, name)
        cert = _certificate(key, subject, key, subject, 3650, [_extension('2.5.29.19', seq(tlv(1, b'\xff')), critical=True), _extension('2.5.29.15', bits(b'\x86', 1), critical=True), _extension('2.5.29.14', octets(key_id(key)))])
        for old in folder.glob('mitmproxy-ca*'):
            old.unlink()
        (folder / 'mitmproxy-ca.pem').write_bytes(key.pem() + pem('CERTIFICATE', cert))
        (folder / 'mitmproxy-ca-cert.pem').write_bytes(pem('CERTIFICATE', cert))
        leaf = folder / 'feuille-cle.pem'
        if leaf.exists():
            leaf.unlink()

    def leaf(self, names, ips=()):
        alt = b''.join([tlv(130, n.encode()) for n in names] + [tlv(135, ipaddress.ip_address(i).packed) for i in ips])
        cert = _certificate(self.key, self.subject, self.leaf_key, _name(names[0], self.name), 365, [_extension('2.5.29.19', seq()), _extension('2.5.29.15', bits(b'\xa0', 5), critical=True), _extension('2.5.29.37', seq(oid('1.3.6.1.5.5.7.3.1'))), _extension('2.5.29.17', seq(alt)), _extension('2.5.29.35', seq(tlv(128, key_id(self.key)))), _extension('2.5.29.14', octets(key_id(self.leaf_key)))])
        path = self.leaves / (hashlib.sha1('|'.join([*names, *ips]).encode()).hexdigest() + '.pem')
        path.write_bytes(pem('CERTIFICATE', cert) + pem('CERTIFICATE', self.cert) + self.leaf_key.pem())
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
        asked = {}

        def by_name(ssl_object, name, _):
            if name:
                asked[id(ssl_object)] = asked['last'] = name.lower()
                ssl_object.context = self.context([name.lower()])
        context.sni_callback = by_name
        return (context, asked)

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
        if kind == 1 and ip.version == 4 or (kind == 28 and ip.version == 6):
            records.append(b'\xc0\x0c' + kind.to_bytes(2, 'big') + b'\x00\x01' + ttl.to_bytes(4, 'big') + len(ip.packed).to_bytes(2, 'big') + ip.packed)
    head = query[:2] + b'\x81\x80' + b'\x00\x01' + len(records).to_bytes(2, 'big') + b'\x00\x00\x00\x00'
    return head + query[12:end] + b''.join(records)

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
    if 'chunked' in (headers.get('transfer-encoding') or '').lower():
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
    length = headers.get('content-length')
    if length is not None:
        data = await reader.readexactly(int(length))
        return (data, data)
    if until_end:
        data = await reader.read()
        return (data, data)
    return (b'', b'')

async def _pipe(reader, writer):
    try:
        while True:
            data = await reader.read(65536)
            if not data:
                break
            writer.write(data)
            await writer.drain()
    except (OSError, asyncio.IncompleteReadError, ssl.SSLError):
        pass
    finally:
        try:
            writer.close()
        except Exception:
            pass

async def tunnel(reader, writer, host, port, first=b''):
    try:
        far_reader, far_writer = await asyncio.wait_for(asyncio.open_connection(host, port), 15)
    except (OSError, asyncio.TimeoutError):
        writer.close()
        return
    if first:
        far_writer.write(first)
    await asyncio.gather(_pipe(reader, far_writer), _pipe(far_reader, writer))

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
        self.recorder.client_connected(type('Client', (), {'peername': peer})())

    async def _secure(self, writer, context, host):
        try:
            await asyncio.wait_for(writer.start_tls(context), 20)
        except Exception as error:
            self.recorder.tls_refused(host, str(error) or type(error).__name__)
            writer.close()
            return False
        self.recorder.tls_ok(host)
        return True

    async def manual(self, reader, writer):
        self._connected(writer)
        try:
            head = await _head(reader)
        except (OSError, asyncio.IncompleteReadError, asyncio.LimitOverrunError):
            writer.close()
            return
        if not head:
            writer.close()
            return
        (method, target, *_), _ = _parse_head(head)
        if method.upper() != 'CONNECT':
            rest = target.split('://', 1)[-1]
            host_port, _, path = rest.partition('/')
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
        if await self._secure(writer, self.authority.context([host]), host):
            await self.relay(reader, writer, host, port)

    async def direct(self, reader, writer, context, asked):
        self._connected(writer)
        try:
            await asyncio.wait_for(writer.start_tls(context), 20)
        except Exception as error:
            self.recorder.tls_refused(asked.get('last', ''), str(error) or type(error).__name__)
            writer.close()
            return
        host = asked.pop(id(writer.get_extra_info('ssl_object')), '')
        if not host or not self.game(host):
            writer.close()
            return
        self.recorder.tls_ok(host)
        await self.relay(reader, writer, host, 443)

    async def relay(self, reader, writer, host, port):
        far = None
        try:
            while not self.stopped.is_set():
                head = await _head(reader)
                if not head:
                    break
                (method, path, *_), headers = _parse_head(head)
                raw, body = await _body(reader, headers)
                request = Request(method, path, host, port, headers, _decoded(headers, body))
                flow = Flow(request)
                self.recorder.request(flow)
                target = (request.host, request.port)
                if far is None or far[0] != target:
                    if far:
                        far[2].close()
                    far_reader, far_writer = await asyncio.wait_for(asyncio.open_connection(request.host, request.port, ssl=self.upstream, server_hostname=request.host_header.split(':')[0]), 20)
                    far = (target, far_reader, far_writer)
                _, far_reader, far_writer = far
                far_writer.write(head + raw)
                await far_writer.drain()
                while True:
                    answer = await _head(far_reader)
                    if not answer:
                        raise ConnectionError('le serveur a fermé')
                    (_, status, *_), answer_headers = _parse_head(answer)
                    status = int(status)
                    if 100 <= status < 200 and status != 101:
                        writer.write(answer)
                        await writer.drain()
                        continue
                    break
                bodiless = method.upper() == 'HEAD' or status in (101, 204, 304)
                closing = 'close' in (answer_headers.get('connection') or '').lower()
                answer_raw, answer_body = (b'', b'') if bodiless else await _body(far_reader, answer_headers, until_end=closing or (answer_headers.get('content-length') is None and 'chunked' not in (answer_headers.get('transfer-encoding') or '').lower()))
                writer.write(answer + answer_raw)
                await writer.drain()
                flow.response = Response(status, answer_headers, _decoded(answer_headers, answer_body))
                try:
                    self.recorder.response(flow)
                except Exception as error:
                    print(f'copie : {error!r}', flush=True)
                if status == 101:
                    await asyncio.gather(_pipe(reader, far_writer), _pipe(far_reader, writer))
                    return
                if closing or 'close' in (headers.get('connection') or '').lower():
                    break
        except (OSError, asyncio.IncompleteReadError, asyncio.LimitOverrunError, asyncio.TimeoutError, ssl.SSLError, ValueError, ConnectionError):
            pass
        finally:
            if far:
                far[2].close()
            writer.close()

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
        self.servers.append(await asyncio.start_server(self._tracked(self.manual), '0.0.0.0', proxy_port, limit=1 << 20))
        if https_port:
            context, asked = self.authority.server_context(fallback_host)
            self.servers.append(await asyncio.start_server(self._tracked(lambda r, w: self.direct(r, w, context, asked)), '0.0.0.0', https_port, limit=1 << 20))

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
            except asyncio.TimeoutError:
                pass
        await asyncio.sleep(0.2)

def resolve(name, kind):
    family = socket.AF_INET if kind == 1 else socket.AF_INET6
    try:
        found = socket.getaddrinfo(name, None, family=family, type=socket.SOCK_STREAM)
    except OSError:
        return []
    return list(dict.fromkeys((item[4][0] for item in found)))

def make_authority(folder, name):
    if not (folder / 'mitmproxy-ca.pem').exists():
        Authority.create(folder, name)
    return Authority(folder, name)

def authority_name(folder):
    try:
        return common_name(from_pem((folder / 'mitmproxy-ca-cert.pem').read_bytes(), 'CERTIFICATE'))
    except (OSError, ValueError, IndexError, TypeError):
        return None

def dns_context(authority, name, address):
    return authority.context([name], [address], alpn=())

def new_authority(folder, name):
    Authority.create(folder, name)
