# Pipeline multi-agents en Python (LangGraph)

Ici, **c'est le code qui orchestre** : le graphe, l'état partagé, les boucles plafonnées
et les arrêts pour validation humaine sont écrits en Python. Le modèle propose, le code décide.

```
analyste -> architecte -> critique --(note < 8 et tours < 3)--> architecte
                                   \--> validation_design   (ARRÊT : vous validez)
validation_design --(valide)--> binôme x N en parallèle (un par tâche)
binôme -> integration (fusion des branches + pytest + bandit)
       -> relecteur x 7 en parallèle -> decision_revue
decision_revue --(problème bloquant et cycles < 2)--> fix -> integration
               \--> merge   (ARRÊT : vous validez la fusion)
```

## Démarrer

```bash
cd pipeline/python-langgraph
pip install -r requirements.txt

# Sans clé API : scénario préparé « livraison Grand Abidjan », idéal pour une démo
python main.py --cahier exemples/livraison_abidjan.md --fonctionnalite Commande --simulation

# Avec un vrai modèle (même .env que le cours : API_KEY, API_ROUTE, MODELE)
cp .env.example .env
python main.py --cahier exemples/livraison_abidjan.md --fonctionnalite Commande

# Le test bout en bout (en simulation)
pytest -q
```

Le pipeline s'arrête deux fois et attend votre réponse dans le terminal :
`ok` pour valider, ou votre correction en texte libre (renvoyée à l'Architecte).
`--auto-valider` saute ces arrêts (tests, démos).

## Ce que produit un passage

Un passage = **une fonctionnalité**. Les livrables sont dans `sortie/<fonctionnalite>/` :

| Chemin | Contenu |
| --- | --- |
| `docs/prd/<f>.md` | Spécifications fonctionnelles : stories, RG-xx, ES-xx, hors périmètre |
| `docs/architecture/<f>.md` | Spécifications techniques, contrat d'API, tâches, historique du Critique |
| `branches/<T-xx>/` | Le travail isolé de chaque binôme (l'équivalent d'un git worktree) |
| `integration/` | Les branches fusionnées, corrigées par Fix, avec les tests |
| `rapport.md` | Le résumé soumis avant la fusion |

## Ordre de lecture du code

1. `pipeline/schemas.py` : les documents échangés et **les garde-fous** (seuil 8/10, sécurité
   bloquante sous 7, 3 tours de design, 2 cycles de correction).
2. `pipeline/graphe.py` : le workflow en entier, sur une page.
3. `pipeline/noeuds.py` : une méthode par étape, dans l'ordre du pipeline.
4. `pipeline/prompts.py` : le rôle de chaque agent spécialisé.
5. `pipeline/llm.py` : l'appel au modèle avec sortie JSON validée (une seconde chance, puis arrêt).
6. `pipeline/simulation.py` : le scénario préparé, écrit pour déclencher les deux boucles.

## Les concepts du webinaire, et où ils sont

| Concept | Où le voir |
| --- | --- |
| Reflection (évaluateur-optimiseur) | `architecte` + `critique` + `apres_critique` |
| Le code décide, pas le modèle | `Evaluation.est_valide()` |
| Human-in-the-loop | `interrupt(...)` dans `validation_design` et `merge`, reprise avec `Command(resume=...)` |
| Fan-out / fan-in | `Send("binome", ...)` puis `binome -> integration` |
| Context engineering | `contexte_tache` : un binôme ne reçoit que SA tâche, ses RG/ES et le contrat d'API |
| Droits minimaux | `ecrire_fichiers` refuse tout chemin hors du dossier de travail |
| Traçabilité RG/ES -> test | identifiants dans le PRD, les tâches, le code et les noms de tests |
| Observabilité | `client.journal` : un enregistrement par appel (agent, durée, tokens) |

## Limites assumées

- En mode réel, le backend généré est de la logique métier **Python pur** testée avec pytest :
  intégrer ce code dans un vrai projet Django reste à faire (c'est le rôle de la version Claude Code,
  qui travaille directement dans votre dépôt).
- Le frontend généré n'est pas testé automatiquement ; le Testeur liste les vérifications manuelles.
- `MemorySaver` garde l'état en mémoire : si vous fermez le terminal pendant un arrêt, le passage est
  perdu. Pour reprendre plus tard, remplacez-le par un checkpointer persistant (SQLite, Postgres).
