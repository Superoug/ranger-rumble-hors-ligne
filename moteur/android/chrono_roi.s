.text
.globl _kt_start
_kt_start:
.globl _kt_timer
_kt_timer:
    stp  x29, x30, [sp, #-0x60]!
    stp  x19, x20, [sp, #0x10]
    stp  x21, x22, [sp, #0x20]
    stp  x23, x24, [sp, #0x30]
    stp  x25, x26, [sp, #0x40]
    mov  x23, x0
    mov  x24, x19
    mov  x21, x20
    mov  x20, x22
    mov  x1, xzr
    bl   ext_ceil_to_int
    mov  w19, w0
    mov  x25, xzr
    mov  w26, #0
    mov  w22, #-1
    cbz  x20, 1f
    str  xzr, [sp, #0x50]
    mov  x0, x20
    add  x1, sp, #0x50
    mov  x2, xzr
    bl   ext_try_get_spec
    cbz  w0, 1f
    ldr  x9, [sp, #0x50]
    cbz  x9, 1f
    ldr  x10, [x9, #0x1e8]
    cmp  x10, #0x10, lsl #12
    b.lt 1f
    ldr  x10, [x9, #0x1c8]
    cbz  x10, 1f
    mov  x25, x10
    ldr  w26, [x9, #0x1d0]
    add  w26, w26, #1
    ldr  x8, [x20]
    ldr  x9, [x8, #0x248]
    ldr  x1, [x8, #0x250]
    mov  x0, x20
    blr  x9
    ldr  x9, [sp, #0x50]
    ldr  w10, [x20, #0x1c]
    ldr  w11, [x9, #0x1d0]
    sub  w10, w10, w11
    sxtw x10, w10
    mul  x10, x0, x10
    ldr  x11, [x9, #0x1e8]
    sub  x0, x11, x10
    cmp  x0, x23
    csel x0, x0, x23, lt
    cmp  x0, #0
    csel x0, xzr, x0, lt
    mov  x1, xzr
    bl   ext_ceil_to_int
    mov  w22, w0
1:  ldr  w8, [x21, #0x7c]
    cmp  w8, w26
    b.eq 4f
    str  w26, [x21, #0x7c]
    cbz  w26, 3f
    mov  w8, #-1
    str  w8, [x21, #0x34]
    adrp x0, slot_quantum_manager@PAGE
    ldr  x0, [x0, slot_quantum_manager@PAGEOFF]
    ldr  x8, [x0]
    tbz  x8, #0, 2f
    bl   ext_init_metadata
2:  adrp x8, slot_quantum_manager@PAGE
    ldr  x8, [x8, slot_quantum_manager@PAGEOFF]
    ldr  x0, [x8]
    ldr  w9, [x0, #0xe4]
    cbnz w9, 21f
    bl   ext_class_init
21: mov  x0, x25
    mov  x1, x24
    mov  x2, x20
    mov  x3, xzr
    bl   ext_is_local_player
    mov  w8, #44
    tst  w0, #1
    mov  w9, #43
    csel w0, w9, w8, ne
    mov  x1, x25
    bl   announce
    b    4f
3:  ldr  w8, [x21, #0x34]
    cmp  w8, #1
    b.le 31f
    mov  w0, #45
    mov  x1, xzr
    bl   announce
31: mov  w8, #-1
    str  w8, [x21, #0x34]
    ldr  x0, [x21, #0x58]
    cbz  x0, 32f
    mov  w1, #0
    mov  x2, xzr
    bl   ext_set_active
32: mov  w0, #0
    bl   colour
    b    9f
4:  cbz  w26, 9f
    cmp  w19, #10
    b.le 8f
    ldr  w8, [x21, #0x34]
    cmp  w8, w22
    b.eq 9f
    str  w22, [x21, #0x34]
    mov  w0, #1
    bl   colour
    mov  x0, x21
    mov  w1, w22
    mov  x2, xzr
    bl   ext_animate_last_seconds
    b    9f
8:  str  w22, [x21, #0x34]
    mov  w0, #0
    bl   colour
9:  mov  w0, w19
    ldp  x25, x26, [sp, #0x40]
    ldp  x23, x24, [sp, #0x30]
    ldp  x21, x22, [sp, #0x20]
    ldp  x19, x20, [sp, #0x10]
    ldp  x29, x30, [sp], #0x60
    ret
colour:
    ldrb w8, [x21, #0x32]
    cmp  w8, w0
    b.eq 9f
    stp  x29, x30, [sp, #-0x20]!
    stp  x19, x20, [sp, #0x10]
    mov  w19, w0
    strb w0, [x21, #0x32]
    ldr  x20, [x21, #0x50]
    cbz  x20, 8f
    adr  x8, white
    cbz  w19, 1f
    adr  x8, gold
1:  ldp  s0, s1, [x8]
    ldp  s2, s3, [x8, #8]
    mov  x0, x20
    mov  x1, xzr
    bl   ext_set_color
    mov  x0, x20
    mov  x1, xzr
    bl   ext_get_transform
    cbz  x0, 8f
    mov  x20, x0
    mov  x1, xzr
    bl   ext_child_count
    cmp  w0, #1
    b.lt 8f
    mov  x0, x20
    mov  w1, #0
    mov  x2, xzr
    bl   ext_get_child
    cbz  x0, 8f
    mov  x1, xzr
    bl   ext_get_game_object
    cbz  x0, 8f
    mov  w1, w19
    mov  x2, xzr
    bl   ext_set_active
8:  ldp  x19, x20, [sp, #0x10]
    ldp  x29, x30, [sp], #0x20
9:  ret
announce:
    stp  x29, x30, [sp, #-0x30]!
    stp  x19, x20, [sp, #0x10]
    stp  x21, x22, [sp, #0x20]
    mov  w19, w0
    mov  x20, x1
    adrp x0, slot_announcer@PAGE
    ldr  x0, [x0, slot_announcer@PAGEOFF]
    ldr  x8, [x0]
    tbz  x8, #0, 1f
    bl   ext_init_metadata
1:  adrp x0, slot_strings@PAGE
    ldr  x0, [x0, slot_strings@PAGEOFF]
    ldr  x8, [x0]
    tbz  x8, #0, 2f
    bl   ext_init_metadata
2:  adrp x8, slot_announcer@PAGE
    ldr  x8, [x8, slot_announcer@PAGEOFF]
    ldr  x0, [x8]
    bl   ext_get_instance
    cbz  x0, 9f
    mov  x21, x0
    adrp x8, slot_strings@PAGE
    ldr  x8, [x8, slot_strings@PAGEOFF]
    ldr  x0, [x8]
    mov  w1, #1
    bl   ext_array_new
    cbz  x0, 9f
    mov  x22, x0
    cbz  x20, 3f
    mov  x0, x20
    mov  x1, xzr
    bl   ext_player_name
    mov  x1, x0
    add  x0, x22, #0x20
    str  x1, [x0]
    bl   ext_write_barrier
3:  mov  x0, x21
    mov  w1, w19
    mov  x2, x22
    mov  x3, xzr
    bl   ext_trigger_line
9:  ldp  x21, x22, [sp, #0x20]
    ldp  x19, x20, [sp, #0x10]
    ldp  x29, x30, [sp], #0x30
    ret
    .p2align 3
gold:  .float 1.0, 0.8, 0.15, 1.0
white: .float 1.0, 1.0, 1.0, 1.0
