import { PosStore } from "@point_of_sale/app/services/pos_store";
import { patch } from "@web/core/utils/patch";

/**
 * Uloží QR kód platby na platební řádek, aby ho šlo vytisknout na účtence.
 *
 * Původní showQR si QR vyžádá ze serveru, ukáže popup a data zase zahodí.
 * Pole qr_code je skutečné pole modelu pos.payment (definuje ho tento modul),
 * takže se s objednávkou uloží na server a je k dispozici i při opakovaném tisku.
 */
patch(PosStore.prototype, {
    async showQR(payment) {
        let qr;
        try {
            qr = await this.data.call("pos.payment.method", "get_qr_code", [
                [payment.payment_method_id.id],
                payment.amount,
                payment.pos_order_id.name + " " + payment.pos_order_id.tracking_number,
                "",
                this.currency.id,
                payment.pos_order_id.partner_id?.id,
            ]);
        } catch {
            qr = payment.payment_method_id.default_qr;
        }
        if (qr) {
            payment.qr_code = qr;
        }
        return await super.showQR(payment);
    },
});
