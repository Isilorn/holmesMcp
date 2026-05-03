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

## Routine de début de session Claude Code

1. Lire ce fichier (`docs/README.md`)
2. Lire `docs/state/PROJECT_STATE.md` (état courant, jalon, blocages)
3. Lire les ADRs `accepted` récentes dans `docs/decisions/`
4. Lire la dernière entrée `docs/sessions/`
5. Annoncer au PO : état du projet + objectifs de la session

Si la dernière session date de plus de 2 semaines : mentionner explicitement au PO et relire l'ensemble des ADRs `accepted` (D13.8).

## Routine de fin de session significative

1. Mettre à jour `docs/state/PROJECT_STATE.md`
2. Créer une entrée `docs/sessions/AAAA-MM-JJ-{slug}.md`
3. Rédiger les ADRs pour les décisions non triviales prises en session
4. Commit + tag pre-release si jalon atteint
