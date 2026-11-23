.text
.macro slot_value reg, name
    adrp x0, \name@PAGE
    ldr  x0, [x0, \name@PAGEOFF]
    bl   ext_init_metadata
    adrp \reg, \name@PAGE
    ldr  \reg, [\reg, \name@PAGEOFF]
    ldr  \reg, [\reg]
.endm
.equ SPAWN_MENU, 10
.globl _dm_start
_dm_start:
    ret
weapon_pointer:
    stp  x29, x30, [sp, #-0x30]!
    stp  x19, x20, [sp, #0x10]
    mov  x19, x0
    mov  x20, x1
    cbz  x20, 8f
    slot_value x9, slot_weapon
    ldr  x8, [x9, #0x38]
    cbnz x8, 1f
    str  x9, [sp, #0x20]
    mov  x0, x9
    bl   ext_init_rgctx
    ldr  x9, [sp, #0x20]
1:  ldr  x8, [x9, #0x38]
    ldr  x3, [x8, #8]
    ldr  x0, [x19, #0xa0]
    cbz  x0, 8f
    mov  x1, x20
    add  x2, sp, #0x28
    str  xzr, [x2]
    bl   ext_weapon_pointer
    tbz  w0, #0, 8f
    ldr  x0, [sp, #0x28]
    b    9f
8:  mov  x0, xzr
9:  ldp  x19, x20, [sp, #0x10]
    ldp  x29, x30, [sp], #0x30
    ret
.globl _dm_ammo_of
_dm_ammo_of:
    stp  x29, x30, [sp, #-0x20]!
    str  x19, [sp, #0x10]
    bl   weapon_pointer
    cbz  x0, 9f
    mov  x19, x0
    mov  x1, xzr
    bl   ext_max_ammo
    mov  w8, #127
    cmp  w0, w8
    csel w8, w0, w8, lt
    cmp  w8, #0
    b.le 8f
    ldr  w9, [x19, #0x20]
    cmp  w9, #0
    csel w9, wzr, w9, lt
    mov  w10, #255
    cmp  w9, w10
    csel w9, w9, w10, lt
    orr  w8, w8, #0x80
    orr  w0, w9, w8, lsl #8
    b    9f
8:  mov  w0, wzr
9:  ldr  x19, [sp, #0x10]
    ldp  x29, x30, [sp], #0x20
    ret
.globl _dm_set_ammo
_dm_set_ammo:
    stp  x29, x30, [sp, #-0x20]!
    stp  x19, x20, [sp, #0x10]
    mov  w20, w2
    tbz  w20, #15, 9f
    bl   weapon_pointer
    cbz  x0, 9f
    mov  x19, x0
    mov  x1, xzr
    bl   ext_max_ammo
    and  w8, w20, #0xff
    cmp  w8, w0
    csel w8, w8, w0, lt
    str  w8, [x19, #0x20]
9:  ldp  x19, x20, [sp, #0x10]
    ldp  x29, x30, [sp], #0x20
    ret
.globl _dm_layout
_dm_layout:
    stp  x29, x30, [sp, #-0x40]!
    stp  x19, x20, [sp, #0x10]
    stp  x21, x22, [sp, #0x20]
    stp  d8, d9, [sp, #0x30]
    mov  x19, x0
    mov  x20, x1
    mov  w21, w2
    mov  w22, w3
    mov  x0, x19
    mov  x1, xzr
    bl   ext_get_anchored
    fmov s8, s0
    fmov s9, s1
    cbnz w22, 1f
    mov  x0, x20
    mov  x1, xzr
    bl   ext_get_anchored
    fadd s8, s8, s0
    fadd s9, s9, s1
    adr  x8, clone_offset
    ldp  s2, s3, [x8]
    fsub s8, s8, s2
    fsub s9, s9, s3
    fmov s4, #0.5
    fmul s8, s8, s4
    fmul s9, s9, s4
1:  adr  x8, clone_offset
    ldr  s3, [x8, #4]
    fmov s0, s8
    fmov s1, s9
    cbz  w21, 2f
    fadd s1, s1, s3
2:  mov  x0, x19
    mov  x1, xzr
    bl   ext_set_anchored
    adr  x8, clone_offset
    ldp  s2, s3, [x8]
    fadd s0, s8, s2
    fmov s1, s9
    cbnz w21, 3f
    fadd s1, s1, s3
3:  mov  x0, x20
    mov  x1, xzr
    bl   ext_set_anchored
    ldr  s0, clone_scale
    fmov s1, s0
    fmov s2, #1.0
    mov  x0, x20
    mov  x1, xzr
    bl   ext_set_scale
    ldp  d8, d9, [sp, #0x30]
    ldp  x21, x22, [sp, #0x20]
    ldp  x19, x20, [sp, #0x10]
    ldp  x29, x30, [sp], #0x40
    ret
.globl _dm_hud_ammo
_dm_hud_ammo:
    stp  x29, x30, [sp, #-0x30]!
    stp  x19, x20, [sp, #0x10]
    stp  x21, x22, [sp, #0x20]
    mov  x19, x0
    mov  w20, w1
    adr  x0, s_updater
    bl   ext_string_new
    mov  x1, x0
    mov  x0, x19
    mov  x2, xzr
    bl   ext_component_by_name
    cbz  x0, 9f
    mov  x21, x0
    ubfx w22, w20, #15, #1
    ldr  x0, [x21, #0x78]
    mov  w1, w22
    bl   set_shown
    ldr  x0, [x21, #0x80]
    mov  w1, w22
    bl   set_shown
    ldr  x0, [x21, #0x88]
    mov  w1, w22
    bl   set_shown
    cbz  w22, 9f
    and  w0, w20, #0xff
    ldr  x1, [x21, #0x78]
    bl   set_number
    ubfx w0, w20, #8, #7
    ldr  x1, [x21, #0x80]
    bl   set_number
9:  ldp  x21, x22, [sp, #0x20]
    ldp  x19, x20, [sp, #0x10]
    ldp  x29, x30, [sp], #0x30
    ret
set_shown:
    stp  x29, x30, [sp, #-0x20]!
    str  x1, [sp, #0x10]
    cbz  x0, 1f
    mov  x1, xzr
    bl   ext_get_gameobject
    cbz  x0, 1f
    ldr  x1, [sp, #0x10]
    mov  x2, xzr
    bl   ext_set_active
1:  ldp  x29, x30, [sp], #0x20
    ret
set_number:
    stp  x29, x30, [sp, #-0x30]!
    str  x19, [sp, #0x10]
    mov  x19, x1
    cbz  x19, 9f
    add  x9, sp, #0x2f
    strb wzr, [x9]
    mov  w10, #10
1:  udiv w11, w0, w10
    msub w12, w11, w10, w0
    add  w12, w12, #'0'
    sub  x9, x9, #1
    strb w12, [x9]
    mov  w0, w11
    cbnz w0, 1b
    mov  x0, x9
    bl   ext_string_new
    mov  x1, x0
    mov  x0, x19
    ldr  x8, [x0]
    ldr  x9, [x8, #0x558]
    ldr  x2, [x8, #0x560]
    blr  x9
9:  ldr  x19, [sp, #0x10]
    ldp  x29, x30, [sp], #0x30
    ret
.globl _dm_anim_event
_dm_anim_event:
    cmp  w1, #SPAWN_MENU
    b.eq 1f
0:  str  x30, [sp, #-0x30]!
    b    ext_anim_event_body
1:  stp  x29, x30, [sp, #-0x20]!
    stp  x0, x1, [sp, #0x10]
    slot_value x0, slot_qm
    ldr  w8, [x0, #0xe4]
    cbnz w8, 2f
    bl   ext_class_init
2:  mov  x0, xzr
    bl   ext_main_game
    mov  x8, x0
    ldp  x0, x1, [sp, #0x10]
    ldp  x29, x30, [sp], #0x20
    cbz  x8, 0b
    ret
s_updater: .asciz "WeaponButtonStatusUpdater"
    .p2align 2
clone_offset: .float 26.0, -122.4
clone_scale:  .float 0.8
.globl _dm_end
_dm_end:
