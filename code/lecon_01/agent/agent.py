"""
agent/agent.py - L'agent. Ce fichier grandit de leçon en leçon.

Leçon 01 : l'agent sait seulement transmettre un texte au modèle.
"""

from cerveau.llm import ClientLLM


class Agent:
    """Pour l'instant, un « agent » qui n'est qu'un passe-plat vers le LLM."""

    def __init__(self, modele: str | None = None):
        # Leçon 01 : le cerveau (le LLM)
        self.llm = ClientLLM(modele)

    # ============================================================
    # LEÇON 01 : texte en entrée, texte en sortie
    # ============================================================

    def demander(self, message: str) -> str:
        """L'interaction la plus simple possible."""
        return self.llm.demander(message)
