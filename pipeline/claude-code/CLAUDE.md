# Instructions du projet pour Claude Code

> Modèle à copier à la racine de votre projet, puis à adapter.

## Stack de l'équipe
- Backend : Django + Django REST Framework, PostgreSQL
- Frontend web : Next.js ; mobile : React Native
- Conteneurs : Docker ; fichiers : MinIO
- Design system : <à préciser, ex. shadcn/ui + Tailwind>

## Organisation des documents
```
docs/
├── prd/            00-prd-principal.md + un fichier par fonctionnalité (spécifications fonctionnelles)
├── architecture/   00-architecture-globale.md + un fichier par fonctionnalité (spécifications techniques)
└── pipeline/       journal et rapport de chaque passage du pipeline
```

## Conventions
- Identifiants uniques dans tout le projet : US-xx (stories), RG-xx (règles de gestion),
  ES-xx (exigences de sécurité), T-xx (tâches), ADR-xx (décisions).
- Chaque RG/ES appliquée est citée en commentaire dans le code et dans le nom de son test.
- Lancer le pipeline : `/pipeline docs/<cahier des charges>`. Il découpe le projet en fonctionnalités
  (liste et statuts dans `docs/prd/00-prd-principal.md`) et les traite une par une.
- Aucune fusion sur la branche principale sans validation humaine.
- Données personnelles : respecter la loi ivoirienne n°2013-450 (autorité ARTCI).

## Commandes utiles
- Tests backend : `<ex. docker compose exec api pytest>`
- Tests frontend : `<ex. npm test>`
- Lint : `<...>`
