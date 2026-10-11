"""
agent.py - Leçon 08 : TOUT l'agent dans UN seul fichier.

Le dossier cerveau/ (leçons 01-06) parle au modèle. Ce fichier contient tout le
reste, à lire de haut en bas :

    1. la configuration
    2. les outils : des fonctions Python ordinaires
    3. le registre des outils : leur description pour le modèle (format "tools")
    4. l'exécution d'un outil demandé par le modèle
    5. l'état de l'agent et son journal
    6. LA BOUCLE de l'agent (décider -> agir -> observer)
    7. la conversation dans le terminal

Lancer depuis ce dossier :  python agent.py
"""

import json
from datetime import datetime
from pathlib import Path

from cerveau.llm import ClientLLM

# =====================================================================
# 1. CONFIGURATION
# =====================================================================

MAX_ETAPES = 8  # garde-fou : la boucle s'arrête TOUJOURS
FICHIER_MEMOIRE = Path("memoire_longue.json")  # mémoire longue (faits)
TAILLE_MEMOIRE_COURTE = 10  # nombre de messages de conversation renvoyés au modèle

ROLE = (
    "Tu es un assistant IA calme, précis et serviable. "
    "Tu dis honnêtement quand tu ne sais pas. Tu réponds en français."
)
CONSIGNES_AGENT = (
    "Tu es un agent. Pour atteindre l'objectif, tu peux appeler des outils, "
    "autant de fois que nécessaire, en plusieurs étapes. "
    "N'invente jamais un résultat d'outil : appelle l'outil. "
    "Quand tu as tout ce qu'il faut, réponds directement sans appeler d'outil."
)


def creer_cerveau() -> ClientLLM:
    """Le client LLM des leçons 01-06 (cerveau/llm.py)."""
    llm = ClientLLM()
    return llm


# =====================================================================
# 2. LES OUTILS : des fonctions Python ordinaires
# =====================================================================

def calculatrice(a: float, b: float, operation: str) -> float:
    if operation == "addition":
        return a + b
    if operation == "soustraction":
        return a - b
    if operation == "multiplication":
        return a * b
    if operation == "division":
        if b == 0:
            raise ValueError("division par zéro")
        return a / b
    raise ValueError(f"opération inconnue : {operation}")


def heure_actuelle() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# --- Mémoire longue : une liste de faits dans un fichier JSON (leçon 08) ---

def charger_memoire() -> list[str]:
    if not FICHIER_MEMOIRE.exists():
        return []
    try:
        return json.loads(FICHIER_MEMOIRE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def memoriser(fait: str) -> str:
    fait = fait.strip()
    faits = charger_memoire()
    if fait and fait not in faits:
        faits.append(fait)
        FICHIER_MEMOIRE.write_text(json.dumps(faits, ensure_ascii=False, indent=2), encoding="utf-8")
    return f"Mémorisé : {fait}"


def rechercher_memoire(requete: str) -> list[str]:
    mots = [mot for mot in requete.lower().split() if len(mot) > 2]
    return [fait for fait in charger_memoire() if any(mot in fait.lower() for mot in mots)]


# =====================================================================
# 3. LE REGISTRE DES OUTILS : ce que le modèle a le droit de demander
# =====================================================================

OUTILS: dict[str, dict] = {}  # nom de l'outil -> fonction Python + description pour l'API


def ajouter_outil(nom: str, fonction, description: str, proprietes: dict | None = None,
                  obligatoires: list[str] | None = None):
    """Enregistre un outil : la fonction à exécuter et sa description pour le modèle."""
    OUTILS[nom] = {
        "fonction": fonction,
        "parametres": {"type": "object", "properties": proprietes or {}, "required": obligatoires or []},
        "description": description,
    }


def schemas_outils() -> list[dict]:
    """La liste des outils au format du champ "tools" de l'API (leçon 06)."""
    return [
        {"type": "function",
         "function": {"name": nom, "description": outil["description"], "parameters": outil["parametres"]}}
        for nom, outil in OUTILS.items()
    ]


ajouter_outil(
    "calculatrice", calculatrice, "Fait une opération entre deux nombres.",
    {"a": {"type": "number"}, "b": {"type": "number"},
     "operation": {"type": "string", "enum": ["addition", "soustraction", "multiplication", "division"]}},
    ["a", "b", "operation"],
)
ajouter_outil("heure_actuelle", heure_actuelle, "Donne la date et l'heure actuelles.")
ajouter_outil(
    "memoriser", memoriser,
    "Enregistre durablement un fait utile sur l'utilisateur ou le contexte "
    "(préférence, nom, décision). Une phrase courte et autonome.",
    {"fait": {"type": "string"}}, ["fait"],
)
ajouter_outil(
    "rechercher_memoire", rechercher_memoire,
    "Cherche dans la mémoire longue les faits contenant certains mots-clés.",
    {"requete": {"type": "string"}}, ["requete"],
)


# =====================================================================
# 4. EXÉCUTER UN OUTIL : le modèle DEMANDE, le code EXÉCUTE
#    Règle d'or : toujours renvoyer un texte, jamais planter.
# =====================================================================

def executer_outil(nom: str, arguments_json: str | None) -> str:
    if nom not in OUTILS:
        return f"ERREUR : outil inconnu « {nom} ». Outils disponibles : {list(OUTILS)}"
    try:
        arguments = json.loads(arguments_json or "{}")  # l'API envoie une CHAÎNE JSON
    except json.JSONDecodeError:
        return "ERREUR : les arguments ne sont pas un JSON valide."
    if not isinstance(arguments, dict):
        return "ERREUR : les arguments doivent être un objet JSON."
    outil = OUTILS[nom]

    try:
        resultat = outil["fonction"](**arguments)
    except Exception as erreur:  # noqa: BLE001 - l'erreur devient un résultat lisible
        return f"ERREUR pendant l'exécution de {nom} : {erreur}"
    return resultat if isinstance(resultat, str) else json.dumps(resultat, ensure_ascii=False)


# =====================================================================
# 5. L'ÉTAT DE L'AGENT : explicite et inspectable (un simple dictionnaire)
# =====================================================================

def nouvel_etat(objectif: str) -> dict:
    return {"objectif": objectif, "etapes": 0, "termine": False, "reponse_finale": None, "journal": []}


def noter(etat: dict, type_evenement: str, detail):
    """Ajoute une ligne au journal (décision, observation, réponse...)."""
    etat["journal"].append({"etape": etat["etapes"], "type": type_evenement, "detail": detail})


# =====================================================================
# 6. LA BOUCLE DE L'AGENT : décider -> agir -> observer, jusqu'à la réponse
# =====================================================================

def construire_messages(objectif: str, historique: list[dict] | None) -> list[dict]:
    """Le contexte = rôle + souvenirs (mémoire longue) + derniers échanges (mémoire courte)."""
    souvenirs = charger_memoire()[-30:]
    bloc_souvenirs = (
        "Ce que tu sais déjà (mémoire longue) :\n" + "\n".join(f"- {fait}" for fait in souvenirs)
        if souvenirs else "Ta mémoire longue est vide."
    )
    recents = (historique or [])[-TAILLE_MEMOIRE_COURTE:]
    while recents and recents[0]["role"] != "user":  # on commence toujours par un message user
        recents = recents[1:]
    return (
        [{"role": "system", "content": f"{ROLE}\n\n{CONSIGNES_AGENT}\n\n{bloc_souvenirs}"}]
        + recents
        + [{"role": "user", "content": objectif}]
    )


def executer(llm: ClientLLM, objectif: str, historique: list[dict] | None = None,
             max_etapes: int = MAX_ETAPES) -> dict:
    """
    Fait tourner la boucle et renvoie l'ÉTAT final (réponse, étapes, journal).
    historique : la mémoire courte (une liste), ou None pour ne rien retenir.
    """
    etat = nouvel_etat(objectif)
    messages = construire_messages(objectif, historique)

    while not etat["termine"] and etat["etapes"] < max_etapes:
        etat["etapes"] += 1

        # DÉCIDER : le modèle répond, ou demande des outils
        reponse = llm.discuter_avec_outils(messages, schemas_outils())

        if not reponse["tool_calls"]:  # pas d'outil demandé = réponse finale
            noter(etat, "reponse", reponse["content"])
            etat["termine"] = True
            etat["reponse_finale"] = (reponse["content"] or "").strip()
            break

        noter(etat, "decision", [appel["function"]["name"] for appel in reponse["tool_calls"]])
        messages.append(reponse)  # la demande d'outils du modèle

        # AGIR + OBSERVER : chaque résultat est relié à sa demande par tool_call_id
        observations = []
        for appel in reponse["tool_calls"]:
            resultat = executer_outil(appel["function"]["name"], appel["function"]["arguments"])
            print(f"  [étape {etat['etapes']}] {appel['function']['name']} → {resultat[:150]}")
            messages.append({"role": "tool", "tool_call_id": appel["id"], "content": resultat})
            observations.append(resultat[:200])
        noter(etat, "observation", observations)

    if not etat["termine"]:
        etat["reponse_finale"] = f"Arrêt : {max_etapes} étapes atteintes sans réponse finale."

    # Mémoire courte : on ne garde que l'objectif et la réponse finale
    if historique is not None:
        historique.append({"role": "user", "content": objectif})
        historique.append({"role": "assistant", "content": etat["reponse_finale"]})
    return etat


# =====================================================================
# 7. LA CONVERSATION DANS LE TERMINAL
# =====================================================================

def main():
    llm = creer_cerveau()
    historique: list[dict] = []  # la mémoire courte de la conversation
    print(f"Agent prêt ({llm.modele}). Tapez 'quit' pour sortir.")
    while True:
        message = input("\nVous > ").strip()
        if message.lower() in {"quit", "exit", "q"}:
            break
        if not message:
            continue
        try:
            etat = executer(llm, message, historique)
        except Exception as erreur:  # noqa: BLE001 - on garde la main en cas d'erreur réseau
            print(f"Erreur : {erreur}")
            continue
        print(f"Agent > {etat['reponse_finale']}")


if __name__ == "__main__":
    main()
