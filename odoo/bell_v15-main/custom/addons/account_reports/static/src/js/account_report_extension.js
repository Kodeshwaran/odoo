odoo.define('account_reports.account_report_extension', function (require) {
    'use strict';

    var AccountReport = require('account_reports.account_report');
    var core = require('web.core');

    var _t = core._t;

    AccountReport.include({
        renderButtons: function ($node) {
            this._super.apply(this, arguments);
            const self = this;

            // Check if we are in the Aged Receivable Report
            if (this.report_model === 'account.aged_receivable.report') {
                // Add custom button
                if (!$node) {
                    return;
                }
                var $customButton = $('<button>', {
                    type: 'button',
                    text: _t('Open Wizard'),
                    class: 'btn btn-primary custom-aged-receivable-wizard',
                }).appendTo($node);

                // Bind click event
                $customButton.on('click', function () {
                    self._openCustomWizard();
                });
            }
        },

        _openCustomWizard: function () {
            this.do_action({
                name: _t('Custom Aged Receivable Wizard'),
                type: 'ir.actions.act_window',
                res_model: 'your.wizard.model',
                views: [[false, 'form']],
                target: 'new',
            });
        },
    });
});
