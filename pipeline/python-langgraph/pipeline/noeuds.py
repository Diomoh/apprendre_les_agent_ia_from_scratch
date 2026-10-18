"""
pipeline/noeuds.py - Un nœud du graphe = une étape du pipeline.

Ordre de lecture conseillé : analyste -> architecte -> critique -> validation_design
-> binome -> integration -> relecteur -> fix -> merge.

Règle d'or du cours : le modèle PROPOSE, le CODE DÉCIDE. Les seuils, les plafonds
de tours et les arrêts pour validation humaine sont écrits ici, pas dans un prompt.
"""

import json
import shutil
import subprocess
import sys
import os
import threading
from pathlib import Path

from langgraph.types import interrupt

from . import prompts
from .documents import architecture_markdown, ecrire, prd_markdown, sauver_json, slug
from .llm import ClientLLM
from .schemas import (
    MAX_CYCLES_FIX,
    PRD,
    Avis,
    Design,
    Evaluation,
    Livraison,
)

EXTENSIONS_CODE = {".py", ".ts", ".tsx", ".js", ".jsx"}
TAILLE_MAX_CODE = 60_000  # caractères de code envoyés à un relecteur


_VERROU_AFFICHAGE = threading.Lock()


def journal(etape: str, message: str) -> None:
    with _VERROU_AFFICHAGE:  # les binômes et relecteurs écrivent en parallèle
        print(f"[{etape}] {message}", flush=True)


class Pipeline:
    def __init__(self, client: ClientLLM, racine_sortie: str | Path = "sortie"):
        self.client = client
        self.racine = Path(racine_sortie)

    # -- utilitaires ------------------------------------------------------------

    def dossier(self, etat_ou_nom) -> Path:
        nom = etat_ou_nom if isinstance(etat_ou_nom, str) else etat_ou_nom["fonctionnalite"]
        return self.racine / slug(nom)

    @staticmethod
    def lire_code(dossier: Path) -> str:
        """Tout le code d'un dossier, chaque fichier précédé de son chemin."""
        morceaux = []
        for fichier in sorted(dossier.rglob("*")):
            if fichier.is_file() and fichier.suffix in EXTENSIONS_CODE:
                relatif = fichier.relative_to(dossier).as_posix()
                morceaux.append(f"### {relatif}\n```\n{fichier.read_text(encoding='utf-8')}\n```")
        return "\n\n".join(morceaux)[:TAILLE_MAX_CODE]

    @staticmethod
    def ecrire_fichiers(dossier: Path, livraison: Livraison) -> list[str]:
        chemins = []
        for f in livraison.fichiers:
            chemin = (dossier / f.chemin).resolve()
            # Garde-fou : un agent n'écrit jamais en dehors de son dossier.
            if dossier.resolve() not in chemin.parents:
                raise ValueError(f"Chemin refusé (hors du dossier de travail) : {f.chemin}")
            ecrire(chemin, f.contenu)
            chemins.append(f.chemin)
        return chemins

    # -- 1. Intake : l'Analyste produit le PRD ------------------------------------

    def analyste(self, etat):
        dossier = self.dossier(etat)
        if dossier.exists():
            shutil.rmtree(dossier)  # un passage = une fonctionnalité, on repart de zéro
        journal("analyste", f"Cahier des charges -> PRD « {etat['fonctionnalite']} »")
        prd = self.client.demander_json(
            "analyste",
            prompts.ANALYSTE,
            f"Fonctionnalité à spécifier : {etat['fonctionnalite']}\n\n"
            f"Cahier des charges :\n{etat['cahier_des_charges']}",
            PRD,
        )
        ecrire(dossier / "docs" / "prd" / f"{slug(etat['fonctionnalite'])}.md", prd_markdown(prd))
        sauver_json(dossier / "docs" / "prd" / f"{slug(etat['fonctionnalite'])}.json", prd.model_dump())
        journal("analyste", f"{len(prd.stories)} stories, {len(prd.regles_gestion)} RG, "
                            f"{len(prd.exigences_securite)} ES")
        return {"prd": prd.model_dump(), "tours_design": 0, "cycles_fix": 0, "commentaire_humain": ""}

    # -- 2. Design : boucle Architecte <-> Critique -----------------------------------

    def architecte(self, etat):
        tour = etat.get("tours_design", 0) + 1
        consigne = f"PRD :\n{json.dumps(etat['prd'], ensure_ascii=False, indent=1)}"
        if etat.get("design"):
            consigne += f"\n\nTa version précédente :\n{json.dumps(etat['design'], ensure_ascii=False)}"
        if etat.get("evaluation"):
            objections = Evaluation.model_validate(etat["evaluation"]).objections
            if objections:
                consigne += "\n\nObjections du Critique à corriger :\n" + "\n".join(f"- {o}" for o in objections)
        if etat.get("commentaire_humain"):
            consigne += f"\n\nCommentaire du validateur humain à appliquer :\n{etat['commentaire_humain']}"
        journal("architecte", f"Tour {tour} : rédaction du dossier d'architecture")
        design = self.client.demander_json(
            "architecte", prompts.ARCHITECTE, consigne, Design, {"tour": tour}
        )
        return {"design": design.model_dump(), "tours_design": tour}

    def critique(self, etat):
        tour = etat["tours_design"]
        evaluation = self.client.demander_json(
            "critique",
            prompts.CRITIQUE,
            f"PRD :\n{json.dumps(etat['prd'], ensure_ascii=False)}\n\n"
            f"Dossier d'architecture :\n{json.dumps(etat['design'], ensure_ascii=False)}",
            Evaluation,
            {"tour": tour},
        )
        verdict = "validé" if evaluation.est_valide() else "renvoyé à l'Architecte"
        journal("critique", f"Tour {tour} : moyenne {evaluation.moyenne()}/10, "
                            f"sécurité {evaluation.notes.securite}/10 -> {verdict}")
        return {
            "evaluation": evaluation.model_dump(),
            "historique_design": [{"tour": tour, "evaluation": evaluation.model_dump()}],
        }

    # -- 3. Validation humaine du dossier (PRD + architecture) -----------------------------

    def validation_design(self, etat):
        dossier = self.dossier(etat)
        design = Design.model_validate(etat["design"])
        historique = [h for h in etat.get("historique_design", [])]
        ecrire(dossier / "docs" / "architecture" / f"{slug(etat['fonctionnalite'])}.md",
               architecture_markdown(design, historique))
        sauver_json(dossier / "docs" / "architecture" / f"{slug(etat['fonctionnalite'])}.json",
                    design.model_dump())
        evaluation = Evaluation.model_validate(etat["evaluation"])

        # Le graphe S'ARRÊTE ici. Il reprendra avec la réponse de l'humain
        # (graphe.invoke(Command(resume=...))). Tout ce qui précède est rejoué
        # à la reprise : c'est pourquoi on n'y met que des écritures idempotentes.
        reponse = interrupt({
            "etape": "validation_design",
            "message": "Validez le PRD et le dossier d'architecture avant le Build.",
            "documents": [str(dossier / "docs" / "prd"), str(dossier / "docs" / "architecture")],
            "note_finale": evaluation.moyenne(),
            "objections_restantes": evaluation.objections,
            "taches": [f"{t.id} ({t.couche}) {t.titre}" for t in design.taches],
        })
        if reponse.get("decision") == "corriger":
            journal("validation", "Corrections demandées, retour à l'Architecte")
            return {"decision_design": "corriger", "tours_design": 0,
                    "commentaire_humain": reponse.get("commentaire", "")}
        journal("validation", "Dossier validé, lancement du Build")
        return {"decision_design": "valide"}

    # -- 4. Build : un binôme Implementer + Tester par tâche, en parallèle -----------------

    def contexte_tache(self, etat, tache: dict) -> str:
        """Context engineering : le binôme ne reçoit que ce qui concerne SA tâche."""
        prd, design = etat["prd"], etat["design"]
        regles = [r for r in prd["regles_gestion"] if r["id"] in tache["regles"]]
        exigences = [e for e in prd["exigences_securite"] if e["id"] in tache["exigences"]]
        mesures = [m for m in design["reponses_securite"] if m["exigence"] in tache["exigences"]]
        return json.dumps({
            "tache": tache,
            "regles_gestion": regles,
            "exigences_securite": exigences,
            "mesures_securite": mesures,
            "contrat_api": design["contrat_api"],
            "modele_donnees": design["modele_donnees"],
            "stack": design["stack"],
        }, ensure_ascii=False, indent=1)

    def binome(self, charge):
        """Reçoit {tache, contexte, fonctionnalite} via Send, pas l'état complet."""
        tache = charge["tache"]
        branche = self.dossier(charge["fonctionnalite"]) / "branches" / tache["id"]
        journal("build", f"{tache['id']} ({tache['couche']}) : Implementer")
        code = self.client.demander_json(
            f"implementer:{tache['id']}", prompts.IMPLEMENTER,
            f"Code cette tâche :\n{charge['contexte']}", Livraison, {"tache": tache},
        )
        fichiers = self.ecrire_fichiers(branche, code)

        journal("build", f"{tache['id']} ({tache['couche']}) : Testeur")
        tests = self.client.demander_json(
            f"testeur:{tache['id']}", prompts.TESTEUR,
            f"Tâche et contexte :\n{charge['contexte']}\n\nCode à tester :\n{self.lire_code(branche)}",
            Livraison, {"tache": tache},
        )
        fichiers += self.ecrire_fichiers(branche, tests)
        return {"resultats_build": [{
            "tache": tache["id"], "couche": tache["couche"], "fichiers": fichiers,
            "resume_code": code.resume, "resume_tests": tests.resume,
        }]}

    # -- 5. Integrate : fusion des branches, tests, scan de sécurité -------------------------

    def integration(self, etat):
        dossier = self.dossier(etat)
        cible = dossier / "integration"
        conflits = []
        if not cible.exists():  # 1re intégration : on fusionne les branches
            origine: dict[str, str] = {}
            for branche in sorted((dossier / "branches").iterdir()):
                for fichier in sorted(branche.rglob("*")):
                    if not fichier.is_file():
                        continue
                    relatif = fichier.relative_to(branche).as_posix()
                    destination = cible / relatif
                    contenu = fichier.read_text(encoding="utf-8")
                    if destination.exists() and destination.read_text(encoding="utf-8") != contenu:
                        conflits.append(f"{relatif} : {origine[relatif]} et {branche.name}")
                    ecrire(destination, contenu)
                    origine[relatif] = branche.name

        tests = self.lancer_pytest(cible)
        scan = self.lancer_bandit(cible)
        etat_tests = "OK" if tests["reussi"] else "ÉCHEC"
        journal("integration", f"Tests {etat_tests} ({tests['resume']}), conflits : {len(conflits)}, "
                               f"scan sécurité : {scan['statut']}")
        return {"rapport_integration": {"tests": tests, "scan_securite": scan, "conflits": conflits}}

    @staticmethod
    def lancer_pytest(dossier: Path) -> dict:
        if not any(dossier.rglob("test_*.py")):
            return {"reussi": False, "resume": "aucun test trouvé", "sortie": ""}
        env = {**os.environ, "PYTHONPATH": str(dossier.resolve())}
        resultat = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
            cwd=dossier, env=env, capture_output=True, text=True, timeout=300,
        )
        lignes = [l for l in resultat.stdout.strip().splitlines() if l.strip()]
        return {
            "reussi": resultat.returncode == 0,
            "resume": lignes[-1] if lignes else f"code retour {resultat.returncode}",
            "sortie": resultat.stdout[-4000:],
        }

    @staticmethod
    def lancer_bandit(dossier: Path) -> dict:
        if not shutil.which("bandit"):
            return {"statut": "non lancé (pip install bandit)", "sortie": ""}
        resultat = subprocess.run(["bandit", "-r", "-q", "."], cwd=dossier,
                                  capture_output=True, text=True, timeout=300)
        statut = "aucun problème" if resultat.returncode == 0 else "problèmes détectés"
        return {"statut": statut, "sortie": resultat.stdout[-4000:]}

    # -- 6. Review : 7 relecteurs en parallèle ------------------------------------------------

    def relecteur(self, charge):
        critere = charge["critere"]
        avis = self.client.demander_json(
            f"relecteur:{critere}",
            prompts.RELECTEUR.format(critere=critere),
            f"PRD :\n{charge['prd']}\n\nDossier d'architecture :\n{charge['design']}\n\n"
            f"Rapport d'intégration :\n{charge['rapport']}\n\nCode intégré :\n{charge['code']}",
            Avis,
            {"cycle": charge["cycle"]},
        )
        avis.critere = critere
        marque = "BLOQUANT" if avis.bloquant else "ok"
        journal("revue", f"Cycle {charge['cycle']} - {critere} : {marque}")
        return {"avis_revue": [{**avis.model_dump(), "cycle": charge["cycle"]}]}

    def decision_revue(self, etat):
        """Point de rendez-vous : attend que les 7 relecteurs aient répondu."""
        return {}

    def problemes_bloquants(self, etat) -> list[str]:
        cycle = etat.get("cycles_fix", 0)
        problemes = [
            f"[{a['critere']}] {p}"
            for a in etat.get("avis_revue", [])
            if a["cycle"] == cycle and a["bloquant"]
            for p in (a["problemes"] or ["problème non détaillé"])
        ]
        tests = etat["rapport_integration"]["tests"]
        if not tests["reussi"]:
            problemes.append(f"[integration] Les tests ne passent pas : {tests['resume']}")
        return problemes

    # -- 7. Fix ------------------------------------------------------------------------------------

    def fix(self, etat):
        cible = self.dossier(etat) / "integration"
        problemes = self.problemes_bloquants(etat)
        journal("fix", f"Cycle {etat.get('cycles_fix', 0) + 1} : {len(problemes)} problème(s) à corriger")
        correction = self.client.demander_json(
            "fix", prompts.FIX,
            "Problèmes bloquants :\n" + "\n".join(f"- {p}" for p in problemes)
            + f"\n\nSortie des tests :\n{etat['rapport_integration']['tests']['sortie']}"
            + f"\n\nCode actuel :\n{self.lire_code(cible)}",
            Livraison,
        )
        fichiers = self.ecrire_fichiers(cible, correction)
        return {
            "cycles_fix": etat.get("cycles_fix", 0) + 1,
            "historique_fix": [{"problemes": problemes, "fichiers": fichiers, "resume": correction.resume}],
        }

    # -- 8. Merge : rapport final et validation humaine ----------------------------------------------

    def merge(self, etat):
        dossier = self.dossier(etat)
        restants = self.problemes_bloquants(etat)
        cycle = etat.get("cycles_fix", 0)
        derniers_avis = [a for a in etat.get("avis_revue", []) if a["cycle"] == cycle]
        tests = etat["rapport_integration"]["tests"]

        lignes = [
            f"# Rapport de livraison : {etat['fonctionnalite']}", "",
            f"- Tours de design : {len(etat.get('historique_design', []))}",
            f"- Tâches livrées : {', '.join(r['tache'] for r in etat.get('resultats_build', []))}",
            f"- Tests : {'OK' if tests['reussi'] else 'ÉCHEC'} ({tests['resume']})",
            f"- Scan de sécurité : {etat['rapport_integration']['scan_securite']['statut']}",
            f"- Cycles de correction : {cycle}", "",
            "## Revue finale", "",
        ] + [f"- {a['critere']} : {'BLOQUANT' if a['bloquant'] else 'ok'}" for a in derniers_avis]
        if etat.get("historique_fix"):
            lignes += ["", "## Corrections appliquées", ""]
            lignes += [f"- {h['resume']} ({', '.join(h['fichiers'])})" for h in etat["historique_fix"]]
        if restants:
            lignes += ["", "## Problèmes NON résolus (plafond de corrections atteint)", ""]
            lignes += [f"- {p}" for p in restants]
        ecrire(dossier / "rapport.md", "\n".join(lignes) + "\n")

        reponse = interrupt({
            "etape": "merge",
            "message": "Validez la fusion du code intégré.",
            "rapport": str(dossier / "rapport.md"),
            "tests": tests["resume"],
            "problemes_restants": restants,
        })
        statut = "fusionne" if reponse.get("decision") == "ok" else "refuse"
        journal("merge", "Fusion validée" if statut == "fusionne" else "Fusion refusée")
        return {"statut": statut}
