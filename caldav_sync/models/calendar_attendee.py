import logging

from odoo import models

_logger = logging.getLogger(__name__)


class CalendarAttendee(models.Model):
    _inherit = "calendar.attendee"

    def _notify_attendees(self, mail_template, notify_author=False, force_send=False):
        """Override to prevent sending emails when dont_notify context is set.

        :param mail_template: a mail.template record
        :param force_send: if True, mail(s) sent immediately instead of queued
        :return: Result of super or False if notification is skipped
        """
        # Check for dont_notify in context
        if self.env.context.get("dont_notify"):
            _logger.info("Email notifications skipped due to dont_notify context")
            return False

        return super()._notify_attendees(mail_template, notify_author, force_send)
