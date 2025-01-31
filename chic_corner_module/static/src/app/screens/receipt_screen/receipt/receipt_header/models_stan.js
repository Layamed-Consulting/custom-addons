/** @odoo-module */
import { Order } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";

patch(Order.prototype, {
    setup(_defaultObj, options) {
        super.setup(...arguments);
        this.cheque_date = this.cheque_date || null;
    },
    init_from_JSON(json) {
        this.set_cheque_date(json.cheque_date);
        super.init_from_JSON(...arguments);
    },
    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        if (json) {

            json.cheque_date = this.get_cheque_date();
        }
        return json;
    },
    set_cheque_date(cheque_date) {
        this.cheque_date = cheque_date;
    },
     get_cheque_date() {
        return this.cheque_date;
    },

});
