.text
.globl _rv_start
_rv_start:
.globl _rv_rarity
_rv_rarity:
    cmp  w20, #0xa0
    b.eq 2f
    cmp  w20, #0xe4
    b.ne 1f
2:  ldr  x9, [x19, #0x20]
    cbz  x9, 3f
    ldr  x9, [x19, #0x30]
    cbz  x9, 3f
    cmp  w9, w9
1:  ret
3:  cmn  w20, #1
    ret
.globl _rv_background
_rv_background:
    cmp  w8, #0x10
    b.eq 1f
    cmp  w8, #0x16
1:  ret
