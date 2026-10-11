"""
agent/agent.py - L'agent. Ce fichier grandit de leçon en leçon.

Leçon 01 : l'agent sait transmettre un texte au modèle.
Leçon 02 : l'agent a un rôle (prompt système) et peut tenir une conversation.
"""

from cerveau.llm import ClientLLM


class Agent:
    """Un agent qui a désormais un rôle et un historique de conversation."""

    def __init__(self, modele: str | None = None):
        # Leçon 01 : le cerveau (le LLM)
        self.llm = ClientLLM(modele)

        # Leçon 02 : le rôle de l'agent
        self.prompt_systeme = (
            "Tu es un assistant IA calme, précis et serviable. "
            "Tu expliques simplement, sans jargon inutile. "
            "Tu dis honnêtement quand tu ne sais pas. Tu réponds en français."
        )

        # Leçon 02 : l'historique de la conversation (le modèle, lui, ne retient rien)
        self.historique: list[dict] = []

    # ============================================================
    # LEÇON 01 : texte en entrée, texte en sortie
    # ============================================================

    def demander(self, message: str) -> str:
        """L'interaction la plus simple possible."""
        return self.llm.demander(message)

    # ============================================================
    # LEÇON 02 : rôle (prompt système) et conversation
    # ============================================================

    def demander_avec_role(self, message: str) -> str:
        """Une question, avec le prompt système placé en tête."""
        messages = [
            {"role": "system", "content": self.prompt_systeme},
            {"role": "user", "content": message},
        ]
        return self.llm.discuter(messages)

    def discuter(self, message: str) -> str:
        """
        Conversation sur plusieurs tours.

        Le LLM n'a aucune mémoire entre deux appels : c'est NOUS qui lui
        renvoyons tout l'historique à chaque fois.
        """
        self.historique.append({"role": "user", "content": message})

        messages = [{"role": "system", "content": self.prompt_systeme}] + self.historique
        reponse = self.llm.discuter(messages)

        self.historique.append({"role": "assistant", "content": reponse})
        return reponse

    def oublier_conversation(self):
        """Repart d'une conversation vide."""
        self.historique = []
