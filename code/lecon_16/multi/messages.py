"""
multi/messages.py - Le format des messages échangés entre agents.

Leçon 13 : des agents qui communiquent ont besoin d'un CONTRAT,
exactement comme deux services web : qui parle, à qui, de quoi, en réponse à quoi.
"""

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime

TYPES_MESSAGE = ["tache", "resultat", "question", "reponse", "info"]


@dataclass
class Message:
    expediteur: str
    destinataire: str
    type: str  # une valeur de TYPES_MESSAGE
    contenu: str
    en_reponse_a: str | None = None  # id du message auquel on répond
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    horodatage: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    def __post_init__(self):
        if self.type not in TYPES_MESSAGE:
            raise ValueError(f"type de message inconnu : {self.type} (attendu : {TYPES_MESSAGE})")

    def to_dict(self) -> dict:
        return asdict(self)

    def pour_prompt(self) -> str:
        """Comment le message est présenté au LLM du destinataire."""
        reference = f" (en réponse au message {self.en_reponse_a})" if self.en_reponse_a else ""
        return (
            f"MESSAGE {self.id} reçu de « {self.expediteur} » - type : {self.type}{reference}\n"
            f"---\n{self.contenu}\n---"
        )
