# MVP Scope

## Objectif

Le MVP (Minimum Viable Product) doit démontrer la faisabilité d'une application permettant d'interroger une source de données en langage naturel via un agent IA.

Cette première version doit être suffisamment complète pour être présentée dans un portfolio, tout en restant limitée afin de garantir une architecture propre et une implémentation maîtrisée.

---

# Fonctionnalités incluses

## Gestion des projets

- créer un projet
- modifier un projet
- supprimer un projet

---

## Gestion des sources de données

- ajouter une source PostgreSQL
- tester la connexion
- enregistrer la configuration
- supprimer une source

---

## Analyse du schéma

- découverte automatique des tables
- découverte des colonnes
- découverte des clés étrangères
- mise en cache du schéma

---

## Questions en langage naturel

- poser une question
- choisir la langue de réponse
- conserver l'historique

---

## Génération SQL

- génération automatique
- validation avant exécution
- affichage de la requête générée

---

## Exécution

- lecture seule
- timeout
- limitation du nombre de lignes

---

## Réponse

- affichage des données
- reformulation en langage naturel

---

## Administration

- authentification simple
- paramètres utilisateur

---

## Internationalisation

- Français
- English

---

# Fonctionnalités exclues

Les fonctionnalités suivantes ne font pas partie du MVP.

## Sources de données

- CSV
- JSON
- BigQuery
- MongoDB
- MySQL
- SQL Server
- Oracle

---

## Visualisation

- graphiques
- dashboards
- export PDF

---

## IA

- fine tuning
- mémoire longue durée
- plusieurs modèles IA

---

## Collaboration

- partage de projets
- commentaires
- travail collaboratif

---

## Administration avancée

- rôles
- permissions complexes
- SSO

---

# Critères de validation

Le MVP sera terminé lorsque :

- un utilisateur peut créer un projet ;
- connecter une base PostgreSQL ;
- explorer automatiquement son schéma ;
- poser une question ;
- obtenir une réponse correcte ;
- consulter le SQL généré ;
- retrouver son historique ;
- utiliser l'application en français et en anglais ;
- lancer l'application avec Docker Compose ;
- exécuter les tests automatiquement via GitHub Actions.