"""
Leçon 15 - Orchestration avancée : graphe de tâches, revue, contrôle humain.

Projet : produire un mini-guide « Bien démarrer avec Git » à plusieurs agents.

Lancer depuis ce dossier :  python exemple.py
                     ou :   python exemple.py --auto   (sans question à l'humain)
"""

import sys

from agent.agent import Agent
from agent.outils import BoiteAOutils
from multi.bus import TableauPartage
from multi.graphe import GrapheTaches, Tache, executeur_avec_revue, point_de_controle

AUTO = "--auto" in sys.argv


def membre(nom: str, role: str) -> Agent:
    return Agent(nom=nom, role=role + " Tu réponds en français.", outils=BoiteAOutils(),
                 outils_memoire=False)


agents = {
    "pedagogue": membre("pedagogue", "Tu es formateur, tu conçois des parcours d'apprentissage."),
    "expert": membre("expert", "Tu es expert Git, précis sur les commandes."),
    "redacteur": membre("redacteur", "Tu es rédacteur technique, clair et concret."),
    "relecteur": membre("relecteur", "Tu es relecteur technique exigeant sur l'exactitude."),
}

graphe = GrapheTaches()
graphe.ajouter(Tache("public", "pedagogue",
                     "Décris en 5 lignes le public débutant visé et 3 objectifs d'apprentissage."))
graphe.ajouter(Tache("commandes", "expert",
                     "Liste les 8 commandes Git indispensables au débutant, une ligne chacune."))
graphe.ajouter(Tache("plan", "pedagogue",
                     "Propose le plan du guide (5 sections maximum).",
                     depend_de=["public", "commandes"]))
graphe.ajouter(Tache("guide", "redacteur",
                     "Rédige le guide complet (500 mots maximum) en suivant le plan.",
                     depend_de=["plan", "commandes"],
                     executeur=executeur_avec_revue("relecteur", max_tours=2)))

print("Graphe (Mermaid) :\n" + graphe.en_mermaid())
print("\nVagues d'exécution :", graphe.vagues())

erreurs = graphe.verifier(agents)
if erreurs:
    raise SystemExit(f"Graphe invalide : {erreurs}")

tableau = TableauPartage()

# On exécute d'abord tout sauf le guide, pour placer un contrôle humain avant la rédaction
guide = graphe.taches.pop("guide")
graphe.executer(agents, tableau=tableau)

if not point_de_controle("Plan du guide", graphe.taches["plan"].resultat or "", automatique=AUTO):
    raise SystemExit("Arrêt demandé par l'humain.")

graphe.ajouter(guide)
graphe.executer(agents, tableau=tableau)  # les tâches déjà terminées ne sont pas relancées

print("\n" + graphe.afficher())
print("\n=== Guide ===\n", graphe.taches["guide"].resultat)
