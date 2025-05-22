from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    resource_booking_count = fields.Integer(
        compute="_compute_resource_booking_count", string="Resource booking count"
    )
    resource_booking_ids = fields.Many2many(
        comodel_name="resource.booking",
        relation="res_partner_resource_booking_rel",
        column1="res_partner_id",
        column2="resource_booking_id",
        string="Bookings",
        copy=False,
    )

    def _compute_resource_booking_count(self):
        booking_count_by_partner = dict(
            self.env["resource.booking"]._read_group(
                [("partner_ids", "in", self.ids)], ["partner_ids"], ["__count"]
            )
        )
        for p in self:
            p.resource_booking_count = booking_count_by_partner.get(p, 0)

    def action_view_resource_booking(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "resource_booking.resource_booking_action"
        )
        action["context"] = {
            "default_partner_ids": self.ids,
            "search_default_partner_ids": self.display_name,
        }
        return action
