.text
.globl _mx_start
_mx_start:
    ret
.globl _mx_weapon
_mx_weapon:
    add  x0, x0, #0x28
    mov  w3, #0
    b    mx_filter
.globl _mx_hero
_mx_hero:
    add  x0, x0, #0x38
    mov  w3, #1
mx_filter:
    stp  x29, x30, [sp, #-0x30]!
    stp  x19, x20, [sp, #0x10]
    stp  x21, x22, [sp, #0x20]
    mov  x19, x0
    mov  w20, w1
    mov  w21, w3
    mov  x2, xzr
    bl   ext_is_unlocked
    cbz  w0, 1f
    mov  x0, x19
    mov  w1, w20
    mov  w2, w21
    mov  x3, xzr
    bl   ext_get_metadata
    cmp  w0, #9
    cset w0, ge
    b    2f
1:  mov  w0, #1
2:  ldp  x21, x22, [sp, #0x20]
    ldp  x19, x20, [sp, #0x10]
    ldp  x29, x30, [sp], #0x30
    ret
.globl _mx_orbs_none
_mx_orbs_none:
    ldr  w8, [sp, #0x10]
    cmp  w8, #1
    b.ne 1f
    b    ext_orbs_false
1:  ldr  w8, [x22, #0x18]
    cbnz w8, 2f
    b    ext_orbs_locked
2:  bl   mx_credits
    b    ext_orbs_return
.globl _mx_plans_none
_mx_plans_none:
    cbz  w22, 1f
    b    ext_plans_pick
1:  bl   mx_credits
    b    ext_plans_return
mx_credits:
    ldr  w9, [x20, #0x4]
    ldr  w10, [x20, #0x10]
    mov  w11, #2
    cmp  w10, #2
    b.ne 3f
    mov  w11, #4
3:  cmp  w10, #3
    b.ne 4f
    mov  w11, #6
4:  mul  w9, w9, w11
    mov  w8, #6
    stp  w8, w9, [x19]
    mov  w8, #5
    stp  wzr, w8, [x19, #0x8]
    str  xzr, [x19, #0x10]
    mov  w0, #1
    ret
