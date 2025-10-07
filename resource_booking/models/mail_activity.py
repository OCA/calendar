# Copyright 2024 Tecnativa - Carolina Fernandez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models, tools
from odoo.tools import is_html_empty


class MailActivityType(models.Model):
    _inherit = "mail.activity.type"

    category = fields.Selection(
        selection_add=[("resource_booking", "Resource booking")]
    )


class MailActivity(models.Model):
    _inherit = "mail.activity"

    booking_id = fields.Many2one(
        "resource.booking", string="Resource booking", ondelete="cascade"
    )

    def action_open_resource_booking(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "resource_booking.resource_booking_action"
        )
        action["view_mode"] = "form"
        del action["views"]
        action["res_id"] = self.booking_id.id
        ctx = dict(self.env.context)
        ctx.update(
            {
                "default_activity_type_id": self.activity_type_id.id,
                "default_name": self.summary or self.res_name,
                "default_description": self.note
                if not is_html_empty(self.note)
                else "",
                "default_booking_activity_ids": [(6, 0, self.ids)],
            }
        )
        action["context"] = ctx
        return action

    def _action_done(self, feedback=False, attachment_ids=False):
        bookings = self.mapped("booking_id")
        messages, activities = super()._action_done(
            feedback=feedback, attachment_ids=attachment_ids
        )
        if feedback:
            for booking in bookings:
                description = booking.description
                description = "{}<br />{}".format(
                    description if not tools.is_html_empty(description) else "",
                    self.env._(
                        "Feedback: %(feedback)s",
                        feedback=tools.plaintext2html(feedback),
                    )
                    if feedback
                    else "",
                )
                booking.write({"description": description})
        return messages, activities
