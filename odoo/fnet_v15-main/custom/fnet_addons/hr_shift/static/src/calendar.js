odoo.define('hr_shift.custom_calendar', function (require) {
    "use strict";

    var CalendarView = require('web_calendar.CalendarView');

    var CustomCalendarView = CalendarView.extend({
        init: function (parent, dataset, view_id, options) {
            this._super.apply(this, arguments);
        },

        _get_fc_event_options: function (record) {
            var options = this._super.apply(this, arguments);

            // Add the color to the event options based on the record's color field
            if (record.color) {
                options.color = record.color;
            }

            return options;
        },

        start: function () {
            this._super.apply(this, arguments);
        },

    });
    return {
        CustomCalendarView: CustomCalendarView,
    };

});

//odoo.define('custom_calendar_color', function (require) {
//    "use strict";
//
//    var CalendarModel = require('web_calendar.CalendarModel');
//    var CalendarRenderer = require('web_calendar.CalendarRenderer');
//    var CustomCalendarView = require('custom_calendar.CustomCalendarView');
//
//    CalendarModel.include({
//
//        _fetch_records: function (params) {
//            var self = this;
//            return this._super.apply(this, arguments).then(function (result) {
//                // Set the color field on each record based on its state
//                result.forEach(function (record) {
//                    if (record.state === 'draft') {
//                        record.color = '#FFA07A';  // Light salmon
//                    } else if (record.state === 'confirmed') {
//                        record.color = '#00FF00';  // Lime
//                    } else if (record.state === 'done') {
//                        record.color = '#87CEFA';  // Light sky blue
//                    }
//                });
//                return result;
//            });
//        },
//
//    });
//
//    CalendarRenderer.include({
//
//        init_calendar: function () {
//            this._super.apply(this, arguments);
//            // Set the custom calendar view as the default view for the calendar
//            this.view_registry.add('custom_calendar', CustomCalendarView);
//        },
//
//    });
//
//});