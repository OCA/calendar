# Copyright 2024 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


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
