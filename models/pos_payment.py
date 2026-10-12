# -*- coding: utf-8 -*-
import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


def qr_payment_message(order):
    """Zpráva pro příjemce jako v pokladně: ``Order <pos_reference> <tracking_number>``."""
    if order.pos_reference:
        return f"Order {order.pos_reference} {order.tracking_number or ''}".strip()
    return order.name or ""


class PosPayment(models.Model):
    _inherit = "pos.payment"

    # Pole ``qr_code`` (obrázek QR jako data URI) má od Odoo 20 přímo point_of_sale ve stejném
    # sloupci, jaký dřív zakládal tento modul. Jádro ho ale po zavření popupu maže; pokladna
    # s tímto modulem ho nechává vyplněné, aby se QR vytiskl na účtenku (viz order_model_ext.js).

    @api.model_create_multi
    def create(self, vals_list):
        """Doplní QR kód platbám QR metodou, které ho z pokladny nedostaly."""
        payments = super().create(vals_list)

        for payment in payments:
            if payment.qr_code:
                # QR už poslala pokladna (uložila si ho při zobrazení popupu)
                continue
            method = payment.payment_method_id
            order = payment.pos_order_id
            if not order or method.payment_method_type != "bank_qr_code" or not method.qr_code_method:
                continue
            try:
                payment.qr_code = method.get_qr_code_image(
                    payment.amount,
                    qr_payment_message(order),
                    "",
                    order.currency_id.id,
                    order.partner_id.id,
                )
            except Exception as error:  # noqa: BLE001 – QR nesmí zablokovat uložení platby
                _logger.warning("Failed to generate QR code for payment %s: %s", payment.id, error)
                payment.env["ir.logging"].sudo().create({
                    "name": "pos.payment",
                    "type": "server",
                    "level": "warning",
                    "message": f"Failed to generate QR code for payment {payment.id}: {error}",
                    "path": "pos_payment",
                    "func": "create",
                    "line": "0",
                })

        return payments
