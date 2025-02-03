# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class CalendarEventLinkTester(models.Model):
    _name = "calendar.event.link.tester"
    _inherit = "calendar.event.link.mixin"
    _description = "Calendar Event Link Tester"

    name = fields.Char()
