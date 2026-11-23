.text
.macro get_pointer slotname, entity
    adrp x0, \slotname@PAGE
    ldr  x0, [x0, \slotname@PAGEOFF]
    bl   ext_init_metadata
    adrp x8, \slotname@PAGE
    ldr  x8, [x8, \slotname@PAGEOFF]
    ldr  x23, [x8]
    ldr  x8, [x23, #0x38]
    cbnz x8, 1f
    mov  x0, x23
    bl   ext_init_rgctx
1:  ldr  x8, [x23, #0x38]
    ldr  x3, [x8, #8]
    ldr  x0, [x19, #0xa0]
    mov  x1, \entity
    add  x2, sp, #0x50
    str  xzr, [x2]
    bl   ext_try_get_pointer
.endm
.globl _flail_enh
_flail_enh:
    sub  sp, sp, #0x70
    stp  x19, x20, [sp, #0x10]
    stp  x21, x22, [sp, #0x20]
    stp  x23, x24, [sp, #0x30]
    stp  x25, x26, [sp, #0x40]
    stp  x29, x30, [sp, #0x60]
    mov  x19, x0
    mov  x20, x1
    mov  x21, x2
    mov  x22, x3
    mov  w24, wzr
    mov  x25, xzr
    get_pointer slot_aoe, x21
    tbz  w0, #0, 2f
    ldr  x8, [sp, #0x50]
    cbz  x8, 2f
    ldr  w9, [x19, #0x1c]
    ldr  w10, [x8, #0x4]
    sub  w9, w9, w10
    str  w9, [sp, #0x58]
    ldr  x8, [x19]
    ldr  x9, [x8, #0x248]
    ldr  x1, [x8, #0x250]
    mov  x0, x19
    blr  x9
    ldrsw x9, [sp, #0x58]
    mul  x9, x9, x0
    add  x9, x9, #0x10, lsl #12
    ldr  x8, [sp, #0x50]
    str  x9, [x8, #0x28]
2:  ldr  x9, enh_delay
    cmp  x22, x9
    b.lt done
    get_pointer slot_loadout, x20
    tbz  w0, #0, done
    ldr  x8, [sp, #0x50]
    cbz  x8, done
    add  x8, x8, #0x28
    mov  w9, #4
    mov  w24, wzr
find:
    ldr  w10, [x8, #0x1c]
    cmp  w10, #9
    b.ne next
    ldrb w24, [x8, #0x18]
    b    found
next:
    add  x8, x8, #0x20
    subs w9, w9, #1
    b.ne find
found:
    cbz  w24, done
    get_pointer slot_aoe, x21
    tbz  w0, #0, torque
    ldr  x8, [sp, #0x50]
    cbz  x8, torque
    ldr  x9, enh_delay
    sub  x10, x22, x9
    lsl  x10, x10, #1
    mov  x11, #0x10000
    cmp  x10, x11
    csel x10, x10, x11, lt
    ldr  x11, mega_gain
    mul  x10, x10, x11
    asr  x10, x10, #16
    add  x10, x10, #0x10, lsl #12
    stp  x10, x10, [x8, #0x40]
    str  x10, [x8, #0x50]
    mov  x25, x10
torque:
    cmp  w24, #2
    b.lt done
    get_pointer slot_pusher, x21
    tbz  w0, #0, done
    ldr  x8, [sp, #0x50]
    cbz  x8, done
    ldr  x9, torque_pusher
    str  x9, [x8]
done:
    bl   log_enh
    ldp  x19, x20, [sp, #0x10]
    ldp  x21, x22, [sp, #0x20]
    ldp  x23, x24, [sp, #0x30]
    ldp  x25, x26, [sp, #0x40]
    ldp  x29, x30, [sp, #0x60]
    add  sp, sp, #0x70
    ret
log_enh:
    ldr  w9, journal
    cbz  w9, log_end
    cbz  w24, log_end
    ldr  w9, [x19, #0x1c]
    tst  w9, #31
    b.ne log_end
    stp  x29, x30, [sp, #-0x40]!
    adr  x9, log_text
    ldp  x10, x11, [x9]
    stp  x10, x11, [sp, #0x10]
    ldp  x10, x11, [x9, #0x10]
    stp  x10, x11, [sp, #0x20]
    add  w10, w24, #48
    strb w10, [sp, #0x21]
    mov  x10, #100
    mul  x10, x25, x10
    asr  x10, x10, #16
    mov  w11, #10
    add  x12, sp, #0x2c
digit:
    udiv w13, w10, w11
    msub w14, w13, w11, w10
    add  w14, w14, #48
    strb w14, [x12], #-1
    mov  w10, w13
    add  x13, sp, #0x29
    cmp  x12, x13
    b.hi digit
    add  x0, sp, #0x10
    bl   ext_string_new
    mov  x1, xzr
    bl   ext_debug_log
    ldp  x29, x30, [sp], #0x40
log_end:
    ret
    .p2align 3
log_text:      .ascii "RR fleau: niveau 0 taille 000\0\0\0"
journal:       .word 0
    .p2align 3
enh_delay:     .quad 131072
mega_gain:     .quad 0
torque_pusher: .quad 0
