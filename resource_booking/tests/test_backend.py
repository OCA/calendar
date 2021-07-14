# Copyright 2021 Tecnativa - Jairo Llopis
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import datetime

from freezegun import freeze_time

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import Form, SavepointCase

from .common import create_test_data

_2dt = fields.Datetime.to_datetime


@freeze_time("2021-02-26 09:00:00", tick=True)
class BackendCase(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_test_data(cls)

    def test_scheduling_conflict_constraints(self):
        # Combination is available on Mondays and Tuesdays
        rbc_montue = self.rbcs[2]
        # Type is available on Mondays
        cal_mon = self.r_calendars[0]
        self.rbt.resource_calendar_id = cal_mon
        # Booking cannot be placed next Tuesday
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            self.env["resource.booking"].create(
                {
                    "partner_id": self.partner.id,
                    "start": "2021-03-02 08:00:00",
                    "stop": "2021-03-02 08:30:00",
                    "type_id": self.rbt.id,
                    "combination_id": rbc_montue.id,
                }
            )
        # Booking cannot be placed next Monday before 8:00
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            self.env["resource.booking"].create(
                {
                    "partner_id": self.partner.id,
                    "start": "2021-03-02 07:45:00",
                    "stop": "2021-03-02 08:15:00",
                    "type_id": self.rbt.id,
                    "combination_id": rbc_montue.id,
                }
            )
        # Booking cannot be placed next Monday after 17:00
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            self.env["resource.booking"].create(
                {
                    "partner_id": self.partner.id,
                    "start": "2021-03-02 16:45:00",
                    "stop": "2021-03-02 17:15:00",
                    "type_id": self.rbt.id,
                    "combination_id": rbc_montue.id,
                }
            )
        # Booking can be placed next Monday
        self.env["resource.booking"].create(
            {
                "partner_id": self.partner.id,
                "start": "2021-03-01 08:00:00",
                "stop": "2021-03-01 08:30:00",
                "type_id": self.rbt.id,
                "combination_id": rbc_montue.id,
            }
        )
        # Another event cannot collide with the same RBC
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            self.env["resource.booking"].create(
                {
                    "partner_id": self.partner.id,
                    "start": "2021-03-01 08:29:59",
                    "stop": "2021-03-01 08:59:59",
                    "type_id": self.rbt.id,
                    "combination_id": rbc_montue.id,
                }
            )
        # Another event can collide with another RBC
        rbc_mon = self.rbcs[0]
        self.env["resource.booking"].create(
            {
                "partner_id": self.partner.id,
                "start": "2021-03-01 08:00:00",
                "stop": "2021-03-01 08:30:00",
                "type_id": self.rbt.id,
                "combination_id": rbc_mon.id,
            }
        )

    def test_rbc_forced_calendar(self):
        # Type is available on Mondays
        cal_mon = self.r_calendars[0]
        self.rbt.resource_calendar_id = cal_mon
        # Cannot book an combination with resources that only work on Tuesdays
        rbc_tue = self.rbcs[1]
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            self.env["resource.booking"].create(
                {
                    "partner_id": self.partner.id,
                    "start": "2021-03-01 08:00:00",
                    "stop": "2021-03-01 08:30:00",
                    "type_id": self.rbt.id,
                    "combination_id": rbc_tue.id,
                }
            )
        # However, if the combination is forced to Mondays, you can book it
        rbc_tue.forced_calendar_id = cal_mon
        self.env["resource.booking"].create(
            {
                "partner_id": self.partner.id,
                "start": "2021-03-01 08:00:00",
                "stop": "2021-03-01 08:30:00",
                "type_id": self.rbt.id,
                "combination_id": rbc_tue.id,
            }
        )

    def test_booking_from_calendar_view(self):
        # The type is configured by default with bookings of 30 minutes
        self.assertEqual(self.rbt.duration, 0.5)
        # Change it to 45 minutes
        self.rbt.duration = 0.75
        # Bookings smart button configures calendar with slots of 45 minutes
        button_context = self.rbt.action_open_bookings()["context"]
        self.assertEqual(button_context["calendar_slot_duration"], "00:45")
        self.assertEqual(button_context["default_duration"], 0.75)
        # When you click & drag on calendar to create an event, it adds the
        # start and end as default; we imitate that here to book a meeting with
        # 2 slots next monday
        booking_form = Form(
            self.env["resource.booking"].with_context(
                **button_context,
                default_start="2021-03-01 08:00:00",
                default_stop="2021-03-01 09:30:00"
            )
        )
        # This might seem redundant, but makes sure onchanges don't mess stuff
        self.assertEqual(_2dt(booking_form.start), datetime(2021, 3, 1, 8))
        self.assertEqual(_2dt(booking_form.stop), datetime(2021, 3, 1, 9, 30))
        # If I change to next week's monday, then the onchange assumes the stop
        # date will be 1 slot, and not 2
        booking_form.start = datetime(2021, 3, 8, 8)
        booking_form.partner_id = self.partner
        self.assertEqual(_2dt(booking_form.stop), datetime(2021, 3, 8, 8, 45))
        # I can book it (which means type & combination were autofilled)
        booking = booking_form.save()
        self.assertTrue(booking.meeting_id)
        self.assertEqual(booking.state, "scheduled")

    def test_dates_inverse(self):
        """Start & stop fields are computed with inverse. Test their workflow."""
        # Set type to be available only on mondays
        self.rbt.resource_calendar_id = self.r_calendars[0]
        # Create a booking from scratch
        booking_form = Form(self.env["resource.booking"])
        booking_form.type_id = self.rbt
        booking_form.partner_id = self.partner
        self.assertFalse(booking_form.start)
        self.assertFalse(booking_form.stop)
        self.assertFalse(booking_form.combination_id)
        # I can save it without booking
        booking = booking_form.save()
        self.assertEqual(booking.state, "pending")
        self.assertFalse(booking.meeting_id)
        self.assertFalse(booking.start)
        self.assertFalse(booking.stop)
        self.assertFalse(booking.combination_id)
        # I edit it again
        with Form(booking) as booking_form:
            # Start next Tuesday: updates stop; no combination available
            booking_form.start = datetime(2021, 3, 2, 8)
            self.assertEqual(_2dt(booking_form.stop), datetime(2021, 3, 2, 8, 30))
            self.assertFalse(booking_form.combination_id)
            # Move to Monday: updates stop; found one combination available
            booking_form.start = datetime(2021, 3, 1, 8)
            self.assertEqual(_2dt(booking_form.stop), datetime(2021, 3, 1, 8, 30))
            self.assertTrue(booking_form.combination_id)
        self.assertEqual(booking.state, "scheduled")
        self.assertTrue(booking.meeting_id)
        self.assertTrue(booking.start)
        self.assertTrue(booking.stop)
        self.assertTrue(booking.combination_id)

    def test_state(self):
        # I create a pending booking
        booking = self.env["resource.booking"].create(
            {"type_id": self.rbt.id, "partner_id": self.partner.id}
        )
        # Without dates, it's pending
        self.assertEqual(booking.state, "pending")
        self.assertTrue(booking.active)
        self.assertFalse(booking.meeting_id)
        self.assertFalse(booking.start)
        self.assertFalse(booking.stop)
        self.assertFalse(booking.combination_id)
        # With a linked meeting, it's scheduled
        with Form(booking) as booking_form:
            booking_form.start = datetime(2021, 3, 1, 8)
        meeting = booking.meeting_id
        self.assertEqual(booking.state, "scheduled")
        self.assertTrue(booking.active)
        self.assertTrue(meeting.exists())
        self.assertTrue(booking.start)
        self.assertTrue(booking.stop)
        self.assertTrue(booking.combination_id)
        # When partner confirms attendance, it's confirmed
        booker_attendance = meeting.attendee_ids.filtered(
            lambda one: one.partner_id == booking.partner_id
        )
        self.assertTrue(booker_attendance)
        booker_attendance.do_accept()
        self.assertEqual(booking.state, "confirmed")
        self.assertTrue(booking.active)
        self.assertTrue(meeting.exists())
        self.assertTrue(booking.start)
        self.assertTrue(booking.stop)
        self.assertTrue(booking.combination_id)
        # Without dates, it's pending again
        booking.action_unschedule()
        self.assertEqual(booking.state, "pending")
        self.assertTrue(booking.active)
        self.assertFalse(meeting.exists())
        self.assertFalse(booking.start)
        self.assertFalse(booking.stop)
        self.assertTrue(booking.combination_id)
        # Archived and without dates, it's canceled
        booking.action_cancel()
        self.assertEqual(booking.state, "canceled")
        self.assertFalse(booking.active)
        self.assertFalse(meeting.exists())
        self.assertFalse(booking.start)
        self.assertFalse(booking.stop)
        self.assertTrue(booking.combination_id)

    def test_sorted_assignment(self):
        """Set sorted assignment on RBT and test it works correctly."""
        rbc_mon, rbc_tue, rbc_montue = self.rbcs
        with Form(self.rbt) as rbt_form:
            rbt_form.combination_assignment = "sorted"
        # Book next monday at 10:00
        rb1_form = Form(self.env["resource.booking"])
        rb1_form.type_id = self.rbt
        rb1_form.partner_id = self.partner
        rb1_form.start = datetime(2021, 3, 1, 10)
        self.assertEqual(rb1_form.combination_id, rbc_mon)
        rb1 = rb1_form.save()
        self.assertEqual(rb1.combination_id, rbc_mon)
        # Another booking, same time
        rb2_form = Form(self.env["resource.booking"])
        rb2_form.type_id = self.rbt
        rb2_form.partner_id = self.partner
        rb2_form.start = datetime(2021, 3, 1, 10)
        self.assertEqual(rb2_form.combination_id, rbc_montue)
        rb2 = rb2_form.save()
        self.assertEqual(rb2.combination_id, rbc_montue)
        # I'm able to alter rb1 timing
        with Form(rb1) as rb1_form:
            rb1_form.start = datetime(2021, 3, 2, 10)
            self.assertEqual(rb1_form.combination_id, rbc_tue)
        self.assertEqual(rb1.combination_id, rbc_tue)

    def test_same_slot_twice_not_utc(self):
        """Scheduling the same slot twice fails, when not in UTC."""
        for loop in range(2):
            rb_f = Form(self.env["resource.booking"].with_context(tz="Europe/Madrid"))
            rb_f.partner_id = self.partner
            rb_f.type_id = self.rbt
            rb_f.start = datetime(2021, 3, 1, 10)
            rb_f.combination_id = self.rbcs[0]
            # 1st one works
            if loop == 0:
                rb = rb_f.save()
                self.assertEqual(rb.state, "scheduled")
            else:
                with self.assertRaises(ValidationError):
                    rb_f.save()

    def test_recurring_event(self):
        """Recurrent events are considered."""
        # Everyone busy past and next Mondays with a recurring meeting
        ce_f = Form(self.env["calendar.event"])
        ce_f.name = "recurring event past monday"
        for user in self.users:
            ce_f.partner_ids.add(user.partner_id)
        ce_f.start_datetime = datetime(2021, 2, 22, 8)
        ce_f.duration = 1
        ce_f.recurrency = True
        ce_f.interval = 1
        ce_f.rrule_type = "weekly"
        ce_f.end_type = "count"
        ce_f.count = 2
        ce_f.mo = True
        ce_f.save()
        # Cannot book next Monday at 8
        rb_f = Form(self.env["resource.booking"])
        rb_f.partner_id = self.partner
        rb_f.type_id = self.rbt
        # No RBC when starting
        self.assertFalse(rb_f.combination_id)
        # No RBC available next Monday at 8
        rb_f.start = datetime(2021, 3, 1, 8)
        self.assertFalse(rb_f.combination_id)
        # Everyone's free at 9
        rb_f.start = datetime(2021, 3, 1, 9)
        self.assertTrue(rb_f.combination_id)

    def test_change_calendar_after_bookings_exist(self):
        """Calendar changes can be done only if they introduce no conflicts."""
        rbc_mon = self.rbcs[0]
        cal_mon = self.r_calendars[0]
        # There's a booking for last monday
        past_booking = self.env["resource.booking"].create(
            {
                "combination_id": rbc_mon.id,
                "partner_id": self.partner.id,
                "start": "2021-02-22 08:00:00",
                "stop": "2021-02-22 08:30:00",
                "type_id": self.rbt.id,
            }
        )
        past_booking.action_confirm()
        self.assertEqual(past_booking.state, "confirmed")
        # There's another one for next monday, confirmed too
        future_booking = self.env["resource.booking"].create(
            {
                "combination_id": rbc_mon.id,
                "partner_id": self.partner.id,
                "start": "2021-03-01 08:00:00",
                "stop": "2021-03-01 08:30:00",
                "type_id": self.rbt.id,
            }
        )
        future_booking.action_confirm()
        self.assertEqual(future_booking.state, "confirmed")
        # Now, it's impossible for me to change the resource calendar
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            with Form(cal_mon) as cal_mon_f:
                with cal_mon_f.attendance_ids.edit(0) as att_mon_f:
                    att_mon_f.hour_from = 9
        # But let's unconfirm future boooking
        future_booking.action_unschedule()
        with Form(future_booking) as future_booking_f:
            future_booking_f.start = "2021-03-01 08:00:00"
        self.assertEqual(future_booking.state, "scheduled")
        # Now I should be able to change the resource calendar
        with Form(cal_mon) as cal_mon_f:
            with cal_mon_f.attendance_ids.edit(0) as att_mon_f:
                att_mon_f.hour_from = 9
        # However, now I shouldn't be able to confirm future booking
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            future_booking.action_confirm()

    def test_notification_tz(self):
        """Mail notification TZ is the same as resource.booking.type always."""
        # Configure RBT with Madrid calendar, but partner has other TZ
        self.r_calendars.write({"tz": "Europe/Madrid"})
        self.partner.tz = "Australia/Sydney"
        rb = self.env["resource.booking"].create(
            {
                "combination_id": self.rbcs[0].id,
                "partner_id": self.partner.id,
                "start": "2021-03-01 08:00:00",  # 09:00 in Madrid
                "stop": "2021-03-01 08:30:00",
                "type_id": self.rbt.id,
            }
        )
        rb.action_confirm()
        invitation_mail = self.env["mail.mail"].search(
            [
                ("state", "=", "outgoing"),
                (
                    "subject",
                    "=",
                    "Invitation to some customer - Test resource booking type",
                ),
            ]
        )
        # Invitation must display Madrid TZ (CET)
        self.assertIn("09:00:00 CET", invitation_mail.body)
