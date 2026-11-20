.text
.globl _tk_start
_tk_start:
.globl _tk_get
_tk_get:
    mov  w0, #1
    str  w0, [x19, #0x20]
    ret
.globl _tk_set
_tk_set:
    mov  w20, #'0'
    cmp  w0, #2
    b.lo 1f
    mov  w20, #'1'
1:  mov  w8, #1
    str  w8, [x19, #0x20]
    ldr  x9, [x19, #0x30]
    ldr  x9, [x9, #0x20]
    ldrh w21, [x9, #0x1e]
    sub  sp, sp, #0x10
    strb w21, [sp]
    strb w20, [sp, #1]
    strb wzr, [sp, #2]
    mov  x0, sp
    bl   ext_string_new
    add  sp, sp, #0x10
    mov  x21, x0
    adr  x0, waiting_key
    bl   ext_string_new
    mov  x1, x21
    mov  x2, xzr
    bl   ext_set_string
    mov  x0, xzr
    bl   ext_save
    b    ext_done
.globl _tk_text
_tk_text:
    ldr  x9, [x0, #0x30]
    cbz  x9, 9f
    ldr  w10, [x9, #0x18]
    cbz  w10, 9f
    ldr  x9, [x9, #0x20]
    cbz  x9, 9f
    ldr  w10, [x9, #0x10]
    cmp  w10, #6
    b.lt 9f
    ldrh w10, [x9, #0x14]
    cmp  w10, #'R'
    b.ne 9f
    ldrh w10, [x9, #0x16]
    cmp  w10, #'R'
    b.ne 9f
    ldrh w10, [x9, #0x1a]
    cmp  w10, #'K'
    b.ne 9f
    stp  x29, x30, [sp, #-0x30]!
    stp  x19, x20, [sp, #0x10]
    mov  x19, x0
    ldrh w20, [x9, #0x1e]
    adr  x8, name_key
    ldp  x10, x11, [x8]
    stp  x10, x11, [sp, #0x20]
    strb w20, [sp, #0x2e]
    strb wzr, [sp, #0x2f]
    add  x0, sp, #0x20
    bl   ext_string_new
    mov  x1, xzr
    bl   ext_prefs_get_string
    cbz  x0, 8f
    mov  x20, x0
    ldr  x8, [x19, #0x28]
    cbz  x8, 8f
    ldr  x0, [x8, #0x20]
    cbz  x0, 8f
    mov  x1, x20
    mov  x2, xzr
    bl   ext_set_text
8:  ldp  x19, x20, [sp, #0x10]
    ldp  x29, x30, [sp], #0x30
    ret
9:  str  x30, [sp, #-0x30]!
    b    ext_update_text_next
.globl _tk_hide
_tk_hide:
    stp  x29, x30, [sp, #-0x20]!
    str  x19, [sp, #0x10]
    mov  x1, xzr
    bl   ext_get_game_object
    mov  x19, x0
    cbz  x0, 1f
    mov  x1, xzr
    bl   ext_get_name
    cbz  x0, 2f
    ldr  w8, [x0, #0x10]
    cmp  w8, #2
    b.lt 2f
    ldrh w8, [x0, #0x14]
    cmp  w8, #'R'
    b.ne 2f
    ldrh w8, [x0, #0x16]
    cmp  w8, #'R'
    b.eq 1f
2:  mov  x0, x19
    mov  w1, wzr
    mov  x2, xzr
    bl   ext_set_active
1:  ldr  x19, [sp, #0x10]
    ldp  x29, x30, [sp], #0x20
    ret
.globl _tk_tab
_tk_tab:
    stp  x29, x30, [sp, #-0x20]!
    stp  x19, x20, [sp, #0x10]
    mov  x19, x0
    bl   _tk_tab_original
    ldr  x0, [x19, #0x38]
    cbz  x0, 1f
    mov  x1, xzr
    bl   ext_go_get_transform
    cbz  x0, 1f
    mov  x1, xzr
    bl   ext_get_parent
    cbz  x0, 1f
    mov  x20, x0
    adr  x0, graphics_container
    bl   ext_string_new
    mov  x1, x0
    mov  x0, x20
    mov  x2, xzr
    bl   ext_transform_find
    cbz  x0, 1f
    mov  x1, xzr
    bl   ext_get_game_object
    cbz  x0, 1f
    mov  w1, wzr
    mov  x2, xzr
    bl   ext_set_active
1:  ldr  x0, [x19, #0x50]
    cbz  x0, 2f
    mov  x1, xzr
    bl   ext_get_transform
    cbz  x0, 2f
    mov  x1, xzr
    bl   ext_get_parent
    cbz  x0, 2f
    mov  x20, x0
    adr  x0, graphics_tab
    bl   ext_string_new
    mov  x1, x0
    mov  x0, x20
    mov  x2, xzr
    bl   ext_transform_find
    cbz  x0, 2f
    mov  x1, xzr
    bl   ext_get_game_object
    cbz  x0, 2f
    mov  x20, x0
    adr  x0, tab_widget
    bl   ext_string_new
    mov  x1, x0
    mov  x0, x20
    mov  x2, xzr
    bl   ext_get_component_by_name
    cbz  x0, 2f
    mov  x1, xzr
    bl   ext_unselect_tab
2:  ldp  x19, x20, [sp, #0x10]
    ldp  x29, x30, [sp], #0x20
    ret
_tk_tab_original:
    str  x30, [sp, #-0x30]!
    b    ext_select_tab_next
    .p2align 3
graphics_container:
    .asciz "RRGraphicsContainer"
    .p2align 3
graphics_tab:
    .asciz "RRGraphicsTab"
    .p2align 3
tab_widget:
    .asciz "TabUIWidget"
    .p2align 3
waiting_key:
    .asciz "rr_touche_attente"
    .p2align 3
name_key:
    .ascii "rr_touche_nom_\0\0"
