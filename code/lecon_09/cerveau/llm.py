"""
cerveau/llm.py - Le client qui parle au modèle de langage (LLM).

Leçon 01 : texte en entrée, texte en sortie.
Leçon 02 : on envoie une liste de messages avec des rôles (system, user, assistant).
Leçon 06 : on transmet la liste des outils à l'API (« function calling » natif).

On utilise l'API « chat completions » compatible OpenAI, proposée par
OpenRouter et par Groq. La route et la clé sont lues dans le fichier .env :
    API_KEY=...
    API_ROUTE=https://openrouter.ai/api/v1/chat/completions
    MODELE=openai/gpt-oss-120b
"""

import os

import requests
from dotenv import load_dotenv

# load_dotenv() cherche un fichier .env en remontant les dossiers :
# un seul .env à la racine du cours suffit pour toutes les leçons.
load_dotenv()


class ClientLLM:
    """Un client minimal : il envoie un texte au modèle et renvoie sa réponse."""

    def __init__(
        self,
        modele: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        timeout: int = 120,
    ):
        self.cle_api = os.environ.get("API_KEY")
        self.route_api = os.environ.get("API_ROUTE")

        if not self.cle_api or not self.route_api:
            raise ValueError(
                "API_KEY ou API_ROUTE introuvable. Copiez .env.example en .env "
                "à la racine du cours et renseignez-les."
            )

        self.modele = modele or os.environ.get("MODELE", "openai/gpt-oss-120b")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout

        # Consommation du dernier appel (tokens d'entrée / de sortie).
        self.derniere_utilisation = None

    def demander(self, prompt: str, temperature: float | None = None) -> str:
        """Envoie un texte au modèle et renvoie le texte de sa réponse."""
        return self.discuter([{"role": "user", "content": prompt}], temperature)

    def discuter(self, messages: list[dict], temperature: float | None = None) -> str:
        """Envoie une liste de messages {"role", "content"} et renvoie la réponse."""
        donnees = self._envoyer(messages, temperature)
        return (donnees["choices"][0]["message"].get("content") or "").strip()

    def discuter_avec_outils(
        self, messages: list[dict], outils: list[dict], temperature: float | None = None
    ) -> dict:
        """
        Envoie les messages ET la description des outils.

        Renvoie le message de l'assistant (un dictionnaire) :
          - soit {"role": "assistant", "content": "texte final", "tool_calls": None}
          - soit {"role": "assistant", "content": None, "tool_calls": [...]}
        """
        donnees = self._envoyer(messages, temperature, outils)
        message = donnees["choices"][0]["message"]

        # On ne garde que les champs standard (certains fournisseurs en ajoutent)
        appels = message.get("tool_calls") or None
        if appels:
            appels = [
                {
                    "id": appel["id"],
                    "type": "function",
                    "function": {
                        "name": appel["function"]["name"],
                        "arguments": appel["function"].get("arguments") or "{}",
                    },
                }
                for appel in appels
            ]
        return {"role": "assistant", "content": message.get("content"), "tool_calls": appels}

    def _envoyer(
        self,
        messages: list[dict],
        temperature: float | None = None,
        outils: list[dict] | None = None,
    ) -> dict:
        """Fait l'appel HTTP et renvoie la réponse JSON brute de l'API."""
        charge_utile = {
            "model": self.modele,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": temperature if temperature is not None else self.temperature,
        }
        if outils:
            charge_utile["tools"] = outils
        entetes = {
            "Authorization": f"Bearer {self.cle_api}",
            "Content-Type": "application/json",
        }

        reponse = requests.post(
            self.route_api, headers=entetes, json=charge_utile, timeout=self.timeout
        )
        if reponse.status_code != 200:
            raise RuntimeError(f"Erreur API {reponse.status_code} : {reponse.text[:500]}")

        donnees = reponse.json()
        self.derniere_utilisation = donnees.get("usage")
        return donnees
