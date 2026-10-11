"""
agent/agent.py - L'agent. Ce fichier grandit de leçon en leçon.

Leçon 01 : l'agent sait transmettre un texte au modèle.
Leçon 02 : l'agent a un rôle (prompt système) et peut tenir une conversation.
Leçon 03 : l'agent sait répondre en JSON validé (sortie structurée).
Leçon 04 : l'agent sait choisir parmi une liste finie d'options (décision).
Leçon 05 : l'agent peut demander un outil (via JSON dans le prompt).
Leçon 06 : l'agent utilise le « function calling » natif de l'API.

Méthodes des leçons précédentes retirées de ce fichier car remplacées :
  - demander() (leçon 01) -> remplacée par demander_avec_role() (leçon 02)
  - demander_avec_role() (leçon 02) -> remplacée par la boucle executer() (leçon 07)
  - choisir_outil() (leçon 05) -> remplacée par le function calling natif (leçon 06)
  - repondre_avec_outil() (leçon 05) -> remplacée par le function calling natif (leçon 06)
"""

from agent.outils import BoiteAOutils, boite_par_defaut
from cerveau.llm import ClientLLM
from cerveau.utils import champs_manquants, extraire_json, lire_json


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
    # LEÇON 06 : function calling natif
    # ============================================================

    def executer_appels_outils(self, appels: list[dict]) -> list[dict]:
        """
        Exécute chaque appel d'outil demandé par le modèle et renvoie
        les messages "tool" à ajouter à la conversation.
        """
        messages_outils = []
        for appel in appels:
            nom = appel["function"]["name"]
            arguments = lire_json(appel["function"]["arguments"])
            if not isinstance(arguments, dict):
                resultat = "ERREUR : les arguments ne sont pas un JSON valide."
            else:
                resultat = self.outils.executer(nom, arguments)
            print(f"  [outil] {nom}({appel['function']['arguments']}) → {resultat[:200]}")

            messages_outils.append(
                {"role": "tool", "tool_call_id": appel["id"], "content": resultat}
            )
        return messages_outils

    def repondre_avec_outils_natifs(self, message: str) -> str:
        """
        Un seul aller-retour d'outils :
        1. on envoie la question + la liste des outils ;
        2. si le modèle demande des outils, on les exécute ;
        3. on renvoie les résultats et le modèle rédige la réponse.
        """
        messages = [
            {"role": "system", "content": self.prompt_systeme},
            {"role": "user", "content": message},
        ]
        schemas = self.outils.schemas()

        reponse = self.llm.discuter_avec_outils(messages, schemas)
        if not reponse["tool_calls"]:
            return reponse["content"] or ""

        messages.append(reponse)  # le message assistant qui contient tool_calls
        messages += self.executer_appels_outils(reponse["tool_calls"])

        reponse_finale = self.llm.discuter_avec_outils(messages, schemas)
        return reponse_finale["content"] or ""
