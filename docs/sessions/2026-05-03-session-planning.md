# Session 2026-05-03 — Planning initial Holmes MCP

- **Date** : 2026-05-03
- **Type** : Session de planning (première session du projet)
- **Objectif** : Produire le corpus de planification complet du projet Holmes MCP

---

## Objectifs initiaux (demande PO)

1. Lire intégralement `docs/sources/00-brief-cadrage.md` + ADRs sources + SKILL.md jeedom-audit
2. Fournir une synthèse de compréhension (sanity check PO)
3. Lister les ambiguïtés et questions du brief
4. Produire les livrables de session :
   - `docs/PLANNING.md` — jalons J0-J7 chiffrés, livrables, dépendances, critères
   - `docs/decisions/ADR-0001..0017.md` — 17 ADRs esquissées (draft)
   - `docs/state/PROJECT_STATE.md` — initialisé
   - `docs/state/CONTRIBUTING-CLAUDE-CODE.md` — contrat opérationnel PO/Claude Code
   - `docs/sessions/2026-05-03-session-planning.md` — ce fichier

---

## Sources lues

| Fichier | Taille | Contenu |
|---|---|---|
| `docs/sources/00-brief-cadrage.md` | 1813 lignes | Brief de cadrage intégral (16 dimensions, ~108 décisions) |
| `docs/sources/ADR-0020-jeedom-mcp-projet-separe.md` | ~75 lignes | ADR fondatrice — projet séparé de jeedom-skills (accepted) |
| `docs/sources/ADR-0006-lecture-seule-absolue.md` | ~65 lignes | Lecture seule perpétuelle jeedom-audit (amendée 2026-05-01) |
| `docs/sources/ADR-0019-mcp-architecture.md` | ~80 lignes | Options A/B/C architecture MCP (superseded) |
| `docs/sources/jeedom-audit-SKILLmd` | ~113 lignes | SKILL.md jeedom-audit — WF1-WF13, routage, modes d'accès |

---

## Ambiguïtés levées en session

### Décisions triviales (auto-validées)

- **Numérotation ADRs Holmes MCP** : séquence propre `ADR-0001..N` dans `docs/decisions/`, indépendante des ADRs externes dans `docs/sources/`
- **Date session** : 2026-05-03 (contexte système)
- **Format ADRs draft** : un fichier complet par ADR (gabarit Contexte/Décision/Conséquences/Liens), 1-2 paragraphes par section
- **Création `docs/README.md`** : ajouté aux livrables (index navigation, routines début/fin session)
- **Création `docs/ROADMAP.md`** : ajouté (anti-drift, initialiser maintenant)
- **Bootstrap technique** : réservé pour J0 (pas de `info.json`, `packages.json`, `.gitignore` en cette session)

### Arbitrages structurés (validés PO)

| Question | Options présentées | Choix PO |
|---|---|---|
| Granularité jalons PLANNING.md | Niveau brief J0-J7 / Sous-jalons fins / Jalons + WBS séparé | **Niveau brief J0-J7** |
| Bascule licence jeedom-skills MIT→AGPL | Pré-requis J0 listé séparé / Workstream parallèle / Hors PLANNING | **Pré-requis J0 listé, bascule séparée** |
| ROADMAP.md timing | Initialiser maintenant en draft / Squelette vide / Réserver J7 | **Initialiser maintenant en draft** |

---

## Artefacts produits

| Artefact | Chemin | Statut |
|---|---|---|
| Index navigation docs | `docs/README.md` | ✅ Produit |
| Plan vivant V1 | `docs/PLANNING.md` | ✅ Produit |
| Roadmap candidates | `docs/ROADMAP.md` | ✅ Produit (draft) |
| État projet | `docs/state/PROJECT_STATE.md` | ✅ Produit |
| Contrat opérationnel | `docs/state/CONTRIBUTING-CLAUDE-CODE.md` | ✅ Produit |
| ADR-0001 — Architecture | `docs/decisions/ADR-0001.md` | ✅ Draft |
| ADR-0002 — Stack technologique | `docs/decisions/ADR-0002.md` | ✅ Draft |
| ADR-0003 — Version spec MCP | `docs/decisions/ADR-0003.md` | ✅ Draft |
| ADR-0004 — Auth MCP externe | `docs/decisions/ADR-0004.md` | ✅ Draft |
| ADR-0005 — Canaux d'accès données | `docs/decisions/ADR-0005.md` | ✅ Draft |
| ADR-0006 — Périmètre V1 | `docs/decisions/ADR-0006.md` | ✅ Draft |
| ADR-0007 — 25 tools V1 | `docs/decisions/ADR-0007.md` | ✅ Draft |
| ADR-0008 — 5 resources V1 | `docs/decisions/ADR-0008.md` | ✅ Draft |
| ADR-0009 — Réutilisation scripts | `docs/decisions/ADR-0009.md` | ✅ Draft |
| ADR-0010 — Nom et identité | `docs/decisions/ADR-0010.md` | ✅ Draft |
| ADR-0011 — Licence AGPL-3.0 | `docs/decisions/ADR-0011.md` | ✅ Draft |
| ADR-0012 — Stratégie tests | `docs/decisions/ADR-0012.md` | ✅ Draft |
| ADR-0013 — Sécurité credentials | `docs/decisions/ADR-0013.md` | ✅ Draft |
| ADR-0014 — Distribution et versioning | `docs/decisions/ADR-0014.md` | ✅ Draft |
| ADR-0015 — Modèle opérationnel | `docs/decisions/ADR-0015.md` | ✅ Draft |
| ADR-0016 — Observabilité | `docs/decisions/ADR-0016.md` | ✅ Draft |
| ADR-0017 — Sanitisation | `docs/decisions/ADR-0017.md` | ✅ Draft |
| Journal de session (ce fichier) | `docs/sessions/2026-05-03-session-planning.md` | ✅ Produit |

**Total** : 7 artefacts de fond + 17 ADRs draft = **24 fichiers créés**.

---

## Décisions techniques prises

Aucune décision technique irréversible. Session de planning uniquement : lecture, synthèse, organisation. Aucun code écrit, aucune dépendance installée, aucun accès SSH utilisé.

---

## Goulets d'étranglement restants

Aucun goulet bloquant à l'issue de cette session. La planification est complète et prête pour J0.

---

## Prochaine session — J0 (Bootstrap + POC)

**Annonce en début de J0** : snapshot Proxmox recommandé avant la session (session SSH avec install plugin sur la box).

**Objectifs J0** :
1. Bootstrap repo : structure fichiers, `.gitignore` strict, hooks pre-commit/pre-push, `info.json`, `packages.json`, `pyproject.toml`, `.gitattributes`, `core/`, `desktop/`, `resources/holmesMcpd/`, `.github/workflows/`
2. POC D2.3 (7 hypothèses — dont hypothèse #7 Claude Desktop, goulet PO)
3. Décisions 🔵 J0 à trancher : D1.2, D3.2, D4bis.1, D4bis.2, D9.1, D10.3, D10.8, D11.6, D12.6, D12.7, D2.4
4. Pré-requis externe : vérification copyright holder jeedom-skills (D10.4)
5. ADRs 0001 à 0017 étoffées (`draft` → `proposed`, par lots de 3-5 pour validation PO)
6. ADR-0018 rédigée (résultat POC D2.3)
7. Pré-release tag `v0.1.0`

**Matière PO requise J0** :
- Confirmation copyright holder jeedom-skills (Claude Code fournit le résultat du `git log`, PO confirme)
- Validation Claude Desktop hypothèse #7 POC (pendant la session J0, PO teste sur sa machine)
- Go/no-go formel sur le POC

---

## Notes de session

- Session conduite intégralement en mode plan (aucune écriture avant validation PO du plan global)
- 3 questions structurées posées au PO en début de session → 3 fois la reco par défaut validée
- Brief de 1813 lignes lu intégralement, synthèse capturée
- Posture clean room respectée : aucune référence à d'autres plugins MCP Jeedom
