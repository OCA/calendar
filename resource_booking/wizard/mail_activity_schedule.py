from odoo import models
from odoo.exceptions import UserError


class MailActivitySchedule(models.TransientModel):
    _inherit = "mail.activity.schedule"

    def action_open_resource_booking(self):
        self.ensure_one()
        if self.is_batch_mode:
            raise UserError(
                self.env._(
                    "Scheduling an activity using the booking "
                    "is not possible on more than one record."
                )
            )
        return self._action_schedule_activities().action_open_resource_booking()
