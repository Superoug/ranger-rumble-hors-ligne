.text
.globl _rv_start
_rv_start:
.globl _rv_rarity
_rv_rarity:
    cmp  w20, #0xa0
    b.eq 1f
    cmp  w20, #0xe4
1:  ret
.globl _rv_background
_rv_background:
    cmp  w8, #0x10
    b.eq 1f
    cmp  w8, #0x16
1:  ret
