# AskMyData

AskMyData est une application web permettant d’interroger des sources de données en langage naturel grâce à un agent IA.

L’objectif est de permettre à un utilisateur non technique de connecter une source de données, poser une question en français ou en anglais, obtenir une requête contrôlée, puis recevoir une réponse compréhensible en langage naturel.

## Objectifs du projet

- Concevoir une architecture modulaire multi-connecteurs.
- Développer une application Python orientée API.
- Mettre en place un backend Django et un service FastAPI.
- Conteneuriser l’application avec Docker.
- Ajouter des tests automatisés.
- Mettre en place une CI/CD avec GitHub Actions.
- Déployer une version démo à faible coût.
- Ajouter du monitoring applicatif.
- Prévoir l’internationalisation français / anglais dès le départ.

## Périmètre MVP

La première version se concentre sur PostgreSQL.

Fonctionnalités prévues :

- création d’un projet ;
- ajout d’une source PostgreSQL de démonstration ;
- lecture automatique du schéma ;
- question en langage naturel ;
- génération d’une requête SQL en lecture seule ;
- validation de sécurité de la requête ;
- exécution contrôlée ;
- réponse en langage naturel ;
- historique des questions ;
- interface bilingue français / anglais.

## Stack envisagée

- Python
- Django
- FastAPI
- PostgreSQL
- SQLAlchemy
- LangChain ou LlamaIndex
- Docker
- pytest
- GitHub Actions
- Sentry
- Grafana ou Grafana Cloud