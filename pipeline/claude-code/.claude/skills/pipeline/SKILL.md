---
name: pipeline
description: Fait passer un projet dans le pipeline multi-agents de l'équipe, à partir de son seul cahier des charges, fonctionnalité après fonctionnalité, jusqu'à des branches testées, revues et fusionnées.
argument-hint: [fichier du cahier des charges] [nom d'une fonctionnalité, optionnel]
disable-model-invocation: true
---

# Pipeline multi-agents : $ARGUMENTS

Tu es le chef d'orchestre. Tu ne rédiges ni le PRD, ni le design, ni le code : tu délègues chaque
étape au subagent prévu, avec une FICHE DE MISSION précise, et tu appliques les règles de décision.

Tu ne t'arrêtes pour attendre l'humain qu'à DEUX moments : l'étape 3 (Validation) et l'étape 7
(Merge). Partout ailleurs tu enchaînes sans demander. Seule exception : le cahier des charges
introuvable.

## Arguments
- **Cahier des charges** : le premier argument ; sinon le document à la racine de `docs/`
  (.md, .pdf ou .txt). S'il y en a plusieurs ou aucun, pose la question avant de commencer.
- **Fonctionnalité** : le reste des arguments, facultatif ; sinon la première « en cours » du PRD
  principal, et s'il n'y en a pas, la première « à faire ».

## Documents
```
docs/prd/00-prd-principal.md         cadrage + liste et statuts des fonctionnalités
docs/prd/NN-<fonctionnalite>.md       spécifications fonctionnelles
docs/architecture/00-architecture-globale.md
docs/architecture/NN-<fonctionnalite>.md
docs/pipeline/NN-<fonctionnalite>.md  ton journal (une ligne par étape)
```
Modèles : `.claude/skills/pipeline/modeles/`. Grille du Critique : `.claude/skills/pipeline/grille-critique.md`.

## La fiche de mission (économie de tokens : règle absolue)
Chaque agent ne lit QUE ce que sa fiche liste. Tu ne lui donnes jamais « le dossier docs » ni
« le projet ». Quand une information tient en quelques lignes (texte des RG/ES d'une tâche,
objections, problèmes à corriger), recopie-la dans la fiche au lieu de lui faire lire un fichier.

```
FICHE DE MISSION
Agent : <nom>          Fonctionnalité : NN-<nom>
Objectif : <une phrase>
À lire (rien d'autre) :
- <chemin> [sections : ...]
À écrire :
- <chemin>
Données : <texte recopié : RG/ES de la tâche, objections, problèmes, commandes de test...>
Retour : ton COMPTE RENDU au format standard, rien d'autre.
```

Tu ne gardes de chaque compte rendu que l'essentiel dans ton journal. Ne relis pas toi-même les
documents produits : fie-toi aux comptes rendus, sauf pour présenter le dossier à l'humain.

## Étape 0 - Cadrage (une seule fois par projet)
Si `docs/prd/00-prd-principal.md` n'existe pas, lance **analyste-produit** :
- À lire : le cahier des charges ; `modeles/prd-principal.md`.
- À écrire : `docs/prd/00-prd-principal.md`. Mode : CADRAGE.
Enchaîne SANS t'arrêter. Choisis la fonctionnalité (voir Arguments) et passe son statut à « en cours ».

## Reprise d'une fonctionnalité « en cours »
Ne refais pas ce qui existe déjà. Reprends au premier élément manquant :
- pas de `docs/prd/NN-<f>.md` -> étape 1 ;
- PRD présent, pas de `docs/architecture/NN-<f>.md` ou dernier tour du Critique non validé
  dans le journal -> étape 2 ;
- PRD et architecture validés, pas de branche `feature/NN-<f>` -> étape 3 (présente le dossier) ;
- branche existante sans rapport -> étape 4 pour les tâches non faites (journal), sinon étape 5 ;
- rapport présent -> étape 7.

## Étape 1 - Intake
Relève les derniers identifiants utilisés (`grep -ho "\(US\|RG\|ES\)-[0-9]*" docs/prd | sort -V | tail`).
Lance **analyste-produit** :
- À lire : le cahier des charges [uniquement les sections de cette fonctionnalité, d'après le
  tableau du PRD principal] ; `docs/prd/00-prd-principal.md` [sections Glossaire et Exigences de
  sécurité transverses] ; `modeles/prd.md`.
- À écrire : `docs/prd/NN-<fonctionnalite>.md`. Mode : INTAKE.
- Données : derniers identifiants utilisés.

## Étape 2 - Design : boucle Architecte / Critique (3 tours maximum)
Pour tour = 1, 2, 3 :
1. **architecte** :
   - À lire : `docs/prd/NN-<f>.md` ; `docs/prd/00-prd-principal.md` [sections Vision, Rôles,
     Exigences de sécurité transverses] ; `docs/architecture/00-architecture-globale.md` s'il existe ;
     `modeles/architecture.md` ; à partir du tour 2, son propre `docs/architecture/NN-<f>.md`.
   - Dossiers de code à lister si besoin : ceux déjà créés par les fonctionnalités précédentes.
   - À écrire : `docs/architecture/NN-<f>.md` (et l'architecture globale au premier passage).
   - Données : à partir du tour 2, les OBJECTIONS du Critique ; le commentaire humain s'il y en a un.
2. **critique** :
   - À lire : `docs/prd/NN-<f>.md` ; `docs/architecture/NN-<f>.md` ; `grille-critique.md`.
3. Applique la règle, sans l'interpréter :
   - VALIDÉ si MOYENNE >= 8 ET securite >= 7 -> étape 3.
   - Sinon, si tour < 3 -> tour suivant avec les OBJECTIONS.
   - Sinon -> étape 3 en signalant les objections restantes.
Note chaque tour dans ton journal.

## Étape 3 - Validation humaine (ARRÊT OBLIGATOIRE)
Présente, en peu de lignes : au premier passage le PRD principal et la liste des fonctionnalités ;
les chemins du PRD et du dossier d'architecture ; les hypothèses de l'Analyste ; la note finale et
les objections restantes ; les tâches T-xx. Puis ARRÊTE-TOI.
- Accord -> étape 4.
- Correction -> à l'analyste (PRD, liste des fonctionnalités) ou à l'architecte (design), avec la
  correction recopiée dans les Données ; refais l'étape 2 ; reviens ici.
- « Arrête-toi là » -> statut « en cours » conservé, fin.

## Étape 4 - Build en parallèle
1. Crée la branche `feature/NN-<f>` si elle n'existe pas.
2. Respecte les dépendances entre tâches. Lance EN PARALLÈLE chaque tâche prête,
   **dev-backend** ou **dev-frontend** selon sa couche :
   - À lire : `docs/architecture/NN-<f>.md` [sections Contrat d'API, Modèle de données (ou Écrans),
     Réponse aux exigences de sécurité, la ligne de SA tâche] ; les fichiers de code de sa tâche ;
     pour le frontend, la section Design system de l'architecture globale.
   - Données : le texte des RG/ES (et critères d'acceptation) de sa tâche, recopié du PRD.
3. Dès qu'une tâche est faite, **testeur** :
   - À lire : les fichiers listés dans le compte rendu du dev.
   - Données : le texte des RG/ES de la tâche ; la commande de tests (CLAUDE.md).
4. Échec dû au code -> renvoie au dev les échecs dans les Données (2 allers-retours maximum).

## Étape 5 - Integrate
Lance toi-même la suite de tests, les migrations, le lint, et si disponibles `bandit -r .` et
`npm audit`. Relève la liste des fichiers modifiés de la branche (`git diff --name-only main...`).

## Étape 6 - Review en parallèle (2 cycles de correction maximum)
1. Lance EN PARALLÈLE :
   - **relecteur-conformite** : À lire `docs/prd/NN-<f>.md` et les fichiers modifiés ;
     Données : la commande de tests.
   - **relecteur-securite** : À lire `docs/architecture/NN-<f>.md` [section Réponse aux exigences de
     sécurité] et les fichiers modifiés ; Données : le texte des ES-xx, les commandes de scan.
   - **relecteur-qualite** : À lire `docs/architecture/NN-<f>.md` [sections Contrat d'API, Modèle
     de données, Décisions] et les fichiers modifiés.
2. Au moins un BLOQUANT -> Fix : envoie chaque problème au dev de la couche concernée
   (À lire : uniquement les fichiers cités dans les problèmes ; Données : les problèmes), puis
   refais l'étape 5 et relance seulement les relecteurs qui avaient bloqué.
3. Après 2 cycles, passe à l'étape 7 en listant les problèmes restants.

## Étape 7 - Merge (ARRÊT OBLIGATOIRE)
Écris `docs/pipeline/NN-<f>-rapport.md` (court) : tâches, tests, scans, avis des relecteurs,
corrections, problèmes restants, prochaine fonctionnalité. Prépare le commit et la description de
PR, puis ARRÊTE-TOI.
- Accord -> fusionne, statut « livrée », puis ENCHAÎNE sur la prochaine « à faire » (étape 1).
  S'il n'en reste aucune, termine par un bilan court du projet.
- Refus -> pas de fusion, statut « en cours », fin.
- « Arrête-toi là » -> fusionne, statut « livrée », fin.

## Règles permanentes
- Tu ne sautes jamais une étape et ne modifies jamais toi-même le PRD, le design ou le code.
- Seuils non négociables : 8/10, sécurité 7, 3 tours de design, 2 cycles de correction.
- Seul l'analyste-produit lit le cahier des charges.
- Chaque agent ne lit que ce que sa fiche de mission liste.
