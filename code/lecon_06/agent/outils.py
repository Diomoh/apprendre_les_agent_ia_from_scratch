"""
agent/outils.py - Les outils de l'agent.

Leçon 05 : un outil est une fonction Python ordinaire, accompagnée d'une
description que le modèle peut lire. Le modèle DEMANDE un outil ;
c'est NOTRE code qui l'exécute.
Leçon 06 : la boîte sait produire le format « tools » attendu par l'API.
"""

import json
from datetime import datetime


class BoiteAOutils:
    """Registre des outils : nom → fonction + description + paramètres."""

    def __init__(self):
        self.outils: dict[str, dict] = {}

    def ajouter(self, nom: str, fonction, description: str, parametres: dict):
        """
        Enregistre un outil.

        `parametres` suit le format JSON Schema :
        {"type": "object", "properties": {...}, "required": [...]}
        """
        self.outils[nom] = {
            "fonction": fonction,
            "description": description,
            "parametres": parametres,
        }

    def noms(self) -> list[str]:
        return list(self.outils)

    def decrire(self) -> str:
        """Texte lisible par le modèle, à placer dans le prompt."""
        lignes = []
        for nom, outil in self.outils.items():
            proprietes = outil["parametres"].get("properties", {})
            params = ", ".join(
                f"{p} ({d.get('type', '?')}{' parmi ' + str(d['enum']) if 'enum' in d else ''})"
                for p, d in proprietes.items()
            )
            lignes.append(f"- {nom} : {outil['description']} | paramètres : {params or 'aucun'}")
        return "\n".join(lignes)

    def schemas(self) -> list[dict]:
        """Description des outils au format de l'API (champ "tools")."""
        return [
            {
                "type": "function",
                "function": {
                    "name": nom,
                    "description": outil["description"],
                    "parameters": outil["parametres"],
                },
            }
            for nom, outil in self.outils.items()
        ]

    def executer(self, nom: str, arguments: dict) -> str:
        """
        Exécute un outil et renvoie TOUJOURS une chaîne de caractères.

        Une erreur n'arrête pas le programme : elle devient un résultat
        que le modèle pourra lire.
        """
        if nom not in self.outils:
            return f"ERREUR : outil inconnu « {nom} ». Outils disponibles : {self.noms()}"
        try:
            resultat = self.outils[nom]["fonction"](**arguments)
        except Exception as erreur:  # noqa: BLE001 - on veut tout attraper ici
            return f"ERREUR pendant l'exécution de {nom} : {erreur}"
        if isinstance(resultat, str):
            return resultat
        return json.dumps(resultat, ensure_ascii=False)


# ============================================================
# Les outils eux-mêmes : des fonctions Python normales
# ============================================================

def calculatrice(a: float, b: float, operation: str) -> float:
    """Les quatre opérations de base."""
    if operation == "addition":
        return a + b
    if operation == "soustraction":
        return a - b
    if operation == "multiplication":
        return a * b
    if operation == "division":
        if b == 0:
            raise ValueError("division par zéro")
        return a / b
    raise ValueError(f"opération inconnue : {operation}")


def heure_actuelle() -> str:
    """Date et heure locales de la machine."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def boite_par_defaut() -> BoiteAOutils:
    """La boîte à outils de base de notre agent."""
    boite = BoiteAOutils()
    boite.ajouter(
        "calculatrice",
        calculatrice,
        "Fait une opération entre deux nombres.",
        {
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "Premier nombre"},
                "b": {"type": "number", "description": "Second nombre"},
                "operation": {
                    "type": "string",
                    "enum": ["addition", "soustraction", "multiplication", "division"],
                },
            },
            "required": ["a", "b", "operation"],
        },
    )
    boite.ajouter(
        "heure_actuelle",
        heure_actuelle,
        "Donne la date et l'heure actuelles.",
        {"type": "object", "properties": {}, "required": []},
    )
    return boite
