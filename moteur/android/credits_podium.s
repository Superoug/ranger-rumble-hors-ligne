.text
.equ LOOT_BLUEPRINT, 5
.equ LOOT_CURRENCY, 6
.equ CURRENCY_CREDITS, 5
.equ PLANS_PER_KILL, 5
.equ MAX_KILLS, 60
.globl _cp_start
_cp_start:
.globl _cp_battle_end
_cp_battle_end:
    sub  sp, sp, #0xc0
    stp  x29, x30, [sp, #0x90]
    stp  x0, x1, [sp, #0x70]
    stp  x2, x3, [sp, #0x80]
    str  x4, [sp, #0xa0]
    stp  x19, x20, [sp, #0x60]
    stp  x21, x22, [sp, #0xb0]
    mov  x19, x0
    cbnz w3, 9f
    cbz  x2, 9f
    mov  x21, x2
    ldr  w9, [x2]
    ldr  w10, [x2, #4]
    ldr  w11, [x2, #0x40]
    mov  w20, #0
    adr  x12, ranked_modes
1:  ldr  w13, [x12], #4
    cbz  w13, 3f
    cmp  w13, w11
    b.ne 1b
    cmp  w10, #1
    b.ne 2f
    mov  w20, #300
    b    5f
2:  cmp  w10, #2
    b.ne 4f
    mov  w20, #200
    b    5f
4:  ldr  w14, last_paid_rank
    cmp  w10, w14
    b.gt 5f
    cmp  w10, #1
    b.lt 5f
    mov  w20, #100
    b    5f
3:  cmp  w9, #1
    b.ne 5f
    mov  w20, #300
5:  cbz  w20, 7f
    mov  w1, #LOOT_CURRENCY
    mov  w2, w20
    mov  w3, #0
    mov  w4, #CURRENCY_CREDITS
    bl   cp_give
    adr  x0, s_credits
    bl   cp_log
7:  ldr  w9, journal
    cbz  w9, 71f
    bl   cp_diag
71: mov  x0, x21
    bl   cp_kills
    ldr  w9, test_kills
    add  w20, w0, w9
    cbz  w20, 9f
    bl   cp_factor
    mul  w20, w20, w0
    mov  w9, #PLANS_PER_KILL
    mul  w20, w20, w9
    add  w20, w20, #50
    mov  w9, #100
    udiv w20, w20, w9
    cbz  w20, 9f
    ldr  w9, plan_targets_on
    cbz  w9, 9f
    bl   ext_plan_targets
    mov  w22, w1
    bl   cp_plans
    mov  w0, w22
    bl   cp_plans
    ldr  w9, second_on
    cbz  w9, 61f
    bl   ext_dw_second_uid
    bl   cp_plans
61: adr  x0, s_plans
    bl   cp_log
9:  ldp  x21, x22, [sp, #0xb0]
    ldp  x19, x20, [sp, #0x60]
    ldr  x4, [sp, #0xa0]
    ldp  x2, x3, [sp, #0x80]
    ldp  x0, x1, [sp, #0x70]
    ldp  x29, x30, [sp, #0x90]
    add  sp, sp, #0xc0
    stp  x29, x30, [sp, #-0x60]!
    b    ext_impl_body
cp_plans:
    stp  x29, x30, [sp, #-0x20]!
    str  w0, [sp, #0x10]
    cbz  w0, 9f
    mov  x1, xzr
    bl   ext_weapon_level
    cmp  w0, #9
    b.ge 9f
    ldr  w3, [sp, #0x10]
    mov  w1, #LOOT_BLUEPRINT
    mov  w2, w20
    mov  w4, #0
    bl   cp_give
9:  ldp  x29, x30, [sp], #0x20
    ret
cp_give:
    stp  x29, x30, [sp, #-0x80]!
    str  x19, [sp, #0x50]
    stp  w2, w1, [sp, #0x58]
    stp  w3, w4, [sp, #0x60]
    adrp x0, slot_modify_pending@PAGE
    ldr  x0, [x0, slot_modify_pending@PAGEOFF]
    bl   ext_init_metadata
    adr  x8, cp_push
    str  x8, [sp, #0x18]
    str  xzr, [sp, #0x28]
    add  x8, sp, #0x50
    str  x8, [sp, #0x40]
    adrp x8, slot_modify_pending@PAGE
    ldr  x8, [x8, slot_modify_pending@PAGEOFF]
    ldr  x2, [x8]
    mov  x0, x19
    mov  x1, sp
    bl   ext_ctx_modify
    ldp  x29, x30, [sp], #0x80
    ret
cp_push:
    stp  x29, x30, [sp, #-0x30]!
    mov  x3, x1
    ldr  w8, [x0, #8]
    ldr  w9, [x0, #0xc]
    stp  w9, w8, [sp, #0x10]
    ldp  w9, w10, [x0, #0x10]
    stp  w9, w10, [sp, #0x18]
    str  xzr, [sp, #0x20]
    ldr  x0, [x0]
    add  x1, sp, #0x10
    mov  w2, #6
    mov  x4, xzr
    bl   ext_push_pending
    ldp  x29, x30, [sp], #0x30
    ret
cp_kills:
    stp  x29, x30, [sp, #-0x10]!
    ldr  x0, [x0, #0x10]
    cbz  x0, 8f
    ldr  x0, [x0, #0x20]
    cbz  x0, 8f
    ldr  w9, [x0, #0x20]
    cmp  w9, #64
    b.hi 8f
    ldr  x0, [x0, #0x10]
    mov  w1, #12
    bl   cp_sum
    cmp  w0, #MAX_KILLS
    b.hi 8f
    ldp  x29, x30, [sp], #0x10
    ret
8:  mov  w0, #0
    ldp  x29, x30, [sp], #0x10
    ret
cp_sum:
    cbz  x0, 1f
    cbz  w1, 1f
    stp  x29, x30, [sp, #-0x30]!
    stp  x19, x20, [sp, #0x10]
    str  x21, [sp, #0x20]
    mov  x19, x0
    sub  w21, w1, #1
    ldr  w20, [x19, #0x14]
    cmp  w20, #MAX_KILLS
    csel w20, wzr, w20, hi
    ldr  x0, [x19, #0x28]
    mov  w1, w21
    bl   cp_sum
    add  w20, w20, w0
    ldr  x0, [x19, #0x30]
    mov  w1, w21
    bl   cp_sum
    add  w0, w20, w0
    ldr  x21, [sp, #0x20]
    ldp  x19, x20, [sp, #0x10]
    ldp  x29, x30, [sp], #0x30
    ret
1:  mov  w0, #0
    ret
cp_factor:
    ldr  w9, [x21]
    ldr  w10, [x21, #4]
    ldr  w11, [x21, #0x40]
    mov  w0, #100
    adr  x12, ranked_modes
1:  ldr  w13, [x12], #4
    cbz  w13, 3f
    cmp  w13, w11
    b.ne 1b
    cmp  w10, #1
    b.eq 4f
    cmp  w10, #2
    b.ne 2f
    mov  w0, #125
    ret
2:  cmp  w10, #3
    b.ne 5f
    mov  w0, #120
5:  ret
3:  cmp  w9, #1
    b.ne 5b
4:  mov  w0, #150
    ret
cp_diag:
    stp  x29, x30, [sp, #-0xa0]!
    stp  x19, x20, [sp, #0x10]
    stp  x21, x22, [sp, #0x20]
    stp  x23, x24, [sp, #0x30]
    mov  w20, #0
    mov  w22, #0
    mov  w23, #0
    mov  w24, #0
    str  xzr, [sp, #0x48]
    str  wzr, [sp, #0x50]
    ldr  x0, [x21, #0x10]
    cbz  x0, 3f
    ldr  x0, [x0, #0x20]
    cbz  x0, 3f
    ldr  w20, [x0, #0x20]
    ldr  x19, [x0, #0x10]
    cbz  x19, 3f
    ldr  w9, [x19, #0x10]
    str  w9, [sp, #0x48]
    bl   diag_node
    ldr  x0, [x19, #0x28]
    mov  x9, x19
    mov  x19, x0
    str  x9, [sp, #0x58]
    cbz  x19, 1f
    ldr  w9, [x19, #0x10]
    str  w9, [sp, #0x4c]
    bl   diag_node
1:  ldr  x9, [sp, #0x58]
    ldr  x19, [x9, #0x30]
    cbz  x19, 3f
    ldr  w9, [x19, #0x10]
    str  w9, [sp, #0x50]
    bl   diag_node
3:  add  x19, sp, #0x60
    adr  x1, s_diag
    mov  x0, x19
4:  ldrb w9, [x1], #1
    strb w9, [x0], #1
    cbnz w9, 4b
    sub  x0, x0, #1
    mov  w1, w20
    bl   put_num
    mov  w9, #' '
    strb w9, [x0], #1
    mov  w9, #'k'
    strb w9, [x0], #1
    mov  w1, w22
    bl   put_num
    mov  w9, #' '
    strb w9, [x0], #1
    mov  w9, #'m'
    strb w9, [x0], #1
    mov  w1, w23
    bl   put_num
    mov  w9, #' '
    strb w9, [x0], #1
    mov  w9, #'d'
    strb w9, [x0], #1
    mov  w1, w24
    bl   put_num
    mov  w9, #' '
    strb w9, [x0], #1
    mov  w9, #'w'
    strb w9, [x0], #1
    ldr  w1, [sp, #0x48]
    bl   put_num
    mov  w9, #','
    strb w9, [x0], #1
    ldr  w1, [sp, #0x4c]
    bl   put_num
    mov  w9, #','
    strb w9, [x0], #1
    ldr  w1, [sp, #0x50]
    bl   put_num
    strb wzr, [x0]
    mov  x0, x19
    bl   cp_log
    ldp  x23, x24, [sp, #0x30]
    ldp  x21, x22, [sp, #0x20]
    ldp  x19, x20, [sp, #0x10]
    ldp  x29, x30, [sp], #0xa0
    ret
diag_node:
    ldr  w9, [x19, #0x14]
    add  w22, w22, w9
    ldr  w9, [x19, #0x18]
    add  w23, w23, w9
    ldr  w9, [x19, #0x20]
    add  w24, w24, w9
    ret
put_num:
    mov  w9, #10
    sub  sp, sp, #0x10
    mov  x10, sp
    mov  x13, sp
1:  udiv w11, w1, w9
    msub w12, w11, w9, w1
    add  w12, w12, #'0'
    strb w12, [x10], #1
    mov  w1, w11
    cbnz w1, 1b
2:  ldrb w12, [x10, #-1]!
    strb w12, [x0], #1
    cmp  x10, x13
    b.ne 2b
    add  sp, sp, #0x10
    ret
cp_log:
    ldr  w9, journal
    cbz  w9, 1f
    stp  x29, x30, [sp, #-0x10]!
    bl   ext_string_new
    mov  x1, xzr
    bl   ext_debug_log
    ldp  x29, x30, [sp], #0x10
1:  ret
s_credits:      .asciz "RR credits: Qredits du podium donnes"
s_plans:        .asciz "RR plans: plans des kills donnes"
s_diag:         .asciz "RR plans diag n="
    .p2align 2
ranked_modes:    .word 125, 131, 219, 57, 68, 0
last_paid_rank:  .word 3
test_kills:      .word 0
plan_targets_on: .word 1
second_on: .word 1
journal:         .word 0
