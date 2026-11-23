# Ranger Rumble hors ligne

[English](README.md) · **Français**

Pour continuer à jouer à *Ratchet & Clank: Ranger Rumble* après la fermeture de ses serveurs, le
1er mai 2027. Windows et macOS, en anglais, français, espagnol, allemand, italien et portugais.


**Il est recommandé d'installer Python 3.15 avant.**


## iPhone et Android

- **La copie de sauvegarde se fait uniquement sur iPhone ou iPad.**
- **Le jeu hors ligne marche sur Android, et sur iPhone et iPad (essai).**
- **Une sauvegarde copiée depuis l'iPhone continue dans le jeu hors ligne.**

## Ce que fait l'outil

Le launcher a une section **Android** et une section **iOS**, avec les quatre mêmes outils :

1. **Copier la sauvegarde** (iPhone et iPad, avant le 1er mai 2027) : scanner un QR code, installer
   un profil, ouvrir le jeu. L'outil garde la sauvegarde et les données du jeu. Sur Android, rien à
   copier : le jeu part d'une nouvelle partie.
2. **Fabriquer et installer** : l'outil fabrique le jeu hors ligne à partir du jeu officiel 1.10.4,
   avec la sauvegarde ou une nouvelle partie. Android : installé par le câble. iOS : une IPA
   installée avec Sideloadly.
3. **Éditer une sauvegarde** : héros, niveaux, armes, costumes, médailles, monnaies, statistiques.
   Depuis un fichier, une copie ou le téléphone lui-même.
4. **Mettre à jour le jeu** : une nouvelle version du jeu par-dessus l'ancienne, sans perdre la
   progression. Le jeu hors ligne annonce les nouvelles versions dans sa boîte de réception.

Le launcher lui-même se met à jour dans **Réglages > Mises à jour**.

Supprimer le jeu supprime aussi sa sauvegarde.

## Nouveautés par rapport au jeu original

Tout le jeu marche sans serveur : boutique, missions, événements, Voie du Ranger, amis.

**Héros**

- 7 nouveaux héros : Molly, Helen, Terry, Crumby, Chance, Flare et Nakari.
- Rivet (un mod, pas un personnage prévu par les développeurs).
- Nakari coûte 750 Raritanium.
- Les nouveaux héros sont sur la Voie du Ranger.
- Des orbes pour chaque nouveau héros, en boutique ou dans les Reebos. Ils s'arrêtent une fois le
  héros au niveau maximum.

**Armes**

- Deux catégories : les armes principales et les gadgets.
- Chaque arme et chaque gadget s'équipe sur chaque héros.
- Les armes et les gadgets se débloquent sur la Voie du Ranger.
- Nouvelle arme : le Fléau-scorpion.
- L'accueil montre de nouveau les armes du héros.
- Les armes et les gadgets montent de nouveau jusqu'au niveau 10.

**Modes et événements**

- Bolt Rush à plusieurs et seul.
- Battle Royale à 16 joueurs : activer « Cartes et modes prototypes » dans les réglages du jeu.
- Les événements de Mme Zurkon et de l'arme aléatoire, comme les développeurs les avaient prévus.

**Jouer à plusieurs**

- Les amis sur le même Wi-Fi apparaissent dans la liste d'amis : invitations et escouades de 3.
- Jeu à distance avec un code d'escouade, jusqu'à 3 joueurs.
- Combats en escouade dans tous les modes, sauf Mob Rush.

**Boutique et récompenses**

- Offres de plans en Qredits, échange de Qredits contre du Raritanium.
- Plus de Raritanium dans les récompenses quotidiennes (jours 3 et 7).

**Autres**

- Un artbook dans le menu du jeu : images du jeu, concepts, plans des cartes.
- Quatre niveaux de difficulté : facile, normal, difficile, ultra difficile.
- Nouvelle langue : le polonais.

## Installer

1. Télécharger `Launcher_Ratchet_Ranger_Rumble.zip` dans la dernière version (onglet **Releases**),
   puis le décompresser.
2. **Windows** : la première fois, double-cliquer sur `Lancer (Windows).bat`. Il installe ce qu'il
   faut et crée le raccourci « Launcher Ratchet Ranger Rumble » sur le Bureau.
   **Mac** : ouvrir « Launcher Ratchet Ranger Rumble ». Si le Mac refuse : Réglages Système >
   Confidentialité et sécurité > Ouvrir quand même.
3. Le premier démarrage prend quelques minutes (Python est téléchargé s'il manque). Aide pas à pas :
   `Read me.txt`.

**Il est recommandé d'installer Python 3.15 avant.**

Il faut aussi le jeu officiel 1.10.4 (`.xapk`, `.apkm` ou `.apk` complet), 5 Go libres, et un
téléphone ou une tablette Android 64 bits (Android 7.1 ou plus récent), ou un iPhone ou un iPad.

## iPhone et iPad (essai)

Les mêmes outils qu'Android, dans la section **iOS** du launcher. Seuls l'installation et l'accès à
la sauvegarde du téléphone changent.

Il faut : [Sideloadly](https://sideloadly.io) (gratuit), un compte Apple (un compte gratuit suffit)
et un câble USB.

**Fabriquer et installer**
1. iOS > **Fabriquer et installer** : choisir le jeu officiel 1.10.4 et une sauvegarde (ou
   **Nouvelle partie**), puis **Préparer pour iPhone**. L'IPA est créée à côté de l'APK Android.
2. Installer Sideloadly. Brancher l'iPhone, le déverrouiller, puis toucher **Se fier**.
3. Sur l'iPhone : Réglages > Confidentialité et sécurité > **Mode développeur** : l'activer, puis
   redémarrer.
4. Dans Sideloadly : déposer l'IPA, choisir l'iPhone, entrer le compte Apple, puis **Start**.
5. Sur l'iPhone : Réglages > Général > VPN et gestion de l'appareil > le compte Apple >
   **Faire confiance**.
6. Ouvrir Ranger Rumble. Tout tourne sur l'iPhone, hors ligne.

Avec un compte Apple gratuit, l'app s'arrête au bout de 7 jours : refaire l'étape 4. La progression
est gardée.

**Éditer la sauvegarde de l'iPhone**
1. Ouvrir le jeu une fois, puis le fermer. Brancher l'iPhone.
2. Finder (Mac) ou l'app Appareils Apple (Windows) > l'iPhone > **Fichiers** > Ranger Rumble :
   glisser `sauvegarde_actuelle.msgpack` sur l'ordinateur.
3. iOS > **Éditer une sauvegarde** > **L'iPhone** > **Choisir le fichier**, puis faire les
   changements.
4. **Envoyer à l'iPhone** : fermer le jeu. Dans le même onglet Fichiers, déplier Ranger Rumble,
   supprimer le fichier `.msgpack` qui s'y trouve, puis y glisser le fichier que montre le launcher
   (`a_importer.msgpack`). Ouvrir le jeu.

**Mettre à jour le jeu**
iOS > **Mises à jour** > **Mettre à jour le jeu**, puis refaire l'étape 4. La progression est gardée.

## Le jeu officiel

**Chaque joueur fournit son propre exemplaire officiel du jeu (1.10.4)**, et l'outil le modifie sur
son ordinateur.

Projet de fans, sans lien avec Sony Interactive Entertainment, Insomniac Games ou Oh BiBi.
*Ratchet & Clank* est une marque de Sony Interactive Entertainment LLC.
