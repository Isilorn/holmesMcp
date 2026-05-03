# ROADMAP.md — Holmes MCP

> Candidates V1.x / V2+ / V3+ — exutoire anti-drift (D8.2).  
> Tout nouveau besoin émergent pendant V1 atterrit ici, **pas en V1**.  
> Statut de toutes les entrées : `draft` jusqu'à validation PO et ADR dédiée.

---

## V1.x — Candidates post-release (mineures, rétro-compatibles)

Évolutions ne cassant pas les schémas in/out des tools/resources V1. Introduites sur retour communauté ou PO.

| Feature | Source brief | Motivation | Effort estimé |
|---|---|---|---|
| **Prompts MCP** (slash commands) | D1.1, D6.5 | Cadrage onboarding, meilleure UX pour nouveaux utilisateurs. Exclu V1 (coût évals + support client variable). | Moyen (évals + docs) |
| **Multi-tokens par utilisateur** (un token par appareil/client) | D4.5 | Un Jeedomiste avec Claude Desktop + Cursor veut des tokens distincts pour traçabilité fine. | Faible (extension `User->setOption()`) |
| **Scopes par rôle Jeedom** (admin vs user) | D4.4 | Un utilisateur Jeedom "user" (non-admin) a accès à un sous-ensemble des tools. | Moyen (middleware auth) |
| **Énumération resources étendue** (>5, plafond configurable) | D6.1 | Installations très grandes : plus de scénarios/équipements énumérés dans `resources/list`. | Faible (config plafond) |
| **Tool "design" / "propose_scenario"** côté serveur | D5.2 | Cadrage plus fort si LLM a du mal à générer des scénarios Jeedom bien formés. Évaluer sur retours V1. | Élevé (logique serveur) |
| **Évals LLM-side** (qualité de réponse) | D11.5 | Mesurer en CI la qualité des réponses du LLM consommant le MCP (outil : Braintrust ou équivalent). | Élevé (infrastructure évals) |
| **Avertissement page config si IP non-LAN** | §10.7 risques | Détecter si le port MCP est accessible depuis l'extérieur et avertir l'utilisateur. | Faible (détection IP) |
| **Raffinements UI vue logs** | D14.4 | Graphes d'activité, export CSV, filtres avancés sur les logs Holmes MCP. | Moyen |
| **Support Jeedom 4.6+** | D12.3 | Politique N/N-1 : quand Jeedom 4.6 sortira, tester et documenter le support. | Variable (dépend des breaking changes Jeedom) |

---

## V2+ — Candidates majeures (écriture via API)

Introduites dans une version majeure (2.0.0) avec migration guide. **L'écriture passe exclusivement par l'API JSON-RPC, jamais par SQL direct** (D4bis.7 — non négociable à perpétuité).

| Feature | Source brief | Motivation | Garde-fous requis |
|---|---|---|---|
| **Exécuter un scénario** (`cmd::execCmd`, `scenario::changeState`) | D5.1, D4bis.5 | Cas d'usage le plus demandé : "Lance le scénario Réveil" | Scope, whitelist méthodes, journal, confirmation LLM |
| **Activer / désactiver un scénario** | D5.1 | Maintenance domotique : activer/désactiver sans ouvrir l'UI | Idem ci-dessus |
| **Écrire une variable dataStore** (`datastore::save`) | D5.1, D4bis.5 | Modifier une variable pour déclencher une logique applicative | Whitelist variables, scope |
| **Exécuter une commande action** | D5.1 | "Allume la lumière du salon" | Scope, confirmation, dry-run |
| **Whitelist explicite des méthodes API autorisées** | D4bis.5 | En V2+, l'approche bascule de blacklist → whitelist positive | ADR de la whitelist |

Critères d'engagement V2 : retours communautaires V1 suffisants, scope guards définis, ADR de la transition.

---

## V3+ — Candidates de configuration légère

| Feature | Source brief | Motivation |
|---|---|---|
| **Renommage d'équipement / commande** via API | ADR-0006 §V3 | Maintenance sans UI Jeedom |
| **Déplacement hiérarchique** (objet, équipement) | ADR-0006 §V3 | Réorganisation domotique |
| **Ajout / modification de Types Génériques** | ADR-0006 §V3 | Classification des commandes, utile pour les automatisations |

---

## Co-événements (liés à la sphère jeedom-audit)

| Événement | Dépendance | Jalon cible |
|---|---|---|
| **Bascule jeedom-skills MIT → AGPL-3.0** | Copyright holder unique confirmé (D10.4) | Annonce conjointe V1.0.0 Holmes MCP |
| **Bascule jeedom-audit consommatrice MCP** | Matrice D5.8 validée, V1.0.0 stable sur market | Post-V1.0.0 stable (décision PO) |
| **Scripts jeedom-audit marqués DEPRECATED** | Bascule consommatrice MCP effective | Post-bascule |

---

## Processus d'entrée dans la roadmap

Tout nouveau besoin identifié pendant V1 (en session, par retour communauté, ou par le PO) :
1. S'assure qu'il n'est pas déjà en V1 (discipline anti-drift D8.2)
2. Ajoute une entrée dans la section V1.x, V2+ ou V3+ de ce fichier avec un commentaire de source
3. Crée une issue GitHub associée (label `roadmap`)
4. Ne l'implémente **pas** en V1 sauf ADR + validation PO explicite (D8.2)
