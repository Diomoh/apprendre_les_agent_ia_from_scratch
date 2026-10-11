"""
multi/orchestration.py - Les patrons d'orchestration.

Leçon 14 : à la leçon 13, personne ne dirigeait. Ici, un CHEF D'ORCHESTRE
(du code ou un agent) décide qui travaille, quand, et avec quelles entrées.

Quatre patrons :
1. pipeline      : A → B → C, la sortie de l'un est l'entrée du suivant.
2. router        : un agent classe la demande, un seul spécialiste la traite.
3. en_parallele  : plusieurs agents travaillent en même temps, on agrège.
4. superviseur   : un agent délègue à des sous-agents qu'il utilise comme des outils.
"""

from concurrent.futures import ThreadPoolExecutor

from agent.agent import Agent
from agent.outils import BoiteAOutils


# ------------------------------------------------------------
# 1. Pipeline séquentiel
# ------------------------------------------------------------

def pipeline(etapes: list[tuple], entree: str) -> list[dict]:
    """
    etapes : [(agent, "consigne avec {entree}"), ...]
    Chaque agent reçoit la sortie du précédent à la place de {entree}.
    """
    traces = []
    courant = entree
    for agent, consigne in etapes:
        courant = agent.executer(consigne.format(entree=courant), memoriser_echange=False)
        traces.append({"agent": agent.nom, "sortie": courant})
        print(f"\n[{agent.nom}]\n{courant}")
    return traces


# ------------------------------------------------------------
# 2. Routeur
# ------------------------------------------------------------

def router(routeur: Agent, specialistes: dict[str, tuple], demande: str) -> dict:
    """
    specialistes : {"nom": (agent, "description de sa spécialité"), ...}
    Le routeur utilise decider() (leçon 04) : un choix dans une liste fermée.
    """
    catalogue = "\n".join(f"- {nom} : {desc}" for nom, (_, desc) in specialistes.items())
    choix = routeur.decider(
        f"Spécialistes disponibles :\n{catalogue}\n\nDemande à confier : {demande}",
        list(specialistes),
    )
    if choix is None:
        return {"specialiste": None, "reponse": "Aucun spécialiste n'a pu être choisi."}

    agent, _ = specialistes[choix["decision"]]
    print(f"→ Routé vers {agent.nom} ({choix['raison']})")
    return {"specialiste": agent.nom, "reponse": agent.executer(demande, memoriser_echange=False)}


# ------------------------------------------------------------
# 3. Parallèle + agrégation
# ------------------------------------------------------------

def en_parallele(taches: list[tuple], max_simultanes: int = 4) -> list[dict]:
    """
    taches : [(agent, consigne), ...] - chaque agent DOIT être différent :
    un même objet Agent n'est pas prévu pour tourner dans deux fils à la fois
    (son état et sa mémoire seraient mélangés).
    """
    noms = [agent.nom for agent, _ in taches]
    if len(set(noms)) != len(noms):
        raise ValueError("un même agent apparaît deux fois : créez des instances séparées")

    def travailler(tache):
        agent, consigne = tache
        return {"agent": agent.nom, "sortie": agent.executer(consigne, memoriser_echange=False)}

    with ThreadPoolExecutor(max_workers=max_simultanes) as executeur:
        return list(executeur.map(travailler, taches))


def agreger(agregateur: Agent, consigne: str, resultats: list[dict]) -> str:
    """Un agent fusionne les productions de plusieurs agents."""
    contributions = "\n\n".join(f"### Contribution de {r['agent']}\n{r['sortie']}" for r in resultats)
    return agregateur.executer(f"{consigne}\n\n{contributions}", memoriser_echange=False)


# ------------------------------------------------------------
# 4. Superviseur (les sous-agents deviennent des outils)
# ------------------------------------------------------------

def creer_superviseur(
    nom: str, role: str, equipe: dict[str, tuple], telemetrie=None
) -> Agent:
    """
    equipe : {"nom": (agent, "quand faire appel à lui"), ...}

    Pour chaque membre, le superviseur reçoit un outil « deleguer_a_<nom> ».
    Il décide lui-même, dans sa boucle agentique, à qui déléguer et dans quel ordre.
    """
    outils = BoiteAOutils()

    for nom_membre, (membre, description) in equipe.items():
        # Fonction fabriquée pour capturer le bon membre (piège classique des closures)
        def deleguer(consigne: str, membre=membre) -> str:
            print(f"\n  ↪ délégation à {membre.nom} : {consigne[:100]}")
            return membre.executer(consigne, memoriser_echange=False)

        outils.ajouter(
            f"deleguer_a_{nom_membre}",
            deleguer,
            f"Confie une tâche à {nom_membre}. {description}",
            {
                "type": "object",
                "properties": {
                    "consigne": {
                        "type": "string",
                        "description": "consigne complète et autonome (le membre ne voit rien d'autre)",
                    }
                },
                "required": ["consigne"],
            },
        )

    role_complet = (
        f"{role}\nTu ne fais pas le travail toi-même : tu délègues aux membres de ton "
        "équipe avec les outils deleguer_a_..., tu vérifies leurs résultats, puis tu "
        "rédiges la réponse finale."
    )
    return Agent(nom=nom, role=role_complet, outils=outils, outils_memoire=False,
                 telemetrie=telemetrie)
