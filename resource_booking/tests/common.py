# Copyright 2021 Tecnativa - Jairo Llopis
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import Command


def create_test_data(obj):
    """Create test data for a case."""
    obj.env = obj.env(
        context=dict(
            obj.env.context, tracking_disable=True, no_reset_password=True, tz="UTC"
        )
    )
    # Create one resource.calendar available on Mondays, another one on
    # Tuesdays, and another one on Mondays and Tuesdays; in that order.
    # Also create an all-day calendar for Saturday and Sunday.
    attendances = [
        Command.create(
            {
                "dayofweek": "0",
                "hour_from": 8,
                "hour_to": 17,
                "day_period": "morning",
            },
        ),
        Command.create(
            {
                "dayofweek": "1",
                "hour_from": 8,
                "hour_to": 17,
                "day_period": "morning",
            },
        ),
        Command.create(
            {
                "dayofweek": "4",
                "hour_from": 0,
                "hour_to": 24,
                "day_period": "morning",
            },
        ),
        Command.create(
            {
                "dayofweek": "5",
                "hour_from": 0,
                "hour_to": 24,
                "day_period": "morning",
            },
        ),
        Command.create(
            {
                "dayofweek": "6",
                "hour_from": 0,
                "hour_to": 24,
                "day_period": "morning",
            },
        ),
    ]
    obj.r_calendars = obj.env["resource.calendar"].create(
        [
            {"name": "Mon", "attendance_ids": [attendances[0]]},
            {"name": "Tue", "attendance_ids": [attendances[1]]},
            {"name": "MonTue", "attendance_ids": attendances[0:2]},
            {"name": "FriSun", "attendance_ids": attendances[2:]},
        ]
    )
    # Create one material resource for each of those calendars; same order
    obj.r_materials = obj.env["resource.resource"].create(
        [
            {
                "name": f"Material resource for {cal.name}",
                "calendar_id": cal.id,
                "resource_type": "material",
            }
            for cal in obj.r_calendars
        ]
    )
    # Create one human resource for each of those calendars; same order
    obj.users = obj.env["res.users"].create(
        [
            {
                "email": f"user_{num}@example.com",
                "login": f"user_{num}",
                "name": f"User {num}",
            }
            for num, _ in enumerate(obj.r_calendars)
        ]
    )
    obj.r_users = obj.env["resource.resource"].create(
        [
            {
                "calendar_id": cal.id,
                "name": f"User {user.name}",
                "resource_type": "user",
                "user_id": user.id,
            }
            for (user, cal) in zip(obj.users, obj.r_calendars, strict=True)
        ]
    )
    # Create one RBC for each of those calendars, which includes the
    # corresponding material and human resources simultaneously; same order
    obj.rbcs = obj.env["resource.booking.combination"].create(
        [
            {"resource_ids": [Command.set([user.id, material.id])]}
            for (user, material) in zip(obj.r_users, obj.r_materials, strict=True)
        ]
    )
    # Create one RBT that includes all RBCs as available combinations
    obj.rbt = obj.env["resource.booking.type"].create(
        {
            "name": "Test resource booking type",
            "combination_rel_ids": [
                Command.create({"sequence": num, "combination_id": rbc.id})
                for num, rbc in enumerate(obj.rbcs)
            ],
            "resource_calendar_id": obj.r_calendars[2].id,
            "location": "Main office",
            "videocall_location": "Videocall Main office",
        }
    )
    # Create some partner
    obj.partner = obj.env["res.partner"].create({"name": "some customer"})
