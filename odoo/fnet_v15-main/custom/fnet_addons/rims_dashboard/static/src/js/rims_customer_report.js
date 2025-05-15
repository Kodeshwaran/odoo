odoo.define('rims_dashboard.custom_page_effect', function (require) {
    var core = require('web.core');
    var Widget = require('web.Widget');

    var CustomPageEffect = Widget.extend({
        js_class: 'bold-page-label',

        start: function () {
            this._super.apply(this, arguments);
            var self = this;
            var $pageLabel = this.$('.o_control_panel .o_cp_left').find('.breadcrumb-item.active');
            if ($pageLabel && $pageLabel.hasClass(self.js_class)) {
                $pageLabel.css('font-weight', 'bold');
            }
        },
    });

    core.action_registry.add('custom_page_effect', CustomPageEffect);

    return {
        CustomPageEffect: CustomPageEffect,
    };
});
