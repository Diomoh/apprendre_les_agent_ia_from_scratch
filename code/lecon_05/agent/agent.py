"""
agent/agent.py - L'agent. Ce fichier grandit de leçon en leçon.

Leçon 01 : l'agent sait transmettre un texte au modèle.
Leçon 02 : l'agent a un rôle (prompt système) et peut tenir une conversation.
Leçon 03 : l'agent sait répondre en JSON validé (sortie structurée).
Leçon 04 : l'agent sait choisir parmi une liste finie d'options (décision).
Leçon 05 : l'agent peut demander un outil (via JSON dans le prompt).

Méthodes des leçons précédentes retirées de ce fichier car remplacées :
  - demander() (leçon 01) -> remplacée par demander_avec_role() (leçon 02)
"""

from agent.outils import BoiteAOutils, boite_par_defaut
from cerveau.llm import ClientLLM
from cerveau.utils import champs_manquants, extraire_json


class Agent:
    """Un agent qui a désormais un rôle et un historique de conversation."""

    def __init__(self, modele: str | None = None, outils: BoiteAOutils | None = None):
        # Leçon 01 : le cerveau (le LLM)
        self.llm = ClientLLM(modele)

        # Leçon 02 : le rôle de l'agent
        self.prompt_systeme = (
            "Tu es un assistant IA calme, précis et serviable. "
            "Tu expliques simplement, sans jargon inutile. "
            "Tu dis honnêtement quand tu ne sais pas. Tu réponds en français."
        )

        # Leçon 02 : l'historique de la conversation (le modèle, lui, ne retient rien)
        self.historique: list[dict] = []

        # Leçon 05 : les outils que l'agent a le droit de demander
        self.outils = outils if outils is not None else boite_par_defaut()

    # ============================================================
    # LEÇON 02 : rôle (prompt système) et conversation
    # ============================================================

    def demander_avec_role(self, message: str) -> str:
        """Une question, avec le prompt système placé en tête."""
        messages = [
            {"role": "system", "content": self.prompt_systeme},
            {"role": "user", "content": message},
        ]
        return self.llm.discuter(messages)

    def discuter(self, message: str) -> str:
        """
        Conversation sur plusieurs tours.

        Le LLM n'a aucune mémoire entre deux appels : c'est NOUS qui lui
        renvoyons tout l'historique à chaque fois.
        """
        self.historique.append({"role": "user", "content": message})

        messages = [{"role": "system", "content": self.prompt_systeme}] + self.historique
        reponse = self.llm.discuter(messages)

        self.historique.append({"role": "assistant", "content": reponse})
        return reponse

    def oublier_conversation(self):
        """Repart d'une conversation vide."""
        self.historique = []

    # ============================================================
    # LEÇON 03 : sorties structurées (JSON)
    # ============================================================

    def demander_structure(
        self,
        message: str,
        schema: str,
        champs_obligatoires: list[str] | None = None,
        tentatives: int = 3,
    ) -> dict | None:
        """
        Demande une réponse au format JSON, la vérifie et réessaie si besoin.

        Renvoie un dictionnaire Python, ou None si toutes les tentatives échouent.
        """
        champs_obligatoires = champs_obligatoires or []
        consignes = f"""{self.prompt_systeme}

CONSIGNES OBLIGATOIRES :
1. Réponds UNIQUEMENT avec un objet JSON valide.
2. Aucune explication, aucun markdown, aucun texte avant ou après le JSON.
3. Ta réponse commence par {{ et se termine par }}.

Schéma à respecter :
{schema}"""

        messages = [
            {"role": "system", "content": consignes},
            {"role": "user", "content": message},
        ]

        for _ in range(tentatives):
            # Température 0 : on veut le résultat le plus prévisible possible
            texte = self.llm.discuter(messages, temperature=0.0)
            donnees = extraire_json(texte)

            if donnees is None:
                erreur = "Ta réponse n'était pas un JSON valide."
            else:
                manquants = champs_manquants(donnees, champs_obligatoires)
                if not manquants:
                    return donnees
                erreur = f"Il manque les champs : {', '.join(manquants)}."

            # On renvoie l'erreur au modèle pour qu'il se corrige
            messages.append({"role": "assistant", "content": texte})
            messages.append(
                {"role": "user", "content": f"{erreur} Recommence en respectant le schéma."}
            )

        return None

    # ============================================================
    # LEÇON 04 : décision (choisir parmi des options connues)
    # ============================================================

    def decider(self, message: str, choix: list[str]) -> dict | None:
        """
        Fait choisir au modèle UNE option dans une liste fermée.

        Renvoie {"decision": "...", "raison": "..."} ou None.
        La décision est TOUJOURS vérifiée par le code : jamais d'option inventée.
        """
        options = "\n".join(f"- {option}" for option in choix)
        schema = f"""{{"decision": "une des options ci-dessous, recopiée à l'identique",
 "raison": "une phrase qui justifie le choix"}}

Options autorisées :
{options}"""

        for _ in range(2):
            resultat = self.demander_structure(
                message, schema, champs_obligatoires=["decision", "raison"]
            )
            if resultat and resultat["decision"] in choix:
                return resultat

        return None

    # ============================================================
    # LEÇON 05 : outils (le modèle demande, le code exécute)
    # ============================================================

    def choisir_outil(self, message: str) -> dict | None:
        """
        Demande au modèle quel outil appeler, sous forme de JSON.

        Renvoie {"outil": "nom" ou null, "arguments": {...}}.
        """
        schema = f"""{{"outil": "nom de l'outil" ou null si aucun outil n'est utile,
 "arguments": {{"nom_parametre": valeur}}}}

Outils disponibles :
{self.outils.decrire()}"""

        resultat = self.demander_structure(
            message, schema, champs_obligatoires=["outil", "arguments"]
        )
        if resultat is None:
            return None
        # Le code vérifie : un outil inconnu est refusé
        if resultat["outil"] is not None and resultat["outil"] not in self.outils.noms():
            return None
        return resultat

    def repondre_avec_outil(self, message: str) -> str:
        """
        1. Le modèle choisit un outil (ou aucun).
        2. Le code exécute l'outil.
        3. Le modèle rédige la réponse finale à partir du résultat.
        """
        choix = self.choisir_outil(message)

        if choix is None or choix["outil"] is None:
            return self.demander_avec_role(message)

        resultat = self.outils.executer(choix["outil"], choix["arguments"] or {})
        print(f"  [outil] {choix['outil']}({choix['arguments']}) → {resultat}")

        messages = [
            {"role": "system", "content": self.prompt_systeme},
            {"role": "user", "content": message},
            {
                "role": "user",
                "content": (
                    f"Résultat de l'outil {choix['outil']} : {resultat}\n"
                    "Rédige la réponse finale à la question en t'appuyant sur ce résultat."
                ),
            },
        ]
        return self.llm.discuter(messages)
