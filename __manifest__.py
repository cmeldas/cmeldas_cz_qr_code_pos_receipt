# -*- coding: utf-8 -*-
{
    "name": "Cmeldas: CZ QR Code on POS Receipt copy",
    "category": "Point of Sale",
    "summary": "Print Czech QR codes on POS receipts for QR payment methods",
    "description": "Extends POS receipts to display QR codes for Czech payment methods that generate QR codes.",
    "version": "19.0.1.1.0",
    "website": "https://github.com/cmeldas",
    "author": "cmeldas",
    "depends": [
        "point_of_sale",
        "cz_qr_payment",
    ],
    "data": [
        "security/ir.model.access.csv",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "cmeldas_cz_qr_code_pos_receipt/static/src/app/order_model_ext.js",
            "cmeldas_cz_qr_code_pos_receipt/static/src/app/order_receipt.xml",
        ],
    },
    "license": "LGPL-3",
    "installable": True,
    "application": False,
    "auto_install": False,
}
