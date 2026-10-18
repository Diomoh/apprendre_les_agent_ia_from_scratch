# Cahier des charges : LivrAbidjan

**Client** : LivrAbidjan, start-up de livraison de colis à moto
**Zone** : Grand Abidjan, avec un lancement pilote à Cocody, Plateau et Marcory
**Délai** : un MVP en trois mois

## 1. Contexte
LivrAbidjan veut mettre en relation des clients (particuliers et petites boutiques) qui ont
un colis à faire livrer, et des livreurs indépendants à moto. Beaucoup d'adresses à Abidjan
ne sont pas normalisées : on se repère avec des points connus (« face à la pharmacie… »).

## 2. Besoins

### 2.1 Commander une course
Le client indique un point de retrait et un point de livraison sur une carte, et peut ajouter
un repère en texte libre. Le prix est affiché avant qu'il valide. Il dépend de la zone de départ
et de la zone d'arrivée.

### 2.2 Attribuer la course à un livreur
Les livreurs voient les courses proposées autour d'eux et en acceptent une. Un livreur ne peut
pas mener plusieurs courses en même temps.

### 2.3 Suivre la livraison
Le client suit la position de son livreur pendant la course. La livraison est confirmée par un
code à 4 chiffres que le destinataire donne au livreur.

### 2.4 Payer
Au lancement, paiement en espèces à la livraison. Le paiement mobile money viendra ensuite.

### 2.5 Administrer
Un administrateur gère les zones, la grille de prix et la liste des livreurs, depuis un back-office web.

## 3. Contraintes
- Applications mobiles pour les clients et les livreurs, back-office web pour l'administrateur.
- Réseau mobile parfois instable : l'app livreur doit tolérer les coupures.
- Les données des clients (téléphone, adresses) sont personnelles et doivent être protégées.
