odoo.define('web_calendar_view_custom_colors.calendar_colour', function (require) {
    "use strict";

    var CalendarView = require('web.CalendarView');
    var CalendarModel = require('web.CalendarModel');
    var CalendarRenderer = require('web.CalendarRenderer');
    var CalendarController = require('web.CalendarController');
    var viewRegistry = require('web.view_registry');
    var rpc = require('web.rpc');

    var CalendarColourRenderer = CalendarRenderer.extend({
        _renderEvents: function () {
                this.$calendar.fullCalendar('removeEvents');
                this.$calendar.fullCalendar('addEventSource', this.state.data);
        },
    });

    var CalendarColourModel = CalendarModel.extend({
        _loadColors: function (element, events) {
            var self= this;
            var color_fields = rpc.query({
                model: 'calendar.view.config',
                method: 'get_calendar_tag_values',
                args: [self.modelName],
            });
            return color_fields.then(function(calendar_colors){
                if (self.fieldColor) {
                    var fieldName = self.fieldColor;
                    _.each(events, function (event) {
                        var value = event.record[fieldName];
                        if (calendar_colors.length > 0){
                            _.each(calendar_colors, function (calendar) {
                                if (calendar['id'] === event.id){
                                    if (calendar['color'] !== false){
                                        event.color = calendar['color'];
                                        event.color_index = calendar['color'];
                                    }else{
                                         event.color_index = _.isArray(value) ? value[0] : value;
                                    }
                                    if (calendar['font_color'] !== false){
                                        if (calendar['font_color'] === 'black'){
                                            event.textColor = 'black';
                                        }else{
                                            event.textColor = 'white';
                                        }
                                    }
                                    if (calendar['hatched'] === true){
                                        event.className = 'calendar_hatched_background';
                                    }
                                }
                            });
                        }else{
                            event.color_index = _.isArray(value) ? value[0] : value;
                        }
                    });
                    self.model_color = self.fields[fieldName].relation || element.model;
                }
                return $.Deferred().resolve();
            });
        },
    });

    var WebCalendarColourView = CalendarView.extend({
        config: _.extend({}, CalendarView.prototype.config, {
                Model: CalendarColourModel,
                Renderer: CalendarColourRenderer,
                Controller: CalendarController,
        }),
    });

    viewRegistry.add('calendar_colour', WebCalendarColourView);

});
