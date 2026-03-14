# Copyright 2022 initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from uuid import uuid4

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """
    Fetches all the PO and resets the sequence of the purchase order lines.
    """
    _logger.info("Setting unique UUID for calendar events")
    for event in env["calendar.event"].search([]):
        event.uuid = str(uuid4())
