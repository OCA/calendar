# flake8: noqa
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import uuid

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class Attendee(models.Model):
    """ Calendar Attendee Information """

    _inherit = "calendar.attendee"
    _rec_name = "common_name"
    _description = "Calendar Attendee Information"

    def _default_access_token(self):
        return uuid.uuid4().hex

    STATE_SELECTION = [
        ("needsAction", "Needs Action"),
        ("tentative", "Uncertain"),
        ("declined", "Declined"),
        ("accepted", "Accepted"),
    ]

    event_id = fields.Many2one(
        "calendar.event", "Meeting linked", required=True, ondelete="cascade"
    )
    partner_id = fields.Many2one("res.partner", "Contact", required=True, readonly=True)
    state = fields.Selection(
        STATE_SELECTION,
        string="Status",
        readonly=True,
        default="needsAction",
        help="Status of the attendee's participation",
    )
    common_name = fields.Char("Common name", compute="_compute_common_name", store=True)
    email = fields.Char(
        "Email", related="partner_id.email", help="Email of Invited Person"
    )
    availability = fields.Selection(
        [("free", "Free"), ("busy", "Busy")], "Free/Busy", readonly=True
    )
    access_token = fields.Char("Invitation Token", default=_default_access_token)
    recurrence_id = fields.Many2one(
        "calendar.recurrence", related="event_id.recurrence_id"
    )

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            if values.get("partner_id") == self.env.user.partner_id.id:
                values["state"] = "accepted"
            if not values.get("email") and values.get("common_name"):
                common_nameval = values.get("common_name").split(":")
                email = [x for x in common_nameval if "@" in x]
                values["email"] = email[0] if email else ""
                values["common_name"] = values.get("common_name")
        attendees = super().create(vals_list)
        attendees._subscribe_partner()
        return attendees

    def unlink(self):
        self._unsubscribe_partner()
        return super().unlink()

    def _subscribe_partner(self):
        for event in self.event_id:
            partners = (
                event.attendee_ids & self
            ).partner_id - event.message_partner_ids
            # current user is automatically added as followers, don't add it twice.
            partners -= self.env.user.partner_id
            event.message_subscribe(partner_ids=partners.ids)

    def _unsubscribe_partner(self):
        for event in self.event_id:
            partners = (
                event.attendee_ids & self
            ).partner_id & event.message_partner_ids
            event.message_unsubscribe(partner_ids=partners.ids)

    def _send_mail_to_attendees(self, *args, **kwargs):
        """ Dispatch between calls with old/new signature """
        kwargs.pop("ignore_recurrence", False)
        return super()._send_mail_to_attendees(*args, **kwargs)
