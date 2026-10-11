"""
Leçon 08 - La mémoire : courte (la conversation) et longue (un fichier JSON).

Lancer depuis ce dossier :  python exemple.py
Relancez-le une deuxième fois : l'agent se souviendra de vous (fichier memoire_longue.json).
"""

import agent

llm = agent.creer_cerveau()
historique = []  # la mémoire courte : une simple liste de messages

print("Mémoire longue au démarrage :", agent.charger_memoire())

# Mémoire courte : l'agent suit la conversation
etat = agent.executer(llm, "Bonjour ! Je m'appelle Awa, je code en Python et je préfère les réponses courtes.", historique)
print("\nAgent :", etat["reponse_finale"])
etat = agent.executer(llm, "Rappelle-moi mon prénom ?", historique)
print("\nAgent :", etat["reponse_finale"])

# Mémoire longue : on vide la mémoire courte pour simuler une nouvelle session
historique.clear()
print("\n--- Nouvelle session (mémoire courte vidée) ---")
etat = agent.executer(llm, "Quel langage est-ce que j'utilise ?", historique)
print("\nAgent :", etat["reponse_finale"])

print("\nFaits stockés sur disque :", agent.charger_memoire())
