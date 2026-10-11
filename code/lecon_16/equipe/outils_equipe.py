"""
equipe/outils_equipe.py - Les outils propres à l'équipe technique.

Leçon 16 : tous les membres lisent l'espace de travail ; chacun n'écrit que
dans ses dossiers ; seul le testeur peut lancer les tests.
"""

import subprocess
import sys

from agent.fichiers import EspaceDeTravail, ajouter_outils_fichiers
from agent.outils import BoiteAOutils


def lancer_pytest(racine) -> str:
    """
    Lance « python -m pytest tests » dans le projet généré.

    ATTENTION : cela EXÉCUTE du code écrit par un LLM sur votre machine.
    C'est pourquoi l'outil est marqué « sensible » (confirmation humaine).
    Idéalement, faites tourner le projet final dans une machine virtuelle ou un conteneur.
    """
    if not (racine / "tests").is_dir():
        return "code_retour=5 (ÉCHEC) : aucun dossier tests/ dans le projet."
    try:
        processus = subprocess.run(
            [sys.executable, "-m", "pytest", "tests", "-q", "-p", "no:cacheprovider"],
            cwd=racine,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        return "code_retour=-1 (ÉCHEC) : les tests ont dépassé 120 secondes."
    sortie = (processus.stdout + processus.stderr)[-3000:]
    etat = "SUCCÈS" if processus.returncode == 0 else "ÉCHEC"
    return f"code_retour={processus.returncode} ({etat})\n{sortie}"


def boite_pour(nom_agent: str, profil: dict, racine: str, confirmer) -> BoiteAOutils:
    """Construit la boîte à outils d'un membre selon ses droits."""
    boite = BoiteAOutils(confirmer=confirmer, taille_max_resultat=12000)
    espace = EspaceDeTravail(racine, dossiers_ecriture=profil["dossiers_ecriture"])
    ajouter_outils_fichiers(boite, espace, ecriture=True)

    if nom_agent == "testeur":
        boite.ajouter(
            "lancer_tests",
            lambda: lancer_pytest(espace.racine),
            "Exécute la suite de tests pytest du projet et renvoie le résultat réel.",
            {"type": "object", "properties": {}, "required": []},
            sensible=True,
        )
    return boite
