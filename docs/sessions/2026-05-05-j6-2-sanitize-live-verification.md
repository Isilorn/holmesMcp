# Session J6-2 — Vérification live sanitisation + enrichissement _PLUGIN_EXTRA_KEYS

**Date** : 2026-05-05
**Branche** : `develop`

## Objectif

Vérifier live sur la box PO les vrais champs credential pour 4 plugins (jMQTT, Alarme, JeedomConnect, MQTT Manager), enrichir `_domain/sanitize.py`, finaliser ADR-0017, produire le rapport de sanity check D15.6.

## Livrables

| Fichier | Ce qui a changé |
| --- | --- |
| `resources/holmesMcpd/_domain/sanitize.py` | `_PLUGIN_EXTRA_KEYS` : noms plugin corrigés + `mqttUser`/`mqttPass`/`mqttTlsClientKey` ajoutés |
| `tests/unit/_domain/test_sanitize.py` | Tests mis à jour (vrais noms, camelCase, fixtures D15.5) |
| `docs/decisions/ADR-0017.md` | Statut → `accepted`, table plugins finalisée, résultats J6-2 |
| `docs/state/PROJECT_STATE.md` | J6-2 ✅ marquée |

## Résultats vérification live (box Jeedom 4.5.3)

### jMQTT (eqType_name : `jMQTT`)

**Security gap confirmé** : les champs du broker MQTT sont en camelCase (`mqttUser`, `mqttPass`) — non couverts par la regex mech 2 et les extras précédents en minuscules (`mqttuser`) ne matchaient pas.

| Champ réel DB | Mech 2 (regex) | Mech 3 avant J6-2 | Mech 3 après J6-2 |
| --- | --- | --- | --- |
| `mqttUser` | ✗ | `mqttuser` (mauvaise casse) ✗ | `mqttUser` ✅ |
| `mqttPass` | ✗ | absent ✗ | `mqttPass` ✅ |
| `mqttTlsClientKey` | ✗ | absent ✗ | `mqttTlsClientKey` ✅ |
| `mqttTlsClientCert` | ✅ (`cert`) | — | — |

Brokers inspectés : Zwave, Zigbee, Nodered — `mqttUser`/`mqttPass` vides sur cette install (broker distant sans auth). Gap corrigé pour les installations avec credentials.

### Alarme (eqType_name réel : `alarm`)

**Nom de plugin incorrect** : la clé `'Alarme'` dans `_PLUGIN_EXTRA_KEYS` ne matchait rien (`eqType_name` = `alarm`).

**Blob config réel** : zones, triggers (`#cmdId#`), actions — **aucun code PIN ni mot de passe**. L'alarme stocke ses codes comme commandes Jeedom (type action), pas dans le blob `configuration`. Extras hypothétiques (`armCode`, `pin`, etc.) supprimés.

### JeedomConnect (eqType_name réel : `JeedomConnect`)

**Nom de plugin incorrect** : la clé `'Jeedom Connect'` (avec espace) ne matchait rien.

**Champs sensibles réels** : `apiKey`, `token`, `userHash`, `pwdAction` — **tous couverts par mech 2** (regex `apikey`, `token`, `hash`, `pwd`). Extras hypothétiques (`installCode`, etc.) conservés en défense en profondeur.

### MQTT Manager (eqType_name réel : `mqtt2`)

**Nom de plugin incorrect** : la clé `'MQTT Manager'` ne matchait rien (`eqType_name` = `mqtt2`).

**Blob config réel** : `createtime`, `updatetime` uniquement. Pas de credentials. Aucune table custom `mqtt%`. Extras hypothétiques supprimés.

### Bonus : noms rectifiés

| Ancien nom (faux) | Nom réel (eqType_name) |
| --- | --- |
| `Agenda` | `calendar` |
| `Virtuel` | `virtual` |

## Rapport sanitisé D15.6 — pour sanity check PO

### CAS 1 : JeedomConnect — données brutes vs sanitisées

**Données brutes (DB)** :
```json
{
  "apiKey": "7818f5e65929defffa6118598965ce57",
  "token": "f2lE0p_qCkEohZjWomjHar:APA91bFtu-W2B...",
  "userHash": "LDC32RxK1UuZZpceVFNKz7WXDlqxJUCW...",
  "pwdAction": "",
  "deviceName": "iPhone"
}
```

**Sortie Holmes MCP sanitisée** :
```json
{
  "apiKey": "***FILTERED***",
  "token": "***FILTERED***",
  "userHash": "***FILTERED***",
  "pwdAction": "***FILTERED***",
  "deviceName": "iPhone",
  "_filtered_fields": ["configuration.apiKey", "configuration.pwdAction", "configuration.token", "configuration.userHash"]
}
```

### CAS 2 : jMQTT broker — données brutes vs sanitisées

**Données brutes (DB)** :
```json
{
  "type": "broker",
  "mqttAddress": "mqtt.cname.iot.home.lan",
  "mqttUser": "",
  "mqttPass": "",
  "mqttTlsClientKey": "",
  "mqttTlsClientCert": ""
}
```

**Sortie Holmes MCP sanitisée** :
```json
{
  "type": "broker",
  "mqttAddress": "mqtt.cname.iot.home.lan",
  "mqttUser": "***FILTERED***",
  "mqttPass": "***FILTERED***",
  "mqttTlsClientKey": "***FILTERED***",
  "mqttTlsClientCert": "***FILTERED***",
  "_filtered_fields": ["configuration.mqttUser", "configuration.mqttPass", "configuration.mqttTlsClientKey", "configuration.mqttTlsClientCert"]
}
```

**Vérification anti-fuite** : aucun credential connu (apiKey JeedomConnect, token FCM) n'apparaît dans les sorties sanitisées. ✅

## Décisions prises en session

**Noms de plugin** : les clés de `_PLUGIN_EXTRA_KEYS` doivent correspondre exactement à `eqLogic.eqType_name`. Les noms "lisibles" (`Alarme`, `Virtuel`, `Jeedom Connect`, `MQTT Manager`) étaient des conventions internes incorrectes — remplacés par les vrais noms DB (`alarm`, `virtual`, `JeedomConnect`, `mqtt2`).

**Extras alarm vides** : le plugin `alarm` ne stocke pas de codes d'armement dans le blob `configuration`. Contrairement à l'hypothèse initiale (ADR-0021), les codes armement sont des commandes Jeedom. Extras supprimés pour ne pas laisser croire que la protection opère sur des champs inexistants.

**Extras JeedomConnect conservés** : même si les champs réels (`apiKey`, `token`) sont couverts par mech 2, les extras (`installCode`, etc.) sont maintenus comme couche défensive supplémentaire pour de futures versions du plugin.

## Résultats qualité

| Métrique | Valeur |
| --- | --- |
| Tests unitaires | 665/665 ✅ |
| Couverture `sanitize.py` | 100% |
| Couverture globale | 98% |
| Ruff | propre |

## Prochaine sous-session : J6-3 ou J7

**Si sanity check PO validé** → tag `v0.6.0` puis démarrage J7 (doc MkDocs + bêta privée).
