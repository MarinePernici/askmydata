# AskMyData

[English](README.md)

**Exploration de données PostgreSQL en langage naturel avec génération et exécution contrôlées de requêtes SQL.**

AskMyData est une application web permettant d'explorer des données structurées sans avoir à écrire soi-même des requêtes SQL. L'utilisateur connecte une source de données PostgreSQL, sélectionne les données accessibles à l'application, puis pose ses questions en langage naturel.

AskMyData construit un Knowledge Catalog sémantique à partir du schéma sélectionné de la base de données, l'utilise pour générer des requêtes SQL, valide chaque requête avant son exécution, exécute les requêtes validées avec un accès en lecture seule, puis produit des réponses en langage naturel.

> **État : MVP terminé — Industrialisation en cours.**
>
> Le parcours complet d'exploration de données PostgreSQL est implémenté et a été validé sur un jeu de données réaliste. Le travail actuel porte sur l'industrialisation, la CI/CD, l'observabilité, le déploiement et la préparation d'un environnement de démonstration public.

## Fonctionnalités principales

- Exploration de données PostgreSQL en langage naturel
- Découverte automatique du schéma de la base de données
- Knowledge Catalog sémantique avec descriptions générées et synonymes orientés métier
- Pipeline contrôlé de génération SQL à partir du langage naturel
- Validation obligatoire du SQL avant exécution
- Accès en lecture seule aux sources de données externes
- Respect du Catalog Scope limitant les schémas et tables accessibles
- Clarification des questions analytiques ambiguës
- Rejet des questions auxquelles les données du projet ne permettent pas de répondre
- Conversations contextualisées avec historique persistant
- Traces d'exécution pour le diagnostic du pipeline de requêtes
- Tests automatisés et benchmark qualité documenté
- Environnement de développement Docker Compose

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

Lorsqu'une question est ambiguë ou nécessite une définition métier manquante, AskMyData peut demander une clarification avant de générer du SQL. Lorsque l'information demandée ne peut pas être déduite des données disponibles dans le projet, la question est rejetée sans exécution SQL.

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

AskMyData sépare la génération, la validation et l'exécution SQL en étapes distinctes. Chaque requête générée doit passer par une validation applicative avant de pouvoir atteindre la base de données externe.

Les mécanismes de protection actuels comprennent :

- opérations SQL en lecture seule ;
- validation SQL obligatoire avant exécution ;
- respect du Catalog Scope pour les schémas et tables accessibles ;
- identifiants de base de données en lecture seule ;
- limites d'exécution des requêtes ;
- validation des résultats avant génération de la réponse ;
- traces d'exécution pour le diagnostic du pipeline ;
- gestion des secrets par variables d'environnement.

Les requêtes qui échouent à la validation SQL ne sont pas exécutées. Les questions nécessitant des informations absentes des données disponibles dans le projet sont rejetées avant d'atteindre l'exécution SQL.

Les instructions fournies au LLM sont considérées comme des indications et non comme une frontière de sécurité. Les permissions de la base de données et la validation applicative restent responsables de l'application effective des restrictions d'accès.

## Architecture

AskMyData suit une architecture en **monolithe modulaire** construite avec Django.

L'application est organisée en modules aux responsabilités explicites :

- **Accounts** — authentification et identité utilisateur
- **Projects** — cycle de vie et configuration des projets
- **Data Source** — configuration des bases externes et test des connexions
- **Knowledge Catalog** — découverte du schéma et métadonnées sémantiques
- **Conversation** — conversations et historique des messages
- **Query Engine** — construction du contexte, génération SQL, validation, exécution et génération des réponses
- **Connectors** — abstractions pour les bases de données et fournisseurs LLM
- **Observability** — traces d'exécution et diagnostic

Les systèmes externes sont accessibles au travers d'abstractions de connecteurs explicites.

PostgreSQL est actuellement la seule source de données implémentée. L'architecture est conçue pour permettre l'ajout d'autres connecteurs sans coupler le modèle de domaine à une technologie de base de données spécifique.

L'accès aux LLM est également indépendant du fournisseur afin de permettre de changer de fournisseur sans modifier le cœur du workflow de requête.

Pour le détail des composants et des décisions d'architecture, voir la [documentation d'architecture](docs/application-components.md) et les [ADR](docs/adrs/README.md).

## Stack technique

### Application

- Python
- Django
- PostgreSQL
- Django Templates
- HTML / CSS
- JavaScript limité

### Données et traitement des requêtes

- psycopg
- pglast pour l'analyse et la validation du SQL PostgreSQL
- intégration LLM indépendante du fournisseur

### Développement et qualité

- framework de tests Django
- Ruff
- Docker
- Docker Compose
- Git / GitHub

## Qualité et validation

Le MVP a été évalué au travers d'un benchmark qualité documenté utilisant la base d'exemple PostgreSQL Pagila.

Le benchmark couvre le parcours complet de l'application, notamment :

- découverte du schéma et génération du catalogue sémantique ;
- agrégations simples et complexes ;
- filtrage temporel ;
- jointures multi-tables et relations many-to-many ;
- contexte conversationnel et clarification ;
- validation SQL et respect du Catalog Scope ;
- métriques métier non définies ;
- questions auxquelles les données du projet ne permettent pas de répondre.

Quatorze scénarios de requêtes et un scénario de génération du catalogue ont été évalués par comparaison avec des résultats PostgreSQL de référence.

Le benchmark a également servi de démarche qualité itérative : les problèmes fonctionnels et d'utilisabilité identifiés lors des tests sur des données réalistes ont été analysés, corrigés puis validés par des tests automatisés et de nouveaux tests sur les données réelles.

Au dernier point de validation documenté dans le benchmark, la suite de tests complète exécutée sous Docker comptait **371 tests réussis**.

Voir le [benchmark qualité du MVP](docs/benchmark/mvp-quality-benchmark.md) pour la méthodologie complète, les scénarios, les résultats, les problèmes identifiés et leurs résolutions.

## Développement local

### Prérequis

- Docker
- Docker Compose

### Installation

Clonez le dépôt et créez le fichier d'environnement local :

```bash
git clone https://github.com/MarinePernici/AskMyData.git
cd AskMyData
cp .env.example .env
```

Vérifiez le fichier `.env` et configurez les valeurs nécessaires, notamment les identifiants du fournisseur LLM.

Construisez et démarrez l'application :

```bash
docker compose build
docker compose up -d
docker compose exec web python manage.py migrate
```

L'application est ensuite accessible à l'adresse :

```text
http://localhost:8000/projects/
```

### Tests

Exécutez la suite de tests complète dans le conteneur de l'application :

```bash
docker compose exec web python manage.py test
```

### Qualité du code

Vérifiez le code avec Ruff :

```bash
uv run ruff check .
uv run ruff format --check .
```

Formatez le code si c'est nécessaire :

```bash
uv run ruff format .
```

### Arrêt de l'environnement

```bash
docker compose down
```

### Base PostgreSQL pour les tests d'intégration

Les tests utilisant une véritable source PostgreSQL externe s'appuient sur des variables d'environnement `TEST_SOURCE_DB_*` dédiées.

Lorsque la base de test s'exécute sur l'hôte Docker, le conteneur de l'application peut y accéder via `host.docker.internal`.

La base d'intégration doit utiliser des identifiants dédiés et ne doit pas pointer vers une base de production ou une base personnelle.

## Roadmap

### Terminé — Fondations

- Architecture Django modulaire
- Modèle de domaine et persistance
- Connecteur PostgreSQL
- Fondations du Knowledge Catalog
- Pipeline langage naturel vers SQL
- Validation SQL et exécution en lecture seule
- Traces d'exécution

### Terminé — MVP

- Authentification utilisateur
- Création et gestion des projets
- Configuration et test des connexions PostgreSQL
- Gestion sécurisée des identifiants des sources de données
- Sélection du Catalog Scope
- Découverte du schéma et génération du Knowledge Catalog sémantique
- Régénération du Knowledge Catalog
- Exploration des données en langage naturel
- Conversations contextualisées et historique persistant
- Clarification des questions ambiguës
- Rejet des questions non supportées par les données du projet
- Validation SQL et respect du périmètre d'accès
- Couverture par des tests automatisés
- Environnement de développement Docker Compose
- Benchmark qualité sur une base PostgreSQL réaliste

### En cours — Industrialisation

Le travail actuel vise à transformer le MVP validé en une application portfolio publique et déployable.

Les travaux prévus comprennent :

- CI/CD avec GitHub Actions
- analyse statique et vérification des types
- logs structurés
- health checks
- monitoring et suivi des erreurs
- configuration Docker orientée production
- déploiement cloud
- environnement de démonstration public sécurisé
- jeux de données de démonstration prédéfinis
- accès par invitation et outils d'administration

### Extensions futures

L'architecture est conçue pour permettre l'ajout futur de nouvelles sources de données, mais ces extensions sont volontairement hors du périmètre actuel d'industrialisation.

## Documentation

La documentation détaillée du projet est disponible dans [`docs/`](docs/) :

- [Vision produit](docs/product-vision.md)
- [Périmètre du MVP](docs/mvp-scope.md)
- [Exigences](docs/requirements.md)
- [Cas d'utilisation fonctionnels](docs/functional-use-cases.md)
- [Modèle de domaine](docs/domain-model.md)
- [Composants applicatifs](docs/application-components.md)
- [Design System](docs/design-system.md)
- [Architecture Decision Records](docs/adrs/README.md)
- [Benchmark qualité du MVP](docs/benchmark/mvp-quality-benchmark.md)
- [Diagrammes PlantUML](docs/diagrams/README.md)

Cette documentation retrace les principales décisions produit, métier, architecturales et techniques prises au cours du projet.

## Contexte du projet

AskMyData est un projet portfolio personnel conçu et développé pour explorer les problématiques d'ingénierie liées à la création d'une interface contrôlée en langage naturel pour des données structurées.

Le projet permet également d'approfondir la pratique de l'architecture logicielle, du développement Python et Django,de l'ingénierie des données, de la sécurisation du SQL, de l'intégration de LLM, des tests automatisés, de la conteneurisation et des pratiques de développement orientées production.

Au-delà de la réalisation d'un prototype fonctionnel, le projet suit une démarche de développement documentée comprenant les exigences, la modélisation du domaine, les décisions d'architecture, les tests fonctionnels, un benchmark qualité sur des données réalistes et une progression vers un niveau de préparation à la production.
