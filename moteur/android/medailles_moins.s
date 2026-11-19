.text
.globl _mm_start
_mm_start:
    ret
.globl _mm_format
_mm_format:
    ldr  x8, [x8]
    tbz  w20, #31, 1f
    stp  x29, x30, [sp, #-0x20]!
    stp  x1, x8, [sp, #0x10]
    adr  x0, s_loss
    bl   ext_string_new
    ldp  x1, x8, [sp, #0x10]
    ldp  x29, x30, [sp], #0x20
    mov  x2, xzr
    cbz  x0, 1f
    mov  x8, x0
    neg  w9, w20
    str  w9, [x1, #0x10]
1:  ret
s_loss: .asciz "<color=#F20206>-{0}</color>"
    .p2align 2
