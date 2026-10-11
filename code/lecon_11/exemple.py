"""
Leçon 11 - Observer (télémétrie) et mesurer (évaluations) son agent.

Lancer depuis ce dossier :  python exemple.py
"""

import json
from pathlib import Path

import agent
from evaluations import CAS_DE_REFERENCE, lancer_evaluations

agent.TELEMETRIE.effacer()
agent.FICHIER_MEMOIRE = Path("memoire_evaluations.json")  # ne touche pas à votre vraie mémoire
llm = agent.creer_cerveau()


def preparer():
    """Avant chaque cas : mémoire longue vide (pas d'influence d'un cas sur l'autre)."""
    if agent.FICHIER_MEMOIRE.exists():
        agent.FICHIER_MEMOIRE.unlink()


print("=== Évaluations ===")
rapport = lancer_evaluations(llm, CAS_DE_REFERENCE, preparer)
print(f"\nTaux de réussite : {rapport['taux_reussite']} % ({rapport['reussis']}/{rapport['total']})")

print("\n=== Résumé de la télémétrie ===")
print(json.dumps(agent.TELEMETRIE.resume(), indent=2, ensure_ascii=False))

print("\n=== Les 3 premiers événements bruts (telemetrie.jsonl) ===")
for evenement in agent.TELEMETRIE.lire()[:3]:
    print(evenement)
