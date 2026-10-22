---
name: pipeline
description: Fait passer un projet dans le pipeline multi-agents de l'équipe, à partir de son seul cahier des charges, fonctionnalité après fonctionnalité, jusqu'à des branches testées, revues et fusionnées.
argument-hint: [fichier du cahier des charges] [nom d'une fonctionnalité, optionnel]
disable-model-invocation: true
---

# Pipeline multi-agents : $ARGUMENTS

Tu es le chef d'orchestre. Tu ne rédiges ni le PRD, ni le design, ni le code : tu délègues
chaque étape au subagent prévu et tu appliques les règles de décision ci-dessous.

Tu ne t'arrêtes pour attendre l'humain qu'à DEUX moments : l'étape 3 (Validation) et l'étape 7
(Merge). Partout ailleurs tu enchaînes sans demander. Tu ne poses aucune autre question, sauf si
tu ne trouves pas le cahier des charges.

## Arguments
- **Cahier des charges** : le premier argument. S'il est absent, prends le document situé à la
  racine de `docs/` (fichier .md, .pdf ou .txt). S'il y en a plusieurs ou aucun, c'est le seul cas
  où tu poses une question avant de commencer.
- **Fonctionnalité** : le reste des arguments, facultatif. Si elle est absente, tu prends la
  première fonctionnalité au statut « à faire » dans `docs/prd/00-prd-principal.md` (étape 0).

## Journal
Tiens à jour, dans `docs/pipeline/<fonctionnalite>.md`, un journal court de chaque étape
(qui, quoi, résultat). C'est la trace que lira le validateur humain.

## Étape 0 - Cadrage du projet (automatique, une seule fois par projet)
Si `docs/prd/00-prd-principal.md` n'existe pas :
1. Lance **analyste-produit** en mode CADRAGE avec le chemin du cahier des charges. Il écrit le
   PRD principal, dont la section « Fonctionnalités » : la liste ordonnée des fonctionnalités, avec
   leurs dépendances et le statut « à faire ».
2. Note dans le journal la liste obtenue, puis enchaîne SANS t'arrêter : le cadrage sera validé
   par l'humain en même temps que la première fonctionnalité, à l'étape 3.

Choisis ensuite la fonctionnalité traitée (argument, sinon la première « à faire ») et passe son
statut à « en cours » dans le PRD principal.

## Étape 1 - Intake
Lance **analyste-produit** avec : le chemin du cahier des charges et le nom de la fonctionnalité.
Il écrit le PRD de la fonctionnalité dans `docs/prd/`.

## Étape 2 - Design : boucle Architecte / Critique (3 tours maximum)
Pour tour = 1, 2, 3 :
1. Lance **architecte** avec le chemin du PRD (et, à partir du tour 2, les objections du tour précédent).
2. Lance **critique** avec les chemins du PRD et du dossier d'architecture.
3. Lis ses NOTES et applique la règle, sans l'interpréter :
   - VALIDÉ si MOYENNE >= 8 ET securite >= 7 -> passe à l'étape 3.
   - Sinon, si tour < 3 -> transmets les OBJECTIONS à l'architecte, tour suivant.
   - Sinon (tour 3 atteint) -> passe à l'étape 3 en signalant les objections restantes.
Note chaque tour (notes, objections, décision) dans le journal et dans la section « Historique »
du dossier d'architecture.

## Étape 3 - Validation humaine (ARRÊT OBLIGATOIRE)
Présente :
- au premier passage du projet : le PRD principal et sa liste ordonnée de fonctionnalités ;
- les chemins du PRD et du dossier d'architecture de la fonctionnalité ;
- les hypothèses de l'Analyste, la note finale du Critique et ses objections restantes ;
- la liste des tâches T-xx.
Puis ARRÊTE-TOI et attends la réponse. Ne lance aucun développement sans un accord explicite.
- Accord -> étape 4.
- Correction demandée -> renvoie-la à l'analyste (si elle concerne le PRD ou la liste des
  fonctionnalités) ou à l'architecte (si elle concerne le design), refais la boucle de l'étape 2,
  puis reviens ici.
- « Arrête-toi là » -> laisse le statut « en cours » et termine : un prochain `/pipeline`
  reprendra cette fonctionnalité.

## Étape 4 - Build en parallèle
1. Crée la branche `feature/<fonctionnalite>` si elle n'existe pas.
2. Respecte les dépendances : une tâche ne démarre que lorsque celles dont elle dépend sont faites.
3. Lance EN PARALLÈLE, pour chaque tâche prête : **dev-backend** ou **dev-frontend** selon sa couche.
   Donne à chacun uniquement : l'identifiant de sa tâche, les chemins du PRD et du dossier
   d'architecture, et la consigne de ne lire que ce qui concerne sa tâche.
4. Dès qu'un dev a fini sa tâche, lance **testeur** sur cette tâche.
5. Si un testeur signale un échec dû au code, renvoie le rapport au dev concerné (2 allers-retours maximum).

## Étape 5 - Integrate
Lance toute la suite de tests du projet, les migrations, le lint, et si disponibles
`bandit -r .` et `npm audit`. Note le résultat dans le journal.

## Étape 6 - Review : relecteurs en parallèle (2 cycles de correction maximum)
1. Lance EN PARALLÈLE **relecteur-conformite**, **relecteur-securite** et **relecteur-qualite**,
   chacun avec les chemins du PRD et du dossier d'architecture et la branche à relire.
2. S'il y a au moins un BLOQUANT : envoie chaque problème au dev de la couche concernée
   (c'est l'étape Fix), relance les tests de l'étape 5, puis relance les relecteurs.
3. Au bout de 2 cycles de correction, passe à l'étape 7 même s'il reste des problèmes, et liste-les.

## Étape 7 - Merge (ARRÊT OBLIGATOIRE)
Écris `docs/pipeline/<fonctionnalite>-rapport.md` : tâches livrées, résultat des tests et des scans,
avis final de chaque relecteur, corrections appliquées, problèmes restants. Prépare le commit et
la description de PR, indique la prochaine fonctionnalité « à faire », puis ARRÊTE-TOI.
- Accord -> fusionne la branche, passe le statut de la fonctionnalité à « livrée » dans le PRD
  principal, puis ENCHAÎNE directement sur la prochaine fonctionnalité « à faire » (retour à
  l'étape 1). S'il n'en reste aucune, termine par un bilan du projet.
- Refus -> ne fusionne pas, laisse le statut « en cours » et termine.
- « Arrête-toi là » -> fusionne, passe le statut à « livrée », et termine sans enchaîner.

## Règles permanentes
- Tu ne sautes jamais une étape et ne modifies jamais toi-même le PRD, le design ou le code.
- Les seuils (8/10, sécurité 7, 3 tours, 2 cycles) ne se négocient pas : ils sont la règle de l'équipe.
- Les identifiants US/RG/ES/T sont uniques dans tout le projet et apparaissent jusque dans les noms des tests.
- Les seuls arrêts sont ceux des étapes 3 et 7 (et la question sur le cahier des charges introuvable).
