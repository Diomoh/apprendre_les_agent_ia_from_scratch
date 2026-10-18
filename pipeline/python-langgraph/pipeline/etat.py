"""
pipeline/etat.py - L'état partagé du pipeline (le « state » LangGraph).

Chaque nœud lit l'état et renvoie seulement les clés qu'il modifie.
Les clés annotées avec `operator.add` s'ACCUMULENT au lieu d'être remplacées :
indispensable quand plusieurs binômes ou relecteurs écrivent en parallèle.
"""

import operator
from typing import Annotated, TypedDict


class Etat(TypedDict, total=False):
    # Entrée
    cahier_des_charges: str
    fonctionnalite: str

    # Intake + Design
    prd: dict
    design: dict
    evaluation: dict
    historique_design: Annotated[list, operator.add]
    tours_design: int
    commentaire_humain: str
    decision_design: str            # "valide" ou "corriger"

    # Build + Integrate
    resultats_build: Annotated[list, operator.add]
    rapport_integration: dict

    # Review + Fix + Merge
    avis_revue: Annotated[list, operator.add]
    cycles_fix: int
    historique_fix: Annotated[list, operator.add]
    statut: str                     # "fusionne", "refuse"
