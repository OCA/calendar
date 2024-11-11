/** @odoo-module **/
import {registry} from "@web/core/registry";

registry.category("web_tour.tours").add("resource_booking_ptl_tour", {
    url: "/my",
    test: true,
    steps: () => [
        {
            content: "Go /my/bookings url",
            trigger: 'a[href*="/my/bookings"]',
        },
        {
            content: "There are currently no bookings for your account.",
            trigger: "p",
        },
    ],
});

registry.category("web_tour.tours").add("resource_booking_ptl2_tour", {
    url: "/my",
    test: true,
    steps: () => [
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
    ],
});
