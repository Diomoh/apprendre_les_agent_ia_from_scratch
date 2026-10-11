"""
agent/telemetrie.py - Observer ce que fait l'agent pendant qu'il tourne.

Leçon 11 : chaque appel au LLM, chaque outil, chaque tâche laisse une trace
(une ligne JSON dans un fichier .jsonl). On peut ensuite compter, mesurer, déboguer.
Leçon 14 : un verrou protège le fichier quand plusieurs agents tournent en parallèle.
"""

import json
import threading
from collections import Counter
from datetime import datetime
from pathlib import Path


class Telemetrie:
    """Écrit des événements au format JSON Lines (un objet JSON par ligne)."""

    def __init__(self, fichier: str = "telemetrie.jsonl"):
        self.fichier = Path(fichier)
        self._verrou = threading.Lock()

    def enregistrer(self, type_evenement: str, **donnees):
        evenement = {
            "horodatage": datetime.now().isoformat(timespec="milliseconds"),
            "type": type_evenement,
            **donnees,
        }
        with self._verrou, self.fichier.open("a", encoding="utf-8") as flux:
            flux.write(json.dumps(evenement, ensure_ascii=False) + "\n")

    def lire(self) -> list[dict]:
        if not self.fichier.exists():
            return []
        with self.fichier.open(encoding="utf-8") as flux:
            return [json.loads(ligne) for ligne in flux if ligne.strip()]

    def resume(self) -> dict:
        """Quelques chiffres utiles calculés à partir des événements."""
        evenements = self.lire()
        appels_llm = [e for e in evenements if e["type"] == "appel_llm"]
        appels_outils = [e for e in evenements if e["type"] == "appel_outil"]
        taches = [e for e in evenements if e["type"] == "fin_tache"]

        return {
            "appels_llm": len(appels_llm),
            "tokens_entree": sum(e.get("tokens_entree") or 0 for e in appels_llm),
            "tokens_sortie": sum(e.get("tokens_sortie") or 0 for e in appels_llm),
            "duree_llm_moyenne_s": round(
                sum(e["duree_s"] for e in appels_llm) / len(appels_llm), 2
            )
            if appels_llm
            else 0,
            "outils": dict(Counter(e["outil"] for e in appels_outils)),
            "outils_en_echec": sum(1 for e in appels_outils if e["statut"] != "ok"),
            "taches": len(taches),
            "taches_terminees": sum(1 for e in taches if e.get("termine")),
        }

    def effacer(self):
        if self.fichier.exists():
            self.fichier.unlink()
