# Ranger Rumble hors ligne

[English](README.md) · **Français**

Un outil pour continuer à jouer à *Ratchet & Clank: Ranger Rumble* après la fermeture de ses
serveurs, le 1er mai 2027. Pour Windows et macOS, en 6 langues : anglais, français, espagnol,
allemand, italien et portugais.

## Ce que fait l'outil

L'outil s'ouvre sur un accueil aux images du jeu. Tu choisis où est ton jeu (iPhone ou iPad,
ou Android), puis tu suis les étapes.

1. **Copier ma sauvegarde** (iPhone et iPad, avant le 1er mai 2027) : l'iPhone scanne un QR code
   et installe un profil. Au démarrage du jeu, l'outil garde une copie de ta sauvegarde et des
   données du jeu. Rien à régler à la main. Sur Android, il n'y a rien à copier.
2. **Installer le jeu** : l'outil fabrique une version du jeu qui marche sans serveur (APK
   Android), à partir du jeu officiel 1.10.4 que tu fournis, avec ta sauvegarde ou une nouvelle
   partie. Puis il l'installe sur le téléphone par le câble.
3. **Éditer une sauvegarde** : héros, niveaux, armes, costumes, médailles, monnaies,
   statistiques... Depuis un fichier, une copie ou directement le téléphone par le câble.
4. **Mises à jour** : met l'outil à jour, puis le jeu du téléphone, sans perdre ta progression.
   Le jeu hors ligne annonce lui-même les nouvelles versions dans sa boîte de réception.

## Ce que le jeu hors ligne ajoute

- Les 7 héros jamais sortis (Molly, Helen, Terry, Crumby, Chance, Flare et Nakari), plus Juycee
  et Rivet, avec Kit dans le dos et son propre marteau.
- Les héros ajoutés se gagnent sur la Ranger Road, Nakari s'achète dans la boutique.
- Chaque héros a son arme principale, et un gadget au choix comme arme secondaire.
- Des modes et des événements : Bolt Rush (à plusieurs ou seul) et son Roi, Battle Royale à 16,
  les événements de Mme Zurkon et de l'arme au hasard.
- Jouer entre amis : sur le même Wi-Fi, ou à distance avec un code de salon.
- Une boutique revue : offres en Qredits, échange de Qredits contre du Raritanium, plus d'offres
  pour un héros ou une arme déjà au maximum.
- L'artbook du jeu, et une galerie pour tes propres images.
- Des costumes qui ne se téléchargeaient qu'en ligne, et le polonais en plus des langues du jeu.

## Installer

Télécharge `OutilSauvegardeRR.zip` dans la dernière version (onglet **Releases**), puis
décompresse-le.

- **Windows** : la première fois, double-clique sur `Lancer (Windows).bat`. Il installe ce qu'il
  faut, puis crée le raccourci « Ranger Rumble hors ligne » sur le Bureau.
- **Mac** : ouvre « Ranger Rumble hors ligne ». Si le Mac refuse : Réglages Système >
  Confidentialité et sécurité > Ouvrir quand même.

La première installation prend quelques minutes (Python est téléchargé s'il manque). Tout est
expliqué pas à pas dans `LIS_MOI.txt`.

Il te faut aussi le jeu officiel 1.10.4 (`.xapk`, `.apkm` ou `.apk` complet), 5 Go libres, et un
téléphone ou une tablette Android 64 bits (Android 7.1 ou plus récent).

## Nouveautés depuis la version 1.0.5

**L'outil**

- Un nouvel accueil aux images du jeu, et toutes les pages refaites : thème sombre, boutons
  arrondis, fenêtre adaptée aux petits écrans.
- Une app pour Mac, et un raccourci Windows avec l'icône du jeu.
- 6 langues, l'anglais par défaut.
- La copie iPhone sans réglage de proxy : le profil s'occupe de tout.
- Windows : marche avec la dernière version de Python, la copie n'utilise plus de composant
  bloqué par Smart App Control, et le pare-feu est vérifié et réglé si besoin.
- Plus besoin de la version 1.10.3 : les héros jamais sortis sont fournis avec l'outil.
- Une nouvelle partie sans copie, et l'installation sur le téléphone depuis l'outil, avec une
  barre de progression.
- Linux n'est plus pris en charge.

**Le jeu**

- Les héros ajoutés sur la Ranger Road, Nakari dans la boutique.
- Rivet : Kit dans le dos et son propre marteau.
- La boutique : offres de plans en Qredits, échange de Qredits contre du Raritanium, héros et
  armes au maximum retirés des offres et des tirages.
- Du Raritanium dans les récompenses quotidiennes (jours 3 et 7).
- Les dégâts de la perceuse affichés.
- Le polonais.

## Ce que l'outil contient, et ce qu'il ne contient pas

Le code de l'outil, nos retouches du jeu et le serveur hors ligne, avec l'artbook (images du jeu
et de sa promotion), des costumes et des éléments d'anciennes versions (les 7 héros jamais
sortis de la 1.10.3, l'écran de collecte de la 1.1.0), et des images de cartes faites pour le
projet. **Pas le jeu lui-même** : chaque joueur fournit son propre exemplaire officiel (1.10.4),
et l'outil le modifie sur son ordinateur. Rien n'est envoyé nulle part, à part la question
« y a-t-il une nouvelle version ? » posée à GitHub.

Projet de fans, sans lien avec Sony Interactive Entertainment, Insomniac Games ou Oh BiBi.
*Ratchet & Clank* est une marque de Sony Interactive Entertainment LLC.
