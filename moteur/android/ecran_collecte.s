.text
.globl _ec_start
_ec_start:
.globl _ec_get_updater
_ec_get_updater:
    stp  x29, x30, [sp, #-0x20]!
    str  x19, [sp, #0x10]
    bl   ext_get_mm
    cbz  x0, 8f
    bl   ec_switch
    mov  w1, #'U'
    bl   ec_log
    cbz  x0, 7f
    mov  x19, x0
    bl   ec_event_id
    cmp  w0, #1
    b.ne 7f
    adr  x0, s_updater
    bl   ext_string_new
    mov  x1, x0
    mov  x0, x19
    mov  x2, xzr
    bl   ext_get_component_by_name
    mov  x19, x0
    bl   ec_mark_opened
    mov  x0, x19
    b    8f
7:  ldr  x19, [sp, #0x10]
    ldp  x29, x30, [sp], #0x20
    stp  x30, x19, [sp, #-0x10]!
    b    ext_get_updater_body
8:  ldr  x19, [sp, #0x10]
    ldp  x29, x30, [sp], #0x20
    ret
.globl _ec_get_canvas
_ec_get_canvas:
    stp  x29, x30, [sp, #-0x10]!
    bl   ext_get_mm
    cbz  x0, 1f
    bl   ec_switch
    mov  w1, #'C'
    bl   ec_log
1:  ldp  x29, x30, [sp], #0x10
    str  x30, [sp, #-0x20]!
    b    ext_get_canvas_body
.globl _ec_transition_finished
_ec_transition_finished:
    stp  x29, x30, [sp, #-0x10]!
    bl   ec_event_id
    ldp  x29, x30, [sp], #0x10
    cmp  w0, #1
    b.eq 1f
    str  x30, [sp, #-0x20]!
    b    ext_transition_body
1:  ret
.globl _ec_refresh_event
_ec_refresh_event:
    stp  x29, x30, [sp, #-0x20]!
    str  x0, [sp, #0x10]
    bl   ec_event_id
    mov  w21, w0
    ldr  x0, [sp, #0x10]
    ldp  x29, x30, [sp], #0x20
    cbnz w21, 1f
    ldr  w21, [x0, #0x60]
1:  ret
.globl _ec_earn_tokens
_ec_earn_tokens:
    sub  sp, sp, #0x150
    stp  x19, x20, [sp, #0x120]
    stp  x21, x22, [sp, #0x130]
    stp  x29, x30, [sp, #0x140]
    mov  x19, x0
    mov  w20, w1
    lsr  x21, x1, #32
    cmp  w21, #1
    b.lt 9f
    adrp x0, slot_get_status@PAGE
    ldr  x0, [x0, slot_get_status@PAGEOFF]
    mov  x22, x0
    bl   ext_init_metadata
    ldr  x1, [x22]
    mov  x0, x19
    mov  x8, sp
    bl   ext_ctx_get
    mov  x0, sp
    mov  w1, w20
    add  x2, sp, #0x40
    mov  x3, xzr
    bl   ext_try_get_user_event
    tbz  w0, #0, 9f
    adrp x0, slot_get_currencies@PAGE
    ldr  x0, [x0, slot_get_currencies@PAGEOFF]
    bl   ext_init_metadata
    adrp x0, slot_set_currencies@PAGE
    ldr  x0, [x0, slot_set_currencies@PAGEOFF]
    bl   ext_init_metadata
    adrp x8, slot_get_currencies@PAGE
    ldr  x8, [x8, slot_get_currencies@PAGEOFF]
    ldr  x1, [x8]
    mov  x0, x19
    add  x8, sp, #0xc0
    bl   ext_currencies_get
    add  x0, sp, #0xc0
    mov  w1, #5
    mov  w2, #5000
    mov  w3, #9
    mov  x4, xzr
    bl   ext_currencies_spend
    tbz  w0, #0, 9f
    ldp  q0, q1, [sp, #0xc0]
    ldr  x9, [sp, #0xe0]
    stp  q0, q1, [sp, #0xf0]
    str  x9, [sp, #0x110]
    adrp x8, slot_set_currencies@PAGE
    ldr  x8, [x8, slot_set_currencies@PAGEOFF]
    ldr  x2, [x8]
    mov  x0, x19
    add  x1, sp, #0xf0
    bl   ext_currencies_set
    ldr  w8, [sp, #0x60]
    add  w8, w8, w21
    str  w8, [sp, #0x60]
    mov  x0, sp
    mov  w1, w20
    add  x2, sp, #0x40
    mov  x3, xzr
    bl   ext_update_event
    adrp x0, slot_set_status@PAGE
    ldr  x0, [x0, slot_set_status@PAGEOFF]
    mov  x22, x0
    bl   ext_init_metadata
    ldp  q0, q1, [sp]
    stp  q0, q1, [sp, #0x20]
    ldr  x2, [x22]
    mov  x0, x19
    add  x1, sp, #0x20
    bl   ext_ctx_set
9:  ldp  x29, x30, [sp, #0x140]
    ldp  x21, x22, [sp, #0x130]
    ldp  x19, x20, [sp, #0x120]
    add  sp, sp, #0x150
    ret
.globl _ec_end_time
_ec_end_time:
    cbz  x0, 1f
    b    ext_time_implicit
1:  mov  x0, x20
    mov  x1, x19
    b    ext_event_end_time
ec_mark_opened:
    stp  x29, x30, [sp, #-0xb0]!
    str  x19, [sp, #0x10]
    mov  x0, xzr
    bl   ext_events_instance
    cbz  x0, 9f
    mov  w1, #1
    add  x2, sp, #0x20
    mov  x3, xzr
    bl   ext_try_get_user_event_sys
    tbz  w0, #0, 9f
    ldr  x8, [sp, #0x28]
    mov  x9, #1000
    udiv x19, x8, x9
    adr  x0, s_seen
    bl   ext_string_new
    mov  w1, w19
    mov  x2, xzr
    bl   ext_set_int
    mov  x0, xzr
    bl   ext_prefs_save
9:  ldr  x19, [sp, #0x10]
    ldp  x29, x30, [sp], #0xb0
    ret
.globl _ec_never_opened
_ec_never_opened:
    ldr  w8, [x0]
    cmp  w8, #1
    b.ne 1f
    stp  x29, x30, [sp, #-0x20]!
    stp  x0, x19, [sp, #0x10]
    ldr  x8, [x0, #8]
    mov  x9, #1000
    udiv x19, x8, x9
    adr  x0, s_seen
    bl   ext_string_new
    mov  w1, #0
    mov  x2, xzr
    bl   ext_get_int
    cmp  w0, w19
    ldp  x0, x19, [sp, #0x10]
    ldp  x29, x30, [sp], #0x20
    b.ne 1f
    mov  w0, #0
    ret
1:  ldrb w8, [x0, #0x30]
    tst  w8, #1
    cset w0, eq
    ret
.globl _ec_can_open_popup
_ec_can_open_popup:
    cbz  x1, 9f
    ldr  w8, [x1, #0x10]
    cmp  w8, #1
    b.ne 9f
    stp  x29, x30, [sp, #-0x30]!
    stp  x0, x1, [sp, #0x10]
    str  x19, [sp, #0x20]
    ldr  x8, [x0, #8]
    mov  x9, #1000
    udiv x19, x8, x9
    adr  x0, s_seen
    bl   ext_string_new
    mov  w1, #0
    mov  x2, xzr
    bl   ext_get_int
    cmp  w0, w19
    ldr  x19, [sp, #0x20]
    ldp  x0, x1, [sp, #0x10]
    ldp  x29, x30, [sp], #0x30
    b.ne 9f
    mov  w0, #0
    ret
9:  str  x30, [sp, #-0x10]!
    b    ext_can_open_body
ec_event_id:
    stp  x29, x30, [sp, #-0x20]!
    str  x19, [sp, #0x10]
    adrp x0, slot_v2_class@PAGE
    ldr  x0, [x0, slot_v2_class@PAGEOFF]
    mov  x19, x0
    bl   ext_init_metadata
    mov  w0, #0
    ldr  x8, [x19]
    cbz  x8, 1f
    ldr  x8, [x8, #0xb8]
    cbz  x8, 1f
    ldr  w0, [x8]
1:  ldr  x19, [sp, #0x10]
    ldp  x29, x30, [sp], #0x20
    ret
ec_switch:
    stp  x29, x30, [sp, #-0x30]!
    stp  x19, x20, [sp, #0x10]
    stp  x21, x22, [sp, #0x20]
    mov  x19, x0
    mov  x21, xzr
    ldr  x0, [x19, #0xb8]
    cbz  x0, 9f
    mov  x1, xzr
    bl   ext_get_transform
    cbz  x0, 9f
    mov  x1, xzr
    bl   ext_get_parent
    cbz  x0, 9f
    mov  x20, x0
    bl   ec_event_id
    cmp  w0, #1
    adr  x0, s_mopz
    b.ne 2f
    bl   ext_string_new
    mov  x1, x0
    mov  x0, x20
    mov  x2, xzr
    bl   ext_find
    cbz  x0, 1f
    mov  x1, xzr
    bl   ext_get_gameobject
    cbz  x0, 1f
    mov  w1, #0
    mov  x2, xzr
    bl   ext_set_active
1:  adr  x0, s_collect
2:  bl   ext_string_new
    mov  x1, x0
    mov  x0, x20
    mov  x2, xzr
    bl   ext_find
    cbz  x0, 9f
    mov  x1, xzr
    bl   ext_get_gameobject
    cbz  x0, 9f
    mov  x22, x0
    adr  x0, s_canvas_group
    bl   ext_string_new
    mov  x1, x0
    mov  x0, x22
    mov  x2, xzr
    bl   ext_get_component_by_name
    cbz  x0, 9f
    mov  x1, x0
    add  x0, x19, #0xb8
    str  x1, [x0]
    bl   ext_write_barrier
    mov  x21, x22
9:  mov  x0, x21
    ldp  x21, x22, [sp, #0x20]
    ldp  x19, x20, [sp, #0x10]
    ldp  x29, x30, [sp], #0x30
    ret
ec_log:
    ldr  w9, journal
    cbz  w9, 9f
    stp  x29, x30, [sp, #-0x40]!
    stp  x0, x19, [sp, #0x30]
    mov  w19, w1
    cmp  x0, #0
    cset w9, ne
    add  w9, w9, #48
    adr  x10, s_log
    ldp  x11, x12, [x10]
    stp  x11, x12, [sp, #0x10]
    ldp  x11, x12, [x10, #0x10]
    stp  x11, x12, [sp, #0x20]
    strb w19, [sp, #0x10 + 12]
    strb w9, [sp, #0x10 + 20]
    bl   ec_event_id
    add  w0, w0, #48
    strb w0, [sp, #0x10 + 16]
    add  x0, sp, #0x10
    bl   ext_string_new
    mov  x1, xzr
    bl   ext_debug_log
    ldp  x0, x19, [sp, #0x30]
    ldp  x29, x30, [sp], #0x40
9:  ret
.globl _ec_info_clicked
_ec_info_clicked:
    stp  x29, x30, [sp, #-0x20]!
    str  x19, [sp, #0x10]
    mov  x19, x0
    bl   ec_event_id
    cmp  w0, #1
    b.ne 7f
    adrp x0, slot_popup_instance@PAGE
    ldr  x0, [x0, slot_popup_instance@PAGEOFF]
    bl   ext_init_metadata
    adrp x8, slot_popup_instance@PAGE
    ldr  x8, [x8, slot_popup_instance@PAGEOFF]
    ldr  x0, [x8]
    bl   ext_singleton_instance
    cbz  x0, 8f
    mov  w1, #1
    mov  x2, xzr
    bl   ext_show_event_info
    b    8f
7:  mov  x0, x19
    ldr  x19, [sp, #0x10]
    ldp  x29, x30, [sp], #0x20
    stp  x30, x19, [sp, #-0x10]!
    b    ext_play_pressed_body
8:  ldr  x19, [sp, #0x10]
    ldp  x29, x30, [sp], #0x20
    ret
.globl _ec_info_text
_ec_info_text:
    ldr  w9, [x19, #0x28]
    cmp  w9, #1
    b.ne 1f
    ldp  x0, x1, [x19, #0xe0]
    cbz  x0, 1f
    ldr  w9, [x0, #0x10]
    cbz  w9, 1f
    ret
1:  ldp  x0, x1, [x19, #0xd0]
    ret
s_log:          .asciz "RR collecte K e=N s=F          "
s_collect:      .asciz "HUD_EventScreen"
s_mopz:         .asciz "HUD_Event"
s_canvas_group: .asciz "CanvasGroup"
s_updater:      .asciz "EventScreenUpdater"
s_seen:         .asciz "rr_zurkon_vu"
    .p2align 2
journal:        .word 0
