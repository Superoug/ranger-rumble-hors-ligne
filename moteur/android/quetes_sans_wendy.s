.text
.equ WENDY, 85
.globl _qw_start
_qw_start:
    ret
.globl _qw_draw
_qw_draw:
    cbz  x22, 9f
    ldr  x9, [x22, #0x10]
    cbz  x9, 9f
    add  x9, x9, #0x20
    ldr  w10, [x22, #0x18]
    mov  w11, wzr
    mov  w12, wzr
1:  cmp  w11, w10
    b.ge 2f
    ldr  w13, [x9, w11, uxtw #2]
    add  w11, w11, #1
    cmp  w13, #WENDY
    b.eq 1b
    str  w13, [x9, w12, uxtw #2]
    add  w12, w12, #1
    b    1b
2:  cmp  w12, w10
    b.eq 9f
    str  w12, [x22, #0x18]
    ldr  w13, [x22, #0x1c]
    add  w13, w13, #1
    str  w13, [x22, #0x1c]
    ldr  w13, journal
    cbz  w13, 9f
    stp  x29, x30, [sp, #-0x50]!
    stp  x0, x1, [sp, #0x10]
    stp  x2, x3, [sp, #0x20]
    stp  x4, x5, [sp, #0x30]
    stp  x6, x7, [sp, #0x40]
    adr  x0, log_text
    bl   ext_string_new
    mov  x1, xzr
    bl   ext_debug_log
    ldp  x0, x1, [sp, #0x10]
    ldp  x2, x3, [sp, #0x20]
    ldp  x4, x5, [sp, #0x30]
    ldp  x6, x7, [sp, #0x40]
    ldp  x29, x30, [sp], #0x50
9:  ldr  x8, [x26]
    ret
    .p2align 2
log_text:  .asciz "RR quetes: Wendy retiree"
    .p2align 2
journal:   .word 0
