from datetime import datetime, time

from dateutil import rrule

from odoo import Command, _, api, fields, models

from odoo.addons.calendar.models.calendar_recurrence import (
    MAX_RECURRENT_EVENT,
    RRULE_WEEKDAY_TO_FIELD,
    RRULE_WEEKDAYS,
)


class CalendarRecurrence(models.Model):
    _inherit = "calendar.recurrence"

    month_by = fields.Selection(selection_add=[("dates", "Dates of month")])
    weekday = fields.Selection(
        selection_add=[
            ("weekday", "Weekday"),
            ("weekend_day", "Weekend Day"),
            ("day", "Day"),
            ("custom", "Custom"),
        ]
    )
    weekday_ids = fields.Many2many(
        comodel_name="calendar.recurrence.weekday",
        compute="_compute_weekday_ids",
        store=True,
    )
    day_ids = fields.Many2many(comodel_name="calendar.recurrence.day")

    @api.depends("weekday", "rrule_type", "month_by", "rrule")
    def _compute_weekday_ids(self):
        for recurrence in self.filtered(
            lambda r: r.weekday != "custom"
            and r.rrule_type == "monthly"
            and r.month_by == "day"
        ):
            if recurrence.weekday == "day":
                recurrence.weekday_ids = self.env[
                    "calendar.recurrence.weekday"
                ].get_ids_of_days()
            elif recurrence.weekday == "weekday":
                recurrence.weekday_ids = self.env[
                    "calendar.recurrence.weekday"
                ].get_ids_of_weekdays()
            elif recurrence.weekday == "weekend_day":
                recurrence.weekday_ids = self.env[
                    "calendar.recurrence.weekday"
                ].get_ids_of_weekend_days()
            else:
                recurrence.weekday_ids = self.env.ref(
                    "calendar_monthly_multi.%s" % RRULE_WEEKDAYS[recurrence.weekday]
                ).ids

    @api.depends("day_ids", "weekday_ids")
    def _compute_rrule(self):
        return super()._compute_rrule()

    @api.model
    def _rrule_parse(self, rule_str, date_start):
        values = super()._rrule_parse(rule_str, date_start)
        rule = rrule.rrulestr(rule_str, dtstart=date_start)
        if rule._freq != rrule.MONTHLY:
            return values
        if rule._bymonthday and len(rule._bymonthday) > 1:
            values["day_ids"] = [
                Command.set(
                    [
                        self.env["calendar.recurrence.day"].get_id_from_day(d)
                        for d in rule._bymonthday
                    ]
                )
            ]
            values["month_by"] = "dates"
            values["rrule_type"] = "monthly"
        elif rule._byweekday:  # (0, 1, 2, 3, 4)
            weekday_ids = []
            if len(rule._byweekday) == 7:
                weekday = "day"
            elif len(rule._byweekday) == 1:
                weekday = RRULE_WEEKDAY_TO_FIELD[rule._byweekday[0]].upper()
            else:
                weekday_ids = [
                    self.env["calendar.recurrence.weekday"].get_id_by_sequence(d)
                    for d in rule._byweekday
                ]
                weekday_ids_set = set(weekday_ids)
                weekend_days_ids = set(
                    self.env["calendar.recurrence.weekday"].get_ids_of_weekend_days()
                )
                week_days_ids = set(
                    self.env["calendar.recurrence.weekday"].get_ids_of_weekdays()
                )
                if weekday_ids_set == weekend_days_ids:
                    weekday = "weekend_day"
                elif weekday_ids_set == week_days_ids:
                    weekday = "weekday"
                else:
                    weekday = "custom"

            values["weekday_ids"] = weekday_ids
            values["month_by"] = "day"
            values["byday"] = str(rule._bysetpos[0])
            values["weekday"] = weekday
            values["rrule_type"] = "monthly"

        return values

    def _compute_name(self):
        monthly_multi = self.filtered(
            lambda r: r.rrule_type == "monthly"
            and (
                r.month_by == "dates"
                or r.month_by == "day"
                and r.weekday in ("day", "weekday", "weekend_day", "custom")
            )
        )
        for recurrence in monthly_multi:
            if recurrence.month_by == "dates":
                recurrence.name = _(
                    "days %(days)s",
                    days=", ".join(
                        [str(day) for day in recurrence.day_ids.mapped("day")]
                    ),
                )
            else:
                recurrence.name = _(
                    "on the %(byday)s %(weekdays)s",
                    byday=dict(self._fields["byday"].selection)[recurrence.byday],
                    weekdays=", ".join(recurrence.weekday_ids.mapped("name")),
                )
        return super(CalendarRecurrence, self - monthly_multi)._compute_name()

    def _get_rrule(self, dtstart=None):
        self.ensure_one()

        if self.rrule_type == "monthly" and (
            self.month_by == "dates"
            or self.month_by == "day"
            and self.weekday in ("weekday", "weekend_day", "day", "custom")
        ):  # If weekday is just one day than just let the calendar module handle it,
            # we can handle it with weekday_ids but still
            rrule_params = {
                "dtstart": dtstart,
                "interval": self.interval,
            }
            if self.month_by == "dates":
                rrule_params["bymonthday"] = self.day_ids.mapped("day")
            else:
                rrule_params["bysetpos"] = int(self.byday)
                rrule_params["byweekday"] = [
                    getattr(rrule, w.key) for w in self.weekday_ids
                ]
            if self.end_type == "count":
                rrule_params["count"] = min(self.count, MAX_RECURRENT_EVENT)
            elif self.end_type == "forever":
                rrule_params["count"] = MAX_RECURRENT_EVENT
            elif self.end_type == "end_date":
                rrule_params["until"] = datetime.combine(self.until, time.max)
            return rrule.rrule(rrule.MONTHLY, **rrule_params)
        return super()._get_rrule(dtstart)
