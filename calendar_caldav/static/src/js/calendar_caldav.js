/* Copyright 2018 Onestein
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */

odoo.define('calendar_caldav', function(require) {
    var CalendarRenderer = require('web.CalendarRenderer');
    var CalendarController = require('web.CalendarController');
    var core = require('web.core');
    var time = require('web.time');
    var qweb = core.qweb;

    CalendarController.include({
        custom_events: _.extend({}, CalendarController.prototype.custom_events, {
            syncCaldavCalendar: '_syncCaldavCalendar',
        }),

        _syncCaldavCalendar: function () {
            var self = this;

            return this._rpc({
                model: 'calendar.caldav',
                method: 'sync_events',
                args: [
                    this.model.data.context.uid,
                    time.datetime_to_str(this.model.data.start_date.toDate()),
                    time.datetime_to_str(this.model.data.end_date.toDate())
                ]
            }).done(function(result) {
                switch(result.status) {
                    case 'success':
                        self.reload();
                        break;

                    case 'setup':
                        self._openCaldavSetup();
                        break;
                }
            });
        },

        _openCaldavSetup: function () {
            this.trigger_up('do_action', {
                action: 'calendar_caldav.calendar_caldav_setup_wizard_action'
            });
        }
    });

    CalendarRenderer.include({
        events: _.extend({}, CalendarRenderer.prototype.events, {
            'click .caldav_sync_button': '_onSyncCaldavCalendar',
        }),

        _initSidebar: function () {
            this._super.apply(this, arguments);

            if (this.model === "calendar.event") {
                this.$syncButton = $(qweb.render('calendar_caldav.SyncButton'));
                this.$syncButton.appendTo(this.$sidebar);
            }
        },

        _onSyncCaldavCalendar: function () {
            this.trigger_up('syncCaldavCalendar');
        },
    });
});

