'use strict';

var holmesMcp = (function () {

    function generateToken(userId) {
        bootbox.confirm('{{Générer un nouveau token pour cet utilisateur ? L\'ancien token sera invalidé.}}', function (result) {
            if (!result) { return; }
            $.ajax({
                type: 'POST',
                url: 'core/ajax/holmesMcp.ajax.php',
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
                    $('#token_' + userId).val(data.result);
                    $('#message').showAlert({ message: '{{Token généré avec succès.}}', level: 'success' });
                },
            });
        });
    }

    return { generateToken: generateToken };
}());
