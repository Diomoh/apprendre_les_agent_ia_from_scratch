"""
agent/outils.py - Les outils de l'agent.

Leçon 05 : un outil est une fonction Python ordinaire, accompagnée d'une
description que le modèle peut lire. Le modèle DEMANDE un outil ;
c'est NOTRE code qui l'exécute.
Leçon 06 : la boîte sait produire le format « tools » attendu par l'API.
Leçon 10 : garde-fous - arguments validés, outils sensibles soumis à
confirmation humaine, résultats tronqués.
Leçon 11 : chaque exécution d'outil est tracée (durée, statut).
"""

import json
import time
from datetime import datetime

# Leçon 10 : correspondance entre types JSON Schema et types Python
TYPES_JSON = {
    "string": (str,),
    "number": (int, float),
    "integer": (int,),
    "boolean": (bool,),
    "array": (list,),
    "object": (dict,),
}


def valider_arguments(parametres: dict, arguments: dict) -> list[str]:
    """
    Vérifie les arguments proposés par le modèle AVANT d'exécuter l'outil.
    Renvoie la liste des erreurs (vide = arguments valides).
    """
    erreurs = []
    proprietes = parametres.get("properties", {})

    for requis in parametres.get("required", []):
        if requis not in arguments:
            erreurs.append(f"argument obligatoire manquant : {requis}")

    for nom, valeur in arguments.items():
        if nom not in proprietes:
            erreurs.append(f"argument inconnu : {nom}")
            continue
        regle = proprietes[nom]
        types_attendus = TYPES_JSON.get(regle.get("type"))
        # En Python, True est aussi un int : on l'exclut explicitement
        mauvais_type = types_attendus and (
            not isinstance(valeur, types_attendus)
            or (isinstance(valeur, bool) and regle.get("type") != "boolean")
        )
        if mauvais_type:
            erreurs.append(f"{nom} doit être de type {regle['type']}")
        elif "enum" in regle and valeur not in regle["enum"]:
            erreurs.append(f"{nom} doit valoir l'une de ces valeurs : {regle['enum']}")
    return erreurs


class BoiteAOutils:
    """Registre des outils : nom → fonction + description + paramètres."""

    def __init__(self, confirmer=None, taille_max_resultat: int = 4000):
        self.outils: dict[str, dict] = {}
        # Leçon 10 : fonction appelée avant un outil sensible -> True / False
        self.confirmer = confirmer
        self.taille_max_resultat = taille_max_resultat
        # Leçon 11 : télémétrie optionnelle
        self.telemetrie = None
        self.source = "agent"

    def ajouter(
        self, nom: str, fonction, description: str, parametres: dict, sensible: bool = False
    ):
        """
        Enregistre un outil.

        `parametres` suit le format JSON Schema :
        {"type": "object", "properties": {...}, "required": [...]}
        `sensible=True` : l'outil modifie le monde réel, un humain doit valider.
        """
        self.outils[nom] = {
            "fonction": fonction,
            "description": description,
            "parametres": parametres,
            "sensible": sensible,
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
        """Exécute l'outil et trace l'exécution (leçon 11)."""
        debut = time.perf_counter()
        resultat = self._executer(nom, arguments)
        if self.telemetrie:
            if resultat.startswith("ERREUR"):
                statut = "erreur"
            elif resultat.startswith("REFUSÉ"):
                statut = "refuse"
            else:
                statut = "ok"
            self.telemetrie.enregistrer(
                "appel_outil",
                source=self.source,
                outil=nom,
                statut=statut,
                duree_s=round(time.perf_counter() - debut, 3),
            )
        return resultat

    def _executer(self, nom: str, arguments: dict) -> str:
        """
        Exécute un outil et renvoie TOUJOURS une chaîne de caractères.

        Une erreur n'arrête pas le programme : elle devient un résultat
        que le modèle pourra lire.
        """
        if nom not in self.outils:
            return f"ERREUR : outil inconnu « {nom} ». Outils disponibles : {self.noms()}"
        outil = self.outils[nom]

        # Garde-fou 1 : les arguments respectent le schéma
        erreurs = valider_arguments(outil["parametres"], arguments)
        if erreurs:
            return f"ERREUR : arguments invalides pour {nom} : {'; '.join(erreurs)}"

        # Garde-fou 2 : un humain valide les actions sensibles
        if outil["sensible"]:
            if self.confirmer is None or not self.confirmer(nom, arguments):
                return f"REFUSÉ : l'action {nom} n'a pas été autorisée par l'humain."

        try:
            resultat = outil["fonction"](**arguments)
        except Exception as erreur:  # noqa: BLE001 - on veut tout attraper ici
            return f"ERREUR pendant l'exécution de {nom} : {erreur}"
        if not isinstance(resultat, str):
            resultat = json.dumps(resultat, ensure_ascii=False)

        # Garde-fou 3 : un résultat énorme ne doit pas saturer le contexte
        if len(resultat) > self.taille_max_resultat:
            resultat = resultat[: self.taille_max_resultat] + "\n[... résultat tronqué]"
        return resultat


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


def confirmer_dans_terminal(nom: str, arguments: dict) -> bool:
    """Demande l'accord de l'humain dans le terminal (leçon 10)."""
    apercu = json.dumps(arguments, ensure_ascii=False)[:300]
    reponse = input(f"\n⚠ L'agent veut exécuter {nom}({apercu}). Autoriser ? (o/n) ")
    return reponse.strip().lower() == "o"
