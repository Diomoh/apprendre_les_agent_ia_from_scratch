# Pipeline multi-agents avec Claude Code

Ici, **on ne code pas l'orchestration** : on décrit des agents spécialisés (fichiers Markdown) et
le workflow (une skill appelée avec `/pipeline`). La session principale de Claude Code joue le chef
d'orchestre et délègue chaque étape au bon subagent.

```
.claude/
├── agents/                     les 9 agents, définis UNE fois, réutilisés à chaque fonctionnalité
│   ├── analyste-produit.md     cahier des charges -> PRD
│   ├── architecte.md           PRD -> dossier d'architecture + tâches
│   ├── critique.md             note le design (lecture seule)
│   ├── dev-backend.md          Django / DRF
│   ├── dev-frontend.md         Next.js / React Native
│   ├── testeur.md              un test par RG et par ES
│   ├── relecteur-conformite.md PRD couvert, traçabilité RG/ES -> test (lecture seule)
│   ├── relecteur-securite.md   ES-xx et failles courantes (lecture seule)
│   └── relecteur-qualite.md    exactitude, architecture, production (lecture seule)
└── skills/
    └── pipeline/
        ├── SKILL.md            le workflow, étape par étape : la commande /pipeline
        ├── grille-critique.md
        └── modeles/            modèles de PRD et de dossier d'architecture
CLAUDE.md                       conventions du projet (stack, dossiers docs/, identifiants)
```

## Installer dans un de vos projets

```bash
cp -r pipeline/claude-code/.claude  /chemin/vers/mon-projet/
cp pipeline/claude-code/CLAUDE.md   /chemin/vers/mon-projet/   # puis adaptez-le
```

Vérifiez dans Claude Code avec `/agents` : les 9 agents doivent apparaître.

## Utiliser

```
/pipeline docs/cahier-des-charges.md Commande
```

Le pipeline s'arrête **deux fois** et attend votre accord : après le PRD et le design, puis avant
la fusion. Tout le reste s'enchaîne seul : boucle Architecte / Critique (3 tours max), devs en
parallèle, tests, relecteurs en parallèle, corrections (2 cycles max).

Vous pouvez aussi appeler un agent seul :
« Utilise l'agent critique sur docs/architecture/02-commande.md ».

## Les choix de conception

- **Droits minimaux** : le Critique et les relecteurs n'ont que `Read`, `Grep`, `Glob` (+ `Bash`
  pour lancer les tests ou les scans). Ils ne peuvent pas modifier le code qu'ils jugent.
- **Context engineering** : chaque dev ne lit que sa tâche, ses RG/ES et le contrat d'API.
- **Traçabilité** : les identifiants US/RG/ES/T vont du PRD jusqu'aux noms des tests ;
  `relecteur-conformite` vérifie cette chaîne.
- **Formats de sortie imposés** (notes du Critique, avis des relecteurs) : le chef d'orchestre
  peut appliquer la règle de décision sans interpréter.

## Différence avec la version Python

| | Claude Code | Python (LangGraph) |
| --- | --- | --- |
| Orchestration | Décrite en langage naturel (SKILL.md) | Codée (graphe, état, conditions) |
| Seuils et plafonds | Consignes que le modèle suit | `if` dans le code : garantis |
| Arrêts humains | Le chef d'orchestre s'arrête et attend | `interrupt()` + reprise |
| Travaille sur | Votre vrai dépôt, votre vraie stack | Un dossier de sortie, code généré |
| Idéal pour | Le travail quotidien sur vos projets | Comprendre, enseigner, intégrer à un produit |

Limite à garder en tête : ici, c'est le modèle qui suit le workflow. C'est fiable, mais ce n'est
pas une garantie comme un `if` dans du code. D'où les formats de sortie stricts, le journal
`docs/pipeline/` et les deux arrêts humains.
