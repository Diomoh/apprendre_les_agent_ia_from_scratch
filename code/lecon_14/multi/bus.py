"""
multi/bus.py - Les deux canaux de communication entre agents.

Leçon 13 :
- BusMessages   : messagerie directe (une boîte aux lettres par agent).
- TableauPartage : un « tableau noir » (blackboard) où chacun publie et lit
                   des documents de travail, sans s'adresser à quelqu'un en particulier.
"""

from datetime import datetime

from multi.messages import Message


class BusMessages:
    def __init__(self, telemetrie=None):
        self.boites: dict[str, list[Message]] = {}
        self.historique: list[Message] = []
        self.telemetrie = telemetrie

    def inscrire(self, nom: str):
        self.boites.setdefault(nom, [])

    def participants(self) -> list[str]:
        return list(self.boites)

    def envoyer(self, message: Message) -> str:
        if message.destinataire not in self.boites:
            raise ValueError(
                f"destinataire inconnu : {message.destinataire}. Connus : {self.participants()}"
            )
        self.boites[message.destinataire].append(message)
        self.historique.append(message)
        if self.telemetrie:
            self.telemetrie.enregistrer("message", **message.to_dict())
        return f"Message {message.id} envoyé à {message.destinataire}."

    def a_des_messages(self, nom: str) -> bool:
        return bool(self.boites.get(nom))

    def prendre_suivant(self, nom: str) -> Message | None:
        """Retire et renvoie le plus ancien message de la boîte (file FIFO)."""
        boite = self.boites.get(nom)
        return boite.pop(0) if boite else None


class TableauPartage:
    def __init__(self):
        self.entrees: dict[str, dict] = {}

    def publier(self, cle: str, contenu: str, auteur: str) -> str:
        version = self.entrees.get(cle, {}).get("version", 0) + 1
        self.entrees[cle] = {
            "contenu": contenu,
            "auteur": auteur,
            "version": version,
            "horodatage": datetime.now().isoformat(timespec="seconds"),
        }
        return f"« {cle} » publié (version {version})."

    def lire(self, cle: str) -> str:
        if cle not in self.entrees:
            raise KeyError(f"rien n'est publié sous « {cle} ». Clés existantes : {self.cles()}")
        entree = self.entrees[cle]
        return f"[{cle} v{entree['version']} par {entree['auteur']}]\n{entree['contenu']}"

    def cles(self) -> list[str]:
        return list(self.entrees)
