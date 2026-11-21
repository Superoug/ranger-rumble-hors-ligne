.text
.equ GADGET_COUNT, 12
.equ ALL_HEROES, 99
.equ RATCHET_BLASTER, 54
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
.globl _ws_start
_ws_start:
make_key:
    stp  x29, x30, [sp, #-0x20]!
    mov  w8, #'r'
    strb w8, [sp, #0x10]
    strb w8, [sp, #0x11]
    mov  w8, #'_'
    strb w8, [sp, #0x12]
    strb w0, [sp, #0x13]
    mov  w9, #10
    udiv w10, w1, w9
    msub w11, w10, w9, w1
    add  w10, w10, #'0'
    add  w11, w11, #'0'
    strb w10, [sp, #0x14]
    strb w11, [sp, #0x15]
    strb wzr, [sp, #0x16]
    add  x0, sp, #0x10
    bl   ext_string_new
    ldp  x29, x30, [sp], #0x20
    ret
get_pref:
    stp  x29, x30, [sp, #-0x20]!
    str  x19, [sp, #0x10]
    mov  w19, w2
    bl   make_key
    mov  w1, w19
    mov  x2, xzr
    bl   ext_get_int
    ldr  x19, [sp, #0x10]
    ldp  x29, x30, [sp], #0x20
    ret
set_pref:
    stp  x29, x30, [sp, #-0x20]!
    str  x19, [sp, #0x10]
    mov  w19, w2
    bl   make_key
    mov  w1, w19
    mov  x2, xzr
    bl   ext_set_int
    mov  x0, xzr
    bl   ext_save
    ldr  x19, [sp, #0x10]
    ldp  x29, x30, [sp], #0x20
    ret
filter_key:
    stp  x29, x30, [sp, #-0x20]!
    str  x19, [sp, #0x10]
    adrp x0, slot_filter_key@PAGE
    ldr  x0, [x0, slot_filter_key@PAGEOFF]
    mov  x19, x0
    bl   ext_init_metadata
    ldr  x0, [x19]
    ldr  x19, [sp, #0x10]
    ldp  x29, x30, [sp], #0x20
    ret
secondary_mode:
    stp  x29, x30, [sp, #-0x10]!
    bl   filter_key
    mov  w1, #4
    mov  x2, xzr
    bl   ext_get_int
    cmp  w0, #0
    cset w0, eq
    ldp  x29, x30, [sp], #0x10
    ret
current_hero:
    stp  x29, x30, [sp, #-0x20]!
    mov  x0, xzr
    bl   ext_user_instance
    cbz  x0, 1f
    ldr  x8, [x0, #0x188]
    str  x8, [sp, #0x10]
    add  x0, sp, #0x10
    mov  w1, wzr
    mov  x2, xzr
    bl   ext_get_at_slot
    mov  x1, xzr
    bl   ext_char_of_skin
    ldp  x29, x30, [sp], #0x20
    ret
1:  mov  w0, #-1
    ldp  x29, x30, [sp], #0x20
    ret
gadget_index:
    adr  x9, gadget_ids
    mov  w10, #0
1:  ldr  w11, [x9, w10, uxtw #2]
    cmp  w11, w0
    b.eq 2f
    add  w10, w10, #1
    cmp  w10, #GADGET_COUNT
    b.lt 1b
    mov  w0, #-1
    ret
2:  mov  w0, w10
    ret
gadget_of_uid:
    stp  x29, x30, [sp, #-0x30]!
    stp  x19, x20, [sp, #0x10]
    str  x21, [sp, #0x20]
    mov  w19, w0
    mov  w20, #0
1:  adr  x9, gadget_ids
    ldr  w21, [x9, w20, uxtw #2]
    mov  w0, w21
    mov  x1, xzr
    bl   ext_weapon_uid
    cmp  w0, w19
    b.eq 2f
    add  w20, w20, #1
    cmp  w20, #GADGET_COUNT
    b.lt 1b
    mov  w21, #0
2:  mov  w0, w21
    ldr  x21, [sp, #0x20]
    ldp  x19, x20, [sp, #0x10]
    ldp  x29, x30, [sp], #0x30
    ret
apply_chardef:
    cbz  x0, 9f
    stp  x29, x30, [sp, #-0x20]!
    str  x19, [sp, #0x10]
    mov  x19, x0
    ldr  x8, [x19, #0x10]
    cbz  x8, 8f
    mov  w1, #ALL_HEROES
    mov  w0, #'g'
    mov  w2, #0
    bl   get_pref
    cbz  w0, 8f
    str  w0, [sp, #0x18]
    mov  x1, xzr
    bl   ext_weapon_uid
    mov  x1, xzr
    bl   ext_weapon_is_unlocked
    tbz  w0, #0, 8f
    ldr  w0, [sp, #0x18]
    bl   gadget_index
    tbnz w0, #31, 8f
    add  w9, w0, #1
    ldr  x10, [x19, #0x58]
    cbz  x10, 8f
    ldr  w11, [x10, #0x18]
    cmp  w9, w11
    b.ge 8f
    ldr  x12, [x10, #0x10]
    cbz  x12, 8f
    add  x12, x12, #0x20
    ldr  x13, [x12, w9, uxtw #3]
    str  x13, [x12]
8:  ldr  x19, [sp, #0x10]
    ldp  x29, x30, [sp], #0x20
9:  ret
.globl _ws_loadout_gadget
_ws_loadout_gadget:
    save_all
    bl   apply_chardef
    restore_all
    mov  x22, x0
    ret
.globl _ws_sheet_gadget
_ws_sheet_gadget:
    save_all
    bl   apply_chardef
    restore_all
    ldr  x0, [x0, #0x58]
    ret
.globl _ws_sim_key
_ws_sim_key:
    save_all
    ldr  w9, [x19, #0xc]
    str  w9, [sp, #0x08]
    mov  x0, x19
    mov  x1, xzr
    bl   ext_is_human
    tbz  w0, #0, 1f
    mov  x0, x21
    ldr  w1, [x19, #0x34]
    mov  x2, xzr
    bl   ext_player_data
    cbz  x0, 1f
    ldr  w0, [x0, #0x50]
    bl   gadget_index
    tbnz w0, #31, 1f
    adr  x9, gadget_owners
    ldr  w9, [x9, w0, uxtw #2]
    str  w9, [sp, #0x08]
1:  restore_all
    ret
.globl _ws_ultimate_key
_ws_ultimate_key:
    save_all
    ldr  w9, [x19, #0xc]
    str  w9, [sp, #0x08]
    adr  x10, _ws_hero_ultimates
1:  ldrb w11, [x10], #2
    cbz  w11, 2f
    cmp  w11, w9
    b.ne 1b
    ldurb w9, [x10, #-1]
    str  w9, [sp, #0x08]
2:  restore_all
    ret
.globl _ws_hero_ultimates
_ws_hero_ultimates:
    .byte 16, 3, 18, 3, 23, 9, 12, 6, 11, 17, 13, 17, 21, 22, 20, 8, 19, 4, 0, 0
    .p2align 2
.globl _ws_equip_weapon
_ws_equip_weapon:
    stp  x29, x30, [sp, #-0x40]!
    stp  x19, x20, [sp, #0x10]
    stp  x21, x22, [sp, #0x20]
    str  x23, [sp, #0x30]
    mov  x19, x0
    mov  w20, w1
    mov  w21, w2
    mov  x22, x3
    cbnz w20, 5f
    bl   secondary_mode
    cbz  w0, 4f
    mov  w0, w21
    bl   gadget_of_uid
    cbz  w0, 4f
    mov  w23, w0
    mov  w0, w21
    mov  x1, xzr
    bl   ext_weapon_is_unlocked
    tbz  w0, #0, 7f
    bl   current_hero
    tbnz w0, #31, 3f
    mov  w1, #ALL_HEROES
    mov  w0, #'g'
    mov  w2, w23
    bl   set_pref
3:  cbz  x22, 2f
    ldr  x8, [x22, #0x18]
    ldr  x0, [x22, #0x40]
    mov  w1, #1
    ldr  x2, [x22, #0x28]
    blr  x8
2:  mov  w0, #1
    b    9f
7:  mov  w0, #0
    b    9f
4:  mov  x0, x19
    mov  w1, w20
    mov  w2, w21
    mov  x3, x22
    bl   equip_weapon_raw
    cbz  w0, 9f
    bl   current_hero
    tbnz w0, #31, 6f
    mov  w1, #ALL_HEROES
    mov  w0, #'w'
    mov  w2, w21
    bl   set_pref
6:  mov  w0, #1
    b    9f
5:  mov  x0, x19
    mov  w1, w20
    mov  w2, w21
    mov  x3, x22
    bl   equip_weapon_raw
9:  ldr  x23, [sp, #0x30]
    ldp  x21, x22, [sp, #0x20]
    ldp  x19, x20, [sp, #0x10]
    ldp  x29, x30, [sp], #0x40
    ret
equip_weapon_raw:
    sub  sp, sp, #0x40
    b    ext_equip_weapon_body
.globl _ws_equip_skin
_ws_equip_skin:
    stp  x29, x30, [sp, #-0x40]!
    stp  x19, x20, [sp, #0x10]
    stp  x21, x22, [sp, #0x20]
    str  x23, [sp, #0x30]
    mov  x19, x0
    mov  w20, w1
    mov  w21, w2
    mov  w23, #0
    cbnz w20, 1f
    mov  x0, xzr
    bl   ext_user_instance
    cbz  x0, 1f
    ldr  x8, [x0, #0x190]
    str  x8, [sp, #0x38]
    add  x0, sp, #0x38
    mov  w1, wzr
    mov  x2, xzr
    bl   ext_get_at_slot
    mov  w23, w0
1:  mov  x0, x19
    mov  w1, w20
    mov  w2, w21
    bl   equip_skin_raw
    mov  w22, w0
    cbz  w22, 9f
    cbnz w20, 9f
    mov  w0, w23
    cbz  w0, 9f
    mov  w2, w0
    mov  x0, x19
    mov  w1, wzr
    mov  x3, xzr
    bl   equip_weapon_raw
9:  mov  w0, w22
    ldr  x23, [sp, #0x30]
    ldp  x21, x22, [sp, #0x20]
    ldp  x19, x20, [sp, #0x10]
    ldp  x29, x30, [sp], #0x40
    ret
equip_skin_raw:
    sub  sp, sp, #0x40
    b    ext_equip_skin_body
main_weapon_test:
    stp  x29, x30, [sp, #-0x10]!
    cmp  w23, #RATCHET_BLASTER
    b.eq 8f
    mov  w0, w23
    bl   gadget_index
    tbz  w0, #31, 8f
    mov  x0, x20
    mov  w1, w23
    mov  x2, x22
    mov  x3, xzr
    bl   ext_is_available
    tbz  w0, #0, 8f
    mov  x0, x20
    mov  w1, w23
    mov  x2, xzr
    bl   ext_is_ultimate
    tbnz w0, #0, 8f
    mov  x0, x20
    mov  w1, w23
    mov  x2, xzr
    bl   ext_is_melee
    tbnz w0, #0, 8f
    mov  w0, #1
    b    9f
8:  mov  w0, #0
9:  ldp  x29, x30, [sp], #0x10
    ret
.globl _ws_slots_candidate
_ws_slots_candidate:
    stp  x29, x30, [sp, #-0x10]!
    bl   main_weapon_test
    cbnz w0, 1f
    mov  w0, w23
    bl   gadget_index
    cmp  w0, #0
    cset w0, ge
1:  ldp  x29, x30, [sp], #0x10
    ret
.globl _ws_slots_mode
_ws_slots_mode:
    stp  x29, x30, [sp, #-0x10]!
    bl   secondary_mode
    cbz  w0, 2f
    mov  w0, w23
    bl   gadget_index
    tbnz w0, #31, 8f
    b    7f
2:  bl   main_weapon_test
    cbz  w0, 8f
7:  ldp  x29, x30, [sp], #0x10
    cbz  x26, 6f
    b    ext_slots_create
6:  b    ext_slots_null
8:  ldp  x29, x30, [sp], #0x10
    b    ext_slots_next
.globl _ws_filter_changed
_ws_filter_changed:
    ldr  x0, [x22]
    mov  x21, x0
    mov  w1, #4
    mov  x2, xzr
    bl   ext_get_int
    mov  w22, w0
    mov  x0, x21
    mov  w1, w19
    mov  x2, xzr
    bl   ext_set_int
    cmp  w22, #0
    cset w8, eq
    cmp  w19, #0
    cset w9, eq
    mov  x0, x20
    mov  w1, w19
    ldp  x20, x19, [sp, #0x20]
    ldp  x22, x21, [sp, #0x10]
    ldr  x30, [sp], #0x30
    cmp  w8, w9
    b.eq 1f
    b    ext_create_slots
1:  b    ext_refresh_slots
.globl _ws_open_primary
_ws_open_primary:
    mov  w9, #4
    b    open_arsenal
.globl _ws_open_secondary
_ws_open_secondary:
    mov  w9, #0
open_arsenal:
    stp  x29, x30, [sp, #-0x30]!
    stp  x19, x20, [sp, #0x10]
    str  x21, [sp, #0x20]
    mov  x19, x0
    mov  w20, w9
    mov  x0, xzr
    bl   ext_user_instance
    cbz  x0, 2f
    mov  x21, x0
    ldr  w1, [x19, #0x20]
    mov  x2, xzr
    bl   ext_can_equip_skin
    cbz  w0, 2f
    mov  x0, x21
    mov  w1, wzr
    ldr  w2, [x19, #0x20]
    mov  x3, xzr
    bl   ext_equip_skin
2:  bl   filter_key
    mov  x21, x0
    mov  w1, w20
    cbz  w20, 4f
    mov  w1, #4
    mov  x2, xzr
    bl   ext_get_int
    cbnz w0, 5f
    mov  w1, #4
4:  mov  x0, x21
    mov  x2, xzr
    bl   ext_set_int
    mov  x0, xzr
    bl   ext_save
5:  mov  x0, xzr
    bl   ext_fsm_instance
    cbz  x0, 8f
    ldr  x8, [x0]
    mov  w1, #5
    mov  w2, wzr
    mov  w3, #1
    ldp  x5, x4, [x8, #0x1c8]
    ldr  x21, [sp, #0x20]
    ldp  x19, x20, [sp, #0x10]
    ldp  x29, x30, [sp], #0x30
    br   x5
8:  ldr  x21, [sp, #0x20]
    ldp  x19, x20, [sp, #0x10]
    ldp  x29, x30, [sp], #0x30
    ret
secondary_weapon:
    stp  x29, x30, [sp, #-0x20]!
    str  x19, [sp, #0x10]
    mov  x0, xzr
    bl   ext_user_instance
    cbz  x0, 8f
    ldr  x8, [x0, #0x188]
    str  x8, [sp, #0x18]
    add  x0, sp, #0x18
    mov  w1, wzr
    mov  x2, xzr
    bl   ext_get_at_slot
    mov  w19, w0
    mov  x0, xzr
    bl   ext_get_economy
    cbz  x0, 8f
    ldr  x0, [x0, #0x20]
    cbz  x0, 8f
    mov  w1, w19
    mov  x2, xzr
    bl   ext_char_def_by_skin
    cbz  x0, 8f
    mov  x19, x0
    bl   apply_chardef
    ldr  x10, [x19, #0x58]
    cbz  x10, 8f
    ldr  w11, [x10, #0x18]
    ldr  x12, [x10, #0x10]
    cbz  x12, 8f
    add  x12, x12, #0x20
    ldr  x13, [x12]
    cbz  x13, 8f
    mov  w9, #0
1:  add  w14, w9, #1
    cmp  w14, w11
    b.ge 8f
    ldr  x15, [x12, w14, uxtw #3]
    cmp  x15, x13
    b.eq 2f
    add  w9, w9, #1
    cmp  w9, #GADGET_COUNT
    b.lt 1b
8:  mov  w0, #0
    b    9f
2:  adr  x10, gadget_ids
    ldr  w0, [x10, w9, uxtw #2]
9:  ldr  x19, [sp, #0x10]
    ldp  x29, x30, [sp], #0x20
    ret
.globl _ws_slot_refresh
_ws_slot_refresh:
    ldr  w8, [x0, #0x58]
    cmp  w8, #1
    b.ne 1f
    stp  x29, x30, [sp, #-0x20]!
    str  x19, [sp, #0x10]
    mov  x19, x0
    bl   secondary_weapon
    mov  w1, w0
    mov  x0, x19
    mov  x2, xzr
    ldr  x19, [sp, #0x10]
    ldp  x29, x30, [sp], #0x20
    b    ext_bin_weapon
1:  str  x30, [sp, #-0x40]!
    b    ext_refresh_body
slot_glow:
    stp  x29, x30, [sp, #-0x30]!
    stp  x19, x20, [sp, #0x10]
    str  x21, [sp, #0x20]
    mov  x19, x0
    mov  w20, #1
    adrp x0, slot_main_menu@PAGE
    ldr  x0, [x0, slot_main_menu@PAGEOFF]
    mov  x21, x0
    bl   ext_init_metadata
    ldr  x0, [x21]
    bl   ext_mono_instance
    cbz  x0, 9f
    ldr  x0, [x0, #0x1e0]
    cbz  x0, 9f
    ldr  x8, [x0, #0x50]
    cbz  x8, 9f
    ldrsw x9, [x19, #0x58]
    ldr  w10, [x8, #0x18]
    cmp  w9, w10
    b.hs 9f
    add  x8, x8, #0x20
    ldr  x21, [x8, x9, lsl #3]
    cbz  x21, 9f
    adrp x0, slot_highlight_name@PAGE
    ldr  x0, [x0, slot_highlight_name@PAGEOFF]
    mov  x19, x0
    bl   ext_init_metadata
    ldr  x1, [x19]
    mov  x0, x21
    mov  w2, w20
    mov  x3, xzr
    bl   ext_animator_set_bool
9:  ldr  x21, [sp, #0x20]
    ldp  x19, x20, [sp, #0x10]
    ldp  x29, x30, [sp], #0x30
    ret
.globl _ws_slot_refresh_if
_ws_slot_refresh_if:
    stp  x29, x30, [sp, #-0x20]!
    str  x19, [sp, #0x10]
    mov  x19, x0
    bl   slot_glow
    ldr  w8, [x19, #0x58]
    cmp  w8, #1
    b.ne 2f
    bl   secondary_weapon
    ldr  w8, [x19, #0x98]
    cmp  w8, w0
    b.eq 1f
    mov  w1, w0
    mov  x0, x19
    mov  x2, xzr
    ldr  x19, [sp, #0x10]
    ldp  x29, x30, [sp], #0x20
    b    ext_bin_weapon
1:  ldr  x19, [sp, #0x10]
    ldp  x29, x30, [sp], #0x20
    ret
2:  mov  x0, x19
    ldr  x19, [sp, #0x10]
    ldp  x29, x30, [sp], #0x20
    stp  x30, x21, [sp, #-0x20]!
    b    ext_refresh_if_body
.globl _ws_slot_clicked
_ws_slot_clicked:
    stp  x29, x30, [sp, #-0x30]!
    stp  x19, x20, [sp, #0x10]
    str  x21, [sp, #0x20]
    mov  x19, x0
    bl   ext_loadout_screen
    cbz  x0, 7f
    mov  x20, x0
    mov  w1, #1
    mov  x2, xzr
    bl   ext_loadout_in_state
    tbz  w0, #0, 7f
    ldr  w8, [x19, #0x58]
    mov  w21, #0
    cbnz w8, 4f
    bl   secondary_mode
    cbz  w0, 6f
    mov  w21, #4
4:  ldr  x0, [x20, #0x88]
    cbz  x0, 6f
    mov  w1, w21
    mov  x2, xzr
    bl   ext_dropdown_set_value
6:  ldr  x21, [sp, #0x20]
    ldp  x19, x20, [sp, #0x10]
    ldp  x29, x30, [sp], #0x30
    ret
7:  ldr  w8, [x19, #0x58]
    mov  w21, #0
    cbnz w8, 5f
    bl   secondary_mode
    cbz  w0, 8f
    mov  w21, #4
5:  bl   filter_key
    mov  w1, w21
    mov  x2, xzr
    bl   ext_set_int
    mov  x0, xzr
    bl   ext_save
8:  mov  x0, x19
    ldr  x21, [sp, #0x20]
    ldp  x19, x20, [sp, #0x10]
    ldp  x29, x30, [sp], #0x30
    sub  sp, sp, #0x60
    b    ext_slot_clicked_body
.globl _ws_plan_targets
_ws_plan_targets:
    stp  x29, x30, [sp, #-0x30]!
    stp  x19, x20, [sp, #0x10]
    mov  w19, #0
    mov  w20, #0
    mov  x0, xzr
    bl   ext_user_instance
    cbz  x0, 1f
    ldr  x8, [x0, #0x190]
    str  x8, [sp, #0x20]
    add  x0, sp, #0x20
    mov  w1, wzr
    mov  x2, xzr
    bl   ext_get_at_slot
    mov  w19, w0
1:  mov  w0, #'g'
    mov  w1, #ALL_HEROES
    mov  w2, #0
    bl   get_pref
    cbnz w0, 4f
    bl   current_hero
    tbnz w0, #31, 5f
    adr  x9, gadget_owners
    mov  w10, #0
2:  ldr  w11, [x9, w10, uxtw #2]
    cmp  w11, w0
    b.eq 3f
    add  w10, w10, #1
    cmp  w10, #GADGET_COUNT
    b.lt 2b
    b    5f
3:  adr  x9, gadget_ids
    ldr  w0, [x9, w10, uxtw #2]
4:  mov  x1, xzr
    bl   ext_weapon_uid
    mov  w20, w0
5:  mov  w0, w19
    mov  w1, w20
    ldp  x19, x20, [sp, #0x10]
    ldp  x29, x30, [sp], #0x30
    ret
    .p2align 2
.globl _ws_shown_weapon
_ws_shown_weapon:
    stp  x29, x30, [sp, #-0x20]!
    str  x19, [sp, #0x10]
    mov  x1, xzr
    bl   ext_default_weapon_uid
    mov  w19, w0
    mov  x0, xzr
    bl   ext_user_instance
    cbz  x0, 1f
    ldr  x8, [x0, #0x190]
    str  x8, [sp, #0x18]
    add  x0, sp, #0x18
    mov  w1, wzr
    mov  x2, xzr
    bl   ext_get_at_slot
    cbz  w0, 1f
    mov  w19, w0
1:  mov  w0, w19
    ldr  x19, [sp, #0x10]
    ldp  x29, x30, [sp], #0x20
    ret
popup_levels:
    stp  x29, x30, [sp, #-0x40]!
    stp  x19, x20, [sp, #0x10]
    stp  x21, x22, [sp, #0x20]
    str  x23, [sp, #0x30]
    ldr  w19, [x0, #0x20]
    mov  w20, w1
    mov  x0, xzr
    bl   ext_get_economy
    cbz  x0, 8f
    ldr  x0, [x0, #0x20]
    cbz  x0, 8f
    mov  w1, w19
    mov  x2, xzr
    bl   ext_char_def_by_id
    cbz  x0, 8f
    mov  x21, x0
    mov  x1, xzr
    bl   ext_default_weapon_uid
    mov  w23, w0
    mov  x0, x21
    bl   _ws_shown_weapon
    mov  w22, w0
    mov  x1, xzr
    bl   ext_weapon_upgrade_qlevel
    mov  w21, w0
    mov  w1, w0
    cmp  w22, w23
    b.ne 9f
    mov  w0, w20
    mov  x1, xzr
    bl   ext_weapon_qlevel
    cmp  w21, w0
    csel w19, w21, w0, gt
    add  w0, w20, #1
    mov  x1, xzr
    bl   ext_weapon_qlevel
    cmp  w21, w0
    csel w1, w21, w0, gt
    mov  w0, w19
    b    7f
8:  mov  w0, w20
    add  w1, w20, #1
    b    7f
9:  mov  w0, w21
7:  ldr  x23, [sp, #0x30]
    ldp  x21, x22, [sp, #0x20]
    ldp  x19, x20, [sp, #0x10]
    ldp  x29, x30, [sp], #0x40
    ret
.globl _ws_popup_weapon_power
_ws_popup_weapon_power:
    adr  x9, weapon_power_raw
    b    popup_stat
.globl _ws_popup_weapon_damage
_ws_popup_weapon_damage:
    adr  x9, weapon_damage_raw
popup_stat:
    stp  x29, x30, [sp, #-0x40]!
    stp  x19, x20, [sp, #0x10]
    stp  x21, x22, [sp, #0x20]
    str  x23, [sp, #0x30]
    mov  x19, x0
    mov  x20, x2
    mov  x21, x3
    mov  x23, x9
    bl   popup_levels
    mov  w22, w1
    mov  w1, w0
    mov  x0, x19
    mov  x2, x20
    add  x3, sp, #0x38
    blr  x23
    mov  x0, x19
    mov  w1, w22
    mov  x2, x21
    add  x3, sp, #0x38
    blr  x23
    ldr  x23, [sp, #0x30]
    ldp  x21, x22, [sp, #0x20]
    ldp  x19, x20, [sp, #0x10]
    ldp  x29, x30, [sp], #0x40
    ret
weapon_power_raw:
    stp  x30, x23, [sp, #-0x30]!
    b    ext_weapon_power_body
weapon_damage_raw:
    sub  sp, sp, #0x70
    b    ext_weapon_damage_body
.globl _ws_gadget_level
_ws_gadget_level:
    mov  x9, sp
    save_all
    ldr  w10, [x19, #0x18]
    str  w10, [x9]
    mov  x0, x19
    mov  x1, xzr
    bl   ext_is_human
    tbz  w0, #0, 1f
    mov  x0, x21
    ldr  w1, [x19, #0x34]
    mov  x2, xzr
    bl   ext_player_data
    cbz  x0, 1f
    ldrb w10, [x0, #0x4d]
    ldr  x9, [sp, #0x48]
    str  w10, [x9]
1:  restore_all
    add  x21, sp, #0x18
    ret
gadget_ui_level:
    stp  x29, x30, [sp, #-0x30]!
    stp  x19, x20, [sp, #0x10]
    str  x21, [sp, #0x20]
    mov  w19, w0
    mov  w20, w1
    mov  x0, xzr
    bl   ext_get_economy
    cbz  x0, 9f
    ldr  x21, [x0, #0x20]
    cbz  x21, 9f
    mov  x0, x21
    mov  w1, w19
    mov  x2, xzr
    bl   ext_char_def_by_id
    cbz  x0, 9f
    bl   apply_chardef
    mov  x0, x21
    mov  w1, wzr
    mov  w2, w19
    mov  x3, xzr
    bl   ext_gadget_weapon_at
    cbz  w0, 9f
    mov  x1, xzr
    bl   ext_weapon_uid
    cbz  w0, 9f
    mov  x1, xzr
    bl   ext_weapon_upgrade_qlevel
    mov  w20, w0
9:  mov  w0, w20
    ldr  x21, [sp, #0x20]
    ldp  x19, x20, [sp, #0x10]
    ldp  x29, x30, [sp], #0x30
    ret
.globl _ws_gadget_power_level
_ws_gadget_power_level:
    save_all
    ldr  w0, [x0, #0x20]
    bl   gadget_ui_level
    mov  w20, w0
    restore_all
    ret
.globl _ws_gadget_cooldown_level
_ws_gadget_cooldown_level:
    save_all
    mov  w1, w0
    ldr  w0, [x19, #0x20]
    bl   gadget_ui_level
    mov  w20, w0
    restore_all
    ret
.globl _ws_gadget_ids
_ws_gadget_ids:
gadget_ids:
    .word 51, 52, 53, 41, 10, 3, 26, 6, 16, 22, 23, 56
gadget_owners:
    .word 2, 3, 4, 5, 6, 8, 9, 10, 14, 15, 17, 22
.globl _ws_end
_ws_end:
