# AskMyData

AskMyData est une application web permettant d'explorer des données structurées en langage naturel.

L'application vise à rendre l'exploration de données accessible à des utilisateurs qui n'ont pas besoin d'écrire eux-mêmes des requêtes SQL. Un utilisateur connecte une source de données, sélectionne les données qu'il souhaite rendre accessibles à AskMyData, puis pose ses questions en langage naturel. AskMyData s'appuie sur un Knowledge Catalog pour comprendre les données disponibles, génère une requête SQL, la valide avant toute exécution, l'exécute avec un accès en lecture seule, puis produit une réponse compréhensible en langage naturel.

La première version se concentre sur PostgreSQL tout en conservant une architecture extensible à d'autres sources de données structurées.

> AskMyData est actuellement en cours de développement. Le projet est construit de manière incrémentale à partir d'une architecture et de spécifications documentées.

## Fonctionnement

Un parcours typique dans AskMyData est le suivant :

1. Créer un projet.
2. Configurer une source de données PostgreSQL et tester la connexion.
3. Sélectionner les schémas et les tables qui définissent le Catalog Scope du projet.
4. Découvrir le schéma de la source et construire le Knowledge Catalog.
5. Poser une question en langage naturel.
6. Construire le contexte pertinent à partir du Knowledge Catalog et de l'historique de la conversation.
7. Générer une requête SQL.
8. Valider la requête avant son exécution.
9. Exécuter la requête validée avec un accès à la base en lecture seule.
10. Valider le résultat et générer une réponse en langage naturel.

Lorsqu'une question est ambiguë ou ne peut pas recevoir de réponse fiable, AskMyData peut demander une clarification plutôt que de générer une réponse non suffisamment étayée par les données disponibles.

## Knowledge Catalog

Le Knowledge Catalog constitue la couche sémantique entre la source de données externe et le pipeline de requêtes assisté par IA.

Il combine :

- les métadonnées techniques découvertes dans la source ;
- les snapshots du schéma ;
- des descriptions sémantiques générées automatiquement ;
- des synonymes orientés métier.

Chaque projet définit un **Catalog Scope** contenant les schémas et les tables disponibles pour l'exploration.

Le Knowledge Catalog peut être régénéré à partir du schéma actuel de la source tout en conservant ce périmètre.

## Exploration conversationnelle des données

AskMyData prend en charge plusieurs conversations au sein d'un même projet.

Chaque conversation conserve son propre contexte, ce qui permet à l'utilisateur de :

- poser de nouvelles questions ;
- poursuivre des échanges précédents ;
- répondre aux demandes de clarification ;
- revenir à des conversations existantes ;
- conserver des historiques de conversation isolés les uns des autres.

## Sécurité et exécution contrôlée du SQL

Le SQL généré n'est jamais exécuté directement.

Le pipeline sépare la génération, la validation et l'exécution des requêtes. Avant toute exécution, le SQL généré est contrôlé selon des règles de sécurité explicites et par rapport au Catalog Scope du projet.

L'application repose notamment sur les protections suivantes :

- opérations SQL en lecture seule ;
- validation obligatoire du SQL avant exécution ;
- accès limité au Catalog Scope sélectionné ;
- identifiants PostgreSQL externes disposant de droits en lecture seule ;
- limites d'exécution contrôlées ;
- validation des résultats avant la génération de la réponse ;
- traces d'exécution pour le diagnostic et la traçabilité du pipeline ;
- protection des secrets applicatifs et des identifiants des sources de données.

Les instructions fournies au LLM ne sont pas considérées à elles seules comme une frontière de sécurité.

## Architecture

AskMyData suit une architecture de type **monolithe modulaire** construite autour de Django.

L'application est organisée autour de plusieurs capacités métier :

- Accounts ;
- Projects ;
- Data Source Management ;
- Knowledge Catalog ;
- Conversation Management ;
- Query Engine ;
- Connectors ;
- Observability.

Le Query Engine est un module interne de l'application chargé de coordonner le pipeline allant de la question en langage naturel à la réponse.

Les sources de données externes sont accessibles à travers une abstraction de connecteur. PostgreSQL est le seul connecteur implémenté dans le périmètre initial, mais l'architecture est conçue pour permettre l'ajout ultérieur d'autres connecteurs sans refonte architecturale majeure.

L'accès aux LLM repose également sur une interface indépendante du fournisseur.

## Stack technique

### Application

- Python
- Django
- PostgreSQL
- Django Templates
- JavaScript côté client limité

### Accès aux données et IA

- connecteur PostgreSQL
- SQLAlchemy Core ou outil SQL équivalent
- intégration LLM indépendante du fournisseur

### Ingénierie et déploiement

- pytest
- Docker / Docker Compose
- GitHub Actions
- analyse statique et vérification des types
- logs structurés
- health checks
- monitoring et suivi des erreurs

Les outils précis d'infrastructure et d'observabilité seront sélectionnés au cours de la phase Production-ready Portfolio.

## Développement local avec Docker

### Prérequis

- Docker
- Docker Compose

### Configuration de l'environnement

Créez le fichier d'environnement local à partir de l'exemple fourni :

```bash
cp .env.example .env
```

Configurez ensuite les valeurs requises dans `.env`.

### Démarrer l'application

Construisez l'image de l'application :

```bash
docker compose build
```

Démarrez les services :

```bash
docker compose up -d
```

Appliquez les migrations de la base de données :

```bash
docker compose exec web python manage.py migrate
```

L'application est ensuite accessible à l'adresse :

```text
http://localhost:8000/projects/
```

Les utilisateurs non authentifiés sont redirigés vers la page de connexion.

### Exécuter les tests

```bash
docker compose exec web python manage.py test
```

### Arrêter l'application

```bash
docker compose down
```

L'environnement de développement Docker Compose exécute l'application Django et sa base de données PostgreSQL applicative dans des conteneurs distincts.

Les tests d'intégration PostgreSQL utilisent la base de données de test externe configurée à l'aide des variables d'environnement `TEST_SOURCE_DB_*`. Lorsque les tests sont exécutés dans Docker Desktop, la base de données de test exécutée sur l'hôte est accessible via `host.docker.internal`.

## Roadmap de développement

Le développement est organisé en trois étapes incrémentales.

### Foundation

La Foundation permet de valider le pipeline technique principal :

- connexion à PostgreSQL ;
- découverte du schéma ;
- Knowledge Catalog minimal ;
- traitement des questions en langage naturel ;
- génération SQL ;
- validation SQL ;
- exécution en lecture seule ;
- validation des résultats ;
- génération d'une réponse en langage naturel ;
- traces d'exécution ;
- tests automatisés du cœur du système.

### MVP

Le MVP ajoute le parcours utilisateur complet :

- authentification et gestion des sessions ;
- création, modification et archivage des projets ;
- configuration PostgreSQL et test de connexion ;
- gestion sécurisée des identifiants ;
- sélection du Catalog Scope ;
- génération et régénération du Knowledge Catalog ;
- génération automatique des métadonnées sémantiques ;
- exploration du schéma de données ;
- plusieurs conversations contextualisées par projet ;
- historique persistant des conversations ;
- gestion des demandes de clarification ;
- interface web responsive pour les différentes tailles d'écran desktop ;
- environnement de développement Docker Compose.

### Production-ready Portfolio

La dernière phase est consacrée à l'industrialisation et au déploiement :

- couverture de tests plus complète ;
- analyse statique et vérification des types ;
- CI/CD avec GitHub Actions ;
- images Docker de production ;
- logs structurés et monitoring ;
- health checks ;
- suivi des erreurs ;
- déploiement cloud ;
- environnement de démonstration public ;
- accès sur invitation ;
- outils d'administration ;
- internationalisation et préférences utilisateur.

## Périmètre actuel

Le périmètre actuel est volontairement limité.

PostgreSQL est la seule source de données externe prise en charge.

Sont notamment exclus du périmètre actuel du portfolio :

- les connecteurs supplémentaires vers d'autres bases de données ou fichiers ;
- les systèmes multi-agents autonomes ;
- la mémoire IA à long terme ;
- le fine-tuning ;
- l'exploration documentaire basée sur du RAG ;
- les espaces de travail collaboratifs ;
- les fonctionnalités avancées d'analytics ;
- les fonctionnalités destinées aux environnements enterprise ;
- l'édition manuelle des métadonnées sémantiques ;
- la gestion manuelle des synonymes ;
- la comparaison avancée des versions du Knowledge Catalog ;
- les interfaces spécifiquement conçues pour mobile.

Ces limitations sont volontaires afin de concentrer le projet sur un parcours d'exploration de données complet, sécurisé, testable et déployable.

## Documentation

Le projet est documenté avant et pendant son implémentation.

La documentation détaillée couvre notamment :

- la vision produit ;
- le périmètre du MVP ;
- les exigences fonctionnelles et non fonctionnelles ;
- les cas d'utilisation fonctionnels ;
- le modèle de domaine ;
- les composants applicatifs ;
- le design system ;
- les Architecture Decision Records (ADR) ;
- les diagrammes d'architecture et de domaine en PlantUML.

Cette documentation sert de référence pour les décisions d'implémentation.

## Objectifs du projet

AskMyData est également un projet portfolio destiné à mettre en pratique et approfondir des compétences en :

- développement d'applications Python ;
- architecture Django ;
- data engineering et SQL ;
- intégration de LLM ;
- accès sécurisé aux données assisté par IA ;
- architecture logicielle ;
- tests automatisés ;
- Docker ;
- CI/CD ;
- observabilité ;
- déploiement en production.

L'objectif n'est pas uniquement de construire un prototype IA fonctionnel, mais de développer un projet logiciel structuré intégrant explicitement des choix d'architecture, des contraintes de sécurité, des tests, de la documentation et des pratiques de déploiement.
