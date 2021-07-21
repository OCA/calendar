# Copyright 2021 Tecnativa - Jairo Llopis
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta
from math import ceil
from random import random

from odoo import _, api, fields, models


class ResourceBookingType(models.Model):
    _name = "resource.booking.type"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Resource Booking Type"
    _sql_constraints = [
        ("duration_positive", "CHECK(duration > 0)", "Duration must be positive."),
    ]

    active = fields.Boolean(index=True, default=True)
    alarm_ids = fields.Many2many(
        string="Default reminders",
        comodel_name="calendar.alarm",
        help="Meetings will be created with these reminders by default.",
    )
    booking_count = fields.Integer(compute="_compute_booking_count")
    categ_ids = fields.Many2many(
        string="Default tags",
        comodel_name="calendar.event.type",
        help="Meetings will be created with these tags by default.",
    )
    combination_assignment = fields.Selection(
        [
            ("sorted", "Sorted: pick the first one that is free"),
            ("random", "Randomly: order is not important"),
        ],
        required=True,
        default="random",
        help=(
            "Choose how to auto-assign resource combinations. "
            "It has no effect if assiged manually."
        ),
    )
    combination_rel_ids = fields.One2many(
        comodel_name="resource.booking.type.combination.rel",
        inverse_name="type_id",
        string="Available resource combinations",
        help="Resource combinations available for this type of bookings.",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        default=lambda self: self._default_company(),
        index=True,
        readonly=False,
        store=True,
        string="Company",
        help="Company where this booking type is available.",
    )
    duration = fields.Float(
        required=True,
        default=0.5,  # 30 minutes
        help="Establish each interval's duration.",
    )
    location = fields.Char()
    modifications_deadline = fields.Float(
        required=True,
        default=24,
        help=(
            "When this deadline has been exceeded, if a booking was not yet "
            "confirmed, it will be canceled automatically. Also, only booking "
            "managers will be able to unschedule or reschedule them. "
            "The value is expressed in hours."
        ),
    )
    name = fields.Char(index=True, translate=True, required=True)
    booking_ids = fields.One2many(
        "resource.booking",
        "type_id",
        string="Bookings",
        help="Bookings available for this type",
    )
    resource_calendar_id = fields.Many2one(
        comodel_name="resource.calendar",
        default=lambda self: self._default_resource_calendar(),
        index=True,
        required=True,
        ondelete="restrict",
        string="Availability Calendar",
        help="Restrict bookings to this schedule.",
    )
    requester_advice = fields.Text(
        translate=True,
        help=(
            "Text that will appear by default in portal invitation emails "
            "and in calendar views for scheduling."
        ),
    )

    @api.model
    def _default_company(self):
        return self.env.company

    @api.model
    def _default_resource_calendar(self):
        return self._default_company().resource_calendar_id

    @api.depends("booking_ids")
    def _compute_booking_count(self):
        for one in self:
            one.booking_count = len(one.booking_ids)

    @api.constrains("booking_ids", "resource_calendar_id", "combination_rel_ids")
    def _check_bookings_scheduling(self):
        """Scheduled bookings must have no conflicts."""
        bookings = self.mapped("booking_ids")
        return bookings._check_scheduling()

    def _event_defaults(self, prefix=""):
        """Get field names that should fill default values in meetings."""
        return {
            prefix + "alarm_ids": [(6, 0, self.alarm_ids.ids)],
            prefix + "description": self.requester_advice,
            prefix + "duration": self.duration,
            prefix + "location": self.location,
        }

    def _get_combinations_priorized(self):
        """Gets all combinations sorted by the chosen assignment method."""
        if not self.combination_assignment:
            return self.combination_rel_ids.mapped("combination_id")
        keys = {"sorted": "sequence", "random": lambda *a: random()}
        rels = self.combination_rel_ids.sorted(keys[self.combination_assignment])
        combinations = rels.mapped("combination_id")
        return combinations

    def _get_next_slot_start(self, start_dt):
        """Slot start as it would come from the beginning of work hours.

        Returns a `datetime` object indicating the next slot start (which could
        be the same as `start_dt` if it matches), or `False` if no slot is
        found in the next 2 weeks.

        If the RBT doesn't have a calendar, it returns `start_dt`, unaltered,
        because there's no way to know when a slot would start.
        """
        duration_delta = timedelta(hours=self.duration)
        end_dt = start_dt + duration_delta
        workday_min = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        attendance_intervals = self.resource_calendar_id._attendance_intervals(
            workday_min, end_dt
        )
        try:
            workday_start, valid_end, _meta = attendance_intervals._items[-1]
            if valid_end != end_dt:
                # Inteval found, but without enough time; same as no interval
                raise IndexError
        except IndexError:
            try:
                # Returns `False` if no slot is found in the next 2 weeks
                return (
                    self.resource_calendar_id.plan_hours(
                        self.duration, end_dt, compute_leaves=True
                    )
                    - duration_delta
                )
            except TypeError:
                return False
        time_passed = valid_end - duration_delta - workday_start
        return workday_start + duration_delta * ceil(time_passed / duration_delta)

    def action_open_bookings(self):
        FloatTimeParser = self.env["ir.qweb.field.float_time"]
        return {
            "context": dict(
                self.env.context,
                # Context used by web_calendar_slot_duration module
                calendar_slot_duration=FloatTimeParser.value_to_html(
                    self.duration, False
                ),
                default_type_id=self.id,
                **self._event_defaults(prefix="default_"),
            ),
            "domain": [("type_id", "=", self.id)],
            "name": _("Bookings"),
            "res_model": "resource.booking",
            "type": "ir.actions.act_window",
            "view_mode": "calendar,tree,form",
        }
