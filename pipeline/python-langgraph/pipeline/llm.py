"""
pipeline/llm.py - Parler au modèle et obtenir un JSON validé.

Même principe que le cours (cerveau/llm.py) : une API « chat completions »
compatible OpenAI (OpenRouter, Groq...), configurée dans le .env :
    API_KEY=...
    API_ROUTE=https://openrouter.ai/api/v1/chat/completions
    MODELE=openai/gpt-oss-120b

Ce qui est nouveau ici : `demander_json`. L'agent doit répondre avec un JSON
conforme à un schéma Pydantic. Si ce n'est pas le cas, on lui renvoie l'erreur
et il a UNE seconde chance. Au-delà, le pipeline s'arrête proprement.

Mode simulation : aucun appel réseau, des réponses préparées (simulation.py).
Utile pour tester le graphe, et pour une démo de webinaire sans connexion.
"""

import json
import os
import re
import threading
import time

import requests
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError

load_dotenv()


class ErreurLLM(RuntimeError):
    """Le modèle n'a pas produit une réponse exploitable."""


def extraire_json(texte: str) -> dict:
    """Récupère l'objet JSON d'une réponse, même entourée de ```json ... ```."""
    texte = texte.strip()
    texte = re.sub(r"^```(?:json)?\s*|\s*```$", "", texte)
    debut, fin = texte.find("{"), texte.rfind("}")
    if debut == -1 or fin == -1:
        raise ValueError("aucun objet JSON trouvé dans la réponse")
    return json.loads(texte[debut : fin + 1])


class ClientLLM:
    def __init__(
        self,
        simulation: bool = False,
        modele: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 8000,
        timeout: int = 180,
    ):
        self.simulation = simulation
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        # Télémétrie : un enregistrement par appel (les binômes tournent en parallèle,
        # d'où le verrou).
        self.journal: list[dict] = []
        self._verrou = threading.Lock()

        if simulation:
            from .simulation import Simulateur

            self.simulateur = Simulateur()
            self.modele = "simulation"
            return

        self.cle_api = os.environ.get("API_KEY")
        self.route_api = os.environ.get("API_ROUTE")
        if not self.cle_api or not self.route_api:
            raise ValueError(
                "API_KEY ou API_ROUTE introuvable. Copiez .env.example en .env, "
                "ou lancez le pipeline avec --simulation."
            )
        self.modele = modele or os.environ.get("MODELE", "openai/gpt-oss-120b")

    # -- appel brut --------------------------------------------------------

    def _appeler(self, messages: list[dict]) -> tuple[str, dict]:
        reponse = requests.post(
            self.route_api,
            headers={
                "Authorization": f"Bearer {self.cle_api}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.modele,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            },
            timeout=self.timeout,
        )
        reponse.raise_for_status()
        donnees = reponse.json()
        contenu = donnees["choices"][0]["message"].get("content") or ""
        return contenu, donnees.get("usage", {})

    def _tracer(self, agent: str, debut: float, usage: dict) -> None:
        with self._verrou:
            self.journal.append(
                {
                    "agent": agent,
                    "duree_s": round(time.time() - debut, 2),
                    "tokens_entree": usage.get("prompt_tokens", 0),
                    "tokens_sortie": usage.get("completion_tokens", 0),
                }
            )

    # -- appel structuré ----------------------------------------------------

    def demander_json(
        self,
        agent: str,
        systeme: str,
        consigne: str,
        modele_sortie: type[BaseModel],
        contexte_simulation: dict | None = None,
    ) -> BaseModel:
        """Demande une réponse JSON et la valide avec le schéma Pydantic."""
        debut = time.time()

        if self.simulation:
            brut = self.simulateur.repondre(agent, contexte_simulation or {})
            objet = modele_sortie.model_validate(brut)
            self._tracer(agent, debut, {})
            return objet

        schema = json.dumps(modele_sortie.model_json_schema(), ensure_ascii=False)
        messages = [
            {
                "role": "system",
                "content": systeme
                + "\n\nRéponds UNIQUEMENT avec un objet JSON valide, conforme à ce "
                "schéma JSON, sans aucun texte avant ou après :\n"
                + schema,
            },
            {"role": "user", "content": consigne},
        ]

        derniere_erreur: Exception | None = None
        for _ in range(2):
            texte, usage = self._appeler(messages)
            try:
                objet = modele_sortie.model_validate(extraire_json(texte))
                self._tracer(agent, debut, usage)
                return objet
            except (ValueError, ValidationError) as erreur:
                derniere_erreur = erreur
                messages += [
                    {"role": "assistant", "content": texte},
                    {
                        "role": "user",
                        "content": f"Ta réponse n'est pas un JSON valide pour le schéma : "
                        f"{erreur}. Renvoie uniquement le JSON corrigé.",
                    },
                ]
        raise ErreurLLM(f"{agent} : JSON invalide après 2 tentatives ({derniere_erreur})")

    # -- bilan ----------------------------------------------------------------

    def bilan(self) -> dict:
        return {
            "appels": len(self.journal),
            "tokens_entree": sum(e["tokens_entree"] for e in self.journal),
            "tokens_sortie": sum(e["tokens_sortie"] for e in self.journal),
        }
