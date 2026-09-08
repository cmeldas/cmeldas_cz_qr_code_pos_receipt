# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class PosPayment(models.Model):
    _inherit = "pos.payment"

    qr_code = fields.Char(
        string="QR Code Data",
        help="Base64 encoded QR code for this payment",
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Generate QR code when payment is created if payment method supports it."""
        payments = super().create(vals_list)
        
        for payment in payments:
            if payment.qr_code:
                # QR už poslala pokladna (uložila si ho při zobrazení popupu)
                continue
            if payment.payment_method_id and payment.payment_method_id.qr_code_method:
                # Get the order to retrieve necessary information
                order = payment.pos_order_id
                if order:
                    try:
                        qr_code_data = payment.payment_method_id.get_qr_code(
                            amount=payment.amount,
                            free_communication=order.name or "",
                            structured_communication="",
                            currency=order.currency_id.id,
                            debtor_partner=order.partner_id.id if order.partner_id else False,
                        )
                        if qr_code_data:
                            payment.qr_code = qr_code_data
                    except Exception as e:
                        # Log error but don't block payment creation
                        payment.env['ir.logging'].sudo().create({
                            'name': 'pos.payment',
                            'type': 'server',
                            'level': 'warning',
                            'message': f'Failed to generate QR code for payment {payment.id}: {str(e)}',
                            'path': 'pos_payment',
                            'func': 'create',
                            'line': '0',
                        })
        
        return payments
