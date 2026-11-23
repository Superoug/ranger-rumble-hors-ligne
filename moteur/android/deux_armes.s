.text
.equ SWAP, 100
.equ RANDOM_WEAPON, 2
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
.globl _dw_start
_dw_start:
    ret
.globl _dw_load
_dw_load:
    save_all
    bl   second_choice
    cbz  w0, 9f
    lsr  x9, x24, #32
    cmp  w0, w9
    b.eq 9f
    stp  x24, x25, [sp, #-0x20]!
    str  x0, [sp, #0x10]
    mov  x1, xzr
    bl   ext_unlockable_of
    str  x0, [sp, #0x18]
    mov  x1, xzr
    bl   ext_upgrade_level
    mov  w10, w0
    ldr  x0, [sp, #0x18]
    str  x10, [sp, #0x18]
    mov  x1, xzr
    bl   ext_enhancement_level
    mov  w11, w0
    ldp  x24, x25, [sp]
    ldr  x9, [sp, #0x10]
    ldr  x10, [sp, #0x18]
    add  sp, sp, #0x20
    bfi  x24, x9, #16, #8
    bfi  x24, x10, #24, #8
    bfi  x25, x11, #16, #8
    adr  x0, log_load
    bl   journal_log
9:  restore_all
    stp  x24, x25, [x20]
    ret
journal_log:
    ldr  w9, journal
    cbz  w9, 1f
    stp  x29, x30, [sp, #-0x10]!
    bl   ext_string_new
    mov  x1, xzr
    bl   ext_debug_log
    ldp  x29, x30, [sp], #0x10
1:  ret
option_on:
    stp  x29, x30, [sp, #-0x10]!
    ldr  w8, shown
    cbz  w8, 1f
    adr  x0, s_option
    bl   ext_string_new
    mov  x1, xzr
    bl   ext_get_string
    cbz  x0, 1f
    ldr  w8, [x0, #0x10]
    cmp  w8, #1
    b.ne 1f
    ldrh w8, [x0, #0x14]
    cmp  w8, #'1'
    cset w0, eq
    b    2f
1:  mov  w0, wzr
2:  ldp  x29, x30, [sp], #0x10
    ret
second_choice:
    stp  x29, x30, [sp, #-0x10]!
    bl   option_on
    cbz  w0, 1f
    adr  x0, s_second
    bl   ext_string_new
    mov  w1, wzr
    mov  x2, xzr
    bl   ext_get_int
    cmp  w0, #57
    b.lo 2f
1:  mov  w0, wzr
2:  ldp  x29, x30, [sp], #0x10
    ret
.globl _dw_option
_dw_option:
    stp  x29, x30, [sp, #-0x10]!
    bl   option_on
    ldp  x29, x30, [sp], #0x10
    ret
.globl _dw_second
_dw_second:
    b    second_choice
.globl _dw_second_uid
_dw_second_uid:
    stp  x29, x30, [sp, #-0x10]!
    bl   second_choice
    cbz  w0, 1f
    mov  x1, xzr
    bl   ext_unlockable_of
1:  ldp  x29, x30, [sp], #0x10
    ret
.globl _dw_profile
_dw_profile:
    stp  x29, x30, [sp, #-0x40]!
    stp  x19, x20, [sp, #0x10]
    stp  x21, x22, [sp, #0x20]
    stp  x0, x1, [sp, #0x30]
    mov  x19, x0
    ldr  x20, [x19, #0x20]
    cbz  x20, 9f
    bl   option_on
    mov  w22, w0
    mov  x0, x20
    mov  x1, xzr
    bl   ext_get_anchored
    adr  x8, column_two
    cbz  w22, 1f
    adr  x8, column_three
1:  ldr  s1, [x8, #4]
    mov  x0, x20
    mov  x1, xzr
    bl   ext_set_anchored
    adr  x8, column_two
    cbz  w22, 2f
    adr  x8, column_three
2:  ldr  s0, [x8]
    fmov s1, s0
    fmov s2, #1.0
    mov  x0, x20
    mov  x1, xzr
    bl   ext_set_scale
    adr  x0, s_slot2
    bl   ext_string_new
    mov  x1, x0
    mov  x0, x20
    mov  x2, xzr
    bl   ext_find
    mov  x21, x0
    cbnz x21, 5f
    cbz  w22, 9f
    ldr  x8, [x19, #0x30]
    cbz  x8, 9f
    ldr  w9, [x8, #0x18]
    cbz  w9, 9f
    ldr  x0, [x8, #0x20]
    cbz  x0, 9f
    mov  x1, xzr
    bl   ext_get_gameobject
    cbz  x0, 9f
    mov  x1, x20
    mov  x2, xzr
    bl   ext_instantiate
    cbz  x0, 9f
    mov  x21, x0
    adr  x0, s_slot2
    bl   ext_string_new
    mov  x1, x0
    mov  x0, x21
    mov  x2, xzr
    bl   ext_set_name
    adr  x0, s_slot_widget
    bl   ext_string_new
    mov  x1, x0
    mov  x0, x21
    mov  x2, xzr
    bl   ext_component_by_name
    cbz  x0, 9f
    mov  w8, #2
    str  w8, [x0, #0x58]
    adr  x0, s_log_slot
    bl   journal_log
    b    9f
5:  mov  x0, x21
    mov  x1, xzr
    bl   ext_get_gameobject
    cbz  x0, 9f
    mov  w1, w22
    mov  x2, xzr
    bl   ext_set_active
9:  ldp  x0, x1, [sp, #0x30]
    ldp  x21, x22, [sp, #0x20]
    ldp  x19, x20, [sp, #0x10]
    ldp  x29, x30, [sp], #0x40
    sub  sp, sp, #0x70
    b    ext_bind_body
.globl _dw_command
_dw_command:
    cmp  w3, #SWAP
    b.eq 0f
    b    ext_switch_to_weapon
0:  ldr  x9, [sp, #8]
    stp  x29, x30, [sp, #-0x60]!
    stp  x19, x20, [sp, #0x10]
    stp  x21, x22, [sp, #0x20]
    stp  x23, x24, [sp, #0x30]
    mov  x19, x0
    mov  x20, x1
    mov  x21, x2
    mov  x22, x9
    cbz  x22, 9f
    cbz  x21, 9f
    ldr  w8, [x21, #0xc]
    cbnz w8, 9f
    ldr  x8, [x19, #0x370]
    cbz  x8, 9f
    ldr  w8, [x8, #0x88]
    cmp  w8, #RANDOM_WEAPON
    b.eq 9f
    mov  x0, x19
    ldr  w1, [x22, #0x34]
    mov  x2, xzr
    bl   ext_player_data
    cbz  x0, 9f
    ldrb w9, [x0, #0x46]
    cbz  w9, 9f
    ldr  w10, [x0, #0x48]
    cmp  w9, w10
    b.eq 9f
    ldr  w11, [x21, #0x44]
    cmp  w11, w10
    b.ne 1f
    ldrb w12, [x0, #0x4e]
    ldrb w13, [x0, #0x47]
    b    2f
1:  cmp  w11, w9
    b.ne 9f
    mov  w9, w10
    ldrb w12, [x0, #0x44]
    ldrb w13, [x0, #0x45]
2:  orr  w12, w12, w13, lsl #8
    mov  w23, w12
    orr  x23, x23, x9, lsl #32
    slot_value x24, slot_table
    ldr  x8, [x24, #0x38]
    cbnz x8, 3f
    mov  x0, x24
    bl   ext_init_rgctx
3:  ldr  x8, [x24, #0x38]
    ldr  x4, [x8, #8]
    ldr  x8, [x19, #0x370]
    ldr  x1, [x8, #0x40]
    str  xzr, [sp, #0x40]
    add  x3, sp, #0x40
    mov  x0, x19
    mov  w2, #1
    bl   ext_find_asset
    tbz  w0, #0, 9f
    ldr  x8, [sp, #0x40]
    cbz  x8, 9f
    ldrh w8, [x21, #0x42]
    str  w8, [sp, #0x48]
    ldr  x24, [x21, #0x38]
    mov  x0, x19
    mov  x1, x24
    bl   ext_dm_ammo_of
    and  x0, x0, #0xffff
    orr  x23, x23, x0, lsl #16
    mov  x0, x24
    mov  x1, xzr
    mov  x2, xzr
    bl   ext_entity_valid
    tbz  w0, #0, 4f
    slot_value x2, slot_destroy
    mov  x0, x19
    mov  x1, x24
    bl   ext_destroy
4:  str  xzr, [x21, #0x38]
    add  x0, x21, #0x28
    mov  x1, x23
    ldr  x2, [sp, #0x40]
    mov  x3, xzr
    bl   ext_init_slot
    mov  x0, x19
    mov  x1, x20
    mov  x2, x21
    mov  x3, xzr
    bl   ext_prewarm
    mov  x0, x19
    mov  x1, x20
    mov  x2, x21
    ldr  w3, [x21, #0xc]
    mov  x4, xzr
    bl   ext_switch_to_weapon
    mov  x0, x19
    ldr  x1, [x21, #0x38]
    ldr  w2, [sp, #0x48]
    bl   ext_dm_set_ammo
    adr  x0, log_swap
    bl   journal_log
9:  ldp  x19, x20, [sp, #0x10]
    ldp  x21, x22, [sp, #0x20]
    ldp  x23, x24, [sp, #0x30]
    ldp  x29, x30, [sp], #0x60
    ret
.globl _dw_button
_dw_button:
    stp  x29, x30, [sp, #-0x20]!
    str  x19, [sp, #0x10]
    mov  x19, x0
    cbz  x0, 1f
    ldr  w8, [x0, #0x10]
    cmp  w8, #5
    b.ne 1f
    ldr  x8, [x0, #0x14]
    ldr  x9, name_arme2
    cmp  x8, x9
    b.ne 1f
    ldrh w8, [x0, #0x1c]
    cmp  w8, #'2'
    b.ne 1f
    bl   send_swap
1:  mov  x0, x19
    ldr  x19, [sp, #0x10]
    ldp  x29, x30, [sp], #0x20
    b    ext_set_button_down
send_swap:
    stp  x29, x30, [sp, #-0x30]!
    stp  x19, x20, [sp, #0x10]
    slot_value x0, slot_qm
    ldr  w8, [x0, #0xe4]
    cbnz w8, 1f
    bl   ext_class_init
1:  mov  x0, xzr
    bl   ext_main_game
    cbz  x0, 9f
    mov  x19, x0
    ldr  x8, [x19, #0x38]
    cbz  x8, 9f
    ldr  x20, [x8, #0x18]
    cbz  x20, 9f
    mov  x0, x19
    mov  x1, x20
    mov  x2, xzr
    bl   ext_local_player
    str  x0, [sp, #0x20]
    slot_value x0, slot_cmd
    bl   ext_object_new
    cbz  x0, 9f
    mov  x20, x0
    mov  x1, xzr
    bl   ext_cmd_ctor
    ldr  x8, [sp, #0x20]
    str  x8, [x20, #0x28]
    mov  w8, #SWAP
    str  w8, [x20, #0x30]
    mov  x0, x19
    mov  x1, x20
    mov  x2, xzr
    bl   ext_send_command
    adr  x0, log_send
    bl   journal_log
9:  ldp  x19, x20, [sp, #0x10]
    ldp  x29, x30, [sp], #0x30
    ret
    .p2align 3
name_arme2:  .short 'A', 'r', 'm', 'e'
s_option:  .asciz "rr_deux_armes"
s_second:  .asciz "rr_v99"
s_slot2:   .asciz "LoadoutSlotWidget_2"
s_slot_widget: .asciz "WeaponLoadoutSlotWidget"
s_log_slot: .asciz "RR deux armes: case 3 creee"
log_load:  .asciz "RR deux armes: seconde chargee"
log_send:  .asciz "RR deux armes: echange envoye"
log_swap:  .asciz "RR deux armes: echange fait"
    .p2align 2
column_two:   .float 1.25, -334.2
column_three: .float 1.0, -228.7
journal:   .word 0
shown:     .word 0
