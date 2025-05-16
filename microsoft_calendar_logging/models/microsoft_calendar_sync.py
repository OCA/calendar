# Copyright 2025 Therp BV <https://therp.nl>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import logging

from odoo import api, fields, models

from odoo.addons.microsoft_account.models.microsoft_service import TIMEOUT

_logger = logging.getLogger(__name__)


class MicrosoftCalendarSync(models.AbstractModel):
    """Track times and direction of synchronization."""

    _inherit = "microsoft.calendar.sync"

    created_by_synchronization = fields.Boolean(
        default=False,
        readonly=True,
    )
    datetime_updated_from_microsoft = fields.Datetime()
    datetime_created_on_microsoft = fields.Datetime()
    datetime_updated_on_microsoft = fields.Datetime()

    def _sync_recurrence_microsoft2odoo(self, microsoft_events, new_events=None):
        synced_recurrences, updated_events = super()._sync_recurrence_microsoft2odoo(
            microsoft_events, new_events=new_events
        )
        if synced_recurrences:
            synced_recurrences.write({"created_by_synchronization": True})
        return synced_recurrences, updated_events

    @api.model
    def _create_from_microsoft(self, microsoft_event, vals_list):
        for vals in vals_list:
            vals["created_by_synchronization"] = True
        return super()._create_from_microsoft(microsoft_event, vals_list)

    def _write_from_microsoft(self, microsoft_event, vals):
        vals["datetime_updated_from_microsoft"] = fields.Datetime.now()
        return super()._write_from_microsoft(microsoft_event, vals)

    def _cancel_microsoft(self):
        for this in self:
            _logger.info(
                "Microsoft deleted %(model)s, (%(id)s, %(name)s)",
                {"model": this._name, "id": this.id, "name": this.name},
            )
        return super()._cancel_microsoft()

    def _microsoft_delete(self, user_id, event_id, timeout=TIMEOUT):
        """Log deletion of microsoft record, for either unlinked or archived record."""
        # Actual delete on microsoft will run after commit.
        for this in self:
            _logger.info(
                "Deleting event on microsoft for %(model)s, (%(id)s, %(name)s)",
                {"model": this._name, "id": this.id, "name": this.name},
            )
        return super()._microsoft_delete(user_id, event_id, timeout=timeout)

    def _microsoft_patch(self, user_id, event_id, values, timeout=TIMEOUT):
        """Mark time record last updated on microsoft from Odoo."""
        # Actual update on microsoft will run after commit.
        super().write({"datetime_updated_on_microsoft": fields.Datetime.now()})
        return super()._microsoft_patch(user_id, event_id, values, timeout=timeout)

    def _microsoft_insert(self, values, timeout=TIMEOUT):
        """Mark time record created on microsoft from Odoo."""
        # Actual insert on microsoft will run after commit.
        super().write({"datetime_created_on_microsoft": fields.Datetime.now()})
        return super()._microsoft_insert(values, timeout=timeout)
