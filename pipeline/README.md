# Pipeline multi-agents : du cahier des charges au code revu

Le même workflow, implémenté de deux façons, dans deux dossiers indépendants :

| Dossier | Approche | Pour quoi faire |
| --- | --- | --- |
| [`python-langgraph/`](python-langgraph/) | L'orchestration est **codée** en Python avec LangGraph | Comprendre chaque mécanisme, l'enseigner, l'intégrer à un produit |
| [`claude-code/`](claude-code/) | Des **subagents** et une skill `/pipeline` dans Claude Code | L'utiliser au quotidien, directement dans vos projets |

## Le workflow

1. **Intake** : l'Analyste produit transforme le cahier des charges en **PRD**
   (stories, règles de gestion RG-xx, exigences de sécurité ES-xx, hors périmètre).
2. **Design** : l'Architecte rédige le **dossier d'architecture** (stack, contrat d'API, réponse
   à chaque ES, tâches T-xx) ; le Critique le note. Validé si moyenne >= 8 et sécurité >= 7,
   sinon correction (3 tours maximum).
3. **Validation humaine** du PRD et du dossier d'architecture.
4. **Build** : un binôme Implementer + Tester par tâche, en parallèle.
5. **Integrate** : fusion, tests, scans de sécurité.
6. **Review** : relecteurs spécialisés en parallèle ; un problème bloquant part en **Fix**
   (2 cycles maximum).
7. **Merge** après **validation humaine**.

Un passage du pipeline = **une fonctionnalité**. Les documents sont organisés en un PRD principal
plus un PRD par fonctionnalité, et de même pour l'architecture.

## Lien avec le cours

Le cours (`lecons/` et `code/`) construit les agents à la main, sans framework. Ce dossier montre
où mène ce travail : la même équipe, organisée en pipeline de production, une fois avec un
framework (LangGraph) et une fois avec un outil (Claude Code).
