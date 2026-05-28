import {registry} from "@web/core/registry";

registry.category("web_tour.tours").add("resource_booking_ptl_tour", {
    url: "/my",
    steps: () => [
        {
            content: "Go /my/bookings url",
            trigger: 'a[href*="/my/bookings"]',
            run: "click",
            // Navigates to /my/bookings
            expectUnloadPage: true,
        },
        {
            content: "There are currently no bookings for your account.",
            trigger: "p",
        },
    ],
});

registry.category("web_tour.tours").add("resource_booking_ptl2_tour", {
    url: "/my",
    steps: () => [
        {
            content: "Go /my/bookings url",
            trigger: 'a[href*="/my/bookings"]',
            run: "click",
            // Navigates to /my/bookings
            expectUnloadPage: true,
        },
        {
            content: "Go to Booking item",
            trigger: ".tr_resource_booking_link:eq(0)",
            run: "click",
            // Navigates to booking detail
            expectUnloadPage: true,
        },
        {
            content: "Schedule button",
            trigger: ".badge:contains('Pending')",
            run: "click",
        },
    ],
});
