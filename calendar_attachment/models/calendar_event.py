from odoo import fields, models


class CalendarEvent(models.Model):
    _inherit = "calendar.event"

    attachment_ids = fields.One2many(
        comodel_name="ir.attachment",
        inverse_name="res_id",
        domain=[("res_model", "=", "calendar.event")],
    )
