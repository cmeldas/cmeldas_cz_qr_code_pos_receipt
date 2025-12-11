/** @odoo-module */
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch";

/**
 * Patch PosStore to save QR code before the popup closes
 */
patch(PosStore.prototype, {
    async showQR(payment) {
        // Call the original showQR which sets qrPaymentData and then clears it
        // We need to get the QR code from the same source and save it
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
        } catch (error) {
            qr = payment.payment_method_id.default_qr;
        }
        
        // Save the QR code on the payment object for later use in receipt
        if (qr) {
            payment.savedQrCode = qr;
        }
        
        // Now call the original method
        return await super.showQR(payment);
    }
});

/**
 * Extend PosOrder to include QR codes in payment lines for receipt printing
 */
patch(PosOrder.prototype, {
    /**
     * Override export_for_printing to include QR code in payment lines
     */
    export_for_printing(baseUrl, headerData) {
        const result = super.export_for_printing(baseUrl, headerData);
        
        // Enhance paymentlines with QR code if available
        if (result.paymentlines && this.payment_ids) {
            // payment_ids may be filtered (no change payments), so we need to match properly
            const paymentData = this.payment_ids.filter((p) => !p.is_change);
            
            for (let i = 0; i < result.paymentlines.length && i < paymentData.length; i++) {
                const payment = paymentData[i];
                // Check if payment has savedQrCode (saved before popup closed)
                if (payment && payment.savedQrCode) {
                    result.paymentlines[i].qr_code = payment.savedQrCode;
                }
            }
        }
        
        return result;
    }
});
