"""
evaluations.py - Leçon 11 : tester l'agent comme on teste du code.

Un LLM est probabiliste et un prompt modifié peut tout casser. On garde donc
un jeu de cas de référence (« golden dataset ») et on mesure le taux de réussite
avant chaque changement. Chaque cas vérifie un COMPORTEMENT observable : la bonne
réponse, mais aussi le bon outil (ou l'absence d'outil).
"""

from dataclasses import dataclass
from typing import Callable

import agent


@dataclass
class CasDeTest:
    nom: str
    entree: str
    # verifier(reponse, etat) -> True si le comportement est correct
    verifier: Callable[[str, dict], bool]
    description: str = ""


def outils_utilises(etat: dict) -> list[str]:
    """Les noms des outils appelés pendant l'exécution (lus dans le journal)."""
    noms = []
    for ligne in etat["journal"]:
        if ligne["type"] == "decision":
            noms += ligne["detail"]
    return noms


def sans_espaces(texte: str) -> str:
    return texte.replace(" ", "").replace(" ", "").replace(".", "").replace(",", "")


CAS_DE_REFERENCE = [
    CasDeTest(
        nom="calcul_utilise_calculatrice",
        entree="Combien font 1234 multiplié par 5678 ?",
        verifier=lambda reponse, etat: "calculatrice" in outils_utilises(etat)
        and "7006652" in sans_espaces(reponse),
        description="Le calcul passe par l'outil et le résultat exact apparaît.",
    ),
    CasDeTest(
        nom="heure_utilise_outil",
        entree="Quelle heure est-il ?",
        verifier=lambda reponse, etat: "heure_actuelle" in outils_utilises(etat),
        description="L'agent ne devine pas l'heure : il appelle l'outil.",
    ),
    CasDeTest(
        nom="culture_generale_sans_outil",
        entree="Quelle est la capitale de la France ? Un mot.",
        verifier=lambda reponse, etat: "paris" in reponse.lower() and not outils_utilises(etat),
        description="Pas d'outil inutile pour une question simple.",
    ),
    CasDeTest(
        nom="division_par_zero_geree",
        entree="Divise 10 par 0 avec la calculatrice.",
        verifier=lambda reponse, etat: etat["termine"],
        description="L'erreur d'outil n'empêche pas l'agent de conclure.",
    ),
    CasDeTest(
        nom="termine_en_peu_d_etapes",
        entree="Combien font 2 plus 2 ?",
        verifier=lambda reponse, etat: etat["termine"] and etat["etapes"] <= 3,
        description="Une tâche simple ne doit pas boucler.",
    ),
]


def lancer_evaluations(llm, cas_de_test: list[CasDeTest], preparer: Callable | None = None) -> dict:
    """Exécute chaque cas (sans mémoire courte partagée) et renvoie un rapport."""
    resultats = []
    for cas in cas_de_test:
        if preparer:
            preparer()  # ex. : vider la mémoire longue
        try:
            etat = agent.executer(llm, cas.entree, None)  # None : pas de mémoire courte
            reponse = etat["reponse_finale"] or ""
            reussi = bool(cas.verifier(reponse, etat))
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
