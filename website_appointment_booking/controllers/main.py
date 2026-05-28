# Copyright 2025 Ledo Enterprises LLC - Don Kendall
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
import logging
import urllib.request
from datetime import datetime, timedelta, timezone

import pytz
from dateutil.parser import isoparse
from dateutil.relativedelta import relativedelta
from werkzeug.exceptions import NotFound

from odoo import http
from odoo.exceptions import ValidationError
from odoo.http import request

_logger = logging.getLogger(__name__)


class WebsiteAppointmentBooking(http.Controller):
    def _get_booking_type(self, slug):
        """Look up a published booking type by its slug."""
        return (
            request.env["resource.booking.type"]
            .sudo()
            .search(
                [("website_slug", "=", slug), ("website_published", "=", True)],
                limit=1,
            )
        )

    @staticmethod
    def _validate_tz(tz):
        """Return ``tz`` if pytz can resolve it (incl. aliases), else None.

        ``pytz.all_timezones_set`` only contains the canonical names —
        modern browsers can emit deprecated-but-valid aliases like
        ``Asia/Calcutta``, ``America/Buenos_Aires``, ``Etc/GMT+5`` which
        membership tests reject. ``pytz.timezone()`` accepts them all,
        so use it as the validity probe.
        """
        if not tz or not isinstance(tz, str):
            return None
        try:
            pytz.timezone(tz)
        except pytz.UnknownTimeZoneError:
            return None
        return tz

    def _create_phantom_booking(self, booking_type, tz=None):
        """Create an in-memory booking for slot computation.

        Uses ``new()`` to avoid writing to the database. The phantom booking
        is configured with auto-assignment so that ``_get_available_slots``
        considers all resource combinations. ``tz`` controls the bucketing
        timezone for the calendar grid; if absent it falls back to the
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

    @staticmethod
    def _has_slots_in_visitor_window(
        slots, visitor_tz, hours_start=9, hours_end=17, days=7
    ):
        """Are any of the padded slots in the visitor's local working hours?

        Walks the slot list (which is already tz-aware, in
        ``visitor_tz`` once the phantom booking is built with
        ``with_context(tz=visitor_tz)``), and counts entries that fall
        within ``hours_start``–``hours_end`` (visitor-local hours)
        across the next ``days`` days from now.

        Returns True as soon as one such slot is found; the loop bails
        early to keep this O(slots-until-first-match), not O(slots).
        """
        try:
            tz = pytz.timezone(visitor_tz)
        except pytz.UnknownTimeZoneError:
            return True  # be conservative — never block when validation regresses
        now = pytz.UTC.localize(datetime.utcnow()).astimezone(tz)
        cutoff = now + timedelta(days=days)
        for day_slots in slots.values():
            for slot_dt in day_slots:
                local = slot_dt.astimezone(tz)
                if now <= local < cutoff and hours_start <= local.hour < hours_end:
                    return True
        return False

    def _serialize_slots(self, slots, time_format, effective_tz=None):
        """Serialize slot data to a JSON-safe list of dicts.

        Each dict contains ``date``, ``time`` (display string) and ``iso``
        (full ISO 8601 value used for form submission).

        ``resource_booking._get_available_slots`` buckets by
        ``test_start.date()`` using the booking's intrinsic tz (resource
        calendar's). When the visitor selected a different tz via ``?tz=``,
        we re-bucket in their tz here so the calendar grid reflects their
        local dates. ``iso`` is normalized to UTC so it stays stable across
        tz views — that lets clients compare slot identity regardless of
        which view they're rendering.
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

    @http.route(
        [
            "/book/<slug>",
            "/book/<slug>/<int:year>/<int:month>",
        ],
        auth="public",
        type="http",
        website=True,
        sitemap=True,
    )
    def booking_page(self, slug, year=None, month=None, error=None, **kwargs):
        """Render the public booking page for a given booking type."""
        booking_type = self._get_booking_type(slug)
        if not booking_type:
            raise NotFound()
        resource_tz = booking_type.resource_calendar_id.tz or "UTC"
        # ``?tz=`` overrides the bucketing timezone for the calendar grid.
        # Invalid values silently fall back to the resource tz.
        effective_tz = self._validate_tz(kwargs.get("tz")) or resource_tz
        phantom = self._create_phantom_booking(booking_type, tz=effective_tz)
        calendar_ctx = phantom._get_calendar_context(year, month)
        lang = calendar_ctx["res_lang"]
        time_format = lang.time_format.replace(":%S", "")

        # Pad the slot fetch window by ±1 day so the JS client-side
        # re-bucketer has neighbouring-day slots when the visitor's
        # timezone shifts a slot across the month boundary. Without
        # padding, a 23:30 ET slot on Mar 31 would bucket to Apr 1 in NZ
        # but be missing if the visitor navigates to April.
        start = calendar_ctx["start"]
        booking_duration = timedelta(hours=booking_type.duration)
        padded_start = start - timedelta(days=1)
        padded_stop = (
            start + relativedelta(months=1) + booking_duration + timedelta(days=1)
        )
        padded_slots = phantom._get_available_slots(padded_start, padded_stop)
        slot_data = self._serialize_slots(padded_slots, time_format, effective_tz)

        # ``show_request_banner``: visitor is outside the resource tz AND
        # has zero slots in their local working hours over the next week.
        # Domestic visitors (same tz as resource) never see the banner.
        has_window_slots = self._has_slots_in_visitor_window(padded_slots, effective_tz)
        show_request_banner = effective_tz != resource_tz and not has_window_slots

        values = {
            "booking_type": booking_type,
            "slot_data": slot_data,
            "slot_data_json": json.dumps(slot_data),
            "error": error,
            "resource_tz": resource_tz,
            "effective_tz": effective_tz,
            "show_request_banner": show_request_banner,
            "request_success": kwargs.get("request_success") == "1",
        }
        values.update(calendar_ctx)
        return request.render("website_appointment_booking.booking_page", values)

    @http.route(
        "/book/<slug>/confirm",
        auth="public",
        type="http",
        website=True,
        methods=["POST"],
        csrf=True,
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
        name = (kwargs.get("name") or "").strip()
        email = (kwargs.get("email") or "").strip()
        when_str = kwargs.get("when", "")
        if not name or not email or not when_str:
            return request.redirect(f"/book/{slug}?error=Please+fill+in+all+fields.")
        # Parse the submitted datetime
        try:
            when_tz_aware = isoparse(when_str)
        except (ValueError, TypeError):
            return request.redirect(f"/book/{slug}?error=Invalid+date+selected.")
        # Convert to UTC-naive for Odoo storage. astimezone is exact —
        # avoids the epoch float rounding of fromtimestamp(timestamp()).
        when_naive = when_tz_aware.astimezone(timezone.utc).replace(tzinfo=None)
        # Find or create partner
        Partner = request.env["res.partner"].sudo()
        partner = Partner.search([("email", "=ilike", email)], limit=1)
        if not partner:
            partner = Partner.create({"name": name, "email": email})
        elif not partner.name or partner.name == email:
            partner.name = name
        # Create and schedule the booking inside a savepoint so that
        # a ValidationError (race condition: slot already taken) can be
        # caught without poisoning the database cursor.
        Booking = request.env["resource.booking"].sudo()
        resource_tz = booking_type.resource_calendar_id.tz or "UTC"
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
                    }
                )
                booking.start = when_naive
                booking.action_confirm()
        except ValidationError:
            # Race condition: slot was taken between page load and submit.
            # The month-nav path is anchored to resource-tz months.
            resource_when = when_tz_aware.astimezone(pytz.timezone(resource_tz))
            month_str = f"{resource_when:%Y/%m}"
            return request.redirect(
                f"/book/{slug}/{month_str}"
                "?error=That+slot+is+no+longer+available.+Please+choose+another."
            )
        # Re-derive the success-page strings from the canonical UTC instant
        # using the validated display tz. This blocks a malicious client
        # from submitting e.g. ``when=…+09:00`` to make the success page
        # show a misleading time.
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

    @http.route(
        "/book/<slug>/success",
        auth="public",
        type="http",
        website=True,
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

    # --- Out-of-hours request flow -----------------------------------------

    _REQUEST_TAG = "intl-after-hours-request"

    def _resolve_request_tag(self):
        """Look up or create the CRM tag attached to every request lead."""
        Tag = request.env["crm.tag"].sudo()
        tag = Tag.search([("name", "=", self._REQUEST_TAG)], limit=1)
        if not tag:
            tag = Tag.create({"name": self._REQUEST_TAG})
        return tag

    def _publish_ntfy(self, lead, booking_type, visitor_tz, preferred_window):
        """Best-effort push to the ntfy topic stored in ir.config_parameter.

        Reads three params: ``ntfy.base_url`` (defaults to the self-hosted
        instance), ``ntfy.topic`` (the bot's write-only topic), and
        ``ntfy.token`` (the bearer token). Missing topic → silent no-op
        (this matches the website tier's ntfy.ts behavior). Failures are
        logged and swallowed: the user-visible flow must never block on
        a notification side-channel.
        """
        icp = request.env["ir.config_parameter"].sudo()
        topic = icp.get_param("ntfy.topic")
        if not topic:
            return
        base = icp.get_param("ntfy.base_url", "https://ntfy.hz.ledoweb.com")
        token = icp.get_param("ntfy.token")

        # Strip CR/LF from any user-supplied text that flows into HTTP
        # headers so we don't get header injection via the visitor name.
        def _safe_header(value, max_len=200):
            if not value:
                return ""
            cleaned = "".join(
                c if c >= " " and c != "\r" and c != "\n" else " " for c in str(value)
            ).strip()
            return cleaned[:max_len]

        title = _safe_header(
            f"🌏 Out-of-hours request: {lead.contact_name or lead.email_from}", 100
        )
        body = (
            f"{lead.contact_name or '(no name)'} <{lead.email_from}>\n"
            f"For: {booking_type.name}\n"
            f"Visitor TZ: {visitor_tz}\n"
            f"Preferred window: {preferred_window or '(none)'}"
        )
        click = f"{request.httprequest.host_url.rstrip('/')}/odoo/crm/{lead.id}"

        url = f"{base.rstrip('/')}/{topic}"
        headers = {
            "Title": title,
            "Tags": "earth_asia,inbox_tray",
            "Priority": "4",
            "Click": _safe_header(click, 512),
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            req = urllib.request.Request(
                url,
                data=body.encode("utf-8"),
                headers=headers,
                method="POST",
            )
            urllib.request.urlopen(req, timeout=3)
        except Exception:  # pylint: disable=broad-except
            # fire-and-forget; never break the request
            _logger.warning("ntfy publish failed", exc_info=True)

    @http.route(
        "/book/<slug>/request",
        auth="public",
        type="http",
        website=True,
        methods=["POST"],
        csrf=True,
    )
    def booking_request(self, slug, **kwargs):
        """Submit an out-of-hours booking request.

        Creates a tagged ``crm.lead`` (no booking — the operator opens a
        slot manually + replies), fires a high-priority ntfy push, sends
        a confirmation email to the visitor, and redirects back to the
        booking page with a success banner.
        """
        booking_type = self._get_booking_type(slug)
        if not booking_type:
            raise NotFound()
        name = (kwargs.get("name") or "").strip()
        email = (kwargs.get("email") or "").strip()
        preferred = (kwargs.get("preferred_window") or "").strip()
        note = (kwargs.get("note") or "").strip()
        visitor_tz = self._validate_tz(kwargs.get("visitor_tz")) or "UTC"

        if not name or not email:
            return request.redirect(f"/book/{slug}?error=Name+and+email+are+required.")

        Partner = request.env["res.partner"].sudo()
        partner = Partner.search([("email", "=ilike", email)], limit=1)
        if not partner:
            partner = Partner.create({"name": name, "email": email})
        elif not partner.name or partner.name == email:
            partner.name = name

        tag = self._resolve_request_tag()
        description = (
            f"Visitor requested an out-of-hours slot.\n\n"
            f"For: {booking_type.name}\n"
            f"Visitor timezone: {visitor_tz}\n"
            f"Preferred window: {preferred or '(none specified)'}\n\n"
            f"Notes:\n{note or '(none)'}"
        )
        Lead = request.env["crm.lead"].sudo()
        lead = Lead.create(
            {
                "name": f"[out-of-hours] {booking_type.name} — {name}",
                "contact_name": name,
                "email_from": email,
                "partner_id": partner.id,
                "type": "lead",
                "description": description,
                "tag_ids": [(4, tag.id)],
            }
        )

        # Best-effort: notify Don via ntfy, send the visitor a confirmation.
        self._publish_ntfy(lead, booking_type, visitor_tz, preferred)

        try:
            template = request.env.ref(
                "website_appointment_booking.mail_template_booking_request_confirmation"
            ).sudo()
            template.send_mail(lead.id, force_send=False)
        except (ValueError, Exception):  # pylint: disable=broad-except
            _logger.warning(
                "booking-request confirmation email failed for lead %s",
                lead.id,
                exc_info=True,
            )

        return request.redirect(f"/book/{slug}?request_success=1")
