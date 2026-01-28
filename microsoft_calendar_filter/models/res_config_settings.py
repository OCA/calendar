# Copyright 2026 Therp BV <https://therp.nl>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import fields, models

FILTER_PRIVATE_EVENTS = "microsoft_calendar_filter_private_events"
FILTER_ODOO_EVENTS = "microsoft_calendar_filter_odoo_events"


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    filter_microsoft_private_events = fields.Boolean(
        config_parameter=FILTER_PRIVATE_EVENTS,
        default=False,
        help="Do not synchronize microsoft private events to Odoo."
        " Actually delete private events that have already been synchronized.",
    )
    filter_odoo_events = fields.Char(
        config_parameter=FILTER_ODOO_EVENTS,
        default="[]",
        help="Limit Odoo events synchronized to records satisfying domain."
        " When no filter is set, all Odoo events will be synchronized."
        " When a filter is set, events NOT satisfying the domain, but"
        " already synchronized, will be removed from Microsoft",
    )
