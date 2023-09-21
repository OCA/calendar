from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    resource_booking_count = fields.Integer(
        compute="_compute_resource_booking_count", string="Resource booking count"
    )
    resource_booking_ids = fields.One2many(
        "resource.booking", "partner_id", string="Bookings"
    )

    def _compute_resource_booking_count(self):
        for p in self:
            p.resource_booking_count = len(p.resource_booking_ids)

    def action_view_resource_booking(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "resource_booking.resource_booking_action"
        )
        action["context"] = {
            "default_partner_id": self.id,
        }
        return action
