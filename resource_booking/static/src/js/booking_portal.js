/** @odoo-module */

import publicWidget from "web.public.widget";
import "portal.portal"; // Force dependencies

publicWidget.registry.PortalHomeCounters.include({
    /**
     * @override
     */
    _getCountersAlwaysDisplayed() {
        return this._super(...arguments).concat(["booking_count"]);
    },
});
