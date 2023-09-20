from odoo import api, fields, models


class CalendarEvent(models.Model):
    _inherit = "calendar.event"

    month_by = fields.Selection(selection_add=[("dates", "Dates of month")])
    weekday = fields.Selection(
        selection_add=[
            ("weekday", "Weekday"),
            ("weekend_day", "Weekend Day"),
            ("day", "Day"),
            ("custom", "Custom"),
        ]
    )
    day_ids = fields.Many2many(
        comodel_name="calendar.recurrence.day",
        compute="_compute_recurrence",
        readonly=False,
    )
    weekday_ids = fields.Many2many(
        comodel_name="calendar.recurrence.weekday",
        compute="_compute_recurrence",
        readonly=False,
    )

    @api.model
    def _get_recurrent_fields(self):
        fields = super()._get_recurrent_fields()
        fields.add("day_ids")
        fields.add("weekday_ids")
        return fields

    def _get_recurrence_params(self):
        params = super()._get_recurrence_params()
        event_date = self._get_start_date()
        params.update(
            day_ids=[
                self.env["calendar.recurrence.day"].get_id_from_day(event_date.day)
            ],
            weekday_ids=[
                self.env["calendar.recurrence.weekday"].get_id_by_sequence(
                    event_date.weekday()
                )
            ],
        )
        return params
