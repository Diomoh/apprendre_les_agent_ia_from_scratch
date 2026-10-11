"""
Leçon 03 - Sorties structurées : obtenir du JSON fiable.

Lancer depuis ce dossier :  python exemple.py
"""

from agent.agent import Agent

agent = Agent()

schema = """{
  "sujet": "string",
  "niveau": "debutant" | "intermediaire" | "avance",
  "notions_cles": ["string", "..."],
  "duree_estimee_minutes": number
}"""

resultat = agent.demander_structure(
    "Je veux apprendre les chaînes de Markov, je connais déjà les probabilités de base.",
    schema,
    champs_obligatoires=["sujet", "niveau", "notions_cles", "duree_estimee_minutes"],
)

if resultat is None:
    print("Le modèle n'a pas produit de JSON valide après 3 tentatives.")
else:
    # C'est un vrai dictionnaire Python : on l'utilise comme une donnée.
    print("Type :", type(resultat))
    print("Sujet :", resultat["sujet"])
    print("Niveau :", resultat["niveau"])
    for notion in resultat["notions_cles"]:
        print(" -", notion)
    print("Durée estimée :", resultat["duree_estimee_minutes"], "minutes")
