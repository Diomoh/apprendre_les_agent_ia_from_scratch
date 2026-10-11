"""
Leçon 04 - Décider : le modèle choisit, le code agit.

Exemple : un routeur de support client. Le LLM classe la demande,
puis le CODE choisit la fonction à exécuter.

Lancer depuis ce dossier :  python exemple.py
"""

from agent.agent import Agent

agent = Agent()
agent.prompt_systeme = "Tu tries les messages du support client d'une boutique en ligne."

CATEGORIES = ["probleme_livraison", "remboursement", "question_produit", "autre"]


# Chaque catégorie correspond à une fonction Python ordinaire (le « code agit »)
def traiter_livraison(message):
    return "→ Transmis au service logistique (suivi de colis)."


def traiter_remboursement(message):
    return "→ Ouverture d'un dossier de remboursement."


def traiter_question_produit(message):
    agent.prompt_systeme = "Tu es un vendeur courtois. Réponds en 2 phrases."
    return "→ " + agent.demander_avec_role(message)


def traiter_autre(message):
    return "→ Transmis à un humain."


ROUTES = {
    "probleme_livraison": traiter_livraison,
    "remboursement": traiter_remboursement,
    "question_produit": traiter_question_produit,
    "autre": traiter_autre,
}

messages_clients = [
    "Mon colis devait arriver lundi et je n'ai toujours rien.",
    "Le casque reçu est cassé, je veux être remboursé.",
    "Est-ce que ce casque fonctionne avec un iPhone ?",
    "Vous recrutez des stagiaires ?",
]

for message in messages_clients:
    agent.prompt_systeme = "Tu tries les messages du support client d'une boutique en ligne."
    choix = agent.decider(message, CATEGORIES)
    print(f"\nClient : {message}")

    if choix is None:
        print("Décision impossible → transmis à un humain.")
        continue

    print(f"Décision : {choix['decision']} ({choix['raison']})")
    print(ROUTES[choix["decision"]](message))
