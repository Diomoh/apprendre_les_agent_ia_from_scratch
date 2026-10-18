"""
main.py - Lancer le pipeline sur une fonctionnalité.

    python main.py --cahier exemples/livraison_abidjan.md --fonctionnalite Commande --simulation
    python main.py --cahier mon_cahier.md --fonctionnalite "Suivi temps réel"

Le pipeline s'arrête deux fois pour vous : après le design, puis avant la fusion.
Répondez « ok » pour valider, ou tapez votre correction.
"""

import argparse
import json
from pathlib import Path

from langgraph.types import Command

from pipeline import ClientLLM, Pipeline, construire_graphe
from pipeline.documents import slug


def afficher_demande(demande: dict) -> None:
    print("\n" + "=" * 70)
    print(f"VALIDATION HUMAINE : {demande['message']}")
    for cle, valeur in demande.items():
        if cle in ("etape", "message"):
            continue
        if isinstance(valeur, list):
            print(f"  {cle} :")
            for element in valeur or ["(aucun)"]:
                print(f"    - {element}")
        else:
            print(f"  {cle} : {valeur}")
    print("=" * 70)


def demander_reponse(demande: dict, auto: bool) -> dict:
    if auto:
        print("  -> validation automatique (--auto-valider)")
        return {"decision": "ok"}
    texte = input("Votre réponse (« ok » pour valider, sinon votre correction) : ").strip()
    if texte.lower() in ("", "ok", "oui"):
        return {"decision": "ok"}
    if demande["etape"] == "merge":
        return {"decision": "refuser", "commentaire": texte}
    return {"decision": "corriger", "commentaire": texte}


def executer(cahier: str, fonctionnalite: str, simulation: bool, auto: bool, sortie: str) -> dict:
    client = ClientLLM(simulation=simulation)
    pipeline = Pipeline(client, sortie)
    graphe = construire_graphe(pipeline)
    config = {"configurable": {"thread_id": slug(fonctionnalite)}}

    resultat = graphe.invoke({"cahier_des_charges": cahier, "fonctionnalite": fonctionnalite}, config)
    while "__interrupt__" in resultat:
        demande = resultat["__interrupt__"][0].value
        afficher_demande(demande)
        resultat = graphe.invoke(Command(resume=demander_reponse(demande, auto)), config)

    bilan = client.bilan()
    print(f"\nStatut : {resultat.get('statut')} | appels LLM : {bilan['appels']} | "
          f"tokens : {bilan['tokens_entree']} en entrée, {bilan['tokens_sortie']} en sortie")
    print(f"Livrables : {pipeline.dossier(fonctionnalite)}")
    return resultat


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline multi-agents de développement")
    parser.add_argument("--cahier", required=True, help="Fichier texte ou Markdown du cahier des charges")
    parser.add_argument("--fonctionnalite", required=True, help="La fonctionnalité traitée par ce passage")
    parser.add_argument("--simulation", action="store_true", help="Réponses préparées, sans API")
    parser.add_argument("--auto-valider", action="store_true", help="Valide automatiquement les deux arrêts")
    parser.add_argument("--sortie", default="sortie", help="Dossier des livrables")
    args = parser.parse_args()

    cahier = Path(args.cahier).read_text(encoding="utf-8")
    executer(cahier, args.fonctionnalite, args.simulation, args.auto_valider, args.sortie)


if __name__ == "__main__":
    main()
