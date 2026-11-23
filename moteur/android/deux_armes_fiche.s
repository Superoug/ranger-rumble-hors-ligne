.text
.globl _df_start
_df_start:
    ret
.globl _df_refresh
_df_refresh:
    stp  x29, x30, [sp, #-0x70]!
    stp  x19, x20, [sp, #0x10]
    stp  x21, x22, [sp, #0x20]
    stp  x23, x24, [sp, #0x30]
    stp  x25, x26, [sp, #0x40]
    str  d8, [sp, #0x60]
    mov  x19, x0
    bl   refresh_raw
    bl   ext_dw_second
    mov  w22, w0
    mov  x0, x19
    mov  x1, xzr
    bl   ext_get_transform
    cbz  x0, 9f
    mov  x20, x0
    mov  x1, xzr
    bl   ext_get_parent
    cbz  x0, 9f
    mov  x21, x0
    adr  x0, s_column
    bl   ext_string_new
    mov  x1, x0
    mov  x0, x20
    mov  x2, xzr
    bl   ext_find
    mov  x25, x0
    cbnz x25, 1f
    mov  x0, x21
    mov  x1, xzr
    bl   ext_get_anchored
    movi d1, #0
    cbz  w22, 2f
    ldr  s1, list_up
2:  mov  x0, x21
    mov  x1, xzr
    bl   ext_set_anchored
    b    3f
1:  mov  x0, x21
    mov  x1, xzr
    bl   ext_get_size
    adr  x8, grid_three
    cbz  w22, 2f
    adr  x8, grid_four
2:  ldr  s0, [x8]
    ldr  s8, [x8, #4]
    mov  x0, x21
    mov  x1, xzr
    bl   ext_set_size
    fmov s0, s8
    fmov s1, s8
    fmov s2, #1.0
    mov  x0, x21
    mov  x1, xzr
    bl   ext_set_scale
3:  adr  x0, s_copy
    bl   ext_string_new
    mov  x1, x0
    mov  x0, x21
    mov  x2, xzr
    bl   ext_find
    mov  x23, x0
    cbnz x23, 4f
    cbz  w22, 9f
    mov  x0, x19
    mov  x1, xzr
    bl   ext_get_gameobject
    cbz  x0, 9f
    mov  x1, x21
    mov  x2, xzr
    bl   ext_instantiate
    cbz  x0, 9f
    mov  x24, x0
    adr  x0, s_copy
    bl   ext_string_new
    mov  x1, x0
    mov  x0, x24
    mov  x2, xzr
    bl   ext_set_name
    mov  x0, x24
    mov  x1, xzr
    bl   ext_go_transform
    cbz  x0, 9f
    mov  x23, x0
    mov  x0, x20
    mov  x1, xzr
    bl   ext_get_sibling
    add  w1, w0, #1
    mov  x0, x23
    mov  x2, xzr
    bl   ext_set_sibling
    cbnz x25, 4f
    mov  x0, x23
    mov  x1, xzr
    bl   ext_get_size
    ldr  s1, copy_height
    mov  x0, x23
    mov  x1, xzr
    bl   ext_set_size
4:  mov  x26, x23
    mov  x0, x23
    mov  x1, xzr
    bl   ext_get_gameobject
    cbz  x0, 9f
    mov  x24, x0
    cmp  w22, #0
    cset w1, ne
    mov  x2, xzr
    bl   ext_set_active
    cbz  w22, 9f
    adr  x0, s_widget
    bl   ext_string_new
    mov  x1, x0
    mov  x0, x24
    mov  x2, xzr
    bl   ext_component_by_name
    cbz  x0, 9f
    mov  x23, x0
    ldr  w8, [x19, #0x20]
    str  w8, [x23, #0x20]
    mov  x0, xzr
    bl   ext_weapon_table
    cbz  x0, 9f
    mov  w1, w22
    mov  x2, xzr
    bl   ext_weapon_spec
    cbz  x0, 9f
    mov  x24, x0
    ldr  x0, [x23, #0x28]
    cbz  x0, 5f
    ldr  x1, [x24, #0x100]
    mov  x2, xzr
    bl   ext_set_sprite
5:  ldr  q0, [x24, #0x20]
    str  q0, [sp, #0x50]
    add  x0, sp, #0x50
    mov  x1, xzr
    bl   ext_loc_text
    ldr  x8, [x23, #0x30]
    cbz  x8, 6f
    mov  x1, x0
    mov  x0, x8
    ldr  x8, [x0]
    ldr  x9, [x8, #0x558]
    ldr  x2, [x8, #0x560]
    blr  x9
6:  cbz  x25, 9f
    adr  x0, s_cards
    bl   ext_string_new
    mov  x1, x0
    mov  x0, x26
    mov  x2, xzr
    bl   ext_find
    cbz  x0, 9f
    mov  x24, x0
    mov  w1, #1
    bl   set_flag
    adr  x0, s_card_0
    bl   refresh_card
    adr  x0, s_card_1
    bl   refresh_card
    mov  w1, #0
    bl   set_flag
9:  ldr  d8, [sp, #0x60]
    ldp  x25, x26, [sp, #0x40]
    ldp  x23, x24, [sp, #0x30]
    ldp  x21, x22, [sp, #0x20]
    ldp  x19, x20, [sp, #0x10]
    ldp  x29, x30, [sp], #0x70
    ret
refresh_raw:
    sub  sp, sp, #0x40
    b    ext_refresh_body
refresh_card:
    stp  x29, x30, [sp, #-0x20]!
    str  x20, [sp, #0x10]
    bl   ext_string_new
    mov  x1, x0
    mov  x0, x24
    mov  x2, xzr
    bl   ext_find
    cbz  x0, 9f
    mov  x1, xzr
    bl   ext_get_gameobject
    cbz  x0, 9f
    mov  x20, x0
    adr  x0, s_power
    bl   ext_string_new
    mov  x1, x0
    mov  x0, x20
    mov  x2, xzr
    bl   ext_component_by_name
    cbnz x0, 1f
    adr  x0, s_damage
    bl   ext_string_new
    mov  x1, x0
    mov  x0, x20
    mov  x2, xzr
    bl   ext_component_by_name
    cbz  x0, 9f
1:  ldr  w8, [x19, #0x20]
    str  w8, [x0, #0x20]
    ldr  x8, [x0]
    ldp  x9, x1, [x8, #0x1b8]
    blr  x9
9:  ldr  x20, [sp, #0x10]
    ldp  x29, x30, [sp], #0x20
    ret
set_flag:
    stp  x29, x30, [sp, #-0x20]!
    str  w1, [sp, #0x10]
    adr  x0, s_flag
    bl   ext_string_new
    ldr  w1, [sp, #0x10]
    mov  x2, xzr
    bl   ext_set_int
    ldp  x29, x30, [sp], #0x20
    ret
s_copy:    .asciz "Weapon2"
s_column:  .asciz "ContentMelee"
s_cards:   .asciz "ContentMelee/Content/MeleeTitle/StatGrid"
s_card_0:  .asciz "WeaponStatWidget"
s_card_1:  .asciz "WeaponStatWidget (1)"
s_widget:  .asciz "HeroWeaponInfoUIWidget"
s_power:   .asciz "HeroWeaponPowerStatUIWidget"
s_damage:  .asciz "HeroWeaponDamageStatUIWidget"
s_flag:    .asciz "rr_s99"
    .p2align 2
list_up:     .float 40.0
copy_height: .float 100.0
grid_three:  .float 1500.0, 1.0
grid_four:   .float 2000.0, 0.75
.globl _df_end
_df_end:
