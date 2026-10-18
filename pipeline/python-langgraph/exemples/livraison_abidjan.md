# Cahier des charges : application de livraison dans le Grand Abidjan

## Contexte
Nous voulons lancer une application de livraison de colis à moto dans le Grand Abidjan,
d'abord sur quelques communes pilotes (Cocody, Plateau, Marcory).

## Besoins
- Un client commande une course en indiquant un point de retrait et un point de livraison sur une carte.
  Beaucoup d'adresses ne sont pas normalisées : il faut pouvoir ajouter un repère (« face à la pharmacie… »).
- Le prix est affiché avant que le client valide. Il dépend des zones de départ et d'arrivée.
- Les livreurs sont indépendants. Ils voient les courses proposées et en acceptent une.
- Le client suit son livreur pendant la course.
- La livraison est confirmée par un code donné par le destinataire.
- Un administrateur gère les zones, la grille de prix et les livreurs.

## Contraintes
- Application mobile pour les clients et les livreurs, back-office web pour l'administrateur.
- Réseau mobile parfois instable.
- Délai : un MVP en trois mois.
