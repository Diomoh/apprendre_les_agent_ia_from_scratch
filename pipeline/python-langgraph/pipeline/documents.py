"""
pipeline/documents.py - Écrire les livrables lisibles par un humain.

Chaque passage du pipeline traite UNE fonctionnalité et produit :
    <sortie>/<fonctionnalite>/
    ├── docs/prd/<fonctionnalite>.md              spécifications fonctionnelles
    ├── docs/architecture/<fonctionnalite>.md     spécifications techniques + historique Critique
    ├── branches/<T-xx>/...                        le travail de chaque binôme, isolé
    ├── integration/...                            les branches fusionnées + tests
    └── rapport.md                                 le résumé soumis avant la fusion
"""

import json
import re
import unicodedata
from pathlib import Path

from .schemas import PRD, Design, Evaluation


def slug(texte: str) -> str:
    texte = unicodedata.normalize("NFKD", texte).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", texte.lower()).strip("-") or "fonctionnalite"


def ecrire(chemin: Path, contenu: str) -> None:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(contenu, encoding="utf-8")


def prd_markdown(prd: PRD) -> str:
    lignes = [f"# PRD : {prd.fonctionnalite}", "", f"**Objectif** : {prd.objectif}", ""]
    if prd.questions_et_hypotheses:
        lignes += ["## Questions et hypothèses", ""] + [f"- {q}" for q in prd.questions_et_hypotheses] + [""]
    lignes += ["## User stories", ""]
    for s in prd.stories:
        lignes.append(f"### {s.id} : en tant que {s.en_tant_que}, je veux {s.je_veux}, afin de {s.afin_de}")
        lignes += [f"- [ ] {c}" for c in s.criteres_acceptation] + [""]
    lignes += ["## Règles de gestion", ""] + [f"- **{r.id}** : {r.texte}" for r in prd.regles_gestion] + [""]
    lignes += ["## Exigences de sécurité", ""] + [f"- **{e.id}** : {e.texte}" for e in prd.exigences_securite] + [""]
    if prd.hors_perimetre:
        lignes += ["## Hors périmètre", ""] + [f"- {h}" for h in prd.hors_perimetre] + [""]
    return "\n".join(lignes)


def architecture_markdown(design: Design, historique: list[dict]) -> str:
    lignes = [
        "# Dossier d'architecture", "",
        f"**Style** : {design.style_architecture}  ",
        f"**Stack** : {', '.join(design.stack)}  ",
        f"**Design system** : {design.design_system}", "",
        "## Modèle de données", "",
    ] + [f"- {m}" for m in design.modele_donnees] + ["", "## Contrat d'API", "",
         "| Méthode | Chemin | Description | Rôles |", "| --- | --- | --- | --- |"]
    lignes += [f"| {e.methode} | `{e.chemin}` | {e.description} | {', '.join(e.roles_autorises)} |"
               for e in design.contrat_api]
    lignes += ["", "## Réponse aux exigences de sécurité", ""]
    lignes += [f"- **{r.exigence}** : {r.mesure}" for r in design.reponses_securite]
    lignes += ["", "## Décisions (ADR)", ""]
    lignes += [f"- **{d.id}** : {d.decision} (écarté : {d.alternatives_ecartees})" for d in design.decisions]
    lignes += ["", "## Tâches", "", "| Tâche | Couche | Titre | RG | ES | Dépend de |",
               "| --- | --- | --- | --- | --- | --- |"]
    lignes += [f"| {t.id} | {t.couche} | {t.titre} | {', '.join(t.regles)} | "
               f"{', '.join(t.exigences)} | {', '.join(t.depend_de)} |" for t in design.taches]
    lignes += ["", "## Historique de la boucle Architecte / Critique", ""]
    for h in historique:
        ev = Evaluation.model_validate(h["evaluation"])
        etat = "validé" if ev.est_valide() else "renvoyé"
        lignes.append(f"- Tour {h['tour']} : moyenne {ev.moyenne()}/10, sécurité {ev.notes.securite}/10, {etat}")
        lignes += [f"  - {o}" for o in ev.objections]
    return "\n".join(lignes) + "\n"


def sauver_json(chemin: Path, donnees) -> None:
    ecrire(chemin, json.dumps(donnees, ensure_ascii=False, indent=2))
