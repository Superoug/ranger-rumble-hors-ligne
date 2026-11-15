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

def cbz_x(register, source, target):
    return word(3019898880 | (target - source >> 2 & 524287) << 5 | register)

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

def ldp_x_signed(first, second, base, offset):
    return ldp_x(first, second, base, offset)

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

def br(register):
    return word(3592355840 | register << 5)
RET = word(3596551104)
NOP = word(3573751839)
SP = 31
