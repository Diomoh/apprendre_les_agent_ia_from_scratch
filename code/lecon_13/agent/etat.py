"""
agent/etat.py - L'état de l'agent.

Leçon 07 : l'état est explicite et inspectable. Pas de magie cachée
dans le modèle : on sait à tout moment à quelle étape on est et ce qui s'est passé.
"""


class EtatAgent:
    """Ce que l'agent sait de sa propre exécution en cours."""

    def __init__(self):
        self.reinitialiser()

    def reinitialiser(self):
        """Repart de zéro pour une nouvelle tâche."""
        self.etapes = 0
        self.termine = False
        self.reponse_finale: str | None = None
        self.journal: list[dict] = []

    def nouvelle_etape(self):
        self.etapes += 1

    def noter(self, type_evenement: str, detail):
        """Ajoute une ligne au journal (décision, action, observation...)."""
        self.journal.append({"etape": self.etapes, "type": type_evenement, "detail": detail})

    def terminer(self, reponse_finale: str):
        self.termine = True
        self.reponse_finale = reponse_finale

    def to_dict(self) -> dict:
        return {
            "etapes": self.etapes,
            "termine": self.termine,
            "reponse_finale": self.reponse_finale,
            "journal": self.journal,
        }

    def __repr__(self) -> str:
        return f"EtatAgent(etapes={self.etapes}, termine={self.termine})"
