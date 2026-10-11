"""
Leçon 10 - Les garde-fous : l'agent agit, mais dans un cadre que le CODE impose.

Lancer depuis ce dossier :  python exemple.py
"""

import agent

# 1. Validation d'arguments : démonstration sans LLM
schema = agent.OUTILS["calculatrice"]["parametres"]
print("Arguments corrects   :", agent.valider_arguments(schema, {"a": 3, "b": 4, "operation": "addition"}))
print("Arguments incorrects :", agent.valider_arguments(schema, {"a": "trois", "operation": "racine", "x": 1}))

# 2. Le bac à sable : démonstration sans LLM
for chemin in ["notes/idee.txt", "../secret.txt", "/etc/passwd"]:
    try:
        agent.chemin_sur(chemin)
        print(f"Autorisé : {chemin}")
    except PermissionError as erreur:
        print(f"Bloqué   : {erreur}")

# 3. Un agent qui écrit des fichiers, avec confirmation humaine (agent.CONFIRMER)
llm = agent.creer_cerveau()
etat = agent.executer(
    llm,
    "Crée un fichier notes/courses.md avec une liste de 5 fruits de saison en automne, "
    "puis relis-le pour vérifier son contenu.",
)
print("\nRéponse :", etat["reponse_finale"])
print("Fichiers dans l'espace de travail :", agent.lister_fichiers())
