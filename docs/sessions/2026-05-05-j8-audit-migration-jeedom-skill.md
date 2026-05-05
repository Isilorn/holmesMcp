# J8-audit — Gap analysis & macro étude de migration jeedom-audit → Holmes MCP

> **Session :** J8-audit (hors roadmap)  
> **Date :** 2026-05-05  
> **Périmètre :** Analyse uniquement — aucune migration effectuée  
> **Destinataires :** PO Holmes MCP (évolution produit) + projet Claude Code jeedom-skills (brief de migration)

---

## Contexte

**jeedom-audit** est une skill Claude Code (V1.1.0+) qui implémente 13 workflows d'audit read-only d'une installation Jeedom 4.5.x. Elle embarque sa propre couche d'accès aux données (SSH+MySQL, API JSON-RPC, SSH logs) via 7 scripts helper, 6 modules communs, et ~3 200 lignes de documentation de référence.

**Holmes MCP** est un plugin natif Jeedom exposant 25 outils + 5 ressources via MCP (Model Context Protocol). Il est également read-only et fournit un accès MySQL, API JSON-RPC et logs locaux — sans SSH client-side.

L'objectif de cette session est de déterminer dans quelle mesure Holmes MCP peut absorber jeedom-audit comme client exclusif, et ce qui reste à faire pour que cette migration soit possible.

---

## 1. Gap analysis fonctionnelle

### Rappel des 13 workflows de jeedom-audit

| WF | Nom | Description courte |
|----|-----|--------------------|
| WF1 | Audit général | Rapport de santé complet (10-20 requêtes batch) |
| WF2 | Diagnostic scénario | Pourquoi un scénario ne se déclenche plus |
| WF3 | Diagnostic équipement | Équipement mort / ne répond plus |
| WF4 | Diagnostic plugin | Daemon/statut plugin en erreur |
| WF5 | Explication scénario | Pseudo-code lisible du scénario |
| WF6 | Graphe d'usage | Qui utilise une commande / un équipement / un scénario |
| WF7 | Suggestions refactor | Anti-patterns + recommandations de nettoyage |
| WF8-11 | Quick reads | Valeur courante, historique, variable, recherche |
| WF12 | Cartographie orchestration | Flux inter-scénarios (mermaid ou prose) |
| WF13 | Forensique causale | Remontée de cause racine multi-sources |

### Couverture par Holmes MCP

| WF | Verdict | Outils Holmes MCP utilisés | Gap résiduel |
|----|---------|---------------------------|--------------|
| **WF1** | ✅ Données couvertes | `get_install_overview()`, `get_health_summary()`, `list_plugins()`, `query_sql()` | Logique de seuils (health-checks.md) et templates de rapport (audit-templates.md) restent dans la skill |
| **WF2** | ✅ Couverture complète | `describe_scenario()`, `get_scenario_log()`, `get_scenario_structure()` | `describe_scenario()` intègre la résolution `#cmdId#` que jeedom-audit faisait en 2 scripts séparés |
| **WF3** | ⚠️ Partiel | `get_equipment()` (enrichi `currentValue`+`collectDate` via API) | Pas de connaissance des schémas plugin-spécifiques (batterie, communication) — ces patterns restent dans la skill |
| **WF4** | ✅ Couverture complète | `list_plugins()`, `get_health_summary()` (daemons nok) | — |
| **WF5** | ✅ Couverture complète | `describe_scenario()` | scenario-grammar.md doit rester dans la skill pour que le LLM interprète les types/subtypes |
| **WF6** | ❌ Gap significatif | `find_scenario_dependencies()` (scenario→scenario uniquement), `search_text()`, `query_sql()` | Pas d'outil dédié pour `cmd → scénarios` (triggers/conditions/actions/dataStore) — coverage partielle via `query_sql()` avec requêtes SQL manuelles |
| **WF7** | ✅ Données couvertes | `query_sql()`, outils d'inventaire | Définitions d'anti-patterns et templates de rapport restent dans la skill |
| **WF8-11** | ✅ Mieux couvert | `get_equipment()`, `get_command_history()`, `get_datastore_variable()`, `find_*` | Holmes a des outils dédiés plus ergonomiques que les scripts directs |
| **WF12** | ✅ Couverture complète | `get_scenario_structure(follow_scenario_calls=1-3)`, `find_scenario_dependencies()` | Template mermaid reste dans la skill |
| **WF13** | ✅ Données couvertes | `get_scenario_log()`, `tail_log()`, `get_command_history()`, `get_health_summary()`, `query_sql()` | Méthodologie d'investigation multi-tour reste dans la skill |

**Verdict global :** Holmes MCP couvre l'intégralité des données nécessaires aux 13 workflows. **Un seul gap fonctionnel réel : WF6** (graphe d'usage cmd → scénarios). Tous les autres gaps sont des questions de logique applicative (seuils, templates, grammaire) qui appartiennent à la skill, pas à l'infrastructure.

---

## 2. Macro étude de migration

### 2.1 Ce qui disparaît complètement

| Composant jeedom-audit | Remplacé par | Note |
|------------------------|--------------|------|
| `scripts/setup.py` | Configuration Holmes MCP (plugin Jeedom UI) | Plus de credentials SSH/MySQL côté client |
| `scripts/api_call.py` | Outils Holmes MCP (Family 1–5) | Blacklist, retry, filtrage gérés par Holmes |
| `scripts/db_query.py` | `query_sql()` + outils spécialisés | Holmes gère l'injection LIMIT, backticks, sanitisation |
| `scripts/logs_query.py` | `tail_log()`, `get_scenario_log()` | Même interface, sans SSH |
| `scripts/scenario_tree_walker.py` | `get_scenario_structure()` + `describe_scenario()` | Holmes intègre récursion, cycle detection, résolution ID |
| `scripts/resolve_cmd_refs.py` | `describe_scenario()` (résolution intégrée) | Fonctionnalité native Holmes |
| `scripts/usage_graph.py` | `find_scenario_dependencies()` + `query_sql()` | Partiel : scenario→scenario natif, cmd→scenario via SQL |
| `_common/credentials.py` | Supprimé | Auth déportée sur Holmes MCP (Bearer token) |
| `_common/ssh.py` | Supprimé | Pas de SSH client-side |
| `_common/router.py` | Supprimé | Routage MySQL/API interne à Holmes |
| `_common/sensitive_fields.py` | Supprimé | Sanitisation 3 couches dans Holmes |
| `_common/version_check.py` | `get_install_overview()` | Retourne la version directement |
| `references/connection.md` | Supprimé | Procédure de setup obsolète |
| `references/api-jsonrpc.md` | Supprimé | Abstrait par Holmes MCP |
| `references/api-http.md` | Supprimé | Abstrait par Holmes MCP |

**Impact volumétrique estimé :** ~2 000 lignes Python supprimées, ~2 000 lignes Markdown de référence supprimées.

### 2.2 Ce qui se transforme

#### sql-cookbook.md (674 lignes) — restructuration partielle

| Catégorie cookbook | Statut | Remplacé par |
|--------------------|--------|--------------|
| System & config | Supprimé | `get_install_overview()`, `get_config()` |
| Plugins | Supprimé | `list_plugins()` |
| Equipment (eqLogic) | Supprimé | `list_equipments()`, `find_equipments_advanced()`, `get_equipment()` |
| Commands (cmd) | Supprimé | `list_commands()`, `find_commands_advanced()` |
| Scenarios | Supprimé | `list_scenarios()`, `find_scenarios_advanced()`, `get_scenario()` |
| Scenario content | Supprimé | `get_scenario_structure()`, `describe_scenario()` |
| Variables | Supprimé | `list_datastore_variables()`, `get_datastore_variable()` |
| History | Supprimé | `get_command_history()` |
| System messages | Supprimé | `get_health_summary()` |
| Audit batch (WF1) | Supprimé | Combinaison d'outils Holmes |
| **Tier-1 plugins** | **Conservé réduit** | `query_sql()` + connaissance inline — requêtes plugin-spécifiques non couvertes par les outils génériques |

#### WF6 — requêtes SQL de remplacement à inliner dans la skill

`usage_graph.py` se réécrit en 3 requêtes `query_sql()` à conserver dans SKILL.md :

```sql
-- Scénarios dont ce cmd est un trigger
SELECT id, name FROM scenario
WHERE JSON_CONTAINS(`trigger`, '"#<cmd_id>#"')

-- Expressions (conditions/actions) référençant ce cmd
-- ⚠️ MariaDB : CAST(... AS JSON) non supporté — utiliser JSON_SEARCH (corrigé J7bis-2)
SELECT se.expression, sse.subtype, s.id AS scenario_id, s.name AS scenario_name
FROM scenarioExpression se
JOIN scenarioSubElement sse ON se.scenarioSubElement_id = sse.id
JOIN scenarioElement sel ON sse.scenarioElement_id = sel.id
JOIN scenario s ON JSON_SEARCH(s.scenarioElement, 'one', CAST(sel.id AS CHAR)) IS NOT NULL
WHERE se.expression LIKE '%#<cmd_id>#%'

-- Variables dataStore référençant ce cmd
SELECT `key`, value, link_id FROM dataStore
WHERE value LIKE '%#<cmd_id>#%'
```

Ces requêtes ont les mêmes contraintes que `query_sql()` : backticks sur `trigger` obligatoires, LIMIT à spécifier explicitement pour les listings.

> **Note J7bis-2 :** La requête expressions ci-dessus remplace la syntaxe originale `CAST(sel.id AS JSON)` qui échoue sur MariaDB (Jeedom Bookworm). `find_command_usages()` utilise la syntaxe corrigée depuis J7bis-2. Les deux autres requêtes (trigger et dataStore) sont inchangées.

#### SKILL.md — restructuration profonde

| Section | Action |
|---------|--------|
| Setup / credentials | Supprimer — remplacer par instructions connexion Holmes MCP (URL + Bearer token) |
| Invocations de scripts (db_query, api_call, etc.) | Supprimer — remplacer par appels d'outils MCP |
| Routing logic | Supprimer — interne à Holmes |
| Seuils health-checks.md | **Conserver intégralement** |
| Templates rapport audit-templates.md | **Conserver intégralement** |
| Grammaire scénario (scenario-grammar.md) | **Conserver intégralement** |
| Documentation tier-1 plugins (6 fichiers) | **Conserver intégralement** |
| Pattern plugin générique | **Conserver intégralement** |
| Tags système (#trigger_id#, etc.) | Migrer en instruction inline (logique de tags.py) |
| SQL WF6 | **Ajouter** (3 requêtes ci-dessus) |
| Contraintes Holmes MCP | **Ajouter** (voir §2.3) |

### 2.3 Contraintes Holmes MCP à documenter dans la skill migrée

Ces comportements de `query_sql()` diffèrent de `db_query.py` et doivent être expliqués dans SKILL.md pour éviter des erreurs silencieuses :

1. **LIMIT auto-injecté :** `query_sql()` injecte `LIMIT 50` si absent, max 200. Les `COUNT(*)` ne sont pas affectés mais les listings exhaustifs peuvent être tronqués silencieusement. Toujours spécifier `LIMIT` explicitement ou utiliser `COUNT(*)`.
2. **Backticks manuels :** `db_query.py` auto-backtiquait `trigger`, `repeat`, `update`. `query_sql()` ne le fait pas — écrire systématiquement `` `trigger` ``, `` `repeat` ``, `` `update` ``.
3. **Version Jeedom ≥ 4.5 uniquement :** Holmes MCP cible Jeedom 4.5+ (Bookworm). Le support Jeedom 4.4.x (actuellement supporté avec warnings par jeedom-audit) disparaît.

### 2.4 Ce qui reste inchangé

| Composant | Raison de conservation |
|-----------|------------------------|
| `references/health-checks.md` | Logique métier (seuils ✅/⚠️/❌) : appartient à la skill, pas à l'infrastructure |
| `references/audit-templates.md` | Templates de rapport WF1/WF7/WF12 |
| `references/scenario-grammar.md` | Interprétation des types/subtypes `scenarioExpression` |
| `references/plugin-virtual.md` + 5 autres | Schémas de configuration plugin-spécifiques — Holmes ne les connaît pas |
| `references/plugin-generic-pattern.md` | Pattern d'inspection générique pour les autres plugins |
| Architecture des 13 workflows | La logique d'orchestration des requêtes et de construction des rapports |

---

## 3. Impacts sur Holmes MCP

### Impact A — Outil manquant : `find_command_usages()` *(priorité moyenne)*

C'est le seul vrai gap fonctionnel de la migration. WF6 doit actuellement se rabattre sur 3 `query_sql()` manuels. Un outil dédié apporterait de la valeur à tous les clients MCP, pas seulement à la skill migrée.

**Spécification suggérée :**

```python
find_command_usages(cmd_id: int) → {
  "cmd_id": int,
  "cmd_name": str,
  "triggers": [{"scenario_id": int, "scenario_name": str}],
  "conditions": [{"scenario_id": int, "scenario_name": str, "expression": str}],
  "actions": [{"scenario_id": int, "scenario_name": str, "expression": str}],
  "datastore_refs": [{"key": str, "link_id": int, "scope": "global"|"scenario"}],
  "false_positive_warnings": [str]  # IDs trouvés dans blocs PHP (coïncidences possibles)
}
```

La logique SQL est déjà documentée dans sql-cookbook.md (section "graphe d'usage"). C'est une implémentation directe.

### Impact B — Comportement LIMIT sur `query_sql()` *(priorité faible — documentation)*

L'injection automatique de `LIMIT 50` peut tronquer silencieusement des résultats pour les requêtes de listing sans `LIMIT` explicite. Deux options :

- **Option 1 (doc) :** Documenter ce comportement explicitement dans la description de l'outil et dans le README.
- **Option 2 (code) :** Exempter les requêtes purement aggregatives (`SELECT COUNT(*)`, `SELECT SUM(...)`, `SELECT MAX(...)`) de l'injection LIMIT.

### Impact C — Auto-backtick sur mots réservés MySQL *(priorité faible — qualité de vie)*

`db_query.py` gérait les mots réservés MySQL (`trigger`, `repeat`, `update`) de façon transparente. `query_sql()` délègue au LLM. Pour un LLM qui formule des requêtes sur les tables Jeedom, les erreurs de syntaxe MySQL sur ces mots sont fréquentes.

**Option :** Dans le parser de `query_sql()`, détecter et auto-backticker les identifiants connus comme réservés dans le contexte Jeedom (liste courte et stable).

### Impact D — Support Jeedom 4.4.x *(impact documentation, pas code)*

jeedom-audit supportait 4.4.x avec avertissements. Holmes MCP cible 4.5+ (Bookworm x86_64). La migration de la skill entraîne une régression de support de version formelle. À documenter dans le CHANGELOG de la skill migrée, et éventuellement dans la FAQ Holmes MCP.

### Impact E — Sécurité : amélioration nette

Holmes MCP a une sanitisation plus robuste que jeedom-audit (3 couches : whitelist, regex, hard-coded plugin list vs 1 couche pattern-matching). La migration améliore le profil sécurité de la skill sans action supplémentaire.

---

## 4. Synthèse

### Pour la décision de migration (brief jeedom-skills)

```
┌──────────────────────────────────────────────────────────────────┐
│  VERDICT MIGRATION jeedom-audit → Holmes MCP                     │
├──────────────────────┬───────────────────────────────────────────┤
│ Faisabilité          │ ✅ Haute — 12/13 WF couverts nativement    │
│ Effort estimé        │ Moyen — refactoring SKILL.md + SQL WF6    │
│ Gain infrastructure  │ Élevé — ~4 000 lignes code/doc supprimées │
│ Régression           │ Faible — WF6 dégradé (SQL manuel),        │
│                      │          support Jeedom 4.4.x supprimé    │
│ Prérequis            │ Holmes MCP installé et accessible          │
└──────────────────────┴───────────────────────────────────────────┘
```

La migration est viable et représente un gain net : la skill se réduit à sa valeur ajoutée (logique métier, connaissance domaine, templates) et délègue entièrement l'accès aux données à Holmes MCP.

### Pour la roadmap Holmes MCP

| # | Item | Priorité | Effort |
|---|------|----------|--------|
| 1 | Nouvel outil `find_command_usages(cmd_id)` | Moyenne | Faible (SQL déjà dans cookbook) |
| 2 | Documenter comportement LIMIT dans `query_sql()` | Faible | Trivial |
| 3 | Auto-backtick mots réservés dans `query_sql()` | Faible | Faible |
| 4 | FAQ : support Jeedom 4.4.x non couvert | Faible | Trivial |

Aucun de ces items n'est bloquant pour la migration. Ils améliorent la qualité de vie des clients MCP en général.

---

## Annexe — Mapping complet scripts → outils Holmes MCP

| Script jeedom-audit | Outil(s) Holmes MCP de substitution |
|---------------------|-------------------------------------|
| `setup.py` | Plugin Jeedom UI + Bearer token |
| `api_call.py` | Tous les outils Family 1–5 selon opération |
| `db_query.py` | `query_sql()` pour les requêtes ad-hoc ; outils spécialisés en priorité |
| `logs_query.py` | `tail_log(log_name, lines, grep)` + `get_scenario_log(scenario_id, lines)` |
| `scenario_tree_walker.py` | `get_scenario_structure(scenario_id, max_depth, follow_scenario_calls)` |
| `resolve_cmd_refs.py` | `describe_scenario()` (résolution intégrée) ; pour usage standalone : `query_sql()` sur `cmd` + `eqLogic` + `object` |
| `usage_graph.py` | `find_scenario_dependencies()` pour scenario→scenario ; 3 requêtes `query_sql()` pour cmd→scenarios (voir §2.2) |
| `_common/credentials.py` | Supprimé |
| `_common/ssh.py` | Supprimé |
| `_common/router.py` | Supprimé (interne à Holmes) |
| `_common/sensitive_fields.py` | Supprimé (Holmes filtre à la source) |
| `_common/version_check.py` | `get_install_overview()` → champ `version` |
| `_common/tags.py` | Instruction inline dans SKILL.md |
