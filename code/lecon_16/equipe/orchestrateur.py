"""
equipe/orchestrateur.py - Le déroulé du projet de l'équipe technique.

Leçon 16 : on assemble TOUT le cours.
- chaque membre est un Agent (leçons 01 à 12) avec ses outils et ses droits (leçon 10) ;
- le travail est un graphe de tâches (leçon 15) exécuté par phases ;
- la revue de code passe par une boucle de revue (leçon 15) ;
- tests et sécurité déclenchent des boucles de correction arbitrées par le CODE ;
- des points de contrôle humains séparent les phases ;
- tout est tracé dans la télémétrie (leçon 11).
"""

from datetime import datetime
from pathlib import Path

from agent.agent import Agent
from agent.telemetrie import Telemetrie
from cerveau.utils import extraire_json
from equipe.outils_equipe import boite_pour
from equipe.profils import CHARTE, PROFILS
from multi.graphe import GrapheTaches, Tache, executeur_avec_revue, point_de_controle


def creer_equipe(racine: str, confirmer, telemetrie) -> dict[str, Agent]:
    """Un Agent par profil : même classe, configuration différente."""
    equipe = {}
    for nom, profil in PROFILS.items():
        equipe[nom] = Agent(
            nom=nom,
            role=f"{profil['role']}\n\n{CHARTE}",
            outils=boite_pour(nom, profil, racine, confirmer),
            outils_memoire=False,
            telemetrie=telemetrie,
            max_etapes=20,
            max_tokens=16000,
        )
    return equipe


# ------------------------------------------------------------
# Exécuteurs spécialisés (des boucles arbitrées par le code)
# ------------------------------------------------------------

def executeur_tests(max_corrections: int = 2):
    """
    Le testeur écrit et lance les tests. Ensuite, c'est le CODE qui relance
    pytest pour vérifier (on ne croit pas l'agent sur parole). En cas d'échec,
    le dev back-end corrige, le testeur re-vérifie, au plus `max_corrections` fois.
    """

    def executeur(tache, agents, consigne):
        testeur, dev = agents["testeur"], agents["dev_backend"]
        rapport = testeur.executer(consigne)

        for numero in range(1, max_corrections + 1):
            sortie = testeur.outils.executer("lancer_tests", {})
            if sortie.startswith("code_retour=0"):
                return f"{rapport}\n\n✅ Vérification par l'orchestrateur : tests au vert."
            if sortie.startswith("REFUSÉ"):
                return f"{rapport}\n\n⚠ Tests non vérifiés : exécution refusée par l'humain."

            print(f"\n🔁 Correction {numero}/{max_corrections} : les tests échouent")
            message_dev = dev.executer(
                "Les tests automatisés échouent. Sortie de pytest :\n"
                f"{sortie}\n\nCorrige le code dans backend/. Ne modifie pas les tests ; "
                "si un test te paraît faux, explique-le dans ta réponse."
            )
            rapport = testeur.executer(
                "Le développeur back-end a livré une correction (voir ci-dessous). Relance "
                "lancer_tests. Si un test est réellement faux, corrige-le et justifie. "
                "Mets à jour docs/rapport_tests.md avec le résultat réel.\n\n"
                f"Message du développeur :\n{message_dev}"
            )

        sortie = testeur.outils.executer("lancer_tests", {})
        bilan = "au vert ✅" if sortie.startswith("code_retour=0") else "TOUJOURS EN ÉCHEC ❌"
        return f"{rapport}\n\nVérification finale par l'orchestrateur : tests {bilan}\n{sortie[-800:]}"

    return executeur


def executeur_securite():
    """
    Audit → si vulnérabilités bloquantes, le code route chaque correction vers
    le bon développeur (selon le dossier du fichier) → contre-audit.
    """

    def executeur(tache, agents, consigne):
        auditeur = agents["cybersecurite"]
        audit = auditeur.executer(consigne)
        bloquantes = (extraire_json(audit) or {}).get("vulnerabilites_bloquantes") or []
        if not bloquantes:
            return audit

        par_dev: dict[str, list] = {}
        for vuln in bloquantes:
            fichier = str(vuln.get("fichier", ""))
            dev = "dev_frontend" if fichier.startswith("frontend") else "dev_backend"
            par_dev.setdefault(dev, []).append(vuln)

        for dev, vulns in par_dev.items():
            liste = "\n".join(
                f"- {v.get('fichier')} : {v.get('probleme')} → {v.get('correction')}" for v in vulns
            )
            print(f"\n🔐 {len(vulns)} vulnérabilité(s) bloquante(s) envoyée(s) à {dev}")
            agents[dev].executer(f"L'audit de sécurité a trouvé ces vulnérabilités à corriger :\n{liste}")

        contre_audit = auditeur.executer(
            "Les développeurs ont corrigé les vulnérabilités bloquantes de ton audit. "
            "Relis les fichiers concernés, vérifie chaque correction et mets à jour "
            "docs/rapport_securite.md (section « Contre-audit »). Termine par le JSON "
            '{"vulnerabilites_bloquantes": [...]} des problèmes qui RESTENT.'
        )
        return f"{audit}\n\n--- Contre-audit ---\n{contre_audit}"

    return executeur


# ------------------------------------------------------------
# Le projet, phase par phase
# ------------------------------------------------------------

def lancer_projet(brief: str, dossier_livrables: str = "livrables", automatique: bool = False,
                  confirmer=None) -> dict:
    racine = Path(dossier_livrables) / f"projet_{datetime.now():%Y%m%d_%H%M%S}"
    racine.mkdir(parents=True)
    telemetrie = Telemetrie(str(racine / "telemetrie.jsonl"))
    agents = creer_equipe(str(racine), confirmer, telemetrie)
    graphe = GrapheTaches()
    print(f"📁 Espace de travail : {racine}")

    def phase(nom: str, taches: list[Tache]) -> bool:
        print(f"\n\n################ PHASE : {nom} ################")
        for tache in taches:
            graphe.ajouter(tache)
        graphe.executer(agents)
        echecs = [t.id for t in taches if t.statut != "terminee"]
        if echecs:
            print(f"\n❌ Phase « {nom} » incomplète : {echecs}")
        return not echecs

    def fin(raison: str) -> dict:
        print(f"\n{raison}\n\n{graphe.afficher()}")
        print("\nTélémétrie :", telemetrie.resume())
        return {"racine": str(racine), "statuts": {t: x.statut for t, x in graphe.taches.items()},
                "raison": raison}

    # ---------- Phase 1 : cadrage ----------
    ok = phase("Cadrage", [
        Tache("cahier_des_charges", "chef_de_projet",
              f"Voici le besoin du client :\n« {brief} »\n\nRédige docs/cahier_des_charges.md."),
    ])
    if not ok:
        return fin("Arrêt : cadrage impossible.")
    if not point_de_controle("Cahier des charges",
                             (racine / "docs/cahier_des_charges.md").read_text(encoding="utf-8")
                             if (racine / "docs/cahier_des_charges.md").exists()
                             else graphe.taches["cahier_des_charges"].resultat,
                             automatique):
        return fin("Arrêt : cahier des charges refusé par l'humain.")

    # ---------- Phase 2 : conception ----------
    ok = phase("Conception", [
        Tache("decisions_techniques", "chef_de_projet",
              "Lis le cahier des charges et rédige docs/decisions_techniques.md.",
              depend_de=["cahier_des_charges"]),
        Tache("ux", "ux_designer",
              "Lis le cahier des charges et rédige docs/ux.md.",
              depend_de=["cahier_des_charges"]),
        Tache("architecture", "lead_tech",
              "Lis le cahier des charges, docs/decisions_techniques.md et docs/ux.md, "
              "puis rédige docs/architecture.md.",
              depend_de=["decisions_techniques", "ux"]),
    ])
    if not ok:
        return fin("Arrêt : conception incomplète.")
    if not point_de_controle("Architecture", graphe.taches["architecture"].resultat, automatique):
        return fin("Arrêt : architecture refusée par l'humain.")

    # ---------- Phase 3 : réalisation et qualité ----------
    phase("Réalisation et qualité", [
        Tache("backend", "dev_backend",
              "Implémente le back-end décrit dans docs/architecture.md.",
              depend_de=["architecture"],
              executeur=executeur_avec_revue("lead_tech", max_tours=2)),
        Tache("frontend", "dev_frontend",
              "Implémente le front-end décrit dans docs/ux.md et docs/architecture.md.",
              depend_de=["architecture"],
              executeur=executeur_avec_revue("lead_tech", max_tours=2)),
        Tache("tests", "testeur",
              "Écris les tests de la logique métier du back-end dans tests/, lance-les avec "
              "lancer_tests et rédige docs/rapport_tests.md.",
              depend_de=["backend"],
              executeur=executeur_tests(max_corrections=2)),
        Tache("securite", "cybersecurite",
              "Audite backend/ et frontend/ et rédige docs/rapport_securite.md.",
              depend_de=["backend", "frontend"],
              executeur=executeur_securite()),
        Tache("go_no_go", "chef_de_projet",
              "Lis docs/rapport_tests.md et docs/rapport_securite.md, puis décide si le "
              "projet peut partir en production.",
              depend_de=["tests", "securite"]),
    ])
    if graphe.taches["go_no_go"].statut != "terminee":
        return fin("Arrêt : la phase de réalisation n'a pas abouti.")

    decision = extraire_json(graphe.taches["go_no_go"].resultat or "") or {}
    feu_vert = decision.get("decision") == "go"
    print(f"\n🚦 Décision du chef de projet : {decision.get('decision', 'inconnue')} - {decision.get('raisons')}")
    if feu_vert:
        feu_vert = point_de_controle("Préparer la mise en production ?",
                                     str(decision), automatique)

    # ---------- Phase 4 : livraison ----------
    taches_finales = []
    if feu_vert:
        taches_finales.append(Tache(
            "deploiement", "chef_de_projet",
            "Prépare le déploiement : deploiement/Dockerfile et deploiement/README_deploiement.md.",
            depend_de=["go_no_go"]))
    taches_finales.append(Tache(
        "bilan", "chef_de_projet",
        "Relis tous les documents et le code, puis rédige docs/bilan.md. "
        + ("" if feu_vert else "Le déploiement n'a PAS été préparé (pas de feu vert) : explique pourquoi."),
        depend_de=["deploiement"] if feu_vert else ["go_no_go"]))
    phase("Livraison", taches_finales)

    return fin("🏁 Projet terminé.")
