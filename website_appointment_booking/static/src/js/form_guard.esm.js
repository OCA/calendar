/* Copyright 2026 ForgeFlow S.L.
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */

/**
 * Anti-abuse guard for the public forms of the booking page.
 *
 * When the website has a reCAPTCHA v3 site key, the first submit of a
 * guarded form is intercepted, a token for ``action`` is fetched and stored
 * in the ``recaptcha_token_response`` hidden input, then the form is
 * submitted for real. Without a site key the token stays empty and the
 * server skips the verification (``ir.http`` returns True), so the guard is
 * a no-op there. The honeypot input needs no JS at all.
 */

/* eslint-env browser */
import {ReCaptcha} from "@google_recaptcha/js/recaptcha";

export class FormGuard {
    /**
     * @param {String} action reCAPTCHA action name, must match the server
     */
    constructor(action) {
        this.action = action;
        this.recaptcha = new ReCaptcha();
        this.enabled = Boolean(this.recaptcha.loadLibs());
    }

    /**
     * @param {HTMLFormElement} form
     */
    attach(form) {
        if (!form || form.dataset.wabGuarded || !this.enabled) {
            return;
        }
        form.dataset.wabGuarded = "1";
        form.addEventListener("submit", (ev) => this._onSubmit(ev, form));
    }

    async _onSubmit(ev, form) {
        const input = form.querySelector("input[name='recaptcha_token_response']");
        if (!input || input.value) {
            return;
        }
        ev.preventDefault();
        const result = await this.recaptcha.getToken(this.action);
        input.value = result.token || "";
        // The submit event only fires once native validation passed, and a
        // programmatic submit does not re-trigger this listener.
        HTMLFormElement.prototype.submit.call(form);
    }
}
