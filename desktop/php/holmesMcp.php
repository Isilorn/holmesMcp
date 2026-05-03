<?php
/* This file is part of Holmes MCP. Licence : AGPL-3.0 — see LICENSE */
/* Vue de configuration du plugin — page "Configuration" de l'UI Jeedom */

if (!isConnect('admin')) {
    throw new Exception(__('Accès non autorisé', __FILE__));
}

$mc_url = holmesMcp::getMcpUrl();
?>

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
<h4>{{Tokens d'accès par utilisateur}}</h4>
<p class="text-muted">
  {{Chaque utilisateur Jeedom peut avoir son propre token MCP. Copiez-le dans la configuration de votre client MCP.}}
</p>
<div id="holmesMcp_tokens">
  <?php
  foreach (user::all() as $user) {
      $uid   = $user->getId();
      $login = htmlspecialchars($user->getLogin(), ENT_QUOTES, 'UTF-8');
      $token = holmesMcp::getTokenForUser($uid);
      ?>
      <div class="form-group">
        <label class="col-sm-3 control-label"><?php echo $login; ?></label>
        <div class="col-sm-5">
          <input type="text" class="form-control" id="token_<?php echo $uid; ?>"
                 readonly value="<?php echo htmlspecialchars($token ?: '—', ENT_QUOTES, 'UTF-8'); ?>" />
        </div>
        <div class="col-sm-4">
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
