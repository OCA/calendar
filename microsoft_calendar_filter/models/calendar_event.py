# Copyright 2026 Therp BV <https://therp.nl>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import logging

from odoo import models
from odoo.osv.expression import AND
from odoo.tools.safe_eval import safe_eval

from odoo.addons.microsoft_calendar.models.microsoft_sync import (
    microsoft_calendar_token,
)

from .res_config_settings import FILTER_ODOO_EVENTS

_logger = logging.getLogger(__name__)


class CalendarEvent(models.Model):
    _inherit = "calendar.event"

    def _sync_odoo2microsoft(self):
        self._remove_events_not_in_filter()
        return super()._sync_odoo2microsoft()

    def _remove_events_not_in_filter(self):
        """Remove those events from Microsoft that should not have been synced.

        When defining a filter to limit the records to be sent to MS, records
        already in the filter might already have been synced. We want to
        remove those records from the MS Calendar, but only when they have
        been created by Odoo.

        Unfortunately, we do not always know for sure where records have been
        created, but when res_model in calendar.event is filled, it are
        definitely Odoo records.
        """
        microsoft_service = self._get_microsoft_service()
        sender_user = self.env.user
        with microsoft_calendar_token(sender_user) as token:
            if token and not sender_user.microsoft_synchronization_stopped:
                filter_domain = self._get_filter_domain()
                if filter_domain:
                    synchronized_events = self.with_context(
                        remove_events_not_in_filter=True
                    )._get_microsoft_records_to_sync()
                    # Events is already filtered on partner and date ranges.
                    for event in synchronized_events:
                        # If event is not in filter, remove it:
                        event_domain = AND([filter_domain, [("id", "=", event.id)]])
                        if self.search(event_domain, limit=1):
                            continue
                        try:
                            microsoft_service.delete(
                                # ms_organizer_event_id is computed from microsoft_id.
                                event.ms_organizer_event_id,
                                token=token,
                                timeout=15,
                            )
                            event.write(
                                {
                                    "microsoft_id": False,
                                    "need_sync_m": False,
                                    "microsoft_recurrence_master_id": False,
                                }
                            )
                        except Exception:
                            _logger.warn(
                                "Could not remove event %(event)s from MS Calendar",
                                {"event": event.name},
                            )

    def _extend_microsoft_domain(self, domain):
        """Only need this for simple calendar.event.

        Recurrent events are not sent to Outlook anyway.
        """
        if self.env.context.get("remove_events_not_in_filter", False):
            # Find Odoo records that have already been synced.
            return AND(
                [
                    domain,
                    [
                        ("microsoft_id", "!=", False),
                        ("res_model", "!=", False),
                    ],
                ]
            )
        filter_domain = self._get_filter_domain()
        extended_domain = super()._extend_microsoft_domain(domain)
        if not filter_domain:
            return extended_domain
        return AND([extended_domain, filter_domain])

    def _get_filter_domain(self):
        """Get filter domain. Return [] if not set."""
        ICP = self.env["ir.config_parameter"].sudo()
        extra_filter = ICP.get_param(FILTER_ODOO_EVENTS)
        domain_text = extra_filter.strip() if extra_filter else ""
        if domain_text in ("", "[]"):
            return []
        return safe_eval(domain_text)
