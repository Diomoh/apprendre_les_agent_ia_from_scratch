"""
agent/evaluations.py - Tester l'agent comme on teste du code.

Leçon 11 : un LLM est probabiliste et un prompt modifié peut tout casser.
On garde donc un jeu de cas de référence (« golden dataset ») et on mesure
le taux de réussite avant chaque changement.
"""

from dataclasses import dataclass
from typing import Callable


@dataclass
class CasDeTest:
    nom: str
    entree: str
    # verifier(reponse, etat) -> True si le comportement est correct
    verifier: Callable[[str, object], bool]
    description: str = ""


def outils_utilises(etat) -> list[str]:
    """Les noms des outils appelés pendant la dernière exécution."""
    noms = []
    for ligne in etat.journal:
        if ligne["type"] == "decision":
            noms += ligne["detail"]
    return noms


def lancer_evaluations(fabrique_agent: Callable, cas_de_test: list[CasDeTest]) -> dict:
    """
    Exécute chaque cas avec un agent NEUF (pas de mémoire partagée entre cas)
    et renvoie un rapport.
    """
    resultats = []
    for cas in cas_de_test:
        agent = fabrique_agent()
        try:
            reponse = agent.executer(cas.entree)
            reussi = bool(cas.verifier(reponse, agent.etat))
            detail = reponse[:120]
        except Exception as erreur:  # noqa: BLE001 - un cas qui plante est un échec
            reussi, detail = False, f"EXCEPTION : {erreur}"

        resultats.append({"cas": cas.nom, "reussi": reussi, "detail": detail})
        print(f"  {'✅' if reussi else '❌'} {cas.nom} - {detail}")

    total = len(resultats)
    reussis = sum(1 for r in resultats if r["reussi"])
    return {
        "total": total,
        "reussis": reussis,
        "taux_reussite": round(100 * reussis / total, 1) if total else 0.0,
        "resultats": resultats,
    }
