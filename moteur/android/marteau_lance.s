.text
.equ WRENCH_EFFECT, 84
.equ RIVET, 16
.globl _mt_start
_mt_start:
    ret
.globl _mt_awake
_mt_awake:
    stp  x29, x30, [sp, #-0x1d0]!
    stp  x19, x20, [sp, #0x10]
    stp  x22, x23, [sp, #0x20]
    ldr  x22, [x19, #0x118]
    cbz  x22, 9f
    ldr  w8, [x22, #0x10]
    cmp  w8, #WRENCH_EFFECT
    b.ne 9f
    strb wzr, [x22, #0x5e]
    cbz  x20, 9f
    ldr  x8, [x20, #0x38]
    cbz  x8, 9f
    ldr  x23, [x8, #0x18]
    cbz  x23, 9f
    adrp x0, slot_projectile@PAGE
    ldr  x0, [x0, slot_projectile@PAGEOFF]
    bl   ext_init_metadata
    adrp x8, slot_projectile@PAGE
    ldr  x8, [x8, slot_projectile@PAGEOFF]
    ldr  x3, [x8]
    mov  x0, x23
    ldr  x1, [x19, #0x28]
    add  x2, sp, #0x40
    bl   ext_try_get_projectile
    tbz  w0, #0, 9f
    ldr  x8, [sp, #0x78]
    str  x8, [sp, #0x30]
    adrp x0, slot_actor@PAGE
    ldr  x0, [x0, slot_actor@PAGEOFF]
    bl   ext_init_metadata
    adrp x8, slot_actor@PAGE
    ldr  x8, [x8, slot_actor@PAGEOFF]
    ldr  x19, [x8]
    ldr  x8, [x19, #0x38]
    cbnz x8, 1f
    mov  x0, x19
    bl   ext_init_rgctx
1:  ldr  x8, [x19, #0x38]
    ldr  x3, [x8, #8]
    ldr  x0, [x23, #0xa0]
    cbz  x0, 9f
    ldr  x1, [sp, #0x30]
    add  x2, sp, #0x38
    str  xzr, [x2]
    bl   ext_actor_pointer
    tbz  w0, #0, 9f
    ldr  x8, [sp, #0x38]
    cbz  x8, 9f
    ldr  w8, [x8, #0xc]
    cmp  w8, #RIVET
    cset w8, eq
    strb w8, [x22, #0x5e]
9:  ldp  x19, x20, [sp, #0x10]
    ldr  x21, [x19, #0x118]
    ldp  x22, x23, [sp, #0x20]
    ldp  x29, x30, [sp], #0x1d0
    ret
.globl _mt_spawned
_mt_spawned:
    str  w21, [x8, #0x58]
    ldr  w9, [x8, #0x10]
    cmp  w9, #WRENCH_EFFECT
    b.ne 9f
    cbz  x20, 9f
    stp  x29, x30, [sp, #-0x30]!
    stp  x8, x19, [sp, #0x10]
    stp  x20, x21, [sp, #0x20]
    ldrb w19, [x8, #0x5e]
    mov  x0, x20
    mov  x1, xzr
    bl   ext_go_transform
    cbz  x0, 8f
    mov  x20, x0
    adr  x0, s_hammer
    mov  w1, w19
    bl   show
    cbz  w0, 8f
    adr  x0, s_wrench
    eor  w1, w19, #1
    bl   show
8:  ldp  x20, x21, [sp, #0x20]
    ldp  x8, x19, [sp, #0x10]
    ldp  x29, x30, [sp], #0x30
9:  ret
show:
    stp  x29, x30, [sp, #-0x20]!
    str  x1, [sp, #0x10]
    bl   ext_string_new
    mov  x1, x0
    mov  x0, x20
    mov  x2, xzr
    bl   ext_find
    cbz  x0, 1f
    mov  x1, xzr
    bl   ext_get_gameobject
    cbz  x0, 1f
    ldr  x1, [sp, #0x10]
    mov  x2, xzr
    bl   ext_set_active
    mov  w0, #1
    ldp  x29, x30, [sp], #0x20
    ret
1:  mov  w0, wzr
    ldp  x29, x30, [sp], #0x20
    ret
s_hammer:  .asciz "Hammer_MeshRenderer"
s_wrench:  .asciz "Wrench_MeshRenderer"
    .p2align 2
