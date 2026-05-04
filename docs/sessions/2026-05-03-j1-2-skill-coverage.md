# Session J1-2 — Matrice couverture D5.8 + ADR-0019 (2026-05-03)

**Jalon** : J1  
**Type** : Analyse + documentation (pas de SSH)  
**Durée** : ~½ session Claude Code (enchaîné après J1-1)

---

## Objectif de la session

Livrer la matrice de couverture D5.8 : vérifier que les 25 tools Holmes MCP V1 couvrent bien les 13 workflows WF1–WF13 de jeedom-audit, sans perte de capacité. Trancher D5.8. Rédiger ADR-0019.

---

## Artefacts produits

| Fichier | Contenu |
|---|---|
| `docs/skill-coverage-matrix.md` | Matrice complète WF1-WF13 ↔ tools MCP V1, 5 sections (synthèse, mapping, écarts, scripts → modules, référence) |
| `docs/decisions/ADR-0019.md` | accepted — 13/13 WF couverts, 0 tool manquant, bascule jeedom-audit faisable sans ajout V1 |

---

## Référence jeedom-audit analysée

- **Commit** : `a792179` (tag `v1.0.1`, branche `main`, repo `jeedom-skills`)
- **Fichiers** : `SKILL.md`, `references/audit-templates.md`, `references/sql-cookbook.md`
- **Workflows analysés** : WF1–WF13 (§7 de SKILL.md)

---

## Résultat de la matrice

| Indicateur | Valeur |
|---|---|
| Workflows analysés | 13 (WF1–WF13) |
| Workflows couverts à 100% | **13/13** |
| Nouveaux tools requis | **0** |
| Bascule jeedom-audit → Holmes MCP | ✅ Faisable sans perte de capacité |

---

## Points de simplification notables vs jeedom-audit

**`router.py` non porté** : inutile — le daemon Holmes MCP tourne sur la box, MySQL et API JSON-RPC sont toujours disponibles simultanément. La notion de "mode API-only" de jeedom-audit disparaît.

**`resolve_cmd_refs.py` non porté comme module séparé** : la résolution `#ID#` → `#[O][E][C]#` est intégrée dans `describe_scenario` (tool J4). Pour les cas SQL ad-hoc, `find_commands_advanced` par `cmd_id` suffit.

---

## Décision tranchée

| Décision | Choix | ADR |
|---|---|---|
| D5.8 — Matrice couverture skill jeedom-audit | 13/13 WF couverts, liste D5.3 figée pour V1 | ADR-0019 accepted |

---

## Conséquences sur le PLANNING

- Liste D5.3 (25 tools) **figée pour V1** — pas d'ajout issu de D5.8.
- La bascule jeedom-audit → consommatrice Holmes MCP reste candidate roadmap post-V1.
- La matrice `docs/skill-coverage-matrix.md` est la référence vivante du couplage. À mettre à jour si jeedom-audit évolue (ADR d'amendement si gap).

---

## Actions SSH réalisées

Aucune — session 100% offline.

---

## Prochaine session : J1-3 (SSH requis)

**Pré-requis PO** : snapshot Proxmox avant de commencer.

- D6.3 : mesure empirique du plafond resources sur la box réelle (Claude Desktop réactif)
- Tests d'intégration `_core/` sur box réelle (connexion MySQL, chargement TokenStore, appel API JSON-RPC, lecture log)
- Redémarrage daemon avec nouvelle version (`--jeedom-apikey` + structlog + `BearerAuthMiddleware`)
