#!/usr/bin/env python3
"""Turns an Android ARM64 library (ELF .so) into a Mach-O dylib that dyld maps and that can be
code-signed, for systems that refuse new executable memory (iOS, a hardened macOS process).

The ELF image is kept byte for byte at one 16 KB-aligned offset, so every PC-relative reference
inside it stays valid. Only the code is changed, ahead of time:
- each "mrs xN, TPIDR_EL0" becomes "adrp xN, <block>" (as elf_chargeur.c does at run time);
- the computer-only patches (RUSTINES) are applied;
- with --x18, each instruction that uses x18 becomes a branch to a small routine that does the
  same work on a per-thread copy of x18 kept in a pthread key (Apple systems clear x18).

Relocations, imports and constructors are left to the loader (elf_macho.c), which writes them
into the writable segment. Layout of the dylib (virtual addresses):

    0x0000          Mach-O header, load commands, info block (INFO_OFFSET)
    0x4000          x18 routines (only with --x18), then padding to 16 KB
    IMAGE           the ELF image: read-only and code segments  -> __TEXT (r-x)
    IMAGE + rw      the ELF writable segments, then one block page -> __DATA (rw-)
    after           __LINKEDIT (empty tables, then the code signature)

usage: elf_vers_macho.py <lib.so> <sortie.dylib> [--plateforme macos|ios|ios-sim]
                         [--x18 auto|<recette.json>] [--ecrire-recette <recette.json>]

The dylib is signed ad hoc here (as codesign -s - does), so this also runs on Windows.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile

PAGE = 0x4000
INFO_OFFSET = 0x3000
KOFF = 0x100            # offset, in the block page, of the word holding key * 8
GUARD = 0x28            # stack guard read through the rewritten TPIDR_EL0

# Patches for the computer only (same list as essai_p1.m): library, address, expected, new.
RUSTINES = [
    ("libil2cpp.so", 0x4371268, 0xA9BC67FE, 0xD65F03C0),  # Main.ConfigureCrashlytics: ret
    ("libil2cpp.so", 0x4617820, 0xF81E0FFE, 0x52800020),  # UserAllowedNotifications: mov w0, #1
    ("libil2cpp.so", 0x4617824, 0xA9014FF4, 0xD65F03C0),  # ... ret
    # NativeCrashlyticsHijacker.LogException: the call to Crashlytics (no Firebase here, it throws and
    # froze Bolt Rush after a failed asset load); the exception is still logged by Unity's own handler.
    ("libil2cpp.so", 0x3EF1154, 0x9422171D, 0xD503201F),  # nop
]

PLATEFORMES = {"macos": (1, (14, 4)), "ios": (2, (15, 0)), "ios-sim": (7, (15, 0))}


def echec(message):
    sys.stderr.write("elf_vers_macho : %s\n" % message)
    sys.exit(1)


def haut(v):
    return (v + PAGE - 1) & ~(PAGE - 1)


def bas(v):
    return v & ~(PAGE - 1)


# --- ELF ------------------------------------------------------------------------------------

class Elf:
    def __init__(self, chemin):
        self.chemin = chemin
        self.nom = os.path.basename(chemin)
        d = self.donnees = open(chemin, "rb").read()
        if d[:4] != b"\x7fELF" or d[4] != 2 or struct.unpack_from("<H", d, 18)[0] != 183:
            echec("%s n'est pas une bibliothèque ELF ARM64" % chemin)
        phoff, = struct.unpack_from("<Q", d, 0x20)
        shoff, = struct.unpack_from("<Q", d, 0x28)
        phentsize, phnum, shentsize, shnum, shstrndx = struct.unpack_from("<HHHHH", d, 0x36)
        self.segments = []
        self.dynamique = None
        for i in range(phnum):
            t, f, off, va, pa, fs, ms, al = struct.unpack_from("<IIQQQQQQ", d, phoff + i * phentsize)
            if t == 1:
                self.segments.append(dict(flags=f, off=off, va=va, fs=fs, ms=ms))
            elif t == 2:
                self.dynamique = va
        self.sections = {}
        if shoff and shnum:
            entetes = [struct.unpack_from("<IIQQQQIIQQ", d, shoff + i * shentsize) for i in range(shnum)]
            noms = entetes[shstrndx]
            for e in entetes:
                o = noms[4] + e[0]
                self.sections[d[o:d.index(b"\0", o)].decode()] = e
        dynsym = [e for e in self.sections.values() if e[1] == 11]
        self.nsym = dynsym[0][5] // 24 if dynsym else 0
        self.segments.sort(key=lambda s: s["va"])
        fin = max(s["va"] + s["ms"] for s in self.segments)
        self.taille = haut(fin)
        lecture = [s for s in self.segments if not s["flags"] & 2]
        ecriture = [s for s in self.segments if s["flags"] & 2]
        if not ecriture or max(s["va"] for s in lecture) > min(s["va"] for s in ecriture):
            echec("%s : segments dans un ordre inattendu" % self.nom)
        self.fin_texte = haut(max(s["va"] + s["ms"] for s in lecture))
        self.debut_donnees = bas(min(s["va"] for s in ecriture))
        self.fin_fichier_donnees = haut(max(s["va"] + s["fs"] for s in ecriture))
        if self.debut_donnees < self.fin_texte:
            echec("%s : une page est à la fois code et données" % self.nom)
        self.code = [(s["va"], s["va"] + s["fs"]) for s in self.segments if s["flags"] & 1]
        self.verifier_relocations()

    def image(self):
        img = bytearray(self.taille + PAGE)  # one more page: the block (guard, x18 key)
        for s in self.segments:
            img[s["va"]:s["va"] + s["fs"]] = self.donnees[s["off"]:s["off"] + s["fs"]]
        return img

    def verifier_relocations(self):
        # Every relocation must land in a writable segment (no text relocations).
        d = self.donnees
        dyn = {}
        seg = [s for s in self.segments if s["va"] <= self.dynamique < s["va"] + s["fs"]][0]
        pos = self.dynamique - seg["va"] + seg["off"]
        while True:
            tag, val = struct.unpack_from("<qQ", d, pos)
            pos += 16
            if tag == 0:
                break
            dyn[tag] = val
        if dyn.get(22) or (dyn.get(30, 0) & 4):  # DT_TEXTREL, DF_TEXTREL
            echec("%s : relocations dans le code" % self.nom)

        def fichier(va):
            for s in self.segments:
                if s["va"] <= va < s["va"] + s["fs"]:
                    return va - s["va"] + s["off"]
            echec("%s : adresse %#x hors fichier" % (self.nom, va))

        for adr, taille in ((7, 8), (23, 2)):  # DT_RELA/DT_RELASZ, DT_JMPREL/DT_PLTRELSZ
            if adr not in dyn:
                continue
            debut = fichier(dyn[adr])
            for i in range(dyn[taille] // 24):
                off, = struct.unpack_from("<Q", d, debut + 24 * i)
                if not self.debut_donnees <= off < self.taille:
                    echec("%s : relocation hors des données (%#x)" % (self.nom, off))


# --- ARM64 encodings used by the routines ---------------------------------------------------

def stp(r1, r2, base, imm):
    return 0xA9000000 | (((imm // 8) & 0x7F) << 15) | (r2 << 10) | (base << 5) | r1


def ldp(r1, r2, base, imm):
    return 0xA9400000 | (((imm // 8) & 0x7F) << 15) | (r2 << 10) | (base << 5) | r1


def mrs_tpidrro(rd):
    return 0xD53BD060 | rd


def and_moins8(rd, rn):  # and rd, rn, #0xfffffffffffffff8
    return 0x92400000 | (61 << 16) | (60 << 10) | (rn << 5) | rd


def adrp(rd, cible, pc):
    imm = (cible >> 12) - (pc >> 12)
    if not -(1 << 20) <= imm < (1 << 20):
        echec("adrp hors de portée")
    return 0x90000000 | ((imm & 3) << 29) | (((imm >> 2) & 0x7FFFF) << 5) | rd


def add_imm(rd, rn, imm):
    return 0x91000000 | ((imm & 0xFFF) << 10) | (rn << 5) | rd


def add_reg(rd, rn, rm):
    return 0x8B000000 | (rm << 16) | (rn << 5) | rd


def ldr_x(rt, rn, off=0):
    return 0xF9400000 | ((off // 8) << 10) | (rn << 5) | rt


def str_x(rt, rn):
    return 0xF9000000 | (rn << 5) | rt


def b(pc, cible):
    d = (cible - pc) // 4
    if not -(1 << 25) <= d < (1 << 25):
        echec("branche hors de portée")
    return 0x14000000 | (d & 0x3FFFFFF)


def br(rn):
    return 0xD61F0000 | (rn << 5)


def signe(v, bits):
    return v - (1 << bits) if v & (1 << (bits - 1)) else v


# --- x18: analysis (needs llvm-objdump, done once) ------------------------------------------

def objdump():
    for chemin in ("/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/llvm-objdump",
                   shutil.which("llvm-objdump") or ""):
        if chemin and os.path.exists(chemin):
            return chemin
    echec("llvm-objdump introuvable (Xcode) : utiliser une recette x18 déjà faite")


LIGNE = re.compile(r"^\s*([0-9a-f]+):\s+(\S+)\s*(.*?)\s*$")
REG18 = re.compile(r"\b([xw])18\b")
REGS = re.compile(r"\b[xw](\d+)\b")


def desassembler_fichier(chemin):
    sortie = subprocess.run([objdump(), "-d", "--no-show-raw-insn", chemin], capture_output=True, text=True).stdout
    for ligne in sortie.splitlines():
        m = LIGNE.match(ligne)
        if m and not m.group(2).startswith("<"):
            yield int(m.group(1), 16), m.group(2), re.sub(r"\s*//.*$", "", m.group(3))


def desassembler_mots(mots):
    """Disassembles a list of instruction words (in a throwaway ELF object)."""
    texte = struct.pack("<%dI" % len(mots), *mots)
    noms = b"\0.text\0.shstrtab\0"
    shoff = 64 + len(texte) + len(noms)
    shoff += (-shoff) % 8
    entete = struct.pack("<4sBBBBB7sHHIQQQIHHHHHH", b"\x7fELF", 2, 1, 1, 0, 0, b"\0" * 7, 1, 183, 1, 0, 0, shoff, 0,
                         64, 0, 0, 64, 3, 2)
    sections = bytes(64)
    sections += struct.pack("<IIQQQQIIQQ", 1, 1, 6, 0, 64, len(texte), 0, 0, 4, 0)
    sections += struct.pack("<IIQQQQIIQQ", 7, 3, 0, 0, 64 + len(texte), len(noms), 0, 0, 1, 0)
    corps = entete + texte + noms
    corps += bytes(shoff - len(corps)) + sections
    with tempfile.NamedTemporaryFile(suffix=".o", delete=False) as f:
        f.write(corps)
    try:
        resultat = {}
        for pc, mnemo, ops in desassembler_fichier(f.name):
            resultat[pc // 4] = (mnemo, ops)
        return [resultat.get(i, ("?", "")) for i in range(len(mots))]
    finally:
        os.unlink(f.name)


def genre_pc(mot):
    """Kind of a PC-relative instruction that has x18 in its Rd/Rt field, else None."""
    if mot & 0x9F000000 == 0x90000000:
        return "adrp"
    if mot & 0x9F000000 == 0x10000000:
        return "adr"
    if mot & 0xBF000000 == 0x18000000:
        return "ldr_lit"
    if mot & 0xFF000000 == 0x98000000:
        return "ldrsw_lit"
    if mot & 0x7E000000 == 0x34000000:
        return "cb"
    if mot & 0x7E000000 == 0x36000000:
        return "tb"
    return None


def analyser_x18(elf, img):
    """Finds every x18 instruction in the code and how to rewrite it: the register fields that
    hold x18, and two scratch registers it does not use."""
    instructions = []
    for pc, mnemo, ops in desassembler_fichier(elf.chemin):
        if not REG18.search(ops) or not any(a <= pc < z for a, z in elf.code):
            continue
        instructions.append((pc, mnemo, ops))
    # Branches through x18 (jump tables) need a register that the whole function never uses.
    toutes = None
    entrees, candidats = [], []
    for pc, mnemo, ops in instructions:
        mot, = struct.unpack_from("<I", img, pc)
        utilises = {int(r) for r in REGS.findall(ops)}
        libres = [r for r in (9, 10, 11, 12, 13, 14, 15, 16, 17, 0, 1, 2, 3, 4, 5, 6, 7, 8) if r not in utilises]
        e = dict(pc=pc, mot=mot, texte="%s %s" % (mnemo, ops), r1=libres[0], r2=libres[1])
        if mnemo in ("br", "blr"):
            if mnemo == "blr" or (mot & 0xFFFFFC1F) != 0xD61F0000:
                echec("%#x : %s par x18 non géré" % (pc, mnemo))
            if toutes is None:
                toutes = list(desassembler_fichier(elf.chemin))
            e["genre"] = "br"
            e["saut"] = registre_mort(toutes, pc)
        elif genre_pc(mot) and (mot & 31) == 18:
            e["genre"] = genre_pc(mot)
        else:
            e["genre"] = "simple"
            champs = [c for c in (0, 5, 10, 16) if (mot >> c) & 31 == 18]
            for masque in range(1, 1 << len(champs)):
                choisis = [champs[i] for i in range(len(champs)) if masque >> i & 1]
                nouveau = mot
                for c in choisis:
                    nouveau = (nouveau & ~(31 << c)) | (e["r1"] << c)
                candidats.append((len(entrees), choisis, nouveau))
        entrees.append(e)
    textes = desassembler_mots([c[2] for c in candidats])
    for (i, choisis, nouveau), (mnemo, ops) in zip(candidats, textes):
        e = entrees[i]
        if "champs" in e:
            continue
        attendu = REG18.sub(lambda m: "%s%d" % (m.group(1), e["r1"]), e["texte"])
        if "%s %s" % (mnemo, ops) == attendu:
            e["champs"] = choisis
    for e in entrees:
        if e["genre"] == "simple" and "champs" not in e:
            echec("%#x : pas de réécriture trouvée pour « %s »" % (e["pc"], e["texte"]))
    return entrees


def registre_mort(toutes, pc):
    """A register among x0-x17 that the function around pc (from the previous ret to the next
    ret, no call inside) never names: free to hold the jump target."""
    i = [k for k, t in enumerate(toutes) if t[0] == pc][0]
    debut = i
    while debut > 0 and toutes[debut - 1][1] != "ret":
        debut -= 1
    fin = i
    while fin < len(toutes) - 1 and toutes[fin][1] != "ret":
        fin += 1
    utilises = set()
    for _, mnemo, ops in toutes[debut:fin + 1]:
        if mnemo in ("bl", "blr"):
            echec("%#x : appel dans la fonction d'un saut par x18" % pc)
        utilises |= {int(r) for r in REGS.findall(ops)}
    libres = [r for r in range(18) if r not in utilises]
    if not libres:
        echec("%#x : aucun registre libre pour le saut par x18" % pc)
    return libres[0]


# --- x18: rewrite ---------------------------------------------------------------------------

def routine(e, pc_routine, image, bloc):
    """Instructions of the routine for one x18 instruction (addresses are dylib addresses)."""
    r1, r2, sp = e["r1"], e["r2"], 31
    pc_orig = image + e["pc"]
    mot = e["mot"]
    code = []

    def ici():
        return pc_routine + 4 * len(code)

    # Spill two scratch registers in the red zone (Linux code keeps nothing below sp; Darwin
    # signal delivery skips 128 bytes), find this thread's x18 slot: r2 = &slot.
    code += [stp(r1, r2, sp, -128), mrs_tpidrro(r2), and_moins8(r2, r2)]
    code.append(adrp(r1, bloc, ici()))
    code += [ldr_x(r1, r1, KOFF), add_reg(r2, r2, r1)]
    g = e["genre"]
    if g == "simple":
        nouveau = mot
        for c in e["champs"]:
            nouveau = (nouveau & ~(31 << c)) | (r1 << c)
        code += [ldr_x(r1, r2), nouveau, str_x(r1, r2)]
    elif g in ("adrp", "adr", "ldr_lit", "ldrsw_lit"):
        if g == "adrp":
            imm = signe(((mot >> 5) & 0x7FFFF) << 2 | ((mot >> 29) & 3), 21)
            cible = (pc_orig & ~0xFFF) + (imm << 12)
            code.append(adrp(r1, cible, ici()))
        else:
            if g == "adr":
                cible = pc_orig + signe(((mot >> 5) & 0x7FFFF) << 2 | ((mot >> 29) & 3), 21)
            else:
                cible = pc_orig + 4 * signe((mot >> 5) & 0x7FFFF, 19)
            code.append(adrp(r1, cible, ici()))
            code.append(add_imm(r1, r1, cible & 0xFFF))
            if g == "ldr_lit":
                code.append((0xF9400000 if mot & 0x40000000 else 0xB9400000) | (r1 << 5) | r1)
            elif g == "ldrsw_lit":
                code.append(0xB9800000 | (r1 << 5) | r1)
        code.append(str_x(r1, r2))
    elif g in ("cb", "tb"):
        if g == "cb":
            cible = pc_orig + 4 * signe((mot >> 5) & 0x7FFFF, 19)
            test = (mot & 0xFF000000) | (3 << 5) | r1          # cbz/cbnz r1, +12
        else:
            cible = pc_orig + 4 * signe((mot >> 5) & 0x3FFF, 14)
            test = (mot & 0xFFF80000) | (3 << 5) | r1          # tbz/tbnz r1, #bit, +12
        code += [ldr_x(r1, r2), test, ldp(r1, r2, sp, -128)]
        code.append(b(ici(), pc_orig + 4))
        code.append(ldp(r1, r2, sp, -128))
        code.append(b(ici(), cible))
        return code
    elif g == "br":
        saut = e["saut"]
        code += [ldr_x(saut, r2), ldp(r1, r2, sp, -128), br(saut)]
        return code
    code.append(ldp(r1, r2, sp, -128))
    code.append(b(ici(), pc_orig + 4))
    return code


def reecrire_x18(entrees, img, image, debut_routines, bloc):
    routines = bytearray()
    for e in entrees:
        pc_routine = debut_routines + len(routines)
        code = routine(e, pc_routine, image, bloc)
        routines += struct.pack("<%dI" % len(code), *code)
        struct.pack_into("<I", img, e["pc"], b(image + e["pc"], pc_routine))
    return routines


# --- other rewrites ---------------------------------------------------------------------------

def reecrire_tpidr(elf, img):
    """mrs xN, TPIDR_EL0 -> adrp xN, <block> (same page for every thread: the stack guard)."""
    n = 0
    bloc = elf.taille
    for a, z in elf.code:
        for pc in range(a, z - 3, 4):
            mot, = struct.unpack_from("<I", img, pc)
            if mot & 0xFFFFFFE0 == 0xD53BD040:
                struct.pack_into("<I", img, pc, adrp(mot & 31, bloc, pc))
                n += 1
    return n


def appliquer_rustines(elf, img):
    n = 0
    for nom, adresse, attendu, nouveau in RUSTINES:
        if nom != elf.nom:
            continue
        mot, = struct.unpack_from("<I", img, adresse)
        if mot != attendu:
            echec("%s+%#x ne contient pas %#x (%#x)" % (nom, adresse, attendu, mot))
        struct.pack_into("<I", img, adresse, nouveau)
        n += 1
    return n


# --- Mach-O -----------------------------------------------------------------------------------

def commande_segment(nom, vmaddr, vmsize, fileoff, filesize, prot, sections):
    corps = struct.pack("<II16sQQQQiiII", 0x19, 72 + 80 * len(sections), nom.encode(), vmaddr, vmsize, fileoff, filesize,
                        prot, prot, len(sections), 0)
    for sect, adr, taille, off, drapeaux in sections:
        corps += struct.pack("<16s16sQQIIIIIIII", sect.encode(), nom.encode(), adr, taille, off, 14, 0, 0, drapeaux, 0, 0, 0)
    return corps


def chaine_commande(cmd, entete, texte):
    t = texte.encode() + b"\0"
    taille = len(entete) + 8 + len(t)
    taille += (-taille) % 8
    return struct.pack("<II", cmd, taille) + entete + t + bytes(taille - 8 - len(entete) - len(t))


def ecrire_macho(elf, img, routines, sortie, plateforme, infos):
    code_plateforme, (maj, mineur) = PLATEFORMES[plateforme]
    zone_routines = haut(len(routines)) if routines else 0
    image = PAGE + zone_routines
    texte_vm = image + elf.fin_texte
    donnees_vm = image + elf.debut_donnees
    donnees_taille = image + elf.taille + PAGE - donnees_vm
    donnees_fichier = elf.fin_fichier_donnees - elf.debut_donnees
    linkedit_vm = donnees_vm + donnees_taille
    linkedit_off = texte_vm + donnees_fichier
    linkedit = bytes(16)                      # empty string table
    signature_off = linkedit_off + len(linkedit)
    identifiant = os.path.basename(sortie).rsplit(".", 1)[0]
    signature_taille = taille_signature(signature_off, identifiant)
    nom_id = "@rpath/" + os.path.basename(sortie)
    uuid = hashlib.md5(bytes(img[:65536]) + nom_id.encode() + routines).digest()

    commandes = [
        commande_segment("__TEXT", 0, texte_vm, 0, texte_vm, 5,
                         [("__text", PAGE, texte_vm - PAGE, PAGE, 0x80000400)]),
        commande_segment("__DATA", donnees_vm, donnees_taille, texte_vm, donnees_fichier, 3,
                         [("__data", donnees_vm, donnees_fichier, texte_vm, 0),
                          ("__bss", donnees_vm + donnees_fichier, donnees_taille - donnees_fichier, 0, 0x1)]),
        commande_segment("__LINKEDIT", linkedit_vm, haut(len(linkedit) + signature_taille), linkedit_off,
                         len(linkedit) + signature_taille, 1, []),
        chaine_commande(0xD, struct.pack("<IIII", 24, 0, 0x10000, 0x10000), nom_id),            # LC_ID_DYLIB
        chaine_commande(0xC, struct.pack("<IIII", 24, 0, 0x10000, 0x10000), "/usr/lib/libSystem.B.dylib"),
        struct.pack("<II16s", 0x1B, 24, uuid),                                                      # LC_UUID
        struct.pack("<IIIIII", 0x32, 24, code_plateforme, maj << 16 | mineur << 8, 0x1A0000, 0),  # LC_BUILD_VERSION
        struct.pack("<IIIIII", 0x2, 24, linkedit_off, 0, linkedit_off, len(linkedit)),             # LC_SYMTAB
        struct.pack("<II18I", 0xB, 80, *([0] * 18)),                                               # LC_DYSYMTAB
        struct.pack("<IIII", 0x1D, 16, signature_off, signature_taille),                           # LC_CODE_SIGNATURE
    ]
    taille_commandes = sum(len(c) for c in commandes)
    if 32 + taille_commandes + 256 > INFO_OFFSET:
        echec("en-tête trop grand")
    entete = struct.pack("<IiiIIIII", 0xFEEDFACF, 0x0100000C, 0, 6, len(commandes), taille_commandes,
                         0x1 | 0x4 | 0x80 | 0x100000, 0)
    tete = bytearray(PAGE)
    tete[:32 + taille_commandes] = entete + b"".join(commandes)
    info = struct.pack("<8sQQQQQQQ64s", b"RRELF01\0", image, elf.taille, image + elf.taille, elf.nsym,
                       infos["x18"], infos["tpidr"], KOFF, elf.nom.encode())
    tete[INFO_OFFSET:INFO_OFFSET + len(info)] = info

    with open(sortie, "wb") as f:
        f.write(tete)
        f.write(routines + bytes(zone_routines - len(routines)))
        f.write(img[:elf.fin_texte])
        f.write(img[elf.debut_donnees:elf.fin_fichier_donnees])
        f.write(linkedit)
    signer(sortie, signature_off, identifiant, texte_vm, signature_taille)
    return image


# --- ad hoc code signature (what codesign -s - writes), in Python: the tool also runs on Windows ---------

PAGE_SIGNEE = 4096


def _blobs_signature(fin_code, identifiant):
    """The sizes of the code directory, and the empty requirements and CMS blobs."""
    ident = identifiant.encode() + b"\0"
    pages = (fin_code + PAGE_SIGNEE - 1) // PAGE_SIGNEE
    return 88 + len(ident) + 32 * (2 + pages), ident, pages


def taille_signature(fin_code, identifiant):
    repertoire, _, _ = _blobs_signature(fin_code, identifiant)
    total = 12 + 3 * 8 + repertoire + 12 + 8
    return total + (-total) % 16


def signer(chemin, fin_code, identifiant, texte_limite, taille):
    """Appends the signature at fin_code: SHA-256 of each 4 KB page before it, ad hoc (no certificate)."""
    longueur, ident, pages = _blobs_signature(fin_code, identifiant)
    exigences = struct.pack(">III", 0xFADE0C01, 12, 0)
    cms = struct.pack(">II", 0xFADE0B01, 8)
    speciales = [hashlib.sha256(exigences).digest(), bytes(32)]  # slots -2 (requirements), -1 (Info.plist)
    empreintes = []
    with open(chemin, "rb") as f:
        lu = 0
        while lu < fin_code:
            bloc = f.read(min(PAGE_SIGNEE, fin_code - lu))
            if not bloc:
                echec("fichier plus court que prévu")
            empreintes.append(hashlib.sha256(bloc).digest())
            lu += len(bloc)
    if len(empreintes) != pages:
        echec("pages à signer inattendues")
    decalage_empreintes = 88 + len(ident) + 32 * 2
    repertoire = struct.pack(">IIIIIIIIIBBBBIIIIQQQQ", 0xFADE0C02, longueur, 0x20400, 0x2, decalage_empreintes, 88, 2,
                             pages, fin_code, 32, 2, 0, 12, 0, 0, 0, 0, 0, 0, texte_limite, 0)
    repertoire += ident + b"".join(speciales) + b"".join(empreintes)
    if len(repertoire) != longueur:
        echec("signature mal formée")
    entete = 12 + 3 * 8
    blobs = [(0, repertoire), (2, exigences), (0x10000, cms)]
    index, contenu, position = b"", b"", entete
    for genre, blob in blobs:
        index += struct.pack(">II", genre, position)
        contenu += blob
        position += len(blob)
    super_blob = struct.pack(">III", 0xFADE0CC0, position, len(blobs)) + index + contenu
    with open(chemin, "r+b") as f:
        f.seek(fin_code)
        f.write(super_blob + bytes(taille - len(super_blob)))


def sha256(chemin):
    h = hashlib.sha256()
    with open(chemin, "rb") as f:
        for bloc in iter(lambda: f.read(1 << 20), b""):
            h.update(bloc)
    return h.hexdigest()


def convertir(chemin_elf, sortie, plateforme="ios", recette=None, ecrire_recette=None):
    """chemin_elf -> sortie (signed dylib). recette: "auto" (llvm-objdump) or a JSON file for x18. The infos."""
    elf = Elf(chemin_elf)
    img = elf.image()
    infos = dict(x18=0, tpidr=reecrire_tpidr(elf, img), rustines=appliquer_rustines(elf, img))
    routines = b""
    if recette:
        if recette == "auto":
            entrees = analyser_x18(elf, img)
        else:
            with open(recette) as f:
                donnees = json.load(f)
            if donnees["sha256"] != sha256(chemin_elf):
                echec("la recette x18 ne correspond pas à %s" % elf.nom)
            entrees = donnees["instructions"]
            for e in entrees:  # the recipe holds places and registers only, the words come from the library
                e["mot"], = struct.unpack_from("<I", img, e["pc"])
        if ecrire_recette:
            with open(ecrire_recette, "w") as f:
                json.dump(dict(bibliotheque=elf.nom, sha256=sha256(chemin_elf), instructions=[
                    {k: v for k, v in e.items() if k not in ("texte", "mot")} for e in entrees]), f)
        # Routines sit before the image; their size is known before their content.
        zone = haut(sum(4 * len(routine(e, 0, PAGE, 0)) for e in entrees))
        image = PAGE + zone
        routines = reecrire_x18(entrees, img, image, PAGE, image + elf.taille)
        if haut(len(routines)) != zone:
            echec("taille des routines x18 inattendue")
        infos["x18"] = len(entrees)
    ecrire_macho(elf, img, routines, sortie, plateforme, infos)
    infos["nom"] = elf.nom
    return infos


def main():
    p = argparse.ArgumentParser()
    p.add_argument("elf")
    p.add_argument("sortie")
    p.add_argument("--plateforme", default="ios", choices=sorted(PLATEFORMES))
    p.add_argument("--x18", help="auto (analyse avec llvm-objdump) ou une recette JSON")
    p.add_argument("--ecrire-recette")
    a = p.parse_args()
    infos = convertir(a.elf, a.sortie, a.plateforme, a.x18, a.ecrire_recette)
    print("%s -> %s : %d TPIDR, %d x18, %d rustines, %.1f Mo" % (infos["nom"], os.path.basename(a.sortie), infos["tpidr"],
          infos["x18"], infos["rustines"], os.path.getsize(a.sortie) / 1e6))


if __name__ == "__main__":
    main()
