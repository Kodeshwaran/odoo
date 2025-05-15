odoo.define('rims_dashboard.dashboard_rims', function (require){
"use strict";

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var QWeb = core.qweb;
    var rpc = require('web.rpc');
    var ajax = require('web.ajax');

    var RimsDashBoard = AbstractAction.extend({
       template: 'DashboardRims',

       events: {
            'click .customer_report': '_onClickCustomerReport',
            'click .email_templates': '_onClickEmailTemplates',
            'click .sop_documents': '_onClickSopDocuments',
            'click .epo_change_request': '_onClickEpoChangeRequest',
            'click .mt_change_request': '_onClickMtChangeRequest',
        },

        _onClickCustomerReport: function (event) {
            event.preventDefault();
            this.do_action({
                name: 'Customer Report',
                type: 'ir.actions.act_window',
                res_model: 'rims.customer.report',
                views: [[false, 'form']],
                target: 'inline',
            });
        },

        _onClickEmailTemplates: function (event) {
            event.preventDefault();
            this.do_action({
                name: 'Email Templates',
                type: 'ir.actions.act_window',
                res_model: 'rims.email.templates',
                views: [[false, 'list'],[false, 'form']],
                target: 'inline',
            });
        },

        _onClickSopDocuments: function (event) {
            event.preventDefault();
            this.do_action({
                name: 'SOP Documents',
                type: 'ir.actions.act_window',
                res_model: 'standard.operating.procedure',
                views: [[false, 'list'],[false, 'form']],
                target: 'inline',
            });
        },

        _onClickEpoChangeRequest: function (event) {
            event.preventDefault();
            this.do_action({
                name: 'EPO Change Request',
                type: 'ir.actions.act_window',
                res_model: 'epo.change.request',
                views: [[false, 'list'],[false, 'form']],
                target: 'current',
            });
        },

        _onClickMtChangeRequest: function (event) {
            event.preventDefault();
            this.do_action({
                name: 'Monitoring Thresholds Change Request',
                type: 'ir.actions.act_window',
                res_model: 'mt.change.request',
                views: [[false, 'list'],[false, 'form']],
                target: 'current',
            });
        },

       init: function(parent, context) {
           this._super(parent, context);
           this.dashboards_templates = ['DashboardRims'];
           this.today_sale = [];
       },
           willStart: function() {
           var self = this;
           return $.when(ajax.loadLibs(this), this._super()).then(function() {
               return self.fetch_data();
           });
       },
       start: function() {
               var self = this;
               this.set("title", 'Dashboard');
               return this._super().then(function() {
                   self.render_dashboards();
               });
           },
           render_dashboards: function(){
           var self = this;
           _.each(this.dashboards_templates, function(template) {
                   self.$('.o_rims_dashboard').append(QWeb.render(template, {widget: self}));
               });
       },
    fetch_data: function() {
           var self = this;
           var def1 =  this._rpc({
                   model: 'rims.links',
                   method: 'search_read',
                   fields: ['name', 'app_icon', 'url'],
                   domain: [['show_in_dashboard', '=', 'true']],
       }).then(function(result)
        {
        self.links = result,
        self.links_count = result.length
//        console.log(self.links)
//        for (var link in self.links) {
//            console.log(link)
//        }
       });
           return $.when(def1);
       },
    })
    core.action_registry.add('dashboard_rims_tag', RimsDashBoard);

    return RimsDashBoard;
})