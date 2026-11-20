# Ranger Rumble hors ligne

[English](README.md) · **Français**

Un outil pour continuer à jouer à *Ratchet & Clank: Ranger Rumble* après la fermeture de ses
serveurs, le 1er mai 2027. Pour Windows et macOS, en 6 langues : anglais, français, espagnol,
allemand, italien et portugais.


**Il est recommandé d'installer Python 3.15 avant.**


## iPhone et Android

- **La copie de sauvegarde se fait uniquement sur iPhone ou iPad.**
- **Le jeu hors ligne (le mod) est uniquement pour Android.**
- **Une copie faite sur iPhone marche sur Android** : la progression iPhone continue dans le jeu
  hors ligne, sur un téléphone ou une tablette Android.

## Ce que fait l'outil

1. **Copier la sauvegarde** (iPhone et iPad uniquement, avant le 1er mai 2027) : il faut scanner le
   QR code avec l'iPhone, puis installer le profil depuis les Réglages. Au démarrage du jeu, l'outil
   garde une copie de la sauvegarde et des données du jeu. Sur Android, il n'y a rien à copier : le
   jeu part d'une nouvelle partie.
2. **Installer le jeu** (Android uniquement) : l'outil fabrique une version du jeu qui marche sans
   serveur (APK Android), à partir du jeu officiel 1.10.4 fourni par le joueur, avec la sauvegarde
   iPhone ou une nouvelle partie. Puis il l'installe sur le téléphone par le câble (sur Android,
   il faut activer « Transfert de fichiers » dans les paramètres USB).
3. **Éditer une sauvegarde** : modification des héros, niveaux, armes, costumes, médailles,
   monnaies, statistiques... depuis un fichier, une copie ou directement sur le téléphone par le
   câble.
4. **Mises à jour** : le jeu se met à jour directement depuis l'outil, avec un simple câble, sans
   perdre la progression. Le jeu hors ligne annonce lui-même les nouvelles versions dans sa boîte
   de réception.

Attention : supprimer le jeu supprime aussi la sauvegarde !

## Nouveautés et modifications par rapport au jeu original

Tout le jeu marche sans serveur : boutique, missions, événements, Voie du Ranger, amis.

**Héros**

- Ajout de 7 nouveaux héros : Molly, Helen, Terry, Crumby, Chance, Flare et Nakari.
- Ajout du personnage de Rivet (il s'agit d'un mod, pas d'un personnage prévu à l'origine).
- Nakari s'achète pour 750 Raritanium.
- La Voie du Ranger a été mise à jour pour inclure les nouveaux héros.
- Ajout de nouveaux orbes pour chaque nouveau héros. Ils s'obtiennent en boutique ou dans les
  Reebos. Une fois un héros au niveau maximum, le jeu ne les propose plus.

**Armes**

- Les armes sont désormais séparées en 2 catégories : les armes principales et les gadgets.
- Chaque arme et chaque gadget peuvent désormais être équipés sur chaque héros.
- Les armes et les gadgets se débloquent sur la Voie du Ranger.
- Ajout d'une nouvelle arme : le Fléau-scorpion.
- L'accueil montre de nouveau les armes du héros, comme dans les anciennes versions.
- Les armes et les gadgets s'améliorent de nouveau jusqu'au niveau 10.

**Modes et événements**

- Bolt Rush à plusieurs et Bolt Rush seul sont désormais disponibles.
- Un Battle Royale à 16 joueurs a été ajouté. Il se débloque en activant « Cartes et modes
  prototypes » dans les réglages du jeu.
- Ajout des événements de Mme Zurkon et de l'arme aléatoire, comme les développeurs les avaient
  prévus.

**Jouer à plusieurs**

- Les amis sur le même Wi-Fi apparaissent dans la liste d'amis : invitations et escouades de 3
  joueurs.
- Jeu à distance avec un code d'escouade, jusqu'à 3 joueurs.
- Les combats en escouade marchent dans tous les modes, sauf Mob Rush.

**Boutique et récompenses**

- Nouvelles offres de plans en Qredits, échange de Qredits contre du Raritanium.
- Du Raritanium en plus dans les récompenses quotidiennes (jours 3 et 7).

**Autres**

- Ajout d'un artbook dans le menu du jeu : images du jeu, concepts, plans des cartes.
- Quatre niveaux de difficulté au choix (facile, normal, difficile, ultra difficile).
- Nouvelle langue : le polonais.
- Le jeu annonce maintenant les nouvelles versions dans sa boîte de réception.

## Installer

Télécharger `Ratchet_Ranger_Rumble.zip` dans la dernière version (onglet **Releases**), puis le
décompresser.

- **Windows** : la première fois, double-cliquer sur `Lancer (Windows).bat`. Il installe ce qu'il
  faut, puis crée le raccourci « Launcher Ratchet Ranger Rumble » sur le Bureau.
- **Mac** : ouvrir « Launcher Ratchet Ranger Rumble ». Si le Mac refuse : Réglages Système >
  Confidentialité et sécurité > Ouvrir quand même.

**Il est recommandé d'installer Python 3.15 avant.**

La première installation prend quelques minutes (Python est téléchargé s'il manque). Tout est
expliqué pas à pas dans `Read me.txt`.

Il faut aussi le jeu officiel 1.10.4 (`.xapk`, `.apkm` ou `.apk` complet), 5 Go libres, et un
téléphone ou une tablette Android 64 bits (Android 7.1 ou plus récent).

## Ce que l'outil contient, et ce qu'il ne contient pas

**Chaque joueur fournit son propre exemplaire officiel du jeu (1.10.4)**, et l'outil le modifie
sur son ordinateur. Rien n'est envoyé nulle part, à part la question « y a-t-il une nouvelle
version ? » posée à GitHub.

Projet de fans, sans lien avec Sony Interactive Entertainment, Insomniac Games ou Oh BiBi.
*Ratchet & Clank* est une marque de Sony Interactive Entertainment LLC.
