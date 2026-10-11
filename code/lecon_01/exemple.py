"""
Leçon 01 - Parler à un modèle.

Lancer depuis ce dossier :  python exemple.py
"""

from agent.agent import Agent

agent = Agent()

print("Modèle utilisé :", agent.llm.modele)

reponse = agent.demander("Qu'est-ce qu'un agent IA ? Réponds en 3 phrases.")
print("\nRéponse :\n", reponse)

# Les tokens consommés par cet appel (renvoyés par l'API)
print("\nConsommation :", agent.llm.derniere_utilisation)

# Même question, deux fois, avec une température élevée : les réponses diffèrent.
for essai in range(2):
    texte = agent.llm.demander("Qu'est-ce qu'un agent IA ? Réponds en 3 phrases.", temperature=1.0)
    print(f"\nEssai {essai + 1} (température 1.0) :", texte)
