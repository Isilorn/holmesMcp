---
description: Routine de fin de sous-session Holmes MCP — qualité, doc, commit, mémoire
argument-hint: "<Jx-y> <slug-court>"
---

Tu es en train de clore la sous-session Holmes MCP **$ARGUMENTS**.
Exécute chaque étape dans l'ordre. Ne passe à l'étape suivante qu'une fois l'étape courante validée.

---

## Étape 1 — Qualité code (bloquante)

```bash
git branch --show-current   # doit afficher "develop"
git diff --name-only HEAD   # liste les fichiers modifiés dans le dernier commit
git status                  # fichiers non commités éventuels
```

Pour **chaque fichier Python modifié depuis le début de la session** (ne pas lancer sur les fichiers PHP, JS, ou autres — ruff est un linter Python uniquement) :
```bash
ruff check <fichier.py>
ruff format --check <fichier.py>
python -m pytest tests/unit/ --cov --cov-report=term-missing -q 2>&1 | tail -20
```

Règles :
- Ruff = 0 erreur. Appliquer `ruff format` si besoin, puis `ruff check --fix` pour les auto-fixables.
- Tests unitaires : tous passés. Module de la session = 100 % couverture si `sanitize.py`, > 80 % sinon.
- Si un test échoue → corriger avant de continuer.

---

## Étape 2 — Fichier de session

Crée `docs/sessions/AAAA-MM-JJ-{Jx-y-slug}.md` avec la structure suivante (adapter le contenu à la session réelle) :

```markdown
# Session {Jx-y} — {Titre descriptif}

**Date** : AAAA-MM-JJ
**Branche** : `develop`
**Commit(s)** : {hash(es) du/des commit(s) de la session}

---

## Objectif

{1-2 phrases résumant ce que cette sous-session devait accomplir}

---

## Livrables

| Fichier | Ce qui a changé |
| --- | --- |
| `path/to/file.py` | {description concise} |

---

## Décisions prises en session

{Lister uniquement les choix non triviaux — si aucun, écrire "Aucune décision structurante."  
Pour chaque décision : contexte → choix → raison.}

---

## Résultats qualité

| Métrique | Valeur |
| --- | --- |
| Tests unitaires | X/X ✅ |
| Couverture globale | XX % |
| Ruff | propre |

---

## Incidents / anomalies

{Si la session a révélé un bug, un incident infra, ou un écart par rapport au plan — le décrire brièvement.  
Si rien à signaler : "Aucun."}

---

## Prochaine sous-session : {Jx-(y+1)}

**Objectif** : {description}
**Pré-requis** : {snapshot Proxmox si SSH nécessaire, autre dépendance}
```

---

## Étape 3 — PROJECT_STATE.md

Dans `docs/state/PROJECT_STATE.md`, mettre à jour :
- `Dernière session` → `AAAA-MM-JJ-{jx-y}`
- `Prochaine session` → `{Jx-(y+1)} — {objectif court}`
- `Statut global` → ajouter `, {Jx-y} ✅ ({résumé 1 ligne : nb tests, livrables})` à la fin de la ligne

---

## Étape 4 — Commit doc

```bash
git add docs/sessions/AAAA-MM-JJ-{Jx-y-slug}.md docs/state/PROJECT_STATE.md
git commit -m "docs({Jx-y}): fichier session + PROJECT_STATE

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

Si des ADRs ont été impactées pendant la session, les inclure dans ce commit.

---

## Étape 5 — Mémoire Claude Code

Mettre à jour `~/.claude/projects/-home-gtillit-Github-holmesMcp/memory/project_holmes_mcp.md` :
- Ligne `État au AAAA-MM-JJ` → mettre à jour avec la session qui vient de se terminer
- Ajouter un bloc `**{Jx-y} livré**` en tête (après la ligne d'état), avec :
  - Livrables clés (fichiers, fonctions, tests)
  - Commit hash
  - Tout fait notable ou bug découvert

Si un incident ou une décision structurante a eu lieu, créer ou mettre à jour le fichier mémoire correspondant (`feedback_*.md` ou `reference_*.md`) et ajouter/mettre à jour le pointeur dans `MEMORY.md`.

---

## Checklist finale

Avant de déclarer la sous-session clôturée, confirme chaque point :

- [ ] Branche = `develop`
- [ ] Ruff propre sur tous les fichiers Python modifiés
- [ ] Tests unitaires : tous passés, couverture objectif atteint
- [ ] Fichier de session créé (`docs/sessions/`)
- [ ] `PROJECT_STATE.md` mis à jour
- [ ] Commit doc posé
- [ ] Mémoire Claude Code à jour (`project_holmes_mcp.md`)
- [ ] Commit(s) de code posé(s) en amont (fait avant `/end-session` ou intégré ici)

Affiche la checklist avec les cases cochées/décochées selon l'état réel, puis annonce la prochaine sous-session.
