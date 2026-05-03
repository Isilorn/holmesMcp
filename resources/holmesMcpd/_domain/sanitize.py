"""Sanitisation des données Jeedom avant exposition MCP (D15.1-D15.6).

3 mécanismes cumulatifs :
  1. Blacklist champs sensibles (regex) — mask + count
  2. Filtrage actif des valeurs suspectes (patterns credentials)
  3. Validation schéma retour tool

Couverture tests : 100% obligatoire (ADR-0017).
Dérivé de jeedom-audit/_common/sensitive_fields.py — étendu (3 mécanismes, mask+count).
Ref jeedom-audit : _common/sensitive_fields.py @ commit à préciser en J1 (D7.4).
Implémenté à partir de J2 (_domain layer).
"""
# Stub J0 — implémentation complète en J2
