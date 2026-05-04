# CONTRIBUTING-CLAUDE-CODE.md — Contrat opérationnel PO / Claude Code

> Document dérivé de la section 0 du brief de cadrage (`docs/sources/00-brief-cadrage.md`).  
> Ce fichier est le contrat opérationnel du binôme PO / Claude Code pour le projet Holmes MCP.  
> Toute évolution de ce contrat passe par une ADR (ADR-0015).

---

## 1. Répartition des rôles

| Rôle | Qui | Responsabilités |
| --- | --- | --- |
| **Product Owner (PO)** | L'utilisateur humain | Décide, oriente, arbitre. Fournit les matières que Claude Code ne peut pas produire seul (captures d'écran UI Jeedom, validation Claude Desktop sur sa machine, sanity check sanitisation, soumission market, communication forum). Ne tape pas de code, ne rédige pas de doc, n'exécute pas de scripts complexes. |
| **Implémenteur** | Claude Code | Code, rédige, propose, pose des questions structurées quand un arbitrage est nécessaire. Produit tous les artefacts du repo (ADRs, guides, doc utilisateur, références, scripts, tests). Avec accès SSH à la box du PO (§4 ci-dessous), exécute aussi : tests live, déploiements, smoke tests, récupération de fixtures réelles, debug. Demande explicitement les matières physiques au PO. |

---

## 2. Conséquences pratiques pour Claude Code

**(a) Pas d'attente que le PO rédige.** Tout texte (ADR, guide, doc utilisateur, README, code, tests) est rédigé par Claude Code. Le PO valide ou demande retouche.

**(b) Pose des questions structurées, pas ouvertes.** Quand un arbitrage est nécessaire, présenter au PO **2 à 4 options claires** avec leurs trade-offs. Indiquer une recommandation par défaut quand possible. Le PO peut accepter, choisir une autre option, ou demander à débattre.

**(c) Préférer "valider un draft" à "produire ex nihilo via questions".** Quand il s'agit de rédiger une section ou un fichier, Claude Code produit un draft et le PO le critique.

**(d) Auto-validation des choix triviaux.** Conventions de nommage internes, organisation de fichiers internes, choix de variables, formulations mineures dans les drafts : Claude Code décide seul et avance. Pas de gaspillage de cycles de validation sur des détails.

**(e) Goulets d'étranglement physiques — matières que seul le PO peut fournir :**

1. **Captures d'écran UI Jeedom** — page de config plugin, état daemon, fiche market (D12.6)
2. **Validation finale Claude Desktop** sur la machine PO avant V1.0.0 (D8.3 critère #4)
3. **Sanity check sanitisation** à l'œil humain sur installation réelle avant V1.0.0 (D15.6)
4. **Soumission market Jeedom** (compte développeur PO)
5. **Communication forum Jeedom** (identité PO)
6. **Snapshots Proxmox** du conteneur Jeedom avant chaque session SSH significative (~30s — sécurité opérationnelle)

Demandes au PO : **explicites, timées, groupées** ("À l'étape J7, j'ai besoin de 3 captures + validation Claude Desktop + sanity check sanitisation"). Format : spec précise du livrable attendu (résolution, contenu, délai).

**(f) Sessions courtes orientées avancement.** Préférer plusieurs sessions ciblées avec validation PO entre les deux à une session marathon. À la fin de chaque session, le PO doit pouvoir comprendre ce qui a été produit en lisant le résumé de session sans relire tout le code.

---

## 3. Discipline de continuité entre sessions

Le PO ne mémorise pas les détails techniques entre sessions. L'**axe documentaire** assure la persistance — `docs/state/PROJECT_STATE.md` et `docs/sessions/*.md` mis à jour à chaque session significative.

### Vocabulaire

| Terme | Définition |
| --- | --- |
| **Sous-session** (J0-1, J1-2…) | Unité de travail et de livrable — correspond à un bloc cohérent du jalon |
| **Session Claude Code** | Fenêtre de conversation — peut couvrir 1 ou N sous-sessions |
| **Jalon** (J0, J1…) | Ensemble de sous-sessions partageant un objectif, avec DoD et tag semver |

### Stratégie de branches (D10.5)

| Branche | Rôle | Règle |
| --- | --- | --- |
| `develop` | Intégration — tout le code J3+ | Commits quotidiens ici. Jamais de commit direct sur `main`. |
| `main` | Stable — toujours = dernier jalon complet | Reçoit **uniquement** les merges depuis `develop` en fin de jalon. |

**Règle fondamentale** : on ne merge `develop` → `main` que lorsque le DoD du jalon est intégralement coché et le tag posé. Entre deux jalons, `main` est figé. Le market Jeedom et les utilisateurs pointent sur `main` — il ne doit jamais contenir de code en cours.

**Garde-fou technique** : le `pre-commit` hook bloque automatiquement tout commit direct sur `main` (déclenché si `git symbolic-ref HEAD` vaut `main` et qu'aucun merge n'est en cours). Les hooks sont versionnés dans `.githooks/` — activer après un clone :

```bash
git config core.hooksPath .githooks
```

Seuls trois cas passent le hook :

1. **Merge commit depuis `develop`** — détecté automatiquement via `.git/MERGE_HEAD`
2. **Hotfix urgent** — `HOLMES_MAIN_COMMIT=1 git commit ...` (justifier dans le message de commit)
3. **Doc post-merge** (fichier session, PROJECT_STATE) — `HOLMES_MAIN_COMMIT=1 git commit ...`

> **Historique** : J0-J2 ont été développés directement sur `main` (dérive pré-garde-fou). `develop` est synchronisée avec `main` depuis la fin de J2 (tag `v0.3.0`). À partir de J3, la règle est appliquée et techniquement renforcée.

### Règle — ADR on commit

**Toute implémentation qui concerne une décision met à jour l'ADR correspondante dans le même commit que le code.** Une ADR `draft` ou `proposed` qui décrit ce qui vient d'être livré passe à `accepted` (ou est corrigée si la réalité diverge du draft). On ne livre pas de code avec une ADR en désaccord avec lui.

### Routine de début de jalon

**Avant de démarrer la première sous-session d'un jalon**, planifier les sous-sessions du jalon :

```bash
# S'assurer d'être sur develop et à jour
git checkout develop
git merge --ff-only main   # develop doit être à parité avec main en début de jalon
```

1. Lire le bloc jalon dans `docs/PLANNING.md` (livrables + DoD)
2. Décomposer en sous-sessions nommées (J2-1, J2-2…) avec objectif et dépendances
3. Lister les sous-sessions dans `docs/state/PROJECT_STATE.md` (bloc jalon en cours)
4. Identifier lesquelles nécessitent SSH et demander le snapshot Proxmox en amont

### Routine de fin de sous-session

**À la fin de chaque sous-session** — que la session Claude Code continue ou non.

#### Étape 1 — Qualité code (bloquante)

```bash
# Lint + format sur tous les fichiers modifiés
ruff check <fichiers>
ruff format --check <fichiers>

# Suite de tests unitaires + couverture
python -m pytest tests/unit/ --cov --cov-report=term-missing -q
```

- Ruff doit être propre (0 erreur). Appliquer `ruff format` si nécessaire.
- Le module implémenté dans la sous-session doit atteindre son objectif de couverture
  (100% pour `sanitize.py`, >80% pour les autres).
- Si un test échoue → corriger avant de passer aux étapes suivantes.

#### Étape 2 — Documentation (dans le même commit que le code)

1. **ADRs impactées** : toute implémentation qui concerne une décision met à jour l'ADR
   correspondante (statut, contenu). Règle ADR on commit.
2. **Fichier de session** : créer `docs/sessions/AAAA-MM-JJ-{Jx-y-slug}.md` avec :
   - Objectif de la sous-session
   - Livrables produits (fichiers, fonctions, tests)
   - Décisions prises en session (choix non triviaux)
   - Résultats des tests (nb tests, couverture)
   - Prochaine sous-session (objectif + pré-requis)
3. **PROJECT_STATE.md** : marquer la sous-session ✅, mettre à jour la prochaine,
   ajouter le commit hash, mettre à jour le risque actif si besoin.

#### Étape 3 — Commit

```bash
# Vérifier qu'on est bien sur develop (jamais sur main)
git branch --show-current   # doit afficher "develop"

# Ajouter explicitement les fichiers (pas git add .)
git add <fichiers code> <ADRs> <session file> PROJECT_STATE.md

# Message de commit : convention "feat/docs/fix(scope): livrable principal"
git commit -m "feat(domain): cmd_refs — résolveur #cmdId# + 100% coverage"
```

Le pre-commit hook vérifie :

- **Branche** : bloque si on est sur `main` sans `MERGE_HEAD` ni `HOLMES_MAIN_COMMIT=1`
- **Credentials** : bloque si pattern IP/token/password détecté

Si credential refusé à tort → demander d'ajuster le filtre (ADR-0013), ne pas bypasser.

#### Étape 4 — Mémoire Claude Code (si la session Claude Code se ferme)

Mettre à jour les fichiers mémoire dans
`~/.claude/projects/-home-gtillit-Github-holmesMcp/memory/` :
- `project_holmes_mcp.md` : état courant (dernier commit, sous-session ✅, prochaine)
- Tout autre fichier mémoire pertinent (nouveau risque, nouvelle décision structurante)

Si la session Claude Code continue vers la sous-session suivante, la mémoire peut
attendre la fermeture de fenêtre.

### Routine de fin de jalon

**Quand toutes les sous-sessions d'un jalon sont ✅** :

1. Vérifier le DoD du jalon dans `docs/PLANNING.md` — cocher chaque critère
2. Merger `develop` → `main` + tag (si DoD ✅) :

   ```bash
   # Depuis develop : dernier commit de code/doc déjà posé
   git checkout main
   git merge --no-ff develop -m "chore: merge develop — J3 clôturé (v0.4.0)"
   git tag v0.x.0
   git checkout develop           # retour sur develop immédiatement

   # Doc post-merge si nécessaire (session file, PROJECT_STATE) :
   # HOLMES_MAIN_COMMIT=1 git commit ...   ← seuls commits directs tolérés sur main
   ```

3. Mettre à jour `docs/state/PROJECT_STATE.md` (jalon ✅, prochain jalon)
4. Synchroniser `develop` avec `main` si des commits post-merge ont été ajoutés :

   ```bash
   git checkout develop
   git merge --ff-only main
   ```

### Routine de début de session Claude Code

1. Lire `docs/README.md`
2. Lire `docs/state/PROJECT_STATE.md`
3. Lire les ADRs `accepted` récentes dans `docs/decisions/`
4. Lire la dernière entrée `docs/sessions/`
5. Annoncer au PO : état courant + objectifs de la session

Si la dernière session date de plus de 2 semaines → mention explicite, relecture complète des ADRs accepted.

---

## 4. Cadre d'usage de l'accès SSH PO

Claude Code dispose d'un alias SSH `Jeedom` opérationnel sur sa machine de dev. La connexion utilise l'utilisateur **`gtillit`** du système. Le daemon Holmes MCP tourne sous le user d'exécution Apache/Jeedom (typiquement `www-data`), distinct du user SSH.

**Conséquence** : la discipline de prompt est le filet de sécurité principal. Les garde-fous suivants sont **non négociables**.

### 4.1 Conditions générales d'usage SSH

- Actions limitées au plugin Holmes MCP (lecture, install/test, démarrage/arrêt daemon plugin)
- Aucune modification non autorisée de la config Jeedom, des autres plugins, du système hors plugin
- Logs des actions SSH dans `docs/sessions/` pour traçabilité PO
- En cas de doute : demande PO avant action

### 4.2 Reco opérationnelle PO — snapshot Proxmox

Avant chaque session SSH significative (install/désinstall plugin, tests live nombreux), le PO **prend un snapshot du conteneur Jeedom** (~30s). Claude Code annonce en début de session "j'aurai besoin d'accès SSH avec install/désinstall plugin, snapshot recommandé" et attend confirmation PO avant action.

### 4.3 Blacklist explicite — commandes interdites sans validation PO préalable

Les commandes suivantes sont **interdites sans validation PO explicite préalable** (demande structurée en chat avec justification + commande exacte, le PO valide ou refuse) :

- `rm -rf`, `rm -r` sur tout chemin hors `/tmp/` ou hors workspace de dev Holmes MCP
- `DROP DATABASE`, `DROP TABLE`, `DROP USER`, `TRUNCATE`, `DELETE FROM`, `UPDATE`, `INSERT` (toute requête MySQL modifiante)
- Modifications de fichiers dans `/etc/`, `/usr/`, `/var/log/` (hors logs Jeedom du plugin Holmes MCP)
- `chmod`/`chown` sur fichiers ou dossiers non liés au plugin Holmes MCP
- `apt-get install/remove/purge`, `pip install` hors venv Holmes MCP
- `systemctl stop/disable/mask` sur services autres que ceux du plugin Holmes MCP
- Toute commande `sudo` **hors périmètre plugin Holmes MCP** — `gtillit` est sudoer, mais sudo reste soumis à validation PO pour toute action hors plugin (chown plugin OK, apt système NON)
- Toute manipulation de `~/.ssh/`, `/etc/shadow`, `/etc/passwd`, fichiers de creds Jeedom (`common.config.php` reste accessible en lecture pour D4bis.2)
- Toute commande pouvant déclencher un redémarrage système ou couper le serveur web

---

## 5. Isolation des credentials et de la configuration d'accès

**Aucun credential, alias SSH, IP, hostname, user MySQL, port, mot de passe, token, apikey, chemin absolu PO-spécifique, ou identifiant lié à l'environnement PO ne doit apparaître dans le repo Holmes MCP.** Stockage exclusif sur la devbox Claude Code.

**Garde-fous techniques** (mis en place en J0) :

- `.gitignore` strict (chemins SSH, credentials, `.env`, fixtures réelles non sanitisées, dumps MySQL)
- Pre-commit hook : scan automatique du commit pour patterns sensibles (regex IP, tokens, hostnames) — refus si détection
- Pre-push hook : second scan avant push GitHub
- Review systématique de chaque PR vers `main` avec checklist credentials avant merge

**Documentation publique** : placeholders systématiques (`<your-jeedom-host>`, `<your-mysql-password>`, `<your-mcp-token>`).

**Logs de sessions** : références neutres aux actions SSH, pas de commande brute incluant des éléments sensibles.

**Fixtures réelles MySQL** : workspace local Claude Code uniquement (hors repo). Fixtures synthétiques uniquement dans le repo.

**Procédure de réponse rapide en cas de leak** : rewrite git history, force push, rotation immédiate du credential, ADR d'incident.

---

## 6. Modèle d'arbitrage — demandes structurées avec options

Quand un arbitrage est nécessaire, Claude Code présente **2 à 4 options claires** avec leurs trade-offs et une recommandation par défaut. Le PO accepte, choisit une autre option, ou demande à débattre.

Pas de questions ouvertes ("comment veux-tu faire X ?"). Toujours : "Option A (recommandée) / Option B / Option C — lequel choisis-tu ?"

---

## 7. Auto-validation des choix triviaux

Conventions de nommage internes, organisation de fichiers internes, choix de variables, formulations mineures dans les drafts, choix entre deux implémentations équivalentes → Claude Code décide seul et avance. Pas de gaspillage de cycles de validation.

---

## 8. Demandes de matières physiques — explicites, timées, groupées

Pour les goulets d'étranglement physiques (§2.e), Claude Code formule ses demandes :

- **Explicites** : "À l'étape J7.4, j'ai besoin de…"
- **Timées** : "…d'ici la fin de cette session" ou "avant J7"
- **Groupées** : une sollicitation PO pour N matières plutôt que N sollicitations
- **Avec spec précise** : format, résolution, contenu attendu

---

## 9. Sessions courtes orientées avancement

Préférence pour plusieurs sessions ciblées avec validation PO entre les deux, plutôt qu'une session marathon qui produit beaucoup sans validation intermédiaire. Critère : à la fin de chaque session, le PO comprend ce qui a été produit en lisant le résumé de session.

---

## 10. Statut "EN ATTENTE" si un goulet bloque

Si une session se termine en attendant une matière du PO, Claude Code :

1. Met à jour `PROJECT_STATE.md` avec statut clair "EN ATTENTE de [matière X]"
2. Liste les tâches qui peuvent avancer en parallèle (autres jalons indépendants)
3. Le PO peut soit fournir la matière, soit demander à avancer sur les autres tâches
