# Copyright 2026 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class CrmLead(models.Model):
    _inherit = "crm.lead"

    resource_booking_ids = fields.One2many(
        comodel_name="resource.booking",
        inverse_name="lead_id",
        string="Bookings",
        groups="resource_booking.group_user",
    )
    resource_booking_count = fields.Integer(
        compute="_compute_resource_booking_count",
        string="Booking Count",
        groups="resource_booking.group_user",
    )

    @api.depends("resource_booking_ids")
    def _compute_resource_booking_count(self):
        counts = {
            lead.id: count
            for lead, count in self.env["resource.booking"]._read_group(
                [("lead_id", "in", self.ids)], ["lead_id"], ["__count"]
            )
        }
        for lead in self:
            lead.resource_booking_count = counts.get(lead.id, 0)

    def action_view_resource_bookings(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "resource_booking.resource_booking_action"
        )
        action["domain"] = [("lead_id", "=", self.id)]
        action["context"] = {"default_lead_id": self.id}
        return action
