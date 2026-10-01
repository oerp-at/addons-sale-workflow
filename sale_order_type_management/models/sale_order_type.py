# Copyright 2026, Weboffice IT-Service und Marketing GmbH & Co KG

from odoo import api, fields, models


class SaleOrderTypology(models.Model):
    _inherit = "sale.order.type"

    no_invoice = fields.Boolean(
        help="Prevents creation of invoice out of the sale order"
    )
    no_delivery = fields.Boolean(
        help="Prevents the creation of deliveries when confirming the sale order"
    )

    template_ids = fields.Many2many(
        string="Available Sale Order Templates",
        comodel_name="sale.order.template",
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="The templates which are available for this sale order type. If none are selected, all templates are available.",
    )

    default_template_id = fields.Many2one(
        string="Default Template",
        comodel_name="sale.order.template",
        help="The default template for the sale order if this type is selected",
    )

    available_template_ids = fields.Many2many(
        comodel_name="sale.order.template",
        compute="_compute_available_template_ids",
    )

    migration_order_type_ids = fields.Many2many(
        string="Available for Migration",
        comodel_name="sale.order.type",
        relation="sale_order_type_migration_order_type_rel",
        column1="original_order_type_id",
        column2="migration_order_type_id",
        help="The types which are available for migration",
    )

    @api.depends("template_ids", "company_id")
    def _compute_available_template_ids(self):
        for rec in self:
            if rec.template_ids:
                rec.available_template_ids = rec.template_ids
            else:
                rec.available_template_ids = self.env["sale.order.template"].search(
                    [
                        "|",
                        ("company_id", "=", False),
                        ("company_id", "parent_of", rec.company_id.id),
                    ]
                )
