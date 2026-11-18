# Ranger Rumble Offline

**English** · [Français](README.fr.md)

A tool to keep playing *Ratchet & Clank: Ranger Rumble* after its servers close on May 1, 2027.
For Windows and macOS, in 6 languages: English, French, Spanish, German, Italian and Portuguese.

## What the tool does

The tool opens on a home screen with the game's pictures. Choose where your game is (iPhone or
iPad, or Android), then follow the steps.

1. **Copy my save** (iPhone and iPad, before May 1, 2027): the iPhone scans a QR code and installs
   a profile. When the game starts, the tool keeps a copy of your save and of the game's data.
   Nothing to set by hand. On Android, there is nothing to copy.
2. **Install the game**: the tool builds a version of the game that works without a server
   (Android APK), from the official 1.10.4 game you provide, with your save or a new game. Then it
   installs it on the phone by cable.
3. **Edit a save**: heroes, levels, weapons, costumes, medals, currencies, statistics... From a
   file, a copy or straight from the phone by cable.
4. **Updates**: updates the tool, then the phone's game, without losing your progress. The
   offline game announces new versions itself, in its inbox.

## What the offline game adds

- The 7 heroes that were never released (Molly, Helen, Terry, Crumby, Chance, Flare and Nakari),
  plus Juycee and Rivet, with Kit on her back and her own hammer.
- The added heroes are earned on the Ranger Road; Nakari is bought in the shop.
- Each hero has their main weapon, and a gadget of your choice as secondary weapon.
- Modes and events: Bolt Rush (together or alone) and its King, a 16-player Battle Royale, the
  Mrs. Zurkon and random weapon events.
- Playing with friends: on the same Wi-Fi, or remotely with a room code.
- A reworked shop: Qredit offers, Qredits exchanged for Raritanium, no more offers for a hero or a
  weapon already at max.
- The game's artbook, and a gallery for your own pictures.
- Costumes that were only downloaded online, and Polish on top of the game's languages.

## Install

Download `OutilSauvegardeRR.zip` from the latest version (**Releases** tab), then unzip it.

- **Windows**: the first time, double-click `Lancer (Windows).bat`. It installs what is needed,
  then creates the "Ranger Rumble hors ligne" shortcut on the Desktop.
- **Mac**: open "Ranger Rumble hors ligne". If the Mac refuses: System Settings > Privacy &
  Security > Open Anyway.

The first installation takes a few minutes (Python is downloaded if missing). Everything is
explained step by step in `LIS_MOI.txt`.

You also need the official 1.10.4 game (`.xapk`, `.apkm` or a complete `.apk`), 5 GB free, and a
64-bit Android phone or tablet (Android 7.1 or newer).

## What's new since version 1.0.5

**The tool**

- A new home screen with the game's pictures, and every page redone: dark theme, rounded
  buttons, a window that fits small screens.
- A Mac app, and a Windows shortcut with the game's icon.
- 6 languages, English by default.
- The iPhone copy without any proxy setting: the profile does it all.
- Windows: works with the latest Python, the copy no longer uses a component blocked by Smart App
  Control, and the firewall is checked and set when needed.
- Version 1.10.3 is no longer needed: the unreleased heroes come with the tool.
- A new game without a copy, and the installation on the phone from the tool, with a progress
  bar.
- Linux is no longer supported.

**The game**

- The added heroes on the Ranger Road, Nakari in the shop.
- Rivet: Kit on her back and her own hammer.
- The shop: plan offers in Qredits, Qredits exchanged for Raritanium, heroes and weapons at max
  left out of offers and random draws.
- Raritanium in the daily rewards (days 3 and 7).
- The drill's damage shown.
- Polish.

## What the tool contains, and what it does not

The tool's code, our changes to the game and the offline server, with the artbook (pictures of
the game and its promotion), costumes and parts of older versions (the 7 unreleased heroes from
1.10.3, the collection screen from 1.1.0), and card pictures made for the project. **Not the game
itself**: each player provides their own official copy (1.10.4), and the tool changes it on their
computer. Nothing is sent anywhere, apart from the question "is there a new version?" asked to
GitHub.

Fan project, not affiliated with Sony Interactive Entertainment, Insomniac Games or Oh BiBi.
*Ratchet & Clank* is a trademark of Sony Interactive Entertainment LLC.
