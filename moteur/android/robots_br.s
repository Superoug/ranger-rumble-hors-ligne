.text
.globl _bb_start
_bb_start:
    ret
.globl _bb_seek
_bb_seek:
    cbz  x1, original
    ldr  x8, [x1, #0x370]
    cbz  x8, original
    ldr  x8, [x8, #0x18]
    ldr  x9, arena
    cmp  x8, x9
    b.ne original
    stp  x29, x30, [sp, #-0xc0]!
    stp  x19, x20, [sp, #0x10]
    stp  x21, x22, [sp, #0x20]
    stp  x23, x24, [sp, #0x30]
    stp  x25, x26, [sp, #0x40]
    stp  x27, x28, [sp, #0x50]
    stp  x0, x1, [sp, #0x60]
    stp  x2, x3, [sp, #0x70]
    mov  x19, x1
    mov  x20, x3
    mov  x0, x19
    mov  x1, x20
    mov  x2, xzr
    bl   ext_is_able_to_seek
    cbz  w0, give_back
    adr  x0, s_seek
    bl   bb_log
    mov  x0, x19
    ldr  x1, [x20, #0x10]
    add  x2, sp, #0x80
    str  xzr, [x2]
    mov  x3, xzr
    bl   ext_try_get_weapon_user
    cbz  w0, no_weapon
    ldr  x8, [sp, #0x80]
    cbz  x8, no_weapon
    ldr  x21, [x8, #0x10]
    bl   weapon_rgctx
    ldr  x3, [x0, #8]
    ldr  x0, [x19, #0xa0]
    cbz  x0, give_back
    mov  x1, x21
    add  x2, sp, #0x80
    str  xzr, [x2]
    bl   ext_try_get_weapon
    cbz  w0, no_weapon
    ldr  x8, [sp, #0x80]
    cbz  x8, no_weapon
    ldr  x9, [x8, #0x78]
    ldr  x10, mark
    cmp  x9, x10
    b.ne not_marked
    ldr  w9, [x8, #0x20]
    cbnz w9, loaded
    adr  x0, s_empty
    bl   bb_log
    ldr  x8, [x20, #8]
    cbz  x8, give_back
    ldp  x9, x10, [x8]
    ldr  x11, [x8, #0x10]
    stp  x9, x10, [sp, #0x88]
    str  x11, [sp, #0x98]
    mov  x0, x19
    mov  x1, xzr
    bl   ext_zone_pointer
    mov  x28, x0
    ldr  x8, [x20, #0x30]
    cbz  x8, give_back
    ldr  x8, [x8, #0x48]
    str  x8, [sp, #0xb8]
    ldr  w22, [x19, #0x20]
    mov  w24, #0
    mov  x25, xzr
    mov  x26, #-1
next:
    cmp  w24, w22
    b.hs done
    ldr  x23, [x19, #0x38]
    add  x8, x23, x24, lsl #4
    ldr  x27, [x8]
    add  w24, w24, #1
    tbz  x27, #63, next
    bl   powerup_rgctx
    ldr  x3, [x0, #8]
    ldr  x0, [x19, #0xa0]
    mov  x1, x27
    add  x2, sp, #0x80
    str  xzr, [x2]
    bl   ext_try_get_powerup
    cbz  w0, next
    ldr  x8, [sp, #0x80]
    cbz  x8, next
    ldr  w9, [x8]
    cbnz w9, next
    ldr  x9, [x8, #8]
    ldr  x10, weapon_spec
    cmp  x9, x10
    b.ne next
    bl   transform_rgctx
    ldr  x2, [x0]
    ldr  x0, [x19, #0xa0]
    mov  x1, x27
    bl   ext_get_transform
    cbz  x0, next
    ldp  x9, x10, [x0]
    ldr  x11, [x0, #0x10]
    stp  x9, x10, [sp, #0xa0]
    str  x11, [sp, #0xb0]
    cbz  x28, near_enough
    mov  x0, x28
    mov  x1, x19
    add  x2, sp, #0xa0
    ldr  x3, [sp, #0xb8]
    mov  x4, xzr
    bl   ext_near_border
    cbnz w0, next
near_enough:
    ldp  x9, x10, [sp, #0xa0]
    ldr  x11, [sp, #0xb0]
    ldp  x12, x13, [sp, #0x88]
    ldr  x14, [sp, #0x98]
    sub  x12, x9, x12
    mul  x12, x12, x12
    sub  x13, x10, x13
    mul  x13, x13, x13
    sub  x14, x11, x14
    mul  x14, x14, x14
    add  x12, x12, x13
    add  x12, x12, x14
    cmp  x12, x26
    b.hs next
    mov  x26, x12
    mov  x25, x27
    b    next
done:
    cbz  x25, give_back
    ldr  x8, [x20, #0x20]
    cbz  x8, give_back
    str  x25, [x8, #0x68]
    adr  x0, s_target
    bl   bb_log
    ldr  x0, utility
    ldp  x19, x20, [sp, #0x10]
    ldp  x21, x22, [sp, #0x20]
    ldp  x23, x24, [sp, #0x30]
    ldp  x25, x26, [sp, #0x40]
    ldp  x27, x28, [sp, #0x50]
    ldp  x29, x30, [sp], #0xc0
    ret
not_marked:
    adr  x0, s_not_marked
    bl   bb_log
    b    give_back
loaded:
    adr  x0, s_loaded
    bl   bb_log
    b    give_back
no_weapon:
    adr  x0, s_no_weapon
    bl   bb_log
give_back:
    ldp  x0, x1, [sp, #0x60]
    ldp  x2, x3, [sp, #0x70]
    ldp  x19, x20, [sp, #0x10]
    ldp  x21, x22, [sp, #0x20]
    ldp  x23, x24, [sp, #0x30]
    ldp  x25, x26, [sp, #0x40]
    ldp  x27, x28, [sp, #0x50]
    ldp  x29, x30, [sp], #0xc0
original:
    stp  x29, x30, [sp, #-0x60]!
    b    ext_seek_back
bb_log:
    ldr  w9, journal
    cbz  w9, 1f
    ldr  w9, [x19, #0x1c]
    tst  w9, #127
    b.ne 1f
    stp  x29, x30, [sp, #-0x10]!
    bl   ext_string_new
    mov  x1, xzr
    bl   ext_debug_log
    ldp  x29, x30, [sp], #0x10
1:  ret
weapon_rgctx:
    stp  x29, x30, [sp, #-0x20]!
    str  x19, [sp, #0x10]
    adrp x0, slot_weapon@PAGE
    ldr  x0, [x0, slot_weapon@PAGEOFF]
    b    rgctx_common
powerup_rgctx:
    stp  x29, x30, [sp, #-0x20]!
    str  x19, [sp, #0x10]
    adrp x0, slot_powerup@PAGE
    ldr  x0, [x0, slot_powerup@PAGEOFF]
    b    rgctx_common
transform_rgctx:
    stp  x29, x30, [sp, #-0x20]!
    str  x19, [sp, #0x10]
    adrp x0, slot_transform@PAGE
    ldr  x0, [x0, slot_transform@PAGEOFF]
rgctx_common:
    str  x0, [sp, #0x18]
    ldr  x9, [x0]
    tbz  x9, #0, 1f
    bl   ext_init_metadata
1:  ldr  x8, [sp, #0x18]
    ldr  x19, [x8]
    ldr  x8, [x19, #0x38]
    cbnz x8, 2f
    mov  x0, x19
    bl   ext_init_rgctx
2:  ldr  x0, [x19, #0x38]
    ldr  x19, [sp, #0x10]
    ldp  x29, x30, [sp], #0x20
    ret
.p2align 3
arena:
    .quad 3380846735053013127
weapon_spec:
    .quad 241661061706034376
mark:
    .quad 0x20001
utility:
    .quad 42598
s_seek:         .asciz "RR BR robot: evaluation"
s_not_marked:   .asciz "RR BR robot: arme tenue sans la marque"
s_empty:        .asciz "RR BR robot: arme vide"
s_loaded:       .asciz "RR BR robot: arme marquee avec munitions"
s_no_weapon:    .asciz "RR BR robot: pas d'arme tenue"
s_target:       .asciz "RR BR robot: ramassage d'arme vise"
    .p2align 2
journal:        .word 0
