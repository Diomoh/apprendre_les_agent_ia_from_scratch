"""
pipeline/simulation.py - Des réponses préparées, pour faire tourner le pipeline sans API.

Scénario : l'app de livraison du Grand Abidjan, fonctionnalité « Commande ».
Il est écrit pour montrer les deux boucles du pipeline :
- le Critique refuse la 1re version du design (sécurité sous 7), accepte la 2e ;
- le relecteur Sécurité bloque la 1re revue (numéro du client exposé, ES-03),
  Fix corrige, la 2e revue passe.
"""

PRD = {
    "fonctionnalite": "Commande",
    "objectif": "Permettre à un client du Grand Abidjan de commander une course "
    "et à un livreur à moto de l'accepter.",
    "questions_et_hypotheses": [
        "Type de livraison non précisé : hypothèse colis entre particuliers et boutiques.",
        "Paiement non précisé : hypothèse espèces à la livraison pour le MVP.",
    ],
    "stories": [
        {
            "id": "US-01",
            "en_tant_que": "client",
            "je_veux": "commander une course entre deux points de la carte",
            "afin_de": "faire livrer un colis",
            "criteres_acceptation": [
                "Le prix est affiché avant validation",
                "L'adresse comprend un point GPS et un repère en texte libre",
            ],
        },
        {
            "id": "US-02",
            "en_tant_que": "livreur",
            "je_veux": "accepter une course proposée",
            "afin_de": "la réaliser",
            "criteres_acceptation": ["Un livreur déjà en course ne peut pas en accepter une autre"],
        },
    ],
    "regles_gestion": [
        {"id": "RG-01", "texte": "Statuts dans l'ordre : créée, acceptée, récupérée, en livraison, livrée (ou annulée)."},
        {"id": "RG-02", "texte": "Le prix dépend de la zone de départ et de la zone d'arrivée (grille administrateur)."},
        {"id": "RG-03", "texte": "Un livreur n'a qu'une seule course active à la fois."},
    ],
    "exigences_securite": [
        {"id": "ES-01", "texte": "Connexion par numéro de téléphone et code OTP."},
        {"id": "ES-02", "texte": "Un livreur ne voit que ses propres courses."},
        {"id": "ES-03", "texte": "Le numéro du client n'est jamais affiché en clair au livreur."},
    ],
    "hors_perimetre": ["Paiement mobile money", "Livraison inter-villes"],
}

TACHES = [
    {
        "id": "T-01", "titre": "Statuts et prix d'une commande", "couche": "backend",
        "description": "Module livraison/commandes.py : transitions de statut et calcul du prix.",
        "regles": ["RG-01", "RG-02"], "exigences": [], "depend_de": [],
    },
    {
        "id": "T-02", "titre": "Attribution d'une course à un livreur", "couche": "backend",
        "description": "Module livraison/attribution.py : acceptation, visibilité, vue livreur.",
        "regles": ["RG-03"], "exigences": ["ES-02", "ES-03"], "depend_de": ["T-01"],
    },
    {
        "id": "T-03", "titre": "Écran de commande client", "couche": "frontend",
        "description": "Page Next.js de création de commande avec carte et repère.",
        "regles": ["RG-02"], "exigences": ["ES-01"], "depend_de": [],
    },
]


def _design(version: int) -> dict:
    design = {
        "stack": ["Django + DRF", "PostgreSQL + PostGIS", "Next.js", "React Native", "Docker"],
        "style_architecture": "Monolithe modulaire Django, une app par domaine",
        "design_system": "shadcn/ui + Tailwind",
        "modele_donnees": [
            "Commande(id, client, livreur, statut, depart, arrivee, repere, prix)",
            "Zone(id, nom, polygone)",
        ],
        "contrat_api": [
            {"methode": "POST", "chemin": "/api/commandes/", "description": "Créer une commande", "roles_autorises": ["client"]},
            {"methode": "POST", "chemin": "/api/commandes/{id}/accepter/", "description": "Accepter une course", "roles_autorises": ["livreur"]},
            {"methode": "GET", "chemin": "/api/livreur/courses/", "description": "Courses du livreur", "roles_autorises": ["livreur"]},
        ],
        "reponses_securite": [
            {"exigence": "ES-01", "mesure": "Authentification OTP par SMS, jeton JWT court"},
        ],
        "decisions": [
            {"id": "ADR-01", "decision": "Monolithe modulaire", "alternatives_ecartees": "Microservices : trop complexe pour un MVP"},
        ],
        "taches": TACHES,
    }
    if version >= 2:
        design["reponses_securite"] += [
            {"exigence": "ES-02", "mesure": "Filtre systématique par livreur connecté dans le service et la vue"},
            {"exigence": "ES-03", "mesure": "Sérialiseur livreur sans téléphone client, numéro masqué"},
        ]
    return design


COMMANDES_PY = '''"""Statuts et prix d'une commande (T-01)."""

# RG-01 : ordre des statuts
TRANSITIONS = {
    "creee": {"acceptee", "annulee"},
    "acceptee": {"recuperee", "annulee"},
    "recuperee": {"en_livraison"},
    "en_livraison": {"livree"},
}


def changer_statut(actuel: str, nouveau: str) -> str:
    """RG-01 : refuse toute transition hors de l'ordre prévu."""
    if nouveau not in TRANSITIONS.get(actuel, set()):
        raise ValueError(f"Transition interdite : {actuel} -> {nouveau}")
    return nouveau


def prix_course(zone_depart: str, zone_arrivee: str, grille: dict) -> int:
    """RG-02 : prix selon la grille (zone de départ, zone d'arrivée)."""
    try:
        return grille[(zone_depart, zone_arrivee)]
    except KeyError:
        raise ValueError("Trajet non couvert par la grille tarifaire") from None
'''

ATTRIBUTION_V1 = '''"""Attribution d'une course à un livreur (T-02)."""


def peut_accepter(courses_actives_du_livreur: int) -> bool:
    """RG-03 : une seule course active à la fois."""
    return courses_actives_du_livreur == 0


def courses_visibles(courses: list[dict], livreur_id: int) -> list[dict]:
    """ES-02 : un livreur ne voit que ses propres courses."""
    return [c for c in courses if c["livreur_id"] == livreur_id]


def vue_livreur(course: dict) -> dict:
    """Données d'une course envoyées à l'app livreur."""
    return dict(course)
'''

ATTRIBUTION_V2 = '''"""Attribution d'une course à un livreur (T-02)."""


def peut_accepter(courses_actives_du_livreur: int) -> bool:
    """RG-03 : une seule course active à la fois."""
    return courses_actives_du_livreur == 0


def courses_visibles(courses: list[dict], livreur_id: int) -> list[dict]:
    """ES-02 : un livreur ne voit que ses propres courses."""
    return [c for c in courses if c["livreur_id"] == livreur_id]


def masquer_telephone(numero: str) -> str:
    """ES-03 : seuls les deux derniers chiffres restent visibles."""
    return "*" * (len(numero) - 2) + numero[-2:]


def vue_livreur(course: dict) -> dict:
    """ES-03 : le numéro du client n'est jamais envoyé en clair au livreur."""
    vue = {cle: valeur for cle, valeur in course.items() if cle != "telephone_client"}
    if "telephone_client" in course:
        vue["telephone_client_masque"] = masquer_telephone(course["telephone_client"])
    return vue
'''

PAGE_TSX = '''// Écran de commande client (T-03) : appelle POST /api/commandes/
"use client";
import { useState } from "react";

export default function PageCommande() {
  const [repere, setRepere] = useState("");
  return (
    <form action="/api/commandes/" method="post">
      {/* Carte de sélection du départ et de l'arrivée (RG-02 : prix affiché avant validation) */}
      <input value={repere} onChange={(e) => setRepere(e.target.value)} placeholder="Repère" />
      <button type="submit">Commander</button>
    </form>
  );
}
'''

TEST_COMMANDES = '''import pytest

from livraison.commandes import changer_statut, prix_course


def test_rg_01_transition_valide():
    assert changer_statut("creee", "acceptee") == "acceptee"


def test_rg_01_transition_interdite():
    with pytest.raises(ValueError):
        changer_statut("creee", "livree")


def test_rg_02_prix_selon_les_zones():
    grille = {("Cocody", "Plateau"): 1500}
    assert prix_course("Cocody", "Plateau", grille) == 1500


def test_rg_02_trajet_hors_grille_refuse():
    with pytest.raises(ValueError):
        prix_course("Cocody", "Bingerville", {})
'''

TEST_ATTRIBUTION = '''from livraison.attribution import courses_visibles, peut_accepter


def test_rg_03_une_seule_course_active():
    assert peut_accepter(0) is True
    assert peut_accepter(1) is False


def test_es_02_livreur_ne_voit_que_ses_courses():
    courses = [{"id": 1, "livreur_id": 7}, {"id": 2, "livreur_id": 8}]
    assert courses_visibles(courses, 7) == [{"id": 1, "livreur_id": 7}]
'''

TEST_ES03 = '''from livraison.attribution import vue_livreur


def test_es_03_numero_client_jamais_en_clair():
    course = {"id": 1, "telephone_client": "0707070707"}
    vue = vue_livreur(course)
    assert "telephone_client" not in vue
    assert vue["telephone_client_masque"].endswith("07")
    assert "0707070707" not in str(vue)
'''


class Simulateur:
    """Renvoie une réponse préparée selon l'agent et le contexte."""

    def repondre(self, agent: str, contexte: dict) -> dict:
        if agent == "analyste":
            return PRD

        if agent == "architecte":
            return _design(version=contexte.get("tour", 1))

        if agent == "critique":
            if contexte.get("tour", 1) == 1:
                return {
                    "notes": {"couverture_prd": 8, "simplicite": 7, "securite": 6,
                              "coherence_stack": 8, "faisabilite": 7},
                    "objections": [
                        "ES-02 n'a aucune mesure technique dans reponses_securite.",
                        "ES-03 non traité : rien n'empêche d'envoyer le numéro du client au livreur.",
                    ],
                }
            return {
                "notes": {"couverture_prd": 9, "simplicite": 8, "securite": 8,
                          "coherence_stack": 9, "faisabilite": 8},
                "objections": [],
            }

        if agent.startswith("implementer:"):
            tache = contexte["tache"]["id"]
            if tache == "T-01":
                fichiers = [{"chemin": "livraison/__init__.py", "contenu": ""},
                            {"chemin": "livraison/commandes.py", "contenu": COMMANDES_PY}]
            elif tache == "T-02":
                fichiers = [{"chemin": "livraison/attribution.py", "contenu": ATTRIBUTION_V1}]
            else:
                fichiers = [{"chemin": "frontend/app/commande/page.tsx", "contenu": PAGE_TSX}]
            return {"fichiers": fichiers, "resume": f"Implémentation de {tache}"}

        if agent.startswith("testeur:"):
            tache = contexte["tache"]["id"]
            if tache == "T-01":
                return {"fichiers": [{"chemin": "tests/test_commandes.py", "contenu": TEST_COMMANDES}],
                        "resume": "Tests RG-01 et RG-02"}
            if tache == "T-02":
                return {"fichiers": [{"chemin": "tests/test_attribution.py", "contenu": TEST_ATTRIBUTION}],
                        "resume": "Tests RG-03 et ES-02"}
            return {"fichiers": [], "resume": "Frontend : vérifier à la main l'affichage du prix avant validation."}

        if agent.startswith("relecteur:"):
            critere = agent.split(":", 1)[1]
            if critere == "securite" and contexte.get("cycle", 0) == 0:
                return {
                    "critere": critere,
                    "bloquant": True,
                    "problemes": [
                        "livraison/attribution.py : vue_livreur renvoie telephone_client en clair (viole ES-03).",
                        "Aucun test ne vérifie ES-03.",
                    ],
                }
            return {"critere": critere, "bloquant": False, "problemes": []}

        if agent == "fix":
            return {
                "fichiers": [
                    {"chemin": "livraison/attribution.py", "contenu": ATTRIBUTION_V2},
                    {"chemin": "tests/test_es_03.py", "contenu": TEST_ES03},
                ],
                "resume": "Numéro du client masqué dans la vue livreur, test ES-03 ajouté.",
            }

        raise ValueError(f"Aucune réponse simulée pour l'agent « {agent} »")
