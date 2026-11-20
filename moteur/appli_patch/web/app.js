// The Windows launcher (lanceur_web.py opens it in Edge): the Mac app's screens, drawn by the page; the engine
// (service.py) does the work. On the Mac, LanceurWeb (a test window) answers what the page asks the window.
"use strict";

const JETON = new URLSearchParams(location.search).get("jeton") || "";
const NATIF = window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.lanceur;

const E = {
  reglages: {}, version: "", jeu: "", langue: "en", langues: [], table: {}, telephones: [], adb: null, maj: {},
  tache: null, barre: null, copieEtat: null, copieFinie: false, qr: null, qrSvg: null, journal: [], sauvegardes: [],
  dernierAPK: null, editeur: { ouvert: false }, edVersion: 0, section: "android", page: null, sectionReglages: "general",
  recherche: "", onglet: "heros", infos: {}, copies: "", base: "", libre: null, apresAdb: null, flip: null, cle: "",
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
  dossier: P("M3 5h7l2 2h9v12H3z"), palette: P("M12 2a10 10 0 0 0 0 20c1.1 0 2-.9 2-2 0-.5-.2-1-.5-1.3-.3-.4-.5-.8-.5-1.3 0-1.1.9-2 2-2h2.4A5.6 5.6 0 0 0 22 10c0-4.4-4.5-8-10-8zM6.5 12a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3zm3-4a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3zm5 0a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3zm3 4a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3z", 1),
  telephone: P("M7 2h10a2 2 0 0 1 2 2v16a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2zm0 3v13h10V5z", 1),
  cle: P("M7 4a5 5 0 0 1 4.6 3H23v4h-2v3h-3v-3h-6.4A5 5 0 1 1 7 4zm0 3a2 2 0 1 0 0 4 2 2 0 0 0 0-4z", 1),
  outil: P("M21 6.4l-3.3 3.3-3.4-.9-.9-3.4L16.7 2A6 6 0 0 0 9.3 9.3L2 16.6 5.4 20l7.3-7.3A6 6 0 0 0 21 6.4z"),
  sablier: P("M6 2h12v5l-4 5 4 5v5H6v-5l4-5-4-5z"), etoile: P("M12 2l2 6 6 2-6 2-2 6-2-6-6-2 6-2z"),
  doc: P("M6 2h8l5 5v15H6zm7 1.5V8h4.5z", 1), avion: P("M2 21l21-9L2 3v7l15 2-15 2z"),
  disquette: P("M5 3h11l4 4v14H4V3zm2 2v5h8V5zm5 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6z", 1),
  annuler: P("M12.5 8c-2.6 0-5 1-6.9 2.6L2 7v9h9l-3.6-3.6A8 8 0 0 1 20.4 16l2.4-.8A10.5 10.5 0 0 0 12.5 8z"),
  liste: P("M3 4h4v4H3zm6 1h12v2H9zM5 10h4v4H5zm6 1h10v2H11zM5 16h4v4H5zm6 1h10v2H11z"),
  qr: P("M3 3h8v8H3zm2 2v4h4V5zm8-2h8v8h-8zm2 2v4h4V5zM3 13h8v8H3zm2 2v4h4v-4zm8-2h3v3h-3zm5 0h3v3h-3zm-5 5h3v3h-3zm5 0h3v3h-3z", 1),
  image: P("M3 4h18v16H3zm2 2v9l4-4 3 3 4-5 3 4V6zm3 1.5a1.5 1.5 0 1 1 0 3 1.5 1.5 0 0 1 0-3z", 1),
  personne: P("M12 3a4.5 4.5 0 1 1 0 9 4.5 4.5 0 0 1 0-9zm0 11c4.4 0 8 2 8 4.5V21H4v-2.5C4 16 7.6 14 12 14z"),
  sortie: P("M11 3h2v10l3.5-3.5 1.4 1.4L12 16.8l-5.9-5.9 1.5-1.4L11 13zM4 19h16v2H4z"),
};

const PAGES = {
  copie: { image: "fond_2", icone: "copie", taches: ["copie"] },
  fabrication: { image: "fond_1", icone: "boite", taches: ["fabrication", "installation", "adb"] },
  editeur: { image: "fond_4", icone: "curseurs", taches: [] },
  majs: { image: "fond_5", icone: "synchro", taches: ["maj_telephone", "maj_outil"] },
};
const BANNIERE = ["fond_1", "fond_3", "fond_2", "fond_5", "fond_6", "fond_4"];

// Small things -----------------------------------------------------------------------------------------
const $ = (choix, dans = document) => dans.querySelector(choix);
const $$ = (choix, dans = document) => [...dans.querySelectorAll(choix)];
const h = (texte) => String(texte ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const nomFichier = (chemin) => String(chemin || "").split(/[\\/]/).pop();
const duree = () => (E.reglages.animations === "aucune" ? 0 : E.reglages.animations === "reduites" || matchMedia("(prefers-reduced-motion: reduce)").matches ? 0.5 : 1);
const chiffre = (n) => Number(n || 0).toLocaleString("fr-FR").replace(/[\s\u00A0\u202F]/g, "\u202F");  // a space that never breaks the number

function tr(texte, valeurs = {}) {
  let resultat = texte;
  if (E.langue !== "fr") {
    const entree = E.table[texte.trim()];
    if (entree) resultat = entree[E.langue] || entree.en || texte;
  }
  for (const [cle, valeur] of Object.entries(valeurs)) resultat = resultat.split(`{${cle}}`).join(valeur);
  return resultat;
}

function nomTache(nom) {
  return { copie: tr("Copie de la sauvegarde"), fabrication: tr("Fabrication"), installation: tr("Installation"),
    maj_telephone: tr("Mise à jour du téléphone"), maj_outil: tr("Mise à jour de l'outil"), adb: tr("Outils Android") }[nom] || nom;
}

function titrePage(page) {
  return { copie: tr("Copier la sauvegarde iPhone"), fabrication: tr("Fabriquer et installer"), editeur: tr("Éditer une sauvegarde"),
    majs: tr("Mises à jour") }[page];
}

function textePage(page) {
  return { copie: tr("Garder la progression de l'iPhone avant le 1er mai 2027."),
    fabrication: tr("Le jeu hors ligne pour Android, installé par le câble."),
    editeur: tr("Héros, armes, costumes, monnaies, statistiques..."),
    majs: tr("L'outil et le jeu du téléphone, sans perdre la progression.") }[page];
}

const telephone = () => E.telephones.find((t) => t.etat === "device");
const majDisponible = () => E.maj.etat === "nouvelle";
const plusAncien = (a, b) => {
  const x = String(a).split(".").map(Number), y = String(b).split(".").map(Number);
  for (let i = 0; i < Math.max(x.length, y.length); i++) if ((x[i] || 0) !== (y[i] || 0)) return (x[i] || 0) < (y[i] || 0);
  return false;
};

// The engine ---------------------------------------------------------------------------------------------
async function api(nom, corps = {}, codes = []) {
  let reponse;
  try {
    const r = await fetch(`/api/${nom}`, { method: "POST", headers: { "X-Jeton": JETON, "Content-Type": "application/json" },
      body: JSON.stringify(corps) });
    reponse = await r.json();
  } catch (erreur) {
    toast(tr("Impossible"), String(erreur), "erreur");
    return [null, null];
  }
  if (reponse.ok) return [reponse, null];
  if (codes.includes(reponse.code)) return [reponse, reponse.code];
  if (reponse.code === "adb_absent") demanderAdb(() => {});
  else toast(tr("Impossible"), reponse.erreur, "erreur");
  return [null, reponse.code];
}

const commande = (nom, corps) => api(nom, corps);

// What a web page cannot do (choose a file and get its path...): the engine does it ------------------------
let numeroDemande = 0;
const attentes = {};
window.lanceurReponse = (id, valeur) => { attentes[id]?.(valeur); delete attentes[id]; };

function demander(type, donnees = {}) {
  if (!NATIF) {
    if (type === "copier") return navigator.clipboard.writeText(donnees.texte).then(() => true, () => false);
    if (type === "son") { son(donnees.nom); return Promise.resolve(true); }
    return api("fenetre", { type, ...donnees }).then(([reponse]) => (reponse ? reponse.valeur : null));
  }
  const id = ++numeroDemande;
  return new Promise((resolve) => { attentes[id] = resolve; NATIF.postMessage({ id, type, ...donnees }); });
}

// Settings -----------------------------------------------------------------------------------------------
async function ecrire(valeurs) {
  Object.assign(E.reglages, valeurs);
  appliquerApparence();
  rendre();
  const [reponse] = await api("reglages_ecrire", valeurs);
  if (reponse) E.reglages = reponse.reglages;
  if (valeurs.langue) { E.langue = valeurs.langue; traduireCadre(); rendre(); }
}

function appliquerApparence() {
  const racine = document.documentElement;
  racine.dataset.theme = E.reglages.theme || "sombre";
  racine.dataset.accent = E.reglages.accent || "or";
  racine.dataset.animations = E.reglages.animations || "completes";
  racine.style.setProperty("--duree", duree() || 0.001);
  racine.lang = E.langue;
}

// Events of the engine --------------------------------------------------------------------------------
function ecouter() {
  const source = new EventSource(`/api/evenements?jeton=${encodeURIComponent(JETON)}`);
  source.onmessage = (message) => recevoir(JSON.parse(message.data));
}

function recevoir(ev) {
  switch (ev.type) {
    case "journal": {
      E.journal.push({ texte: ev.texte, tache: ev.tache });
      if (E.journal.length > 3000) E.journal.splice(0, E.journal.length - 3000);
      for (const boite of $$(".journal[data-taches]")) {
        if (ev.tache && boite.dataset.taches.split(",").includes(ev.tache)) {
          boite.append(document.createTextNode((boite.textContent ? "\n" : "") + ev.texte));
          boite.scrollTop = boite.scrollHeight;
        }
      }
      return;
    }
    case "barre":
      E.barre = { debut: ev.debut, but: ev.but, secondes: ev.secondes, texte: ev.texte, etape: ev.etape, depuis: performance.now() };
      if (!$(".progression")) rendre();
      return;
    case "tache": recevoirTache(ev); break;
    case "copie":
      if (ev.etat === "attente") E.copieFinie = false;
      if (ev.etat === "fini") { E.copieFinie = true; toast(tr("Sauvegarde copiée !"), tr("Elle est choisie pour fabriquer le jeu."), "succes"); }
      if (!(E.copieFinie && ev.etat === "arret")) E.copieEtat = ev.etat;
      break;
    case "copie_qr": E.qr = ev.url; E.qrSvg = ev.svg; break;
    case "telephones": E.adb = ev.adb; E.telephones = ev.telephones || []; break;
    case "maj": E.maj = ev; break;
    case "pare_feu":
      question(tr("Pare-feu"), tr("Le pare-feu de Windows bloque l'iPhone."), [
        { titre: tr("Autoriser"), action: () => commande("pare_feu_regler") }, { titre: tr("Plus tard"), annuler: true }]);
      break;
    default: return;
  }
  rendreBarre();
  rendre();
}

function recevoirTache(ev) {
  if (ev.etat === "debut") { E.tache = ev.nom; return; }
  E.tache = null;
  const resultat = ev.resultat || {};
  if (E.reglages.son_fin && ev.nom !== "copie") son(ev.ok ? "Glass" : "Basso");
  E.barre = null;
  if (!ev.ok) {
    if (ev.code === "autre_signature") demanderReinstallation(ev.apk || E.dernierAPK || E.reglages.output, ev.nom === "maj_telephone");
    else toast(tr("Échec"), ev.erreur || "", "erreur");
    return;
  }
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
    commande("telephones", { rafraichir: true });
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

function son(nom) {
  if (NATIF) { NATIF.postMessage({ id: 0, type: "son", nom }); return; }
  try {
    const ctx = new AudioContext(), osc = ctx.createOscillator(), gain = ctx.createGain();
    osc.frequency.value = nom === "Glass" ? 880 : 220;
    gain.gain.setValueAtTime(0.15, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.5);
    osc.connect(gain).connect(ctx.destination);
    osc.start(); osc.stop(ctx.currentTime + 0.5);
  } catch { /* no sound */ }
}

// Toasts and questions -----------------------------------------------------------------------------------
function toast(titre, texte, genre = "info") {
  const el = document.createElement("div");
  el.className = `toast ${genre}`;
  el.innerHTML = `${genre === "succes" ? SVG.succes : genre === "erreur" ? SVG.alerte : SVG.info}<div><b>${h(titre)}</b>${texte ? `<small>${h(texte)}</small>` : ""}</div>`;
  $("#toasts").append(el);
  const fermer = () => { el.classList.add("part"); setTimeout(() => el.remove(), 320); };
  el.onclick = fermer;
  setTimeout(fermer, genre === "erreur" ? 9000 : 5000);
}

function question(titre, texte, choix) {
  $("#question")?.remove();
  const fond = document.createElement("div");
  fond.id = "question";
  const boutons = [...choix].reverse().map((c, i) => {
    const premier = c === choix[0];
    return `<button data-q="${choix.length - 1 - i}" class="${premier && !c.annuler ? "principal" : "secondaire"}">${h(c.titre)}</button>`;
  }).join("");
  fond.innerHTML = `<div class="boite"><h3 class="jeu">${h(titre)}</h3><p>${h(texte)}</p><div class="boutons">${boutons}</div></div>`;
  fond.addEventListener("click", (e) => {
    const bouton = e.target.closest("[data-q]");
    if (!bouton) return;
    fond.remove();
    choix[Number(bouton.dataset.q)].action?.();
  });
  document.body.append(fond);
  fond.querySelector(".principal")?.focus();
}

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    if ($("#question")) { $("#question .secondaire:last-child, #question .secondaire")?.click(); return; }
    if ($(".feuille")) { $(".feuille").remove(); return; }
    if (E.section === "android" && E.page) aller("android", null);
  }
  if (e.key === "," && (e.metaKey || e.ctrlKey)) { e.preventDefault(); aller("reglages"); }
});

// Actions that ask --------------------------------------------------------------------------------------
function demanderAdb(suite) {
  question(tr("Outils Android"), tr("Il faut les outils Android de Google (10 Mo). Les télécharger ?"), [
    { titre: tr("Télécharger"), action: () => { E.apresAdb = suite; commande("adb_telecharger"); } },
    { titre: tr("Annuler"), annuler: true }]);
}

async function installer(apk, remplacer) {
  const fichier = apk || E.dernierAPK || E.reglages.output;
  const corps = { apk: fichier };
  if (remplacer !== undefined) corps.remplacer = remplacer;
  const [, code] = await api("installer", corps, ["question_remplacer", "adb_absent"]);
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
    { titre: tr("Désinstaller et installer"), action: () => commande("reinstaller", { apk, tache: garde ? "maj_telephone" : "installation" }) },
    { titre: tr("Annuler"), annuler: true }]);
}

async function mettreAJourTelephone(forcer = false) {
  const [details, code] = await api("maj_telephone", { forcer }, ["deja_a_jour", "jeu", "adb_absent"]);
  if (code === "deja_a_jour") {
    question(tr("Déjà à jour"), tr("Le jeu du téléphone est déjà à jour ({version}). Le réinstaller quand même ?", { version: details.version || "" }), [
      { titre: tr("Réinstaller"), action: () => mettreAJourTelephone(true) }, { titre: tr("Annuler"), annuler: true }]);
  } else if (code === "jeu") {
    toast(tr("Jeu officiel manquant"), details.erreur || "", "erreur");
    aller("android", "fabrication");
  } else if (code === "adb_absent") demanderAdb(() => mettreAJourTelephone(forcer));
}

async function lister() {
  const [reponse] = await api("sauvegardes");
  E.sauvegardes = reponse?.sauvegardes || [];
  rendre();
}

async function ouvrirSauvegarde(source, chemin, oublier = false) {
  const corps = { source, oublier };
  if (chemin) corps.chemin = chemin;
  const [reponse, code] = await api("ed_ouvrir", corps, ["changements", "adb_absent"]);
  if (code === "changements") {
    question(tr("Changements non enregistrés"), tr("Les oublier ?"), [
      { titre: tr("Oublier"), action: () => ouvrirSauvegarde(source, chemin, true) }, { titre: tr("Annuler"), annuler: true }]);
  } else if (code === "adb_absent") demanderAdb(() => ouvrirSauvegarde(source, chemin, oublier));
  else if (reponse) majEditeur(reponse);
}

function majEditeur(reponse) {
  E.editeur = reponse;
  E.edVersion++;
  // the lines stay shown while they are read again: the box just clicked stays, with its cursor
  E.edArbre = null;
  rendre();
}

async function editer(nom, corps) {
  const [reponse] = await api(nom, corps);
  if (reponse) majEditeur(reponse); else { E.edVersion++; E.edLignes = null; rendre(); }
}

// Navigation -----------------------------------------------------------------------------------------------
function aller(section, page = null) {
  const changeSection = section !== E.section;
  E.section = section;
  E.page = section === "android" ? page : null;
  rendreBarre();
  rendre(changeSection ? "entree" : page ? "entree-cote" : "entree");
  if (section !== "reglages" && E.reglages.derniere_page !== section) {
    E.reglages.derniere_page = section;
    api("reglages_ecrire", { derniere_page: section });
  }
}

// Rendering ------------------------------------------------------------------------------------------------
let cleVue = "";

function rendre(passage = "entree") {
  const contenu = $("#contenu");
  const cle = `${E.section}/${E.page || ""}`;
  const html = vue();
  const actuelle = $(".vue:not(.sortie)", contenu);
  if (cle === cleVue && actuelle) {
    garderEtat(actuelle, () => { actuelle.innerHTML = html; });
  } else {
    cleVue = cle;
    if (actuelle) {
      actuelle.classList.add("sortie");
      setTimeout(() => actuelle.remove(), 320 * duree());
    }
    const nouvelle = document.createElement("div");
    nouvelle.className = `vue ${passage}`;
    nouvelle.innerHTML = html;
    contenu.append(nouvelle);
    if (E.flip) voler(nouvelle);
    // once in, the view's entrance animations do not play again when it is drawn again
    setTimeout(() => nouvelle.classList.add("calme"), 900 * duree());
  }
  apresRendu();
}

/// What the player was doing stays: the field being typed in, where the lists were scrolled.
function garderEtat(vue, refaire) {
  const actif = document.activeElement;
  const focus = actif && vue.contains(actif) && actif.id ? { id: actif.id, debut: actif.selectionStart, fin: actif.selectionEnd,
    tape: actif.dataset.tape ? actif.value : null } : null;
  const defilements = [vue, ...$$("[data-garde]", vue)].map((el) => [el.dataset.garde || "", el.scrollTop]);
  // the banner's pictures and the sparks keep moving: the same elements stay
  const gardes = [".banniere .images", "canvas[data-particules]", ".qr svg"].map((choix) => [choix, $(choix, vue)]);
  refaire();
  for (const [choix, ancien] of gardes) {
    const nouveau = $(choix, vue);
    if (ancien && nouveau && (choix !== ".qr svg" || ancien.outerHTML === nouveau.outerHTML)) nouveau.replaceWith(ancien);
  }
  for (const [nom, haut] of defilements) {
    const el = nom ? $(`[data-garde="${nom}"]`, vue) : vue;
    if (el) el.scrollTop = haut;
  }
  if (focus) {
    const el = document.getElementById(focus.id);
    if (el) {
      if (focus.tape !== null) { el.value = focus.tape; el.dataset.tape = "1"; }  // what was being typed is not lost
      el.focus();
      try { el.setSelectionRange(focus.debut, focus.fin); } catch { /* not a text field */ }
    }
  }
}

/// A card's badge flies to the page's header (FLIP).
function voler(vue) {
  const depart = E.flip;
  E.flip = null;
  const arrivee = $(".entete .badge", vue);
  if (!arrivee || !duree()) return;
  const fin = arrivee.getBoundingClientRect();
  const dx = depart.left - fin.left, dy = depart.top - fin.top;
  arrivee.animate([{ transform: `translate(${dx}px, ${dy}px) scale(1.1)` }, { transform: "none" }],
    { duration: 600 * duree(), easing: "cubic-bezier(.2,.9,.25,1.12)" });
}

function vue() {
  if (E.section === "ios" || E.section === "ordinateur") return prochainement(E.section);
  if (E.section === "reglages") return reglages();
  return E.page ? pageOutil(E.page) : accueil();
}

function apresRendu() {
  for (const canvas of $$("canvas[data-particules]")) particules(canvas);
  const banniere = $(".banniere");
  if (banniere && !banniere.dataset.pret) {
    banniere.dataset.pret = 1;
    banniere.addEventListener("mousemove", (e) => {
      if (E.reglages.animations !== "completes") return;
      const r = banniere.getBoundingClientRect();
      banniere.style.setProperty("--px", ((e.clientX - r.left) / r.width - 0.5) * 2);
      banniere.style.setProperty("--py", ((e.clientY - r.top) / r.height - 0.5) * 2);
    });
  }
  for (const boite of $$(".journal[data-taches]")) if (!boite.dataset.bas) { boite.scrollTop = boite.scrollHeight; boite.dataset.bas = 1; }
  placerIndicateurs();
  if (E.section === "android" && E.page === "editeur" && E.editeur.ouvert) chargerEditeur();
  if (E.section === "android" && E.page === "fabrication" && E.libre === null) {
    E.libre = 0;
    api("espace", { chemin: E.reglages.output }).then(([r]) => { if (r) { E.libre = r.libre; rendre(); } });
  }
}

function placerIndicateurs() {
  const onglets = $(".onglets");
  if (onglets) {
    const choisi = $("button.choisi", onglets), indic = $(".indic", onglets);
    if (choisi && indic) { indic.style.width = `${choisi.offsetWidth}px`; indic.style.transform = `translateX(${choisi.offsetLeft}px)`; }
  }
  const sections = $(".sections");
  if (sections) {
    const choisie = $("button.choisie", sections), indic = $(".indic", sections);
    if (indic) {
      indic.style.opacity = choisie ? 1 : 0;
      if (choisie) indic.style.transform = `translateY(${choisie.offsetTop}px)`;
    }
  }
}

// The sidebar ----------------------------------------------------------------------------------------------
function rendreBarre() {
  const t = telephone();
  const detailAndroid = E.tache ? tr("En cours : {t}", { t: nomTache(E.tache) }) : t ? t.modele : tr("Disponible");
  const tuile = (section, icone, titre, detail, bientot) => `
    <button class="tuile ${E.section === section ? "choisie" : ""}" data-action="section" data-section="${section}">
      <span class="ic">${SVG[icone]}</span>
      <span><div class="t jeu">${h(titre)}</div>${detail ? `<div class="d ${bientot ? "prochain" : ""}">${h(detail)}</div>` : ""}</span>
      ${bientot ? SVG.cadenas.replace("<svg", '<svg class="cadenas"') : ""}
    </button>`;
  $("#tuiles").innerHTML = tuile("android", "android", "Android", detailAndroid, false)
    + tuile("ios", "apple", "iOS", tr("Prochainement"), true)
    + tuile("ordinateur", "ordinateur", tr("Ordinateur"), tr("Prochainement"), true);
  $("#tuiles-bas").innerHTML = tuile("reglages", "reglages", tr("Réglages"), "", false);
  $("#version").innerHTML = `${majDisponible() ? '<span class="point"></span>' : ""}${h(tr("Outil {v} · Jeu {g}", { v: E.version, g: E.jeu }))}`;
  let surligne = $("#surligne");
  if (!surligne) {
    surligne = document.createElement("div");
    surligne.id = "surligne";
    surligne.className = "surligne";
    $("#barre").append(surligne);
  }
  const choisie = $(`#barre .tuile.choisie`);
  if (choisie) {
    const barre = $("#barre").getBoundingClientRect(), r = choisie.getBoundingClientRect();
    surligne.style.transform = `translateY(${r.top - barre.top}px)`;
    surligne.style.left = `${r.left - barre.left}px`;
    surligne.style.width = `${r.width}px`;
  }
}

function traduireCadre() {
  for (const el of $$("[data-tr]")) el.textContent = tr(el.dataset.tr);
}

// Android: home ---------------------------------------------------------------------------------------
function accueil() {
  const cartes = Object.keys(PAGES).map((page, i) => `
    <button class="carte-outil" style="animation-delay:${(0.12 + i * 0.07) * duree()}s" data-action="page" data-page="${page}">
      <div class="img"><img src="/ressources/lanceur/${PAGES[page].image}.png" alt=""></div>
      <span class="badge">${SVG[PAGES[page].icone]}</span>
      <div class="corps"><h3 class="jeu">${h(titrePage(page))}</h3><p>${h(textePage(page))}</p>
      ${PAGES[page].taches.includes(E.tache) ? `<span class="puce" style="--c:var(--a1)">${SVG.sablier.replace("<svg", '<svg width="10"')} ${h(tr("En cours"))}</span>` : ""}</div>
    </button>`).join("");
  return `${banniere()}<div class="section"><div class="titre-section">${h(tr("OUTILS"))}</div><div class="grille">${cartes}</div></div>`;
}

function banniere() {
  const images = BANNIERE.map((nom, i) => `<img src="/ressources/lanceur/${nom}.png" alt="" class="${i === rangBanniere ? "vue-img" : ""}">`).join("");
  return `<div class="banniere"><div class="images">${images}</div><canvas data-particules="28"></canvas>
    <div class="texte">
      <div class="puces"><span class="puce" style="--c:var(--vert)">${SVG.check.replace("<svg", '<svg width="10" fill="currentColor"')} ANDROID</span>
      <span class="puce" style="--c:var(--a1)">${h(tr("Jeu {g}", { g: E.jeu }))}</span></div>
      <h1 class="jeu">${h(tr("Ranger Rumble hors ligne"))}</h1>
      <p>${h(tr("Le jeu complet, sans serveur. La progression iPhone continue sur Android."))}</p>
      <div class="actions">${boutonPrincipal()}${etatTelephone()}</div>
    </div></div>`;
}

let rangBanniere = 0;
setInterval(() => {
  const banniere = $(".banniere .images");
  if (!banniere || document.hidden || E.reglages.animations === "aucune") return;
  const images = $$("img", banniere);
  images[rangBanniere].classList.remove("vue-img");
  rangBanniere = (rangBanniere + 1) % images.length;
  images[rangBanniere].classList.add("vue-img");
}, 7000);

function boutonPrincipal() {
  const t = telephone();
  if (E.tache) {
    const page = E.tache === "copie" ? "copie" : E.tache.startsWith("maj") ? "majs" : "fabrication";
    return `<button class="principal grand jeu" data-action="page" data-page="${page}">${SVG.sablier} ${h(tr("En cours : {t}", { t: nomTache(E.tache) }))}</button>`;
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
  return `<button class="aide-i" data-action="aide-telephone" title="${h(tr("Faire reconnaître le téléphone"))}">i</button>`;
}

// Android: tool pages -------------------------------------------------------------------------------
function pageOutil(page) {
  const corps = { copie: pageCopie, fabrication: pageFabrication, editeur: pageEditeur, majs: pageMajs }[page]();
  return `<div class="entete"><img class="fond" src="/ressources/lanceur/${PAGES[page].image}.png" alt="">
    <div class="ligne"><button class="retour" data-action="retour">${SVG.retour}</button>
    <span class="badge">${SVG[PAGES[page].icone]}</span>
    <div><h2 class="jeu">${h(titrePage(page))}</h2><p>${h(textePage(page))}</p></div></div></div>${corps}`;
}

function journal(taches) {
  const lignes = E.journal.filter((l) => taches.includes(l.tache)).slice(-400).map((l) => l.texte).join("\n");
  return `<div class="journal" data-taches="${taches.join(",")}" data-garde="journal-${taches[0]}">${h(lignes)}</div>`;
}

function progression(taches, etapes = []) {
  if (!E.barre || !taches.includes(E.tache)) return "";
  const chips = etapes.map((nom, i) => `<span data-etape="${i + 1}">${h(nom)}</span>`).join("");
  return `<div class="carte progression apparait"><div class="tete jeu"><span>${h(E.barre.texte)}</span><b>0 %</b></div>
    <div class="piste"><div class="plein"></div></div>${chips ? `<div class="etapes">${chips}</div>` : ""}</div>`;
}

function animerBarre() {
  const carte = $(".progression");
  if (carte && E.barre) {
    const b = E.barre;
    let valeur = b.debut;
    if (b.secondes > 0 && b.but > b.debut) valeur = b.debut + (b.but - b.debut) * (1 - Math.exp(-(performance.now() - b.depuis) / 1000 / b.secondes));
    valeur = Math.max(0, Math.min(100, valeur));
    $(".plein", carte).style.width = `${valeur}%`;
    $(".tete b", carte).textContent = `${Math.floor(valeur)} %`;
    $(".tete span", carte).textContent = b.texte;
    for (const chip of $$("[data-etape]", carte)) {
      const n = Number(chip.dataset.etape);
      chip.className = (b.etape || 0) > n || valeur >= 100 ? "faite" : (b.etape || 0) === n ? "encours" : "";
    }
  }
  requestAnimationFrame(animerBarre);
}

function pageCopie() {
  const etats = ["attente", "iphone", "jeu", "sauvegarde", "fini"];
  const titres = { attente: tr("En attente"), iphone: "iPhone", jeu: tr("Jeu"), sauvegarde: tr("Sauvegarde"), fini: tr("Copiée") };
  const rang = E.copieFinie ? 4 : etats.indexOf(E.copieEtat) >= 0 ? etats.indexOf(E.copieEtat) : E.copieEtat === "certificat" ? 2 : -1;
  const frise = etats.map((nom, i) => {
    const jalon = `<div class="jalon ${rang >= i ? "atteint" : ""} ${rang === i && E.tache === "copie" && !E.copieFinie ? "actuel" : ""}">
      <div class="rond">${rang >= i ? SVG.check : ""}</div>${h(titres[nom])}</div>`;
    return i < etats.length - 1 ? jalon + `<div class="trait" style="--plein:${rang > i ? 1 : 0}"></div>` : jalon;
  }).join("");
  const etape = (n, texte) => `<div class="etape"><span class="num">${n}</span><span>${h(texte)}</span></div>`;
  const marche = E.tache === "copie";
  return `<div class="colonne">
    <div class="rangee">
      <div class="carte"><h4 class="jeu">${h(tr("Sur l'iPhone"))}</h4>
        ${etape(1, tr("Mettre l'iPhone sur le même Wi-Fi que cet ordinateur."))}
        ${etape(2, tr("Scanner le QR code avec l'appareil photo, puis télécharger le profil RatchetRR."))}
        ${etape(3, tr("Réglages > Général > tout en bas, « VPN et gestion de l'appareil » > RatchetRR : valider le profil (Installer)."))}
        ${etape(4, tr("Réglages > Général > Informations : tout en bas, « Réglages des certificats » > activer RatchetRR."))}
        ${etape(5, tr("Ouvrir Ranger Rumble et attendre l'écran d'accueil."))}
        <div class="boutons">
          ${marche ? `<button class="principal jeu" data-action="copie-arreter">${SVG.stop} ${h(tr("Arrêter"))}</button>`
            : `<button class="principal jeu" data-action="copie-demarrer" ${E.tache ? "disabled" : ""}>${SVG.play} ${h(tr("Démarrer"))}</button>`}
          <button class="secondaire" data-action="ouvrir" data-chemin="${h(E.copies)}">${h(tr("Dossier des copies"))}</button>
        </div></div>
      <div class="carte" style="flex:none;width:260px;display:flex;flex-direction:column;align-items:center">
        <div class="qr">${E.qrSvg || SVG.qr.replace("<svg", '<svg class="vide"')}</div>
        <div class="adresse">${h(E.qr || tr("Le QR code apparaît au démarrage."))}</div></div>
    </div>
    <div class="carte"><h4 class="jeu" style="font-size:16px">${h(tr("Progression"))}</h4><div class="frise">${frise}</div>
      ${E.copieEtat === "certificat" ? `<div class="message ko">${SVG.alerte.replace("<svg", '<svg width="16" fill="currentColor"')} ${h(tr("Le jeu refuse le certificat : il faut refaire l'étape 4."))}</div>` : ""}
      ${E.copieFinie ? `<div class="message ok">${SVG.succes.replace("<svg", '<svg width="16" fill="currentColor"')} ${h(tr("Sauvegarde copiée ! Il faut ensuite supprimer le profil RatchetRR de l'iPhone."))}
        <span style="flex:1"></span><button class="principal jeu" data-action="page" data-page="fabrication">${h(tr("Fabriquer le jeu"))}</button></div>` : ""}
    </div>
    ${journal(["copie"])}</div>`;
}

function champ(cle, titre, icone, vide, action) {
  const valeur = E.reglages[cle] || "";
  return `<div class="champ">${SVG[icone]}<div class="quoi"><small>${h(titre)}</small>
    <span class="${valeur ? "" : "vide"}" title="${h(valeur)}">${valeur ? `<span class="ok" style="display:inline">✓</span>${h(nomFichier(valeur))}` : h(vide)}</span></div>
    ${cle === "artworks" && valeur ? `<button class="secondaire" data-action="effacer" data-cle="artworks">${h(tr("Retirer"))}</button>` : ""}
    <button class="secondaire" data-action="${action}" data-cle="${cle}">${h(tr("Choisir…"))}</button></div>`;
}

function pageFabrication() {
  const options = E.sauvegardes.map((s) => `<option value="${h(s.chemin)}" ${s.chemin === E.reglages.sauvegarde ? "selected" : ""}>${h(s.libelle)}</option>`).join("");
  const nouvelle = !!E.reglages.nouvelle_partie;
  const etapes = [tr("Lecture"), tr("Modifications"), tr("Préparation"), tr("Sauvegarde"), tr("Signature"), tr("Fini")];
  const libre = E.libre ? `<div class="libre ${E.libre < 5e9 ? "peu" : ""}">${h(tr("Espace libre : {n} Go (il faut 5 Go)", { n: (E.libre / 1e9).toFixed(1) }))}</div>` : "";
  const t = telephone();
  return `<div class="colonne">
    <div class="carte" style="padding:8px 22px">
      ${champ("official", tr("Jeu officiel 1.10.4"), "doc", tr("Le fichier .xapk, .apkm ou .apk complet"), "choisir-jeu")}
      <div class="champ">${SVG.personne}<div class="quoi"><small>${h(tr("Progression"))}</small>
        <div class="boutons" style="margin-top:6px">
          <select class="choix" id="choix-sauvegarde" data-change="sauvegarde" ${nouvelle ? "disabled" : ""}>
            <option value="">${h(tr("Choisir une sauvegarde"))}</option>${options}</select>
          <button class="secondaire" data-action="autre-sauvegarde">${h(tr("Autre fichier…"))}</button>
          <label class="interrupteur"><input type="checkbox" data-change="nouvelle" ${nouvelle ? "checked" : ""}><i></i></label>
          <span style="font-size:13px">${h(tr("Nouvelle partie"))}</span>
        </div></div></div>
      ${champ("artworks", tr("Images de la galerie (facultatif)"), "image", tr("Un dossier d'images pour l'artbook du jeu"), "choisir-dossier")}
      ${champ("output", tr("APK à créer"), "sortie", "RangerRumble_hors_ligne.apk", "choisir-sortie")}
      ${libre}
    </div>
    <div class="boutons">
      <button class="principal grand jeu" data-action="fabriquer" ${E.tache ? "disabled" : ""}>${SVG.marteau} ${h(tr("Fabriquer l'APK"))}</button>
      <button class="secondaire" data-action="installer" ${E.tache ? "disabled" : ""}>${SVG.cable} ${h(tr("Installer sur le téléphone"))}</button>
      <span style="flex:1"></span>
      <span style="display:flex;align-items:center;gap:8px;font-size:12.5px;color:var(--doux)"><span class="dot" style="width:8px;height:8px;border-radius:50%;background:${t ? "var(--vert)" : "var(--pale)"}"></span>${h(t ? t.modele : tr("Aucun téléphone branché"))}${t ? "" : boutonAideTelephone()}</span>
    </div>
    ${progression(["fabrication", "installation"], E.tache === "fabrication" ? etapes : [])}
    ${journal(["fabrication", "installation", "adb"])}</div>`;
}

function pageMajs() {
  const t = telephone();
  const etatOutil = { nouvelle: tr("La version {v} est disponible.", { v: E.maj.version || "" }), a_jour: tr("À jour."),
    impossible: tr("Vérification impossible (pas de connexion ?).") }[E.maj.etat] || tr("Pas encore vérifié.");
  let etatTel = tr("Aucun téléphone branché.");
  if (t) etatTel = !t.jeu ? tr("{m} : pas de Ranger Rumble.", { m: t.modele }) : t.origine === "officiel" ? tr("{m} : jeu officiel.", { m: t.modele })
    : tr("{m} : jeu hors ligne {v}.", { m: t.modele, v: t.version || "?" });
  return `<div class="colonne"><div class="rangee">
    <div class="carte"><h4 class="jeu" style="display:flex;gap:8px;align-items:center">${h(tr("L'outil"))}<span style="flex:1"></span><span class="puce" style="--c:var(--a1)">${h(E.version)}</span></h4>
      <p style="color:var(--doux);margin:0 0 12px">${h(etatOutil)}</p>
      ${majDisponible() && E.maj.notes ? `<div class="journal" style="height:auto;max-height:140px;margin-bottom:12px">${h(E.maj.notes)}</div>` : ""}
      <div class="boutons"><button class="secondaire" data-action="maj-verifier">${h(tr("Vérifier maintenant"))}</button>
      ${majDisponible() ? `<button class="principal jeu" data-action="maj-outil" ${E.tache ? "disabled" : ""}>${h(tr("Installer la version {v}", { v: E.maj.version }))}</button>` : ""}</div></div>
    <div class="carte"><h4 class="jeu" style="display:flex;gap:8px;align-items:center">${h(tr("Le jeu du téléphone"))}<span style="flex:1"></span><span class="puce" style="--c:var(--a1)">${h(E.jeu)}</span></h4>
      <p style="color:var(--doux);margin:0 0 4px">${h(etatTel)}</p><p style="color:var(--pale);font-size:12px;margin:0 0 12px">${h(tr("La progression est gardée."))}</p>
      <button class="principal jeu" data-action="maj-telephone" ${E.tache || !t ? "disabled" : ""}>${SVG.sortie} ${h(tr("Mettre à jour le téléphone"))}</button></div>
    </div>${progression(["maj_telephone", "maj_outil"])}${journal(["maj_telephone", "maj_outil", "installation"])}</div>`;
}

// The editor ----------------------------------------------------------------------------------------------
const ONGLETS = [["profil", "Profil", "personne"], ["heros", "Héros", "personne"], ["armes", "Armes", "marteau"],
  ["costumes", "Costumes", "palette"], ["modes", "Modes", "liste"], ["tout", "Tout", "liste"]];

function pageEditeur() {
  const ouvrir = `<div class="boutons"><span style="font-weight:700;color:var(--doux)">${h(tr("Ouvrir :"))}</span>
    <button class="secondaire" data-action="ed-ouvrir" data-source="telephone">${SVG.cable} ${h(tr("Le téléphone"))}</button>
    <button class="secondaire" data-action="ed-ouvrir" data-source="fichier">${SVG.doc} ${h(tr("Un fichier…"))}</button>
    <button class="secondaire" data-action="ed-ouvrir" data-source="copie">${SVG.dossier} ${h(tr("Une copie…"))}</button>
    <button class="secondaire" data-action="ed-ouvrir" data-source="nouvelle">${SVG.etoile} ${h(tr("Partie vierge"))}</button></div>`;
  if (!E.editeur.ouvert) {
    return `<div class="editeur">${ouvrir}<div class="vide-editeur">${SVG.sortie}<h3 class="jeu" style="margin:0">${h(tr("Aucune sauvegarde ouverte"))}</h3>
      <span>${h(tr("Il faut en ouvrir une, en haut."))}</span></div></div>`;
  }
  const resume = E.editeur.resume || {};
  const monnaies = (resume.currencies || []).map((m) => `<span class="monnaie" title="${h(m.name)}">${m.icon ? `<img src="/ressources/icones/${m.icon}.png" alt="">` : ""}${chiffre(m.value)}</span>`).join("");
  const comptes = (resume.counts || []).map((c) => `<span class="compte"><b class="jeu">${c.total ? `${c.owned}/${c.total}` : c.owned}</b><small>${h(c.label)}</small></span>`).join("");
  const changements = (E.editeur.changements || []).length;
  const onglets = ONGLETS.map(([cle, titre]) => `<button class="${E.onglet === cle ? "choisi" : ""}" data-action="onglet" data-onglet="${cle}">${h(tr(titre))}</button>`).join("");
  return `<div class="editeur">${ouvrir}
    <div class="carte resume"><div><div class="pseudo jeu">${h(resume.nickname || tr("Sans nom"))}</div><div class="source">${h(E.editeur.source)}</div></div>
      ${monnaies}<span style="flex:1"></span>${comptes}
      ${changements ? `<span class="puce" style="--c:var(--orange)">${h(tr("{n} modifiée(s)", { n: changements }))}</span>` : ""}</div>
    <div class="onglets"><span class="indic"></span>${onglets}</div>
    ${E.onglet === "tout" ? arbre() : tableau()}
    <div class="boutons">
      <button class="principal jeu" data-action="ed-envoyer">${SVG.avion} ${h(tr("Envoyer au téléphone"))}</button>
      <button class="secondaire" data-action="ed-enregistrer">${SVG.disquette} ${h(tr("Enregistrer sous…"))}</button>
      <button class="secondaire" data-action="ed-pour-apk">${SVG.boite} ${h(tr("Utiliser pour l'APK"))}</button>
      <span style="flex:1"></span>
      <button class="secondaire" data-action="ed-annuler" ${changements ? "" : "disabled"}>${SVG.annuler} ${h(tr("Annuler les changements"))}</button></div></div>`;
}

let chargement = "";
async function chargerEditeur() {
  const cle = `${E.onglet}-${E.edVersion}`;
  if (chargement === cle) return;
  if (E.onglet === "tout") {
    if (E.edArbre) return;
    chargement = cle;
    const [r] = await api("ed_arbre");
    E.edArbre = { racines: r?.noeuds || [], ouverts: {} };
  } else {
    if (E.edLignes && E.edLignes.cle === cle) return;
    chargement = cle;
    const [r] = await api("ed_lignes", { onglet: E.onglet });
    E.edLignes = { cle, colonnes: r?.colonnes || [], lignes: r?.lignes || [] };
  }
  chargement = "";
  rendre();
}

function tableau() {
  const donnees = E.edLignes;
  if (!donnees || !donnees.cle.startsWith(`${E.onglet}-`)) return `<div class="carte table"></div>`;
  const colonnes = donnees.colonnes;
  // a name keeps a sensible width; the space a large window adds goes to the values
  const gabarit = `40px ${colonnes.map((c) => (["name", "hero"].includes(c.cle) ? "minmax(140px, 260px)" : "minmax(64px, 1fr)")).join(" ")}`;
  const tete = `<div class="tete" style="grid-template-columns:${gabarit}"><span></span>${colonnes.map((c) => `<span class="${c.type ? "c" : ""}">${h(c.titre)}</span>`).join("")}</div>`;
  const lignes = donnees.lignes.map((l, i) => {
    const cellules = colonnes.map((c) => {
      const v = l.valeurs[c.cle];
      const modifiable = l.modifiable[c.cle];
      if (c.type === "bool") return `<span class="c"><label class="interrupteur" style="display:inline-block"><input type="checkbox" ${v ? "checked" : ""} ${modifiable ? "" : "disabled"} data-change="ed-bool" data-ligne="${i}" data-cle="${c.cle}"><i></i></label></span>`;
      if (c.type === "int" && modifiable) return `<span class="c"><input class="valeur" id="v-${i}-${c.cle}" value="${h(v ?? "")}" data-change="ed-valeur" data-ligne="${i}" data-cle="${c.cle}" data-texte="${typeof v === "string" ? 1 : ""}" style="${typeof v === "string" ? "width:150px" : ""}"></span>`;
      return `<span class="${c.type ? "c" : "nom"}">${h(v === null || v === undefined ? "—" : v)}</span>`;
    }).join("");
    return `<div class="ligne ${l.possede === true ? "possede" : l.possede === false ? "absent" : ""}" style="grid-template-columns:${gabarit}">${l.icone ? `<img src="/ressources/icones/${l.icone}.png" alt="">` : "<span></span>"}${cellules}</div>`;
  }).join("");
  const actions = { heros: [["tous_heros", tr("Débloquer tous les héros")], ["max_heros", tr("Niveau max pour tous")]],
    armes: [["toutes_armes", tr("Débloquer toutes les armes")], ["max_armes", tr("Niveau max pour toutes")]],
    costumes: [["tous_costumes", tr("Donner tous les costumes")]] }[E.onglet] || [];
  const boutons = actions.length ? `<div class="boutons">${actions.map(([a, t]) => `<button class="secondaire" data-action="ed-action" data-quoi="${a}">${h(t)}</button>`).join("")}</div>` : "";
  return `${boutons}<div class="carte table">${tete}<div class="lignes" data-garde="lignes">${lignes}</div></div>`;
}

function arbre() {
  if (!E.edArbre) return `<div class="carte table"></div>`;
  const noeud = (n, cle) => {
    const ouvert = E.edArbre.ouverts[cle];
    const enfants = ouvert && Array.isArray(ouvert) ? `<div class="enfants">${ouvert.map((e, i) => noeud(e, `${cle}/${i}`)).join("")}</div>` : "";
    return `<div class="noeud ${ouvert ? "ouvert" : ""}"><div class="tete-noeud" data-action="noeud" data-cle="${h(cle)}">
      <span class="fleche">${n.children ? "▶" : ""}</span><b>${h(n.label)}</b><span class="val ${n.modifiable ? "modif" : ""}">${h(n.text)}</span>
      <span class="type">${h(n.kind)}</span></div>${enfants}</div>`;
  };
  return `<div style="font-size:12px;color:var(--pale)">${h(tr("Toute la sauvegarde. Avec précaution."))}</div>
    <div class="carte table"><div class="arbre" data-garde="arbre">${E.edArbre.racines.map((n, i) => noeud(n, String(i))).join("")}</div></div>`;
}

function noeudDe(cle) {
  const morceaux = cle.split("/").map(Number);
  let liste = E.edArbre.racines, n = null;
  morceaux.forEach((i, k) => {
    n = liste[i];
    if (k < morceaux.length - 1) liste = E.edArbre.ouverts[morceaux.slice(0, k + 1).join("/")];
  });
  return n;
}

// Coming soon ---------------------------------------------------------------------------------------------
function prochainement(plateforme) {
  const ios = plateforme === "ios";
  return `<div class="bientot"><img class="flou" src="/ressources/lanceur/${ios ? "fond_6" : "fond_3"}.png" alt="">
    <canvas data-particules="55"></canvas>
    <div class="milieu"><div class="medaillon">${ios ? SVG.apple : SVG.ordinateur}<span class="badge verrou">${SVG.cadenas}</span></div>
      <div class="sous jeu">${ios ? "iOS" : h(tr("Ordinateur"))}</div>
      <h1 class="brillant jeu">${h(tr("Prochainement"))}</h1>
      <div style="font-size:15px;color:var(--doux)">${h(ios ? tr("Le jeu hors ligne sur iPhone et iPad est en préparation.") : tr("Le jeu hors ligne sur ordinateur est en préparation."))}</div>
      <button class="puce" style="--c:var(--a1);margin-top:6px;cursor:pointer" data-action="section" data-section="android">← ${h(tr("En attendant : la version Android"))}</button>
    </div></div>`;
}

// Particles: sparks drifting up, paused when the window is hidden ---------------------------------------
function particules(canvas) {
  if (canvas.dataset.vivant) return;
  canvas.dataset.vivant = 1;
  const nombre = Number(canvas.dataset.particules) || 30;
  const grains = Array.from({ length: nombre }, () => ({ x: Math.random(), v: 0.015 + Math.random() * 0.035, t: 1.5 + Math.random() * 3,
    p: Math.random(), d: (Math.random() - 0.5) * 0.08 }));
  const ctx = canvas.getContext("2d");
  const dessiner = (temps) => {
    if (!canvas.isConnected) return;
    if (E.reglages.animations !== "completes" || document.hidden) { ctx.clearRect(0, 0, canvas.width, canvas.height); setTimeout(() => requestAnimationFrame(dessiner), 500); return; }
    const echelle = devicePixelRatio || 1;
    const l = canvas.clientWidth, ht = canvas.clientHeight;
    if (canvas.width !== l * echelle) { canvas.width = l * echelle; canvas.height = ht * echelle; }
    ctx.setTransform(echelle, 0, 0, echelle, 0, 0);
    ctx.clearRect(0, 0, l, ht);
    const couleur = getComputedStyle(document.documentElement).getPropertyValue("--a1").trim() || "#f7b731";
    const s = temps / 1000;
    for (const g of grains) {
      const avance = (g.p + s * g.v) % 1;
      const x = (g.x + Math.sin(s * 0.3 + g.p * 6) * g.d) * l, y = (1 - avance) * (ht + 40) - 20;
      ctx.globalAlpha = Math.sin(avance * Math.PI) * 0.8;
      ctx.shadowBlur = g.t * 4;
      ctx.shadowColor = couleur;
      ctx.fillStyle = couleur;
      ctx.beginPath();
      ctx.arc(x, y, g.t / 2, 0, Math.PI * 2);
      ctx.fill();
    }
    requestAnimationFrame(dessiner);
  };
  requestAnimationFrame(dessiner);
}

// Settings ------------------------------------------------------------------------------------------------
const SECTIONS = [["general", "Général", "reglages"], ["apparence", "Apparence", "palette"], ["jeu", "Jeu et fichiers", "dossier"],
  ["telephone", "Téléphone", "telephone"], ["copie", "Copie iPhone", "copie"], ["cle", "Clé de signature", "cle"],
  ["majs", "Mises à jour", "synchro"], ["composants", "Composants", "boite"], ["avance", "Avancé", "outil"], ["apropos", "À propos", "info"]];

function interrupteur(cle) {
  return `<label class="interrupteur"><input type="checkbox" data-change="drapeau" data-cle="${cle}" ${E.reglages[cle] ? "checked" : ""}><i></i></label>`;
}

function segments(cle, choix) {
  return `<div class="segments">${choix.map(([v, t]) => `<button class="${E.reglages[cle] === v ? "choisi" : ""}" data-action="regler" data-cle="${cle}" data-valeur="${v}">${h(t)}</button>`).join("")}</div>`;
}

const bouton = (action, texte, extra = "", desactive = false) => `<button class="secondaire" data-action="${action}" ${extra} ${desactive ? "disabled" : ""}>${h(texte)}</button>`;
const info = (nom, cle) => { const v = E.infos[nom]?.[cle]; return v === null || v === undefined ? "—" : String(v); };

function listeReglages() {
  const r = [];
  const ajouter = (section, titre, detail, vue) => r.push({ section, titre, detail, vue });
  const chemin = (cle, vide) => E.reglages[cle] || vide;
  const choisirChemin = (cle, dossier, effacer) => `<div class="boutons">${bouton(dossier ? "choisir-dossier" : "choisir-jeu", tr("Choisir…"), `data-cle="${cle}"`)}
    ${effacer && E.reglages[cle] ? bouton("effacer", tr("Retirer"), `data-cle="${cle}"`) : ""}</div>`;
  ajouter("general", tr("Langue"), tr("Les textes de l'outil."), `<select class="choix" data-change="langue">${E.langues.map(([c, n]) => `<option value="${c}" ${c === E.langue ? "selected" : ""}>${h(n)}</option>`).join("")}</select>`);
  ajouter("general", tr("Chercher les mises à jour au démarrage"), tr("Une question posée à GitHub, rien d'autre."), interrupteur("maj_demarrage"));
  ajouter("general", tr("Page d'ouverture"), "", segments("page_depart", [["accueil", tr("Android")], ["derniere", tr("La dernière ouverte")]]));
  ajouter("general", tr("Son à la fin d'une tâche"), tr("Fabrication, installation, mise à jour."), interrupteur("son_fin"));
  ajouter("general", tr("Empêcher la veille pendant une tâche"), tr("L'ordinateur reste éveillé pendant une fabrication ou une installation."), interrupteur("anti_veille"));
  ajouter("apparence", tr("Thème"), "", segments("theme", [["auto", tr("Automatique")], ["sombre", tr("Sombre")], ["clair", tr("Clair")]]));
  ajouter("apparence", tr("Animations"), tr("Le réglage « Réduire les animations » du système est suivi aussi."), segments("animations", [["completes", tr("Complètes")], ["reduites", tr("Réduites")], ["aucune", tr("Aucune")]]));
  const accents = [["or", "#f7b731", "#ff7a2f", "Or"], ["bleu", "#4da3ff", "#7b5cff", "Bleu"], ["vert", "#3ddc84", "#1fb5a8", "Vert"], ["violet", "#a77bff", "#ff5cc8", "Violet"]];
  ajouter("apparence", tr("Couleur"), "", `<div class="pastilles">${accents.map(([v, a, b, n]) => `<button title="${h(tr(n))}" class="${(E.reglages.accent || "or") === v ? "choisi" : ""}" style="--c:${a};background:linear-gradient(135deg,${a},${b})" data-action="regler" data-cle="accent" data-valeur="${v}"></button>`).join("")}</div>`);
  ajouter("jeu", tr("Jeu officiel 1.10.4"), chemin("official", tr("Pas encore choisi")), choisirChemin("official", false));
  ajouter("jeu", tr("Dossier des sauvegardes"), chemin("dossier_sauvegardes", E.copies), choisirChemin("dossier_sauvegardes", true, true));
  ajouter("jeu", tr("APK à créer"), chemin("output", ""), `<div class="boutons">${bouton("choisir-sortie", tr("Choisir…"), 'data-cle="output"')}${bouton("montrer", tr("Montrer"), `data-chemin="${h(E.reglages.output)}"`)}</div>`);
  ajouter("jeu", tr("Images de la galerie"), chemin("artworks", tr("Aucune (facultatif)")), choisirChemin("artworks", true, true));
  ajouter("jeu", tr("Dossier de travail"), `${chemin("dossier_travail", tr("À côté de l'APK"))} · ${tr("5 Go libres pendant la fabrication")}`, choisirChemin("dossier_travail", true, true));
  ajouter("telephone", tr("Outils Android (adb)"), E.reglages.adb || (E.adb ? tr("Automatique : {p}", { p: E.adb }) : tr("Pas encore installés")),
    `<div class="boutons">${bouton("choisir-adb", tr("Choisir…"))}${E.reglages.adb ? bouton("effacer", tr("Automatique"), 'data-cle="adb"') : ""}${bouton("adb", E.adb ? tr("Réinstaller") : tr("Télécharger"), "", !!E.tache)}</div>`);
  ajouter("telephone", tr("Téléphones branchés"), tr("Débogage USB activé, USB en « Transfert de fichiers »."), bouton("actualiser", tr("Actualiser")));
  for (const t of E.telephones) {
    const origine = !t.jeu ? (t.etat === "device" ? tr("pas de Ranger Rumble") : "") : t.origine === "officiel" ? tr("jeu officiel")
      : t.origine === "cet_ordinateur" ? tr("jeu hors ligne {v}, installé par cet ordinateur", { v: t.version || "?" }) : tr("jeu hors ligne {v}, installé par un autre ordinateur", { v: t.version || "?" });
    ajouter("telephone", t.modele, [t.serie, origine].filter(Boolean).join(" · "),
      `<span class="puce" style="--c:${t.etat === "device" ? "var(--vert)" : "var(--orange)"}">${h(t.etat === "device" ? tr("Prêt") : t.etat === "unauthorized" ? tr("À autoriser") : t.etat)}</span>`);
  }
  const certificat = E.infos.certificat_info?.existe;
  ajouter("copie", tr("Certificat RatchetRR"), certificat ? tr("Créé le {d}", { d: info("certificat_info", "date") }) : tr("Créé à la première copie"),
    `<div class="boutons">${bouton("ouvrir", tr("Montrer"), `data-chemin="${h(info("certificat_info", "dossier"))}"`, !certificat)}${bouton("certificat-recreer", tr("Recréer"), "", E.tache === "copie")}</div>`);
  ajouter("copie", tr("Dossier des copies"), E.copies, bouton("ouvrir", tr("Ouvrir"), `data-chemin="${h(E.copies)}"`));
  const cle = E.infos.cle_info?.existe;
  ajouter("cle", tr("Clé de cet ordinateur"), cle ? tr("Signature {s} · créée le {d}", { s: info("cle_info", "signature"), d: info("cle_info", "date") }) : tr("Créée à la première fabrication"),
    bouton("cle-exporter", tr("Exporter…"), "", !cle));
  ajouter("cle", tr("Importer une clé"), tr("Pour mettre à jour, depuis cet ordinateur, un jeu installé par un autre ordinateur. La clé actuelle est gardée à côté."), bouton("cle-importer", tr("Importer…")));
  ajouter("majs", tr("Versions"), tr("Outil {v} · Jeu {g}", { v: E.version, g: E.jeu }),
    `<div class="boutons">${bouton("maj-verifier", tr("Vérifier maintenant"))}${majDisponible() ? `<button class="principal jeu" data-action="maj-outil">${h(tr("Installer la version {v}", { v: E.maj.version }))}</button>` : ""}</div>`);
  const composants = E.infos.composants || {};
  ajouter("composants", "Python", `${info("composants", "python")} · ${info("composants", "chemin")}`,
    `<span class="puce" style="--c:${composants.ok === false ? "var(--orange)" : "var(--vert)"}">${h(composants.ok === false ? tr("À réparer") : tr("Prêt"))}</span>`);
  ajouter("composants", tr("Réparer les composants"), tr("Ils sont installés de nouveau au prochain démarrage."), bouton("reparer", tr("Réparer"), "", !!E.tache));
  if (composants.pip_log) ajouter("composants", tr("Journal d'installation"), composants.pip_log, bouton("ouvrir", tr("Ouvrir"), `data-chemin="${h(composants.pip_log)}"`));
  ajouter("avance", tr("Journal de la session"), tr("Tout ce que l'outil a écrit depuis son ouverture."), `<div class="boutons">${bouton("journal", tr("Voir"))}${bouton("journal-copier", tr("Copier"))}</div>`);
  if (composants.erreur_log) ajouter("avance", tr("Dernière erreur au démarrage"), composants.erreur_log, bouton("ouvrir", tr("Ouvrir"), `data-chemin="${h(composants.erreur_log)}"`));
  ajouter("avance", tr("Dossier de l'outil"), E.base, bouton("ouvrir", tr("Ouvrir"), `data-chemin="${h(E.base)}"`));
  const taille = E.infos.temporaires?.taille || 0;
  ajouter("avance", tr("Fichiers temporaires"), taille ? tr("{n} Mo laissés par une fabrication arrêtée", { n: Math.round(taille / 1e6) }) : tr("Rien à nettoyer"), bouton("nettoyer", tr("Nettoyer"), "", !taille || !!E.tache));
  ajouter("avance", tr("Réinitialiser les réglages"), tr("L'ancien fichier est gardé."), bouton("reinitialiser", tr("Réinitialiser")));
  ajouter("apropos", tr("Ranger Rumble hors ligne"), tr("Projet de fans, sans lien avec Sony Interactive Entertainment, Insomniac Games ou Oh BiBi."), `<img src="/ressources/lanceur/logo_petit.png" width="90" alt="">`);
  ajouter("apropos", tr("Versions"), tr("Outil {v} · Jeu {g}", { v: E.version, g: E.jeu }), "");
  return r;
}

function reglages() {
  const tous = listeReglages();
  const plier = (t) => String(t).normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  const titreSection = (cle) => tr(SECTIONS.find((s) => s[0] === cle)[1]);
  const groupe = (cle, liste) => `<div class="groupe apparait"><h3 class="jeu">${SVG[SECTIONS.find((s) => s[0] === cle)[2]]}${h(titreSection(cle))}</h3>
    <div class="carte">${liste.map((g) => `<div class="reglage"><div class="quoi"><b>${h(g.titre)}</b>${g.detail ? `<small>${h(g.detail)}</small>` : ""}</div>${g.vue}</div>`).join("")}</div></div>`;
  let droite;
  if (E.recherche) {
    const cherche = plier(E.recherche);
    const trouves = tous.filter((g) => [g.titre, g.detail, titreSection(g.section)].some((t) => plier(t).includes(cherche)));
    droite = trouves.length ? SECTIONS.map(([cle]) => trouves.filter((g) => g.section === cle)).map((l, i) => (l.length ? groupe(SECTIONS[i][0], l) : "")).join("")
      : `<p style="color:var(--doux);margin-top:40px">${h(tr("Aucun réglage trouvé."))}</p>`;
  } else {
    droite = groupe(E.sectionReglages, tous.filter((g) => g.section === E.sectionReglages));
  }
  const nav = SECTIONS.map(([cle, titre, icone]) => `<button class="${!E.recherche && E.sectionReglages === cle ? "choisie" : ""}" data-action="section-reglages" data-cle="${cle}">${SVG[icone]}${h(tr(titre))}</button>`).join("");
  return `<div class="reglages"><nav><h2 class="jeu">${h(tr("Réglages"))}</h2>
    <div class="recherche">${SVG.recherche}<input id="recherche" placeholder="${h(tr("Rechercher"))}" value="${h(E.recherche)}" data-change="recherche"></div>
    <div class="sections"><span class="indic"></span>${nav}</div></nav>
    <div class="droite" data-garde="reglages"><div>${droite}</div></div></div>`;
}

async function chargerInfos() {
  for (const nom of ["cle_info", "certificat_info", "composants", "temporaires"]) {
    const [r] = await api(nom);
    if (r) E.infos[nom] = r;
  }
  if (E.section === "reglages") rendre();
}

// Clicks and changes ---------------------------------------------------------------------------------
const ACTIONS = {
  section: (el) => { if (el.dataset.section === E.section && E.section === "android") aller("android", null); else aller(el.dataset.section); },
  page: (el) => {
    const badge = $(".badge", el);
    if (badge) E.flip = badge.getBoundingClientRect();
    aller("android", el.dataset.page);
  },
  retour: () => aller("android", null),
  "maj-telephone": () => mettreAJourTelephone(),
  "copie-demarrer": () => commande("copie_demarrer"),
  "copie-arreter": () => commande("copie_arreter"),
  ouvrir: (el) => demander("ouvrir", { chemin: el.dataset.chemin }),
  montrer: (el) => demander("montrer", { chemin: el.dataset.chemin }),
  "choisir-jeu": async (el) => { const c = await demander("choisir", { types: el.dataset.cle === "official" ? ["xapk", "apkm", "apk"] : [], depart: E.reglages[el.dataset.cle] }); if (c) ecrire({ [el.dataset.cle]: c }); },
  "choisir-dossier": async (el) => {
    const c = await demander("choisir", { dossier: true, depart: E.reglages[el.dataset.cle] });
    if (c) { await ecrire({ [el.dataset.cle]: c }); if (el.dataset.cle === "dossier_sauvegardes") lister(); }
  },
  "choisir-sortie": async () => { const c = await demander("enregistrer", { nom: "RangerRumble_hors_ligne.apk", types: ["apk"] }); if (c) { E.libre = null; ecrire({ output: c }); } },
  "choisir-adb": async () => { const c = await demander("choisir", {}); if (c) ecrire({ adb: c }); },
  effacer: async (el) => { await ecrire({ [el.dataset.cle]: "" }); if (el.dataset.cle === "dossier_sauvegardes") lister(); },
  "autre-sauvegarde": async () => { const c = await demander("choisir", { types: ["msgpack"] }); if (c) { await ecrire({ sauvegarde: c, nouvelle_partie: false }); lister(); } },
  fabriquer: () => commande("fabriquer", { jeu: E.reglages.official, sortie: E.reglages.output, sauvegarde: E.reglages.sauvegarde,
    nouvelle: !!E.reglages.nouvelle_partie, images: E.reglages.artworks }),
  installer: () => installer(E.reglages.output),
  "maj-verifier": () => commande("maj_verifier"),
  "aide-telephone": () => question(tr("Faire reconnaître le téléphone"), tr("1. Brancher le téléphone avec un câble USB.\n2. Sur le téléphone : glisser du haut de l'écran, toucher la notification USB, choisir « Transfert de fichiers ».\n3. Toujours rien ? Activer le mode développeur (une seule fois) : Paramètres > À propos du téléphone, toucher 7 fois « Numéro de build » (Samsung : À propos du téléphone > Informations sur le logiciel > « Numéro de version »).\n4. Paramètres > Options de développement (tout en bas, ou dans Système) : activer « Débogage USB ».\n5. Toucher « Autoriser » quand le téléphone demande « Autoriser le débogage USB ? »."), [{ titre: tr("OK") }]),
  "maj-outil": () => commande("maj_outil"),
  "ed-ouvrir": async (el) => {
    const source = el.dataset.source;
    if (source === "fichier") { const c = await demander("choisir", { types: ["msgpack"] }); if (c) ouvrirSauvegarde("fichier", c); }
    else if (source === "copie") { const c = await demander("choisir", { dossier: true, depart: `${E.copies}/` }); if (c) ouvrirSauvegarde("copie", c); }
    else ouvrirSauvegarde(source);
  },
  onglet: (el) => { E.onglet = el.dataset.onglet; rendre(); },
  "ed-action": (el) => {
    const quoi = el.dataset.quoi;
    const corps = { action: quoi };
    if (quoi.startsWith("max")) corps.lignes = (E.edLignes?.lignes || []).map((l, i) => (l.possede ? i : -1)).filter((i) => i >= 0);
    editer("ed_action", corps);
  },
  "ed-envoyer": () => editer("ed_envoyer", {}),
  "ed-enregistrer": async () => { const c = await demander("enregistrer", { nom: "RangerRumble_sauvegarde.msgpack", types: ["msgpack"] }); if (c) editer("ed_enregistrer", { chemin: c }); },
  "ed-pour-apk": async () => {
    const c = await demander("enregistrer", { nom: "RangerRumble_sauvegarde.msgpack", types: ["msgpack"] });
    if (c) { await editer("ed_enregistrer", { chemin: c, pour_apk: true }); toast(tr("C'est fait"), tr("L'APK partira de cette sauvegarde."), "succes"); lister(); }
  },
  "ed-annuler": () => editer("ed_annuler", {}),
  noeud: async (el) => {
    const cle = el.dataset.cle, n = noeudDe(cle);
    if (!n) return;
    if (n.children) {
      if (E.edArbre.ouverts[cle]) { delete E.edArbre.ouverts[cle]; rendre(); return; }
      const [r] = await api("ed_arbre", { partie: n.part, chemin: n.path, type: n.kind });
      E.edArbre.ouverts[cle] = r?.noeuds || [];
      rendre();
    } else if (n.modifiable) {
      const saisie = prompt(n.label, String(n.text).replace(/^'|'$/g, ""));
      if (saisie === null) return;
      const valeur = n.text === "True" || n.text === "False" ? saisie.toLowerCase() === "true" : saisie !== "" && !isNaN(Number(saisie)) ? Number(saisie) : saisie;
      editer("ed_noeud_changer", { partie: n.part, chemin: n.path, type: n.kind, valeur });
    }
  },
  "section-reglages": (el) => { E.recherche = ""; E.sectionReglages = el.dataset.cle; rendre(); },
  regler: (el) => ecrire({ [el.dataset.cle]: el.dataset.valeur }),
  adb: () => demanderAdb(() => {}),
  actualiser: () => commande("telephones", { rafraichir: true }),
  "certificat-recreer": () => question(tr("Recréer le certificat ?"), tr("L'ancien est gardé à côté. Il faudra réinstaller le profil sur l'iPhone."), [
    { titre: tr("Recréer"), action: async () => { const [r] = await api("certificat_recreer"); if (r) { E.infos.certificat_info = r; rendre(); } } },
    { titre: tr("Annuler"), annuler: true }]),
  "cle-exporter": async () => {
    const c = await demander("enregistrer", { nom: "cle_apk.p12", types: ["p12"] });
    if (c && (await api("cle_exporter", { chemin: c }))[0]) toast(tr("Clé exportée"), tr("À garder en lieu sûr."), "succes");
  },
  "cle-importer": async () => {
    const c = await demander("choisir", { types: ["p12"] });
    if (!c) return;
    question(tr("Remplacer la clé de cet ordinateur ?"), tr("Les prochains APK seront signés avec la clé importée."), [
      { titre: tr("Importer"), action: async () => { const [r] = await api("cle_importer", { chemin: c }); if (r) { E.infos.cle_info = r; toast(tr("Clé importée"), "", "succes"); rendre(); } } },
      { titre: tr("Annuler"), annuler: true }]);
  },
  reparer: () => question(tr("Réparer les composants ?"), tr("L'outil va redémarrer."), [
    { titre: tr("Réparer"), action: async () => { await api("composants_reparer"); demander("relancer"); } }, { titre: tr("Annuler"), annuler: true }]),
  journal: () => {
    const feuille = document.createElement("div");
    feuille.className = "feuille";
    feuille.innerHTML = `<div class="boutons"><h3 class="jeu" style="margin:0;flex:1">${h(tr("Journal de la session"))}</h3>
      <button class="principal jeu" onclick="this.closest('.feuille').remove()">${h(tr("Fermer"))}</button></div>
      <div class="journal">${h(E.journal.map((l) => l.texte).join("\n"))}</div>`;
    document.body.append(feuille);
  },
  "journal-copier": async () => { await demander("copier", { texte: E.journal.map((l) => l.texte).join("\n") }); toast(tr("Journal copié"), "", "succes"); },
  nettoyer: async () => {
    const [r] = await api("nettoyer");
    if (r) { toast(tr("Nettoyé"), tr("{n} Mo dans la Corbeille", { n: Math.round((r.liberes || 0) / 1e6) }), "succes"); E.infos.temporaires = { taille: 0 }; rendre(); }
  },
  reinitialiser: () => question(tr("Réinitialiser les réglages ?"), tr("La langue est gardée."), [
    { titre: tr("Réinitialiser"), action: async () => { const [r] = await api("reinitialiser"); if (r) { E.reglages = r.reglages; appliquerApparence(); rendre(); } } },
    { titre: tr("Annuler"), annuler: true }]),
};

document.addEventListener("click", (e) => {
  const el = e.target.closest("[data-action]");
  if (!el || el.disabled) return;
  ACTIONS[el.dataset.action]?.(el, e);
});

// A value changed in the editor's table shows at once, before the lines are read again.
function noterValeur(el, valeur) {
  const ligne = E.edLignes?.lignes[Number(el.dataset.ligne)];
  if (ligne) ligne.valeurs[el.dataset.cle] = valeur;
}

const CHANGEMENTS = {
  sauvegarde: (el) => ecrire({ sauvegarde: el.value, nouvelle_partie: false }),
  nouvelle: (el) => ecrire({ nouvelle_partie: el.checked }),
  drapeau: (el) => ecrire({ [el.dataset.cle]: el.checked }),
  langue: (el) => ecrire({ langue: el.value }),
  "ed-bool": (el) => {
    noterValeur(el, el.checked);
    editer("ed_changer", { onglet: E.onglet, ligne: Number(el.dataset.ligne), cle: el.dataset.cle, valeur: el.checked,
      nom: E.edLignes?.lignes[Number(el.dataset.ligne)]?.valeurs.name ?? null });
  },
  "ed-valeur": (el) => {
    const valeur = el.dataset.texte ? el.value : Number(el.value.replace(/\s/g, ""));
    if (!el.dataset.texte && !Number.isFinite(valeur)) return;
    noterValeur(el, valeur);
    editer("ed_changer", { onglet: E.onglet, ligne: Number(el.dataset.ligne), cle: el.dataset.cle, valeur,
      nom: E.edLignes?.lignes[Number(el.dataset.ligne)]?.valeurs.name ?? null });
  },
};

// A number box of the editor: its value selected at once, so that typing replaces it (Return or leaving sends it).
document.addEventListener("focusin", (e) => { if (e.target.matches?.("input.valeur") && !e.target.dataset.tape) e.target.select(); });

document.addEventListener("change", (e) => {
  const el = e.target.closest("[data-change]");
  if (el && el.dataset.change !== "recherche") CHANGEMENTS[el.dataset.change]?.(el);
});

document.addEventListener("input", (e) => {
  if (e.target.dataset?.change === "recherche") { E.recherche = e.target.value; rendre(); }
  if (e.target.matches?.("input.valeur")) e.target.dataset.tape = "1";  // typed, not sent yet
});

window.addEventListener("resize", () => { rendreBarre(); placerIndicateurs(); });

// Start --------------------------------------------------------------------------------------------------
async function demarrer() {
  try {
    const r = await fetch("/ressources/langues.json");
    E.table = await r.json();
  } catch { E.table = {}; }
  const [bonjour] = await api("bonjour");
  if (!bonjour) return;
  Object.assign(E, { version: bonjour.version, jeu: bonjour.jeu, reglages: bonjour.reglages, langues: bonjour.langues, langue: bonjour.langue,
    copies: bonjour.copies, base: bonjour.base, tache: bonjour.tache });
  if (E.reglages.page_depart === "derniere" && ["android", "ios", "ordinateur"].includes(E.reglages.derniere_page)) E.section = E.reglages.derniere_page;
  const essai = new URLSearchParams(location.search).get("page");
  if (essai) { const [s, p] = essai.split("/"); E.section = s; if (s === "android") E.page = p || null; if (s === "reglages" && p) E.sectionReglages = p; }
  if (NATIF) document.documentElement.classList.add("mac");
  appliquerApparence();
  traduireCadre();
  rendreBarre();
  rendre();
  ecouter();
  lister();
  chargerInfos();
  requestAnimationFrame(animerBarre);
  setTimeout(() => { $("#ouverture").classList.add("parti"); $("#app").classList.add("pret"); rendreBarre(); }, 900 * duree());
  if (new URLSearchParams(location.search).get("visite")) visite();
}

/// ?visite=1: the window shows itself, page after page (the trials' video).
async function visite() {
  const etapes = [["android", 5], ["android/copie", 3.5], ["android", 2], ["android/fabrication", 3.5], ["android", 2], ["android/editeur", 4],
    ["android/majs", 3], ["ios", 4], ["ordinateur", 4], ["reglages/general", 3], ["reglages/apparence", 3], ["reglages/telephone", 3],
    ["reglages/cle", 3], ["android", 3]];
  const attendre = (s) => new Promise((r) => setTimeout(r, s * 1000));
  await attendre(2);
  for (const [chemin, secondes] of etapes) {
    const [s, p] = chemin.split("/");
    if (s === "reglages" && p) E.sectionReglages = p;
    if (s === "android" && p && E.section === "android" && !E.page) {
      const carte = $(`.carte-outil[data-page="${p}"] .badge`);
      if (carte) E.flip = carte.getBoundingClientRect();
    }
    if (s === "reglages" && E.section === "reglages") rendre(); else aller(s, s === "android" ? p || null : null);
    await attendre(secondes);
  }
}

demarrer();
