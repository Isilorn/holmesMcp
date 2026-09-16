"""Remontée expression → scénario (ADR-0023).

`scenarioElement` ne porte AUCUNE colonne de rattachement au scénario : le lien vit
dans le JSON `scenario.scenarioElement`, qui ne liste que les éléments **racines**.
Les éléments imbriqués s'atteignent depuis leur parent par une expression
`type='element'` dont l'`expression` porte l'id de l'enfant.

Toute remontée « quel scénario contient cette expression ? » est donc **récursive**.
Sur l'installation de référence : 116 racines pour 374 éléments — 69 % des éléments
sont invisibles à un rattachement direct.

Deux façons de se tromper, toutes deux constatées en production :

- `JOIN scenario s ON s.scenarioElement LIKE CONCAT('%', sel.id, '%')` — l'élément 1
  matche `["100","218"]` : 199 rattachements inventés sur l'installation de référence,
  plus tous les imbriqués manqués.
- `JOIN scenario s ON JSON_SEARCH(s.scenarioElement, 'one', CAST(sel.id AS CHAR))` —
  exact, donc zéro invention, mais **racines seulement** : 31 % de rappel.

Le test de racine retenu reste `JSON_SEARCH` (exact, éprouvé). Ce module n'ajoute que
ce qui manquait : la remontée de l'élément porteur jusqu'à ses racines.
"""

from __future__ import annotations

# Garde-fou anti-cycle : une chaîne d'éléments Jeedom ne dépasse pas quelques niveaux
# (5 au plus profond sur l'installation de référence). `UNION` déduplique déjà, cette
# borne protège d'un graphe corrompu.
MAX_DEPTH = 20

_CTE_TEMPLATE = """WITH RECURSIVE anc (expr_id, ss_id, node_id, depth) AS (
    SELECT x.id, ss.id, ss.scenarioElement_id, 0
    FROM scenarioExpression x
    JOIN scenarioSubElement ss ON ss.id = x.scenarioSubElement_id
    {seed_joins}
    WHERE {seed_where}
  UNION
    SELECT a.expr_id, a.ss_id, ss2.scenarioElement_id, a.depth + 1
    FROM anc a
    JOIN scenarioExpression x2  ON x2.type = 'element'
                               AND x2.expression = CAST(a.node_id AS CHAR)
    JOIN scenarioSubElement ss2 ON ss2.id = x2.scenarioSubElement_id
    WHERE a.depth < {max_depth}
)
"""

# Rattachement d'un nœud remonté à son scénario — exact, jamais de sous-chaîne.
ROOT_JOIN = (
    "JOIN scenario s ON JSON_SEARCH(s.scenarioElement, 'one', CAST(a.node_id AS CHAR)) IS NOT NULL"
)

# Retour aux lignes d'origine (l'expression qui cite la cible, et son sous-élément).
EXPR_JOIN = 'JOIN scenarioExpression expr ON expr.id = a.expr_id'
SUBELEMENT_JOIN = 'JOIN scenarioSubElement ss ON ss.id = a.ss_id'


def ancestors_cte(seed_where: str, seed_joins: str = '') -> str:
    """CTE récursive remontant l'élément porteur d'une expression jusqu'à ses racines.

    Args:
        seed_where : condition de sélection des expressions de départ. Ne contient que
                     du SQL écrit dans ce dépôt ; les valeurs passent par des `%s`.
        seed_joins : jointures supplémentaires pour la sélection de départ (ex. `cmd`).

    La CTE expose `anc(expr_id, ss_id, node_id, depth)` : `expr_id`/`ss_id` désignent
    la ligne d'origine, `node_id` un ancêtre (l'élément porteur lui-même à depth 0).
    """
    return _CTE_TEMPLATE.format(
        seed_joins=seed_joins,
        seed_where=seed_where,
        max_depth=MAX_DEPTH,
    )
