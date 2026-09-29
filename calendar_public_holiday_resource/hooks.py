# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Materialise the public holidays of the current sync window."""
    lines = env["calendar.public.holiday.line"]._get_lines_to_sync()
    if not lines:
        return
    summary = lines._sync_global_leaves()
    _logger.info(
        "calendar_public_holiday_resource: %(created)s time off created, "
        "%(adopted)s adopted, %(updated)s updated, %(removed)s removed",
        summary,
    )
    for conflict in summary["conflicts"]:
        _logger.warning(
            "calendar_public_holiday_resource: skipped %(line)s on %(date)s -- "
            "%(reason)s (resource.calendar.leaves %(leave_id)s)",
            conflict,
        )
    for issue in summary["issues"]:
        _logger.warning(
            "calendar_public_holiday_resource: no time off generated -- %s", issue
        )
