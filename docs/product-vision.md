# Product Vision

## 1. Présentation

AskMyData est une application web permettant d'interroger différentes sources de données en langage naturel grâce à un agent d'intelligence artificielle.

L'utilisateur peut connecter une source de données, poser une question en français ou en anglais et obtenir une réponse en langage naturel, accompagnée de la requête exécutée et des résultats associés.

L'application est conçue comme une plateforme extensible pouvant supporter plusieurs types de sources de données sans modifier le cœur de l'application.

---

# 2. Problématique

Les données sont souvent stockées dans des bases de données ou des fichiers nécessitant des compétences techniques pour être exploitées.

Même lorsque les données sont disponibles, les utilisateurs métiers doivent généralement :

- connaître SQL ;
- comprendre le schéma de la base ;
- demander l'aide d'un développeur ou d'un data analyst.

L'objectif est de réduire cette dépendance en permettant une interrogation des données en langage naturel.

---

# 3. Objectifs

Le projet poursuit plusieurs objectifs.

## Objectif fonctionnel

Permettre à un utilisateur de :

- connecter une source de données ;
- explorer automatiquement son schéma ;
- poser une question en langage naturel ;
- obtenir une réponse fiable et compréhensible.

## Objectif technique

Concevoir une application moderne mettant en œuvre :

- une architecture modulaire ;
- une API REST ;
- un moteur IA indépendant ;
- une architecture extensible basée sur des connecteurs ;
- des pratiques d'industrialisation.

## Objectif pédagogique

Le projet sert de support d'apprentissage afin d'acquérir et démontrer des compétences en :

- architecture logicielle ;
- développement Python ;
- Django ;
- FastAPI ;
- Docker ;
- tests automatisés ;
- CI/CD ;
- déploiement cloud ;
- monitoring ;
- développement d'applications intégrant des LLM.

---

# 4. Public cible

Le projet s'adresse principalement à :

- des utilisateurs non techniques ;
- des équipes métiers ;
- des analystes ;
- des développeurs souhaitant explorer rapidement une base de données.

La version actuelle est développée comme démonstrateur technique pour un portfolio.

---

# 5. Cas d'utilisation principal

1. L'utilisateur crée un projet.
2. Il ajoute une source de données.
3. L'application analyse automatiquement le schéma.
4. L'utilisateur pose une question.
5. L'agent IA génère une requête adaptée.
6. La requête est validée.
7. La requête est exécutée.
8. Les résultats sont reformulés en langage naturel.
9. L'utilisateur peut consulter l'historique.

---

# 6. Fonctionnalités

## Version MVP

- gestion de projets ;
- connexion à PostgreSQL ;
- découverte automatique du schéma ;
- questions en langage naturel ;
- génération de SQL ;
- validation de sécurité ;
- exécution en lecture seule ;
- réponse en langage naturel ;
- historique des questions ;
- interface bilingue français / anglais.

## Versions futures

- CSV ;
- JSON ;
- BigQuery ;
- MongoDB ;
- autres bases SQL ;
- visualisation graphique des résultats ;
- génération automatique de tableaux de bord ;
- gestion de plusieurs utilisateurs ;
- authentification externe ;
- partage de projets.

---

# 7. Principes de conception

Le projet est conçu selon les principes suivants :

- séparation des responsabilités ;
- architecture modulaire ;
- extensibilité ;
- sécurité par défaut ;
- observabilité ;
- internationalisation ;
- documentation systématique ;
- qualité logicielle.

---

# 8. Internationalisation

L'application est conçue dès l'origine pour être multilingue.

La première version proposera :

- Français
- English

L'ajout de nouvelles langues devra pouvoir être réalisé sans modification importante du code.

---

# 9. Contraintes

- coût de déploiement faible ;
- application démonstrative publique ;
- architecture proche d'un environnement de production ;
- open source autant que possible ;
- sécurité des connexions aux bases de données.

---

# 10. Critères de réussite

Le projet sera considéré comme réussi si :

- une base PostgreSQL peut être connectée sans développement spécifique ;
- une question en langage naturel produit une réponse pertinente ;
- l'application est entièrement conteneurisée ;
- les tests sont automatisés ;
- la CI/CD est opérationnelle ;
- une démonstration est accessible en ligne ;
- l'architecture permet d'ajouter un nouveau connecteur avec un impact minimal sur le reste de l'application.

---

# 11. Non-objectifs

La première version de l'application n'a pas vocation à :

- remplacer un outil de Business Intelligence ;
- modifier les données des sources connectées ;
- entraîner un modèle d'intelligence artificielle ;
- prendre en charge toutes les bases de données existantes ;
- gérer un très grand nombre d'utilisateurs simultanément.