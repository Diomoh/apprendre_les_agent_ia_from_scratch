"""
agent.py - Leçon 07 : TOUT l'agent dans UN seul fichier.

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

from cerveau.llm import ClientLLM

# =====================================================================
# 1. CONFIGURATION
# =====================================================================

MAX_ETAPES = 8  # garde-fou : la boucle s'arrête TOUJOURS

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

def executer(llm: ClientLLM, objectif: str, max_etapes: int = MAX_ETAPES) -> dict:
    """Fait tourner la boucle et renvoie l'ÉTAT final (réponse, étapes, journal)."""
    etat = nouvel_etat(objectif)
    messages = [
        {"role": "system", "content": f"{ROLE}\n\n{CONSIGNES_AGENT}"},
        {"role": "user", "content": objectif},
    ]

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
    return etat


# =====================================================================
# 7. LA CONVERSATION DANS LE TERMINAL
# =====================================================================

def main():
    llm = creer_cerveau()
    print(f"Agent prêt ({llm.modele}). Tapez 'quit' pour sortir.")
    while True:
        message = input("\nVous > ").strip()
        if message.lower() in {"quit", "exit", "q"}:
            break
        if not message:
            continue
        try:
            etat = executer(llm, message)
        except Exception as erreur:  # noqa: BLE001 - on garde la main en cas d'erreur réseau
            print(f"Erreur : {erreur}")
            continue
        print(f"Agent > {etat['reponse_finale']}")


if __name__ == "__main__":
    main()
