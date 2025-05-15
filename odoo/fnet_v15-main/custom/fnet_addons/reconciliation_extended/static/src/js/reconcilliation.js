odoo.define('reconciliation_extended.custom_payment', function (require) {
    "use strict";

    var ShowPaymentLineWidget = require('account.payment').ShowPaymentLineWidget;
    var field_registry = require('web.field_registry');
    var core = require('web.core');
    var session = require('web.session');
    var Dialog = require('web.Dialog');
    var _t = core._t;

    var CustomShowPaymentLineWidget = ShowPaymentLineWidget.extend({

        _onRemoveMoveReconcile: function (event) {
            if (this.recordData.move_type !== 'in_invoice' || this.recordData.expense_bill === true) {
                this._super(event);
                return;
            }

            var self = this;
            var moveId = this.recordData.id;
            var userId = session.uid;
            var partialId = parseInt($(event.target).attr('partial-id'));

            this._rpc({
                model: 'res.users',
                method: 'has_group',
                args: ['reconciliation_extended.group_unreconcile'],
            }).then(function (hasUnreconcileGroup) {
                if (!hasUnreconcileGroup) {
                    self.displayNotification({
                        message: _t("You do not have the necessary permissions to perform this action."),
                        type: 'danger',
                    });
                    return;
                }

                if (partialId !== undefined && !isNaN(partialId)) {
                    var dialog = new Dialog(self, {
                        title: _t("Unreconcile Reason"),
                        size: 'medium',
                        buttons: [
                            {
                                text: _t('Confirm'),
                                classes: 'btn-primary',
                                click: function () {
                                    var reconcillReason = this.$('textarea[name="reconcill_reason"]').val();
                                    if (!reconcillReason) {
                                        self.displayNotification({
                                            message: _t("Please provide a reason for unreconciling."),
                                            type: 'danger',
                                        });
                                        return;
                                    }

                                    self._rpc({
                                        model: 'account.move',
                                        method: 'js_remove_outstanding_partial',
                                        args: [moveId, partialId],
                                    }).then(function () {

                                        var currentDate = new Date().toISOString().slice(0, 19).replace('T', ' ');

                                        console.log('Creating unreconcile.history record with the following data:');
                                        console.log('Date:', currentDate);
                                        console.log('Reconcill Reason:', reconcillReason);
                                        console.log('Account Move ID:', moveId);
                                        console.log('Account User ID:', userId);

                                        self._rpc({
                                            model: 'unreconcile.history',
                                            method: 'create',
                                            args: [{
                                                date: currentDate,
                                                reconcill_reason: reconcillReason,
                                                account_move_id: moveId,
                                                user_id: userId,
                                            }],
                                        }).then(function (result) {
                                            console.log('unreconcile.history record created with ID:', result);
                                            self.trigger_up('reload');
                                        }).catch(function (error) {
                                            console.error('Error creating unreconcile.history record:', error);
                                        });
                                    });
                                    dialog.close();
                                }
                            },
                            { text: _t('Cancel'), close: true }
                        ],
                        $content: $('<div>', { html: `
                            <div class="o_input">
                                <label for="reconcill_reason">${_t("Please provide a reason for unreconciling.")}</label>
                                <textarea name="reconcill_reason" class="form-control"></textarea>
                            </div>
                        ` }),
                    }).open();
                }
            }).catch(function (error) {
                console.error('Error fetching user groups:', error);
            });
        },
    });

    field_registry.add('payment', CustomShowPaymentLineWidget);

    return {
        CustomShowPaymentLineWidget: CustomShowPaymentLineWidget
    };

});