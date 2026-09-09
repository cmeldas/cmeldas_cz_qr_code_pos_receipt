import { PosStore } from "@point_of_sale/app/services/pos_store";
import { QRPopup } from "@point_of_sale/app/components/popups/qr_code_popup/qr_code_popup";
import { ask } from "@point_of_sale/app/utils/make_awaitable_dialog";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { ConnectionLostError } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";

/**
 * QR platba v pokladně: zpráva s číslem objednávky a uložení QR pro účtenku.
 *
 * Odoo 19 posílá do zprávy `pos_order_id.name`, které u nové objednávky v prohlížeči
 * není vyplněné (číslo objednávky je v `pos_reference`), takže v QR chybělo číslo
 * objednávky. Skládáme zprávu jako Odoo 18: "Order <pos_reference> <tracking_number>".
 *
 * Metoda nahrazuje původní showQR celou (ne přes super), aby popup i účtenka
 * používaly tentýž QR kód a server se volal jen jednou. Pole qr_code je skutečné
 * pole modelu pos.payment (definuje ho tento modul), s objednávkou se uloží na server
 * a je k dispozici i při opakovaném tisku.
 */
patch(PosStore.prototype, {
    czQrPaymentMessage(payment) {
        const order = payment.pos_order_id;
        const reference = order.pos_reference || order.name || "";
        return `Order ${reference} ${order.tracking_number || ""}`.trim();
    },

    async showQR(payment) {
        let qr;
        try {
            qr = await this.data.call("pos.payment.method", "get_qr_code", [
                [payment.payment_method_id.id],
                payment.amount,
                this.czQrPaymentMessage(payment),
                "",
                this.currency.id,
                payment.pos_order_id.partner_id?.id,
            ]);
        } catch (error) {
            qr = payment.payment_method_id.default_qr;
            if (!qr) {
                let message;
                if (error instanceof ConnectionLostError) {
                    message = _t(
                        "Connection to the server has been lost. Please check your internet connection."
                    );
                } else {
                    message = error.data?.message || String(error);
                }
                this.env.services.dialog.add(AlertDialog, {
                    title: _t("Failure to generate Payment QR Code"),
                    body: message,
                });
                return false;
            }
        }
        payment.qr_code = qr;
        payment.qrPaymentData = {
            name: payment.payment_method_id.name,
            amount: this.env.utils.formatCurrency(payment.amount),
            qrCode: qr,
        };
        return await ask(
            this.env.services.dialog,
            {
                title: payment.name,
                line: payment,
                order: payment.pos_order_id,
                qrCode: qr,
            },
            {},
            QRPopup
        ).then((result) => {
            payment.qrPaymentData = null;
            return result;
        });
    },
});
