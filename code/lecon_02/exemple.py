"""
Leçon 02 - Donner un rôle au modèle et tenir une conversation.

Lancer depuis ce dossier :  python exemple.py
"""

from agent.agent import Agent

agent = Agent()
question = "Qu'est-ce qu'un agent IA ?"

# 1. Sans rôle (leçon 01)
print("=== Sans prompt système ===")
print(agent.demander(question))

# 2. Avec le rôle par défaut
print("\n=== Avec le prompt système par défaut ===")
print(agent.demander_avec_role(question))

# 3. Même modèle, autre rôle : le comportement change
agent.prompt_systeme = (
    "Tu expliques tout à un enfant de 8 ans, avec une image du quotidien. "
    "Deux phrases maximum. Tu réponds en français."
)
print("\n=== Rôle « explique à un enfant » ===")
print(agent.demander_avec_role(question))

# 4. Conversation sur plusieurs tours : l'historique est renvoyé à chaque appel
agent.prompt_systeme = "Tu es un assistant concis. Tu réponds en français."
print("\n=== Conversation ===")
print("Agent :", agent.discuter("Je m'appelle Awa et je suis développeuse Python."))
print("Agent :", agent.discuter("Comment je m'appelle et quel est mon métier ?"))

print("\nHistorique envoyé au modèle :")
for message in agent.historique:
    print(f"  [{message['role']}] {message['content'][:70]}")
