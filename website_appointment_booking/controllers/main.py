# Copyright 2025 Ledo Enterprises LLC - Don Kendall
# Copyright 2026 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
import logging
from datetime import datetime, time, timedelta, timezone

import pytz
from dateutil.parser import isoparse
from dateutil.relativedelta import relativedelta
from werkzeug.exceptions import NotFound

from odoo import SUPERUSER_ID, http
from odoo.exceptions import ValidationError
from odoo.http import request
from odoo.tools.mail import email_normalize

_logger = logging.getLogger(__name__)

# Honeypot input present in every public form: visually hidden, so a human
# never fills it while a naive bot does. A non-empty value rejects the post.
HONEYPOT_FIELD = "company_website"
# reCAPTCHA v3 action name; the token sent by the page must carry the same one.
RECAPTCHA_ACTION = "website_appointment_booking"


def sitemap_booking(env, rule, qs):
    """List every published booking page in the website sitemap.

    The routes use a plain ``<slug>`` converter, which the sitemap builder
    cannot enumerate on its own, hence this explicit generator.
    """
    booking_types = (
        env["resource.booking.type"].sudo().search([("is_published", "=", True)])
    )
    for booking_type in booking_types:
        loc = f"/book/{booking_type.website_slug}"
        if not qs or qs.lower() in loc:
            yield {"loc": loc}


class WebsiteAppointmentBooking(http.Controller):
    # ------------------------------------------------------------------
    # Helpers shared with extension modules
    # ------------------------------------------------------------------

    def _get_error_message(self, code):
        """Translate an error code carried in the URL into a message.

        Only codes known here (or by an override) render; anything else is
        ignored, so the page never echoes arbitrary text from the query
        string.
        """
        messages = {
            "missing_fields": request.env._("Please fill in all fields."),
            "invalid_email": request.env._("Please enter a valid email address."),
            "invalid_date": request.env._("Invalid date selected."),
            "slot_taken": request.env._(
                "That slot is no longer available. Please choose another."
            ),
            "rejected": request.env._(
                "Your submission could not be verified. Please try again."
            ),
        }
        return messages.get(code)

    def _get_booking_type(self, slug):
        """Look up a published booking type by its slug."""
        return (
            request.env["resource.booking.type"]
            .sudo()
            .search(
                [("website_slug", "=", slug), ("is_published", "=", True)],
                limit=1,
            )
        )

    @staticmethod
    def _validate_tz(tz):
        """Return ``tz`` if pytz can resolve it (incl. aliases), else None.

        ``pytz.all_timezones_set`` only contains the canonical names;
        browsers can emit deprecated-but-valid aliases like ``Asia/Calcutta``
        which ``pytz.timezone()`` still accepts.
        """
        if not tz or not isinstance(tz, str):
            return None
        try:
            pytz.timezone(tz)
        except pytz.UnknownTimeZoneError:
            return None
        return tz

    def _redirect_error(self, slug, code, month_path=""):
        return request.redirect(f"/book/{slug}{month_path}?error={code}")

    def _check_submission(self, kwargs, action=RECAPTCHA_ACTION):
        """Anti-abuse gate for the public POST routes.

        Returns an error code, or None when the submission may proceed.
        The honeypot always applies; reCAPTCHA v3 applies when the website
        has a site key configured (``ir.http`` returns True otherwise).
        """
        if (kwargs.get(HONEYPOT_FIELD) or "").strip():
            return "rejected"
        if not request.env["ir.http"]._verify_request_recaptcha_token(action):
            return "rejected"
        return None

    def _get_or_create_partner(self, name, email):
        """Reuse the contact with that email or create it.

        A pre-existing contact only gets its name filled when it has none
        (or the email was used as name), so a visitor cannot rename someone
        else's contact by reusing their address.
        """
        Partner = request.env["res.partner"].sudo()
        partner = Partner.search([("email", "=ilike", email)], limit=1)
        if not partner:
            partner = Partner.create({"name": name, "email": email})
        elif not partner.name or partner.name == email:
            partner.name = name
        return partner

    def _create_phantom_booking(self, booking_type, tz=None):
        """Create an in-memory booking for slot computation.

        ``new()`` avoids writing to the database. Auto-assignment makes
        ``_get_available_slots`` consider every resource combination. ``tz``
        is the bucketing timezone of the calendar grid; it defaults to the
        booking type's resource calendar timezone.
        """
        Booking = request.env["resource.booking"].sudo()
        if tz is None:
            tz = booking_type.resource_calendar_id.tz or "UTC"
        return Booking.with_context(tz=tz).new(
            {
                "type_id": booking_type.id,
                "duration": booking_type.duration,
                "combination_auto_assign": True,
            }
        )

    def _is_available_slot(self, booking_type, when_naive):
        """Is ``when_naive`` (UTC) one of the slots offered for that day?

        Re-runs the slot computation the page used, so a hand-crafted POST
        cannot book off-grid times, times inside the modification deadline,
        or times outside the working hours.
        """
        resource_tz = pytz.timezone(booking_type.resource_calendar_id.tz or "UTC")
        when_local = pytz.UTC.localize(when_naive).astimezone(resource_tz)
        day_start = resource_tz.localize(datetime.combine(when_local.date(), time.min))
        phantom = self._create_phantom_booking(booking_type, tz=resource_tz.zone)
        slots = phantom._get_available_slots(
            day_start, day_start + timedelta(days=1, hours=booking_type.duration)
        )
        return any(
            slot.astimezone(pytz.UTC).replace(tzinfo=None) == when_naive
            for day_slots in slots.values()
            for slot in day_slots
        )

    def _serialize_slots(self, slots, time_format, effective_tz=None):
        """Serialize slot data to a JSON-safe list of dicts.

        Each dict contains ``date``, ``time`` (display string) and ``iso``
        (UTC ISO 8601 value used for form submission). Slots are re-bucketed
        in ``effective_tz`` so the calendar grid reflects the visitor's
        local dates; ``iso`` stays in UTC so slot identity is stable across
        timezone views.
        """
        tz = pytz.timezone(effective_tz) if effective_tz else None
        result = []
        for day, times in sorted(slots.items()):
            for slot_dt in times:
                if tz is not None and slot_dt.tzinfo is not None:
                    local = slot_dt.astimezone(tz)
                    result.append(
                        {
                            "date": local.date().isoformat(),
                            "time": local.strftime(time_format),
                            "iso": slot_dt.astimezone(pytz.UTC).isoformat(),
                        }
                    )
                else:
                    result.append(
                        {
                            "date": day.isoformat(),
                            "time": slot_dt.strftime(time_format),
                            "iso": slot_dt.isoformat(),
                        }
                    )
        return result

    def _prepare_booking_page_values(self, booking_type, year=None, month=None, **kw):
        """Build the rendering values of the booking page.

        Extension point: modules adding blocks to the page override this and
        enrich the returned dict. ``padded_slots`` (tz-aware datetimes per
        day, one day of padding on each side of the month) is exposed for
        them and is not rendered as such.
        """
        resource_tz = booking_type.resource_calendar_id.tz or "UTC"
        # ``?tz=`` overrides the bucketing timezone for the calendar grid.
        # Invalid values silently fall back to the resource tz.
        effective_tz = self._validate_tz(kw.get("tz")) or resource_tz
        phantom = self._create_phantom_booking(booking_type, tz=effective_tz)
        calendar_ctx = phantom._get_calendar_context(year, month)
        lang = calendar_ctx["res_lang"]
        time_format = lang.time_format.replace(":%S", "")

        # Pad the slot fetch window by one day on each side so the client-side
        # re-bucketer has neighbouring-day slots when the visitor's timezone
        # shifts a slot across the month boundary.
        start = calendar_ctx["start"]
        booking_duration = timedelta(hours=booking_type.duration)
        padded_start = start - timedelta(days=1)
        padded_stop = (
            start + relativedelta(months=1) + booking_duration + timedelta(days=1)
        )
        padded_slots = phantom._get_available_slots(padded_start, padded_stop)
        slot_data = self._serialize_slots(padded_slots, time_format, effective_tz)

        values = {
            "booking_type": booking_type,
            "slot_data": slot_data,
            "slot_data_json": json.dumps(slot_data),
            "error": self._get_error_message(kw.get("error")),
            "resource_tz": resource_tz,
            "effective_tz": effective_tz,
            "padded_slots": padded_slots,
            "honeypot_field": HONEYPOT_FIELD,
        }
        values.update(calendar_ctx)
        return values

    # ------------------------------------------------------------------
    # Routes
    # ------------------------------------------------------------------

    @http.route(
        [
            "/book/<slug>",
            "/book/<slug>/<int:year>/<int:month>",
        ],
        auth="public",
        type="http",
        website=True,
        sitemap=sitemap_booking,
    )
    def booking_page(self, slug, year=None, month=None, **kwargs):
        """Render the public booking page for a given booking type."""
        booking_type = self._get_booking_type(slug)
        if not booking_type:
            raise NotFound()
        values = self._prepare_booking_page_values(booking_type, year, month, **kwargs)
        return request.render("website_appointment_booking.booking_page", values)

    @http.route(
        "/book/<slug>/confirm",
        auth="public",
        type="http",
        website=True,
        methods=["POST"],
        csrf=True,
        sitemap=False,
    )
    def booking_confirm(self, slug, **kwargs):
        """Process a booking confirmation.

        Expects POST parameters ``name``, ``email``, ``when`` (ISO 8601) and
        an optional ``display_tz`` (IANA name) used to format the success
        page in the visitor's timezone. Creates or finds the partner,
        creates the booking, assigns the slot and confirms.
        """
        booking_type = self._get_booking_type(slug)
        if not booking_type:
            raise NotFound()
        rejection = self._check_submission(kwargs)
        if rejection:
            return self._redirect_error(slug, rejection)
        name = (kwargs.get("name") or "").strip()
        email = (kwargs.get("email") or "").strip()
        when_str = kwargs.get("when", "")
        if not name or not email or not when_str:
            return self._redirect_error(slug, "missing_fields")
        email = email_normalize(email)
        if not email:
            return self._redirect_error(slug, "invalid_email")
        try:
            when_tz_aware = isoparse(when_str)
        except (ValueError, TypeError):
            return self._redirect_error(slug, "invalid_date")
        if when_tz_aware.tzinfo is None:
            return self._redirect_error(slug, "invalid_date")
        # Convert to UTC-naive for storage. astimezone is exact and avoids
        # the epoch float rounding of fromtimestamp(timestamp()).
        when_naive = when_tz_aware.astimezone(timezone.utc).replace(tzinfo=None)
        # The month-navigation path is anchored to resource-tz months.
        resource_tz = booking_type.resource_calendar_id.tz or "UTC"
        resource_when = when_tz_aware.astimezone(pytz.timezone(resource_tz))
        month_path = f"/{resource_when.year}/{resource_when.month}"
        if not self._is_available_slot(booking_type, when_naive):
            return self._redirect_error(slug, "slot_taken", month_path)
        partner = self._get_or_create_partner(name, email)
        # Create and schedule the booking inside a savepoint so that a
        # ValidationError (race: slot taken between page load and submit)
        # can be caught without poisoning the database cursor.
        Booking = request.env["resource.booking"].sudo()
        try:
            with request.env.cr.savepoint():
                booking = Booking.with_context(
                    tz=resource_tz,
                    using_portal=True,
                    mail_create_nosubscribe=True,
                ).create(
                    {
                        "type_id": booking_type.id,
                        "partner_ids": [(4, partner.id)],
                        "combination_auto_assign": True,
                        # The organizer defaults to the current (public) user.
                        # Set it once the combination is known, see below.
                        "user_id": False,
                    }
                )
                booking.start = when_naive
                booking.user_id = self._get_organizer(booking)
                booking.action_confirm()
        except ValidationError:
            return self._redirect_error(slug, "slot_taken", month_path)
        # Re-derive the success-page strings from the canonical UTC instant
        # using the validated display tz, so a client cannot make the success
        # page show a misleading time by submitting an odd ``when`` offset.
        display_tz = self._validate_tz(kwargs.get("display_tz")) or resource_tz
        display_dt = when_naive.replace(tzinfo=timezone.utc).astimezone(
            pytz.timezone(display_tz)
        )
        request.session["last_booking"] = {
            "name": booking_type.name,
            "start": display_dt.strftime("%B %d, %Y"),
            "time": display_dt.strftime("%H:%M"),
            "tz": display_tz,
            "duration": booking_type.duration,
            "location": booking_type.location or "",
        }
        return request.redirect(f"/book/{slug}/success")

    def _get_organizer(self, booking):
        """User shown as organizer of the meeting a public visitor books.

        The public user must not own records: prefer the first human
        resource of the assigned combination, else fall back to the admin
        user, else the superuser.
        """
        users = booking.combination_id.resource_ids.filtered(
            lambda res: res.resource_type == "user"
        ).user_id
        if users:
            return users[0]
        return request.env.ref("base.user_admin", raise_if_not_found=False) or (
            request.env["res.users"].sudo().browse(SUPERUSER_ID)
        )

    @http.route(
        "/book/<slug>/success",
        auth="public",
        type="http",
        website=True,
        sitemap=False,
    )
    def booking_success(self, slug, **kwargs):
        """Thank-you page after a successful booking."""
        booking_type = self._get_booking_type(slug)
        if not booking_type:
            raise NotFound()
        last_booking = request.session.pop("last_booking", {})
        values = {
            "booking_type": booking_type,
            "last_booking": last_booking,
        }
        return request.render("website_appointment_booking.booking_success", values)
