"""
Leçon 05 - Les outils : le modèle demande, le code exécute.

Lancer depuis ce dossier :  python exemple.py
"""

from agent.agent import Agent

agent = Agent()

print("Outils connus de l'agent :")
print(agent.outils.decrire())

questions = [
    "Combien font 1234 multiplié par 5678 ?",
    "Quelle heure est-il ?",
    "Pourquoi le ciel est-il bleu ?",  # aucun outil utile
]

for question in questions:
    print(f"\nQuestion : {question}")
    print("Réponse :", agent.repondre_avec_outil(question))
