"""
multi/graphe.py - Orchestration avancée : un graphe de tâches entre agents.

Leçon 15 : on combine la planification (leçon 09) et l'orchestration (leçon 14).
Un projet = des tâches, chacune confiée à un agent, avec des DÉPENDANCES.
Le code calcule l'ordre, lance en parallèle ce qui peut l'être, transmet les
résultats, réessaie en cas d'échec et bloque ce qui dépend d'une tâche ratée.
"""

from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from cerveau.utils import extraire_json


@dataclass
class Tache:
    id: str
    agent: str  # nom de l'agent responsable
    consigne: str
    depend_de: list[str] = field(default_factory=list)
    statut: str = "a_faire"  # a_faire | en_cours | terminee | echec | bloquee
    resultat: str | None = None
    tentatives: int = 0
    # Optionnel : fonction(tache, agents) -> str qui remplace l'exécution simple
    # (ex. une boucle de revue). Par défaut : agent.executer(consigne).
    executeur: object = None


class GrapheTaches:
    def __init__(self):
        self.taches: dict[str, Tache] = {}

    def ajouter(self, tache: Tache) -> Tache:
        if tache.id in self.taches:
            raise ValueError(f"id de tâche en double : {tache.id}")
        self.taches[tache.id] = tache
        return tache

    # ---------- vérifications : AVANT de dépenser le moindre token ----------

    def verifier(self, agents: dict) -> list[str]:
        erreurs = []
        for tache in self.taches.values():
            if tache.agent not in agents:
                erreurs.append(f"{tache.id} : agent inconnu « {tache.agent} »")
            for dep in tache.depend_de:
                if dep not in self.taches:
                    erreurs.append(f"{tache.id} : dépendance inconnue « {dep} »")
        if not erreurs:
            try:
                self.vagues()
            except ValueError as erreur:
                erreurs.append(str(erreur))
        return erreurs

    def vagues(self) -> list[list[str]]:
        """
        Tri topologique par niveaux (algorithme de Kahn) :
        vague 1 = tâches sans dépendance, vague 2 = celles qui ne dépendent que
        de la vague 1, etc. Lève ValueError s'il y a un cycle.
        """
        restantes = {tid: set(t.depend_de) for tid, t in self.taches.items()}
        resultat = []
        while restantes:
            pretes = sorted(tid for tid, deps in restantes.items() if not deps)
            if not pretes:
                raise ValueError(f"cycle de dépendances entre : {sorted(restantes)}")
            resultat.append(pretes)
            for tid in pretes:
                del restantes[tid]
            for deps in restantes.values():
                deps.difference_update(pretes)
        return resultat

    # ---------- exécution ----------

    def _consigne_avec_contexte(self, tache: Tache) -> str:
        if not tache.depend_de:
            return tache.consigne
        entrees = "\n\n".join(
            f"### Résultat de « {dep} » ({self.taches[dep].agent})\n{self.taches[dep].resultat}"
            for dep in tache.depend_de
        )
        return f"{tache.consigne}\n\nTu disposes des résultats suivants :\n{entrees}"

    def _executer_une(self, tache: Tache, agents: dict, max_tentatives: int):
        if tache.statut == "terminee":
            return  # déjà faite lors d'une exécution précédente : on ne repaie pas
        if any(self.taches[dep].statut != "terminee" for dep in tache.depend_de):
            tache.statut = "bloquee"
            print(f"⛔ {tache.id} bloquée (une dépendance a échoué)")
            return

        tache.statut = "en_cours"
        while tache.tentatives < max_tentatives:
            tache.tentatives += 1
            print(f"▶ {tache.id} → {tache.agent} (tentative {tache.tentatives})")
            try:
                if tache.executeur:
                    resultat = tache.executeur(tache, agents, self._consigne_avec_contexte(tache))
                else:
                    resultat = agents[tache.agent].executer(
                        self._consigne_avec_contexte(tache), memoriser_echange=False
                    )
            except Exception as erreur:  # noqa: BLE001 - une tâche ne doit pas tout faire tomber
                resultat = f"ERREUR : {erreur}"

            # « Arrêt : » = la boucle agentique a atteint sa limite d'étapes (leçon 07)
            if resultat and not resultat.startswith(("ERREUR", "Arrêt :")):
                tache.resultat, tache.statut = resultat, "terminee"
                print(f"✔ {tache.id} terminée")
                return
            print(f"✖ {tache.id} : {resultat[:120] if resultat else 'réponse vide'}")

        tache.statut, tache.resultat = "echec", resultat

    def executer(self, agents: dict, max_tentatives: int = 2, tableau=None) -> dict:
        """
        Exécute le graphe vague par vague. Dans une vague, les tâches de
        DIFFÉRENTS agents tournent en parallèle ; celles d'un même agent
        passent l'une après l'autre (un agent = un seul fil à la fois).
        """
        erreurs = self.verifier(agents)
        if erreurs:
            raise ValueError("graphe invalide :\n- " + "\n- ".join(erreurs))

        for numero, vague in enumerate(self.vagues(), start=1):
            deja_faites = {tid for tid in vague if self.taches[tid].statut == "terminee"}
            if len(deja_faites) == len(vague):
                continue  # vague déjà exécutée lors d'un appel précédent
            print(f"\n===== Vague {numero} : {vague} =====")
            par_agent = defaultdict(list)
            for tid in vague:
                par_agent[self.taches[tid].agent].append(self.taches[tid])

            def lancer_file(file_taches):
                for tache in file_taches:
                    self._executer_une(tache, agents, max_tentatives)

            with ThreadPoolExecutor(max_workers=len(par_agent)) as executeur:
                list(executeur.map(lancer_file, par_agent.values()))

            if tableau is not None:
                for tid in vague:
                    if tid not in deja_faites and self.taches[tid].statut == "terminee":
                        tableau.publier(tid, self.taches[tid].resultat, self.taches[tid].agent)

        return {tid: t.statut for tid, t in self.taches.items()}

    def afficher(self) -> str:
        lignes = []
        for tache in self.taches.values():
            deps = f" ← {', '.join(tache.depend_de)}" if tache.depend_de else ""
            lignes.append(f"  [{tache.statut:^9}] {tache.id} ({tache.agent}){deps}")
        return "\n".join(lignes)

    def en_mermaid(self) -> str:
        """Le graphe au format Mermaid, à coller dans un fichier .md."""
        lignes = ["flowchart LR"]
        for tache in self.taches.values():
            lignes.append(f'    {tache.id}["{tache.id}<br/>{tache.agent}"]')
            for dep in tache.depend_de:
                lignes.append(f"    {dep} --> {tache.id}")
        return "\n".join(lignes)


# ------------------------------------------------------------
# Boucle de revue : produire → critiquer → corriger
# ------------------------------------------------------------

CONSIGNE_REVUE = """Relis le travail ci-dessous. Termine ta réponse par un objet JSON :
{"approuve": true ou false, "remarques": ["remarque précise et actionnable", "..."]}
N'approuve que si le travail respecte la demande. Pas plus de 5 remarques."""


def boucle_revue(producteur, relecteur, consigne: str, max_tours: int = 3) -> dict:
    """
    Le producteur fait une version, le relecteur la juge (JSON), le producteur
    corrige... jusqu'à approbation ou `max_tours`. Le CODE arbitre la fin.
    """
    version = producteur.executer(consigne, memoriser_echange=False)
    historique = []

    for tour in range(1, max_tours + 1):
        avis_texte = relecteur.executer(
            f"{CONSIGNE_REVUE}\n\nDemande initiale :\n{consigne}\n\nTravail à relire :\n{version}",
            memoriser_echange=False,
        )
        avis = extraire_json(avis_texte) or {"approuve": False, "remarques": [avis_texte[:500]]}
        historique.append({"tour": tour, "approuve": bool(avis.get("approuve")),
                           "remarques": avis.get("remarques", [])})
        print(f"  🔎 revue {tour} par {relecteur.nom} : "
              f"{'APPROUVÉ' if avis.get('approuve') else 'à corriger'}")

        if avis.get("approuve"):
            return {"version": version, "approuve": True, "tours": tour, "historique": historique}
        if tour == max_tours:
            break

        remarques = "\n".join(f"- {r}" for r in avis.get("remarques", []))
        version = producteur.executer(
            f"Demande initiale :\n{consigne}\n\nTa version précédente :\n{version}\n\n"
            f"Remarques du relecteur {relecteur.nom} :\n{remarques}\n\n"
            "Produis la version corrigée complète.",
            memoriser_echange=False,
        )

    return {"version": version, "approuve": False, "tours": max_tours, "historique": historique}


def executeur_avec_revue(nom_relecteur: str, max_tours: int = 3):
    """Fabrique un `executeur` de Tache qui passe par une boucle de revue."""

    def executeur(tache: Tache, agents: dict, consigne: str) -> str:
        bilan = boucle_revue(agents[tache.agent], agents[nom_relecteur], consigne, max_tours)
        statut = "approuvée" if bilan["approuve"] else "NON approuvée"
        return f"{bilan['version']}\n\n(Revue par {nom_relecteur} : {statut} en {bilan['tours']} tour(s))"

    return executeur


# ------------------------------------------------------------
# Point de contrôle humain
# ------------------------------------------------------------

def point_de_controle(titre: str, contenu: str, automatique: bool = False) -> bool:
    """Un humain valide avant de continuer. `automatique=True` pour les démos/tests."""
    print(f"\n🛑 POINT DE CONTRÔLE : {titre}\n{contenu[:1500]}")
    if automatique:
        print("(validation automatique)")
        return True
    return input("Valider et continuer ? (o/n) ").strip().lower() == "o"
