# Use Cases

## Acteurs

### Utilisateur

Personne utilisant l'application pour interroger des données.

### Administrateur

Personne administrant l'application (version future).

### Agent IA

Service chargé de comprendre la question, générer une requête et reformuler les résultats.

### Source de données

Système externe contenant les données (PostgreSQL dans le MVP).

---

# UC01 - Créer un projet

Acteur principal : Utilisateur

Objectif :
Créer un nouvel espace de travail.

Scénario nominal :

1. L'utilisateur clique sur "Nouveau projet".
2. Il saisit un nom.
3. Le projet est créé.

Résultat :

Le projet apparaît dans la liste.

---

# UC02 - Ajouter une source de données

Acteur principal : Utilisateur

Objectif :

Ajouter une connexion PostgreSQL.

Scénario nominal :

1. L'utilisateur ouvre un projet.
2. Il clique sur "Ajouter une source".
3. Il renseigne les paramètres.
4. L'application teste la connexion.
5. La source est enregistrée.

Résultat :

La source est disponible.

---

# UC03 - Explorer le schéma

Acteur principal : Utilisateur

Objectif :

Découvrir automatiquement la structure de la base.

Scénario nominal :

1. L'utilisateur sélectionne une source.
2. L'application lit le schéma.
3. Les tables sont affichées.
4. Les colonnes sont affichées.
5. Les relations sont affichées.

Résultat :

Le schéma est disponible.

---

# UC04 - Poser une question

Acteur principal : Utilisateur

Objectif :

Interroger les données.

Scénario nominal :

1. L'utilisateur saisit une question.
2. La question est envoyée à l'agent IA.
3. Une requête SQL est générée.
4. La requête est validée.
5. La requête est exécutée.
6. Les résultats sont reformulés.
7. La réponse est affichée.

Résultat :

L'utilisateur obtient une réponse.

---

# UC05 - Consulter l'historique

Acteur principal : Utilisateur

Objectif :

Retrouver les anciennes questions.

Scénario nominal :

1. L'utilisateur ouvre l'historique.
2. Les conversations sont affichées.
3. Une conversation peut être rouverte.

---

# UC06 - Changer de langue

Acteur principal : Utilisateur

Objectif :

Modifier la langue de l'interface.

Scénario nominal :

1. L'utilisateur ouvre les paramètres.
2. Il sélectionne Français ou English.
3. Toute l'interface est mise à jour.

---

# Cas d'utilisation futurs

- Ajouter un connecteur CSV
- Ajouter un connecteur JSON
- Ajouter MongoDB
- Ajouter BigQuery
- Exporter les résultats
- Générer des graphiques
- Ajouter des utilisateurs
- Partager un projet