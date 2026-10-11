"""
Leçon 09 - Planifier : le plan est une donnée qu'on lit, modifie, puis exécute.

Lancer depuis ce dossier :  python exemple.py
"""

import agent

# Le même catalogue FICTIF que dans la leçon 07
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


agent.ajouter_outil(
    "consulter_catalogue",
    consulter_catalogue,
    "Donne le prix hors taxes et le stock d'un produit de la boutique.",
    {"produit": {"type": "string"}},
    ["produit"],
)

llm = agent.creer_cerveau()
objectif = (
    "Prépare un devis daté pour 3 claviers, 2 écrans et 1 souris, avec le total TTC "
    "(TVA 20 %), en signalant les produits en rupture de stock."
)

# 1. Planifier (rien n'est exécuté)
plan = agent.planifier(llm, objectif)
if plan is None:
    raise SystemExit("Impossible d'obtenir un plan valide.")
print(agent.afficher_plan(plan))

# 2. Le plan est une donnée : un humain (ou du code) peut le relire et le modifier
reponse = input("\nExécuter ce plan ? (o/n) ").strip().lower()
if reponse != "o":
    raise SystemExit("Plan abandonné.")

# 3. Exécuter
resultat = agent.executer_plan(llm, plan)
print("\n" + agent.afficher_plan(plan))
print("\n=== Réponse finale ===\n", resultat)
