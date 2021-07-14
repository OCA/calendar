# Copyright 2021 Tecnativa - Jairo Llopis
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


def create_test_data(obj):
    """Create test data for a case."""
    obj.env = obj.env(context={"tz": "UTC"})
    # Create one resource.calendar available on Mondays, another one on
    # Tuesdays, and another one on Mondays and Tuesdays; in that order
    attendances = [
        (
            0,
            0,
            {
                "name": "Mondays",
                "dayofweek": "0",
                "hour_from": 8,
                "hour_to": 17,
                "day_period": "morning",
            },
        ),
        (
            0,
            0,
            {
                "name": "Tuesdays",
                "dayofweek": "1",
                "hour_from": 8,
                "hour_to": 17,
                "day_period": "morning",
            },
        ),
    ]
    obj.r_calendars = obj.env["resource.calendar"].create(
        [
            {"name": "Mon", "attendance_ids": attendances[:1], "tz": "UTC"},
            {"name": "Tue", "attendance_ids": attendances[1:], "tz": "UTC"},
            {"name": "MonTue", "attendance_ids": attendances, "tz": "UTC"},
        ]
    )
    # Create one material resource for each of those calendars; same order
    obj.r_materials = obj.env["resource.resource"].create(
        [
            {
                "name": "Material resource for %s" % cal.name,
                "calendar_id": cal.id,
                "resource_type": "material",
                "tz": "UTC",
            }
            for cal in obj.r_calendars
        ]
    )
    # Create one human resource for each of those calendars; same order
    obj.users = obj.env["res.users"].create(
        [
            {
                "email": "user_%d@example.com" % num,
                "login": "user_%d" % num,
                "name": "User %d" % num,
            }
            for num in range(3)
        ]
    )
    obj.r_users = obj.env["resource.resource"].create(
        [
            {
                "calendar_id": cal.id,
                "name": "User %s" % user.name,
                "resource_type": "user",
                "tz": "UTC",
                "user_id": user.id,
            }
            for (user, cal) in zip(obj.users, obj.r_calendars)
        ]
    )
    # Create one RBC for each of those calendars, which includes the
    # corresponding material and human resources simultaneously; same order
    obj.rbcs = obj.env["resource.booking.combination"].create(
        [
            {"resource_ids": [(6, 0, [user.id, material.id])]}
            for (user, material) in zip(obj.r_users, obj.r_materials)
        ]
    )
    # Create one RBT that includes all 3 RBCs as available combinations
    obj.rbt = obj.env["resource.booking.type"].create(
        {
            "name": "Test resource booking type",
            "combination_rel_ids": [
                (0, 0, {"sequence": num, "combination_id": rbc.id})
                for num, rbc in enumerate(obj.rbcs)
            ],
            "resource_calendar_id": obj.r_calendars[2].id,
            "location": "Main office",
        }
    )
    # Create some partner
    obj.partner = obj.env["res.partner"].create({"name": "some customer"})
