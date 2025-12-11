# -*- coding: utf-8 -*-
from odoo import models, api


class PosOrder(models.Model):
    _inherit = "pos.order"

    def _export_for_ui(self, order):
        """Add QR code data to order export for UI receipt."""
        result = super()._export_for_ui(order)
        
        # Add QR code to each payment line that has one
        if result.get('payment_ids') and order.payment_ids:
            payment_qr_codes = {p.id: p.qr_code for p in order.payment_ids if p.qr_code}
            
            for payment in result.get('payment_ids', []):
                payment_id = payment.get('id')
                if payment_id and payment_id in payment_qr_codes:
                    payment['qr_code'] = payment_qr_codes[payment_id]
        
        return result
