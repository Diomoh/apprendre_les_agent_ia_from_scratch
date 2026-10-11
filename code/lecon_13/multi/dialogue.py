"""
multi/dialogue.py - Deux agents qui se parlent.

Leçon 12 : la forme la plus simple de multi-agents. Le message de l'un
devient l'entrée de l'autre. Chacun garde son rôle, ses outils, sa mémoire.
"""


def dialogue(agent_a, agent_b, message_initial: str, tours: int = 2) -> list[dict]:
    """
    agent_a reçoit le message initial, répond ; agent_b lit cette réponse,
    répond à son tour ; et ainsi de suite pendant `tours` allers-retours.

    Renvoie la transcription : [{"agent": nom, "message": texte}, ...]
    """
    transcription = []
    message = message_initial

    for _ in range(tours):
        for agent in (agent_a, agent_b):
            message = agent.executer(message)
            transcription.append({"agent": agent.nom, "message": message})
            print(f"\n[{agent.nom}]\n{message}")

    return transcription
