"""
Leçon 06 - Function calling natif : l'API gère le format des appels d'outils.

Lancer depuis ce dossier :  python exemple.py
"""

import json

from agent.agent import Agent

agent = Agent()

print("Ce que l'API reçoit dans le champ « tools » :")
print(json.dumps(agent.outils.schemas()[0], indent=2, ensure_ascii=False))

questions = [
    "Combien font 1234 multiplié par 5678 ?",
    "Quelle heure est-il, et combien font 365 fois 24 ?",  # deux outils d'un coup
    "Pourquoi le ciel est-il bleu ?",  # aucun outil
]

for question in questions:
    print(f"\nQuestion : {question}")
    print("Réponse :", agent.repondre_avec_outils_natifs(question))
