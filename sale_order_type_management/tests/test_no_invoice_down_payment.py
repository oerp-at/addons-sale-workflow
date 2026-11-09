# Copyright 2026, Weboffice IT-Service und Marketing GmbH & Co KG

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestNoInvoiceDownPayment(TransactionCase):
    """Orders of a ``no_invoice`` type get no invoice from the invoicing
    wizard either: neither a down payment nor a regular invoice of a mixed
    selection."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Down Payment Partner"})
        cls.product = cls.env["product.product"].create(
            {
                "name": "Down payment test product",
                "type": "service",
                "invoice_policy": "order",
                "list_price": 100.0,
            }
        )
        cls.no_invoice_type = cls.env["sale.order.type"].create(
            {"name": "No Invoice Type", "no_invoice": True}
        )
        cls.plain_type = cls.env["sale.order.type"].create({"name": "Plain Type"})

    def _confirmed_order(self, order_type):
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "type_id": order_type.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                            "price_unit": 100.0,
                        }
                    )
                ],
            }
        )
        order.action_confirm()
        return order

    def _wizard(self, orders, **values):
        return (
            self.env["sale.advance.payment.inv"]
            .with_context(
                active_model="sale.order",
                active_ids=orders.ids,
                active_id=orders[:1].id,
            )
            .create(values)
        )

    def _assert_nothing_invoiced(self, order):
        self.assertFalse(order.invoice_ids, f"{order.name} must not be invoiced.")
        self.assertFalse(
            order.order_line.filtered("is_downpayment"),
            f"{order.name} must not get down payment lines.",
        )

    def test_down_payment_blocked(self):
        order = self._confirmed_order(self.no_invoice_type)
        for values in (
            {"advance_payment_method": "percentage", "amount": 30.0},
            {"advance_payment_method": "fixed", "fixed_amount": 50.0},
        ):
            with self.subTest(method=values["advance_payment_method"]):
                wizard = self._wizard(order, **values)
                with self.assertRaisesRegex(UserError, order.name):
                    wizard.create_invoices()
                # Code calling the wizard's business method directly is
                # stopped by the order itself.
                with self.assertRaisesRegex(UserError, order.name):
                    wizard._create_invoices(order)
                self._assert_nothing_invoiced(order)

    def test_down_payment_order_hooks_blocked(self):
        """Modules rebuilding the down payment creation without calling the
        wizard's super still add the section and lines through the order,
        which refuses them."""
        order = self._confirmed_order(self.no_invoice_type)
        with self.assertRaisesRegex(UserError, order.name):
            order._create_down_payment_section_line_if_needed()
        with self.assertRaisesRegex(UserError, order.name):
            order._create_down_payment_lines_from_base_lines([])
        self._assert_nothing_invoiced(order)

    def test_mixed_selection_creates_nothing(self):
        blocked = self._confirmed_order(self.no_invoice_type)
        regular = self._confirmed_order(self.plain_type)
        wizard = self._wizard(blocked | regular, advance_payment_method="delivered")
        with self.assertRaises(UserError) as error:
            wizard.create_invoices()
        message = str(error.exception)
        self.assertIn(f"{blocked.name} ({self.no_invoice_type.name})", message)
        self.assertNotIn(regular.name, message)
        self._assert_nothing_invoiced(blocked)
        self._assert_nothing_invoiced(regular)

    def test_message_translated(self):
        if not self.env["res.lang"]._lang_get("de_DE"):
            self.skipTest("German is not installed.")
        order = self._confirmed_order(self.no_invoice_type)
        with self.assertRaisesRegex(UserError, "Keine Rechnung"):
            order.with_context(lang="de_DE")._check_no_invoice_order_type()

    def test_regular_order_still_invoiced(self):
        order = self._confirmed_order(self.plain_type)
        self._wizard(
            order, advance_payment_method="percentage", amount=30.0
        ).create_invoices()
        self.assertEqual(len(order.invoice_ids), 1)
        self.assertTrue(order.order_line.filtered("is_downpayment"))
        regular = self._confirmed_order(self.plain_type)
        self._wizard(regular, advance_payment_method="delivered").create_invoices()
        self.assertEqual(len(regular.invoice_ids), 1)
