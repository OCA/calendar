from openupgradelib import openupgrade

xmlids_spec = [
    (
        "resource_booking.menu_resource_resource",
        "resource_booking.resource_resource_menu",
    ),
    (
        "resource_booking.menu_resource_calendar",
        "resource_booking.resource_calendar_menu",
    ),
    (
        "resource_booking.menu_view_resource_calendar_leaves_search",
        "resource_booking.resource_calendar_leaves_menu",
    ),
    (
        "resource_booking.resource_booking_combination_form",
        "resource_booking.resource_booking_combination_view_form",
    ),
    (
        "resource_booking.resource_booking_type_form",
        "resource_booking.resource_booking_type_view_form",
    ),
    (
        "resource_booking.resource_booking_form",
        "resource_booking.resource_booking_view_form",
    ),
]


@openupgrade.migrate(use_env=False)
def migrate(cr, version):
    openupgrade.rename_xmlids(cr, xmlids_spec)
