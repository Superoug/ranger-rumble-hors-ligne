.text
.macro save_all
    sub  sp, sp, #0xa0
    stp  x0, x1, [sp, #0x00]
    stp  x2, x3, [sp, #0x10]
    stp  x4, x5, [sp, #0x20]
    stp  x6, x7, [sp, #0x30]
    stp  x8, x9, [sp, #0x40]
    stp  x10, x11, [sp, #0x50]
    stp  x12, x13, [sp, #0x60]
    stp  x14, x15, [sp, #0x70]
    stp  x16, x17, [sp, #0x80]
    stp  x29, x30, [sp, #0x90]
.endm
.macro restore_all
    ldp  x0, x1, [sp, #0x00]
    ldp  x2, x3, [sp, #0x10]
    ldp  x4, x5, [sp, #0x20]
    ldp  x6, x7, [sp, #0x30]
    ldp  x8, x9, [sp, #0x40]
    ldp  x10, x11, [sp, #0x50]
    ldp  x12, x13, [sp, #0x60]
    ldp  x14, x15, [sp, #0x70]
    ldp  x16, x17, [sp, #0x80]
    ldp  x29, x30, [sp, #0x90]
    add  sp, sp, #0xa0
.endm
.macro slot_value reg, name
    adrp x0, \name@PAGE
    ldr  x0, [x0, \name@PAGEOFF]
    bl   ext_init_metadata
    adrp \reg, \name@PAGE
    ldr  \reg, [\reg, \name@PAGEOFF]
    ldr  \reg, [\reg]
.endm
.globl _dh_start
_dh_start:
    ret
.globl _dw_hud
_dw_hud:
    save_all
    stp  x19, x20, [sp, #-0x70]!
    stp  x21, x22, [sp, #0x10]
    stp  x23, x24, [sp, #0x20]
    stp  x25, x26, [sp, #0x30]
    mov  x19, x0
    mov  x20, x1
    mov  x21, x2
    ldr  w8, [x19, #0x20]
    cbnz w8, 9f
    cbz  x20, 9f
    bl   other_weapon
    cbz  w2, 9f
    stp  w2, w3, [sp, #0x48]
    str  wzr, [sp, #0x50]
    mov  w22, w0
    mov  w23, w1
    mov  x0, x19
    mov  x1, xzr
    bl   ext_get_transform
    cbz  x0, 9f
    mov  x24, x0
    mov  x1, xzr
    bl   ext_get_parent
    cbz  x0, 9f
    mov  x25, x0
    adr  x0, s_clone
    bl   ext_string_new
    mov  x1, x0
    mov  x0, x25
    mov  x2, xzr
    bl   ext_find
    mov  x26, x0
    cbnz x26, 2f
    cbz  w22, 9f
    bl   make_clone
    mov  x26, x0
    cbz  x26, 9f
    mov  w8, #1
    str  w8, [sp, #0x50]
    ldr  w9, journal
    cbz  w9, 2f
    adr  x0, log_clone
    bl   ext_string_new
    mov  x1, xzr
    bl   ext_debug_log
2:
    ldr  w8, [sp, #0x48]
    cmp  w23, w8
    cset w2, eq
    ldr  w3, [sp, #0x50]
    mov  x0, x24
    mov  x1, x26
    bl   ext_dm_layout
    mov  x0, x26
    mov  x1, xzr
    bl   ext_get_gameobject
    cbz  x0, 9f
    mov  x25, x0
    cmp  w22, #0
    cset w1, ne
    mov  x2, xzr
    bl   ext_set_active
    cbz  w22, 9f
    ldr  x0, [x19, #0x30]
    cbz  x0, 3f
    mov  x1, xzr
    bl   ext_get_alpha
    str  s0, [sp, #0x40]
    adr  x0, s_group
    bl   ext_string_new
    mov  x1, x0
    mov  x0, x25
    mov  x2, xzr
    bl   ext_component_by_name
    cbz  x0, 3f
    ldr  s0, [sp, #0x40]
    ldr  s1, clone_alpha
    fmul s0, s0, s1
    mov  x1, xzr
    bl   ext_set_alpha
3:  mov  x0, x25
    ldr  w1, [sp, #0x4c]
    bl   ext_dm_hud_ammo
    mov  w1, w22
    mov  x0, x25
    bl   show_weapon
    mov  x0, x19
    mov  x1, xzr
    bl   ext_get_gameobject
    cbz  x0, 9f
    mov  w1, w23
    bl   show_weapon
9:  ldp  x21, x22, [sp, #0x10]
    ldp  x23, x24, [sp, #0x20]
    ldp  x25, x26, [sp, #0x30]
    ldp  x19, x20, [sp], #0x70
    restore_all
    mov  x20, x0
    ret
other_weapon:
    stp  x29, x30, [sp, #-0x40]!
    stp  x22, x23, [sp, #0x10]
    mov  w22, wzr
    mov  w23, wzr
    slot_value x9, slot_actor
    ldr  x8, [x9, #0x38]
    cbnz x8, 1f
    str  x9, [sp, #0x20]
    mov  x0, x9
    bl   ext_init_rgctx
    ldr  x9, [sp, #0x20]
1:  ldr  x8, [x9, #0x38]
    ldr  x3, [x8, #8]
    ldr  x0, [x20, #0xa0]
    cbz  x0, 8f
    mov  x1, x21
    add  x2, sp, #0x30
    str  xzr, [x2]
    bl   ext_actor_pointer
    tbz  w0, #0, 8f
    ldr  x8, [sp, #0x30]
    cbz  x8, 8f
    mov  x0, x20
    ldr  w1, [x8, #0x34]
    mov  x2, xzr
    bl   ext_player_data
    cbz  x0, 8f
    ldrb w22, [x0, #0x46]
    ldr  w23, [x0, #0x48]
    slot_value x9, slot_loadout
    ldr  x8, [x9, #0x38]
    cbnz x8, 2f
    str  x9, [sp, #0x20]
    mov  x0, x9
    bl   ext_init_rgctx
    ldr  x9, [sp, #0x20]
2:  ldr  x8, [x9, #0x38]
    ldr  x3, [x8, #8]
    ldr  x0, [x20, #0xa0]
    mov  x1, x21
    add  x2, sp, #0x30
    str  xzr, [x2]
    bl   ext_try_get_pointer
    tbz  w0, #0, 8f
    ldr  x8, [sp, #0x30]
    cbz  x8, 8f
    ldr  w1, [x8, #0x44]
    ldrh w3, [x8, #0x42]
    mov  w0, wzr
    cbz  w22, 9f
    cmp  w22, w23
    b.eq 9f
    cmp  w1, w23
    csel w0, w22, w0, eq
    b.eq 9f
    cmp  w1, w22
    csel w0, w23, w0, eq
    b    9f
8:  mov  w0, wzr
    mov  w1, wzr
    mov  w3, wzr
    mov  w22, wzr
9:  mov  w2, w22
    ldp  x22, x23, [sp, #0x10]
    ldp  x29, x30, [sp], #0x40
    ret
make_clone:
    stp  x29, x30, [sp, #-0x30]!
    stp  x19, x20, [sp, #0x10]
    str  x21, [sp, #0x20]
    mov  x0, x19
    mov  x1, xzr
    bl   ext_get_gameobject
    cbz  x0, 8f
    mov  x1, x25
    mov  x2, xzr
    bl   ext_instantiate
    cbz  x0, 8f
    mov  x20, x0
    adr  x0, s_clone
    bl   ext_string_new
    mov  x1, x0
    mov  x0, x20
    mov  x2, xzr
    bl   ext_set_name
    adr  x0, s_widget
    bl   disable_component
    adr  x0, s_preset
    bl   disable_component
    adr  x0, s_updater
    bl   disable_component
    mov  x21, x0
    cbz  x21, 1f
    ldr  x0, [x21, #0x48]
    bl   hide_component
    ldr  x0, [x21, #0x78]
    bl   hide_component
    ldr  x0, [x21, #0x80]
    bl   hide_component
    ldr  x0, [x21, #0x88]
    bl   hide_component
1:  adr  x0, s_handler
    bl   ext_string_new
    mov  x1, x0
    mov  x0, x20
    mov  x2, xzr
    bl   ext_component_by_name
    cbz  x0, 2f
    mov  x21, x0
    adr  x0, s_arme2
    bl   ext_string_new
    mov  x1, x0
    add  x0, x21, #0x20
    str  x1, [x0]
    bl   ext_wbarrier
2:  mov  x0, x20
    mov  x1, xzr
    bl   ext_go_transform
    b    9f
8:  mov  x0, xzr
9:  ldp  x19, x20, [sp, #0x10]
    ldr  x21, [sp, #0x20]
    ldp  x29, x30, [sp], #0x30
    ret
disable_component:
    stp  x29, x30, [sp, #-0x20]!
    str  x19, [sp, #0x10]
    bl   ext_string_new
    mov  x1, x0
    mov  x0, x20
    mov  x2, xzr
    bl   ext_component_by_name
    mov  x19, x0
    cbz  x0, 1f
    mov  w1, wzr
    mov  x2, xzr
    bl   ext_set_enabled
1:  mov  x0, x19
    ldr  x19, [sp, #0x10]
    ldp  x29, x30, [sp], #0x20
    ret
hide_component:
    stp  x29, x30, [sp, #-0x10]!
    cbz  x0, 1f
    mov  x1, xzr
    bl   ext_get_gameobject
    cbz  x0, 1f
    mov  w1, wzr
    mov  x2, xzr
    bl   ext_set_active
1:  ldp  x29, x30, [sp], #0x10
    ret
show_weapon:
    stp  x29, x30, [sp, #-0x30]!
    stp  x19, x20, [sp, #0x10]
    mov  x19, x0
    mov  w20, w1
    cbz  w20, 9f
    mov  x0, xzr
    bl   ext_weapon_table
    cbz  x0, 9f
    mov  w1, w20
    mov  x2, xzr
    bl   ext_weapon_spec
    cbz  x0, 9f
    ldr  x20, [x0, #0x100]
    cbz  x20, 9f
    adr  x0, s_widget
    bl   ext_string_new
    mov  x1, x0
    mov  x0, x19
    mov  x2, xzr
    bl   ext_component_by_name
    cbz  x0, 9f
    mov  x19, x0
    ldr  x0, [x19, #0x40]
    cbz  x0, 1f
    mov  x1, x20
    mov  x2, xzr
    bl   ext_set_sprite
1:  ldr  x0, [x19, #0x48]
    cbz  x0, 9f
    mov  x1, x20
    mov  x2, xzr
    bl   ext_set_sprite
9:  ldp  x19, x20, [sp, #0x10]
    ldp  x29, x30, [sp], #0x30
    ret
    .p2align 3
clone_alpha: .float 0.65
s_clone:   .asciz "Button_Arme2"
s_arme2:   .asciz "Arme2"
s_widget:  .asciz "ReloadButtonWidget"
s_updater: .asciz "WeaponButtonStatusUpdater"
s_preset:  .asciz "PresetButtonItem"
s_handler: .asciz "ButtonHandler"
s_group:   .asciz "CanvasGroup"
log_clone: .asciz "RR deux armes: case creee"
    .p2align 2
journal:   .word 0
