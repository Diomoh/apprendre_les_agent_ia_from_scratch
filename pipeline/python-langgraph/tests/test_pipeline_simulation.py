"""Le pipeline complet, en simulation : aucune clé API nécessaire.

    pytest tests/ -q
"""

from pathlib import Path

from main import executer

CAHIER = (Path(__file__).parent.parent / "exemples" / "cahier-des-charges-livrabidjan.md").read_text(encoding="utf-8")


def test_pipeline_complet_en_simulation(tmp_path):
    resultat = executer(CAHIER, "Commande", simulation=True, auto=True, sortie=str(tmp_path))
    dossier = tmp_path / "commande"

    # Boucle Architecte <-> Critique : refusé au tour 1, validé au tour 2
    assert len(resultat["historique_design"]) == 2

    # Build : un binôme par tâche (2 backend + 1 frontend)
    assert sorted(r["tache"] for r in resultat["resultats_build"]) == ["T-01", "T-02", "T-03"]
    assert (dossier / "branches" / "T-02" / "livraison" / "attribution.py").exists()

    # Revue -> Fix : le relecteur Sécurité a bloqué une fois, Fix a corrigé
    assert resultat["cycles_fix"] == 1
    assert "telephone_client_masque" in (dossier / "integration" / "livraison" / "attribution.py").read_text()

    # Les tests du code généré passent après correction, et la fusion est validée
    assert resultat["rapport_integration"]["tests"]["reussi"]
    assert resultat["statut"] == "fusionne"

    # Livrables pour l'humain
    for chemin in ["docs/prd/commande.md", "docs/architecture/commande.md", "rapport.md"]:
        assert (dossier / chemin).exists(), chemin
