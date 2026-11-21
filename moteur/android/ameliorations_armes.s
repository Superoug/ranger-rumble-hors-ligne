.text
.globl _ae_start
_ae_start:
    ret
.globl _ae_entry
_ae_entry:
    mov  w23, w4
    ldur w9, [x30, #-8]
    ldr  w10, loadout_ldrb
    cmp  w9, w10
    csel w9, w5, wzr, eq
    str  w9, [sp]
    b    ext_entry_return
.globl _ae_apply
_ae_apply:
    ldr  w9, [sp]
    ldr  x10, [sp, #0x38]
    sub  sp, sp, #0x60
    stp  x19, x20, [sp, #0x10]
    stp  x21, x22, [sp, #0x20]
    stp  x23, x24, [sp, #0x30]
    stp  x29, x30, [sp, #0x50]
    mov  x19, x0
    mov  x20, x2
    mov  w21, w9
    mov  x22, x10
    str  w3, [sp, #0x8]
    mov  w24, wzr
    bl   ext_talents
    cbz  w21, done
    cbz  x22, done
    ldr  x22, [x22, #0x1d8]
    cbz  x22, done
    mov  w23, wzr
next:
    cmp  w23, w21
    b.ge done
    ldr  w8, [x22, #0x18]
    cmp  w23, w8
    b.ge done
    ldr  x8, [x22, #0x10]
    add  x8, x8, #0x20
    ldr  x8, [x8, w23, uxtw #3]
    cbz  x8, skip
    str  x8, [sp, #0x40]
    adrp x0, slot_enh@PAGE
    ldr  x0, [x0, slot_enh@PAGEOFF]
    bl   ext_init_metadata
    adrp x8, slot_enh@PAGE
    ldr  x8, [x8, slot_enh@PAGEOFF]
    ldr  x9, [x8]
    str  x9, [sp, #0x48]
    ldr  x8, [x9, #0x38]
    cbnz x8, 1f
    mov  x0, x9
    bl   ext_init_rgctx
1:  ldr  x9, [sp, #0x48]
    ldr  x8, [x9, #0x38]
    ldr  x4, [x8, #8]
    mov  x0, x19
    ldr  x1, [sp, #0x40]
    mov  w2, #1
    add  x3, sp, #0x48
    str  xzr, [x3]
    bl   ext_find_asset
    tbz  w0, #0, skip
    ldr  x0, [sp, #0x48]
    cbz  x0, skip
    ldr  x8, [x0]
    ldp  x9, x3, [x8, #0x198]
    mov  x1, x19
    mov  x2, x20
    blr  x9
    add  w24, w24, #1
skip:
    add  w23, w23, #1
    b    next
done:
    bl   log_ae
    ldp  x19, x20, [sp, #0x10]
    ldp  x21, x22, [sp, #0x20]
    ldp  x23, x24, [sp, #0x30]
    ldp  x29, x30, [sp, #0x50]
    add  sp, sp, #0x60
    ret
log_ae:
    ldr  w9, journal
    cbz  w9, log_end
    ldr  w12, [sp, #0x8]
    stp  x29, x30, [sp, #-0x30]!
    adr  x9, log_text
    ldp  x10, x11, [x9]
    stp  x10, x11, [sp, #0x10]
    ldp  x10, x11, [x9, #0x10]
    stp  x10, x11, [sp, #0x20]
    mov  w13, #9
    cmp  w12, w13
    csel w12, w12, w13, ls
    add  w12, w12, #48
    strb w12, [sp, #0x1d]
    cmp  w21, w13
    csel w12, w21, w13, ls
    add  w12, w12, #48
    strb w12, [sp, #0x26]
    cmp  w24, w13
    csel w12, w24, w13, ls
    add  w12, w12, #48
    strb w12, [sp, #0x2b]
    add  x0, sp, #0x10
    bl   ext_string_new
    mov  x1, xzr
    bl   ext_debug_log
    ldp  x29, x30, [sp], #0x30
log_end:
    ret
    .p2align 3
log_text:     .ascii "RR arsenal: s0 niveau 0 ok 0\0\0\0\0"
loadout_ldrb: .word 0x39406265
journal:      .word 0
