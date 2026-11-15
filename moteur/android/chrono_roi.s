.text
.globl _kt_start
_kt_start:
.globl _kt_timer
_kt_timer:
    stp  x29, x30, [sp, #-0x40]!
    stp  x19, x20, [sp, #0x10]
    stp  x21, x22, [sp, #0x20]
    mov  x19, x0
    mov  x21, x20
    mov  x20, x22
    mov  w22, #0
    cbz  x20, 8f
    str  xzr, [sp, #0x30]
    mov  x0, x20
    add  x1, sp, #0x30
    mov  x2, xzr
    bl   ext_try_get_spec
    cbz  w0, 8f
    ldr  x9, [sp, #0x30]
    cbz  x9, 8f
    ldr  x10, [x9, #0x1e8]
    cmp  x10, #0x10, lsl #12
    b.lt 8f
    ldr  x10, [x9, #0x1c8]
    cbz  x10, 8f
    str  x9, [sp, #0x38]
    ldr  x8, [x20]
    ldr  x9, [x8, #0x248]
    ldr  x1, [x8, #0x250]
    mov  x0, x20
    blr  x9
    ldr  x9, [sp, #0x38]
    ldr  w10, [x20, #0x1c]
    ldr  w11, [x9, #0x1d0]
    sub  w10, w10, w11
    sxtw x10, w10
    mul  x10, x0, x10
    ldr  x11, [x9, #0x1e8]
    sub  x11, x11, x10
    cmp  x11, x19
    csel x19, x11, x19, lt
    cmp  x19, #0
    csel x19, xzr, x19, lt
    mov  w22, #1
8:  ldr  x0, [x21, #0x38]
    cbz  x0, 9f
    ldr  w8, [x21, #0x7c]
    cmp  w8, w22
    b.eq 9f
    str  w22, [x21, #0x7c]
    adr  x8, white
    cbz  w22, 7f
    adr  x8, gold
7:  ldp  s0, s1, [x8]
    ldp  s2, s3, [x8, #8]
    mov  x1, xzr
    bl   ext_set_color
9:  mov  x0, x19
    mov  x1, xzr
    bl   ext_ceil_to_int
    ldp  x21, x22, [sp, #0x20]
    ldp  x19, x20, [sp, #0x10]
    ldp  x29, x30, [sp], #0x40
    ret
    .p2align 3
gold:  .float 1.0, 0.8, 0.15, 1.0
white: .float 1.0, 1.0, 1.0, 1.0
