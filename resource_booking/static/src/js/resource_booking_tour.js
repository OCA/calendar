odoo.define("resource_booking.tour", function (require) {
    "use strict";

    var tour = require("web_tour.tour");

    tour.register(
        "resource_booking_ptl_tour",
        {
            test: true,
            url: "/my",
        },
        [
            {
                content: "Go /my/bookings url",
                trigger: 'a[href*="/my/bookings"]',
            },
            {
                content: "There are currently no bookings for your account.",
                trigger: "p",
            },
        ]
    );
    tour.register(
        "resource_booking_ptl2_tour",
        {
            test: true,
            url: "/my",
        },
        [
            {
                content: "Go /my/bookings url",
                trigger: 'a[href*="/my/bookings"]',
            },
            {
                content: "Go to Booking item",
                trigger: ".tr_resource_booking_link:eq(0)",
            },
            {
                content: "Schedule button",
                trigger: ".badge:contains('Pending')",
            },
        ]
    );
});
