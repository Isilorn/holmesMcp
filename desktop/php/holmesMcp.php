<?php
/* This file is part of Holmes MCP. Licence : AGPL-3.0 — see LICENSE */
/* Vue de configuration du plugin — page "Configuration" de l'UI Jeedom */

if (!isConnect('admin')) {
    throw new Exception(__('Accès non autorisé', __FILE__));
}

include_file('desktop', 'holmesMcp', 'js', 'holmesMcp');

$mc_url = holmesMcp::getMcpUrl();
?>

<h4><i class="fas fa-cog"></i> {{Configuration daemon}}</h4>
<form class="form-horizontal">
  <fieldset>

    <!-- Port MCP -->
    <div class="form-group">
      <label class="col-sm-3 control-label">{{Port MCP}}</label>
      <div class="col-sm-2">
        <input type="number" class="configKey form-control" data-l1key="port"
               placeholder="8765" min="1024" max="65535" />
      </div>
      <div class="col-sm-7">
        <span class="help-block">
          {{Port d'écoute du daemon Holmes MCP. Doit être libre sur votre box. Redémarrez le daemon après modification.}}
        </span>
      </div>
    </div>

    <!-- URL MCP (lecture seule, informatif) -->
    <div class="form-group">
      <label class="col-sm-3 control-label">{{URL MCP}}</label>
      <div class="col-sm-7">
        <div class="input-group">
          <input type="text" id="holmesMcp_url" class="form-control"
                 readonly value="<?php echo htmlspecialchars($mc_url, ENT_QUOTES, 'UTF-8'); ?>" />
          <span class="input-group-btn">
            <button class="btn btn-default" type="button" onclick="navigator.clipboard.writeText(document.getElementById('holmesMcp_url').value)">
              <i class="fas fa-copy"></i>
            </button>
          </span>
        </div>
        <span class="help-block">
          {{URL à coller dans votre client MCP (Claude Desktop, Cursor…). Ajoutez un header Authorization: Bearer <token>.}}
        </span>
      </div>
    </div>

  </fieldset>
</form>

<!-- Section tokens par utilisateur -->
<hr />
<h4><i class="fas fa-key"></i> {{Tokens d'accès par utilisateur}}</h4>
<p class="text-muted">
  {{Chaque utilisateur Jeedom peut avoir son propre token MCP. Copiez-le dans la configuration de votre client MCP.}}
</p>
<form class="form-horizontal">
<div id="holmesMcp_tokens">
  <?php
  foreach (user::all() as $user) {
      $uid    = $user->getId();
      $login  = htmlspecialchars($user->getLogin(), ENT_QUOTES, 'UTF-8');
      $token  = holmesMcp::getTokenForUser($uid);
      $masked = $token
          ? (htmlspecialchars(substr($token, 0, 8), ENT_QUOTES, 'UTF-8') . str_repeat('•', 16))
          : '—';
      $full   = $token ? htmlspecialchars($token, ENT_QUOTES, 'UTF-8') : '';
      ?>
      <div class="form-group">
        <label class="col-xs-3 control-label"><?php echo $login; ?></label>
        <div class="col-xs-5">
          <div class="input-group">
            <input type="text" class="form-control" id="token_<?php echo $uid; ?>"
                   readonly
                   value="<?php echo $masked; ?>"
                   data-full="<?php echo $full; ?>"
                   data-masked="1" />
            <span class="input-group-btn">
              <button class="btn btn-default btn-sm" type="button"
                      id="reveal_<?php echo $uid; ?>"
                      onclick="holmesMcp.toggleToken(<?php echo $uid; ?>)"
                      <?php echo $token ? '' : 'disabled="disabled"'; ?>>
                <i class="fas fa-eye"></i>
              </button>
            </span>
          </div>
        </div>
        <div class="col-xs-4">
          <button class="btn btn-sm btn-warning" type="button"
                  onclick="holmesMcp.generateToken(<?php echo $uid; ?>)">
            <i class="fas fa-sync-alt"></i> {{Générer / Régénérer}}
          </button>
        </div>
      </div>
      <?php
  }
  ?>
</div>
</form>
<div class="clearfix"></div>

<!-- Section activité MCP (D14.4) -->
<hr />
<h4><i class="fas fa-list-alt"></i> {{Activité MCP}}</h4>
<p class="text-muted">
  {{Appels de tools enregistrés par le daemon Holmes MCP.}}
</p>

<div class="row" style="margin-bottom:8px">
  <div class="col-xs-2">
    <select id="holmes_filter_user" class="form-control input-sm">
      <option value="">{{Tous les utilisateurs}}</option>
    </select>
  </div>
  <div class="col-xs-2">
    <select id="holmes_filter_tool" class="form-control input-sm">
      <option value="">{{Tous les tools}}</option>
    </select>
  </div>
  <div class="col-xs-2">
    <select id="holmes_filter_status" class="form-control input-sm">
      <option value="">{{Tous statuts}}</option>
      <option value="ok">{{OK}}</option>
      <option value="error">{{Erreur}}</option>
    </select>
  </div>
  <div class="col-xs-2">
    <select id="holmes_filter_window" class="form-control input-sm">
      <option value="3600">{{Dernière heure}}</option>
      <option value="21600">{{6 heures}}</option>
      <option value="86400" selected="selected">{{24 heures}}</option>
      <option value="604800">{{7 jours}}</option>
    </select>
  </div>
  <div class="col-xs-2">
    <select id="holmes_refresh_interval" class="form-control input-sm">
      <option value="0">{{Pas de refresh}}</option>
      <option value="5000">{{Refresh 5s}}</option>
      <option value="30000" selected="selected">{{Refresh 30s}}</option>
    </select>
  </div>
  <div class="col-xs-2">
    <button class="btn btn-default btn-sm" type="button" onclick="holmesMcp.loadLogs()">
      <i class="fas fa-sync-alt"></i> {{Rafraîchir}}
    </button>
  </div>
</div>

<div class="table-responsive">
  <table class="table table-condensed table-striped table-hover">
    <thead>
      <tr>
        <th style="white-space:nowrap">{{Date/heure}}</th>
        <th>{{Utilisateur}}</th>
        <th>{{Tool}}</th>
        <th>{{Paramètres}}</th>
        <th style="white-space:nowrap">{{Durée}}</th>
        <th>{{Résultat}}</th>
      </tr>
    </thead>
    <tbody id="holmes_activity_body">
      <tr>
        <td colspan="6" class="text-center text-muted">
          <i class="fas fa-spinner fa-spin"></i> {{Chargement…}}
        </td>
      </tr>
    </tbody>
  </table>
</div>

<script>
holmesMcp.loadLogs();
holmesMcp.setupRefresh();
$('#holmes_refresh_interval').on('change', function () { holmesMcp.setupRefresh(); });
$('#holmes_filter_user, #holmes_filter_tool, #holmes_filter_status, #holmes_filter_window').on('change', function () {
  holmesMcp.loadLogs();
});
</script>
