# Copyright 2025 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
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
    apply_partner_filter = fields.Boolean(
        default=True,
        help="If enabled, only events where this partner is an attendee are exported.",
    )
    domain = fields.Char(
        help="Optional extra domain (to safe_eval)",
    )
    share_webcal_url = fields.Char(compute="_compute_share_urls", readonly=True)
    share_url = fields.Char(compute="_compute_share_urls", readonly=True)

    def _compute_access_url(self):
        """Adjust to modufy access url"""
        res = super()._compute_access_url()
        base_url = self.get_base_url()
        for cal in self:
            cal.access_url = f"{base_url}/calendar/shared/{cal.id}/ics"
        return res

    @api.depends("access_token")
    def _compute_share_urls(self):
        """Compute actual share urls (https://, webcall:)"""
        base_url = self.get_base_url()
        for cal in self:
            cal._portal_ensure_token()
            ics_url = f"{base_url}/calendar/shared/{cal.id}/ics?access_token={cal.access_token}"
            cal.share_url = ics_url
            cal.share_webcal_url = ics_url.replace("https://", "webcal://").replace(
                "http://", "webcal://"
            )

    def action_reset_access_token(self):
        """Rotate token (invalidate old subscription URLs)."""
        for cal in self.sudo():
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

    def _combine_ics_files(self, events, files_by_event_id):
        """Combine individual VCALENDAR payloads into one VCALENDAR bytes."""
        combined = vobject.iCalendar()
        for ev in events:
            payload = files_by_event_id.get(ev.id)
            if not payload:
                continue
            ics_text = payload.decode("utf-8", errors="replace")
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
