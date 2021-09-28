# Copyright 2021 Tecnativa - Jairo Llopis
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import calendar
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.resource.models.resource import Intervals


class ResourceBooking(models.Model):
    _name = "resource.booking"
    _inherit = ["mail.thread", "mail.activity.mixin", "portal.mixin"]
    _description = "Resource Booking"
    _order = "start DESC"
    _sql_constraints = [
        (
            "combination_required_if_event",
            "CHECK(meeting_id IS NULL OR combination_id IS NOT NULL)",
            "Missing resource booking combination.",
        ),
        (
            "unique_meeting_id",
            "UNIQUE(meeting_id)",
            "Only one event per resource booking can exist.",
        ),
    ]

    active = fields.Boolean(default=True)
    meeting_id = fields.Many2one(
        comodel_name="calendar.event",
        string="Meeting",
        context={"default_res_id": False, "default_res_model": False},
        copy=False,
        index=True,
        ondelete="set null",
        help="Meeting confirmed for this booking.",
    )
    categ_ids = fields.Many2many(
        string="Tags",
        comodel_name="calendar.event.type",
        compute="_compute_categ_ids",
        store=True,
        readonly=False,
    )
    combination_id = fields.Many2one(
        comodel_name="resource.booking.combination",
        string="Resources combination",
        compute="_compute_combination_id",
        copy=False,
        domain="[('type_rel_ids.type_id', 'in', [type_id])]",
        index=True,
        readonly=False,
        states={"scheduled": [("required", True)], "confirmed": [("required", True)]},
        store=True,
        tracking=True,
    )
    combination_auto_assign = fields.Boolean(
        string="Auto assigned",
        default=True,
        help=(
            "When checked, resource combinations will be (un)assigned automatically "
            "based on their availability during the booking dates."
        ),
    )
    name = fields.Char(index=True, help="Leave empty to autogenerate a booking name.")
    partner_id = fields.Many2one(
        "res.partner",
        string="Requester",
        index=True,
        ondelete="cascade",
        required=True,
        tracking=True,
        help="Who requested this booking?",
    )
    user_id = fields.Many2one(
        "res.users",
        default=lambda self: self._default_user_id(),
        store=True,
        readonly=False,
        compute="_compute_user_id",
        string="Organizer",
        index=True,
        tracking=True,
        help=(
            "Who organized this booking? Usually whoever created the record. "
            "It will appear as the calendar event organizer, when scheduled, "
            "and calendar notifications will be sent in his/her name."
        ),
    )
    location = fields.Char(compute="_compute_location", readonly=False, store=True,)
    requester_advice = fields.Text(related="type_id.requester_advice", readonly=True)
    is_modifiable = fields.Boolean(compute="_compute_is_modifiable")
    is_overdue = fields.Boolean(compute="_compute_is_overdue")
    state = fields.Selection(
        [
            ("pending", "Pending"),
            ("scheduled", "Scheduled"),
            ("confirmed", "Confirmed"),
            ("canceled", "Canceled"),
        ],
        compute="_compute_state",
        store=True,
        default="pending",
        index=True,
        tracking=True,
        help=(
            "Pending: No meeting scheduled.\n"
            "Scheduled: The requester has not confirmed attendance yet.\n"
            "Confirmed: Meeting scheduled, and requester attendance confirmed.\n"
            "Canceled: Meeting removed, booking archived."
        ),
    )
    start = fields.Datetime(
        compute="_compute_start",
        copy=False,
        index=True,
        readonly=False,
        store=True,
        track_sequence=200,
        tracking=True,
    )
    duration = fields.Float(
        compute="_compute_duration",
        readonly=False,
        store=True,
        track_sequence=220,
        tracking=True,
        help="Amount of time that the resources will be booked and unavailable for others.",
    )
    stop = fields.Datetime(
        compute="_compute_stop",
        copy=False,
        index=True,
        store=True,
        track_sequence=210,
        tracking=True,
    )
    type_id = fields.Many2one(
        comodel_name="resource.booking.type",
        string="Type",
        index=True,
        ondelete="cascade",
        required=True,
        tracking=True,
    )

    @api.model
    def _default_user_id(self):
        return self.env.user

    def _compute_access_url(self):
        result = super()._compute_access_url()
        for one in self:
            one.access_url = "/my/bookings/%d" % one.id
        return result

    @api.depends("type_id")
    def _compute_categ_ids(self):
        """Copy default tags from RBT when changing it."""
        for one in self:
            if one.type_id:
                one.categ_ids = one.type_id.categ_ids

    @api.depends("start", "type_id", "combination_auto_assign")
    def _compute_combination_id(self):
        """Select best combination candidate when changing booking dates."""
        for one in self:
            # Useless without the interval
            if one.start and one.combination_auto_assign:
                one.combination_id = one._get_best_combination()

    @api.depends("start")
    def _compute_is_overdue(self):
        """Indicate if booking is overdue."""
        now = fields.Datetime.now()
        for one in self:
            # You can always modify it if there's no meeting yet
            if not one.start:
                one.is_overdue = False
                continue
            anticipation = timedelta(hours=one.type_id.modifications_deadline)
            deadline = one.start - anticipation
            one.is_overdue = now > deadline

    @api.depends("is_overdue")
    @api.depends_context("uid", "using_portal")
    def _compute_is_modifiable(self):
        """Indicate if the booking is modifiable."""
        self.is_modifiable = True
        is_manager = not self.env.context.get(
            "using_portal"
        ) and self.env.user.has_group("resource_booking.group_manager")
        # Managers can always modify overdue bookings
        if not is_manager:
            overdue = self.filtered("is_overdue")
            overdue.is_modifiable = False

    @api.depends("name", "partner_id", "type_id", "meeting_id")
    @api.depends_context("uid", "using_portal")
    def _compute_display_name(self):
        """Overridden just for dependencies; see `name_get()` for implementation."""
        return super()._compute_display_name()

    @api.depends("meeting_id.location", "type_id")
    def _compute_location(self):
        """Get location from meeting or type."""
        for record in self:
            # Get location from type when changing it or creating from ORM
            # HACK https://github.com/odoo/odoo/issues/74152
            if not record.location or record._origin.type_id != record.type_id:
                record.location = record.type_id.location
            # Get it from meeting only when available
            elif record.meeting_id:
                record.location = record.meeting_id.location

    @api.depends("active", "meeting_id.attendee_ids.state")
    def _compute_state(self):
        """Obtain request state."""
        to_check = self.browse()
        for one in self:
            if not one.active:
                one.state = "canceled"
                continue
            confirmed = False
            for attendee in one.meeting_id.attendee_ids:
                if attendee.partner_id == one.partner_id:
                    confirmed = attendee.state == "accepted"
                    break
            if confirmed:
                one.state = "confirmed"
                to_check |= one
                continue
            one.state = "scheduled" if one.meeting_id else "pending"
        to_check._check_scheduling()

    @api.depends("meeting_id.start")
    def _compute_start(self):
        """Get start date from related meeting, if available."""
        for record in self:
            if record.id:
                record.start = record.meeting_id.start

    @api.depends("meeting_id.duration", "type_id")
    def _compute_duration(self):
        """Compute duration for each booking."""
        for record in self:
            # Special case when creating record from UI
            if not record.id:
                record.duration = self.default_get(["duration"]).get(
                    "duration", record.type_id.duration
                )
            # Get duration from type only when changing type or when creating from ORM
            elif not record.duration or record._origin.type_id != record.type_id:
                record.duration = record.type_id.duration
            # Get it from meeting only when available
            elif record.meeting_id:
                record.duration = record.meeting_id.duration

    @api.depends("start", "duration")
    def _compute_stop(self):
        """Get stop date from start date and duration."""
        for record in self:
            try:
                record.stop = record.start + timedelta(hours=record.duration)
            except TypeError:
                # Either value is False: no stop date
                record.stop = False

    @api.depends("meeting_id.user_id")
    def _compute_user_id(self):
        """Get user from related meeting, if available."""
        for record in self:
            if record.meeting_id.user_id:
                record.user_id = record.meeting_id.user_id

    def _sync_meeting(self):
        """Lazy-create or destroy calendar.event."""
        # Notify changed dates to attendees
        _self = self.with_context(syncing_booking_ids=self.ids)
        # Avoid sync recursion
        _self -= self.browse(self.env.context.get("syncing_booking_ids"))
        to_create, to_delete = [], _self.env["calendar.event"]
        for one in _self:
            if one.start:
                resource_partners = one.combination_id.resource_ids.filtered(
                    lambda res: res.resource_type == "user"
                ).mapped("user_id.partner_id")
                meeting_vals = dict(
                    alarm_ids=[(6, 0, one.type_id.alarm_ids.ids)],
                    categ_ids=[(6, 0, one.categ_ids.ids)],
                    description=one.type_id.requester_advice,
                    duration=one.duration,
                    location=one.location,
                    name=one.name
                    or one._get_name_formatted(one.partner_id, one.type_id),
                    partner_ids=[
                        (4, partner.id, 0)
                        for partner in one.partner_id | resource_partners
                    ],
                    resource_booking_ids=[(6, 0, one.ids)],
                    start=one.start,
                    stop=one.stop,
                    user_id=one.user_id.id,
                    # These 2 avoid creating event as activity
                    res_model_id=False,
                    res_id=False,
                )
                if one.meeting_id:
                    meeting = one.meeting_id
                    if not all(
                        (
                            one.meeting_id.start == one.start,
                            one.meeting_id.stop == one.stop,
                            one.meeting_id.duration == one.duration,
                        )
                    ):
                        # Context to notify scheduling change
                        meeting = meeting.with_context(from_ui=True)
                    meeting.write(meeting_vals)
                else:
                    to_create.append(meeting_vals)
            else:
                to_delete |= one.meeting_id
        to_delete.unlink()
        _self.env["calendar.event"].create(to_create)

    @api.constrains("combination_id", "meeting_id", "type_id")
    def _check_scheduling(self):
        """Scheduled bookings must have no conflicts."""
        # Nothing to do if no bookings are scheduled
        has_meeting = self.filtered("meeting_id")
        if not has_meeting:
            return
        # Ensure all scheduled bookings have booked some resources
        has_rbc = self.filtered("combination_id.resource_ids")
        missing_rbc = has_meeting - has_rbc
        if missing_rbc:
            raise ValidationError(
                _(
                    "Cannot schedule these bookings because no resources "
                    "are selected for them:\n\n- %s"
                )
                % ("\n- ".join(missing_rbc.mapped("display_name")))
            )
        # Ensure all bookings fit in their type and resources calendars
        unfitting_bookings = has_meeting
        now = fields.Datetime.now()
        for booking in has_meeting:
            # Ignore if the event already happened
            already_happened = booking.stop and booking.stop < now
            if already_happened:
                unfitting_bookings -= booking
                continue
            meeting_dates = tuple(
                fields.Datetime.context_timestamp(self, booking[field])
                for field in ("start", "stop")
            )
            available_intervals = booking._get_intervals(*meeting_dates)
            if (
                len(available_intervals) == 1
                and available_intervals._items[0][:2] == meeting_dates
            ):
                unfitting_bookings -= booking
        # Explain which bookings failed validation
        if unfitting_bookings:
            raise ValidationError(
                _(
                    "Cannot schedule these bookings because they do not fit "
                    "in their type or resources calendars, or because "
                    "all resources are busy:\n\n- %s"
                )
                % "\n- ".join(unfitting_bookings.mapped("display_name"))
            )

    def _get_calendar_context(self, year=None, month=None, now=None):
        """Get the required context for the calendar view in the portal.

        See the `resource_booking.scheduling_calendar` view.

        :param int year: Year of the calendar to be displayed.
        :param int month: Month of the calendar to be displayed.
        :param datetime now: Represents the current datetime.
        """
        month1 = relativedelta(months=1)
        now = now or fields.Datetime.now()
        year = year or now.year
        month = month or now.month
        start = datetime(year, month, 1)
        start, now = (
            fields.Datetime.context_timestamp(self, dt) for dt in (start, now)
        )
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        lang = self.env["res.lang"]._lang_get(self.env.lang or self.env.user.lang)
        weekday_names = dict(lang.fields_get(["week_start"])["week_start"]["selection"])
        slots = self._get_available_slots(start, start + month1)
        return {
            "booking": self,
            "calendar": calendar.Calendar(int(lang.week_start) - 1),
            "now": now,
            "res_lang": lang,
            "slots": slots,
            "start": start,
            "weekday_names": weekday_names,
        }

    @api.model
    def _get_name_formatted(self, partner, type_, meeting=None):
        """Produce a beautifully formatted name."""
        values = {"partner": partner.display_name, "type": type_.display_name}
        if meeting:
            values["time"] = meeting.display_time
            return _("%(partner)s - %(type)s - %(time)s") % values
        return _("%(partner)s - %(type)s") % values

    def _get_best_combination(self):
        """Pick best combination based on current booking state."""
        # No dates? Then return whatever is already selected (can be empty)
        if not self.start:
            return self.combination_id
        # If there's a combination already, put it 1st (highest priority)
        sorted_combinations = self.combination_id + (
            self.type_id._get_combinations_priorized() - self.combination_id
        )
        desired_interval = tuple(
            fields.Datetime.context_timestamp(self, dt)
            for dt in (self.start, self.stop)
        )
        # Get 1st combination available in the desired interval
        for combination in sorted_combinations:
            availability = self._get_intervals(*desired_interval, combination)
            if (
                len(availability) == 1
                and availability._items[0][:2] == desired_interval
            ):
                return combination
        # Tell portal user there's no combination available
        if self.env.context.get("using_portal"):
            hours = (self.stop - self.start).total_seconds() / 3600
            raise ValidationError(
                _("No resource combinations available on %s")
                % self.env["calendar.event"]._get_display_time(
                    self.start, self.stop, hours, False
                )
            )

    def _get_available_slots(self, start_dt, end_dt):
        """Return available slots for scheduling current booking."""
        result = {}
        now = fields.Datetime.context_timestamp(self, fields.Datetime.now())
        slot_duration = timedelta(hours=self.type_id.duration)
        booking_duration = timedelta(hours=self.duration)
        current = max(
            start_dt, now + timedelta(hours=self.type_id.modifications_deadline)
        )
        available_intervals = self._get_intervals(current, end_dt)
        while current and current < end_dt:
            slot_start = self.type_id._get_next_slot_start(current)
            if current != slot_start:
                current = slot_start
                continue
            current_interval = Intervals([(current, current + booking_duration, self)])
            for start, end, _meta in available_intervals & current_interval:
                if end - start == booking_duration:
                    result.setdefault(current.date(), [])
                    result[current.date()].append(current)
                # I actually only care about the 1st interval, if any
                break
            current += slot_duration
        return result

    def _get_intervals(self, start_dt, end_dt, combination=None):
        """Get available intervals for this booking."""
        # Get all intervals except those from current booking
        try:
            booking_id = self.id or self._origin.id or -1
        except AttributeError:
            booking_id = -1
        # Detached compatibility with hr_holidays_public
        booking = self.with_context(
            analyzing_booking=booking_id, exclude_public_holidays=True
        )
        # RBT calendar uses no resources to restrict bookings
        result = booking.type_id.resource_calendar_id._work_intervals(start_dt, end_dt)
        # Restrict with the chosen combination, or to at least one of the
        # available ones
        combinations = (
            combination
            or booking.combination_id
            or booking.mapped("type_id.combination_rel_ids.combination_id")
        ).with_context(analyzing_booking=booking_id)
        result &= combinations._get_intervals(start_dt, end_dt)
        return result

    @api.model_create_multi
    def create(self, vals_list):
        """Sync booking with meeting if needed."""
        result = super().create(vals_list)
        result._sync_meeting()
        return result

    def write(self, vals):
        """Sync booking with meeting if needed."""
        result = super().write(vals)
        self._sync_meeting()
        return result

    def unlink(self):
        """Unlink meeting if needed."""
        self.meeting_id.unlink()
        return super().unlink()

    def name_get(self):
        """Autogenerate booking name if none is provided."""
        old = super().name_get()
        new = []
        for id_, name in old:
            record = self.browse(id_)
            if self.env.context.get("using_portal"):
                # ID optionally suffixed with custom name for portal users
                template = _("# %(id)d - %(name)s") if record.name else _("# %(id)d")
                name = template % {"id": id_, "name": name}
            elif not record.name:
                # Automatic name for backend users
                name = self._get_name_formatted(
                    record.partner_id, record.type_id, record.meeting_id
                )
            new.append((id_, name))
        return new

    def _message_auto_subscribe_followers(self, updated_values, default_subtype_ids):
        """Auto-subscribe and notify resource partners."""
        result = super()._message_auto_subscribe_followers(
            updated_values, default_subtype_ids
        )
        combination = (
            self.env["resource.booking.combination"]
            .sudo()
            .browse(updated_values.get("combination_id"))
        )
        resource_partners = combination.mapped(
            "resource_ids.user_id.partner_id"
        ).filtered("active")
        for partner in resource_partners:
            result.append(
                (
                    partner.id,
                    default_subtype_ids,
                    "resource_booking.message_combination_assigned"
                    if partner != self.env.user.partner_id
                    else False,
                )
            )
        return result

    def _message_get_suggested_recipients(self):
        """Suggest related partners."""
        recipients = super()._message_get_suggested_recipients()
        for record in self:
            record._message_add_suggested_recipient(
                recipients,
                partner=record.partner_id,
                reason=self._fields["partner_id"].string,
            )
        return recipients

    def action_schedule(self):
        """Redirect user to a simpler way to schedule this booking."""
        FloatTimeParser = self.env["ir.qweb.field.float_time"]
        return {
            "context": dict(
                self.env.context,
                # These 2 avoid creating event as activity
                default_res_model_id=False,
                default_res_id=False,
                # Context used by web_calendar_slot_duration module
                calendar_slot_duration=FloatTimeParser.value_to_html(
                    self.duration, False
                ),
                default_resource_booking_ids=[(6, 0, self.ids)],
                default_name=self.name,
            ),
            "name": _("Schedule booking"),
            "res_model": "calendar.event",
            "target": "self",
            "type": "ir.actions.act_window",
            "view_mode": "calendar,tree,form",
        }

    def action_confirm(self):
        """Confirm own and requesting partner's attendance."""
        attendees_to_confirm = self.env["calendar.attendee"]
        confirm_always = self.env["res.partner"]
        if self.env.context.get("confirm_own_attendance"):
            confirm_always |= self.env.user.partner_id
        # Avoid wasted state recomputes
        with self.env.norecompute():
            for booking in self:
                if not booking.meeting_id:
                    continue
                # Make sure requester and user resources are meeting attendees
                booking.meeting_id.partner_ids |= booking.partner_id | booking.mapped(
                    "combination_id.resource_ids.user_id.partner_id"
                )
                # Find meeting attendees that should be confirmed
                partners_to_confirm = confirm_always | booking.partner_id
                for attendee in booking.meeting_id.attendee_ids:
                    if attendee.partner_id & partners_to_confirm:
                        # attendee.state='accepted'
                        attendees_to_confirm |= attendee
            attendees_to_confirm.write({"state": "accepted"})
        self.recompute()

    def action_unschedule(self):
        """Remove associated meetings."""
        self.mapped("meeting_id").unlink()
        # Force recomputing, in case meeting_id is not visible in the form
        self.write({"meeting_id": False})

    def action_cancel(self):
        """Cancel this booking."""
        # Remove related meeting
        self.action_unschedule()
        # Archive and reset access token
        self.write({"active": False, "access_token": False})

    def action_open_portal(self):
        return {
            "target": "self",
            "type": "ir.actions.act_url",
            "url": self.get_portal_url(),
        }
