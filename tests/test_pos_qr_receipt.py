# -*- coding: utf-8 -*-
from odoo.tests import tagged

from odoo.addons.cmeldas_cz_qr_code_pos_receipt.models.pos_payment import qr_payment_message
from odoo.addons.point_of_sale.tests.common import TestPoSCommon

PNG_PREFIX = "data:image/png;base64,"


@tagged("post_install", "-at_install")
class TestPosQrReceipt(TestPoSCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config = cls.basic_config
        bank_journal = cls.company_data["default_journal_bank"]
        cls.bank_account = cls.env["res.partner.bank"].create({
            "account_number": "CZ38 2010 0000 0024 0183 5999",
            "partner_id": cls.company.partner_id.id,
        })
        bank_journal.bank_account_id = cls.bank_account
        cls.qr_pm = cls.env["pos.payment.method"].create({
            "name": "QR",
            "type": "bank",
            "journal_id": bank_journal.id,
            "payment_method_type": "bank_qr_code",
            "qr_code_method": "qr_czk",
            "receivable_account_id": cls.pos_receivable_bank.id,
            "outstanding_account_id": cls.outstanding_bank.id,
            "company_id": cls.env.company.id,
        })
        cls.config.write({"payment_method_ids": [(4, cls.qr_pm.id)]})
        cls.product = cls.create_product("Zmrzlina", cls.categ_basic, 50.0)

    def _sync_order(self, qr_code=None):
        order_data = self.create_ui_order_data(
            [(self.product, 1)],
            pos_order_ui_args={"pos_reference": "26A-1-000042", "tracking_number": "A12"},
            payments=[(self.qr_pm, 50.0)],
        )
        if qr_code:
            order_data["payment_ids"][0][2]["qr_code"] = qr_code
        result = self.env["pos.order"].sync_from_ui([order_data])
        return self.env["pos.order"].browse(result["pos.order"][0]["id"])

    def test_qr_code_image(self):
        """Obrázek pro popup a účtenku generuje server jako PNG (data URI) jako v Odoo 19."""
        image = self.qr_pm.get_qr_code_image(123.5, "Order 26A-1-000042 A12", "", self.company.currency_id.id, False)
        self.assertTrue(image.startswith(PNG_PREFIX))

    def test_qr_code_value_unchanged(self):
        """Hodnota pro jádro Odoo 20 (get_qr_code_value) je tentýž řetězec SPD."""
        value = self.qr_pm.get_qr_code_value(123.5, "Order 26A-1-000042 A12", "", self.company.currency_id.id, False)
        self.assertEqual(
            value,
            "SPD*1.0*ACC:CZ3820100000002401835999*AM:123.5*CC:%s*PT:IP*MSG:Order26A-1-000042A12"
            % self.company.currency_id.name,
        )
        # výchozí QR pro offline režim pokladny: bez částky a zprávy
        self.assertEqual(
            self.qr_pm.default_qr,
            "SPD*1.0*ACC:CZ3820100000002401835999*CC:%s*PT:IP" % self.company.currency_id.name,
        )

    def test_receipt_with_server_generated_qr(self):
        """Platba bez QR z pokladny dostane QR na serveru a ten je na účtence."""
        self.open_new_session()
        order = self._sync_order()
        payment = order.payment_ids.filtered(lambda p: p.payment_method_id == self.qr_pm)
        self.assertTrue(payment.qr_code and payment.qr_code.startswith(PNG_PREFIX))
        self.assertEqual(qr_payment_message(order), "Order 26A-1-000042 A12")

        html = str(order.order_receipt_generate_html())
        self.assertIn("pos-receipt-qr-code", html)
        self.assertIn(payment.qr_code, html)

    def test_qr_code_from_pos_is_kept(self):
        """QR, který poslala pokladna (stejný jako v popupu), se nepřepisuje."""
        self.open_new_session()
        qr_code = "data:image/svg+xml;base64,PHN2Zy8+"
        order = self._sync_order(qr_code=qr_code)
        self.assertEqual(order.payment_ids.qr_code, qr_code)

    def test_receipt_without_qr(self):
        """Bez QR platby účtenka žádný blok QR nemá."""
        self.open_new_session()
        order_data = self.create_ui_order_data([(self.product, 1)])
        result = self.env["pos.order"].sync_from_ui([order_data])
        order = self.env["pos.order"].browse(result["pos.order"][0]["id"])
        self.assertNotIn("pos-receipt-qr-code", str(order.order_receipt_generate_html()))
