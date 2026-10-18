# Architecture NN : <Nom de la fonctionnalité>

> Spécifications techniques : le COMMENT. Référence : `docs/prd/NN-<fonctionnalite>.md`.

## Vue d'ensemble
<Comment la fonctionnalité s'insère dans l'architecture globale, en quelques phrases.>

## Modèle de données
| Modèle | Champs | Contraintes (avec RG-xx) |
| --- | --- | --- |
| Commande | id, client, livreur, statut, ... | statut suit RG-01 |

## Contrat d'API (figé avant le Build)
| Méthode | Chemin | Rôles | Entrée | Sortie | Erreurs |
| --- | --- | --- | --- | --- | --- |
| POST | `/api/...` | client | ... | 201 ... | 400, 403 |

## Écrans (frontend)
- <écran> : composants du design system utilisés, états (chargement, erreur, vide)

## Réponse aux exigences de sécurité
- **ES-01** : <mesure technique précise>
- **ES-02** : <mesure technique précise, sur quels endpoints>

## Décisions (ADR)
- **ADR-NN** : <décision>. Alternatives écartées : <...>, parce que <...>.

## Tâches
| Tâche | Couche | Description | RG | ES | Dépend de |
| --- | --- | --- | --- | --- | --- |
| T-01 | backend | ... | RG-01 | ES-02 | |
| T-02 | frontend | ... | | ES-01 | |

## Historique
- Tour 1 : moyenne x/10, sécurité y/10, objections : ... ; corrections apportées : ...
