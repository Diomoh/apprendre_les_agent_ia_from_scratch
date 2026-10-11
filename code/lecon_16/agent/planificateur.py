"""
agent/planificateur.py - La planification.

Leçon 09 : un plan n'est pas une « pensée » cachée, c'est une DONNÉE (JSON)
que l'on peut lire, vérifier, modifier, puis exécuter étape par étape.
"""

SCHEMA_PLAN = """{
  "objectif": "l'objectif reformulé en une phrase",
  "etapes": [
    {"id": 1, "description": "action courte et vérifiable", "outil_suggere": "nom d'outil ou null"},
    {"id": 2, "description": "...", "outil_suggere": null}
  ]
}"""


def valider_plan(plan: dict, max_etapes: int = 8) -> list[str]:
    """Renvoie la liste des problèmes du plan (liste vide = plan valide)."""
    problemes = []
    etapes = plan.get("etapes")
    if not isinstance(etapes, list) or not etapes:
        return ["le plan ne contient aucune étape"]
    if len(etapes) > max_etapes:
        problemes.append(f"trop d'étapes ({len(etapes)} > {max_etapes})")
    for position, etape in enumerate(etapes, start=1):
        if not isinstance(etape, dict) or not etape.get("description"):
            problemes.append(f"l'étape {position} n'a pas de description")
    return problemes


def creer_plan(agent, objectif: str, max_etapes: int = 8) -> dict | None:
    """Demande un plan au modèle, puis le vérifie avec du code."""
    message = (
        f"Découpe cet objectif en {max_etapes} étapes maximum, dans l'ordre.\n"
        f"Outils disponibles :\n{agent.outils.decrire()}\n\n"
        f"Objectif : {objectif}"
    )
    for _ in range(2):
        plan = agent.demander_structure(
            message, SCHEMA_PLAN, champs_obligatoires=["objectif", "etapes"]
        )
        if plan and not valider_plan(plan, max_etapes):
            # On normalise : numérotation propre et statut initial
            for numero, etape in enumerate(plan["etapes"], start=1):
                etape["id"] = numero
                etape["statut"] = "a_faire"
                etape["resultat"] = None
            return plan
    return None


def afficher_plan(plan: dict) -> str:
    lignes = [f"Plan : {plan['objectif']}"]
    for etape in plan["etapes"]:
        outil = f" [{etape.get('outil_suggere')}]" if etape.get("outil_suggere") else ""
        lignes.append(f"  {etape['id']}. ({etape['statut']}) {etape['description']}{outil}")
    return "\n".join(lignes)
