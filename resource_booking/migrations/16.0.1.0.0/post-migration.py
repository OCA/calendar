from openupgradelib import openupgrade


def _update_attendance_hour_to(env):
    """According to the refactoring of _merge_intervals() a booking from 23:00 to 01:00
    of the next day must be completely available, having defined hour_to=23.59 is not,
    so it is changed to 24.0.
    This behavior is confirmed to be correct because in the tests calendars are set
    with full days (hour_from=0, hour_to=24)."""
    lines = env["resource.calendar.attendance"].search(
        [("hour_to", ">=", 23 + 59 / 60)]
    )
    lines.hour_to = 24.0


@openupgrade.migrate()
def migrate(env, version):
    _update_attendance_hour_to(env)
