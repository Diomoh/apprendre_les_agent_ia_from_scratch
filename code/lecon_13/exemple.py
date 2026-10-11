"""
Leçon 13 - Communication entre agents : messages directs + tableau partagé.

Trois agents produisent un court article SANS chef d'orchestre :
chacun sait à qui transmettre son travail.

Lancer depuis ce dossier :  python exemple.py
"""

from agent.agent import Agent
from agent.outils import BoiteAOutils
from multi.bus import BusMessages, TableauPartage
from multi.communication import ajouter_outils_communication, faire_circuler
from multi.messages import Message

bus = BusMessages()
tableau = TableauPartage()
bus.inscrire("humain")  # l'humain a aussi une boîte aux lettres

ROLES = {
    "planificateur": (
        "Tu es planificateur éditorial. Quand tu reçois une tâche, tu écris un plan en "
        "3 parties, tu le publies sur le tableau sous la clé « plan », puis tu envoies "
        "une tâche à « redacteur » pour lui demander d'écrire l'article à partir du plan."
    ),
    "redacteur": (
        "Tu es rédacteur. Quand tu reçois une tâche, tu lis « plan » sur le tableau, "
        "tu écris un article de 150 mots maximum, tu le publies sous la clé « brouillon », "
        "puis tu envoies une tâche à « relecteur ». Si tu reçois des remarques, tu "
        "republies « brouillon » corrigé et tu préviens « relecteur »."
    ),
    "relecteur": (
        "Tu es relecteur. Tu lis « brouillon » sur le tableau. S'il a un défaut important, "
        "tu envoies UNE fois des remarques à « redacteur ». Sinon (ou à la deuxième "
        "relecture), tu envoies un message de type resultat à « humain » qui dit que "
        "l'article est prêt."
    ),
}

agents = []
for nom, role in ROLES.items():
    agent = Agent(nom=nom, role=role + " Tu réponds en français.", outils=BoiteAOutils(),
                  outils_memoire=False)
    ajouter_outils_communication(agent, bus, tableau)
    agents.append(agent)

# L'humain lance le travail en écrivant au planificateur
bus.envoyer(Message("humain", "planificateur", "tache",
                    "Prépare un court article sur les bienfaits de la marche quotidienne."))

nombre = faire_circuler(agents, bus, max_messages=10)

print(f"\n=== {nombre} messages traités ===")
print("Documents sur le tableau :", tableau.cles())
if "brouillon" in tableau.cles():
    print("\n" + tableau.lire("brouillon"))

print("\nBoîte de l'humain :")
while (message := bus.prendre_suivant("humain")) is not None:
    print(f"- de {message.expediteur} : {message.contenu}")

print("\nHistorique des échanges :")
for message in bus.historique:
    print(f"  {message.id} {message.expediteur:>13} → {message.destinataire:<13} [{message.type}]")
