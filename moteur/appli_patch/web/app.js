// The Windows launcher (lanceur_web.py opens it in Edge's app mode): the Mac app's screens, drawn by this page.
// The engine (service.py) does the work: it answers commands (POST /api/<command>) and sends events (SSE).
"use strict";

const PARAMETRES = new URLSearchParams(location.search);
const JETON = PARAMETRES.get("jeton") || "";
const JOURNAL_GARDE = 3000;    // log lines kept in memory
const JOURNAL_MONTRE = 400;    // log lines drawn in a box
const TACHES_MAJ = ["maj_outil", "maj_telephone"];

// State ------------------------------------------------------------------------------------------------
const E = {
  // given by the engine
  version: "", jeu: "", reglages: {}, langue: "en", langues: [], table: {}, copies: "", base: "",
  telephones: [], adb: null, maj: {}, infos: {}, sauvegardes: [], journal: [],
  // the running task
  tache: null, barre: null, verification: false, apresAdb: null, dernierAPK: null, libre: null,
  // the iPhone copy
  copieEtat: null, copieFinie: false, qr: null, qrSvg: null,
  // the game for iPhone (jeu_ios): { bientot, manque, pret, ipa, taille, infos }
  iphone: {},
  // the editor
  editeur: { ouvert: false }, edVersion: 0, edLignes: null, edArbre: null, onglet: "heros",
  // where the window is
  section: "android", page: null, sectionReglages: "general", recherche: "",
};

// Pictures ---------------------------------------------------------------------------------------------
const P = (d, regle = "") => `<svg viewBox="0 0 24 24"${regle ? ' fill-rule="evenodd"' : ""}><path d="${d}"/></svg>`;
const SVG = {
  android: `<svg viewBox="0 0 24 24" fill-rule="evenodd"><path d="M3 18a9 9 0 0 1 18 0zM8.5 13.7a1.1 1.1 0 1 0 0 2.2 1.1 1.1 0 0 0 0-2.2zm7 0a1.1 1.1 0 1 0 0 2.2 1.1 1.1 0 0 0 0-2.2z"/><path d="M6.4 6.9l1.2-.7 1.7 2.8-1.2.7zm11.2 0l-1.2-.7-1.7 2.8 1.2.7z"/></svg>`,
  apple: P("M16.4 12.6c0-2.3 1.9-3.4 2-3.5-1.1-1.6-2.8-1.8-3.4-1.8-1.4-.1-2.8.9-3.5.9-.7 0-1.9-.9-3.1-.8-1.6 0-3 .9-3.8 2.3-1.6 2.8-.4 7 1.2 9.3.8 1.1 1.7 2.4 2.9 2.3 1.2 0 1.6-.7 3-.7s1.8.7 3.1.7c1.3 0 2.1-1.1 2.8-2.3.9-1.3 1.3-2.6 1.3-2.6s-2.5-1-2.5-3.8zM14.1 5.8c.6-.8 1.1-1.9 1-3-.9 0-2.1.6-2.7 1.4-.6.7-1.1 1.8-1 2.9 1.1.1 2.1-.5 2.7-1.3z"),
  ordinateur: P("M3 4h18a1 1 0 0 1 1 1v11a1 1 0 0 1-1 1h-7v2h3v2H7v-2h3v-2H3a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1zm1 2v9h16V6z", 1),
  reglages: P("M12 8.5a3.5 3.5 0 1 0 0 7 3.5 3.5 0 0 0 0-7zm8.4 2.3l-1.9-.4a6.9 6.9 0 0 0-.7-1.7l1.1-1.6-1.9-1.9-1.6 1.1a6.9 6.9 0 0 0-1.7-.7l-.4-1.9h-2.6l-.4 1.9a6.9 6.9 0 0 0-1.7.7L7 5.2 5.1 7.1l1.1 1.6a6.9 6.9 0 0 0-.7 1.7l-1.9.4v2.6l1.9.4c.2.6.4 1.2.7 1.7l-1.1 1.6 1.9 1.9 1.6-1.1c.5.3 1.1.5 1.7.7l.4 1.9h2.6l.4-1.9c.6-.2 1.2-.4 1.7-.7l1.6 1.1 1.9-1.9-1.1-1.6c.3-.5.5-1.1.7-1.7l1.9-.4z", 1),
  cadenas: P("M7 10V7a5 5 0 0 1 10 0v3h1a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V11a1 1 0 0 1 1-1zm2 0h6V7a3 3 0 0 0-6 0z", 1),
  copie: P("M7 2h8a2 2 0 0 1 2 2v4h-2V5H7v14h8v-3h2v4a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2zm9 7l5 3-5 3v-2h-6v-2h6z"),
  boite: P("M12 2l9 4.5v11L12 22l-9-4.5v-11zm0 2.2L6.2 7 12 9.8 17.8 7zM5 8.6v7.7l6 3v-7.7zm14 0l-6 3v7.7l6-3z", 1),
  curseurs: P("M3 6h9.2a3 3 0 0 1 5.6 0H21v2h-3.2a3 3 0 0 1-5.6 0H3zm12-1a1 1 0 1 0 0 2 1 1 0 0 0 0-2zM3 16h3.2a3 3 0 0 1 5.6 0H21v2h-9.2a3 3 0 0 1-5.6 0H3zm6-1a1 1 0 1 0 0 2 1 1 0 0 0 0-2z", 1),
  synchro: P("M12 4a8 8 0 0 1 7.4 5H17v2h6V5h-2v2.3A10 10 0 0 0 2 12h2a8 8 0 0 1 8-8zm8 8a8 8 0 0 1-15.4 3H7v-2H1v6h2v-2.3A10 10 0 0 0 22 12z"),
  retour: P("M15.5 3.5L7 12l8.5 8.5 1.4-1.4L9.8 12l7.1-7.1z"),
  play: P("M7 4v16l13-8z"), stop: P("M6 6h12v12H6z"), check: P("M9 16.2l-4.2-4.2-1.4 1.4L9 19 21 7l-1.4-1.4z"),
  alerte: P("M12 2L1 21h22zm-1 7h2v6h-2zm0 8h2v2h-2z", 1),
  info: P("M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zm-1 5h2v2h-2zm0 4h2v6h-2z", 1),
  succes: P("M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zm-1.5 14.5L6 12l1.4-1.4 3.1 3.1 6.1-6.1L18 9z", 1),
  recherche: P("M10 3a7 7 0 0 1 5.6 11.2l5.1 5.1-1.4 1.4-5.1-5.1A7 7 0 1 1 10 3zm0 2a5 5 0 1 0 0 10 5 5 0 0 0 0-10z", 1),
  marteau: P("M3 20.6l9.4-9.4 2.1 2.1-9.4 9.4zM13 3l8 8-2.8 2.8-2.1-2.1-1.4 1.4-4.2-4.2 1.4-1.4-2.1-2.1z"),
  cable: P("M9 2h6v5h-1v4a2 2 0 0 1-4 0V7H9zm2 13h2v7h-2z"),
  rafraichir: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M20 12a8 8 0 1 1-2.3-5.7"/><path d="M20 4v5h-5"/></svg>`,
  dossier: P("M3 5h7l2 2h9v12H3z"), palette: P("M12 2a10 10 0 0 0 0 20c1.1 0 2-.9 2-2 0-.5-.2-1-.5-1.3-.3-.4-.5-.8-.5-1.3 0-1.1.9-2 2-2h2.4A5.6 5.6 0 0 0 22 10c0-4.4-4.5-8-10-8zM6.5 12a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3zm3-4a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3zm5 0a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3zm3 4a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3z", 1),
  telephone: P("M7 2h10a2 2 0 0 1 2 2v16a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2zm0 3v13h10V5z", 1),
  cle: P("M7 4a5 5 0 0 1 4.6 3H23v4h-2v3h-3v-3h-6.4A5 5 0 1 1 7 4zm0 3a2 2 0 1 0 0 4 2 2 0 0 0 0-4z", 1),
  outil: P("M21 6.4l-3.3 3.3-3.4-.9-.9-3.4L16.7 2A6 6 0 0 0 9.3 9.3L2 16.6 5.4 20l7.3-7.3A6 6 0 0 0 21 6.4z"),
  sablier: P("M6 2h12v5l-4 5 4 5v5H6v-5l4-5-4-5z"), etoile: P("M12 2l2 6 6 2-6 2-2 6-2-6-6-2 6-2z"),
  doc: P("M6 2h8l5 5v15H6zm7 1.5V8h4.5z", 1), avion: P("M2 21l21-9L2 3v7l15 2-15 2z"),
  disquette: P("M5 3h11l4 4v14H4V3zm2 2v5h8V5zm5 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6z", 1),
  annuler: P("M12.5 8c-2.6 0-5 1-6.9 2.6L2 7v9h9l-3.6-3.6A8 8 0 0 1 20.4 16l2.4-.8A10.5 10.5 0 0 0 12.5 8z"),
  qr: P("M3 3h8v8H3zm2 2v4h4V5zm8-2h8v8h-8zm2 2v4h4V5zM3 13h8v8H3zm2 2v4h4v-4zm8-2h3v3h-3zm5 0h3v3h-3zm-5 5h3v3h-3zm5 0h3v3h-3z", 1),
  image: P("M3 4h18v16H3zm2 2v9l4-4 3 3 4-5 3 4V6zm3 1.5a1.5 1.5 0 1 1 0 3 1.5 1.5 0 0 1 0-3z", 1),
  personne: P("M12 3a4.5 4.5 0 1 1 0 9 4.5 4.5 0 0 1 0-9zm0 11c4.4 0 8 2 8 4.5V21H4v-2.5C4 16 7.6 14 12 14z"),
  sortie: P("M11 3h2v10l3.5-3.5 1.4 1.4L12 16.8l-5.9-5.9 1.5-1.4L11 13zM4 19h16v2H4z"),
};
const icone = (nom, classe) => SVG[nom].replace("<svg", `<svg class="${classe}"`);

// What the screens are made of (titles are translation keys) -----------------------------------------------
const PAGES = {
  copie: { titre: "Copier la sauvegarde iPhone", image: "fond_2", icone: "copie", taches: ["copie"] },
  fabrication: { titre: "Fabriquer et installer", image: "fond_1", icone: "boite", taches: ["fabrication", "installation", "adb"] },
  editeur: { titre: "Éditer une sauvegarde", image: "fond_4", icone: "curseurs", taches: [] },
  majs: { titre: "Mises à jour", image: "fond_5", icone: "synchro", taches: TACHES_MAJ },
};
const BANNIERE = ["fond_1", "fond_3", "fond_2", "fond_5", "fond_6", "fond_4"];
const NOMS_TACHES = { copie: "Copie de la sauvegarde", fabrication: "Fabrication", installation: "Installation",
  maj_telephone: "Mise à jour du téléphone", maj_outil: "Mise à jour de l'outil", adb: "Outils Android",
  iphone: "Préparation pour iPhone" };
const ONGLETS = [["profil", "Profil"], ["heros", "Héros"], ["armes", "Armes"], ["costumes", "Costumes"], ["modes", "Modes"], ["tout", "Tout"]];
const ACTIONS_ONGLET = {
  heros: [["tous_heros", "Débloquer tous les héros"], ["max_heros", "Niveau max pour tous"]],
  armes: [["toutes_armes", "Débloquer toutes les armes"], ["max_armes", "Niveau max pour toutes"]],
  costumes: [["tous_costumes", "Donner tous les costumes"]],
};
const SECTIONS = [["general", "Général", "reglages"], ["apparence", "Apparence", "palette"], ["jeu", "Jeu et fichiers", "dossier"],
  ["telephone", "Téléphone", "telephone"], ["copie", "Copie iPhone", "copie"], ["cle", "Clé de signature", "cle"],
  ["majs", "Mises à jour", "synchro"], ["composants", "Composants", "boite"], ["avance", "Avancé", "outil"], ["apropos", "À propos", "info"]];
const ACCENTS = [["vert", "#3df2a4", "#1fd1c2", "Vert"], ["or", "#ffd21b", "#ff9d1b", "Or"], ["bleu", "#3cc3ff", "#3c7dff", "Bleu"],
  ["violet", "#c46bff", "#ff5cc8", "Violet"]];

// Small things -----------------------------------------------------------------------------------------
const $ = (choix, dans = document) => dans.querySelector(choix);
const $$ = (choix, dans = document) => [...dans.querySelectorAll(choix)];
const ENTITES = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
const h = (texte) => String(texte ?? "").replace(/[&<>"']/g, (c) => ENTITES[c]);
const nomFichier = (chemin) => String(chemin || "").split(/[\\/]/).pop();
const duree = () => (E.reglages.animations === "aucune" ? 0
  : E.reglages.animations === "reduites" || matchMedia("(prefers-reduced-motion: reduce)").matches ? 0.5 : 1);
const chiffre = (n) => Number(n || 0).toLocaleString("fr-FR").replace(/[\s  ]/g, " ");  // a space that never breaks the number
const vueActuelle = () => $("#contenu > .vue:not(.sortie)");

function tr(texte, valeurs = {}) {
  let resultat = texte;
  if (E.langue !== "fr") {
    const entree = E.table[texte.trim()];
    if (entree) resultat = entree[E.langue] || entree.en || texte;
  }
  for (const [cle, valeur] of Object.entries(valeurs)) resultat = resultat.split(`{${cle}}`).join(valeur);
  return resultat;
}

const nomTache = (nom) => (NOMS_TACHES[nom] ? tr(NOMS_TACHES[nom]) : nom);
const titrePage = (page) => tr(PAGES[page].titre);
const pageDeTache = (tache) => Object.keys(PAGES).find((page) => PAGES[page].taches.includes(tache)) || "fabrication";
const telephone = () => E.telephones.find((t) => t.etat === "device");
const majDisponible = () => E.maj.etat === "nouvelle";
const texteJournal = () => E.journal.map((l) => l.texte).join("\n");

function plusAncien(a, b) {
  const x = String(a).split(".").map(Number), y = String(b).split(".").map(Number);
  for (let i = 0; i < Math.max(x.length, y.length); i++) if ((x[i] || 0) !== (y[i] || 0)) return (x[i] || 0) < (y[i] || 0);
  return false;
}

// The engine -------------------------------------------------------------------------------------------
// Answers [reply, code]. A code listed in `codes` is the caller's to handle; others show an error, except for a
// silent call (a background reading), whose failure goes to the console only.
async function api(nom, corps = {}, { codes = [], silencieux = false } = {}) {
  let reponse;
  try {
    const r = await fetch(`/api/${nom}`, { method: "POST", headers: { "X-Jeton": JETON, "Content-Type": "application/json" },
      body: JSON.stringify(corps) });
    reponse = await r.json();
  } catch (erreur) {
    if (silencieux) console.warn(nom, erreur); else toast(tr("Impossible"), String(erreur), "erreur");
    return [null, null];
  }
  if (reponse.ok) return [reponse, null];
  if (codes.includes(reponse.code)) return [reponse, reponse.code];
  if (silencieux) console.warn(nom, reponse.erreur);
  else if (reponse.code === "adb_absent") demanderAdb();
  else toast(tr("Impossible"), reponse.erreur, "erreur");
  return [null, reponse.code];
}

// What a web page cannot do itself (choose a file and get its path, show a folder, restart): the engine does it.
const demander = (type, donnees = {}) => api("fenetre", { type, ...donnees }).then(([reponse]) => (reponse ? reponse.valeur : null));
const choisir = (donnees) => demander("choisir", donnees);  // a file or folder's path, or null

// Settings ---------------------------------------------------------------------------------------------
async function ecrire(valeurs) {
  Object.assign(E.reglages, valeurs);
  appliquerApparence();
  rendre();
  const [reponse] = await api("reglages_ecrire", valeurs);
  if (reponse) E.reglages = reponse.reglages;
  if (valeurs.langue) {
    E.langue = valeurs.langue;
    appliquerApparence();
    traduireCadre();
    rendreBarre();
    rendre();
  }
}

function appliquerApparence() {
  const racine = document.documentElement;
  racine.dataset.accent = E.reglages.accent || "vert";
  racine.dataset.animations = E.reglages.animations || "completes";
  racine.style.setProperty("--duree", duree() || 0.001);
  // the first-paint colours of index.html give way to the stylesheet's
  racine.style.removeProperty("background");
  racine.style.removeProperty("color-scheme");
  racine.lang = E.langue;
}

function traduireCadre() {
  for (const el of $$("[data-tr]")) el.textContent = tr(el.dataset.tr);
}

// Events of the engine ---------------------------------------------------------------------------------
function ecouter() {
  const source = new EventSource(`/api/evenements?jeton=${encodeURIComponent(JETON)}`);
  source.onmessage = (message) => recevoir(JSON.parse(message.data));
}

function recevoir(ev) {
  switch (ev.type) {
    case "journal": ajouterJournal(ev); return;
    case "barre": recevoirBarre(ev); return;
    case "tache": recevoirTache(ev); break;
    case "copie": recevoirCopie(ev); break;
    case "copie_qr": E.qr = ev.url; E.qrSvg = ev.svg; break;
    case "telephones": E.adb = ev.adb; E.telephones = ev.telephones || []; break;
    case "maj": E.maj = ev; break;
    case "pare_feu":
      question(tr("Pare-feu"), tr("Le pare-feu de Windows bloque l'iPhone."), [
        { titre: tr("Autoriser"), action: () => api("pare_feu_regler") }, { titre: tr("Plus tard"), annuler: true }]);
      break;
    default: return;
  }
  rendreBarre();
  rendre();
}

// A line goes straight into the log boxes that show its task: the view is not drawn again for it.
function ajouterJournal({ texte, tache }) {
  E.journal.push({ texte, tache });
  if (E.journal.length > JOURNAL_GARDE) E.journal.splice(0, E.journal.length - JOURNAL_GARDE);
  if (!tache) return;
  for (const boite of $$(".journal[data-taches]")) {
    if (!boite.dataset.taches.split(",").includes(tache)) continue;
    boite.append((boite.textContent ? "\n" : "") + texte);
    boite.scrollTop = boite.scrollHeight;
  }
}

function recevoirBarre(ev) {
  E.barre = { debut: ev.debut, but: ev.but, secondes: ev.secondes, texte: ev.texte, etape: ev.etape, depuis: performance.now() };
  if (!$(".barre-version") && TACHES_MAJ.includes(E.tache)) rendreBarre();
  if (!vueActuelle()?.querySelector(".progression")) rendre();
  suivreBarre();
}

function recevoirCopie(ev) {
  if (ev.etat === "attente") E.copieFinie = false;
  if (ev.etat === "fini") {
    E.copieFinie = true;
    toast(tr("Sauvegarde copiée !"), tr("Elle est choisie pour fabriquer le jeu."), "succes");
  }
  if (!(E.copieFinie && ev.etat === "arret")) E.copieEtat = ev.etat;
}

function recevoirTache(ev) {
  if (ev.etat === "debut") { E.tache = ev.nom; return; }
  E.tache = null;
  E.barre = null;
  if (E.reglages.son_fin && ev.nom !== "copie") son(ev.ok);
  if (ev.nom === "iphone") lireIphone();
  if (!ev.ok) {
    if (ev.code === "autre_signature") demanderReinstallation(ev.apk || E.dernierAPK || E.reglages.output, ev.nom === "maj_telephone");
    else toast(tr("Échec"), ev.erreur || "", "erreur");
    return;
  }
  const resultat = ev.resultat || {};
  if (ev.nom === "fabrication") {
    E.dernierAPK = resultat.apk;
    question(tr("L'APK est prêt"), tr("L'installer sur le téléphone branché ?"), [
      { titre: tr("Installer"), action: () => installer() },
      { titre: tr("Voir le fichier"), action: () => demander("montrer", { chemin: E.dernierAPK }) },
      { titre: tr("Plus tard"), annuler: true }]);
  } else if (ev.nom === "installation" || ev.nom === "maj_telephone") {
    let texte = tr("Le jeu est installé sur {model}.", { model: resultat.modele || "" });
    if (resultat.gardee) texte += "\n" + tr("Ancienne sauvegarde gardée : {name}", { name: nomFichier(resultat.gardee) });
    toast(ev.nom === "maj_telephone" ? tr("Téléphone à jour") : tr("Jeu installé"), texte, "succes");
    api("telephones", { rafraichir: true });
  } else if (ev.nom === "iphone") {
    toast(tr("L'IPA est prête"), tr("À installer avec Sideloadly."), "succes");
  } else if (ev.nom === "copie" && resultat.sauvegarde) {
    lister();
  } else if (ev.nom === "maj_outil") {
    question(tr("Outil à jour"), tr("Il faut relancer l'outil."), [{ titre: tr("Relancer"), action: () => demander("relancer") }]);
  } else if (ev.nom === "adb") {
    toast(tr("Outils Android installés"), "", "succes");
    const suite = E.apresAdb;
    E.apresAdb = null;
    suite?.();
  }
}

// The end of a task: a high tone when it worked, a low one when it failed.
function son(reussi) {
  try {
    const ctx = new AudioContext(), osc = ctx.createOscillator(), gain = ctx.createGain();
    osc.frequency.value = reussi ? 880 : 220;
    gain.gain.setValueAtTime(0.15, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.5);
    osc.connect(gain).connect(ctx.destination);
    osc.onended = () => ctx.close();  // the browser allows only a few open audio contexts
    osc.start();
    osc.stop(ctx.currentTime + 0.5);
  } catch { /* no sound device */ }
}

// Toasts and questions -----------------------------------------------------------------------------------
const ICONE_TOAST = { succes: "succes", erreur: "alerte" };

function toast(titre, texte, genre = "info") {
  const el = document.createElement("div");
  el.className = `toast ${genre}`;
  el.dataset.action = "fermer-toast";
  el.innerHTML = `${SVG[ICONE_TOAST[genre] || "info"]}<div><b>${h(titre)}</b>${texte ? `<small>${h(texte)}</small>` : ""}</div>`;
  $("#toasts").append(el);
  setTimeout(() => fermerToast(el), genre === "erreur" ? 9000 : 5000);
}

function fermerToast(el) {
  if (el.classList.contains("part")) return;
  el.classList.add("part");
  setTimeout(() => el.remove(), 320);
}

// A question's choices: the first is the main button (unless it cancels), the one with `annuler` answers Escape.
let choixQuestion = [];

function question(titre, texte, choix) {
  $("#question")?.remove();
  choixQuestion = choix;
  const boutons = choix.map((c, i) => `<button data-action="repondre" data-q="${i}" class="${i === 0 && !c.annuler ? "principal" : "secondaire"}">${h(c.titre)}</button>`);
  const fond = document.createElement("div");
  fond.id = "question";
  fond.innerHTML = `<div class="boite"><h3 class="jeu">${h(titre)}</h3><p>${h(texte)}</p><div class="boutons">${boutons.reverse().join("")}</div></div>`;
  document.body.append(fond);
  $(".principal", fond)?.focus();
}

function repondre(rang) {
  const choix = choixQuestion[rang];
  $("#question")?.remove();
  choixQuestion = [];
  choix?.action?.();
}

// Actions that ask -------------------------------------------------------------------------------------
function demanderAdb(suite = null) {
  question(tr("Outils Android"), tr("Il faut les outils Android de Google (10 Mo). Les télécharger ?"), [
    { titre: tr("Télécharger"), action: () => { E.apresAdb = suite; api("adb_telecharger"); } },
    { titre: tr("Annuler"), annuler: true }]);
}

async function installer(apk, remplacer) {
  const fichier = apk || E.dernierAPK || E.reglages.output;
  const corps = { apk: fichier };
  if (remplacer !== undefined) corps.remplacer = remplacer;
  const [, code] = await api("installer", corps, { codes: ["question_remplacer", "adb_absent"] });
  if (code === "adb_absent") demanderAdb(() => installer(fichier, remplacer));
  else if (code === "question_remplacer") {
    question(tr("Le jeu hors ligne est déjà sur le téléphone"),
      tr("Garder sa progression, ou la remplacer par la sauvegarde de cet APK ? L'ancienne est gardée dans Sauvegardes."), [
        { titre: tr("Garder la progression"), action: () => installer(fichier, false) },
        { titre: tr("Remplacer"), action: () => installer(fichier, true) },
        { titre: tr("Annuler"), annuler: true }]);
  } else E.dernierAPK = fichier;
}

function demanderReinstallation(apk, garde) {
  const texte = garde
    ? tr("Ce jeu vient d'un autre ordinateur : il faut d'abord le désinstaller. La progression est gardée, pas les réglages du jeu.")
    : tr("Un autre Ranger Rumble est sur le téléphone. Le désinstaller pour installer celui-ci ? Sa progression sur le téléphone sera effacée (une copie est gardée).");
  question(tr("Désinstaller l'ancien jeu ?"), texte, [
    { titre: tr("Désinstaller et installer"), action: () => api("reinstaller", { apk, tache: garde ? "maj_telephone" : "installation" }) },
    { titre: tr("Annuler"), annuler: true }]);
}

async function mettreAJourTelephone(forcer = false) {
  const [details, code] = await api("maj_telephone", { forcer }, { codes: ["deja_a_jour", "jeu", "adb_absent"] });
  if (code === "deja_a_jour") {
    question(tr("Déjà à jour"), tr("Le jeu du téléphone est déjà à jour ({version}). Le réinstaller quand même ?", { version: details.version || "" }), [
      { titre: tr("Réinstaller"), action: () => mettreAJourTelephone(true) }, { titre: tr("Annuler"), annuler: true }]);
  } else if (code === "jeu") {
    toast(tr("Jeu officiel manquant"), details.erreur || "", "erreur");
    aller("android", "fabrication");
  } else if (code === "adb_absent") demanderAdb(() => mettreAJourTelephone(forcer));
}

async function lister() {
  const [reponse] = await api("sauvegardes", {}, { silencieux: true });
  E.sauvegardes = reponse?.sauvegardes || [];
  rendre();
}

async function lireEspaceLibre() {
  E.libre = 0;  // asked once; null again when the APK's place changes
  const [reponse] = await api("espace", { chemin: E.reglages.output });
  if (reponse) { E.libre = reponse.libre; rendre(); }
}

async function lireIphone() {
  const [reponse] = await api("iphone_etat", {}, { silencieux: true });
  if (!reponse) return;
  E.iphone = reponse;
  rendreBarre();
  if (E.section === "ios") rendre();
}

async function chargerInfos() {
  for (const nom of ["cle_info", "certificat_info", "composants", "temporaires"]) {
    const [reponse] = await api(nom, {}, { silencieux: true });
    if (reponse) E.infos[nom] = reponse;
  }
  if (E.section === "reglages") rendre();
}

async function ouvrirSauvegarde(source, chemin, oublier = false) {
  const corps = { source, oublier };
  if (chemin) corps.chemin = chemin;
  const [reponse, code] = await api("ed_ouvrir", corps, { codes: ["changements", "adb_absent"] });
  if (code === "changements") {
    question(tr("Changements non enregistrés"), tr("Les oublier ?"), [
      { titre: tr("Oublier"), action: () => ouvrirSauvegarde(source, chemin, true) }, { titre: tr("Annuler"), annuler: true }]);
  } else if (code === "adb_absent") demanderAdb(() => ouvrirSauvegarde(source, chemin, oublier));
  else if (reponse) majEditeur(reponse);
}

function majEditeur(reponse) {
  E.editeur = reponse;
  E.edVersion++;
  // the table's lines stay shown while they are read again (the box just changed keeps its cursor); the tree is read again whole
  E.edArbre = null;
  rendre();
}

// Answers whether the engine took the change. Refused: the lines are read again, so a value shown early goes back.
async function editer(nom, corps = {}) {
  const [reponse] = await api(nom, corps);
  if (reponse) { majEditeur(reponse); return true; }
  E.edVersion++;
  E.edLignes = null;
  rendre();
  return false;
}

// A cell of the editor's table: shown changed at once, before the lines are read again.
function changerCase(el, valeur) {
  const rang = Number(el.dataset.ligne), ligne = E.edLignes?.lignes[rang];
  if (ligne) ligne.valeurs[el.dataset.cle] = valeur;
  editer("ed_changer", { onglet: E.onglet, ligne: rang, cle: el.dataset.cle, valeur, nom: ligne?.valeurs.name ?? null });
}

// Every « check for updates » button: the sidebar's turns while the engine asks, and the answer shows in a toast.
async function verifierMaj() {
  if (E.verification) return;
  E.verification = true;
  rendreBarre();
  const [reponse] = await api("maj_verifier");
  E.verification = false;
  rendreBarre();
  const titre = tr("Mises à jour");
  if (reponse?.etat === "nouvelle") toast(titre, tr("La version {v} est disponible.", { v: reponse.version || "" }), "succes");
  else if (reponse?.etat === "a_jour") toast(titre, tr("Pas de mise à jour."), "succes");
  else toast(titre, tr("Vérification impossible (pas de connexion ?)."), "erreur");
}

// Navigation and drawing -------------------------------------------------------------------------------
function aller(section, page = null) {
  E.section = section;
  E.page = section === "android" ? page : null;
  rendreBarre();
  rendre();
  if (section !== "reglages" && E.reglages.derniere_page !== section) {
    E.reglages.derniere_page = section;
    api("reglages_ecrire", { derniere_page: section });
  }
}

// A view is drawn again in place while the window stays on it; another one fades in while the old one fades out.
let cleVue = "";

function rendre() {
  const cle = `${E.section}/${E.page || ""}`;
  const html = vue();
  const actuelle = vueActuelle();
  if (cle === cleVue && actuelle) {
    garderEtat(actuelle, () => { actuelle.innerHTML = html; journauxEnBas(actuelle); });
  } else {
    cleVue = cle;
    if (actuelle) {
      actuelle.classList.add("sortie");
      setTimeout(() => actuelle.remove(), 220 * duree());
    }
    const nouvelle = document.createElement("div");
    nouvelle.className = "vue";
    nouvelle.innerHTML = html;
    $("#contenu").append(nouvelle);
    journauxEnBas(nouvelle);
    // once in, the view's entrance animations do not play again when it is drawn again
    setTimeout(() => nouvelle.classList.add("calme"), 500 * duree());
  }
  apresRendu();
}

function vue() {
  if (E.section === "ios") return E.iphone.bientot === false ? pageIphone() : prochainement("ios");
  if (E.section === "ordinateur") return prochainement("ordinateur");
  if (E.section === "reglages") return reglages();
  return E.page ? pageOutil(E.page) : accueil();
}

function journauxEnBas(dans) {
  for (const boite of $$(".journal[data-taches]", dans)) boite.scrollTop = boite.scrollHeight;
}

// Elements kept across a redraw: the banner's pictures keep moving, an unchanged QR code does not fade in again.
const VIVANTS = [".banniere .images", ".qr svg"];

// What the player was doing stays: the field being typed in, where the lists and logs were scrolled.
function garderEtat(vue, refaire) {
  const actif = document.activeElement;
  const focus = actif?.id && vue.contains(actif)
    ? { id: actif.id, debut: actif.selectionStart, fin: actif.selectionEnd, tape: actif.dataset.tape ? actif.value : null } : null;
  const defilements = [vue, ...$$("[data-garde]", vue)].map((el) => [el.dataset.garde || "", el.scrollTop]);
  const vivants = VIVANTS.map((choix) => [choix, $(choix, vue)]);
  refaire();
  for (const [choix, ancien] of vivants) {
    const nouveau = $(choix, vue);
    if (ancien && nouveau && (choix !== ".qr svg" || ancien.outerHTML === nouveau.outerHTML)) nouveau.replaceWith(ancien);
  }
  for (const [nom, haut] of defilements) {
    const el = nom ? $(`[data-garde="${nom}"]`, vue) : vue;
    if (el) el.scrollTop = haut;
  }
  const el = focus && document.getElementById(focus.id);
  if (!el) return;
  if (focus.tape !== null) { el.value = focus.tape; el.dataset.tape = "1"; }  // what was being typed is not lost
  el.focus();
  try { el.setSelectionRange(focus.debut, focus.fin); } catch { /* not a text field */ }
}

function apresRendu() {
  // a picture that already failed (index.html) is hidden before it shows broken
  if (window.imagesCassees?.size) for (const img of $$("img:not(.cassee)")) if (imagesCassees.has(img.src)) img.classList.add("cassee");
  placerIndicateurs();
  retrouverBulle();
  if (E.section === "ios" && E.iphone.bientot === false && E.libre === null) lireEspaceLibre();
  if (E.section !== "android") return;
  if (E.page === "editeur" && E.editeur.ouvert) chargerEditeur();
  if (E.page === "fabrication" && E.libre === null) lireEspaceLibre();
}

// Where each sliding highlight last stood. A view drawn again makes a new highlight element: it is put back
// there first, without a transition, then slides to its new place (not from the top of the list).
const indicateurs = {};

function glisser(nom, el, place) {
  if (!el.dataset.place) {
    el.dataset.place = 1;
    el.style.transition = "none";
    Object.assign(el.style, indicateurs[nom] || place);
    void el.offsetWidth;  // the start position is drawn before the transition comes back
    el.style.transition = "";
  }
  Object.assign(el.style, place);
  indicateurs[nom] = place;
}

function placerIndicateurs() {
  const vue = vueActuelle();
  if (!vue) return;
  const onglet = $(".onglets button.choisi", vue), indicOnglet = $(".onglets .indic", vue);
  if (onglet && indicOnglet) glisser("onglets", indicOnglet, { width: `${onglet.offsetWidth}px`, transform: `translateX(${onglet.offsetLeft}px)` });
  const section = $(".sections button.choisie", vue), indicSection = $(".sections .indic", vue);
  if (indicSection) {
    indicSection.style.opacity = section ? 1 : 0;
    if (section) glisser("sections", indicSection, { transform: `translateY(${section.offsetTop}px)` });
  }
}

function placerSurligne() {
  const choisie = $("#barre .tuile.choisie");
  if (!choisie) return;
  const barre = $("#barre").getBoundingClientRect(), r = choisie.getBoundingClientRect();
  glisser("barre", $("#surligne"), { transform: `translateY(${r.top - barre.top}px)`, left: `${r.left - barre.left}px`, width: `${r.width}px` });
}

// Notes ------------------------------------------------------------------------------------------------
// A note waits in data-bulle; it shows in a bubble on hover or keyboard focus, after a short delay.
const BULLE = { el: null, cible: null, minuterie: 0, x: -1, y: -1 };

function bulleAvec(contenu, note) {
  if (!note) return contenu;
  return `<span class="avec-bulle" data-bulle="${h(note)}">${avecI(contenu, `<span class="i-bulle" tabindex="0" role="img" aria-label="${h(note)}">i</span>`)}</span>`;
}

// The « i » stays on the line of the title's last word (html: the title, already escaped).
function avecI(html, i) {
  const k = html.lastIndexOf(" ");
  return `${html.slice(0, k + 1)}<span class="colle">${html.slice(k + 1)}${i}</span>`;
}

function viserBulle(cible, delai) {
  if (cible?.closest(".sortie")) cible = null;  // a view on its way out shows no note
  if (cible === BULLE.cible) return;
  cacherBulle();
  if (!cible) return;
  BULLE.cible = cible;
  BULLE.minuterie = setTimeout(() => BULLE.cible && montrerBulle(BULLE.cible), delai);
}

function montrerBulle(cible) {
  if (!cible.isConnected || cible.closest(".sortie")) { cacherBulle(); return; }
  clearTimeout(BULLE.minuterie);
  BULLE.cible = cible;
  if (!BULLE.el) {
    BULLE.el = document.createElement("div");
    BULLE.el.id = "bulle";
    BULLE.el.setAttribute("role", "tooltip");
    document.body.append(BULLE.el);
  }
  const el = BULLE.el;
  el.textContent = cible.dataset.bulle;
  const ancre = cible.getBoundingClientRect();
  const largeur = el.offsetWidth, hauteur = el.offsetHeight;
  const x = Math.max(8, Math.min(ancre.left, innerWidth - largeur - 8));
  const y = ancre.bottom + 8 + hauteur <= innerHeight - 8 ? ancre.bottom + 8 : Math.max(8, ancre.top - hauteur - 8);
  el.style.left = `${x}px`;
  el.style.top = `${y}px`;
  el.classList.add("visible");
}

function cacherBulle() {
  clearTimeout(BULLE.minuterie);
  BULLE.cible = null;
  BULLE.el?.classList.remove("visible");
}

// After a redraw the note's element is a new one: the bubble follows it if the pointer is still on the same note.
function retrouverBulle() {
  if (!BULLE.cible || BULLE.cible.isConnected) return;
  const texte = BULLE.cible.dataset.bulle, montree = BULLE.el?.classList.contains("visible");
  const sous = BULLE.x >= 0 ? document.elementFromPoint(BULLE.x, BULLE.y)?.closest("[data-bulle]") : null;
  if (!sous || sous.dataset.bulle !== texte) { cacherBulle(); return; }
  BULLE.cible = sous;
  if (montree) montrerBulle(sous);
}

// The sidebar ------------------------------------------------------------------------------------------
function tuile(section, nomIcone, titre, detail, bientot = false) {
  return `
    <button class="tuile ${E.section === section ? "choisie" : ""}" data-action="section" data-section="${section}">
      <span class="ic">${SVG[nomIcone]}</span>
      <span><div class="t jeu">${h(titre)}</div>${detail ? `<div class="d ${bientot ? "prochain" : ""}">${h(detail)}</div>` : ""}</span>
      ${bientot ? icone("cadenas", "cadenas") : ""}
    </button>`;
}

const BARRE_VERSION = `<div class="barre-version"><div class="tete"><span></span><b>0 %</b></div><div class="piste"><div class="plein"></div></div></div>`;

function ligneVersion() {
  const nouvelle = majDisponible();
  const verifier = h(tr("Vérifier les mises à jour"));
  return `<div class="ligne-version">${nouvelle ? '<span class="point"></span>' : ""}
    <span class="texte-version" ${nouvelle ? 'data-action="page-majs"' : ""}>${h(tr("Outil {v} · Jeu {g}", { v: E.version, g: E.jeu }))}</span>
    <button class="verifier-maj ${E.verification ? "tourne" : ""}" data-action="maj-verifier" data-bulle="${verifier}" aria-label="${verifier}"
      ${E.tache === "maj_outil" ? "disabled" : ""}>${SVG.rafraichir}</button></div>
    ${E.barre && TACHES_MAJ.includes(E.tache) ? BARRE_VERSION : ""}`;
}

function rendreBarre() {
  const t = telephone();
  const detailAndroid = E.tache ? tr("En cours : {t}", { t: nomTache(E.tache) }) : t ? t.modele : tr("Disponible");
  const iosBientot = E.iphone.bientot !== false;
  const detailIos = iosBientot ? tr("Prochainement") : E.tache === "iphone" ? tr("En cours : {t}", { t: nomTache("iphone") })
    : E.iphone.pret ? tr("IPA prête") : tr("Disponible");
  $("#tuiles").innerHTML = tuile("android", "android", "Android", detailAndroid)
    + tuile("ios", "apple", "iOS", detailIos, iosBientot)
    + tuile("ordinateur", "ordinateur", tr("Ordinateur"), tr("Prochainement"), true);
  $("#tuiles-bas").innerHTML = tuile("reglages", "reglages", tr("Réglages"), "");
  $("#version").innerHTML = ligneVersion();
  placerSurligne();
  retrouverBulle();
}

// Android: home ----------------------------------------------------------------------------------------
function accueil() {
  const cartes = Object.entries(PAGES).map(([page, { image, icone: nomIcone, taches }]) => `
    <button class="carte-outil" data-action="page" data-page="${page}">
      <div class="img"><img src="/ressources/lanceur/${image}.png" alt=""></div>
      <span class="badge">${SVG[nomIcone]}</span>
      <div class="corps"><h3 class="jeu">${h(titrePage(page))}</h3>
      ${taches.includes(E.tache) ? `<span class="puce" style="--c:var(--a1)">${SVG.sablier} ${h(tr("En cours"))}</span>` : ""}</div>
    </button>`).join("");
  return `${banniere()}<div class="section"><div class="titre-section">${h(tr("OUTILS"))}</div><div class="grille">${cartes}</div></div>`;
}

// The banner shows its pictures in turn; a redraw keeps the same elements (garderEtat), so the turn goes on.
let rangBanniere = 0;

function banniere() {
  const images = BANNIERE.map((nom, i) => `<img src="/ressources/lanceur/${nom}.png" alt="" class="${i === rangBanniere ? "vue-img" : ""}">`).join("");
  return `<div class="banniere"><div class="images">${images}</div>
    <div class="texte">
      <div class="puces"><span class="puce" style="--c:var(--vert)">${SVG.check} ANDROID</span>
      <span class="puce" style="--c:var(--a1)">${h(tr("Jeu {g}", { g: E.jeu }))}</span></div>
      <h1 class="jeu">${h(tr("Ranger Rumble hors ligne"))}</h1>
      <p>${h(tr("Le jeu complet, sans serveur. La progression iPhone continue sur Android."))}</p>
      <div class="actions">${boutonPrincipal()}${etatTelephone()}</div>
    </div></div>`;
}

function tournerBanniere() {
  const vue = vueActuelle();
  if (!vue || document.hidden || E.reglages.animations === "aucune") return;
  const images = $$(".banniere .images img", vue);
  if (images.length < 2) return;
  images[rangBanniere].classList.remove("vue-img");
  rangBanniere = (rangBanniere + 1) % images.length;
  images[rangBanniere].classList.add("vue-img");
}

function boutonPrincipal() {
  const t = telephone();
  if (E.tache) {
    const vers = E.tache === "iphone" ? 'data-action="section" data-section="ios"' : `data-action="page" data-page="${pageDeTache(E.tache)}"`;
    return `<button class="principal grand jeu" ${vers}>${SVG.sablier} ${h(tr("En cours : {t}", { t: nomTache(E.tache) }))}</button>`;
  }
  if (t && t.jeu && t.origine !== "officiel" && t.version && plusAncien(t.version, E.jeu)) {
    return `<button class="principal grand jeu" data-action="maj-telephone">${SVG.sortie} ${h(tr("Mettre à jour le téléphone"))}</button>`;
  }
  return `<button class="principal grand jeu" data-action="page" data-page="fabrication">${SVG.play} ${h(tr("Installer le jeu"))}</button>`;
}

function etatTelephone() {
  const t = telephone();
  let detail;
  if (!t) detail = E.telephones.some((x) => x.etat === "unauthorized") ? tr("Toucher « Autoriser » sur le téléphone") : tr("Téléphone : notification USB > « Transfert de fichiers »");
  else if (!t.jeu) detail = tr("Pas de Ranger Rumble");
  else if (t.origine === "officiel") detail = tr("Jeu officiel");
  else detail = tr("Jeu hors ligne {v}", { v: t.version || "?" });
  return `<div class="verre"><span class="dot ${t ? "on" : ""}"></span><span><b>${h(t ? t.modele : tr("Aucun téléphone branché"))}</b><small>${h(detail)}</small></span>${t ? "" : boutonAideTelephone()}</div>`;
}

// The small « i » beside « Aucun téléphone branché »: how to have the phone recognized (USB, developer mode).
function boutonAideTelephone() {
  const titre = h(tr("Faire reconnaître le téléphone"));
  return `<button class="aide-i" data-action="aide-telephone" data-bulle="${titre}" aria-label="${titre}">i</button>`;
}

// Android: tool pages ----------------------------------------------------------------------------------
// Only the copy's header has a line under its title: the deadline.
function pageOutil(page) {
  const corps = { copie: pageCopie, fabrication: pageFabrication, editeur: pageEditeur, majs: pageMajs }[page]();
  return `<div class="entete"><img class="fond" src="/ressources/lanceur/${PAGES[page].image}.png" alt="">
    <div class="ligne"><button class="retour" data-action="retour">${SVG.retour}</button>
    <span class="badge">${SVG[PAGES[page].icone]}</span>
    <div><h2 class="jeu">${h(titrePage(page))}</h2>${page === "copie" ? `<p>${h(tr("Garder la progression de l'iPhone avant le 1er mai 2027."))}</p>` : ""}</div></div></div>${corps}`;
}

function boiteJournal(taches) {
  const lignes = E.journal.filter((l) => taches.includes(l.tache)).slice(-JOURNAL_MONTRE).map((l) => l.texte).join("\n");
  return `<div class="journal" data-taches="${taches.join(",")}" data-garde="journal-${taches[0]}">${h(lignes)}</div>`;
}

// The progress card of a running task (filled by animerBarre), with its steps' names when it has some.
function progression(taches, etapes = []) {
  if (!E.barre || !taches.includes(E.tache)) return "";
  const chips = etapes.map((nom, i) => `<span data-etape="${i + 1}">${h(nom)}</span>`).join("");
  return `<div class="carte progression apparait"><div class="tete jeu"><span>${h(E.barre.texte)}</span><b>0 %</b></div>
    <div class="piste"><div class="plein"></div></div>${chips ? `<div class="etapes">${chips}</div>` : ""}</div>`;
}

const bascule = (coche, attributs, desactive = false) =>
  `<label class="interrupteur"><input type="checkbox" ${attributs}${coche ? " checked" : ""}${desactive ? " disabled" : ""}><i></i></label>`;

function pageCopie() {
  const etats = ["attente", "iphone", "jeu", "sauvegarde", "fini"];
  const titres = { attente: tr("En attente"), iphone: "iPhone", jeu: tr("Jeu"), sauvegarde: tr("Sauvegarde"), fini: tr("Copiée") };
  const rang = E.copieFinie ? 4 : etats.includes(E.copieEtat) ? etats.indexOf(E.copieEtat) : E.copieEtat === "certificat" ? 2 : -1;
  const marche = E.tache === "copie";
  const frise = etats.map((nom, i) => {
    const jalon = `<div class="jalon ${rang >= i ? "atteint" : ""} ${rang === i && marche && !E.copieFinie ? "actuel" : ""}">
      <div class="rond">${rang >= i ? SVG.check : ""}</div>${h(titres[nom])}</div>`;
    return i < etats.length - 1 ? jalon + `<div class="trait" style="--plein:${rang > i ? 1 : 0}"></div>` : jalon;
  }).join("");
  const etape = (n, texte) => `<div class="etape"><span class="num">${n}</span><span>${h(texte)}</span></div>`;
  const demarrer = marche
    ? `<button class="principal jeu" data-action="copie-arreter">${SVG.stop} ${h(tr("Arrêter"))}</button>`
    : `<button class="principal jeu" data-action="copie-demarrer" ${E.tache ? "disabled" : ""}>${SVG.play} ${h(tr("Démarrer"))}</button>`;
  return `<div class="colonne">
    <div class="rangee">
      <div class="carte"><h4 class="jeu">${h(tr("Sur l'iPhone"))}</h4>
        ${etape(1, tr("Mettre l'iPhone sur le même Wi-Fi que cet ordinateur."))}
        ${etape(2, tr("Scanner le QR code avec l'appareil photo, puis télécharger le profil RatchetRR."))}
        ${etape(3, tr("Réglages > Général > tout en bas, « VPN et gestion de l'appareil » > RatchetRR : valider le profil (Installer)."))}
        ${etape(4, tr("Réglages > Général > Informations : tout en bas, « Réglages des certificats » > activer RatchetRR."))}
        ${etape(5, tr("Ouvrir Ranger Rumble et attendre l'écran d'accueil."))}
        <div class="boutons">
          ${demarrer}
          <button class="secondaire" data-action="ouvrir" data-chemin="${h(E.copies)}">${h(tr("Dossier des copies"))}</button>
        </div></div>
      <div class="carte carte-qr">
        <div class="qr">${E.qrSvg || icone("qr", "vide")}</div>
        <div class="adresse">${h(E.qr || tr("Le QR code apparaît au démarrage."))}</div></div>
    </div>
    <div class="carte"><h4 class="jeu petit">${h(tr("Progression"))}</h4><div class="frise">${frise}</div>
      ${E.copieEtat === "certificat" ? `<div class="message ko">${SVG.alerte} ${h(tr("Le jeu refuse le certificat : il faut refaire l'étape 4."))}</div>` : ""}
      ${E.copieFinie ? `<div class="message ok">${SVG.succes} ${h(tr("Sauvegarde copiée ! Il faut ensuite supprimer le profil RatchetRR de l'iPhone."))}
        <span class="espace"></span><button class="principal jeu" data-action="page" data-page="fabrication">${h(tr("Fabriquer le jeu"))}</button></div>` : ""}
    </div>
    ${boiteJournal(["copie"])}</div>`;
}

// A path of the settings, chosen with its button (the file's name shown, the whole path in a note).
function champ(cle, titre, nomIcone, vide, action) {
  const valeur = E.reglages[cle] || "";
  const montre = valeur
    ? `<span data-bulle="${h(valeur)}"><span class="ok">✓</span>${h(nomFichier(valeur))}</span>`
    : `<span class="vide">${h(vide)}</span>`;
  return `<div class="champ">${SVG[nomIcone]}<div class="quoi"><small>${h(titre)}</small>
    ${montre}</div>
    ${cle === "artworks" && valeur ? `<button class="secondaire" data-action="effacer" data-cle="artworks">${h(tr("Retirer"))}</button>` : ""}
    <button class="secondaire" data-action="${action}" data-cle="${cle}">${h(tr("Choisir…"))}</button></div>`;
}

const etapesFabrication = () => [tr("Lecture"), tr("Modifications"), tr("Préparation"), tr("Sauvegarde"), tr("Signature"), tr("Fini")];
// The iPhone's: the APK's first five, then the libraries' conversion and the IPA (jeu_ios.STEP_CONVERSION...).
const etapesIphone = () => [...etapesFabrication().slice(0, 5), tr("Conversion"), "IPA"];
const espaceLibre = () => (E.libre ? `<div class="libre ${E.libre < 5e9 ? "peu" : ""}">${h(tr("Espace libre : {n} Go (il faut 5 Go)", { n: (E.libre / 1e9).toFixed(1) }))}</div>` : "");

// What a build is made from: the official file, the progression (a save or a new game), the gallery's pictures.
function champsJeu() {
  const nouvelle = !!E.reglages.nouvelle_partie;
  const options = E.sauvegardes.map((s) => `<option value="${h(s.chemin)}" ${s.chemin === E.reglages.sauvegarde ? "selected" : ""}>${h(s.libelle)}</option>`).join("");
  return `${champ("official", tr("Jeu officiel 1.10.4"), "doc", tr("Le fichier .xapk, .apkm ou .apk complet"), "choisir-jeu")}
      <div class="champ">${SVG.personne}<div class="quoi"><small>${h(tr("Progression"))}</small>
        <div class="boutons">
          <select class="choix" id="choix-sauvegarde" data-change="sauvegarde" ${nouvelle ? "disabled" : ""}>
            <option value="">${h(tr("Choisir une sauvegarde"))}</option>${options}</select>
          <button class="secondaire" data-action="autre-sauvegarde">${h(tr("Autre fichier…"))}</button>
          ${bascule(nouvelle, 'data-change="nouvelle"')}
          <span class="petit">${h(tr("Nouvelle partie"))}</span>
        </div></div></div>
      ${champ("artworks", tr("Images de la galerie (facultatif)"), "image", tr("Un dossier d'images pour l'artbook du jeu"), "choisir-dossier")}`;
}

function pageFabrication() {
  const t = telephone();
  return `<div class="colonne">
    <div class="carte champs">
      ${champsJeu()}
      ${champ("output", tr("APK à créer"), "sortie", "RangerRumble_hors_ligne.apk", "choisir-sortie")}
      ${espaceLibre()}
    </div>
    <div class="boutons">
      <button class="principal grand jeu" data-action="fabriquer" ${E.tache ? "disabled" : ""}>${SVG.marteau} ${h(tr("Fabriquer l'APK"))}</button>
      <button class="secondaire" data-action="installer" ${E.tache ? "disabled" : ""}>${SVG.cable} ${h(tr("Installer sur le téléphone"))}</button>
      <span class="espace"></span>
      <span class="etat-tel"><span class="dot ${t ? "on" : ""}"></span>${h(t ? t.modele : tr("Aucun téléphone branché"))}${t ? "" : boutonAideTelephone()}</span>
    </div>
    ${progression(["fabrication", "installation"], E.tache === "fabrication" ? etapesFabrication() : [])}
    ${boiteJournal(["fabrication", "installation", "adb"])}</div>`;
}

function pageMajs() {
  const t = telephone();
  const etatOutil = { nouvelle: tr("La version {v} est disponible.", { v: E.maj.version || "" }), a_jour: tr("À jour."),
    impossible: tr("Vérification impossible (pas de connexion ?).") }[E.maj.etat] || tr("Pas encore vérifié.");
  let etatTel = tr("Aucun téléphone branché.");
  if (t) etatTel = !t.jeu ? tr("{m} : pas de Ranger Rumble.", { m: t.modele }) : t.origine === "officiel" ? tr("{m} : jeu officiel.", { m: t.modele })
    : tr("{m} : jeu hors ligne {v}.", { m: t.modele, v: t.version || "?" });
  const tete = (titre, version, etat) => `<h4 class="jeu avec-puce">${h(titre)}<span class="espace"></span><span class="puce" style="--c:var(--a1)">${h(version)}</span></h4>
      <p class="etat">${h(etat)}</p>`;
  return `<div class="colonne"><div class="rangee">
    <div class="carte">${tete(tr("L'outil"), E.version, etatOutil)}
      ${majDisponible() && E.maj.notes ? `<div class="journal notes">${h(E.maj.notes)}</div>` : ""}
      <div class="boutons"><button class="secondaire" data-action="maj-verifier">${h(tr("Vérifier maintenant"))}</button>
      ${majDisponible() ? `<button class="principal jeu" data-action="maj-outil" ${E.tache ? "disabled" : ""}>${h(tr("Installer la version {v}", { v: E.maj.version }))}</button>` : ""}</div></div>
    <div class="carte">${tete(tr("Le jeu du téléphone"), E.jeu, etatTel)}
      <button class="principal jeu" data-action="maj-telephone" ${E.tache || !t ? "disabled" : ""}>${SVG.sortie} ${h(tr("Mettre à jour le téléphone"))}</button></div>
    </div>${progression(TACHES_MAJ)}${boiteJournal(["maj_telephone", "maj_outil", "installation"])}</div>`;
}

// Android: the editor ----------------------------------------------------------------------------------
function pageEditeur() {
  const ouvrir = `<div class="boutons"><span class="intitule">${h(tr("Ouvrir :"))}</span>
    <button class="secondaire" data-action="ed-ouvrir" data-source="telephone">${SVG.cable} ${h(tr("Le téléphone"))}</button>
    <button class="secondaire" data-action="ed-ouvrir" data-source="fichier">${SVG.doc} ${h(tr("Un fichier…"))}</button>
    <button class="secondaire" data-action="ed-ouvrir" data-source="copie">${SVG.dossier} ${h(tr("Une copie…"))}</button>
    <button class="secondaire" data-action="ed-ouvrir" data-source="nouvelle">${SVG.etoile} ${h(tr("Partie vierge"))}</button></div>`;
  if (!E.editeur.ouvert) {
    return `<div class="editeur">${ouvrir}<div class="vide-editeur">${SVG.sortie}<h3 class="jeu">${h(tr("Aucune sauvegarde ouverte"))}</h3>
      <span>${h(tr("Il faut en ouvrir une, en haut."))}</span></div></div>`;
  }
  const resume = E.editeur.resume || {};
  const monnaies = (resume.currencies || []).map((m) => `<span class="monnaie" data-bulle="${h(m.name)}">${m.icon ? `<img src="/ressources/icones/${h(m.icon)}.png" alt="">` : ""}${chiffre(m.value)}</span>`).join("");
  const comptes = (resume.counts || []).map((c) => `<span class="compte"><b class="jeu">${h(c.total ? `${c.owned}/${c.total}` : c.owned)}</b><small>${h(c.label)}</small></span>`).join("");
  const changements = (E.editeur.changements || []).length;
  const onglets = ONGLETS.map(([cle, titre]) => `<button class="${E.onglet === cle ? "choisi" : ""}" data-action="onglet" data-onglet="${cle}">${h(tr(titre))}</button>`).join("");
  return `<div class="editeur">${ouvrir}
    <div class="carte resume"><div><div class="pseudo jeu">${h(resume.nickname || tr("Sans nom"))}</div><div class="source">${h(E.editeur.source)}</div></div>
      ${monnaies}<span class="espace"></span>${comptes}
      ${changements ? `<span class="puce" style="--c:var(--orange)">${h(tr("{n} modifiée(s)", { n: changements }))}</span>` : ""}</div>
    <div class="onglets"><span class="indic"></span>${onglets}</div>
    ${E.onglet === "tout" ? arbre() : tableau()}
    <div class="boutons">
      <button class="principal jeu" data-action="ed-envoyer">${SVG.avion} ${h(tr("Envoyer au téléphone"))}</button>
      <button class="secondaire" data-action="ed-enregistrer">${SVG.disquette} ${h(tr("Enregistrer sous…"))}</button>
      <button class="secondaire" data-action="ed-pour-apk">${SVG.boite} ${h(tr("Utiliser pour l'APK"))}</button>
      <span class="espace"></span>
      <button class="secondaire" data-action="ed-annuler" ${changements ? "" : "disabled"}>${SVG.annuler} ${h(tr("Annuler les changements"))}</button></div></div>`;
}

// Reads the open tab's lines (or the tree's roots) once per tab and per change of the save.
let chargement = "";

async function chargerEditeur() {
  const cle = `${E.onglet}-${E.edVersion}`;
  if (chargement === cle) return;
  if (E.onglet === "tout") {
    if (E.edArbre) return;
    chargement = cle;
    const [reponse] = await api("ed_arbre");
    E.edArbre = { racines: reponse?.noeuds || [], ouverts: {} };
  } else {
    if (E.edLignes?.cle === cle) return;
    chargement = cle;
    const [reponse] = await api("ed_lignes", { onglet: E.onglet });
    E.edLignes = { cle, colonnes: reponse?.colonnes || [], lignes: reponse?.lignes || [] };
  }
  chargement = "";
  rendre();
}

function tableau() {
  const donnees = E.edLignes;
  if (!donnees?.cle.startsWith(`${E.onglet}-`)) return `<div class="carte table"></div>`;
  const { colonnes, lignes } = donnees;
  // a name keeps a sensible width; the space a large window adds goes to the values
  const gabarit = `40px ${colonnes.map((c) => (["name", "hero"].includes(c.cle) ? "minmax(140px, 260px)" : "minmax(64px, 1fr)")).join(" ")}`;
  const tete = `<div class="tete"><span></span>${colonnes.map((c) => `<span class="${c.type ? "c" : ""}">${h(c.titre)}</span>`).join("")}</div>`;
  const rangees = lignes.map((ligne, i) => {
    const etat = ligne.possede === true ? "possede" : ligne.possede === false ? "absent" : "";
    const image = ligne.icone ? `<img src="/ressources/icones/${h(ligne.icone)}.png" alt="">` : "<span></span>";
    return `<div class="ligne ${etat}">${image}${colonnes.map((c) => cellule(ligne, i, c)).join("")}</div>`;
  }).join("");
  const actions = (ACTIONS_ONGLET[E.onglet] || []).map(([quoi, titre]) => `<button class="secondaire" data-action="ed-action" data-quoi="${quoi}">${h(tr(titre))}</button>`).join("");
  return `${actions ? `<div class="boutons">${actions}</div>` : ""}<div class="carte table" style="--colonnes:${gabarit}">${tete}<div class="lignes" data-garde="lignes">${rangees}</div></div>`;
}

function cellule(ligne, rang, { cle, type }) {
  const valeur = ligne.valeurs[cle], modifiable = ligne.modifiable[cle];
  const reperes = `data-ligne="${rang}" data-cle="${h(cle)}"`;
  if (type === "bool") return `<span class="c">${bascule(valeur, `data-change="ed-bool" ${reperes}`, !modifiable)}</span>`;
  if (type === "int" && modifiable) {
    const texte = typeof valeur === "string";
    return `<span class="c"><input class="valeur${texte ? " texte" : ""}" id="v-${rang}-${h(cle)}" value="${h(valeur ?? "")}" data-change="ed-valeur" ${reperes}></span>`;
  }
  return `<span class="${type ? "c" : "nom"}">${h(valeur ?? "—")}</span>`;
}

// The whole save as a tree: a node's children are read when it opens, under the key "0/3/1" (its place).
function arbre() {
  if (!E.edArbre) return `<div class="carte table"></div>`;
  const noeud = (n, cle) => {
    const enfants = E.edArbre.ouverts[cle];
    return `<div class="noeud ${enfants ? "ouvert" : ""}"><div class="tete-noeud" data-action="noeud" data-cle="${h(cle)}">
      <span class="fleche">${n.children ? "▶" : ""}</span><b>${h(n.label)}</b><span class="val ${n.modifiable ? "modif" : ""}">${h(n.text)}</span>
      <span class="type">${h(n.kind)}</span></div>${enfants ? `<div class="enfants">${enfants.map((e, i) => noeud(e, `${cle}/${i}`)).join("")}</div>` : ""}</div>`;
  };
  return `<div class="note-arbre">${h(tr("Toute la sauvegarde. Avec précaution."))}</div>
    <div class="carte table"><div class="arbre" data-garde="arbre">${E.edArbre.racines.map((n, i) => noeud(n, String(i))).join("")}</div></div>`;
}

function noeudDe(cle) {
  const rangs = cle.split("/").map(Number);
  let liste = E.edArbre.racines, n = null;
  rangs.forEach((i, k) => {
    n = liste[i];
    if (k < rangs.length - 1) liste = E.edArbre.ouverts[rangs.slice(0, k + 1).join("/")];
  });
  return n;
}

async function toucherNoeud(cle) {
  const n = noeudDe(cle);
  if (!n) return;
  if (n.children) {
    if (E.edArbre.ouverts[cle]) { delete E.edArbre.ouverts[cle]; rendre(); return; }
    const [reponse] = await api("ed_arbre", { partie: n.part, chemin: n.path, type: n.kind });
    E.edArbre.ouverts[cle] = reponse?.noeuds || [];
    rendre();
  } else if (n.modifiable) {
    const saisie = prompt(n.label, String(n.text).replace(/^'|'$/g, ""));
    if (saisie === null) return;
    const valeur = n.text === "True" || n.text === "False" ? saisie.toLowerCase() === "true"
      : saisie !== "" && !isNaN(Number(saisie)) ? Number(saisie) : saisie;
    editer("ed_noeud_changer", { partie: n.part, chemin: n.path, type: n.kind, valeur });
  }
}

// iPhone and iPad: an .ipa made from the official file, installed with Sideloadly ----------------------------
function pageIphone() {
  const I = E.iphone, pret = !!I.pret, marche = E.tache === "iphone";
  let etat;
  if (I.manque) etat = ["", tr("Impossible"), I.manque];
  else if (pret) etat = ["on", tr("IPA prête"), tr("Préparée le {d}, {n} Go", { d: I.infos?.date || "?", n: ((I.taille || 0) / 1e9).toFixed(1) })];
  else etat = ["", tr("À préparer"), tr("Quelques minutes, une seule fois")];
  const preparer = `data-action="iphone-preparer" ${E.tache || I.manque ? "disabled" : ""}`;
  const principal = marche
    ? `<button class="principal grand jeu" disabled>${SVG.sablier} ${h(tr("En cours : {t}", { t: nomTache("iphone") }))}</button>`
    : pret ? `<button class="principal grand jeu" data-action="montrer" data-chemin="${h(I.ipa)}">${SVG.dossier} ${h(tr("Afficher l'IPA"))}</button>`
      : `<button class="principal grand jeu" ${preparer}>${SVG.marteau} ${h(tr("Préparer pour iPhone"))}</button>`;
  return `<div class="banniere"><div class="images"><img src="/ressources/lanceur/fond_6.png" alt="" class="vue-img"></div>
    <div class="texte">
      <div class="puces"><span class="puce" style="--c:#8ab4ff">${SVG.apple} IPHONE · IPAD</span>
      <span class="puce" style="--c:var(--a1)">${h(tr("Jeu {g}", { g: E.jeu }))}</span>
      <span class="puce" style="--c:var(--orange)">${h(tr("Essai"))}</span></div>
      <h1 class="jeu">${h(tr("Ranger Rumble hors ligne"))}</h1>
      <div class="actions">${principal}
        <div class="verre"><span class="dot ${etat[0]}"></span><span><b>${h(etat[1])}</b><small>${h(etat[2])}</small></span></div></div>
    </div></div>
    <div class="section"><div class="titre-section">${h(tr("PRÉPARATION"))}</div>
    <div class="colonne">
      <div class="carte champs">${champsJeu()}${espaceLibre()}</div>
      <div class="boutons">
        <button class="secondaire" ${preparer}>${SVG.marteau} ${h(pret ? tr("Préparer à nouveau") : tr("Préparer pour iPhone"))}</button>
        <span class="espace"></span>
        ${pret ? `<button class="secondaire" data-action="montrer" data-chemin="${h(I.ipa)}">${h(tr("Afficher l'IPA"))}</button>` : ""}
      </div>
      ${progression(["iphone"], etapesIphone())}
      ${marche || E.journal.some((l) => l.tache === "iphone") ? boiteJournal(["iphone"]) : ""}
    </div>
    <div class="titre-section">${h(tr("INSTALLATION AVEC SIDELOADLY"))}</div>
    ${etapesSideloadly(pret ? I.ipa : null)}</div>`;
}

// What to do with the IPA: Sideloadly, the iPhone's settings, every 7 days.
function etapesSideloadly(ipa) {
  const etape = (n, texte) => `<div class="etape"><span class="num">${n}</span><span>${h(texte)}</span></div>`;
  return `<div class="carte">
    ${etape(1, tr("Installer Sideloadly sur cet ordinateur (gratuit)."))}
    ${etape(2, tr("Brancher l'iPhone par câble, le déverrouiller, puis « Se fier » à cet ordinateur."))}
    ${etape(3, tr("Sur l'iPhone : Réglages > Confidentialité et sécurité > Mode développeur : activer, puis redémarrer."))}
    ${etape(4, tr("Dans Sideloadly : glisser l'IPA, choisir l'iPhone, saisir son identifiant Apple, puis Start."))}
    ${etape(5, tr("Sur l'iPhone : Réglages > Général > VPN et gestion de l'appareil > son identifiant Apple > Faire confiance."))}
    ${etape(6, tr("Ouvrir Ranger Rumble."))}
    <div class="message note">${SVG.synchro} ${h(tr("Avec un compte Apple gratuit, l'app s'arrête au bout de 7 jours : refaire l'étape 4. La progression est gardée."))}</div>
    <div class="boutons">
      <button class="secondaire" data-action="iphone-site">${h(tr("Site de Sideloadly"))}</button>
      ${ipa ? `<button class="secondaire" data-action="montrer" data-chemin="${h(ipa)}">${h(tr("Afficher l'IPA"))}</button>` : ""}
    </div></div>`;
}

// Coming soon ------------------------------------------------------------------------------------------
function prochainement(plateforme) {
  const ios = plateforme === "ios";
  return `<div class="bientot"><img class="flou" src="/ressources/lanceur/${ios ? "fond_6" : "fond_3"}.png" alt="">
    <div class="milieu"><div class="medaillon">${ios ? SVG.apple : SVG.ordinateur}<span class="badge verrou">${SVG.cadenas}</span></div>
      <div class="sous jeu">${ios ? "iOS" : h(tr("Ordinateur"))}</div>
      <h1 class="brillant jeu">${h(tr("Prochainement"))}</h1>
      <div class="phrase">${h(ios ? tr("Le jeu hors ligne sur iPhone et iPad est en préparation.") : tr("Le jeu hors ligne sur ordinateur est en préparation."))}</div>
      <button class="puce" style="--c:var(--a1)" data-action="section" data-section="android">← ${h(tr("En attendant : la version Android"))}</button>
    </div></div>`;
}

// Settings ---------------------------------------------------------------------------------------------
const interrupteur = (cle) => bascule(E.reglages[cle], `data-change="drapeau" data-cle="${cle}"`);

function segments(cle, choix) {
  return `<div class="segments">${choix.map(([valeur, titre]) => `<button class="${E.reglages[cle] === valeur ? "choisi" : ""}" data-action="regler" data-cle="${cle}" data-valeur="${h(valeur)}">${h(titre)}</button>`).join("")}</div>`;
}

const bouton = (action, texte, attributs = "", desactive = false) =>
  `<button class="secondaire" data-action="${action}" ${attributs} ${desactive ? "disabled" : ""}>${h(texte)}</button>`;
const boutons = (...contenu) => `<div class="boutons">${contenu.join("")}</div>`;
const info = (nom, cle) => { const v = E.infos[nom]?.[cle]; return v === null || v === undefined ? "—" : String(v); };

// Every setting, in order: { section, titre, detail (a value under the title: path, version, state),
// vue (its controls), note (what it does, in the « i ») }. The search looks through all of them.
function listeReglages() {
  const liste = [];
  const ajouter = (section, titre, detail, vue, note = "") => liste.push({ section, titre, detail, vue, note });
  const chemin = (cle, vide) => E.reglages[cle] || vide;
  const choisirChemin = (cle, dossier, effacer) => boutons(bouton(dossier ? "choisir-dossier" : "choisir-jeu", tr("Choisir…"), `data-cle="${cle}"`),
    effacer && E.reglages[cle] ? bouton("effacer", tr("Retirer"), `data-cle="${cle}"`) : "");
  const puce = (couleur, texte) => `<span class="puce" style="--c:${couleur}">${h(texte)}</span>`;

  ajouter("general", tr("Langue"), "", `<select class="choix" data-change="langue">${E.langues.map(([code, nom]) => `<option value="${h(code)}" ${code === E.langue ? "selected" : ""}>${h(nom)}</option>`).join("")}</select>`);
  ajouter("general", tr("Chercher les mises à jour au démarrage"), "", interrupteur("maj_demarrage"));
  ajouter("general", tr("Page d'ouverture"), "", segments("page_depart", [["accueil", tr("Android")], ["derniere", tr("La dernière ouverte")]]));
  ajouter("general", tr("Son à la fin d'une tâche"), "", interrupteur("son_fin"));
  ajouter("general", tr("Empêcher la veille pendant une tâche"), "", interrupteur("anti_veille"));

  ajouter("apparence", tr("Animations"), "", segments("animations", [["completes", tr("Complètes")], ["reduites", tr("Réduites")], ["aucune", tr("Aucune")]]));
  const accent = E.reglages.accent || "vert";
  ajouter("apparence", tr("Couleur"), "", `<div class="pastilles">${ACCENTS.map(([valeur, a, b, nom]) => `<button data-bulle="${h(tr(nom))}" aria-label="${h(tr(nom))}" class="${accent === valeur ? "choisi" : ""}" style="background:linear-gradient(135deg,${a},${b})" data-action="regler" data-cle="accent" data-valeur="${valeur}"></button>`).join("")}</div>`);

  ajouter("jeu", tr("Jeu officiel 1.10.4"), chemin("official", tr("Pas encore choisi")), choisirChemin("official", false));
  ajouter("jeu", tr("Dossier des sauvegardes"), chemin("dossier_sauvegardes", E.copies), choisirChemin("dossier_sauvegardes", true, true));
  ajouter("jeu", tr("APK à créer"), chemin("output", ""), boutons(bouton("choisir-sortie", tr("Choisir…"), 'data-cle="output"'), bouton("montrer", tr("Montrer"), `data-chemin="${h(E.reglages.output)}"`)));
  ajouter("jeu", tr("Images de la galerie"), chemin("artworks", tr("Aucune (facultatif)")), choisirChemin("artworks", true, true));
  ajouter("jeu", tr("Dossier de travail"), chemin("dossier_travail", tr("À côté de l'APK")), choisirChemin("dossier_travail", true, true));

  ajouter("telephone", tr("Outils Android (adb)"), E.reglages.adb || (E.adb ? tr("Automatique : {p}", { p: E.adb }) : tr("Pas encore installés")),
    boutons(bouton("choisir-adb", tr("Choisir…")), E.reglages.adb ? bouton("effacer", tr("Automatique"), 'data-cle="adb"') : "", bouton("adb", E.adb ? tr("Réinstaller") : tr("Télécharger"), "", !!E.tache)));
  ajouter("telephone", tr("Téléphones branchés"), "", bouton("actualiser", tr("Actualiser")), tr("Débogage USB activé, USB en « Transfert de fichiers »."));
  for (const t of E.telephones) {
    const origine = !t.jeu ? (t.etat === "device" ? tr("pas de Ranger Rumble") : "") : t.origine === "officiel" ? tr("jeu officiel")
      : t.origine === "cet_ordinateur" ? tr("jeu hors ligne {v}, installé par cet ordinateur", { v: t.version || "?" }) : tr("jeu hors ligne {v}, installé par un autre ordinateur", { v: t.version || "?" });
    const etat = t.etat === "device" ? tr("Prêt") : t.etat === "unauthorized" ? tr("À autoriser") : t.etat;
    ajouter("telephone", t.modele, [t.serie, origine].filter(Boolean).join(" · "), puce(t.etat === "device" ? "var(--vert)" : "var(--orange)", etat));
  }

  const certificat = E.infos.certificat_info?.existe;
  ajouter("copie", tr("Certificat RatchetRR"), certificat ? tr("Créé le {d}", { d: info("certificat_info", "date") }) : tr("Créé à la première copie"),
    boutons(bouton("ouvrir", tr("Montrer"), `data-chemin="${h(info("certificat_info", "dossier"))}"`, !certificat), bouton("certificat-recreer", tr("Recréer"), "", E.tache === "copie")));
  ajouter("copie", tr("Dossier des copies"), E.copies, bouton("ouvrir", tr("Ouvrir"), `data-chemin="${h(E.copies)}"`));

  const cle = E.infos.cle_info?.existe;
  ajouter("cle", tr("Clé de cet ordinateur"), cle ? tr("Signature {s} · créée le {d}", { s: info("cle_info", "signature"), d: info("cle_info", "date") }) : tr("Créée à la première fabrication"),
    bouton("cle-exporter", tr("Exporter…"), "", !cle));
  ajouter("cle", tr("Importer une clé"), "", bouton("cle-importer", tr("Importer…")),
    tr("Pour mettre à jour, depuis cet ordinateur, un jeu installé par un autre ordinateur. La clé actuelle est gardée à côté."));

  const versions = tr("Outil {v} · Jeu {g}", { v: E.version, g: E.jeu });
  ajouter("majs", tr("Versions"), versions,
    boutons(bouton("maj-verifier", tr("Vérifier maintenant")), majDisponible() ? `<button class="principal jeu" data-action="maj-outil">${h(tr("Installer la version {v}", { v: E.maj.version }))}</button>` : ""));

  const composants = E.infos.composants || {};
  ajouter("composants", "Python", `${info("composants", "python")} · ${info("composants", "chemin")}`,
    composants.ok === false ? puce("var(--orange)", tr("À réparer")) : puce("var(--vert)", tr("Prêt")));
  ajouter("composants", tr("Réparer les composants"), "", bouton("reparer", tr("Réparer"), "", !!E.tache));
  if (composants.pip_log) ajouter("composants", tr("Journal d'installation"), composants.pip_log, bouton("ouvrir", tr("Ouvrir"), `data-chemin="${h(composants.pip_log)}"`));

  ajouter("avance", tr("Journal de la session"), "", boutons(bouton("journal", tr("Voir")), bouton("journal-copier", tr("Copier"))));
  if (composants.erreur_log) ajouter("avance", tr("Dernière erreur au démarrage"), composants.erreur_log, bouton("ouvrir", tr("Ouvrir"), `data-chemin="${h(composants.erreur_log)}"`));
  ajouter("avance", tr("Dossier de l'outil"), E.base, bouton("ouvrir", tr("Ouvrir"), `data-chemin="${h(E.base)}"`));
  const taille = E.infos.temporaires?.taille || 0;
  ajouter("avance", tr("Fichiers temporaires"), taille ? tr("{n} Mo laissés par une fabrication arrêtée", { n: Math.round(taille / 1e6) }) : tr("Rien à nettoyer"),
    bouton("nettoyer", tr("Nettoyer"), "", !taille || !!E.tache));
  ajouter("avance", tr("Réinitialiser les réglages"), "", bouton("reinitialiser", tr("Réinitialiser")));

  ajouter("apropos", tr("Ranger Rumble hors ligne"), tr("Projet de fans, sans lien avec Sony Interactive Entertainment, Insomniac Games ou Oh BiBi."),
    `<img src="/ressources/lanceur/logo_petit.png" width="90" alt="">`);
  ajouter("apropos", tr("Versions"), versions, "");
  return liste;
}

const plier = (texte) => String(texte).normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();  // no case, no accents

function reglages() {
  const tous = listeReglages();
  const titreSection = (cle) => tr(SECTIONS.find(([c]) => c === cle)[1]);
  const groupe = (cle, liste) => `<div class="groupe apparait"><h3 class="jeu">${SVG[SECTIONS.find(([c]) => c === cle)[2]]}${h(titreSection(cle))}</h3>
    <div class="carte">${liste.map((g) => `<div class="reglage"><div class="quoi"><b>${bulleAvec(h(g.titre), g.note)}</b>${g.detail ? `<small>${h(g.detail)}</small>` : ""}</div>${g.vue}</div>`).join("")}</div></div>`;
  let droite;
  if (E.recherche) {
    const cherche = plier(E.recherche);
    const trouves = tous.filter((g) => [g.titre, g.detail, g.note, titreSection(g.section)].some((t) => plier(t).includes(cherche)));
    droite = trouves.length
      ? SECTIONS.map(([cle]) => [cle, trouves.filter((g) => g.section === cle)]).map(([cle, liste]) => (liste.length ? groupe(cle, liste) : "")).join("")
      : `<p class="aucun-reglage">${h(tr("Aucun réglage trouvé."))}</p>`;
  } else {
    droite = groupe(E.sectionReglages, tous.filter((g) => g.section === E.sectionReglages));
  }
  const nav = SECTIONS.map(([cle, titre, nomIcone]) => `<button class="${!E.recherche && E.sectionReglages === cle ? "choisie" : ""}" data-action="section-reglages" data-cle="${cle}">${SVG[nomIcone]}${h(tr(titre))}</button>`).join("");
  return `<div class="reglages"><nav><h2 class="jeu">${h(tr("Réglages"))}</h2>
    <div class="recherche">${SVG.recherche}<input id="recherche" placeholder="${h(tr("Rechercher"))}" value="${h(E.recherche)}" data-change="recherche"></div>
    <div class="sections"><span class="indic"></span>${nav}</div></nav>
    <div class="droite" data-garde="reglages"><div>${droite}</div></div></div>`;
}

function montrerJournal() {
  const feuille = document.createElement("div");
  feuille.className = "feuille";
  feuille.innerHTML = `<div class="boutons"><h3 class="jeu">${h(tr("Journal de la session"))}</h3>
      <button class="principal jeu" data-action="fermer-feuille">${h(tr("Fermer"))}</button></div>
      <div class="journal">${h(texteJournal())}</div>`;
  document.body.append(feuille);
}

// The progress bars -----------------------------------------------------------------------------------
// The engine gives a start, a goal and the seconds it should take: the bar eases towards the goal. It is painted
// each frame while a task has one, in the progress card and in the slim bar under the version (an update).
function avancement(b) {
  let valeur = b.debut;
  if (b.secondes > 0 && b.but > b.debut) valeur += (b.but - b.debut) * (1 - Math.exp(-(performance.now() - b.depuis) / 1000 / b.secondes));
  return Math.max(0, Math.min(100, valeur));
}

function peindreBarre(el, b, valeur) {
  $(".plein", el).style.width = `${valeur}%`;
  $(".tete b", el).textContent = `${Math.floor(valeur)} %`;
  $(".tete span", el).textContent = b.texte;
}

let imageBarre = 0;
const suivreBarre = () => { if (!imageBarre) imageBarre = requestAnimationFrame(animerBarre); };

function animerBarre() {
  imageBarre = 0;
  const b = E.barre;
  if (!b) return;
  const valeur = avancement(b), etape = b.etape || 0;
  const petite = $(".barre-version");
  if (petite) peindreBarre(petite, b, valeur);
  const carte = vueActuelle()?.querySelector(".progression");
  if (carte) {
    peindreBarre(carte, b, valeur);
    for (const chip of $$("[data-etape]", carte)) {
      const n = Number(chip.dataset.etape);
      chip.className = etape > n || valeur >= 100 ? "faite" : etape === n ? "encours" : "";
    }
  }
  suivreBarre();
}

// Clicks and changes: one layer, on the document. data-action names a click, data-change a field's change ---------
const ACTIONS = {
  // where to go
  section: (el) => aller(el.dataset.section),
  page: (el) => aller("android", el.dataset.page),
  retour: () => aller("android", null),
  "page-majs": () => aller("android", "majs"),
  "section-reglages": (el) => { E.recherche = ""; E.sectionReglages = el.dataset.cle; rendre(); },
  onglet: (el) => { E.onglet = el.dataset.onglet; rendre(); },

  // toasts, questions, sheets
  repondre: (el) => repondre(Number(el.dataset.q)),
  "fermer-toast": (el) => fermerToast(el),
  "fermer-feuille": (el) => el.closest(".feuille").remove(),
  "aide-telephone": () => question(tr("Faire reconnaître le téléphone"), tr("1. Brancher le téléphone avec un câble USB.\n2. Sur le téléphone : glisser du haut de l'écran, toucher la notification USB, choisir « Transfert de fichiers ».\n3. Toujours rien ? Activer le mode développeur (une seule fois) : Paramètres > À propos du téléphone, toucher 7 fois « Numéro de build » (Samsung : À propos du téléphone > Informations sur le logiciel > « Numéro de version »).\n4. Paramètres > Options de développement (tout en bas, ou dans Système) : activer « Débogage USB ».\n5. Toucher « Autoriser » quand le téléphone demande « Autoriser le débogage USB ? »."), [{ titre: tr("OK") }]),

  // files and folders
  ouvrir: (el) => demander("ouvrir", { chemin: el.dataset.chemin }),
  montrer: (el) => demander("montrer", { chemin: el.dataset.chemin }),
  "choisir-jeu": async (el) => {
    const cle = el.dataset.cle;
    const chemin = await choisir({ types: cle === "official" ? ["xapk", "apkm", "apk"] : [], depart: E.reglages[cle] });
    if (chemin) ecrire({ [cle]: chemin });
  },
  "choisir-dossier": async (el) => {
    const cle = el.dataset.cle;
    const chemin = await choisir({ dossier: true, depart: E.reglages[cle] });
    if (!chemin) return;
    await ecrire({ [cle]: chemin });
    if (cle === "dossier_sauvegardes") lister();
  },
  "choisir-sortie": async () => {
    const chemin = await demander("enregistrer", { nom: "RangerRumble_hors_ligne.apk", types: ["apk"] });
    if (chemin) { E.libre = null; ecrire({ output: chemin }); }
  },
  "choisir-adb": async () => { const chemin = await choisir({}); if (chemin) ecrire({ adb: chemin }); },
  effacer: async (el) => {
    await ecrire({ [el.dataset.cle]: "" });
    if (el.dataset.cle === "dossier_sauvegardes") lister();
  },
  "autre-sauvegarde": async () => {
    const chemin = await choisir({ types: ["msgpack"] });
    if (!chemin) return;
    await ecrire({ sauvegarde: chemin, nouvelle_partie: false });
    lister();
  },

  // tasks
  "copie-demarrer": () => api("copie_demarrer"),
  "copie-arreter": () => api("copie_arreter"),
  fabriquer: () => api("fabriquer", { jeu: E.reglages.official, sortie: E.reglages.output, sauvegarde: E.reglages.sauvegarde,
    nouvelle: !!E.reglages.nouvelle_partie, images: E.reglages.artworks }),
  installer: () => installer(E.reglages.output),
  "iphone-preparer": () => api("iphone_preparer", { jeu: E.reglages.official, sauvegarde: E.reglages.sauvegarde,
    nouvelle: !!E.reglages.nouvelle_partie, images: E.reglages.artworks }),
  "iphone-site": () => api("iphone_site"),
  "maj-telephone": () => mettreAJourTelephone(),
  "maj-verifier": () => verifierMaj(),
  "maj-outil": () => api("maj_outil"),
  adb: () => demanderAdb(),
  actualiser: () => api("telephones", { rafraichir: true }),

  // the editor
  "ed-ouvrir": async (el) => {
    const source = el.dataset.source;
    if (source === "fichier") {
      const chemin = await choisir({ types: ["msgpack"] });
      if (chemin) ouvrirSauvegarde("fichier", chemin);
    } else if (source === "copie") {
      const chemin = await choisir({ dossier: true, depart: `${E.copies}/` });
      if (chemin) ouvrirSauvegarde("copie", chemin);
    } else ouvrirSauvegarde(source);
  },
  "ed-action": (el) => {
    const corps = { action: el.dataset.quoi };
    // « max »: for the lines owned only
    if (corps.action.startsWith("max")) corps.lignes = (E.edLignes?.lignes || []).flatMap((l, i) => (l.possede ? [i] : []));
    editer("ed_action", corps);
  },
  "ed-envoyer": () => editer("ed_envoyer"),
  "ed-enregistrer": async () => {
    const chemin = await demander("enregistrer", { nom: "RangerRumble_sauvegarde.msgpack", types: ["msgpack"] });
    if (chemin) editer("ed_enregistrer", { chemin });
  },
  "ed-pour-apk": async () => {
    const chemin = await demander("enregistrer", { nom: "RangerRumble_sauvegarde.msgpack", types: ["msgpack"] });
    if (!chemin || !(await editer("ed_enregistrer", { chemin, pour_apk: true }))) return;
    toast(tr("C'est fait"), tr("L'APK partira de cette sauvegarde."), "succes");
    lister();
  },
  "ed-annuler": () => editer("ed_annuler"),
  noeud: (el) => toucherNoeud(el.dataset.cle),

  // settings
  regler: (el) => ecrire({ [el.dataset.cle]: el.dataset.valeur }),
  "certificat-recreer": () => question(tr("Recréer le certificat ?"), tr("L'ancien est gardé à côté. Il faudra réinstaller le profil sur l'iPhone."), [
    { titre: tr("Recréer"), action: async () => { const [r] = await api("certificat_recreer"); if (r) { E.infos.certificat_info = r; rendre(); } } },
    { titre: tr("Annuler"), annuler: true }]),
  "cle-exporter": async () => {
    const chemin = await demander("enregistrer", { nom: "cle_apk.p12", types: ["p12"] });
    if (chemin && (await api("cle_exporter", { chemin }))[0]) toast(tr("Clé exportée"), tr("À garder en lieu sûr."), "succes");
  },
  "cle-importer": async () => {
    const chemin = await choisir({ types: ["p12"] });
    if (!chemin) return;
    question(tr("Remplacer la clé de cet ordinateur ?"), tr("Les prochains APK seront signés avec la clé importée."), [
      { titre: tr("Importer"), action: async () => { const [r] = await api("cle_importer", { chemin }); if (r) { E.infos.cle_info = r; toast(tr("Clé importée"), "", "succes"); rendre(); } } },
      { titre: tr("Annuler"), annuler: true }]);
  },
  reparer: () => question(tr("Réparer les composants ?"), tr("L'outil va redémarrer."), [
    { titre: tr("Réparer"), action: async () => { await api("composants_reparer"); demander("relancer"); } }, { titre: tr("Annuler"), annuler: true }]),
  journal: () => montrerJournal(),
  "journal-copier": () => navigator.clipboard.writeText(texteJournal()).then(
    () => toast(tr("Journal copié"), "", "succes"), () => toast(tr("Impossible"), "", "erreur")),
  nettoyer: async () => {
    const [r] = await api("nettoyer");
    if (!r) return;
    toast(tr("Nettoyé"), tr("{n} Mo dans la Corbeille", { n: Math.round((r.liberes || 0) / 1e6) }), "succes");
    E.infos.temporaires = { taille: 0 };
    rendre();
  },
  reinitialiser: () => question(tr("Réinitialiser les réglages ?"), tr("La langue est gardée."), [
    { titre: tr("Réinitialiser"), action: async () => { const [r] = await api("reinitialiser"); if (r) { E.reglages = r.reglages; appliquerApparence(); rendre(); } } },
    { titre: tr("Annuler"), annuler: true }]),
};

const CHANGEMENTS = {
  sauvegarde: (el) => ecrire({ sauvegarde: el.value, nouvelle_partie: false }),
  nouvelle: (el) => ecrire({ nouvelle_partie: el.checked }),
  drapeau: (el) => ecrire({ [el.dataset.cle]: el.checked }),
  langue: (el) => ecrire({ langue: el.value }),
  "ed-bool": (el) => changerCase(el, el.checked),
  "ed-valeur": (el) => {
    const texte = el.classList.contains("texte");
    const valeur = texte ? el.value : Number(el.value.replace(/\s/g, ""));
    if (texte || Number.isFinite(valeur)) changerCase(el, valeur);
  },
};

function surClic(e) {
  if (e.target.closest?.(".i-bulle")) { e.preventDefault(); return; }  // an « i » only shows its note
  const el = e.target.closest?.("[data-action]");
  if (el && !el.disabled) ACTIONS[el.dataset.action]?.(el, e);
}

function surTouche(e) {
  if (e.key === "Escape") {
    cacherBulle();
    if ($("#question")) {
      const annuler = choixQuestion.findIndex((c) => c.annuler);
      if (annuler >= 0) repondre(annuler);
      return;
    }
    if ($(".feuille")) { $(".feuille").remove(); return; }
    if (E.section === "android" && E.page) aller("android", null);
  } else if (e.key === "," && (e.metaKey || e.ctrlKey)) {
    e.preventDefault();
    aller("reglages");
  }
}

document.addEventListener("click", surClic);
document.addEventListener("keydown", surTouche);
document.addEventListener("change", (e) => {
  const el = e.target.closest?.("[data-change]");
  if (el) CHANGEMENTS[el.dataset.change]?.(el);
});
document.addEventListener("input", (e) => {
  const el = e.target;
  if (el.dataset?.change === "recherche") { E.recherche = el.value; rendre(); }
  if (el.matches?.("input.valeur")) el.dataset.tape = "1";  // typed, not sent yet
});
document.addEventListener("focusin", (e) => {
  if (e.target.matches?.(":focus-visible")) viserBulle(e.target.closest?.("[data-bulle]") || null, 150);
  // an editor box: its value selected at once, so that typing replaces it (Return or leaving sends it)
  if (e.target.matches?.("input.valeur") && !e.target.dataset.tape) e.target.select();
});
document.addEventListener("focusout", () => { if (BULLE.cible && !BULLE.cible.matches(":hover")) cacherBulle(); });
document.addEventListener("pointerover", (e) => {
  BULLE.x = e.clientX; BULLE.y = e.clientY;
  viserBulle(e.target.closest?.("[data-bulle]") || null, 450);
});
document.addEventListener("pointermove", (e) => { BULLE.x = e.clientX; BULLE.y = e.clientY; }, { passive: true });
document.addEventListener("pointerdown", (e) => {
  const i = e.target.closest?.(".i-bulle");
  if (i) montrerBulle(i.closest("[data-bulle]")); else cacherBulle();
}, true);
document.addEventListener("scroll", cacherBulle, true);
document.documentElement.addEventListener("pointerleave", () => { BULLE.x = -1; cacherBulle(); });
window.addEventListener("resize", () => { placerSurligne(); placerIndicateurs(); });
setInterval(tournerBanniere, 7000);

// Start ------------------------------------------------------------------------------------------------
// ?page=section/page opens a page at once (trials): android/editeur, reglages/telephone...
function ouvrirPageDemandee() {
  const [section, page] = (PARAMETRES.get("page") || "").split("/");
  if (!["android", "ios", "ordinateur", "reglages"].includes(section)) return;
  E.section = section;
  if (section === "android") E.page = PAGES[page] ? page : null;
  if (section === "reglages" && SECTIONS.some(([cle]) => cle === page)) E.sectionReglages = page;
}

async function demarrer() {
  E.table = await fetch("/ressources/langues.json").then((r) => r.json()).catch(() => ({}));
  const [bonjour] = await api("bonjour");
  if (!bonjour) return;
  const { version, jeu, reglages, langues, langue, copies, base, tache } = bonjour;
  Object.assign(E, { version, jeu, reglages, langues, langue, copies, base, tache });
  if (E.reglages.page_depart === "derniere" && ["android", "ios", "ordinateur"].includes(E.reglages.derniere_page)) E.section = E.reglages.derniere_page;
  ouvrirPageDemandee();
  appliquerApparence();
  traduireCadre();
  rendreBarre();
  rendre();
  ecouter();
  lister();
  chargerInfos();
  lireIphone();
  setTimeout(() => { $("#ouverture").classList.add("parti"); $("#app").classList.add("pret"); placerSurligne(); }, 900 * duree());
  if (PARAMETRES.get("visite")) visite();
}

// ?visite=1: the window shows itself, page after page (for a video of the launcher).
async function visite() {
  const etapes = [["android", 5], ["android/copie", 3.5], ["android", 2], ["android/fabrication", 3.5], ["android", 2], ["android/editeur", 4],
    ["android/majs", 3], ["ios", 4], ["ordinateur", 4], ["reglages/general", 3], ["reglages/apparence", 3], ["reglages/telephone", 3],
    ["reglages/cle", 3], ["android", 3]];
  const attendre = (secondes) => new Promise((r) => setTimeout(r, secondes * 1000));
  await attendre(2);
  for (const [chemin, secondes] of etapes) {
    const [section, page] = chemin.split("/");
    if (section === "reglages" && page) E.sectionReglages = page;
    if (section === "reglages" && E.section === "reglages") rendre(); else aller(section, page || null);
    await attendre(secondes);
  }
}

demarrer();
