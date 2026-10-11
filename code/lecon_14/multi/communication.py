"""
multi/communication.py - Donner aux agents les moyens de communiquer.

Leçon 13 : la communication passe par des OUTILS. Le modèle décide à qui
écrire et quoi publier ; le code fixe l'expéditeur (l'identité vient du
code, jamais du modèle) et vérifie les destinataires.
"""

from multi.bus import BusMessages, TableauPartage
from multi.messages import TYPES_MESSAGE, Message


def ajouter_outils_communication(agent, bus: BusMessages, tableau: TableauPartage):
    bus.inscrire(agent.nom)

    def envoyer_message(destinataire: str, type: str, contenu: str) -> str:
        return bus.envoyer(Message(agent.nom, destinataire, type, contenu))

    def publier(cle: str, contenu: str) -> str:
        return tableau.publier(cle, contenu, auteur=agent.nom)

    agent.outils.ajouter(
        "envoyer_message",
        envoyer_message,
        "Envoie un message à un autre participant.",
        {
            "type": "object",
            "properties": {
                "destinataire": {"type": "string", "description": "nom du participant"},
                "type": {"type": "string", "enum": TYPES_MESSAGE},
                "contenu": {"type": "string"},
            },
            "required": ["destinataire", "type", "contenu"],
        },
    )
    agent.outils.ajouter(
        "publier_sur_tableau",
        publier,
        "Publie (ou met à jour) un document de travail sur le tableau partagé.",
        {
            "type": "object",
            "properties": {
                "cle": {"type": "string", "description": "nom court du document, ex : plan"},
                "contenu": {"type": "string"},
            },
            "required": ["cle", "contenu"],
        },
    )
    agent.outils.ajouter(
        "lire_tableau",
        tableau.lire,
        "Lit un document publié sur le tableau partagé.",
        {"type": "object", "properties": {"cle": {"type": "string"}}, "required": ["cle"]},
    )


def faire_circuler(agents: list, bus: BusMessages, max_messages: int = 20) -> int:
    """
    Le « facteur » : tant qu'un agent a du courrier, on le lui donne à traiter.
    Personne ne dirige : ce sont les agents qui décident à qui écrire.

    Renvoie le nombre de messages traités. S'arrête à `max_messages` (garde-fou).
    """
    traites = 0
    while traites < max_messages:
        en_attente = [agent for agent in agents if bus.a_des_messages(agent.nom)]
        if not en_attente:
            break
        for agent in en_attente:
            message = bus.prendre_suivant(agent.nom)
            print(f"\n📨 {message.expediteur} → {agent.nom} [{message.type}] {message.contenu[:80]}")
            agent.executer(message.pour_prompt(), memoriser_echange=False)
            traites += 1
    return traites
