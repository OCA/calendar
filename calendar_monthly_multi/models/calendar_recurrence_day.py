from odoo import fields, models, tools


class CalendarRecurrenceDay(models.Model):
    _name = "calendar.recurrence.day"
    _description = "Recurrence Day"
    _order = "day"

    day = fields.Integer()

    _sql_constraints = [("day_uniq", "unique (day)", "Already exists")]

    def name_get(self):
        res = []
        for record in self:
            res.append((record.id, str(record.day)))
        return res

    @tools.ormcache("day")
    def get_id_from_day(self, day):
        return self.search([("day", "=", day)], limit=1).id

    @tools.ormcache("day_id")
    def get_day_from_id(self, day_id):
        return self.browse(day_id).day
