# Installation

## 1. Prérequis

- **Python 3.10 ou plus récent** (le code utilise la syntaxe `str | None`).
  Vérifiez : `python3 --version`
- Une **clé API** chez [OpenRouter](https://openrouter.ai/) ou [Groq](https://console.groq.com/).

## 2. Créer l'environnement Python

Depuis le dossier `agent_officiel/` :

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows : .venv\Scripts\activate
pip install -r requirements.txt
```

Trois bibliothèques seulement :

| Bibliothèque | Pourquoi |
|---|---|
| `requests` | faire les appels HTTP vers l'API du LLM |
| `python-dotenv` | lire la clé API dans le fichier `.env` |
| `pytest` | uniquement pour la leçon 16 : l'agent testeur lance les tests |

## 3. Configurer la clé API

```bash
cp .env.example .env
```

Puis ouvrez `.env` et renseignez **une** des deux configurations :

```ini
# OpenRouter
API_KEY=sk-or-...
API_ROUTE=https://openrouter.ai/api/v1/chat/completions
MODELE=openai/gpt-oss-120b
```

```ini
# Groq
API_KEY=gsk_...
API_ROUTE=https://api.groq.com/openai/v1/chat/completions
MODELE=openai/gpt-oss-120b
```

Un seul `.env`, à la racine du cours, suffit : `load_dotenv()` le trouve en remontant les dossiers
depuis `code/lecon_NN/cerveau/llm.py`.

> **Sécurité :** ne publiez jamais votre `.env` (il est listé dans `.gitignore`).

### Et les autres fournisseurs ?

OpenRouter et Groq sont donnés en exemple. Le code fonctionne avec **n'importe quel service
compatible avec l'API *chat completions* d'OpenAI** (y compris un modèle local) : il suffit de
renseigner sa route, sa clé et le nom du modèle dans `.env`. C'est l'objet de l'exercice 5 de la
[leçon 01](lecons/01_parler_a_un_llm.md). À partir de la leçon 06, choisissez un modèle qui gère
l'appel d'outils.

## 4. Vérifier

```bash
cd code/lecon_01
python exemple.py
```

Vous devez voir une réponse du modèle et la consommation de tokens.

## Problèmes fréquents

| Message | Cause probable |
|---|---|
| `API_KEY ou API_ROUTE introuvable` | le fichier `.env` n'existe pas ou n'est pas à la racine du cours |
| `Erreur API 401` | clé invalide, ou clé OpenRouter utilisée avec la route Groq (ou l'inverse) |
| `Erreur API 404` / modèle introuvable | le nom dans `MODELE` n'existe pas chez ce fournisseur |
| `Erreur API 429` | limite de requêtes atteinte : attendez, ou changez de fournisseur/modèle |
| `ModuleNotFoundError: No module named 'agent'` | lancez le script **depuis** le dossier de la leçon (`cd code/lecon_NN`) |
| Réponse vide | le modèle a utilisé tous ses tokens : augmentez `max_tokens` dans `ClientLLM` |

## Coût

Chaque exemple fait de quelques appels (leçons 01 à 11) à plusieurs dizaines d'appels (leçons 14 à 16).
Le projet final, lui, enchaîne **de nombreux appels** (plusieurs par agent et par tâche). La leçon 11 vous apprend à mesurer
précisément la consommation (tokens) de vos agents ; consultez les tarifs de votre fournisseur.
