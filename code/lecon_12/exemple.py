"""
Leçon 12 - Plusieurs agents : même code, rôles et outils différents.

Lancer depuis ce dossier :  python exemple.py
"""

from agent.agent import Agent
from agent.outils import BoiteAOutils
from multi.dialogue import dialogue


def compter_mots(texte: str) -> int:
    return len(texte.split())


# Le rédacteur n'a besoin d'aucun outil
redacteur = Agent(
    nom="redacteur",
    role=(
        "Tu es rédacteur web. Tu écris des fiches produit claires et vendeuses, "
        "en français. Quand tu reçois des remarques, tu renvoies UNIQUEMENT la "
        "nouvelle version complète du texte."
    ),
    outils=BoiteAOutils(),
    outils_memoire=False,
)

# Le relecteur a un outil que le rédacteur n'a pas
outils_relecteur = BoiteAOutils()
outils_relecteur.ajouter(
    "compter_mots",
    compter_mots,
    "Compte le nombre de mots d'un texte.",
    {"type": "object", "properties": {"texte": {"type": "string"}}, "required": ["texte"]},
)
relecteur = Agent(
    nom="relecteur",
    role=(
        "Tu es relecteur exigeant. Une fiche produit doit faire moins de 80 mots "
        "(vérifie avec compter_mots), sans superlatif vide, avec un bénéfice concret. "
        "Tu réponds par 2 ou 3 remarques précises, ou par « VALIDÉ » si tout est bon."
    ),
    outils=outils_relecteur,
    outils_memoire=False,
)

print(redacteur)
print(relecteur)

transcription = dialogue(
    redacteur,
    relecteur,
    "Écris la fiche produit d'une gourde isotherme en inox de 750 ml.",
    tours=2,
)

print(f"\n{len(transcription)} messages échangés.")
