# -*- coding: utf-8 -*-
# Copyright 2026, Weboffice IT-Service und Marketing GmbH & Co KG

from odoo import Command
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestSaleOrderTypeManagement(TransactionCase):
    def test_sale_order_type_management(self):
        first_template_id = self.env['sale.order.template'].create({'name': 'First Template'})
        second_template_id = self.env['sale.order.template'].create({'name': 'Second Template'})
        partner_id = self.env['res.partner'].create({'name': 'Test Partner'})

        first_sot_id = self.env['sale.order.type'].create({
            'name': 'First SOT',
            'default_template_id': first_template_id.id,
        })
        second_sot_id = self.env['sale.order.type'].create({
            'name': 'Second SOT',
            'default_template_id': second_template_id.id,
            'migration_order_type_ids': first_sot_id.ids,
            'no_delivery': True,
        })

        product_id = self.env['product.product'].create({
            'name': 'Test product',
            'type': 'consu',
            'is_storable': True,
            'invoice_policy': 'order',
        })

        so_id = self.env['sale.order'].create({
            'partner_id': partner_id.id,
            'type_id': second_sot_id.id,
        })
        so_id._onchange_type_id()
        self.assertEqual(so_id.sale_order_template_id, second_template_id)

        so_id.migration_order_type_id = first_sot_id
        so_id.order_line = [Command.create({
            'product_id': product_id.id,
            'price_unit': 10,
            'product_uom_qty': 5,
        })]
        so_id.action_confirm()
        self.assertEqual(so_id.delivery_count, 0)
        so_id.action_migrate_sale_order()

        migrated_so_id = self.env['sale.order'].search(
            [('source_sale_order_id', '=', so_id.id)]
        )
        self.assertEqual(so_id.migrated_sale_order_ids, migrated_so_id)
        self.assertEqual(migrated_so_id.sale_order_template_id, first_template_id)
        self.assertEqual(migrated_so_id.type_id, first_sot_id)
        self.assertEqual(migrated_so_id.source_sale_order_id, so_id)

        # The migrated order's stat buttons point at each other.
        source_action = migrated_so_id.action_view_source_order()
        self.assertEqual(source_action['res_id'], so_id.id)
        migrated_action = so_id.action_view_migrated_orders()
        self.assertEqual(migrated_action['res_id'], migrated_so_id.id)
        self.assertEqual(migrated_action['view_mode'], 'form')

    def test_no_invoice_blocks_invoice_creation(self):
        """A sale order type flagged ``no_invoice`` must not produce any
        invoice, even through ``_create_invoices`` directly."""
        partner = self.env['res.partner'].create({'name': 'No Invoice Partner'})
        product = self.env['product.product'].create({
            'name': 'Invoiceable product',
            'type': 'consu',
            'invoice_policy': 'order',
        })
        no_invoice_type = self.env['sale.order.type'].create({
            'name': 'No Invoice Type',
            'no_invoice': True,
        })
        plain_type = self.env['sale.order.type'].create({'name': 'Plain Type'})

        def _make_order(order_type):
            order = self.env['sale.order'].create({
                'partner_id': partner.id,
                'type_id': order_type.id,
                'order_line': [Command.create({
                    'product_id': product.id,
                    'price_unit': 10,
                    'product_uom_qty': 1,
                })],
            })
            order.action_confirm()
            return order

        no_invoice_order = _make_order(no_invoice_type)
        self.assertFalse(
            no_invoice_order._create_invoices(),
            "A no_invoice order must not create any invoice.",
        )

        normal_order = _make_order(plain_type)
        self.assertTrue(
            normal_order._create_invoices(),
            "A regular order must still create its invoice.",
        )

    def test_available_template_ids_explicit_and_fallback(self):
        """``available_template_ids`` returns the configured templates when
        set, and otherwise falls back to a company-scoped search (on both
        ``sale.order.type`` and ``sale.order``)."""
        template_one, template_two = self.env['sale.order.template'].create([
            {'name': 'Available Template One'},
            {'name': 'Available Template Two'},
        ])

        explicit_type = self.env['sale.order.type'].create({
            'name': 'Explicit Type',
            'template_ids': [Command.set((template_one | template_two).ids)],
        })
        self.assertEqual(
            explicit_type.available_template_ids, template_one | template_two
        )

        fallback_type = self.env['sale.order.type'].create({'name': 'Fallback Type'})
        # Fallback searches all templates of the company (and company-less);
        # the freshly created ones must be part of it.
        self.assertLessEqual(
            template_one | template_two, fallback_type.available_template_ids
        )

        partner = self.env['res.partner'].create({'name': 'Template Partner'})
        order = self.env['sale.order'].create({
            'partner_id': partner.id,
            'type_id': explicit_type.id,
        })
        self.assertEqual(
            order.available_template_ids, template_one | template_two
        )
