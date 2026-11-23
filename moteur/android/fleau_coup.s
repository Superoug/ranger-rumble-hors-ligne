.text
.macro statics reg, name
    adrp x0, \name@PAGE
    ldr  x0, [x0, \name@PAGEOFF]
    bl   ext_init_metadata
    adrp \reg, \name@PAGE
    ldr  \reg, [\reg, \name@PAGEOFF]
    ldr  \reg, [\reg]
    ldr  w8, [\reg, #0xe4]
    cbnz w8, 1f
    mov  x0, \reg
    bl   ext_class_init
1:  ldr  \reg, [\reg, #0xb8]
.endm
.globl _fc_start
_fc_start:
    ret
.globl _fc_trigger
_fc_trigger:
    ldr  w25, [x10, #0x30]
    ldr  x11, [x19, #0x78]
    cbz  x11, 1f
    ldr  w12, [x11, #0xc4]
    cmp  w12, #3
    b.ne 1f
    ldr  w25, [x10, #0x34]
1:  ret
.globl _fc_spin
_fc_spin:
    stp  x29, x30, [sp, #-0x40]!
    stp  x19, x20, [sp, #0x10]
    stp  x21, x22, [sp, #0x20]
    str  x23, [sp, #0x30]
    and  w20, w1, #1
    ldr  x8, [x0, #0x118]
    cbz  x8, 9f
    ldr  x19, [x8, #0x58]
    cbz  x19, 9f
    ldr  x21, [x19, #0x38]
    cbz  x21, 9f
    statics x9, slot_anim_bool
    ldr  w22, [x9, #0x18]
    statics x9, slot_anim_trigger
    ldr  w23, [x9, #0x48]
    mov  x0, x21
    mov  w1, w22
    mov  x2, xzr
    bl   ext_get_bool
    and  w0, w0, #1
    cmp  w0, w20
    b.eq 9f
    mov  x0, x19
    mov  w1, w23
    mov  x2, xzr
    cbz  w20, 2f
    bl   ext_set_trigger
    b    3f
2:  bl   ext_reset_trigger
3:  mov  x0, x19
    mov  w1, w22
    mov  w2, w20
    mov  x3, xzr
    bl   ext_set_bool
9:  ldr  x23, [sp, #0x30]
    ldp  x21, x22, [sp, #0x20]
    ldp  x19, x20, [sp, #0x10]
    ldp  x29, x30, [sp], #0x40
    ret
