odoo.define('rims_dashboard.rims_user_dashboard', function (require) {
"use strict";

    var core = require('web.core');
    var registry = require('web.ActionRegistry');
    const actionRegistry = registry.category("actions");
    var session = require('web.session');
    var ajax = require('web.ajax');
    var ActionManager = require('web.ActionManager');
    var view_registry = require('web.view_registry');
    var Widget = require('web.Widget');
    var AbstractAction = require('web.AbstractAction');
    var ControlPanelMixin = require('web.ControlPanelMixin');

    var QWeb = core.qweb;

    var _t = core._t;
    var _lt = core._lt;

    var RimsDashboardView = Widget.extend(ControlPanelMixin, {
    	template: 'rims_dashboard.rims_user_dashboard',
        events: _.extend({}, Widget.prototype.events, {
            'click .total-links': 'total_links',
        }),
        init: function(parent, context) {
            this._super(parent, context);
            var links_data = [];
            var self = this;
            if (context.tag == 'rims_dashboard.rims_user_dashboard') {
                self._rpc({
                    model: 'rims.dashboard',
                    method: 'get_links_details',
                }, []).then(function(result){
                    self.links_data = result[0]
                    var action_client = {
                        type: "ir.actions.client",
                        name: _t('Dashboard '),
                        tag: 'hr_dashboard',
                    };
                }).done(function(){
                    if(self.links_data) {
                        self.render();
                        self.href = window.location.href;
                            }else {
                         alert("Please configure url correctly")
                    }
                });
            }
        },
        willStart: function() {
             return $.when(ajax.loadLibs(this), this._super());
        },
        start: function() {
            var self = this;
            return this._super();
        },
        render: function() {
            var super_render = this._super;
            var self = this;
            var rims_dashboard = QWeb.render( 'rims_dashboard.rims_user_dashboard', {
                widget: self,
            });
            $( ".o_control_panel" ).addClass( "o_hidden" );
            $(rims_dashboard).prependTo(self.$el);
//            self.graph();
            return rims_dashboard
        },
        reload: function () {
                window.location.href = this.href;
        },
        total_links: function(event) {
            var self = this;
            event.stopPropagation();
            event.preventDefault();
            return this.do_action({
                name: _t("Apps"),
                type: 'ir.actions.act_url',
                res_model: 'rims.links',
                view_mode: 'kanban,tree,form',
                view_type: 'form',
                views: [[false, 'list'],[false, 'form']],
                context: {},
                domain: [],
                target: 'current'
            },{on_reverse_breadcrumb: function(){ return self.reload();}})
        },
         getRandomColor: function () {
            var letters = '0123456789ABCDEF'.split('');
            var color = '#';
            for (var i = 0; i < 6; i++ ) {
                color += letters[Math.floor(Math.random() * 16)];
            }
            return color;
        },
    //    graph: function() {
    //        var self = this;
    ////        HoursChar
    //        var ctx = this.$el.find('#HoursChart')
    //        bg_color_list = []
    //        for (var i=0;i<=self.project_data.attendance_dataset.length;i++){
    //            bg_color_list.push(self.getRandomColor())
    //        }
    //        Chart.plugins.register({
    //          beforeDraw: function(chartInstance) {
    //            var ctx = chartInstance.chart.ctx;
    //            ctx.fillStyle = "white";
    //            ctx.fillRect(0, 0, chartInstance.chart.width, chartInstance.chart.height);
    //          }
    //        });
    //        var bg_color_list = []
    //        for (var i=0;i<=12;i++){
    //            bg_color_list.push(self.getRandomColor())
    //        }
    //        var myChart = new Chart(ctx, {
    //            type: 'bar',
    //            data: {
    //                //labels: ["January","February", "March", "April", "May", "June", "July", "August", "September",
    //                // "October", "November", "December"],
    //                labels: self.project_data.attendance_label,
    //                datasets: [{
    //                    label: 'Worked Hours',
    //                    data: self.project_data.attendance_dataset,
    //                    backgroundColor: bg_color_list,
    //                    borderColor: bg_color_list,
    //                    borderWidth: 1,
    //                    pointBorderColor: 'white',
    //                    pointBackgroundColor: 'red',
    //
    //                }]
    //            },
    //            options: {
    //
    //                scales: {
    //                    xAxes: [{
    //                        ticks: {
    //                        autoSkip:false,
    //                        }
    //                    }],
    //                    yAxes: [{
    //                        ticks: {
    //                            min: 0,
    //                            max: Math.max.apply(null,self.project_data.attendance_dataset),
    //                            //min: 1000,
    //                            //max: 100000,
    //                            stepSize: self.project_data.attendance_dataset.reduce((pv,cv)=>{return pv + (parseFloat(cv)||0)},0)/self.project_data.attendance_dataset.length
    //                          }
    //                    }]
    //                },
    //                responsive: true,
    //                maintainAspectRatio: true,
    //                animation: {
    //                    duration: 100, // general animation time
    //                },
    //                hover: {
    //                    animationDuration: 500, // duration of animations when hovering an item
    //                },
    //                responsiveAnimationDuration: 500, // animation duration after a resize
    //                legend: {
    //                    display: true,
    //                    labels: {
    //                        fontColor: 'black'
    //                    }
    //                },
    //            },
    //        });
    ////        Task Chart
    //        var task = this.$el.find('#TaskChart')
    //        bg_color_list = []
    //        for (var i=0;i<=self.project_data.attendance_dataset.length;i++){
    //            bg_color_list.push(self.getRandomColor())
    //        }
    //        var taskChart = new Chart(task, {
    //            type: 'doughnut',
    //            data: {
    //                //labels: ["January","February", "March", "April", "May", "June", "July", "August", "September",
    //                // "October", "November", "December"],
    //                labels: self.project_data.task_label,
    //                datasets: [{
    //                    label: 'Worked Hours',
    //                    data: self.project_data.task_dataset,
    //                    backgroundColor: bg_color_list,
    //                    borderColor: bg_color_list,
    //                    borderWidth: 1,
    //                    pointBorderColor: 'white',
    //                    pointBackgroundColor: 'red',
    //                }]
    //            },
    //            options: {
    //                cutoutPercentage:50,
    //                responsive: true,
    //                maintainAspectRatio: true,
    //                animation: {
    //                    duration: 100, // general animation time
    //                },
    //                hover: {
    //                    animationDuration: 500, // duration of animations when hovering an item
    //                },
    //                responsiveAnimationDuration: 500, // animation duration after a resize
    //                legend: {
    //                    display: true,
    //                    labels: {
    //                        fontColor: 'black'
    //                    }
    //                },
    //            },
    //        });
    //    },

    });
    core.action_registry.add('rims_user_dashboard', RimsDashboardView);

    return RimsDashboardView;
})
