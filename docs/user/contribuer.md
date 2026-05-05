# Contribuer

## Licence

Holmes MCP est distribué sous licence **AGPL-3.0**. Toute modification et redistribution du code doit être publiée sous la même licence.

## Signaler un bug

Ouvrez une issue sur [GitHub → Issues](https://github.com/Isilorn/holmesMcp/issues) avec :

- La version du plugin (visible dans la page Jeedom)
- La version de Jeedom et Debian
- Les logs du daemon (`Analyse → Logs → holmesMcp` en niveau Debug)
- Les étapes pour reproduire le problème

## Proposer une amélioration

Ouvrez une issue avec le label **enhancement** avant de soumettre une PR. Cela permet de discuter du périmètre et d'éviter un travail non intégrable (notamment pour les fonctions d'écriture, réservées à V2).

## Structure du repo

```
holmesMcp/
├── plugin_info/          # Manifeste Jeedom (info.json, icône)
├── core/                 # PHP — hooks Jeedom (cron, install, update)
├── desktop/              # PHP — UI Jeedom (page config, vue activité)
├── resources/
│   └── holmesMcpd/       # Daemon Python
│       ├── holmesMcpd.py # Point d'entrée daemon
│       ├── _core/        # Auth, DB, API JSON-RPC, logs
│       ├── _domain/      # Sanitisation, cmd_refs
│       ├── _tools/       # 25 tools (7 familles)
│       └── _resources/   # 5 resources
├── tests/
│   ├── unit/             # Tests unitaires (665 tests, 98% couverture)
│   └── integration/      # Tests d'intégration (fixtures synthétiques + live)
├── docs/
│   ├── user/             # Cette documentation (source MkDocs)
│   ├── decisions/        # ADRs (Architecture Decision Records)
│   ├── sessions/         # Journaux de sessions de développement
│   └── state/            # PROJECT_STATE.md, PLANNING.md, CONTRIBUTING
└── .github/workflows/    # CI (tests + lint + doc)
```

## Exécuter les tests

```bash
# Installer les dépendances de dev
pip install -e ".[test]"

# Tests unitaires
pytest tests/unit/ -v --cov=resources/holmesMcpd

# Lint et format
ruff check resources/ tests/
ruff format resources/ tests/
```

Les 665 tests unitaires doivent tous passer et la couverture globale doit rester ≥ 95%.

## Consulter les ADRs

Les décisions d'architecture sont documentées dans `docs/decisions/` (21 ADRs). Les ADRs au statut `accepted` font foi. Les ADRs `draft` ou `proposed` sont en discussion.

## Branches

| Branche | Rôle |
| --- | --- |
| `main` | Stable — versions taguées uniquement |
| `develop` | Intégration — PRs et développement actif |

Les PRs doivent cibler `develop`. La stratégie de merge est **fast-forward only** sur `main`.
