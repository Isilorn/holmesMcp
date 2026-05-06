# Brief de migration — jeedom-audit → Holmes MCP

> **Destinataire :** projet Claude Code `jeedom-skills`, branche `develop`
> **Produit par :** Holmes MCP, session J8-1 (2026-05-06)
> **Version Holmes MCP cible :** v1.1.1 (26 tools, 5 resources)
> **Version jeedom-audit source :** main (état au 2026-05-06)

---

## 1. Contexte et objectif

**Situation actuelle :** `jeedom-audit` embarque sa propre couche d'accès aux données — 7 scripts Python (SSH + MySQL + API JSON-RPC + logs) et 6 modules communs. Chaque utilisateur doit configurer un alias SSH, un user MySQL RO sur la box, et des credentials locaux.

**Objectif de la migration :** remplacer cette couche d'accès par des appels aux outils Holmes MCP. Holmes MCP tourne comme daemon sur la box Jeedom et expose les mêmes données via HTTP + Bearer token — sans SSH côté client, sans credentials MySQL côté client, sans installation Python.

**Ce qui ne change pas :**

- La règle d'or lecture seule
- Les 13 workflows et leur logique d'orchestration
- La convention de nommage `#[Objet][Équipement][Commande]#`
- Les fichiers de référence (templates, health-checks, scenario-grammar, guides plugins)
- La philosophie de réponse (markdown lisible, noms pas IDs, données filtrées explicites)

**Périmètre de cette migration :** branche `develop` de `jeedom-skills`. La branche `main` reste inchangée jusqu'à validation complète.

**Ce qui est hors scope :** modifier Holmes MCP, créer de nouveaux outils Holmes MCP, tester la migration sur une autre skill.

---

## 2. Inventaire des composants — Éliminer / Transformer / Conserver

### Éliminer (supprimer du repo)

Ces fichiers sont entièrement remplacés par Holmes MCP. Aucune adaptation possible — les supprimer.

| Fichier | Remplacé par |
|---------|-------------|
| `scripts/setup.py` | Configuration Holmes MCP via page plugin Jeedom (Bearer token) |
| `scripts/api_call.py` | Outils Holmes MCP familles 1–5 |
| `scripts/db_query.py` | `query_sql()` + outils spécialisés Holmes MCP |
| `scripts/logs_query.py` | `tail_log()`, `get_scenario_log()` |
| `scripts/scenario_tree_walker.py` | `get_scenario_structure()`, `describe_scenario()` |
| `scripts/resolve_cmd_refs.py` | `describe_scenario()` (résolution intégrée) |
| `scripts/usage_graph.py` | `find_command_usages()`, `find_scenario_dependencies()` |
| `scripts/_common/credentials.py` | Auth Bearer côté client (config `.mcp.json`) |
| `scripts/_common/ssh.py` | Pas de SSH côté client |
| `scripts/_common/router.py` | Routage interne à Holmes MCP (daemon sur la box) |
| `scripts/_common/sensitive_fields.py` | Sanitisation 3 couches dans Holmes MCP |
| `scripts/_common/version_check.py` | `get_install_overview()` retourne `jeedom_version` |
| `references/connection.md` | Procédure setup SSH/MySQL obsolète |
| `references/api-jsonrpc.md` | API JSON-RPC abstraite par Holmes MCP |
| `references/api-http.md` | Connexion HTTP abstraite par Holmes MCP |

**Volume estimé : ~2 000 lignes Python + ~600 lignes Markdown.**

### Transformer (réécrire)

Ces fichiers doivent être réécrits pour Holmes MCP. Le contenu change mais l'intention reste.

| Fichier | Ce qui change |
|---------|--------------|
| `SKILL.md` | §3 Pré-requis (SSH/MySQL → Bearer token), §Routage (supprimer entièrement), §6 Gotchas (adapter), §7 WF scripts (remplacer par outils Holmes MCP), §9 Index références (supprimer les Éliminer) |
| `references/sql-cookbook.md` | Supprimer les requêtes remplacées par des outils Holmes MCP dédiés. Conserver uniquement les requêtes d'audit avancé passant par `query_sql()`. Mettre à jour les notes sur les backticks et LIMIT. |

### Conserver (ne pas toucher)

Ces fichiers constituent la valeur ajoutée de la skill — ils ne sont pas remplaçables par Holmes MCP.

| Fichier | Contenu |
|---------|---------|
| `references/health-checks.md` | Seuils et critères de santé métier |
| `references/audit-templates.md` | Templates de rapport WF1 (12 sections), WF7 (refactor), WF12 (mermaid) |
| `references/scenario-grammar.md` | Interprétation `scenarioExpression` : types, subtypes, options |
| `references/plugin-virtual.md` | Connaissance domaine plugin Virtual |
| `references/plugin-jmqtt.md` | Connaissance domaine plugin jMQTT |
| `references/plugin-agenda.md` | Connaissance domaine plugin Agenda |
| `references/plugin-script.md` | Connaissance domaine plugin Script |
| `references/plugin-alarme.md` | Connaissance domaine plugin Alarme |
| `references/plugin-thermostat.md` | Connaissance domaine plugin Thermostat |
| `references/plugin-generic-pattern.md` | Pattern d'inspection générique tous plugins |
| `scripts/_common/tags.py` | Tags système Jeedom à préserver intacts — peut rester ou être intégré à SKILL.md |

---

## 3. Connexion à Holmes MCP depuis jeedom-skills

### Format `.mcp.json` (Claude Code)

L'utilisateur ajoute Holmes MCP dans son `.mcp.json` (à la racine du projet ou dans `~/.claude/`) :

```json
{
  "mcpServers": {
    "holmes": {
      "type": "http",
      "url": "http://<ip-box>:8765/mcp",
      "headers": {
        "Authorization": "Bearer <votre-token>"
      }
    }
  }
}
```

Le token est généré dans la page du plugin Jeedom → section "Tokens d'accès".

### Pré-requis utilisateur (nouveaux §3 de SKILL.md)

- Holmes MCP installé et démarré sur la box Jeedom (plugin Jeedom)
- `.mcp.json` configuré avec l'URL et le Bearer token
- Même réseau LAN que la box (pas de VPN ou accès externe requis pour V1)

**Ce qui disparaît :**

- Alias SSH `Jeedom`
- `~/.my.cnf` sur la box
- `~/.config/jeedom-audit/credentials.json`
- `python3 scripts/setup.py`

### Vérification de version

Remplacer `scripts/_common/version_check.py` par :

```
holmes__get_install_overview()
→ retourne jeedom_version, ex: "4.5.3"
```

Politique de version inchangée : Jeedom < 4.5 → refus explicite. Holmes MCP cible Jeedom 4.5+ (Bookworm x86_64).

---

## 4. Mapping WF → outils Holmes MCP

Pour chaque workflow, les scripts à remplacer et les outils Holmes MCP à utiliser.

### WF1 — Audit général

| Ancienne approche | Nouvel appel Holmes MCP |
|------------------|------------------------|
| `db_query.run("SELECT value FROM config WHERE key='version'...")` | `holmes__get_install_overview()` |
| `db_query.run("SELECT ... FROM update WHERE type='plugin'")` | `holmes__list_plugins()` |
| `db_query.run("SELECT COUNT(*) FROM eqLogic")` | `holmes__get_install_overview()` (inclut comptages) |
| `db_query.run("SELECT COUNT(*) FROM scenario")` | `holmes__get_install_overview()` |
| `db_query.run("SELECT ... FROM message WHERE type='error'")` | `holmes__get_health_summary()` |
| `db_query.run("SELECT ... FROM update WHERE status != 'ok'")` | `holmes__list_plugins()` (champ `update_available`) |
| `db_query.run(requête commandes mortes)` | `holmes__query_sql(sql)` |
| `db_query.run(requête qualité historique)` | `holmes__query_sql(sql)` |
| `logs_query.py tail http.error` | `holmes__tail_log(log_name="http", lines=200)` |

### WF2 — Diagnostic scénario

| Ancienne approche | Nouvel appel Holmes MCP |
|------------------|------------------------|
| `db_query.run("SELECT ... FROM scenario WHERE name LIKE ?")` | `holmes__find_scenarios_advanced(name_contains=...)` |
| `scenario_tree_walker.py` | `holmes__get_scenario_structure(scenario_id, follow_scenario_calls=0)` |
| `api_call.run("scenario::byId")` pour `lastLaunch`/`state` | `holmes__get_scenario(scenario_id)` (inclut `lastLaunch` + `state`) |
| `logs_query.py tail scenarioLog/N` | `holmes__get_scenario_log(scenario_id, lines=100)` |
| `resolve_cmd_refs.py` sur expressions | `holmes__describe_scenario(scenario_id)` (résolution intégrée) |

### WF3 — Diagnostic équipement

| Ancienne approche | Nouvel appel Holmes MCP |
|------------------|------------------------|
| `db_query.run("SELECT ... FROM eqLogic WHERE name LIKE ?")` | `holmes__find_equipment_by_name(name=...)` |
| `db_query.run("SELECT ... FROM cmd WHERE eqLogic_id = ?")` | `holmes__get_equipment(equipment_id)` (inclut commandes + `currentValue`) |
| `api_call.run("plugin::listPlugin")` pour état daemon | `holmes__get_health_summary()` |
| `logs_query.py tail <plugin>` | `holmes__tail_log(log_name="<plugin>", lines=200)` |

### WF4 — Diagnostic plugin

| Ancienne approche | Nouvel appel Holmes MCP |
|------------------|------------------------|
| `db_query.run("SELECT ... FROM update WHERE type='plugin'")` | `holmes__list_plugins()` |
| `api_call.run("plugin::listPlugin")` | `holmes__get_health_summary()` (daemons nok) |
| `db_query.run("SELECT ... FROM eqLogic WHERE eqType_name = ?")` | `holmes__find_equipments_advanced(plugin=...)` |
| `logs_query.py tail <plugin>_dep` | `holmes__tail_log(log_name="<plugin>_dep", lines=200)` |

### WF5 — Explication scénario

| Ancienne approche | Nouvel appel Holmes MCP |
|------------------|------------------------|
| `scenario_tree_walker.py` + `resolve_cmd_refs.py` | `holmes__describe_scenario(scenario_id)` (remplace les deux) |
| `scenario_tree_walker.py follow_scenario_calls=2` | `holmes__get_scenario_structure(scenario_id, follow_scenario_calls=2)` |

### WF6 — Graphe d'usage

| Ancienne approche | Nouvel appel Holmes MCP |
|------------------|------------------------|
| `usage_graph.py {"target_type": "cmd", "target_id": N}` | `holmes__find_command_usages(cmd_id=N)` |
| `usage_graph.py {"target_type": "scenario", "target_id": N}` | `holmes__find_scenario_dependencies(scenario_id=N)` |
| `usage_graph.py {"target_type": "eqLogic", "target_id": N}` | `holmes__query_sql(sql)` — voir SQL cookbook §A ci-dessous |
| `resolve_cmd_refs.py` sur résultats | Non nécessaire — `describe_scenario()` résout si contexte scénario |

### WF7 — Suggestions de refactor

Composition de WF1 + WF5. Aucun script spécifique à remplacer. Les requêtes ad-hoc passent par `holmes__query_sql()`.

### WF8 — Valeur courante

| Ancienne approche | Nouvel appel Holmes MCP |
|------------------|------------------------|
| `db_query.run("SELECT ... FROM cmd WHERE id = ?")` | `holmes__find_commands_advanced(...)` pour localiser l'`equipment_id` |
| `api_call.run("cmd::byId")` pour `currentValue` | `holmes__list_commands(equipment_id=...)` ou `holmes__get_equipment(equipment_id=...)` |

> **Note :** `find_commands_advanced()` ne retourne pas `currentValue` (coût N×API prohibitif). Passer d'abord par `find_commands_advanced` pour obtenir `equipment_id`, puis `list_commands(equipment_id)`.

### WF9 — Historique

| Ancienne approche | Nouvel appel Holmes MCP |
|------------------|------------------------|
| `api_call.run("cmd::getHistory")` | `holmes__get_command_history(cmd_id=N)` (live + archivé) |

### WF10 — Variable dataStore

| Ancienne approche | Nouvel appel Holmes MCP |
|------------------|------------------------|
| `db_query.run("SELECT ... FROM dataStore WHERE type='scenario'")` | `holmes__list_datastore_variables()` |
| `db_query.run("SELECT ... FROM dataStore WHERE key = ?")` | `holmes__get_datastore_variable(key=...)` |

### WF11 — Recherche libre

| Ancienne approche | Nouvel appel Holmes MCP |
|------------------|------------------------|
| Multiples `db_query.run()` avec LIKE | `holmes__search_text(text=..., limit=50)` |

### WF12 — Cartographie d'orchestration

| Ancienne approche | Nouvel appel Holmes MCP |
|------------------|------------------------|
| `scenario_tree_walker.py follow_scenario_calls=3` | `holmes__get_scenario_structure(scenario_id, follow_scenario_calls=3)` |
| `resolve_cmd_refs.py` sur annotations | `holmes__describe_scenario(scenario_id)` |

### WF13 — Forensique causale

| Ancienne approche | Nouvel appel Holmes MCP |
|------------------|------------------------|
| `usage_graph.py` | `holmes__find_scenario_dependencies(scenario_id)` |
| `logs_query.py` sur fenêtre temporelle | `holmes__tail_log(log_name=..., lines=500, grep=...)` |
| `api_call.run("cmd::getHistory")` | `holmes__get_command_history(cmd_id)` |

---

## 5. Contraintes techniques de `query_sql()`

`query_sql()` remplace `db_query.run()` pour les requêtes SQL ad-hoc. Différences comportementales à connaître :

### LIMIT auto-injectée

| Comportement | `db_query.py` (avant) | `query_sql()` (Holmes MCP) |
|---|---|---|
| Requête sans LIMIT | Retourne tout | LIMIT 50 injectée automatiquement |
| Requête avec LIMIT | Respectée | Respectée, plafonnée à 200 |
| `COUNT(*)` | Non affecté | Non affecté |

**Impact :** les requêtes exhaustives WF1 (audit général) qui ne mettaient pas de LIMIT seront silencieusement tronquées à 50. Vérifier et ajouter `LIMIT 200` explicite sur les requêtes où l'exhaustivité est importante.

### Backticks — mots réservés

`query_sql()` auto-backtick les mêmes mots réservés que `db_query.py` : `trigger`, `repeat`, `update`. Comportement identique — écrire sans backticks dans les requêtes.

### Blacklist tables

Tables interdites (refus immédiat) : `user`, `session`, `network`, et tout nom contenant `creds`, `credentials`, `password`, `token`.

### Colonnes sensibles — SELECT explicite

`SELECT password, token, apikey, secret` → rejeté. `SELECT *` → autorisé et filtré à la sortie.

### Format de retour

```json
{
  "rows": [...],
  "_filtered_fields": ["champ_masqué"],
  "error": null
}
```

Si `_filtered_fields` n'est pas vide : mentionner explicitement que des champs ont été masqués (`[FILTRÉ]`).

---

## 6. SQL cookbook de substitution

Requêtes à conserver dans `references/sql-cookbook.md` après migration — celles qui n'ont pas d'outil Holmes MCP dédié. Toutes testées sur MariaDB 10.x (Jeedom Bookworm).

### Important — MariaDB vs MySQL

`CAST(col AS JSON)` est syntaxe MySQL pure — **échoue sur MariaDB** avec `ProgrammingError: 1064`. Substitution obligatoire dans toutes les requêtes :

```sql
-- NE PAS UTILISER (MySQL uniquement)
JSON_CONTAINS(arr_col, CAST(id_col AS JSON))

-- UTILISER (MariaDB/Jeedom Bookworm)
JSON_SEARCH(arr_col, 'one', CAST(id_col AS CHAR)) IS NOT NULL
```

Point connexe : `scenario.scenarioElement` stocke les IDs comme chaînes JSON (`["502"]`, pas `[502]`). `JSON_SEARCH` avec `CAST AS CHAR` est cohérent.

### A. Graphe d'usage eqLogic (WF6 — pas d'outil Holmes MCP dédié)

Scénarios dont un équipement est utilisé (via ses commandes) :

```sql
SELECT DISTINCT s.id, s.name
FROM scenario s
JOIN scenarioElement sel
  ON JSON_SEARCH(s.scenarioElement, 'one', CAST(sel.id AS CHAR)) IS NOT NULL
JOIN scenarioSubElement ss ON ss.scenarioElement_id = sel.id
JOIN scenarioExpression expr ON expr.scenarioSubElement_id = ss.id
JOIN cmd c ON expr.expression LIKE CONCAT('%#', c.id, '#%')
WHERE c.eqLogic_id = <EQUIPEMENT_ID>
LIMIT 50
```

### B. Commandes mortes (WF1 — audit général)

```sql
SELECT c.id, c.name, c.eqLogic_id
FROM cmd c
LEFT JOIN eqLogic e ON c.eqLogic_id = e.id
WHERE e.id IS NULL OR e.isEnable = 0
ORDER BY c.eqLogic_id
LIMIT 200
```

### C. Variables dataStore orphelines (WF7 — refactor)

```sql
SELECT d.`key`, d.value
FROM dataStore d
WHERE d.type = 'scenario' AND d.link_id = -1
  AND NOT EXISTS (
    SELECT 1 FROM scenarioExpression expr
    WHERE expr.expression LIKE CONCAT('%variable(', d.`key`, ')%')
       OR (expr.options IS NOT NULL AND expr.options LIKE CONCAT('%"', d.`key`, '"%'))
  )
LIMIT 200
```

### D. Commandes sans Type Générique (WF7 — refactor)

```sql
SELECT c.id, c.name, c.type, c.subType,
       e.name AS equipement, e.eqType_name
FROM cmd c
JOIN eqLogic e ON c.eqLogic_id = e.id
WHERE c.type = 'info'
  AND (c.generic_type IS NULL OR c.generic_type = '')
ORDER BY e.name, c.name
LIMIT 200
```

### E. Qualité d'historique — commandes info sans aucune valeur (WF1)

```sql
SELECT COUNT(*) AS cmd_info_sans_historique
FROM cmd c
WHERE c.type = 'info'
  AND c.isHistorized = 1
  AND NOT EXISTS (SELECT 1 FROM history h WHERE h.cmd_id = c.id)
```

### F. Équipements en warning ou danger (WF1 / WF3)

```sql
SELECT id, name, eqType_name, status
FROM eqLogic
WHERE JSON_UNQUOTE(JSON_EXTRACT(status, '$.warning')) != ''
   OR JSON_UNQUOTE(JSON_EXTRACT(status, '$.danger')) != ''
LIMIT 100
```

### G. Scénarios désactivés mais appelés en action (WF7)

```sql
SELECT DISTINCT s.id, s.name
FROM scenario s
WHERE s.isActive = 0
  AND EXISTS (
    SELECT 1 FROM scenarioExpression expr
    WHERE expr.type = 'action'
      AND expr.expression = 'scenario'
      AND JSON_UNQUOTE(JSON_EXTRACT(expr.options, '$.scenario_id')) = CAST(s.id AS CHAR)
  )
LIMIT 50
```

### H. Résumé plugins avec mises à jour (WF1)

```sql
SELECT id, name, localVersion, remoteVersion, status
FROM `update`
WHERE type = 'plugin' AND status != 'ok'
ORDER BY name
LIMIT 50
```

> `update` est auto-backtické par `query_sql()` — écrire sans backticks.

---

## 7. Réécriture SKILL.md — section par section

### §3 Pré-requis et connexion — réécrire entièrement

Remplacer le contenu actuel (SSH, `~/.my.cnf`, `credentials.json`, `setup.py`, modes d'accès, router) par :

```markdown
## 3. Pré-requis et connexion

**Pré-requis :**
- Holmes MCP installé et démarré sur la box Jeedom (plugin Jeedom v1.1.1+)
- Jeedom 4.5+ (Bookworm x86_64) — refus explicite si version inférieure
- Même réseau LAN que la box (accès HTTP direct)

**Configuration `.mcp.json` :**
Ajouter Holmes MCP dans le `.mcp.json` de Claude Code (racine du projet ou `~/.claude/`) :

{
  "mcpServers": {
    "holmes": {
      "type": "http",
      "url": "http://<ip-box>:8765/mcp",
      "headers": {
        "Authorization": "Bearer <votre-token>"
      }
    }
  }
}

Le token est généré dans la page du plugin Jeedom → section "Tokens d'accès".

**Vérification de version :**
Appeler `holmes__get_install_overview()` en début de session.
- `jeedom_version` < 4.5 → refus explicite
- `jeedom_version` >= 4.6 → avertissement (schéma peut différer)

**Aucun setup supplémentaire :** pas de SSH, pas de credentials MySQL, pas de `setup.py`.
```

### §Routage automatique — supprimer entièrement

La section entière "Routage automatique (router.py)" disparaît. Holmes MCP gère le routage MySQL/API en interne — invisible pour la skill.

### §6 Gotchas critiques — mettre à jour

| Gotcha | Avant | Après |
|--------|-------|-------|
| `trigger` mot réservé | "auto-backtické par `db_query.py`" | "auto-backtické par `query_sql()` — comportement identique, écrire sans backticks" |
| `repeat` mot réservé | "auto-backtické par `db_query.py` depuis J5" | "auto-backtické par `query_sql()`" |
| `update` mot réservé | "auto-backtické par `db_query.py`" | "auto-backtické par `query_sql()`" |
| `JSON_EXTRACT` via echo | "échoue — passer via subprocess" | Supprimer — `query_sql()` gère nativement les requêtes complexes |
| Nouveau | — | "LIMIT auto-injectée par `query_sql()` : 50 si absente, max 200. `COUNT(*)` non affecté." |
| Nouveau | — | "SELECT explicite de colonnes sensibles (password, token, apikey) rejeté. `SELECT *` filtré à la sortie." |
| `CAST(id AS JSON)` MariaDB | Non documenté | "CAST(col AS JSON) échoue sur MariaDB — utiliser `JSON_SEARCH(arr, 'one', CAST(id AS CHAR)) IS NOT NULL`" |

Gotchas 2, 3, 4, 5, 7, 8 (scenarioExpression, scenarioElement FK, jMQTT topic, int vs string JSON, cmd.value thermostat) : **conserver inchangés**.

### §7 WF — section scripts — mettre à jour chaque WF

Pour chaque WF, remplacer la ligne `**Scripts :**` et les références aux scripts par les outils Holmes MCP correspondants (cf. §4 de ce document).

Exemple WF2 avant → après :

```markdown
# Avant
**Scripts** : `scenario_tree_walker.py`, `resolve_cmd_refs.py`, `logs_query.py`

# Après
**Outils Holmes MCP** : `get_scenario()`, `describe_scenario()`, `get_scenario_structure()`, `get_scenario_log()`
```

### §9 Index des références — nettoyer

Supprimer les entrées des fichiers Éliminer (scripts + references/connection.md + api-*.md).
Conserver les entrées des fichiers Conserver.
Mettre à jour les références aux scripts dans les descriptions des fichiers Conserver restants.

---

## 8. Gotcha post-migration — comportement `describe_scenario()`

`describe_scenario()` retourne le scénario LLM-friendly avec résolution `#[O][E][C]#` intégrée. Il remplace **à la fois** `scenario_tree_walker.py` ET `resolve_cmd_refs.py`.

Différence de comportement notable : l'ancien pipeline résolvait les IDs en deux passes (walker → refs). `describe_scenario()` le fait en une passe — le résultat est légèrement différent dans le formatage des nœuds imbriqués. Ajuster la logique d'interprétation dans SKILL.md §7 WF5 si nécessaire.

---

## 9. Checklist de validation de la migration

La migration sur branche `develop` est complète quand :

- [ ] Branche `develop` créée depuis `main` sur `jeedom-skills`
- [ ] Fichiers Éliminer supprimés (voir §2)
- [ ] SKILL.md §3 réécrit (pré-requis → Bearer token, sans SSH ni credentials)
- [ ] SKILL.md §Routage supprimé
- [ ] SKILL.md §6 Gotchas mis à jour (backticks, LIMIT, MariaDB JSON)
- [ ] SKILL.md §7 scripts → outils Holmes MCP pour les 13 WF
- [ ] SKILL.md §9 Index références nettoyé
- [ ] `references/sql-cookbook.md` mis à jour (requêtes obsolètes supprimées, LIMIT ajoutée, MariaDB JSON corrigé)
- [ ] 12/13 WF testables depuis Claude Code avec Holmes MCP connecté
- [ ] WF6 graphe d'usage cmd opérationnel via `find_command_usages()`
- [ ] Aucune référence à SSH, `db_query`, `api_call`, `setup.py` dans SKILL.md

**Ce que "testable" signifie :** lancer le WF depuis Claude Code avec Holmes MCP dans le `.mcp.json`, et obtenir une réponse cohérente sans erreur d'outil.

---

## 10. Documents de référence Holmes MCP

| Document | Contenu |
|---------|---------|
| `docs/skill-coverage-matrix.md` | Mapping détaillé WF ↔ tools Holmes MCP (version J7bis-2) |
| `docs/sessions/2026-05-05-j8-audit-migration-jeedom-skill.md` | Gap analysis complète jeedom-audit v1.0.0 → Holmes MCP |
| `docs/sessions/2026-05-05-j7bis-2-audit-jeedom-audit.md` | Gap analysis mise à jour v1.1.0, SQL MariaDB corrigés |
| `docs/skill-migration-audit-playbook.md` | Méthodologie d'audit (contexte, non requis pour la migration) |
| `docs/user/tools.md` | Documentation utilisateur des 26 tools Holmes MCP |
| `docs/user/clients-mcp.md` | Configuration `.mcp.json` et autres clients |
