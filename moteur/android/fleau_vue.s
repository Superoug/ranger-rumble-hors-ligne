.text
.globl _flail_view
_flail_view:
    sub  sp, sp, #0xc0
    stp  x0, x1, [sp, #0x50]
    stp  x19, x20, [sp, #0x60]
    stp  x21, x22, [sp, #0x70]
    stp  x23, x24, [sp, #0x80]
    stp  x25, x26, [sp, #0x90]
    stp  x29, x30, [sp, #0xa0]
    stp  d8, d9, [sp, #0xb0]
    mov  x19, x0
    ldr  x8, [x19, #0x20]
    ldr  x9, weapon_guid
    cmp  x8, x9
    b.ne out
    mov  x0, x19
    mov  x1, xzr
    bl   ext_get_transform
    cbz  x0, out
    mov  x20, x0
    adr  x0, s_trail
    bl   ext_string_new
    mov  x1, x0
    mov  x0, x20
    mov  x2, xzr
    bl   ext_find
    cbz  x0, out
    mov  x1, xzr
    bl   ext_get_gameobject
    cbz  x0, out
    mov  x21, x0
    adr  x0, s_line
    bl   ext_string_new
    mov  x1, x0
    mov  x0, x21
    mov  x2, xzr
    bl   ext_get_component_by_name
    cbz  x0, out
    mov  x21, x0
    adr  x0, s_ball
    bl   ext_string_new
    mov  x1, x0
    mov  x0, x20
    mov  x2, xzr
    bl   ext_find
    mov  x22, x0
    adr  x0, s_origin
    bl   ext_string_new
    mov  x1, x0
    mov  x0, x20
    mov  x2, xzr
    bl   ext_find
    cbnz x0, have_origin
    mov  x0, x20
have_origin:
    mov  x1, xzr
    bl   ext_get_position
    stp  s0, s1, [sp, #0x10]
    str  s2, [sp, #0x18]
    mov  x0, xzr
    bl   ext_observed_game
    cbz  x0, hide
    ldr  x0, [x0, #0x38]
    cbz  x0, hide
    ldr  x23, [x0, #0x18]
    cbz  x23, hide
    adrp x0, slot@PAGE
    ldr  x0, [x0, slot@PAGEOFF]
    bl   ext_init_metadata
    adrp x8, slot@PAGE
    ldr  x8, [x8, slot@PAGEOFF]
    ldr  x24, [x8]
    ldr  x8, [x24, #0x38]
    cbnz x8, rgctx_ready
    mov  x0, x24
    bl   ext_init_rgctx
rgctx_ready:
    ldr  x8, [x24, #0x38]
    ldr  x3, [x8, #8]
    ldr  x0, [x23, #0xa0]
    cbz  x0, hide
    ldr  x1, [x19, #0x28]
    str  xzr, [sp, #0x30]
    add  x2, sp, #0x30
    bl   ext_try_get_pointer
    tbz  w0, #0, hide
    ldr  x25, [sp, #0x30]
    cbz  x25, hide
    str  x25, [sp, #0x40]
    ldr  x24, [x25, #0x68]
    bl   valid
    cbz  w0, not_thrown
    mov  x0, x24
    mov  x1, xzr
    bl   ext_get_entity_view
    cbz  x0, hide
    mov  x1, xzr
    bl   ext_get_transform
    cbz  x0, hide
    mov  x1, xzr
    bl   ext_get_position
    stp  s0, s1, [sp, #0x20]
    str  s2, [sp, #0x28]
    mov  x0, x19
    mov  w1, #0
    bl   ext_flail_spin_anim
    mov  w26, #0
    b    draw
not_thrown:
    ldr  x24, [x25, #0x58]
    bl   valid
    mov  w26, w0
    mov  x0, x19
    mov  w1, w26
    bl   ext_flail_spin_anim
    cbz  w26, hide
    mov  x0, x24
    mov  x1, xzr
    bl   ext_get_entity_view
    cbz  x0, hide
    mov  x1, xzr
    bl   ext_get_transform
    cbz  x0, hide
    mov  x1, xzr
    bl   ext_get_position
    stp  s0, s1, [sp, #0x20]
    str  s2, [sp, #0x28]
    ldr  s0, spin_radius
    str  s0, [sp, #0x38]
    adrp x0, slot_aoe@PAGE
    ldr  x0, [x0, slot_aoe@PAGEOFF]
    bl   ext_init_metadata
    adrp x8, slot_aoe@PAGE
    ldr  x8, [x8, slot_aoe@PAGEOFF]
    ldr  x25, [x8]
    ldr  x8, [x25, #0x38]
    cbnz x8, aoe_rgctx_ready
    mov  x0, x25
    bl   ext_init_rgctx
aoe_rgctx_ready:
    ldr  x8, [x25, #0x38]
    ldr  x3, [x8, #8]
    ldr  x0, [x23, #0xa0]
    mov  x1, x24
    add  x2, sp, #0x30
    str  xzr, [x2]
    bl   ext_try_get_pointer
    tbz  w0, #0, orbit
    ldr  x8, [sp, #0x30]
    cbz  x8, orbit
    ldr  x8, [x8, #0x40]
    scvtf s1, x8, #16
    ldr  s0, [sp, #0x38]
    fmul s0, s0, s1
    str  s0, [sp, #0x38]
orbit:
    ldr  x8, [sp, #0x40]
    ldr  w9, [x8]
    ldr  w10, [x23, #0x1c]
    sub  w9, w10, w9
    str  w9, [sp, #0x3c]
    ldr  x8, [x23]
    ldr  x9, [x8, #0x248]
    ldr  x1, [x8, #0x250]
    mov  x0, x23
    blr  x9
    ldrsw x9, [sp, #0x3c]
    mul  x9, x9, x0
    ldr  x10, spin_up
    subs x9, x9, x10
    csel x9, xzr, x9, lt
    mov  x10, #5
    mul  x9, x9, x10
    mov  x10, #0x10000
    cmp  x9, x10
    csel x9, x9, x10, lt
    scvtf s1, x9, #16
    ldr  s0, [sp, #0x38]
    fmul s0, s0, s1
    str  s0, [sp, #0x38]
    mov  x0, xzr
    bl   ext_time
    ldr  s1, spin_speed
    fmul s8, s0, s1
    fmov s0, s8
    mov  x0, xzr
    bl   ext_cos
    fmov s9, s0
    fmov s0, s8
    mov  x0, xzr
    bl   ext_sin
    str  s0, [sp, #0x48]
    str  wzr, [sp, #0x4c]
    mov  x0, xzr
    bl   ext_camera_main
    cbz  x0, ring
    mov  x1, xzr
    bl   ext_get_transform
    cbz  x0, ring
    mov  x1, xzr
    bl   ext_get_position
    ldr  s3, [sp, #0x20]
    ldr  s4, [sp, #0x28]
    fsub s0, s0, s3
    fsub s2, s2, s4
    fmul s5, s0, s0
    fmadd s5, s2, s2, s5
    fsqrt s5, s5
    ldr  s1, min_distance
    fcmp s5, s1
    b.lt ring
    fdiv s0, s0, s5
    fdiv s2, s2, s5
    ldr  s6, [sp, #0x48]
    fmul s7, s9, s0
    fmadd s7, s6, s2, s7
    fmov s1, wzr
    fmax s7, s7, s1
    fmul s7, s7, s7
    ldr  s1, camera_lift
    fmul s1, s1, s7
    str  s1, [sp, #0x4c]
    ldr  s1, camera_cut
    fmul s7, s7, s1
    fmov s1, #1.0
    fsub s7, s1, s7
    ldr  s1, [sp, #0x38]
    fmul s1, s1, s7
    str  s1, [sp, #0x38]
ring:
    ldr  s0, [sp, #0x48]
    ldr  s2, [sp, #0x38]
    fmul s0, s0, s2
    fmul s9, s9, s2
    ldp  s3, s4, [sp, #0x20]
    fadd s3, s3, s9
    ldr  s1, [sp, #0x4c]
    fadd s4, s4, s1
    ldr  s5, [sp, #0x28]
    fadd s5, s5, s0
    stp  s3, s4, [sp, #0x20]
    str  s5, [sp, #0x28]
    mov  w26, #2
draw:
    mov  x0, x21
    mov  x1, xzr
    bl   ext_get_material
    cbz  x0, draw_line
    mov  x25, x0
    adr  x0, s_color
    bl   ext_string_new
    mov  x1, x0
    mov  x0, x25
    fmov s0, wzr
    ldr  s1, trail_green
    ldr  s2, trail_blue
    fmov s3, wzr
    mov  x2, xzr
    bl   ext_set_color
draw_line:
    mov  x0, x21
    mov  w1, #2
    mov  x2, xzr
    bl   ext_set_position_count
    ldp  s0, s1, [sp, #0x10]
    ldr  s2, [sp, #0x18]
    mov  x0, x21
    mov  w1, #0
    mov  x2, xzr
    bl   ext_line_set_position
    ldp  s0, s1, [sp, #0x20]
    ldr  s2, [sp, #0x28]
    mov  x0, x21
    mov  w1, #1
    mov  x2, xzr
    bl   ext_line_set_position
    b    ball
hide:
    mov  x0, x21
    mov  w1, #0
    mov  x2, xzr
    bl   ext_set_position_count
    mov  w26, #1
ball:
    cbz  x22, out
    mov  x0, x22
    mov  x1, xzr
    bl   ext_get_gameobject
    cbz  x0, out
    cmp  w26, #0
    cset w1, ne
    mov  x2, xzr
    bl   ext_set_active
    cmp  w26, #2
    b.ne ball_home
    ldr  s0, quarter_pi
    fmov s1, #0.5
    fmul s1, s8, s1
    fsub s8, s0, s1
    fmov s0, s8
    mov  x0, xzr
    bl   ext_sin
    fmov s9, s0
    fmov s0, s8
    mov  x0, xzr
    bl   ext_cos
    fmov s3, s0
    fmov s0, wzr
    fmov s1, s9
    fmov s2, wzr
    mov  x0, x22
    mov  x1, xzr
    bl   ext_set_rotation
    ldp  s0, s1, [sp, #0x20]
    ldr  s2, [sp, #0x28]
    fmov s3, #0.75
    fsub s1, s1, s3
    mov  x0, x22
    mov  x1, xzr
    bl   ext_set_position
    b    out
ball_home:
    fmov s0, wzr
    fmov s1, wzr
    fmov s2, wzr
    mov  x0, x22
    mov  x1, xzr
    bl   ext_set_local_position
    fmov s0, wzr
    fmov s1, wzr
    fmov s2, wzr
    fmov s3, #1.0
    mov  x0, x22
    mov  x1, xzr
    bl   ext_set_local_rotation
out:
    ldp  d8, d9, [sp, #0xb0]
    ldp  x29, x30, [sp, #0xa0]
    ldp  x25, x26, [sp, #0x90]
    ldp  x23, x24, [sp, #0x80]
    ldp  x21, x22, [sp, #0x70]
    ldp  x19, x20, [sp, #0x60]
    ldp  x0, x1, [sp, #0x50]
    add  sp, sp, #0xc0
    ldrb w8, [x0, #0x10a]
    b    ext_back
valid:
    mov  w0, wzr
    ldr  w8, [x23, #0x2c]
    cmp  w8, w24
    b.ls valid_end
    ldr  x8, [x23, #0x38]
    cbz  x8, valid_end
    lsl  x9, x24, #32
    add  x8, x8, x9, asr #28
    ldr  w8, [x8, #4]
    lsr  x9, x24, #32
    cmp  w8, w9
    cset w0, eq
valid_end:
    ret
    .p2align 3
weapon_guid: .quad 270776430341173830
spin_up:     .quad 0
spin_speed:  .float -12.566371
spin_radius: .float 3.0
quarter_pi:  .float 0.7853982
camera_cut:  .float 0.5
camera_lift: .float 0.8
min_distance: .float 0.01
trail_green: .float 1.3088407
trail_blue:  .float 2.828427
s_trail:     .asciz "PFB_FX_WPN_ScorpionFlail_Trail"
s_line:      .asciz "LineRenderer"
s_ball:      .asciz "Q_WeaponVisual_ScorpionFlail/Scorpion_Flail/ScorpionFlail_Ball"
s_origin:    .asciz "Q_WeaponVisual_ScorpionFlail/ProjectileOrigin"
s_color:     .asciz "_ColorMult"
    .p2align 3
