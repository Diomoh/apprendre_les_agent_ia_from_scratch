"""
agent/memoire.py - La mémoire de l'agent.

Leçon 08 : la mémoire n'est pas de la conscience, ce sont des DONNÉES
que le code stocke puis remet dans le prompt.

- Mémoire courte : les derniers échanges de la conversation (en RAM).
- Mémoire longue : des faits durables, enregistrés dans un fichier JSON.
"""

import json
from pathlib import Path


class MemoireCourte:
    """Une fenêtre glissante sur les derniers messages user/assistant."""

    def __init__(self, taille_max: int = 20):
        self.taille_max = taille_max
        self.messages: list[dict] = []

    def ajouter(self, role: str, contenu: str):
        self.messages.append({"role": role, "content": contenu})

    def messages_recents(self) -> list[dict]:
        """Les `taille_max` derniers messages : le reste est oublié."""
        recents = self.messages[-self.taille_max :]
        # On commence toujours par un message utilisateur
        while recents and recents[0]["role"] != "user":
            recents = recents[1:]
        return recents

    def vider(self):
        self.messages = []


class MemoireLongue:
    """Des faits qui survivent à l'arrêt du programme (fichier JSON)."""

    def __init__(self, fichier: str = "memoire_longue.json"):
        self.fichier = Path(fichier)
        self.faits: list[str] = self._charger()

    def _charger(self) -> list[str]:
        if not self.fichier.exists():
            return []
        try:
            return json.loads(self.fichier.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []

    def _sauvegarder(self):
        self.fichier.write_text(
            json.dumps(self.faits, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def memoriser(self, fait: str) -> str:
        fait = fait.strip()
        if fait and fait not in self.faits:
            self.faits.append(fait)
            self._sauvegarder()
        return f"Mémorisé : {fait}"

    def rechercher(self, requete: str) -> list[str]:
        """Recherche simple par mots-clés (pas de magie, pas d'embeddings)."""
        mots = [mot for mot in requete.lower().split() if len(mot) > 2]
        return [fait for fait in self.faits if any(mot in fait.lower() for mot in mots)]

    def tout(self) -> list[str]:
        return list(self.faits)

    def oublier_tout(self):
        self.faits = []
        self._sauvegarder()
