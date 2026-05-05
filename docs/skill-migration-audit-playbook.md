# Playbook — Audit de migration d'une skill Claude Code vers Holmes MCP

> **Usage :** Ce document est une méthodologie reproductible pour évaluer si une skill Claude Code existante peut migrer vers Holmes MCP comme unique couche d'accès aux données Jeedom.  
> **Durée estimée :** 1 session (2–3 h selon la taille de la skill)  
> **Produits livrables :** 1 document d'analyse (session record) + éventuellement une mise à jour de ce playbook

---

## Vue d'ensemble du processus

```
Phase 1 — Cadrage (15 min)
    ↓
Phase 2 — Exploration duale en parallèle (45 min)
    ├─ Exploration skill source
    └─ Exploration Holmes MCP
    ↓
Phase 3 — Gap analysis fonctionnelle (30 min)
    ↓
Phase 4 — Macro étude de migration (30 min)
    ↓
Phase 5 — Impacts Holmes MCP (15 min)
    ↓
Phase 6 — Production des livrables (30 min)
```

---

## Phase 1 — Cadrage

### 1.1 Identifier le périmètre exact

Avant toute exploration, fixer par écrit :

- **Skill auditée :** chemin absolu du repository + nom de la skill
- **Objectif :** gap analysis + macro étude migration + impacts Holmes MCP
- **Ce qui n'est PAS dans le scope :** écrire le code de migration, modifier Holmes MCP, toucher à la skill

### 1.2 Directive invariante

> **Aucune modification n'a lieu durant cet audit.** Toute action de type `Edit`, `Write`, `Bash` modifiant un fichier des repositories audités est hors scope.

### 1.3 Rappeler les contraintes Holmes MCP connues

Avant d'explorer, noter les contraintes déjà documentées de `query_sql()` qui impactent systématiquement les comparaisons :

| Contrainte | Comportement |
|------------|--------------|
| LIMIT auto-injectée | 50 si absent, max 200 — `COUNT(*)` non affecté |
| Backticks | Mots réservés MySQL (`trigger`, `repeat`, `update`) doivent être écrits manuellement |
| Blacklist tables | `user`, `session`, `network`, patterns `creds*`, `password*`, `token*` |
| Colonnes sensibles | Explicit SELECT de `password`, `token`, `apikey`, etc. rejeté ; SELECT * autorisé et filtré |
| Version Jeedom | 4.5+ uniquement (Bookworm) |

---

## Phase 2 — Exploration duale en parallèle

Lancer les deux explorations **simultanément** (agents parallèles). Ne pas attendre le résultat de l'un pour démarrer l'autre.

### 2.1 Exploration de la skill source

**Question centrale :** Que fait cette skill, comment accède-t-elle aux données, et quelle connaissance domaine est embarquée ?

**Axes d'investigation :**

```
1. Structure du repository
   - Quelles skills existent (scope global du repo)
   - Arborescence de la skill auditée

2. Inventaire des workflows / features
   - Lister exhaustivement les cas d'usage supportés
   - Pour chaque workflow : ce qu'il fait, quelles données il consomme,
     ce qu'il produit (format de sortie)
   - Ce que la skill refuse explicitement (hors scope documenté)

3. Couche d'accès aux données
   - Mécanismes de connexion (SSH, API, MySQL direct, fichiers)
   - Scripts d'accès : db_query, api_call, logs_query, etc.
   - Logique de routing (si plusieurs vecteurs disponibles)
   - Gestion des credentials (où, comment, sécurité)

4. Scripts helpers et modules communs
   - Rôle précis de chaque script
   - Inputs/outputs (stdin/stdout ou paramètres)
   - Dépendances entre scripts
   - Logique de sécurité embarquée (blacklists, sanitisation)

5. Documentation de référence
   - Quels fichiers .md ou .txt constituent la base de connaissance
   - Contenu : recettes SQL, templates de rapport, seuils métier,
     grammaires de parsing, schémas de plugins, etc.
   - Volume (lignes)

6. Contraintes de version
   - Versions du système cible supportées / rejetées
   - Dépendances externes (Python version, librairies, etc.)
```

**Fichiers à lire en priorité :**
- Fichier de manifest principal (SKILL.md, README.md, ou équivalent)
- Tous les scripts Python/shell (pas seulement les lister)
- Les fichiers de référence/documentation embarquée
- Les exemples d'acceptation s'ils existent

### 2.2 Exploration de Holmes MCP

**Question centrale :** Quels outils Holmes MCP expose-t-il, avec quelles contraintes, et quelles données peut-il fournir ?

**Axes d'investigation :**

```
1. Inventaire complet des outils (25 outils en V1.0)
   - Nom, paramètres, valeur retournée
   - Regroupement par famille fonctionnelle
   - Outils qui enrichissent via l'API en plus de MySQL

2. Capacités SQL (query_sql)
   - Ce qui est permis / blacklisté
   - Comportements automatiques (LIMIT, backticks, filtrage)
   - Format de retour (_filtered_fields, rows, error)

3. Canaux de données disponibles
   - MySQL : quelles tables, lecture seule, contraintes
   - API JSON-RPC : opérations disponibles, coût (N+1 ?)
   - Fichiers logs : chemin, format, grep disponible

4. Ressources MCP (Resource Objects)
   - Liste des 5 ressources statiques/templated
   - Ce qu'elles retournent

5. Authentification et déploiement
   - Comment un client se connecte (Bearer token, URL)
   - Pas de setup client-side

6. Limitations connues et décisions de design
   - Ce qui est hors scope V1 (write, alerting, etc.)
   - Raisons documentées des choix (ADRs si disponibles)
```

**Fichiers à lire en priorité :**
- Code des outils (fichiers Python définissant les tools FastMCP)
- Middleware de sécurité (sanitisation, blacklists)
- README / documentation utilisateur des outils
- ADRs pertinents (decisions/)

---

## Phase 3 — Gap analysis fonctionnelle

### 3.1 Construire la matrice de couverture

Pour chaque workflow de la skill, déterminer :

| WF | Nom | Données Holmes MCP | Verdict | Gap résiduel |
|----|-----|-------------------|---------|--------------|
| WFn | ... | Outils utilisés | ✅/⚠️/❌ | ... |

**Règles de verdict :**

- **✅ Données couvertes** — Holmes MCP expose nativement toutes les données nécessaires via des outils dédiés. La logique de rapport/analyse peut rester dans la skill.
- **⚠️ Partiel** — Les données sont accessibles mais via `query_sql()` avec des requêtes SQL manuelles, ou via assemblage de plusieurs outils. Fonctionnel mais moins ergonomique.
- **❌ Gap fonctionnel** — Une donnée nécessaire n'est pas accessible du tout via Holmes MCP (ni outils, ni `query_sql()`).

### 3.2 Distinguer gap fonctionnel et gap de connaissance

C'est la distinction la plus importante de l'analyse :

| Type | Définition | Exemple jeedom-audit | Action |
|------|------------|---------------------|--------|
| **Gap fonctionnel** | Donnée inaccessible via Holmes MCP | Graphe d'usage cmd→scénarios (WF6) | Candidat outil Holmes MCP |
| **Gap de connaissance** | Logique métier absente de Holmes, mais données disponibles | Seuils health-checks, templates rapport | Reste dans SKILL.md — c'est normal |

> Les gaps de connaissance ne sont pas des limitations Holmes MCP. C'est la valeur ajoutée de la skill.

### 3.3 Questions à se poser pour chaque workflow

1. De quelles données a besoin ce workflow ?
2. Ces données sont-elles dans MySQL, l'API, ou les logs ?
3. Holmes MCP a-t-il un outil dédié qui les retourne directement ?
4. Si non, `query_sql()` peut-il les récupérer ? Avec quelles contraintes ?
5. La logique de traitement (seuils, templates, parsing) doit-elle rester dans la skill ou pourrait-elle être dans Holmes MCP ?
6. Quel est l'impact sur l'ergonomie d'utilisation si on passe par `query_sql()` plutôt qu'un outil dédié ?

---

## Phase 4 — Macro étude de migration

### 4.1 Classifier chaque composant de la skill

Pour chaque script, module, et fichier de référence de la skill, le classer en :

| Catégorie | Définition | Action pour le projet migration |
|-----------|------------|----------------------------------|
| **Éliminer** | Remplacé complètement par Holmes MCP | Supprimer du projet |
| **Transformer** | Doit être réécrit pour utiliser Holmes MCP | Identifier le travail (nouveau code ou adaptation SKILL.md) |
| **Conserver** | Valeur ajoutée de la skill, Holmes MCP ne peut pas le remplacer | Aucune action |

**Heuristiques de classification :**

```
→ Éliminer :
  - Scripts d'accès aux données (SSH, MySQL, API) → outils Holmes MCP
  - Modules de credentials / routing → architecture Holmes MCP
  - Modules de sanitisation → Holmes MCP filtre à la source
  - Documentation de setup / connexion → obsolète

→ Transformer :
  - SQL cookbook → évaluer requête par requête (outil dédié vs query_sql ?)
  - Invocations de scripts dans SKILL.md → appels d'outils MCP
  - Gestion de version du système cible → get_install_overview()

→ Conserver :
  - Seuils métier et logique de scoring (health-checks)
  - Templates de rapport et formats de sortie
  - Grammaires de parsing (comment interpréter les données)
  - Connaissance domaine des plugins / composants
  - Logique d'orchestration des workflows
```

### 4.2 Quantifier la réduction

Estimer pour les livrables :
- Lignes Python supprimées
- Lignes Markdown de référence supprimées
- Ce qui reste (volume SKILL.md final estimé)

### 4.3 Identifier les contraintes de migration

Chercher spécifiquement les points où le comportement de Holmes MCP **diffère** de ce que la skill faisait :

- **LIMIT auto-injectée :** Y a-t-il des requêtes exhaustives qui seront silencieusement tronquées ?
- **Backticks :** La skill avait-elle un auto-backtick ? Si oui, à documenter dans SKILL.md.
- **Gestion d'erreurs :** La skill avait-elle des retry, timeouts, fallbacks ? Holmes en gère certains, pas tous.
- **Version compatibility :** Y a-t-il des utilisateurs de versions non supportées par Holmes MCP ?
- **Mode offline :** La skill fonctionnait-elle sans connexion réseau ? Holmes MCP requiert un daemon actif.

### 4.4 Traiter le cas des requêtes SQL sans outil dédié (WF6-like)

Pour les workflows sans outil Holmes MCP dédié, produire les requêtes SQL de substitution :

```sql
-- Documenter : quel workflow, quel besoin
-- Tester : les colonnes et tables existent-elles dans Jeedom 4.5+ ?
-- Vérifier : LIMIT explicite si listing, backticks si mots réservés
-- Format : paramètre sous forme de ?  ou directement littéral selon contexte
```

Ces requêtes vont dans la section dédiée de SKILL.md, pas dans Holmes MCP.

---

## Phase 5 — Impacts sur Holmes MCP

### 5.1 Identifier les outils manquants

Pour chaque gap fonctionnel (❌) et gap partiel significatif (⚠️), évaluer :

| Critère | Question |
|---------|----------|
| **Généricité** | Cet outil serait-il utile à d'autres clients MCP, ou seulement à cette skill ? |
| **Effort** | La logique SQL/API est-elle déjà documentée quelque part (cookbook, helper scripts) ? |
| **Sécurité** | Expose-t-il des données sensibles ? Nécessite-t-il une nouvelle règle de filtrage ? |
| **Priorité** | Est-ce bloquant pour la migration, ou contournable via `query_sql()` ? |

**Format de spécification suggéré pour un nouvel outil :**

```python
nom_outil(parametre: type, ...) → {
  "champ1": type,   # description
  "champ2": type,   # description
  "warnings": [str] # cas limites à signaler au LLM
}
# Source : remplace <script_source.py> / requêtes <section-cookbook.md>
```

### 5.2 Identifier les clarifications de comportement

Pour chaque contrainte Holmes MCP qui diffère du comportement de la skill :

- Faut-il documenter la contrainte dans la description de l'outil (`query_sql`) ?
- Faut-il changer le comportement (auto-backtick, exemption LIMIT sur COUNT) ?
- Ou suffit-il de documenter dans le playbook / SKILL.md de la skill migrée ?

### 5.3 Vérifier la compatibilité de version

- Holmes MCP supporte-t-il la même plage de versions Jeedom que la skill ?
- Y a-t-il des schémas MySQL différents entre versions qui pourraient créer des problèmes ?

---

## Phase 6 — Production des livrables

### 6.1 Document d'analyse session (obligatoire)

Créer dans `docs/sessions/` avec le format `YYYY-MM-DD-j<N>-audit-<skill-name>.md` :

```markdown
# J<N>-audit — Gap analysis & macro étude de migration <skill> → Holmes MCP

## 1. Contexte         (skill source, Holmes MCP, objectif)
## 2. Gap analysis     (tableau workflow × couverture)
## 3. Macro migration  (éliminer / transformer / conserver + SQL de substitution)
## 4. Impacts Holmes   (outils suggérés, clarifications, compatibilité)
## 5. Synthèse         (tableaux décisionnels pour chaque destinataire)
## Annexe              (mapping scripts → outils, si pertinent)
```

### 6.2 Mise à jour du playbook (si nécessaire)

Si l'audit a révélé un pattern d'investigation non couvert par ce playbook, le mettre à jour avant de clore la session.

### 6.3 Checklist de clôture

```
[ ] Gap analysis complète (tous les workflows couverts)
[ ] Au moins 1 verdict ✅, ⚠️ ou ❌ par workflow
[ ] Gaps fonctionnels distingués des gaps de connaissance
[ ] Chaque composant classé Éliminer/Transformer/Conserver
[ ] Contraintes de migration documentées (LIMIT, backticks, version)
[ ] Requêtes SQL de substitution écrites pour les ⚠️
[ ] Impacts Holmes MCP listés et priorisés
[ ] Document de session écrit dans docs/sessions/
[ ] Aucune modification apportée aux repositories audités
```

---

## Exemple de référence : jeedom-audit (J8-audit, 2026-05-05)

| Résultat | Valeur |
|----------|--------|
| Skill auditée | jeedom-audit V1.1.0+ — 13 workflows, ~2 000 lignes Python, ~3 200 lignes Markdown |
| Gap fonctionnel | 1 seul : WF6 (graphe d'usage cmd→scénarios) |
| Gaps de connaissance | 4 (seuils health, templates rapport, grammaire scénario, tier-1 plugins) — restent dans skill |
| Composants éliminés | 13 (7 scripts + 6 modules) + ~2 000 lignes Markdown de référence |
| Composants conservés | 7 (health-checks, audit-templates, scenario-grammar, 6 plugin guides) |
| Contraintes identifiées | LIMIT auto-injectée, backticks manuels, Jeedom 4.4.x abandonné |
| Impacts Holmes MCP | 1 outil suggéré (`find_command_usages`), 2 clarifications doc, 1 FAQ |
| Document session | `docs/sessions/2026-05-05-j8-audit-migration-jeedom-skill.md` |

---

## Patterns découverts en J7bis-2

### Compatibilité JSON MariaDB vs MySQL

`CAST(col AS JSON)` est syntaxe MySQL pure — échoue sur MariaDB (Jeedom Bookworm) avec `ProgrammingError: 1064`. Substitution :

```sql
-- MySQL (ne pas utiliser sur Jeedom)
JSON_CONTAINS(arr_col, CAST(id_col AS JSON))

-- MariaDB (correct)
JSON_SEARCH(arr_col, 'one', CAST(id_col AS CHAR)) IS NOT NULL
```

Point connexe : `scenario.scenarioElement` stocke les IDs comme chaînes JSON (`["502"]`), pas comme entiers (`[502]`). `JSON_SEARCH` avec `CAST AS CHAR` est cohérent avec ce format.

**À vérifier systématiquement** lors des tests live : toute requête SQL de substitution impliquant `JSON_CONTAINS` avec un entier doit être testée sur MariaDB avant d'être documentée.

---

## Notes d'utilisation

**Pour rejouer cet audit sur une autre skill :**

1. Remplacer les références à jeedom-audit par la skill cible dans les prompts d'exploration (Phase 2)
2. Adapter la liste des workflows à la structure de la nouvelle skill
3. Les contraintes Holmes MCP (Phase 1.3) sont fixes — ne pas les adapter
4. Le template de document session (Phase 6.1) est fixe

**Ce playbook n'est pas adapté pour :**
- Auditer Holmes MCP lui-même (périmètre différent)
- Évaluer une skill qui accède à un système autre que Jeedom
- Évaluer la migration vers autre chose que Holmes MCP
