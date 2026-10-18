r"""
pipeline/graphe.py - Le workflow, dessiné en code.

    analyste -> architecte -> critique --(note < 8 et tours < 3)--> architecte
                                       \--> validation_design (ARRÊT : humain)
    validation_design --(corriger)--> architecte
                      \--(valide)--> binome x N en parallèle (Send)
    binome -> integration -> relecteur x 7 en parallèle (Send) -> decision_revue
    decision_revue --(problème bloquant et cycles < 2)--> fix -> integration
                   \--> merge (ARRÊT : humain) -> FIN
"""

import json

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from .etat import Etat
from .noeuds import Pipeline
from .schemas import CRITERES_REVUE, MAX_CYCLES_FIX, MAX_TOURS_DESIGN, Evaluation


def construire_graphe(pipeline: Pipeline):
    g = StateGraph(Etat)

    g.add_node("analyste", pipeline.analyste)
    g.add_node("architecte", pipeline.architecte)
    g.add_node("critique", pipeline.critique)
    g.add_node("validation_design", pipeline.validation_design)
    g.add_node("binome", pipeline.binome)
    g.add_node("integration", pipeline.integration)
    g.add_node("relecteur", pipeline.relecteur)
    g.add_node("decision_revue", pipeline.decision_revue)
    g.add_node("fix", pipeline.fix)
    g.add_node("merge", pipeline.merge)

    # -- Intake et Design --------------------------------------------------------
    g.add_edge(START, "analyste")
    g.add_edge("analyste", "architecte")
    g.add_edge("architecte", "critique")

    def apres_critique(etat):
        evaluation = Evaluation.model_validate(etat["evaluation"])
        if evaluation.est_valide() or etat["tours_design"] >= MAX_TOURS_DESIGN:
            return "validation_design"
        return "architecte"

    g.add_conditional_edges("critique", apres_critique, ["architecte", "validation_design"])

    # -- Validation, puis Build en parallèle -----------------------------------------
    def apres_validation(etat):
        if etat.get("decision_design") == "corriger":
            return "architecte"
        # Fan-out : un binôme par tâche, chacun avec SON contexte seulement.
        return [
            Send("binome", {
                "tache": tache,
                "contexte": pipeline.contexte_tache(etat, tache),
                "fonctionnalite": etat["fonctionnalite"],
            })
            for tache in etat["design"]["taches"]
        ]

    g.add_conditional_edges("validation_design", apres_validation, ["architecte", "binome"])
    g.add_edge("binome", "integration")  # fan-in : attend tous les binômes

    # -- Revue en parallèle ------------------------------------------------------------
    def lancer_revue(etat):
        code = pipeline.lire_code(pipeline.dossier(etat) / "integration")
        rapport = {k: v for k, v in etat["rapport_integration"].items()}
        commun = {
            "cycle": etat.get("cycles_fix", 0),
            "prd": json.dumps(etat["prd"], ensure_ascii=False),
            "design": json.dumps(etat["design"], ensure_ascii=False),
            "rapport": json.dumps(rapport, ensure_ascii=False)[:6000],
            "code": code,
        }
        return [Send("relecteur", {**commun, "critere": c}) for c in CRITERES_REVUE]

    g.add_conditional_edges("integration", lancer_revue, ["relecteur"])
    g.add_edge("relecteur", "decision_revue")  # fan-in : attend les 7 avis

    def apres_revue(etat):
        if pipeline.problemes_bloquants(etat) and etat.get("cycles_fix", 0) < MAX_CYCLES_FIX:
            return "fix"
        return "merge"

    g.add_conditional_edges("decision_revue", apres_revue, ["fix", "merge"])
    g.add_edge("fix", "integration")
    g.add_edge("merge", END)

    # Le checkpointer sauvegarde l'état à chaque étape : c'est lui qui permet
    # de s'arrêter pour une validation humaine puis de reprendre au même endroit.
    return g.compile(checkpointer=MemorySaver())
