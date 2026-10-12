# -*- coding: utf-8 -*-
from odoo import _, models
from odoo.exceptions import UserError


class PosPaymentMethod(models.Model):
    _inherit = "pos.payment.method"

    def get_qr_code_image(self, amount, free_communication, structured_communication, currency, debtor_partner):
        """Obrázek QR kódu platby (data URI PNG) pro popup v pokladně i pro účtenku.

        Odoo 19 mělo ``get_qr_code`` s obrázkem z backendu; Odoo 20 vrací jen surovou hodnotu
        (``get_qr_code_value``) a obrázek kreslí prohlížeč jako SVG (přes 24 kB i u QR bez částky). Účtenka
        ale obrázek ukládá k platbě, proto ho dál generuje server stejně jako v 19: PNG
        z ``res.partner.bank.build_qr_code_base64`` se stejným řetězcem SPD jako hodnota pro jádro.
        """
        self.ensure_one()
        if self.payment_method_type != "bank_qr_code" or not self.qr_code_method:
            raise UserError(_("This payment method is not configured to generate QR codes."))
        payment_bank = self.journal_id.bank_account_id
        debtor_partner = self.env["res.partner"].browse(debtor_partner)
        currency = self.env["res.currency"].browse(currency)

        return payment_bank.with_context(is_online_qr=True).build_qr_code_base64(
            float(amount), free_communication, structured_communication, currency, debtor_partner,
            self.qr_code_method, silent_errors=False,
        )
