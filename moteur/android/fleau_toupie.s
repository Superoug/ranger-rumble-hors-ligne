.text
.globl _flail_spin
_flail_spin:
    sub  sp, sp, #0x100
    stp  x0, x1, [sp, #0x88]
    stp  x2, x3, [sp, #0x98]
    stp  x19, x20, [sp, #0xa8]
    stp  x21, x22, [sp, #0xb8]
    stp  x23, x24, [sp, #0xc8]
    stp  x25, x26, [sp, #0xd8]
    stp  x29, x30, [sp, #0xe8]
    mov  x19, x0
    cbz  x3, out
    ldr  x8, [x3, #0x18]
    ldr  x9, flail_guid
    cmp  x8, x9
    b.ne out
    ldr  x23, [x2, #8]
    cbz  x23, out
    ldr  x24, [x1, #0x10]
    ldr  x20, [x1]
    cbz  x24, stop
    add  x0, x24, #0x30
    mov  x1, xzr
    bl   ext0_button_is_down
    tbz  w0, #0, stop
    ldr  x24, [x23, #0x68]
    bl   valid
    mov  w22, w0
    ldr  w8, [x23, #0x20]
    cmp  w8, #0
    b.le stop
    mov  x0, x19
    mov  x1, x20
    mov  x2, xzr
    bl   ext1_is_dead
    tbnz w0, #0, stop
    ldr  w9, [x19, #0x1c]
    ldr  w8, [x23]
    cbnz w8, held
    str  w9, [x23]
    mov  w8, w9
held:
    sub  w25, w9, w8
    ldr  x8, [x19]
    ldr  x9, [x8, #0x248]
    ldr  x1, [x8, #0x250]
    mov  x0, x19
    blr  x9
    mov  x26, x0
    sxtw x10, w25
    mul  x21, x10, x26
    ldr  x24, [x23, #0x58]
    bl   valid
    cbz  w0, not_spinning
    ldr  w8, [x19, #0x1c]
    str  w8, [x23, #0x10]
    str  wzr, [x23, #0x24]
    mov  x0, x19
    mov  x1, x20
    mov  x2, x24
    mov  x3, x21
    bl   ext8_enhancements
    sub  x11, x21, x26
    asr  x12, x21, #16
    asr  x11, x11, #16
    cmp  x12, x11
    b.eq out
    ldr  w8, [x23, #0x20]
    sub  w8, w8, #1
    str  w8, [x23, #0x20]
    cmp  w8, #0
    b.gt out
    b    stop
not_spinning:
    ldr  x9, spin_up
    cmp  x21, x9
    b.lt out
    cbz  w22, spawn
    mov  x0, x19
    ldr  x1, [x23, #0x68]
    mov  x2, xzr
    bl   ext6_destroy
spawn:
    mov  x0, x19
    mov  x1, x20
    mov  x2, xzr
    bl   ext2_team_id
    mov  w7, w0
    movz x9, #1, lsl #16
    stp  xzr, xzr, [sp, #0x10]
    stp  xzr, xzr, [sp, #0x20]
    stp  xzr, xzr, [sp, #0x30]
    stp  xzr, x9, [sp, #0x38]
    stp  xzr, xzr, [sp]
    mov  x0, x19
    ldr  x1, spin_guid
    add  x2, sp, #0x10
    add  x3, sp, #0x28
    mov  x4, x20
    mov  x5, xzr
    mov  x6, xzr
    bl   ext3_create_dynamic
    str  x0, [x23, #0x58]
    mov  x25, x0
    adrp x0, slot@PAGE
    ldr  x0, [x0, slot@PAGEOFF]
    bl   ext4_init_metadata
    movz x9, #1, lsl #16
    stp  x20, xzr, [sp, #0x48]
    stp  x9, xzr, [sp, #0x58]
    stp  xzr, xzr, [sp, #0x68]
    stp  xzr, xzr, [sp, #0x78]
    adrp x3, slot@PAGE
    ldr  x3, [x3, slot@PAGEOFF]
    ldr  x3, [x3]
    mov  x0, x19
    mov  x1, x25
    add  x2, sp, #0x48
    bl   ext5_set_hierarchy
    ldr  w8, journal
    cbz  w8, out
    adr  x0, log_spawn
    bl   ext9_string_new
    mov  x1, xzr
    bl   ext10_debug_log
    b    out
stop:
    str  wzr, [x23]
    ldr  x24, [x23, #0x58]
    str  xzr, [x23, #0x58]
    bl   valid
    cbz  w0, out
    mov  x0, x19
    mov  x1, x24
    mov  x2, xzr
    bl   ext6_destroy
out:
    ldp  x0, x1, [sp, #0x88]
    ldp  x2, x3, [sp, #0x98]
    ldp  x19, x20, [sp, #0xa8]
    ldp  x21, x22, [sp, #0xb8]
    ldp  x23, x24, [sp, #0xc8]
    ldp  x25, x26, [sp, #0xd8]
    ldp  x29, x30, [sp, #0xe8]
    add  sp, sp, #0x100
    sub  sp, sp, #0x70
    b    ext7_back
valid:
    mov  w0, wzr
    ldr  w8, [x19, #0x2c]
    cmp  w8, w24
    b.ls valid_end
    ldr  x8, [x19, #0x38]
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
flail_guid: .quad 3873562517302156309
spin_guid:  .quad 2021436754639239773
spin_up:    .quad 7864
log_spawn:  .asciz "RR fleau: tourbillon cree"
    .p2align 2
journal:    .word 0
