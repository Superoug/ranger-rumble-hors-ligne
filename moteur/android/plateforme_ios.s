.text
.globl _pf_start
_pf_start:
    ret
.globl _pf_tags
_pf_tags:
    stp  x29, x30, [sp, #-0x20]!
    str  x19, [sp, #0x10]
    bl   ext_tags_string
    ldr  w8, ios
    cbz  w8, 9f
    cbz  x0, 9f
    mov  x19, x0
    adr  x0, android_text
    bl   ext_string_new
    str  x0, [sp, #0x18]
    adr  x0, ios_text
    bl   ext_string_new
    mov  x2, x0
    ldr  x1, [sp, #0x18]
    mov  x0, x19
    mov  x3, xzr
    bl   ext_string_replace
9:  ldr  x19, [sp, #0x10]
    ldp  x29, x30, [sp], #0x20
    ret
    .p2align 2
android_text:  .asciz "platform/android"
ios_text:      .asciz "platform/ios"
    .p2align 2
mark:      .ascii "RRPLATEFORME"
ios:       .word 0
