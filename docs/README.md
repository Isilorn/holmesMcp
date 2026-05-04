# docs/ — Holmes MCP

Index de navigation de la documentation projet.

Ce dossier contient **la mémoire vivante du projet Holmes MCP** : planification, décisions, état courant, sessions. Il est distinct de la documentation utilisateur publique (source dans `docs/user/`, publiée sur GitHub Pages via MkDocs Material — réservé J7).

> La **source d'autorité absolue** du projet est `docs/sources/00-brief-cadrage.md`. Ce brief est figé : aucune modification directe. Toute évolution des décisions qu'il contient passe par une ADR dans `docs/decisions/`.

---

## Navigation rapide

| Document | Description |
|---|---|
| [`PLANNING.md`](PLANNING.md) | Jalons J0-J7, livrables, critères d'avancement — **point d'entrée session** |
| [`ROADMAP.md`](ROADMAP.md) | Candidates V1.x / V2+ / V3+ (anti-drift scope V1) |
| [`state/PROJECT_STATE.md`](state/PROJECT_STATE.md) | État courant du projet (version, jalon, blocages) |
| [`state/CONTRIBUTING-CLAUDE-CODE.md`](state/CONTRIBUTING-CLAUDE-CODE.md) | Contrat opérationnel PO / Claude Code |
| [`decisions/`](decisions/) | ADRs Holmes MCP (ADR-0001 à ADR-N) |
| [`sessions/`](sessions/) | Journal des sessions Claude Code |
| [`sources/`](sources/) | Matériaux source figés (brief, ADRs parentales, scripts jeedom-audit) |

---

## Conventions ADRs Holmes MCP

Les ADRs du projet Holmes MCP vivent dans `docs/decisions/` avec une **numérotation propre repartant à ADR-0001**, indépendante des ADRs issues des projets parents.

Les **ADRs sources externes** (issues de jeedom-audit / jeedom-skills) restent dans `docs/sources/` avec leur numérotation d'origine :
- `sources/ADR-0006-lecture-seule-absolue.md` — lecture seule perpétuelle jeedom-audit (amendée 2026-05-01)
- `sources/ADR-0019-mcp-architecture.md` — options architecture MCP (superseded)
- `sources/ADR-0020-jeedom-mcp-projet-separe.md` — fondatrice du projet (accepted)

Gabarit d'une ADR Holmes MCP :

```markdown
# ADR-{NNNN} — {titre}

- **Date** : AAAA-MM-JJ
- **Statut** : draft | proposed | accepted | superseded | deprecated
- **Source brief** : section {X}, décisions D{X.Y}

## Contexte
## Décision
## Conséquences
## Liens
```

Statuts possibles :
- `draft` — esquissée en session de planning, à étoffer en J0
- `proposed` — rédigée, soumise au PO pour validation
- `accepted` — validée par le PO, fait loi
- `superseded` — remplacée par une ADR plus récente (référencer laquelle)
- `deprecated` — décision annulée sans remplacement

---

## Distinction `sources/` vs `decisions/`

| `docs/sources/` | `docs/decisions/` |
|---|---|
| Figé, immuable | Vivant, mis à jour |
| Source d'autorité (brief) + ADRs parentales | ADRs propres à Holmes MCP |
| Lu, jamais modifié | Créé et modifié en session |
| Référence pour les arbitrages | Résultat des arbitrages |

---

## Routines opérationnelles

Détail complet dans `docs/state/CONTRIBUTING-CLAUDE-CODE.md §3`. Résumé :

**Début de jalon** → planifier les sous-sessions (J2-1, J2-2…) et les documenter dans `PROJECT_STATE.md` avant de commencer.

**Début de session Claude Code** → lire README → PROJECT_STATE → ADRs accepted récentes → dernière session → annoncer état + objectifs au PO. Si > 2 semaines sans session : relire toutes les ADRs accepted.

**Fin de chaque sous-session** (J0-1, J1-2…) → (1) ruff propre + tests verts + couverture objectif atteint → (2) ADRs impactées + fichier session + PROJECT_STATE → (3) commit groupé → (4) mémoire Claude Code si fermeture de fenêtre. Détail : `CONTRIBUTING-CLAUDE-CODE.md §3`.

**Fin de jalon** → DoD coché ligne par ligne dans PLANNING.md → commit + tag pre-release (`v0.x.0`).
