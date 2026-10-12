# -*- coding: utf-8 -*-
"""Migrace 19 → 20 před načtením dat modulu.

1. Přístupová práva: Odoo 20 nahradilo ``ir.model.access`` modelem ``ir.access``. Modul
   načítá ``security/ir.access.csv`` se stejnými XML ID (``access_pos_payment_user``,
   ``access_pos_payment_manager``). Kdyby XML ID v ``ir_model_data`` ukazovala dál na starý
   model, načtení spadne na „found record of different model ir.model.access“. Smažou se
   proto jen ta, která rámec migrace nepřevedl (model je pořád ``ir.model.access`` / ``ir.rule``);
   nové záznamy ``ir.access`` pak vzniknou znovu. Staré řádky ``ir_model_access`` zůstanou
   (rámec OpenUpgrade tabulky nemaže, model v 20 neexistuje).
2. Typ integrace platební metody: Odoo 19 ``payment_method_type = 'qr_code'`` je v Odoo 20
   ``'bank_qr_code'``. Bez převodu by pokladna QR metodu nepoznala (``useBankQrCode``) a QR
   by se neukázal ani nevytiskl. Převod patří do migrace ``point_of_sale``; tady jen pro jistotu
   a idempotentně.

Pole ``pos.payment.qr_code`` (obrázky QR uložené od roku 2024) převod nepotřebuje: Odoo 20
ho definuje samo ve stejném sloupci ``qr_code`` (varchar).
"""
import logging

from odoo.tools.sql import column_exists

_logger = logging.getLogger(__name__)

MODULE = "cmeldas_cz_qr_code_pos_receipt"


def migrate(cr, version):
    if not version:
        return

    cr.execute(
        """
        DELETE FROM ir_model_data
         WHERE module = %s
           AND model IN ('ir.model.access', 'ir.rule')
        """,
        (MODULE,),
    )
    if cr.rowcount:
        _logger.info("%s: %s starých XML ID práv odpojeno (ir.model.access → ir.access)", MODULE, cr.rowcount)

    if column_exists(cr, "pos_payment_method", "payment_method_type"):
        cr.execute(
            """
            UPDATE pos_payment_method
               SET payment_method_type = 'bank_qr_code'
             WHERE payment_method_type = 'qr_code'
            """
        )
        if cr.rowcount:
            _logger.info("%s: %s platebních metod qr_code → bank_qr_code", MODULE, cr.rowcount)
