import logging

import caldav

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = "res.users"

    caldav_calendar_url = fields.Char(string="CalDAV Calendar URL")
    caldav_username = fields.Char(string="CalDAV Username")
    caldav_password = fields.Char(string="CalDAV Password")
    is_caldav_enabled = fields.Boolean(compute="_compute_is_caldav_enabled", store=True)

    @api.depends("caldav_username", "caldav_password", "caldav_calendar_url")
    def _compute_is_caldav_enabled(self):
        """Compute whether CalDAV is enabled for each user.

        Validates credentials by checking if we can connect to the server and
        access the principal, without fetching events to avoid timeouts.
        """
        for rec in self:
            # If any required field is empty, CalDAV is disabled
            if not (
                rec.caldav_username and rec.caldav_password and rec.caldav_calendar_url
            ):
                rec.is_caldav_enabled = False
                continue
            try:
                client = rec._get_caldav_client()
                # Just try to access the principal, which is a lightweight operation
                client.principal()
                rec.is_caldav_enabled = True
            except Exception as e:
                rec.is_caldav_enabled = False
                _logger.error("Failed to validate CalDAV credentials: %s", e)

    def _get_caldav_client(self):
        self.ensure_one()
        return caldav.DAVClient(
            url=self.caldav_calendar_url,
            username=self.caldav_username,
            password=self.caldav_password,
        )

    def _get_caldav_events(self):
        self.ensure_one()
        client = self._get_caldav_client()
        try:
            calendar = client.calendar(url=self.caldav_calendar_url)
            events = calendar.events()
            self.is_caldav_enabled = True
        except Exception as e:
            self.is_caldav_enabled = False
            _logger.error(e)
            try:
                principal = client.principal()
                msg = (
                    f"Failed to connect to the calendar, but successfully connected "
                    f"to the server at {client.url}. You may need to select another "
                    f"calendar URL from those below.\n\n"
                )
                for calendar in principal.calendars():
                    msg += f"{calendar.name}: {calendar.url}\n"
                raise UserError(msg)
            except Exception as e:
                _logger.error(e)
                return
        return events
