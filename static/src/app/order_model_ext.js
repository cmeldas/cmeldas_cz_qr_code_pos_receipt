import { PosStore } from "@point_of_sale/app/services/pos_store";
import { QRPopup } from "@point_of_sale/app/components/popups/qr_code_popup/qr_code_popup";
import { ask } from "@point_of_sale/app/utils/make_awaitable_dialog";
import { generateQRCodeDataUrl } from "@point_of_sale/utils";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { ConnectionLostError } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";

/**
 * QR platba v pokladně: zpráva s číslem objednávky a uložení QR pro účtenku.
 *
 * Odoo 20 posílá do zprávy `pos_order_id.name`, které u nové objednávky v prohlížeči
 * není vyplněné ("/", číslo objednávky je v `pos_reference`), takže v QR chybělo číslo
 * objednávky. Skládáme zprávu jako Odoo 18: "Order <pos_reference> <tracking_number>".
 *
 * Metoda nahrazuje showQR jádra celou (ne přes super), aby popup i účtenka používaly
 * tentýž QR kód a server se volal jen jednou. Obrázek (PNG jako data URI) vrací server
 * (`pos.payment.method.get_qr_code_image`, viz Python), uloží se do pole `qr_code` platby
 * a s objednávkou na server; účtenka (šablona `point_of_sale.pos_order_receipt`) ho čte
 * z dat platby, takže je i při opakovaném tisku. Jádro 20 `qr_code` po zavření popupu maže,
 * tady zůstává. Bez spojení se použije výchozí QR metody bez částky (`default_qr`,
 * v Odoo 20 surová hodnota SPD), který vykreslí prohlížeč.
 */
patch(PosStore.prototype, {
    czQrPaymentMessage(payment) {
        const order = payment.pos_order_id;
        const reference = order.pos_reference || (order.name !== "/" && order.name) || "";
        return `Order ${reference} ${order.tracking_number || ""}`.trim();
    },

    async showQR(payment) {
        if (this.currency.isZero(payment.amount)) {
            this.notification.add(_t("Can't create a QR for a zero amount"), { type: "warning" });
            return false;
        }
        payment.setPaymentStatus("waiting");
        let qr;
        try {
            qr = await this.data.call("pos.payment.method", "get_qr_code_image", [
                [payment.payment_method_id.id],
                payment.amount,
                this.czQrPaymentMessage(payment),
                "",
                this.currency.id,
                payment.pos_order_id.partner_id?.id || false,
            ]);
        } catch (error) {
            const defaultValue = payment.payment_method_id.default_qr;
            if (!defaultValue) {
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
            qr = generateQRCodeDataUrl(defaultValue);
        }
        payment.qr_code = qr;
        return await ask(this.env.services.dialog, payment.getQrPopupProps(), {}, QRPopup);
    },
});
