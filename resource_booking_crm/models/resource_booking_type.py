# Copyright 2026 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResourceBookingType(models.Model):
    _inherit = "resource.booking.type"

    crm_lead_type = fields.Selection(
        selection=[("lead", "Lead"), ("opportunity", "Opportunity")],
        string="Create in CRM",
        help="When set, scheduling a booking of this type creates a lead or an "
        "opportunity linked to it, carrying the UTM campaign, source and medium "
        "of the booking.",
    )
    crm_team_id = fields.Many2one(
        comodel_name="crm.team",
        string="Sales Team",
        check_company=True,
    )
    crm_user_id = fields.Many2one(
        comodel_name="res.users",
        string="Salesperson",
        domain="[('share', '=', False)]",
        check_company=True,
        help="Salesperson of the created leads. When empty, the booking organizer "
        "or the first user of the assigned resources is used.",
    )
    crm_tag_ids = fields.Many2many(
        comodel_name="crm.tag",
        string="CRM Tags",
    )
    crm_lead_reuse = fields.Boolean(
        string="Reuse Open Lead",
        help="Link the booking to the most recent open lead or opportunity of the "
        "requester's company instead of creating a new one.",
    )
