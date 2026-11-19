.text
.globl _in_start
_in_start:
    ret
.globl _in_hud
_in_hud:
    stp  x29, x30, [sp, #-0x30]!
    stp  x19, x20, [sp, #0x10]
    str  x0, [sp, #0x20]
    adrp x0, slot_skins_table@PAGE
    ldr  x0, [x0, slot_skins_table@PAGEOFF]
    bl   ext_init_metadata
    adrp x8, slot_skins_table@PAGE
    ldr  x8, [x8, slot_skins_table@PAGEOFF]
    ldr  x0, [x8]
    ldr  w9, [x0, #0xe4]
    cbnz w9, 1f
    bl   ext_class_init
1:  mov  x0, x21
    mov  x1, xzr
    bl   ext_skin_for_actor
    cbz  x0, 9f
    mov  x19, x0
    mov  x0, xzr
    bl   ext_economy
    cbz  x0, 9f
    ldr  x0, [x0, #0x20]
    cbz  x0, 9f
    mov  w1, #19
    mov  x2, xzr
    bl   ext_char_def
    cbz  x0, 9f
    mov  x20, x0
    ldr  x8, [x20, #0x48]
    cbz  x8, 9f
    ldr  w9, [x8, #0x18]
    ldr  x8, [x8, #0x10]
    cbz  x8, 9f
    add  x8, x8, #0x20
2:  cbz  w9, 9f
    ldr  x10, [x8], #8
    sub  w9, w9, #1
    cmp  x10, x19
    b.ne 2b
    ldr  x8, [x20, #0x50]
    cbz  x8, 9f
    ldr  w9, [x8, #0x18]
    cbz  w9, 9f
    ldr  x8, [x8, #0x10]
    cbz  x8, 9f
    ldr  x8, [x8, #0x20]
    cbz  x8, 9f
    cmp  x8, x22
    b.eq 9f
    ldr  x8, [x8, #0x58]
    cbz  x8, 9f
    str  x8, [sp, #0x20]
9:  ldr  x1, [sp, #0x20]
    ldp  x19, x20, [sp, #0x10]
    ldp  x29, x30, [sp], #0x30
    ret
