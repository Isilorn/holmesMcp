'use strict';

var holmesMcp = (function () {

    var _refreshTimer = null;

    function generateToken(userId) {
        bootbox.confirm('{{Générer un nouveau token pour cet utilisateur ? L\'ancien token sera invalidé.}}', function (result) {
            if (!result) { return; }
            $.ajax({
                type: 'POST',
                url: 'plugins/holmesMcp/core/ajax/holmesMcp.ajax.php',
                data: { action: 'generateToken', user_id: userId },
                dataType: 'json',
                error: function (request, status, error) {
                    handleAjaxError(request, status, error);
                },
                success: function (data) {
                    if (data.state !== 'ok') {
                        $('#message').showAlert({ message: data.result, level: 'danger' });
                        return;
                    }
                    var full = data.result;
                    var masked = full.substring(0, 8) + '••••••••••••••••';
                    $('#token_' + userId)
                        .val(masked)
                        .attr('data-full', full)
                        .attr('data-masked', '1');
                    $('#reveal_' + userId)
                        .prop('disabled', false)
                        .find('i').removeClass('fa-eye-slash').addClass('fa-eye');
                    $('#message').showAlert({ message: '{{Token généré avec succès.}}', level: 'success' });
                },
            });
        });
    }

    function toggleToken(userId) {
        var $input = $('#token_' + userId);
        var $icon  = $('#reveal_' + userId).find('i');
        var full   = $input.attr('data-full') || '';
        if (!full) { return; }
        if ($input.attr('data-masked') === '1') {
            $input.val(full).attr('data-masked', '0');
            $icon.removeClass('fa-eye').addClass('fa-eye-slash');
        } else {
            $input.val(full.substring(0, 8) + '••••••••••••••••').attr('data-masked', '1');
            $icon.removeClass('fa-eye-slash').addClass('fa-eye');
        }
    }

    function loadLogs() {
        var params = {
            action: 'getLogs',
            user:   $('#holmes_filter_user').val()   || '',
            tool:   $('#holmes_filter_tool').val()   || '',
            status: $('#holmes_filter_status').val() || '',
            window: $('#holmes_filter_window').val() || 86400,
        };
        $.ajax({
            type: 'POST',
            url: 'plugins/holmesMcp/core/ajax/holmesMcp.ajax.php',
            data: params,
            dataType: 'json',
            error: function () {
                $('#holmes_activity_body').html(
                    '<tr><td colspan="6" class="text-center text-danger">' +
                    '{{Erreur lors du chargement des logs.}}</td></tr>'
                );
            },
            success: function (data) {
                if (data.state !== 'ok') { return; }
                _renderTable(data.result);
                _updateFilterOptions(data.result);
            },
        });
    }

    function setupRefresh() {
        if (_refreshTimer) {
            clearInterval(_refreshTimer);
            _refreshTimer = null;
        }
        var interval = parseInt($('#holmes_refresh_interval').val(), 10);
        if (interval > 0) {
            _refreshTimer = setInterval(loadLogs, interval);
        }
    }

    function _renderTable(entries) {
        var $tbody = $('#holmes_activity_body');
        if (!entries || entries.length === 0) {
            $tbody.html(
                '<tr><td colspan="6" class="text-center text-muted">' +
                '{{Aucune activité sur cette période.}}</td></tr>'
            );
            return;
        }
        var rows = '';
        for (var i = 0; i < entries.length; i++) {
            var e = entries[i];
            var ts = (e.timestamp || '').replace('T', ' ').substring(0, 19);
            var statusCell = e.status === 'ok'
                ? '<span class="label label-success">ok</span>'
                : '<span class="label label-danger" title="' + _esc(e.error || '') + '">erreur</span>';
            rows += '<tr' + (e.status !== 'ok' ? ' class="danger"' : '') + '>' +
                '<td><small class="text-muted">' + _esc(ts) + '</small></td>' +
                '<td>' + _esc(e.user || '') + '</td>' +
                '<td><code>' + _esc(e.tool || '') + '</code></td>' +
                '<td><small class="text-muted">' + _esc(e.params_summary || '') + '</small></td>' +
                '<td style="white-space:nowrap">' + (e.duration_ms || 0) + ' ms</td>' +
                '<td>' + statusCell + '</td>' +
                '</tr>';
        }
        $tbody.html(rows);
    }

    function _updateFilterOptions(entries) {
        if (!entries || entries.length === 0) { return; }
        var users = {}, tools = {};
        for (var i = 0; i < entries.length; i++) {
            if (entries[i].user) { users[entries[i].user] = true; }
            if (entries[i].tool) { tools[entries[i].tool] = true; }
        }
        var $fu = $('#holmes_filter_user');
        var $ft = $('#holmes_filter_tool');
        var curUser = $fu.val();
        var curTool = $ft.val();
        $fu.find('option:not(:first)').remove();
        Object.keys(users).sort().forEach(function (u) {
            $fu.append($('<option>').val(u).text(u));
        });
        if (curUser) { $fu.val(curUser); }
        $ft.find('option:not(:first)').remove();
        Object.keys(tools).sort().forEach(function (t) {
            $ft.append($('<option>').val(t).text(t));
        });
        if (curTool) { $ft.val(curTool); }
    }

    function _esc(s) {
        return String(s)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }

    return {
        generateToken: generateToken,
        toggleToken:   toggleToken,
        loadLogs:      loadLogs,
        setupRefresh:  setupRefresh,
    };
}());
