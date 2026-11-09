# Copyright 2026, Weboffice IT-Service und Marketing GmbH & Co KG

from odoo import models


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def create_invoices(self):
        # The whole selection is refused when it holds an order whose type
        # forbids invoicing; ``sale.order._create_invoices`` alone would
        # silently skip it and invoice the rest.
        self.sale_order_ids._check_no_invoice_order_type()
        return super().create_invoices()
