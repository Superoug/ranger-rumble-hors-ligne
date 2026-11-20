import re
import struct
TEXT_DELTA = 16384
CONDITIONS = {'eq': 0, 'ne': 1, 'hs': 2, 'lo': 3, 'ge': 10, 'lt': 11, 'gt': 12, 'le': 13}

def word(value):
    return struct.pack('<I', value & 4294967295)

def bl(source, target):
    return word(2483027968 | target - source >> 2 & 67108863)

def b(source, target):
    return word(335544320 | target - source >> 2 & 67108863)

def b_cond(condition, source, target):
    return word(1409286144 | (target - source >> 2 & 524287) << 5 | CONDITIONS[condition])

def mov_w(destination, source):
    return word(704644064 | source << 16 | destination)

def mov_x_zero(destination):
    return word(2854159328 | destination)

def movz_w(destination, value):
    return word(1384120320 | value << 5 | destination)

def ldr_x(destination, base, offset):
    return word(4181721088 | offset // 8 << 10 | base << 5 | destination)

def ldr_w(destination, base, offset):
    return word(3107979264 | offset // 4 << 10 | base << 5 | destination)

def str_x(source, base, offset):
    return word(4177526784 | offset // 8 << 10 | base << 5 | source)

def stp_x_pre(first, second, base, offset):
    return word(2843738112 | (offset // 8 & 127) << 15 | second << 10 | base << 5 | first)

def stp_x(first, second, base, offset):
    return word(2835349504 | (offset // 8 & 127) << 15 | second << 10 | base << 5 | first)

def ldp_x_post(first, second, base, offset):
    return word(2831155200 | (offset // 8 & 127) << 15 | second << 10 | base << 5 | first)

def ldp_x(first, second, base, offset):
    return word(2839543808 | (offset // 8 & 127) << 15 | second << 10 | base << 5 | first)

def cmp_w(first, second):
    return word(1795162143 | second << 16 | first << 5)

def cmp_w_imm(register, value):
    return word(1895825439 | value << 10 | register << 5)

def cmp_x_imm(register, value):
    return word(4043309087 | value << 10 | register << 5)

def movz_x(destination, value):
    return word(3531603968 | value << 5 | destination)

def udiv_x(destination, first, second):
    return word(2596276224 | second << 16 | first << 5 | destination)

def msub_x(destination, first, second, minuend):
    return word(2600501248 | second << 16 | minuend << 10 | first << 5 | destination)

def madd_x(destination, first, second, addend):
    return word(2600468480 | second << 16 | addend << 10 | first << 5 | destination)

def mrs_counter(destination):
    return word(3577471040 | destination)

def cmp_x(first, second):
    return word(3942645791 | second << 16 | first << 5)

def csel_w(destination, first, second, condition):
    return word(444596224 | second << 16 | CONDITIONS[condition] << 12 | first << 5 | destination)

def adrp_add(register, source, target):
    page = (target + TEXT_DELTA >> 12) - (source + TEXT_DELTA >> 12)
    adrp = 2415919104 | (page & 3) << 29 | (page >> 2 & 524287) << 5 | register
    add = 2432696320 | (target + TEXT_DELTA & 4095) << 10 | register << 5 | register
    return word(adrp) + word(add)

def is_bl(raw_word):
    return raw_word >> 26 == 37

def branch_target(source, raw_word):
    offset = raw_word & 67108863
    return source + (offset - (1 << 26) if offset & 33554432 else offset) * 4

def br(register):
    return word(3592355840 | register << 5)
RET = word(3596551104)
NOP = word(3573751839)
SP = 31
LOADS = {8: 4181721088, 4: 3107979264, 1: 960495616}
STORES = {8: 4177526784, 4: 3103784960, 1: 956301312}
OFFSET19_KINDS = {'cbz': 3019898880, 'cbzw': 872415232, 'cbnzw': 889192448, 'cbnzx': 3036676096, 'ldrlit': 1476395008, 'ldrlit_s': 469762048}
TBZ, TBNZ = (905969664, 922746880)

def ldst(base, size, rt, rn, offset):
    return word(base | offset // size << 10 | rn << 5 | rt)

def adr(rd, source, target):
    delta = target - source
    return word(268435456 | (delta & 3) << 29 | (delta >> 2 & 524287) << 5 | rd)

def offset19(base, rt, source, target):
    return word(base | (target - source >> 2 & 524287) << 5 | rt)

def test_bit_branch(opcode, register, bit, source, target):
    return word(opcode | (bit & 31) << 19 | (target - source >> 2 & 16383) << 5 | register)

def str_w(source, base, offset):
    return ldst(STORES[4], 4, source, base, offset)

def add_w(destination, first, second):
    return word(184549376 | second << 16 | first << 5 | destination)

def sub_w_imm(destination, source, value):
    return word(1358954496 | value << 10 | source << 5 | destination)

def umaddl_x(destination, first, second, addend):
    return word(2610954240 | second << 16 | addend << 10 | first << 5 | destination)

def adrp(register, source, address):
    page = (address >> 12) - (source + TEXT_DELTA >> 12)
    return word(2415919104 | (page & 3) << 29 | (page >> 2 & 524287) << 5 | register)

class Assembler:

    def __init__(self, at_address):
        self.at = at_address
        self.code = bytearray()
        self.labels = {}
        self.fixups = []

    def here(self):
        return self.at + len(self.code)

    def emit(self, raw):
        self.code.extend(raw)

    def call(self, target):
        self.emit(bl(self.here(), target))

    def jump(self, kind, label, register=0):
        self.fixups.append((kind, len(self.code), label, register))
        self.code.extend(bytes(4))

    def label(self, name):
        self.labels[name] = len(self.code)

    def align(self, size=8):
        while len(self.code) % size:
            self.emit(NOP)

    def adrp_ldr(self, register, address):
        self.emit(adrp(register, self.here(), address))
        self.emit(ldr_x(register, register, address & 4095))

    def build(self):
        for kind, position, label, register in self.fixups:
            source, target = (self.at + position, self.at + self.labels[label])
            test_bit = re.fullmatch('(tbn?z)(\\d+)', kind)
            if kind == 'b':
                raw = b(source, target)
            elif kind == 'bl':
                raw = bl(source, target)
            elif kind == 'adr':
                raw = adr(register, source, target)
            elif kind in OFFSET19_KINDS:
                raw = offset19(OFFSET19_KINDS[kind], register, source, target)
            elif test_bit:
                opcode = TBNZ if test_bit.group(1) == 'tbnz' else TBZ
                raw = test_bit_branch(opcode, register, int(test_bit.group(2)), source, target)
            else:
                raw = b_cond(kind[2:], source, target)
            self.code[position:position + 4] = raw
        return bytes(self.code)
