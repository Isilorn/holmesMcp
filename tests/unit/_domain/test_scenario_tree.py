"""Tests unitaires _domain/scenario_tree.py — fragment SQL de remontée récursive.

La correction se JOUE en base (CTE récursive) : ces tests garantissent la forme du
SQL produit — la preuve de résultat, elle, est dans les tests d'intégration live
(`tests/integration/tools/test_recursive_usages_live.py`), avec les chiffres
mesurés sur la box comme oracle.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3] / 'resources' / 'holmesMcpd'))

from _domain import scenario_tree as tree


class TestAncestorsCte:
    def test_is_recursive(self):
        sql = tree.ancestors_cte(seed_where='x.expression LIKE %s')
        assert 'WITH RECURSIVE' in sql

    def test_seed_where_injected(self):
        sql = tree.ancestors_cte(seed_where="x.expression = 'scenario'")
        assert "WHERE x.expression = 'scenario'" in sql

    def test_seed_joins_injected(self):
        sql = tree.ancestors_cte(
            seed_where='c.eqLogic_id = %s',
            seed_joins='JOIN cmd c ON 1 = 1',
        )
        assert 'JOIN cmd c ON 1 = 1' in sql

    def test_seed_joins_optional(self):
        sql = tree.ancestors_cte(seed_where='1 = 1')
        assert 'JOIN cmd' not in sql

    def test_climbs_through_element_expressions(self):
        """La remontée suit les expressions type='element' — le seul lien enfant→parent."""
        sql = tree.ancestors_cte(seed_where='1 = 1')
        assert "x2.type = 'element'" in sql
        assert 'x2.expression = CAST(a.node_id AS CHAR)' in sql

    def test_depth_guard_present(self):
        sql = tree.ancestors_cte(seed_where='1 = 1')
        assert f'a.depth < {tree.MAX_DEPTH}' in sql

    def test_exposes_expected_columns(self):
        sql = tree.ancestors_cte(seed_where='1 = 1')
        assert 'anc (expr_id, ss_id, node_id, depth)' in sql

    def test_union_deduplicates(self):
        """UNION (et non UNION ALL) : un graphe cyclique ne peut pas boucler."""
        sql = tree.ancestors_cte(seed_where='1 = 1')
        assert 'UNION ALL' not in sql
        assert 'UNION' in sql


class TestRootJoin:
    def test_uses_exact_json_search(self):
        """Le test de racine reste exact : c'est lui qui interdit les faux positifs."""
        assert "JSON_SEARCH(s.scenarioElement, 'one', CAST(a.node_id AS CHAR))" in tree.ROOT_JOIN

    def test_never_uses_like_on_scenario_element(self):
        assert 'LIKE' not in tree.ROOT_JOIN


class TestBackJoins:
    def test_expr_join_returns_to_origin_row(self):
        assert 'expr.id = a.expr_id' in tree.EXPR_JOIN

    def test_subelement_join_returns_to_origin_row(self):
        assert 'ss.id = a.ss_id' in tree.SUBELEMENT_JOIN
