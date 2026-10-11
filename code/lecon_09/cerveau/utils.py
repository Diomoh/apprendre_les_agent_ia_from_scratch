"""
cerveau/utils.py - Petits outils ennuyeux et prévisibles.

Leçon 03 : extraire et valider du JSON dans la réponse d'un modèle.
"""

import json


def lire_json(texte: str) -> dict | list | None:
    """Essaie de lire du JSON ; renvoie None en cas d'échec (jamais d'exception)."""
    try:
        return json.loads(texte)
    except (json.JSONDecodeError, TypeError):
        return None


def extraire_json(texte: str) -> dict | None:
    """
    Extrait un objet JSON d'une réponse de modèle, même « sale ».

    Les modèles ajoutent parfois des blocs ```json ... ``` ou une phrase
    avant / après le JSON. On les retire avant de lire.
    """
    if not texte:
        return None

    texte = texte.strip()

    # 1. Retirer un éventuel bloc de code markdown
    if texte.startswith("```"):
        texte = texte.split("\n", 1)[1] if "\n" in texte else ""
        if texte.rstrip().endswith("```"):
            texte = texte.rstrip()[:-3]
        texte = texte.strip()

    # 2. Essai direct
    resultat = lire_json(texte)
    if isinstance(resultat, dict):
        return resultat

    # 3. Prendre ce qui se trouve entre la première { et la dernière }
    debut, fin = texte.find("{"), texte.rfind("}")
    if debut != -1 and fin > debut:
        resultat = lire_json(texte[debut : fin + 1])
        if isinstance(resultat, dict):
            return resultat

    return None


def champs_manquants(donnees: dict, champs_obligatoires: list[str]) -> list[str]:
    """Renvoie la liste des champs obligatoires absents du dictionnaire."""
    return [champ for champ in champs_obligatoires if champ not in donnees]
