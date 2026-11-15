.text
.globl _tk_start
_tk_start:
.globl _tk_add
_tk_add:
    stp  x29, x30, [sp, #-0x20]!
    stp  x0, x2, [sp, #0x10]
    bl   ext_qlist_add
    ldp  x0, x2, [sp, #0x10]
    ldr  x1, token_dropper
    bl   ext_qlist_add
    adr  x0, s_with_bolts
    bl   tk_log
    ldp  x29, x30, [sp], #0x20
    ret
.globl _tk_no_bolt
_tk_no_bolt:
    tbnz w0, #0, 1f
    ret
1:  cbz  x19, 9f
    adrp x8, slot_dropper_class@PAGE
    ldr  x8, [x8, slot_dropper_class@PAGEOFF]
    ldr  x23, [x8]
    ldr  x8, [x23, #0x38]
    cbnz x8, 3f
    mov  x0, x23
    bl   ext_class_init
    ldr  x8, [x23, #0x38]
    cbz  x8, 9f
3:  ldr  x3, [x8, #8]
    ldr  x0, [x19, #0xa0]
    cbz  x0, 9f
    mov  x1, x20
    add  x2, sp, #0x38
    bl   ext_try_get_pointer
    tbz  w0, #0, 2f
    ldr  x0, [sp, #0x38]
    mov  x1, xzr
    bl   ext_get_specs
    mov  w1, w0
    mov  x0, x19
    adrp x8, slot_resolve_list@PAGE
    ldr  x8, [x8, slot_resolve_list@PAGEOFF]
    ldr  x2, [x8]
    bl   ext_resolve_list
    stp  x0, x1, [sp, #0x10]
    add  x0, sp, #0x10
    ldr  x1, token_dropper
    adrp x8, slot_list_add@PAGE
    ldr  x8, [x8, slot_list_add@PAGEOFF]
    ldr  x2, [x8]
    bl   ext_qlist_add
    adr  x0, s_added
    bl   tk_log
    b    9f
2:  mov  x0, x19
    mov  w1, #8
    adrp x8, slot_alloc_list@PAGE
    ldr  x8, [x8, slot_alloc_list@PAGEOFF]
    ldr  x2, [x8]
    bl   ext_alloc_list
    stp  x0, x1, [sp, #0x10]
    add  x0, sp, #0x10
    ldr  x1, token_dropper
    adrp x8, slot_list_add@PAGE
    ldr  x8, [x8, slot_list_add@PAGEOFF]
    ldr  x2, [x8]
    bl   ext_qlist_add
    ldp  x0, x1, [sp, #0x10]
    adrp x8, slot_list_ptr@PAGE
    ldr  x8, [x8, slot_list_ptr@PAGEOFF]
    ldr  x2, [x8]
    bl   ext_list_ptr
    stp  xzr, xzr, [sp, #0x48]
    mov  w1, w0
    add  x0, sp, #0x48
    mov  x2, xzr
    bl   ext_set_specs
    mov  x0, x19
    mov  x1, x20
    ldp  x2, x3, [sp, #0x48]
    adrp x8, slot_frame_add@PAGE
    ldr  x8, [x8, slot_frame_add@PAGEOFF]
    ldr  x4, [x8]
    bl   ext_frame_add
    adr  x0, s_made
    bl   tk_log
9:  b    ext_setup_end
.globl _tk_replaced
_tk_replaced:
    add  x0, sp, #0x28
    ldr  x1, token_dropper
    adrp x8, slot_list_add@PAGE
    ldr  x8, [x8, slot_list_add@PAGEOFF]
    ldr  x2, [x8]
    bl   ext_qlist_add
    adr  x0, s_replaced
    bl   tk_log
    b    ext_setup_end
tk_log:
    ldr  w9, journal
    cbz  w9, 1f
    stp  x29, x30, [sp, #-0x10]!
    bl   ext_string_new
    mov  x1, xzr
    bl   ext_debug_log
    ldp  x29, x30, [sp], #0x10
1:  ret
s_added:        .asciz "RR jetons: jeton ajoute au lacher d'un joueur"
s_made:         .asciz "RR jetons: lacher avec jeton cree pour un joueur"
s_with_bolts:   .asciz "RR jetons: jeton ajoute avec les boulons"
s_replaced:     .asciz "RR jetons: jeton ajoute au lacher remplace"
    .p2align 3
token_dropper:  .quad 4349289682992116869
    .p2align 2
journal:        .word 0
