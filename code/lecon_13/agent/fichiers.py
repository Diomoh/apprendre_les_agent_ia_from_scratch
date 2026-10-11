"""
agent/fichiers.py - Des outils de fichiers enfermés dans un « bac à sable ».

Leçon 10 : l'agent ne peut lire/écrire QUE dans son espace de travail.
Le code, pas le modèle, décide de ces limites.
"""

import os
import tempfile
from pathlib import Path


class EspaceDeTravail:
    """Un dossier racine hors duquel l'agent ne peut rien toucher."""

    def __init__(self, racine: str, dossiers_ecriture: list[str] | None = None):
        self.racine = Path(racine).resolve()
        self.racine.mkdir(parents=True, exist_ok=True)
        # Moindre privilège : si une liste est donnée, l'écriture est limitée à ces sous-dossiers
        self.dossiers_ecriture = dossiers_ecriture

    def chemin_sur(self, chemin: str) -> Path:
        """Transforme un chemin relatif en chemin absolu SÛR (refuse '../', '/etc'...)."""
        complet = (self.racine / chemin).resolve()
        if not complet.is_relative_to(self.racine):
            raise PermissionError(f"chemin interdit (hors de l'espace de travail) : {chemin}")
        return complet

    def lire(self, chemin: str) -> str:
        fichier = self.chemin_sur(chemin)
        if not fichier.is_file():
            raise FileNotFoundError(f"fichier introuvable : {chemin}")
        return fichier.read_text(encoding="utf-8")

    def ecrire(self, chemin: str, contenu: str) -> str:
        fichier = self.chemin_sur(chemin)
        relatif = fichier.relative_to(self.racine).as_posix()
        if self.dossiers_ecriture is not None and not any(
            relatif.startswith(dossier.rstrip("/") + "/") for dossier in self.dossiers_ecriture
        ):
            raise PermissionError(
                f"écriture interdite dans « {relatif} ». Dossiers autorisés : {self.dossiers_ecriture}"
            )
        fichier.parent.mkdir(parents=True, exist_ok=True)

        # Écriture ATOMIQUE : on écrit dans un fichier temporaire puis on le renomme.
        # Le fichier final est soit l'ancien, soit le nouveau, jamais à moitié écrit.
        descripteur, temporaire = tempfile.mkstemp(dir=fichier.parent)
        with os.fdopen(descripteur, "w", encoding="utf-8") as flux:
            flux.write(contenu)
        os.replace(temporaire, fichier)
        return f"Fichier écrit : {relatif} ({len(contenu)} caractères)"

    def lister(self, dossier: str = ".") -> list[str]:
        base = self.chemin_sur(dossier)
        if not base.is_dir():
            return []
        return sorted(
            p.relative_to(self.racine).as_posix() for p in base.rglob("*") if p.is_file()
        )


def ajouter_outils_fichiers(boite, espace: EspaceDeTravail, ecriture: bool = True):
    """Ajoute lire / lister (et éventuellement écrire) à une boîte à outils."""
    boite.ajouter(
        "lister_fichiers",
        espace.lister,
        "Liste les fichiers de l'espace de travail (chemins relatifs).",
        {
            "type": "object",
            "properties": {"dossier": {"type": "string", "description": "par défaut : ."}},
            "required": [],
        },
    )
    boite.ajouter(
        "lire_fichier",
        espace.lire,
        "Lit un fichier texte de l'espace de travail.",
        {
            "type": "object",
            "properties": {"chemin": {"type": "string", "description": "chemin relatif"}},
            "required": ["chemin"],
        },
    )
    if ecriture:
        boite.ajouter(
            "ecrire_fichier",
            espace.ecrire,
            "Crée ou remplace un fichier texte dans l'espace de travail.",
            {
                "type": "object",
                "properties": {
                    "chemin": {"type": "string", "description": "chemin relatif"},
                    "contenu": {"type": "string", "description": "contenu complet du fichier"},
                },
                "required": ["chemin", "contenu"],
            },
            sensible=True,
        )
