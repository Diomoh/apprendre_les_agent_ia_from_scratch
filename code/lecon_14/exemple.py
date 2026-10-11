"""
Leçon 14 - Orchestration : quatre façons de faire travailler des agents ensemble.

Lancer depuis ce dossier :
    python exemple.py              (les quatre patrons)
    python exemple.py routeur      (un seul patron : pipeline | routeur | parallele | superviseur)
"""

import sys

from agent.agent import Agent
from agent.outils import BoiteAOutils
from multi.orchestration import agreger, creer_superviseur, en_parallele, pipeline, router


def specialiste(nom: str, role: str) -> Agent:
    """Un agent sans outils ni mémoire longue : il ne fait que réfléchir et rédiger."""
    return Agent(nom=nom, role=role + " Tu réponds en français, de façon concise.",
                 outils=BoiteAOutils(), outils_memoire=False)


IDEE = "Une application mobile qui aide les étudiants à planifier leurs révisions."
choix = sys.argv[1] if len(sys.argv) > 1 else "tous"

if choix in ("pipeline", "tous"):
    print("\n================ 1. PIPELINE ================")
    pipeline(
        [
            (specialiste("analyste", "Tu es analyste produit."),
             "Liste les 3 besoins principaux des utilisateurs de cette idée : {entree}"),
            (specialiste("concepteur", "Tu es concepteur produit."),
             "Propose une fonctionnalité pour chacun de ces besoins :\n{entree}"),
            (specialiste("redacteur", "Tu es rédacteur marketing."),
             "Écris un slogan et un pitch de 3 phrases à partir de :\n{entree}"),
        ],
        IDEE,
    )

if choix in ("routeur", "tous"):
    print("\n================ 2. ROUTEUR ================")
    specialistes = {
        "juriste": (specialiste("juriste", "Tu es juriste spécialisé dans le numérique."),
                    "questions de droit, RGPD, contrats, CGU"),
        "developpeur": (specialiste("developpeur", "Tu es développeur mobile senior."),
                        "questions techniques, code, architecture, performance"),
        "marketeur": (specialiste("marketeur", "Tu es responsable marketing."),
                      "prix, communication, acquisition d'utilisateurs"),
    }
    routeur = specialiste("routeur", "Tu orientes chaque demande vers le bon spécialiste.")
    for demande in [
        "Ai-je le droit de stocker les emplois du temps des étudiants ?",
        "Flutter ou React Native pour cette application ?",
    ]:
        print(f"\nDemande : {demande}")
        print(router(routeur, specialistes, demande)["reponse"])

if choix in ("parallele", "tous"):
    print("\n================ 3. PARALLÈLE ================")
    resultats = en_parallele([
        (specialiste("critique_technique", "Tu évalues la faisabilité technique."),
         f"Donne 3 risques techniques de cette idée : {IDEE}"),
        (specialiste("critique_marche", "Tu évalues le potentiel commercial."),
         f"Donne 3 risques commerciaux de cette idée : {IDEE}"),
        (specialiste("critique_usage", "Tu es designer UX."),
         f"Donne 3 risques d'adoption par les utilisateurs de cette idée : {IDEE}"),
    ])
    for r in resultats:
        print(f"\n[{r['agent']}]\n{r['sortie']}")
    synthese = agreger(specialiste("synthetiseur", "Tu synthétises des avis d'experts."),
                       "Fais une synthèse en 5 points, du risque le plus grave au moins grave.",
                       resultats)
    print(f"\n[synthèse]\n{synthese}")

if choix in ("superviseur", "tous"):
    print("\n================ 4. SUPERVISEUR ================")
    equipe = {
        "analyste": (specialiste("analyste", "Tu es analyste produit."),
                     "Identifie les besoins des utilisateurs."),
        "developpeur": (specialiste("developpeur", "Tu es développeur mobile senior."),
                        "Estime la complexité technique et propose une architecture."),
        "marketeur": (specialiste("marketeur", "Tu es responsable marketing."),
                      "Propose un positionnement et un prix."),
    }
    chef = creer_superviseur("chef_de_produit", "Tu es chef de produit.", equipe)
    print(chef.executer(f"Rédige une note de cadrage d'une page pour : {IDEE}", max_etapes=10))
