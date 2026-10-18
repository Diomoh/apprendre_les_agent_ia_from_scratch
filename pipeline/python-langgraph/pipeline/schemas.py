"""
pipeline/schemas.py - Les documents que les agents s'échangent.

Chaque agent répond avec un objet JSON validé par un de ces modèles Pydantic.
C'est le « contrat » entre les étapes : si la sortie d'un agent ne respecte pas
son schéma, le pipeline le détecte tout de suite au lieu de propager l'erreur.

Les identifiants (US-xx, RG-xx, ES-xx, T-xx) sont uniques dans tout le projet :
c'est ce qui permet de suivre une règle du PRD jusqu'au test qui la prouve.
"""

from typing import Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Réglages du pipeline (les garde-fous sont dans le CODE, pas dans un prompt)
# ---------------------------------------------------------------------------

SEUIL_DESIGN = 8.0          # moyenne minimale exigée par le Critique
SEUIL_SECURITE = 7.0        # critère bloquant : sécurité sous 7 = correction obligatoire
MAX_TOURS_DESIGN = 3        # au-delà, on transmet à l'humain avec les objections restantes
MAX_CYCLES_FIX = 2          # nombre maximal de boucles Revue -> Fix

CRITERES_REVUE = [
    "conformite_prd",       # chaque critère d'acceptation, RG et ES est couvert
    "exactitude",           # le code fait ce qu'il dit
    "tests",                # au moins un test par RG et par ES
    "securite",             # les ES-xx sont respectées, pas de faille évidente
    "architecture",         # le code suit le dossier d'architecture
    "production",           # erreurs gérées, pas de secret dans le code, performance
    "second_avis",          # relecture générale, idéalement par un autre modèle
]


# ---------------------------------------------------------------------------
# 1. PRD = spécifications fonctionnelles (produit par l'Analyste)
# ---------------------------------------------------------------------------

class Story(BaseModel):
    id: str = Field(description="Identifiant unique, ex. US-01")
    en_tant_que: str
    je_veux: str
    afin_de: str
    criteres_acceptation: list[str]


class Regle(BaseModel):
    id: str = Field(description="Identifiant unique, ex. RG-01")
    texte: str


class Exigence(BaseModel):
    id: str = Field(description="Identifiant unique, ex. ES-01")
    texte: str


class PRD(BaseModel):
    fonctionnalite: str
    objectif: str
    questions_et_hypotheses: list[str] = Field(
        default_factory=list,
        description="Ce que le cahier des charges ne dit pas, et l'hypothèse retenue",
    )
    stories: list[Story]
    regles_gestion: list[Regle]
    exigences_securite: list[Exigence]
    hors_perimetre: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# 2. Dossier d'architecture = spécifications techniques (produit par l'Architecte)
# ---------------------------------------------------------------------------

class Endpoint(BaseModel):
    methode: str
    chemin: str
    description: str
    roles_autorises: list[str] = Field(default_factory=list)


class ReponseSecurite(BaseModel):
    exigence: str = Field(description="Identifiant ES-xx traité")
    mesure: str


class Decision(BaseModel):
    id: str = Field(description="Identifiant unique, ex. ADR-01")
    decision: str
    alternatives_ecartees: str


class Tache(BaseModel):
    id: str = Field(description="Identifiant unique, ex. T-01")
    titre: str
    couche: Literal["backend", "frontend"]
    description: str
    regles: list[str] = Field(default_factory=list, description="RG-xx couvertes")
    exigences: list[str] = Field(default_factory=list, description="ES-xx couvertes")
    depend_de: list[str] = Field(default_factory=list)


class Design(BaseModel):
    stack: list[str]
    style_architecture: str
    design_system: str
    modele_donnees: list[str]
    contrat_api: list[Endpoint]
    reponses_securite: list[ReponseSecurite]
    decisions: list[Decision]
    taches: list[Tache]


# ---------------------------------------------------------------------------
# 3. Évaluation du Critique
# ---------------------------------------------------------------------------

class Notes(BaseModel):
    couverture_prd: float = Field(ge=0, le=10)
    simplicite: float = Field(ge=0, le=10)
    securite: float = Field(ge=0, le=10)
    coherence_stack: float = Field(ge=0, le=10)
    faisabilite: float = Field(ge=0, le=10)


class Evaluation(BaseModel):
    notes: Notes
    objections: list[str] = Field(
        default_factory=list,
        description="Chaque objection désigne un défaut précis et corrigeable",
    )

    def moyenne(self) -> float:
        n = self.notes
        valeurs = [n.couverture_prd, n.simplicite, n.securite, n.coherence_stack, n.faisabilite]
        return round(sum(valeurs) / len(valeurs), 2)

    def est_valide(self) -> bool:
        """La règle de validation est du CODE : le modèle note, le code décide."""
        return self.moyenne() >= SEUIL_DESIGN and self.notes.securite >= SEUIL_SECURITE


# ---------------------------------------------------------------------------
# 4. Code produit par les binômes et par Fix
# ---------------------------------------------------------------------------

class Fichier(BaseModel):
    chemin: str = Field(description="Chemin relatif, ex. livraison/tarifs.py")
    contenu: str


class Livraison(BaseModel):
    fichiers: list[Fichier]
    resume: str


# ---------------------------------------------------------------------------
# 5. Avis d'un relecteur
# ---------------------------------------------------------------------------

class Avis(BaseModel):
    critere: str
    bloquant: bool
    problemes: list[str] = Field(default_factory=list)
