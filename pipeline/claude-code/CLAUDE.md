# Projet

> Modèle à copier à la racine du projet, puis à adapter. Gardez-le court : il est chargé par
> chaque agent à chaque action.

## Stack
- Backend : Django + Django REST Framework, PostgreSQL
- Frontend web : Next.js ; mobile : React Native
- Conteneurs : Docker ; fichiers : MinIO
- Design system : <à préciser>

## Conventions
- Identifiants uniques dans le projet : US, RG, ES, T, ADR. Chaque RG/ES est citée en commentaire
  dans le code et dans le nom de son test.
- Données personnelles : loi ivoirienne n°2013-450 (ARTCI).
- Aucune fusion sur la branche principale sans validation humaine.

## Commandes
- Tests backend : `<ex. docker compose exec api pytest>`
- Tests frontend : `<ex. npm test>`
- Lint : `<...>`
