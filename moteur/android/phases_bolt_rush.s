.text
.globl _phase_tick
.globl _phase_spawner
.globl _phase_spawned
.globl _phase_kill
.p2align 2
_phase_tick:
    stp  x29, x30, [sp, #-0x70]!
    stp  x0, x1, [sp, #0x10]
    stp  x2, x3, [sp, #0x20]
    stp  x4, x19, [sp, #0x30]
    stp  x20, x21, [sp, #0x40]
    stp  x22, x23, [sp, #0x50]
    mov  x19, x0
    mov  x20, x1
    cbz  x19, tick_out
    cbz  x20, tick_out
    ldr  w8, [x20]
    cmp  w8, #8
    b.ne tick_out
    mov  x0, x19
    bl   bolt_rush
    cbz  w0, tick_out
    ldr  w8, [x20, #0x9c]
    ldr  w9, magic
    cmp  w8, w9
    b.eq ready
    bl   phase_init
ready:
    ldrb w21, [x20, #0x94]
    cmp  w21, #4
    b.hs tick_out
    add  x9, x20, #0x98
    ldrb w22, [x9, x21]
    cbz  w22, tick_out
    adr  x9, filters
    ldr  w23, [x9, x22, lsl #2]
    ldrb w8, [x20, #0x95]
    cbnz w8, phase_on
    ldr  w8, [x19, #0x1c]
    ldr  w9, [x20, #0x90]
    cmp  w8, w9
    b.lt tick_out
    mov  x0, x19
    mov  w1, w23
    mov  w2, #1
    mov  w3, #0
    mov  x4, xzr
    bl   ext_set_spawners_enabled
    mov  w8, #1
    strb w8, [x20, #0x95]
    strh wzr, [x20, #0x96]
    ldr  w8, [x19, #0x1c]
    str  w8, [x20, #0x90]
    adr  x0, s_start
    bl   log_phase
    b    tick_out
phase_on:
    bl   frame_dt
    ldr  w8, [x19, #0x1c]
    ldr  w9, [x20, #0x90]
    sub  w8, w8, w9
    sxtw x8, w8
    mul  x8, x0, x8
    ldr  x9, grace
    cmp  x8, x9
    b.lt tick_out
    ldrb w9, [x20, #0x96]
    ldrb w10, [x20, #0x97]
    cbnz w9, some_spawned
    ldr  x11, spawn_window
    cmp  x8, x11
    b.lt tick_out
    b    phase_over
some_spawned:
    cmp  w10, w9
    b.lo tick_out
phase_over:
    mov  x0, x19
    mov  w1, w23
    mov  w2, #0
    mov  w3, #0
    mov  x4, xzr
    bl   ext_set_spawners_enabled
    strb wzr, [x20, #0x95]
    add  w21, w21, #1
    strb w21, [x20, #0x94]
    bl   frame_dt
    ldr  x9, next_delay
    sdiv x9, x9, x0
    ldr  w8, [x19, #0x1c]
    add  w8, w8, w9
    str  w8, [x20, #0x90]
    adr  x0, s_end
    bl   log_phase
tick_out:
    ldp  x22, x23, [sp, #0x50]
    ldp  x20, x21, [sp, #0x40]
    ldp  x4, x19, [sp, #0x30]
    ldp  x2, x3, [sp, #0x20]
    ldp  x0, x1, [sp, #0x10]
    ldp  x29, x30, [sp], #0x70
    sub  sp, sp, #0x40
    b    ext_back_tick
phase_init:
    stp  x29, x30, [sp, #-0x50]!
    stp  x21, x22, [sp, #0x10]
    mov  x0, x19
    mov  w1, #4380
    mov  w2, #0
    mov  w3, #1
    mov  x4, xzr
    bl   ext_set_spawners_enabled
    mov  w8, #1
    strb w8, [x20, #0x98]
    mov  x0, x19
    mov  x1, xzr
    bl   ext_get_rng
    mov  x21, x0
    mov  w1, #0
    mov  w2, #2
    mov  x3, xzr
    bl   ext_rng_next
    add  w8, w0, #2
    strb w8, [x20, #0x99]
    cmp  w8, #3
    b.eq after_mini
    mov  x0, x21
    mov  w1, #0
    mov  w2, #2
    mov  x3, xzr
    bl   ext_rng_next
    add  w8, w0, #3
    strb w8, [x20, #0x9a]
    cmp  w8, #3
    mov  w8, #4
    csel w8, w8, wzr, eq
    strb w8, [x20, #0x9b]
    b    plan_done
after_mini:
    mov  w8, #4
    strb w8, [x20, #0x9a]
    strb wzr, [x20, #0x9b]
plan_done:
    str  wzr, [x20, #0x94]
    bl   frame_dt
    ldr  x9, first_delay
    sdiv x9, x9, x0
    ldr  w8, [x19, #0x1c]
    add  w8, w8, w9
    str  w8, [x20, #0x90]
    ldr  x8, [x19, #0x368]
    cbz  x8, init_done
    ldr  x8, [x8, #0x10]
    adr  x21, minis
    mov  w22, #4
find_map:
    ldr  x9, [x21]
    cmp  x8, x9
    b.eq found
    add  x21, x21, #56
    subs w22, w22, #1
    b.ne find_map
    b    init_done
found:
    ldp  x9, x10, [x21, #8]
    stp  x9, x10, [sp, #0x20]
    ldr  x9, [x21, #24]
    str  x9, [sp, #0x30]
    mov  x0, x19
    ldr  x1, slammer_spawner
    add  x2, sp, #0x20
    mov  x3, xzr
    bl   ext_create_dynamic
    ldp  x9, x10, [x21, #32]
    stp  x9, x10, [sp, #0x20]
    ldr  x9, [x21, #48]
    str  x9, [sp, #0x30]
    mov  x0, x19
    ldr  x1, slammer_spawner
    add  x2, sp, #0x20
    mov  x3, xzr
    bl   ext_create_dynamic
init_done:
    ldr  w8, magic
    str  w8, [x20, #0x9c]
    mov  w22, #0
    adr  x0, s_init
    bl   log_phase
    ldp  x21, x22, [sp, #0x10]
    ldp  x29, x30, [sp], #0x50
    ret
_phase_spawner:
    stp  x29, x30, [sp, #-0x60]!
    stp  x0, x1, [sp, #0x10]
    stp  x2, x19, [sp, #0x20]
    stp  x20, x21, [sp, #0x30]
    mov  x19, x1
    cbz  x19, sp_go
    ldr  x20, [x2, #8]
    cbz  x20, sp_go
    mov  x0, x19
    bl   bolt_rush
    cbz  w0, sp_go
    str  xzr, [sp, #0x40]
    mov  x0, x19
    add  x1, sp, #0x40
    mov  x2, xzr
    bl   ext_try_get_handler
    cbz  w0, sp_go
    ldr  x21, [sp, #0x40]
    cbz  x21, sp_go
    ldr  w8, [x21]
    cmp  w8, #8
    b.ne sp_go
    ldr  w8, [x21, #0x9c]
    ldr  w9, magic
    cmp  w8, w9
    b.ne sp_skip
    ldr  w8, [x20, #4]
    cbz  w8, sp_go
    ldr  w8, [x20]
    tbz  w8, #31, sp_go
    ldr  w8, [x19, #0x1c]
    str  w8, [x20]
    stp  x22, x23, [sp, #0x48]
    mov  w22, #9
    adr  x0, s_spawn
    bl   log_phase
    ldp  x22, x23, [sp, #0x48]
sp_go:
    ldp  x20, x21, [sp, #0x30]
    ldp  x2, x19, [sp, #0x20]
    ldp  x0, x1, [sp, #0x10]
    ldp  x29, x30, [sp], #0x60
    sub  sp, sp, #0x1b0
    b    ext_back_spawner
sp_skip:
    ldp  x20, x21, [sp, #0x30]
    ldp  x2, x19, [sp, #0x20]
    ldp  x0, x1, [sp, #0x10]
    ldp  x29, x30, [sp], #0x60
    ret
_phase_spawned:
    stp  x29, x30, [sp, #-0x10]!
    bl   ext_on_spawned
    mov  x0, x19
    bl   phase_handler
    cbz  x0, spd_out
    ldrb w8, [x0, #0x96]
    cmp  w8, #255
    b.hs spd_out
    add  w8, w8, #1
    strb w8, [x0, #0x96]
spd_out:
    ldp  x29, x30, [sp], #0x10
    ret
_phase_kill:
    stp  x29, x30, [sp, #-0x40]!
    stp  x0, x1, [sp, #0x10]
    stp  x2, x3, [sp, #0x20]
    stp  x19, x20, [sp, #0x30]
    mov  x19, x1
    mov  x0, x1
    bl   phase_handler
    cbz  x0, kill_out
    mov  x20, x0
    ldrb w9, [x20, #0x94]
    add  x10, x20, #0x98
    ldrb w9, [x10, x9]
    adr  x10, filters
    ldr  w2, [x10, x9, lsl #2]
    mov  x0, x19
    ldr  x1, [sp, #0x20]
    mov  x3, xzr
    bl   ext_has_type
    cbz  w0, kill_out
    ldrb w8, [x20, #0x97]
    cmp  w8, #255
    b.hs kill_out
    add  w8, w8, #1
    strb w8, [x20, #0x97]
kill_out:
    ldp  x19, x20, [sp, #0x30]
    ldp  x2, x3, [sp, #0x20]
    ldp  x0, x1, [sp, #0x10]
    ldp  x29, x30, [sp], #0x40
    mov  x2, xzr
    b    ext_set_need_update
phase_handler:
    stp  x29, x30, [sp, #-0x30]!
    stp  x19, x20, [sp, #0x10]
    mov  x19, x0
    cbz  x19, ph_none
    bl   bolt_rush
    cbz  w0, ph_none
    str  xzr, [sp, #0x20]
    mov  x0, x19
    add  x1, sp, #0x20
    mov  x2, xzr
    bl   ext_try_get_handler
    cbz  w0, ph_none
    ldr  x20, [sp, #0x20]
    cbz  x20, ph_none
    ldr  w8, [x20]
    cmp  w8, #8
    b.ne ph_none
    ldr  w8, [x20, #0x9c]
    ldr  w9, magic
    cmp  w8, w9
    b.ne ph_none
    ldrb w8, [x20, #0x95]
    cbz  w8, ph_none
    mov  x0, x20
    b    ph_end
ph_none:
    mov  x0, xzr
ph_end:
    ldp  x19, x20, [sp, #0x10]
    ldp  x29, x30, [sp], #0x30
    ret
bolt_rush:
    stp  x29, x30, [sp, #-0x20]!
    str  xzr, [sp, #0x10]
    add  x1, sp, #0x10
    mov  x2, xzr
    bl   ext_try_get_bolt_king_spec
    cbz  w0, br_end
    ldr  x8, [sp, #0x10]
    mov  w0, #0
    cbz  x8, br_end
    ldr  x9, [x8, #0x1e8]
    cmp  x9, #0x10, lsl #12
    cset w0, ge
br_end:
    ldp  x29, x30, [sp], #0x20
    ret
frame_dt:
    stp  x29, x30, [sp, #-0x10]!
    ldr  x8, [x19]
    ldr  x9, [x8, #0x248]
    ldr  x1, [x8, #0x250]
    mov  x0, x19
    blr  x9
    ldp  x29, x30, [sp], #0x10
    ret
log_phase:
    ldr  w9, journal
    cbz  w9, log_end
    stp  x29, x30, [sp, #-0x40]!
    ldp  x9, x10, [x0]
    stp  x9, x10, [sp, #0x10]
    ldp  x9, x10, [x0, #0x10]
    stp  x9, x10, [sp, #0x20]
    add  w9, w22, #48
    strb w9, [sp, #0x19]
    add  x0, sp, #0x10
    bl   ext_string_new
    mov  x1, xzr
    bl   ext_debug_log
    ldp  x29, x30, [sp], #0x40
log_end:
    ret
    .p2align 3
magic:           .word 0x52520110
journal:         .word 0
grace:           .quad 196608
spawn_window:    .quad 524288
first_delay:     .quad 98304
next_delay:      .quad 327680
slammer_spawner: .quad 640592018880317754
filters:         .word 0, 8, 4, 4096, 16
minis:
    .quad 289354170677996343
    .quad 2097152, 589824, 1638400
    .quad -2097152, 589824, -1638400
    .quad 1295867825452176766
    .quad -2667315, 557056, -2667315
    .quad 2667315, 557056, 2667315
    .quad 1220172026003034691
    .quad 393216, 524288, -819200
    .quad -393216, 524288, 819200
    .quad 4027187063009458707
    .quad 2490368, 917504, 2555904
    .quad -2490368, 917504, -2555904
s_init:  .ascii "RR phase X tirage"
         .zero 15
s_start: .ascii "RR phase X debut"
         .zero 16
s_end:   .ascii "RR phase X fin"
         .zero 18
s_spawn: .ascii "RR phase X lance"
         .zero 16
