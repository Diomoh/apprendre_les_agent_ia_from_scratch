"""
evaluations/jeu_de_reference.py - Les cas de référence de notre agent.

Chaque cas vérifie un COMPORTEMENT observable : la bonne réponse,
mais aussi le bon outil (ou l'absence d'outil).
"""

from agent.evaluations import CasDeTest, outils_utilises

CAS_DE_REFERENCE = [
    CasDeTest(
        nom="calcul_utilise_calculatrice",
        entree="Combien font 1234 multiplié par 5678 ?",
        verifier=lambda reponse, etat: "calculatrice" in outils_utilises(etat)
        and "7006652" in reponse.replace(" ", "").replace(" ", "").replace(".", "").replace(",", ""),
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
        verifier=lambda reponse, etat: etat.termine,
        description="L'erreur d'outil n'empêche pas l'agent de conclure.",
    ),
    CasDeTest(
        nom="termine_en_peu_d_etapes",
        entree="Combien font 2 plus 2 ?",
        verifier=lambda reponse, etat: etat.termine and etat.etapes <= 3,
        description="Une tâche simple ne doit pas boucler.",
    ),
]
