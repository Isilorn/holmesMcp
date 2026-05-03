# ADR 0006 : Lecture seule absolue V1 + roadmap V2/V3

- **Date** : 2026-04-27
- **Statut** : Accepté
- **Contexte de décision** : idéation initiale (D1.5, D3.2, D8.1)

## Contexte

Une skill de diagnostic et d'audit Jeedom pourrait en théorie effectuer des modifications (lancer un scénario, corriger une valeur, renommer un équipement). Certains utilisateurs le demanderont. Il faut décider si V1 autorise des opérations d'écriture et dans quelles conditions.

## Options considérées

- **Option A — Lecture seule absolue V1** : aucune modification, toute suggestion de modification = pas-à-pas verbal pour que l'utilisateur l'exécute via l'UI. ➕ Sécurité maximale, impossibilité de causer des dégâts, confiance utilisateur. ➖ Friction pour les opérations répétitives de maintenance.
- **Option B — Opérations modifiantes limitées dès V1** : lancer un scénario, activer/désactiver, avec confirmation. ➕ Utilité accrue. ➖ Risque de dérive scope, sécurité à prouver, complexité accrue pour une V1.
- **Option C — Lecture seule V1, modifiant V2+** : roadmap explicite permettant d'anticiper sans implémenter prématurément. ➕ Focus V1, extensibilité planifiée.

## Décision

**Option A pour V1, avec roadmap V2/V3 explicite (Option C).**

| Phase | Posture | Périmètre |
|---|---|---|
| **V1** | Lecture seule absolue | Aucune méthode API modifiante, aucun INSERT/UPDATE/DELETE SQL |
| **V2** | Opérations réversibles via API + confirmation | Lancer scénario, activer/désactiver, exécuter cmd action, écrire variable dataStore |
| **V3** | Modifications config légère via API | Renommages, déplacements hiérarchie, ajout Types Génériques |
| **Jamais** | Hors limite indéfinie | UPDATE/DELETE/INSERT SQL directs, modifications schéma |

**Méthodes API blacklistées V1** (codées en dur dans `api_call.py`) :
- `cmd::execCmd`, `scenario::changeState`, `datastore::save`, `interact::tryToReply`
- Toute méthode dont le nom suggère une modification

**Comportement face à l'insistance** : refus en une phrase, sans excuses longues, énergie sur l'alternative (pas-à-pas UI).

## Conséquences

- ✅ Impossibilité technique de modifier l'installation (blacklist codée en dur)
- ✅ Confiance utilisateur maximale : la skill est un outil de lecture, pas d'action
- ✅ User MySQL read-only à perpétuité (même V2/V3 passent par l'API)
- ⚠️ Certaines demandes naturelles ("change le nom de cet équipement") reçoivent un refus + pas-à-pas
- ⚠️ La blacklist API doit être maintenue à jour à chaque version Jeedom
- 🔗 ADR 0005 (accès MySQL), PLANNING §3.3-3.4

---

## Amendement — 2026-05-01 : lecture seule perpétuelle

**Décision amendée** : la lecture seule n'est plus "absolue V1 avec roadmap V2/V3 modifiante" — elle est **perpétuelle dans `jeedom-audit`**.

Les capacités modifiantes prévues en V2/V3 (lancer scénario, activer/désactiver, écrire variable dataStore, modifications légères de configuration) sont **définitivement retirées du périmètre de cette skill**. Elles seront implémentées dans un projet séparé (voir ADR-0020).

**Raisons :**

1. **Identité de la skill** : la lecture seule absolue est devenue une caractéristique identitaire forte, valorisée par la communauté ("la skill ne peut pas casser votre install"). L'affaiblir — même progressivement — détruirait cette proposition de valeur.

2. **Destination naturelle** : le protocole MCP, conçu pour exposer des outils à n'importe quel client LLM, est l'architecture adéquate pour les opérations pilotées. Un plugin Jeedom natif distribuable via le market est le bon vecteur — pas une skill Claude Code réservée aux power users avec SSH.

3. **Séparation des préoccupations** : `jeedom-audit` = outil de compréhension (diagnostic, explication, audit). `jeedom-mcp` = outil de contrôle (actions, modifications). Deux produits distincts, deux personas distincts.

**Conséquences de l'amendement :**

- ✅ La roadmap V2/V3 de ce repo ne contient plus de capacités modifiantes
- ✅ La table "Phase / Posture / Périmètre" ci-dessus est caduque pour les lignes V2 et V3
- ✅ PLANNING.md §10 (roadmap) doit être lu à la lumière de cet amendement
- 🔗 ADR-0020 (projet jeedom-mcp — plugin Jeedom natif MCP)
