from odoo import api, fields, models, tools


class CalendarRecurrenceWeekday(models.Model):
    _name = "calendar.recurrence.weekday"
    _description = "Recurrence Weekday"
    _order = "sequence"

    sequence = fields.Integer()
    key = fields.Char(required=True)
    name = fields.Char(required=True)
    weekend_day = fields.Boolean()

    @api.model
    @tools.ormcache("sequence")
    def get_id_by_sequence(self, sequence):
        return self.search([("sequence", "=", sequence)], limit=1).id

    @api.model
    @tools.ormcache()
    def get_ids_of_days(self):
        return self.search([]).ids

    @api.model
    @tools.ormcache()
    def get_ids_of_weekend_days(self):
        return self.search([("weekend_day", "=", True)]).ids

    @api.model
    @tools.ormcache()
    def get_ids_of_weekdays(self):
        return self.search([("weekend_day", "=", False)]).ids
