# Copyright 2024 Camptocamp
# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

# The many2many that scoped a public holiday line to country states before
# the lines were scoped to regions instead.
LEGACY_STATE_REL_TABLE = "public_holiday_state_rel"


def migrate_rename_xmlid_event_type_holiday(env):
    if not openupgrade.is_module_installed(env.cr, "hr_holidays_public"):
        return
    xmlid_renames = [
        (
            "hr_holidays_public.event_type_holiday",
            "calendar_public_holiday.event_type_holiday",
        ),
    ]
    openupgrade.rename_xmlids(env.cr, xmlid_renames)


def migrate_rename_field_model_hr_holidays_public_line(env):
    field_renames = [
        (
            "hr.holidays.public.line",
            "hr_holidays_public_line",
            "year_id",
            "public_holiday_id",
        ),
    ]
    openupgrade.rename_fields(env, field_renames, no_deep=True)


def migrate_rename_model_hr_holidays_public_line(env):
    if not openupgrade.table_exists(env.cr, "hr_holidays_public_line"):
        return
    model_renames = [("hr.holidays.public.line", "calendar.public.holiday.line")]
    openupgrade.rename_models(env.cr, model_renames)
    tables_renames = [("hr_holidays_public_line", "calendar_public_holiday_line")]
    openupgrade.rename_tables(env.cr, tables_renames)
    # Rename Many2many relation
    tables_renames = [("hr_holiday_public_state_rel", LEGACY_STATE_REL_TABLE)]
    openupgrade.rename_tables(env.cr, tables_renames)
    column_renames = {
        LEGACY_STATE_REL_TABLE: [("line_id", "public_holiday_line_id")],
    }
    openupgrade.rename_columns(env.cr, column_renames)


def migrate_rename_model_hr_holidays_public(env):
    if not openupgrade.table_exists(env.cr, "hr_holidays_public"):
        return
    model_renames = [
        ("hr.holidays.public", "calendar.public.holiday"),
    ]
    openupgrade.rename_models(env.cr, model_renames)
    tables_renames = [("hr_holidays_public", "calendar_public_holiday")]
    openupgrade.rename_tables(env.cr, tables_renames)


def pre_init_hook(env):
    migrate_rename_xmlid_event_type_holiday(env)
    migrate_rename_field_model_hr_holidays_public_line(env)
    migrate_rename_model_hr_holidays_public_line(env)
    migrate_rename_model_hr_holidays_public(env)


def _legacy_state_rows(cr):
    """``(line_id, state_id)`` pairs of the legacy state scoping, if any.

    A line that selected every state of its country meant the whole country
    and is left out: it stays nationwide.
    """
    if not openupgrade.table_exists(cr, LEGACY_STATE_REL_TABLE):
        return []
    cr.execute(
        """
        SELECT rel.public_holiday_line_id, rel.state_id
        FROM public_holiday_state_rel rel
        JOIN calendar_public_holiday_line line
            ON line.id = rel.public_holiday_line_id
        JOIN calendar_public_holiday holiday
            ON holiday.id = line.public_holiday_id
        JOIN res_country_state state ON state.id = rel.state_id
        WHERE holiday.country_id IS NULL
           OR EXISTS (
               SELECT 1
               FROM res_country_state missing
               WHERE missing.country_id = holiday.country_id
                 AND NOT EXISTS (
                     SELECT 1
                     FROM public_holiday_state_rel r
                     WHERE r.public_holiday_line_id = line.id
                       AND r.state_id = missing.id
                 )
           )
        ORDER BY rel.public_holiday_line_id, rel.state_id
        """
    )
    return cr.fetchall()


def _legacy_state_ids_by_line(cr):
    state_ids_by_line = {}
    for line_id, state_id in _legacy_state_rows(cr):
        state_ids_by_line.setdefault(line_id, set()).add(state_id)
    return state_ids_by_line


def disable_lines_with_legacy_states(env):
    """Disable the lines once scoped to states that no region stands for.

    Public holiday lines used to be scoped to country states; they are
    scoped to public holiday regions now, and regions only exist for the
    places people work at, which this module knows nothing about. A line
    that was scoped to states and has no region yet would apply nationwide,
    so it is disabled instead; ``assign_regions_from_legacy_states`` enables
    it again as soon as a module that knows the places of work hands it the
    regions lying in its states.

    Idempotent. Returns the lines disabled by this run.
    """
    line_model = env["calendar.public.holiday.line"].with_context(active_test=False)
    state_ids_by_line = _legacy_state_ids_by_line(env.cr)
    lines = line_model.browse(sorted(state_ids_by_line)).exists()
    unscoped = lines.filtered(lambda line: line.active and not line.region_ids)
    if unscoped:
        unscoped.write({"active": False})
    for line in unscoped:
        _logger.warning(
            "calendar_public_holiday: no region stands for the former states of "
            "%s (%s); the line is disabled until one does",
            line.display_name,
            line.date,
        )
    return unscoped


def assign_regions_from_legacy_states(env, regions_by_state):
    """Give the lines once scoped to states the regions lying in those states.

    :param regions_by_state: ``{state_id: regions}``, the regions lying in
        each state as resolved by a module that knows the places of work --
        ``hr_holidays_public`` takes them from the work addresses.

    Every line that was scoped to states is assigned the regions of those
    states; a line disabled for lack of a region is enabled again when it
    receives one. A line that selected every state of its country meant the
    whole country and is left nationwide.

    Idempotent: an assignment already made is left alone. Returns the lines
    that received a region.
    """
    line_model = env["calendar.public.holiday.line"].with_context(active_test=False)
    region_model = env["calendar.public.holiday.region"]
    state_ids_by_line = _legacy_state_ids_by_line(env.cr)
    assigned = line_model
    for line in line_model.browse(sorted(state_ids_by_line)).exists():
        regions = region_model
        for state_id in state_ids_by_line[line.id]:
            regions |= regions_by_state.get(state_id, region_model)
        missing = regions - line.region_ids
        if not missing:
            continue
        line.write({"region_ids": [(4, region.id) for region in missing]})
        if not line.active:
            line.active = True
        assigned |= line
    _logger.info(
        "calendar_public_holiday: %s public holiday line(s) received the regions "
        "of their former states",
        len(assigned),
    )
    return assigned


def post_init_hook(env):
    # A database coming from hr_holidays_public still carries the legacy
    # state relation the pre-init hook renamed; the lines are scoped to
    # regions now, so the state-scoped ones are disabled until a module
    # knowing the places of work hands them the regions of their states.
    disable_lines_with_legacy_states(env)
