"""Tests d'intégration live — remontée expression → scénario (ADR-0023).

Ces tests ne figent AUCUN identifiant de l'installation : ils recalculent la vérité
depuis la base (remontée récursive de référence, écrite ici en Python) et comparent
le tool à cette vérité. Un test qui se contenterait de vérifier « le tool trouve
quelque chose » mesurerait la sensibilité, pas la précision — c'est exactement ce
qui avait laissé passer une surestimation d'un facteur 3 côté jeedom-audit V1.

Garde-fou de vacuité : la comparaison exige au moins un cas réellement imbriqué,
sinon le test passerait sur une box sans blocs imbriqués sans rien prouver.
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[3] / 'resources' / 'holmesMcpd'))

from _core import db as _db
from _domain.sanitize import FILTERED
from tools import equipments, query_sql, scenarios

pytestmark = pytest.mark.integration

_CMD_REF_RE = re.compile(r'#(\d+)#')
_SAMPLE_SIZE = 40


# ── Vérité de référence, recalculée depuis la base ────────────────────────────


class _Truth:
    """Remontée récursive de référence — indépendante du SQL des tools."""

    def __init__(self, conn) -> None:
        self.roots: dict[int, int] = {}
        for s in _db.query(conn, 'SELECT id, name, scenarioElement FROM scenario'):
            try:
                ids = json.loads(s['scenarioElement'] or '[]')
            except (ValueError, TypeError):
                ids = []
            for elem in ids:
                self.roots[int(elem)] = int(s['id'])

        self.parents: dict[int, list[int]] = defaultdict(list)
        for r in _db.query(
            conn,
            'SELECT ss.scenarioElement_id AS p, x.expression AS c FROM scenarioExpression x'
            ' JOIN scenarioSubElement ss ON ss.id = x.scenarioSubElement_id'
            " WHERE x.type = 'element'",
        ):
            if r['p'] is not None and str(r['c']).strip().isdigit():
                self.parents[int(r['c'])].append(int(r['p']))

        self.cmd_elements: dict[int, set[int]] = defaultdict(set)
        for r in _db.query(
            conn,
            'SELECT x.expression, ss.scenarioElement_id AS el FROM scenarioExpression x'
            ' JOIN scenarioSubElement ss ON ss.id = x.scenarioSubElement_id'
            " WHERE x.expression REGEXP '#[0-9]+#'",
        ):
            if r['el'] is None:
                continue
            for m in _CMD_REF_RE.finditer(r['expression'] or ''):
                self.cmd_elements[int(m.group(1))].add(int(r['el']))

    def scenarios_of_element(self, elem: int, seen: frozenset[int] | None = None) -> set[int]:
        seen = seen or frozenset()
        if elem in seen:
            return set()
        seen = seen | {elem}
        found = {self.roots[elem]} if elem in self.roots else set()
        for parent in self.parents.get(elem, []):
            found |= self.scenarios_of_element(parent, seen)
        return found

    def scenarios_of_cmd(self, cmd_id: int) -> set[int]:
        found: set[int] = set()
        for elem in self.cmd_elements.get(cmd_id, set()):
            found |= self.scenarios_of_element(elem)
        return found

    def is_nested(self, elem: int) -> bool:
        return elem not in self.roots


@pytest.fixture(scope='module')
def truth(db_conn) -> _Truth:
    return _Truth(db_conn)


@pytest.fixture(scope='module')
def sampled_cmds(truth) -> list[int]:
    """Commandes citées dans une expression, imbriquées d'abord — ordre déterministe."""
    nested = sorted(
        c for c, els in truth.cmd_elements.items() if any(truth.is_nested(e) for e in els)
    )
    flat = sorted(c for c in truth.cmd_elements if c not in set(nested))
    return (nested + flat)[:_SAMPLE_SIZE]


# ── find_command_usages ───────────────────────────────────────────────────────


class TestFindCommandUsagesRecursive:
    def test_echantillon_non_vide_et_imbrique(self, truth, sampled_cmds):
        """Sans élément imbriqué dans l'échantillon, la comparaison ne prouverait rien."""
        assert sampled_cmds, 'aucune commande citée dans une expression'
        nested = [c for c in sampled_cmds if any(truth.is_nested(e) for e in truth.cmd_elements[c])]
        assert nested, 'échantillon sans élément imbriqué — test sans valeur probante'

    def test_scenarios_identiques_a_la_verite(self, db_conn, truth, sampled_cmds):
        ecarts = []
        for cmd_id in sampled_cmds:
            attendu = truth.scenarios_of_cmd(cmd_id)
            result = equipments.find_command_usages(db_conn, cmd_id)
            obtenu = {int(r['id']) for r in result['expressions']}
            if obtenu != attendu:
                ecarts.append((cmd_id, sorted(attendu), sorted(obtenu)))
        assert not ecarts, f'{len(ecarts)} commande(s) en écart : {ecarts[:5]}'

    def test_aucun_scenario_invente(self, db_conn, truth, sampled_cmds):
        for cmd_id in sampled_cmds:
            result = equipments.find_command_usages(db_conn, cmd_id)
            obtenu = {int(r['id']) for r in result['expressions']}
            inventes = obtenu - truth.scenarios_of_cmd(cmd_id)
            assert not inventes, f'cmd {cmd_id} : scénario(s) inventé(s) {sorted(inventes)}'

    def test_commande_sans_usage_rend_zero(self, db_conn, truth):
        """Un zéro doit rester un zéro : la remontée n'invente rien sur une cmd non citée."""
        rows = _db.query(db_conn, 'SELECT id FROM cmd ORDER BY id DESC LIMIT 400')
        libres = [int(r['id']) for r in rows if not truth.cmd_elements.get(int(r['id']))]
        assert libres, 'aucune commande non référencée trouvée'
        result = equipments.find_command_usages(db_conn, libres[0])
        assert result['total_expressions'] == 0
        assert result['total_triggers'] == 0


class TestFindEquipmentUsagesRecursive:
    def test_scenarios_identiques_a_la_verite(self, db_conn, truth, sampled_cmds):
        cmd_id = sampled_cmds[0]
        rows = _db.query(db_conn, 'SELECT eqLogic_id FROM cmd WHERE id = %s', (cmd_id,))
        eq_id = int(rows[0]['eqLogic_id'])

        cmd_ids = [
            int(r['id'])
            for r in _db.query(db_conn, 'SELECT id FROM cmd WHERE eqLogic_id = %s', (eq_id,))
        ]
        attendu: set[int] = set()
        for cid in cmd_ids:
            attendu |= truth.scenarios_of_cmd(cid)

        result = equipments.find_equipment_usages(db_conn, eq_id)
        obtenu = {int(s['id']) for s in result['scenarios']}
        assert obtenu == attendu


# ── find_scenario_dependencies ────────────────────────────────────────────────


class TestFindScenarioDependenciesRecursive:
    def test_callers_identiques_a_la_verite(self, db_conn, truth):
        ecarts = []
        for row in _db.query(db_conn, 'SELECT id FROM scenario ORDER BY id'):
            sid = int(row['id'])
            appels = _db.query(
                db_conn,
                'SELECT ss.scenarioElement_id AS el FROM scenarioExpression x'
                ' JOIN scenarioSubElement ss ON ss.id = x.scenarioSubElement_id'
                " WHERE x.expression = 'scenario' AND x.options LIKE %s",
                (f'%"scenario_id":"{sid}"%',),
            )
            attendu: set[int] = set()
            for a in appels:
                if a['el'] is not None:
                    attendu |= truth.scenarios_of_element(int(a['el']))

            result = scenarios.find_scenario_dependencies(db_conn, sid)
            obtenu = {int(c['id']) for c in result['references']['scenario_calls']}
            if obtenu != attendu:
                ecarts.append((sid, sorted(attendu), sorted(obtenu)))
        assert not ecarts, f'{len(ecarts)} scénario(s) en écart : {ecarts[:5]}'


# ── query_sql : agrégats, troncature, table config ────────────────────────────


class TestQuerySqlComputedAndTruncationLive:
    def test_count_rendu_en_clair(self, db_conn):
        reel = _db.query(db_conn, 'SELECT COUNT(*) AS n FROM scenario')[0]['n']
        result = query_sql.query_sql(db_conn, 'SELECT COUNT(*) AS n FROM scenario')
        assert result['rows'][0]['n'] == reel
        assert result['rows'][0]['n'] != FILTERED

    def test_agregat_sur_colonne_non_exposable_reste_filtre(self, db_conn):
        result = query_sql.query_sql(db_conn, 'SELECT MAX(configuration) AS m FROM scenario')
        assert result['rows'][0]['m'] == FILTERED

    def test_troncature_signalee(self, db_conn):
        result = query_sql.query_sql(db_conn, 'SELECT id FROM cmd')
        assert result['truncated'] is True
        assert result['limit_applied'] == result['count']

    def test_absence_de_troncature_signalee(self, db_conn):
        """`truncated` dit que la limite a été ATTEINTE — ici une seule ligne sur 50."""
        result = query_sql.query_sql(db_conn, 'SELECT COUNT(*) AS n FROM scenario')
        assert result['truncated'] is False
        assert result['count'] == 1

    def test_config_sans_colonne_key_est_masquee(self, db_conn):
        """Fail closed : sans `key`, la valeur ne peut pas être qualifiée → masquée."""
        result = query_sql.query_sql(db_conn, 'SELECT value FROM config LIMIT 5')
        assert result['rows'], 'table config vide'
        assert all(r['value'] == FILTERED for r in result['rows'])

    def test_config_avec_colonne_key_reste_lisible(self, db_conn):
        """La correction ne doit pas aveugler l'usage légitime."""
        result = query_sql.query_sql(
            db_conn, "SELECT `key`, value FROM config WHERE `key` = 'language' LIMIT 1"
        )
        if result['rows']:
            assert result['rows'][0]['value'] != FILTERED
