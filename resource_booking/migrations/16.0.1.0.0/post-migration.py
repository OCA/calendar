from openupgradelib import openupgrade


def _update_attendance_hour_to(env):
    # 23:59 -> 24:00
    lines = env["resource.calendar.attendance"].search(
        [("hour_to", ">=", 23 + 59 / 60)]
    )
    lines.hour_to = 24.0


@openupgrade.migrate()
def migrate(env, version):
    _update_attendance_hour_to(env)
