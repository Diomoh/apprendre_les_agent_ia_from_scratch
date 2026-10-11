"""
Leçon 07 - La boucle agentique : l'agent enchaîne plusieurs outils tout seul.

Lancer depuis ce dossier :  python exemple.py
"""

import agent

# Un petit catalogue FICTIF, juste pour la démonstration.
CATALOGUE = {
    "clavier": {"prix_ht": 45.0, "stock": 12},
    "souris": {"prix_ht": 19.5, "stock": 0},
    "ecran": {"prix_ht": 189.0, "stock": 4},
}


def consulter_catalogue(produit: str) -> dict:
    produit = produit.lower().strip()
    if produit not in CATALOGUE:
        raise ValueError(f"produit inconnu, produits existants : {list(CATALOGUE)}")
    return CATALOGUE[produit]


# On ajoute un outil au registre de agent.py, sans modifier ce fichier
agent.ajouter_outil(
    "consulter_catalogue",
    consulter_catalogue,
    "Donne le prix hors taxes et le stock d'un produit de la boutique.",
    {"produit": {"type": "string", "description": "ex : clavier"}},
    ["produit"],
)

llm = agent.creer_cerveau()
objectif = (
    "Un client veut 3 claviers et 2 écrans. Quel est le total TTC avec une TVA de 20 % ? "
    "Vérifie aussi que le stock est suffisant."
)

print("Objectif :", objectif, "\n")
etat = agent.executer(llm, objectif, max_etapes=8)

print("\nRéponse finale :\n", etat["reponse_finale"])
print("\nJournal de l'exécution :")
for ligne in etat["journal"]:
    print(f"  étape {ligne['etape']} | {ligne['type']} | {ligne['detail']}")
print(f"\nÉtat : {etat['etapes']} étapes, terminé = {etat['termine']}")
