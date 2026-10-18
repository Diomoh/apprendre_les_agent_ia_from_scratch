# Grille du Critique

Chaque critère est noté de 0 à 10. Toute note sous 8 doit être justifiée par une objection.

| Critère | 10 | 7 | 4 ou moins |
| --- | --- | --- | --- |
| **couverture_prd** | Chaque story, RG et ES a sa réponse dans le design | Un élément secondaire oublié | Une RG ou une ES ignorée |
| **simplicite** | La solution la plus simple qui couvre le besoin | Un composant superflu | Architecture surdimensionnée (microservices pour un MVP...) |
| **securite** | Chaque ES a une mesure concrète, sur tous les chemins | Une mesure vague ou incomplète | Une ES sans aucune mesure, ou une faille dans le design |
| **coherence_stack** | Respecte la stack de `CLAUDE.md`, exceptions justifiées par ADR | Une exception non justifiée | Technologie étrangère à l'équipe sans raison |
| **faisabilite** | Réalisable par l'équipe dans le délai, tâches indépendantes | Une tâche trop grosse ou une dépendance mal placée | Dépend d'un service, d'un accès ou d'une compétence indisponible |

## Règle de décision (appliquée par le pipeline, pas par le Critique)

- **Validé** : moyenne >= 8 **et** sécurité >= 7.
- Sécurité sous 7 : correction obligatoire, même avec une bonne moyenne.
- Au 3e tour, le dossier est transmis à l'humain avec les objections restantes.
