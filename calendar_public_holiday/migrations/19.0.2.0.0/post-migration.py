# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade

from odoo.addons.calendar_public_holiday.hooks import (
    disable_lines_with_legacy_states,
)


@openupgrade.migrate()
def migrate(env, version):
    # The lines are scoped to regions instead of states from this version
    # on. Regions only exist for the places people work at, so every line
    # scoped to states is disabled until a module knowing those places
    # (hr_holidays_public) assigns it the regions lying in its states.
    disable_lines_with_legacy_states(env)
