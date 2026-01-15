# Copyright 2025 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
import re
from datetime import timedelta

import vobject

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval


class CalendarSharedIcs(models.Model):
    _name = "calendar.shared.ics"
    _description = "Shared ICS calendar"
    _inherit = ["portal.mixin", "mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    name = fields.Char(required=True, default="Shared calendar")
    active = fields.Boolean(default=True)
    partner_id = fields.Many2one("res.partner", index=True)
    apply_user_filter = fields.Boolean(
        default=True,
        help="If enabled, restrict partner selection to partners linked to users.",
    )
    include_internal_users = fields.Boolean(
        default=True,
        help="If enabled, include internal users in partner selection.",
    )
    include_portal_users = fields.Boolean(
        default=False,
        help="If enabled, include portal users in partner selection.",
    )

    apply_partner_filter = fields.Boolean(
        default=True,
        help="If enabled, only events where this partner is an attendee are exported.",
    )
    domain = fields.Char(
        help="Optional extra domain (to safe_eval)",
        string="Additional Filtering",
    )
    share_webcal_url = fields.Char(compute="_compute_share_urls", readonly=True)
    share_url = fields.Char(compute="_compute_share_urls", readonly=True)
    only_recent_events = fields.Boolean(
        default=True,
        help="If enabled, only export events that ended recently or are in the future ",
    )
    recent_days = fields.Integer(
        default=7,
        help="How many days back to include for recent events",
    )
    allowed_partner_ids = fields.Many2many(
        "res.partner",
        compute="_compute_allowed_partner_ids",
        compute_sudo=True,
        help="Partners selectable in partner_id according to the user filter options.",
    )

    def _compute_access_url(self):
        """Adjust to modify access url"""
        res = super()._compute_access_url()
        base_url = self.get_base_url()
        for cal in self:
            cal.access_url = f"{base_url}/calendar/shared/{cal.id}/ics"
        return res

    @api.depends("access_url", "access_token")
    def _compute_share_urls(self):
        for cal in self:
            cal._portal_ensure_token()
            if not cal.access_url:
                cal.share_url = False
                cal.share_webcal_url = False
                continue
            url = f"{cal.access_url}?access_token={cal.access_token}"
            cal.share_url = url
            cal.share_webcal_url = url.replace("https://", "webcal://").replace(
                "http://", "webcal://"
            )

    @api.depends("apply_user_filter", "include_internal_users", "include_portal_users")
    def _compute_allowed_partner_ids(self):
        Users = self.env["res.users"].sudo()
        for cal in self:
            if not cal.apply_user_filter:
                cal.allowed_partner_ids = False
                continue
            # If neither is selected allow none.
            if not cal.include_internal_users and not cal.include_portal_users:
                cal.allowed_partner_ids = [(6, 0, [])]
                continue
            domain = []
            parts = []
            if cal.include_internal_users:
                parts.append([("share", "=", False)])
            if cal.include_portal_users:
                parts.append([("share", "=", True)])
            if len(parts) == 1:
                domain = parts[0]
            else:
                domain = ["|"] + parts[0] + parts[1]
            users = Users.search(domain)
            cal.allowed_partner_ids = [(6, 0, users.mapped("partner_id").ids)]

    def action_reset_access_token(self):
        """Rotate token (invalidate old subscription URLs)."""
        # Enforce security
        self.check_access_rights("write")
        self.check_access_rule("write")
        for cal in self:
            cal.access_token = False
            cal._portal_ensure_token()

    def action_open_share_wizard(self):
        """Open portal share wizard for this feed."""
        self.ensure_one()
        self._portal_ensure_token()
        ctx = dict(self.env.context)
        ctx.update(
            active_model=self._name,
            active_id=self.id,
            active_ids=[self.id],
        )
        if self.partner_id:
            ctx["default_partner_ids"] = [(6, 0, [self.partner_id.id])]
        return {
            "type": "ir.actions.act_window",
            "name": "Share",
            "res_model": "portal.share",
            "view_mode": "form",
            "target": "new",
            "context": ctx,
        }

    def _get_share_url(self, redirect=False, **kwargs):
        self.ensure_one()
        self._portal_ensure_token()
        return f"/calendar/shared/{self.id}/landing?access_token={self.access_token}"

    def _check_access_token(self, token):
        self.ensure_one()
        self._portal_ensure_token()
        return bool(token) and token == self.access_token

    def _get_events_domain(self):
        """Compute the calendar.event domain for this shared feed."""
        self.ensure_one()
        domain = []
        # limit events to recent_days in the past
        if self.only_recent_events:
            cutoff = fields.Datetime.now() - timedelta(days=self.recent_days or 0)
            domain.append(("stop", ">=", cutoff))
        if self.apply_partner_filter and self.partner_id:
            domain.append(("partner_ids", "in", [self.partner_id.id]))
        if self.domain:
            extra = safe_eval(self.domain.strip(), {"uid": self.env.uid})
            domain += list(extra)
        return domain

    def _get_events_for_export(self):
        """Return calendar.event recordset to export."""
        self.ensure_one()
        domain = self._get_events_domain()
        return self.env["calendar.event"].sudo().search(domain, order="start asc")

    def _fix_recurrence_lines(self, ics_text):
        """
        Fix malformed recurrence lines seen in some _get_ics_file() outputs.
        Wrong: RRULE:DTSTART:20220425T063000
        Right: DTSTART:20220425T063000
        """
        if "RRULE:DTSTART:" not in ics_text:
            return ics_text
        # If the VEVENT already has a proper DTSTART, drop the malformed line.
        # Otherwise, rewrite the malformed line into DTSTART.
        fixed_blocks = []
        in_vevent = False
        vevent_lines = []
        for line in ics_text.splitlines(True):
            if line.startswith("BEGIN:VEVENT"):
                in_vevent = True
                vevent_lines = [line]
                continue
            if in_vevent:
                vevent_lines.append(line)
                if line.startswith("END:VEVENT"):
                    block = "".join(vevent_lines)
                    if "RRULE:DTSTART:" in block:
                        if "DTSTART:" in block:
                            block = re.sub(
                                r"^RRULE:DTSTART:.*\r?\n",
                                "",
                                block,
                                flags=re.MULTILINE,
                            )
                        else:
                            block = re.sub(
                                r"^RRULE:DTSTART:(.+)$",
                                r"DTSTART:\1",
                                block,
                                flags=re.MULTILINE,
                            )
                    fixed_blocks.append(block)
                    in_vevent = False
                continue
            fixed_blocks.append(line)
        return "".join(fixed_blocks)

    def _combine_ics_files(self, events, files_by_event_id):
        """Combine individual VCALENDAR payloads into one VCALENDAR bytes."""
        combined = vobject.iCalendar()
        for ev in events:
            payload = files_by_event_id.get(ev.id)
            if not payload:
                continue
            ics_text = payload.decode("utf-8", errors="replace")
            ics_text = self._fix_recurrence_lines(ics_text)
            cal = vobject.readOne(ics_text)
            for vev in cal.vevent_list:
                combined.add(vev)
        return combined.serialize().encode("utf-8")

    def _render_ics_content(self):
        """Return merged ICS content (bytes) for this feed."""
        self.ensure_one()
        events = self._get_events_for_export()
        files = events._get_ics_file() or {}
        return self._combine_ics_files(events, files)

    def _get_ics_filename(self):
        """Return download filename for this feed."""
        self.ensure_one()
        return (self.name or "calendar").strip() + ".ics"
