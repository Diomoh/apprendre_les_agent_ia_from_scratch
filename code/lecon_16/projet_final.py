"""
Leçon 16 - Projet final : une équipe technique de 7 agents construit une application.

Lancer depuis ce dossier :
    python projet_final.py
    python projet_final.py --auto                  (aucune question : démo sans surveillance)
    python projet_final.py --brief "Votre besoin client ici"

Les livrables sont écrits dans livrables/projet_<date>/.

⚠ Le testeur EXÉCUTE le code généré (pytest). Sans --auto, vous devez l'autoriser
à chaque fois. Avec --auto, tout est autorisé : faites-le dans une machine
virtuelle ou un conteneur.
"""

import argparse

from equipe.orchestrateur import lancer_projet

BRIEF_PAR_DEFAUT = (
    "Nous voulons une petite application web de gestion de tâches pour une équipe. "
    "On doit pouvoir créer une tâche (titre obligatoire, description facultative), "
    "voir la liste des tâches, marquer une tâche comme terminée, la modifier et la "
    "supprimer, et filtrer la liste entre tâches à faire et tâches terminées. "
    "Les données doivent être conservées quand on redémarre le serveur."
)

parser = argparse.ArgumentParser(description="Équipe technique d'agents IA")
parser.add_argument("--brief", default=BRIEF_PAR_DEFAUT, help="le besoin du client")
parser.add_argument("--auto", action="store_true",
                    help="valide automatiquement les points de contrôle ET l'exécution des tests")
args = parser.parse_args()


def confirmer(nom_outil: str, arguments: dict) -> bool:
    """
    Politique de confirmation de l'équipe :
    - écrire un fichier : autorisé (bac à sable + droits limités par dossier) ;
    - tout autre outil sensible (lancer les tests = exécuter du code) : on demande.
    """
    if nom_outil == "ecrire_fichier" or args.auto:
        return True
    reponse = input(f"\n⚠ L'agent veut exécuter « {nom_outil} ». Autoriser ? (o/n) ")
    return reponse.strip().lower() == "o"


resultat = lancer_projet(args.brief, automatique=args.auto, confirmer=confirmer)

print(f"\n📁 Livrables : {resultat['racine']}")
print("Pour essayer l'application générée (si elle a été produite) :")
print(f"    cd {resultat['racine']} && python -m backend.serveur")
print("    puis ouvrez http://127.0.0.1:8000")
