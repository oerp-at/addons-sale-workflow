# Copyright 2026, Weboffice IT-Service und Marketing GmbH & Co KG

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    migration_order_type_id = fields.Many2one(
        "sale.order.type",
        string="Migration Type",
        domain='[("id", "in", possible_migration_order_type_ids)]',
    )

    possible_migration_order_type_ids = fields.Many2many(
        "sale.order.type", related="type_id.migration_order_type_ids", readonly=True
    )

    order_type_no_invoice = fields.Boolean(related="type_id.no_invoice", readonly=True)
    order_type_no_delivery = fields.Boolean(
        related="type_id.no_delivery", readonly=True
    )

    source_sale_order_id = fields.Many2one("sale.order", "Source Order")

    migrated_sale_order_ids = fields.One2many(
        "sale.order", "source_sale_order_id", "Migrated Sale Orders"
    )
    migrated_sale_order_count = fields.Integer(
        compute="_compute_migrated_sale_order_count"
    )

    available_template_ids = fields.Many2many(
        comodel_name="sale.order.template",
        compute="_compute_available_template_ids",
    )

    @api.depends("migrated_sale_order_ids")
    def _compute_migrated_sale_order_count(self):
        for rec in self:
            rec.migrated_sale_order_count = len(rec.migrated_sale_order_ids)

    def _create_invoices(self, final=False, grouped=False):
        # A sale order type flagged ``no_invoice`` must not produce invoices
        # on any path (wizard, list action, programmatic), not only by hiding
        # the form buttons.
        allowed = self.filtered(lambda o: not o.type_id.no_invoice)
        if not allowed:
            return self.env["account.move"]
        return super(SaleOrder, allowed)._create_invoices(final=final, grouped=grouped)

    @api.onchange("type_id")
    def _onchange_type_id(self):
        if (not self.sale_order_template_id and self.type_id.default_template_id) or (
            self.sale_order_template_id
            and self.sale_order_template_id not in self.type_id.available_template_ids
        ):
            self.sale_order_template_id = self.type_id.default_template_id
            self._onchange_sale_order_template_id()
        if not self.possible_migration_order_type_ids or (
            self.migration_order_type_id
            and self.migration_order_type_id
            not in self.possible_migration_order_type_ids
        ):
            self.migration_order_type_id = False

    def action_migrate_sale_order(self):
        self.ensure_one()

        sale_order_id = self.copy(
            {
                "type_id": self.migration_order_type_id.id,
                "sale_order_template_id": self.migration_order_type_id.default_template_id.id,
                "migration_order_type_id": False,
                "source_sale_order_id": self.id,
            }
        )
        sale_order_id._onchange_sale_order_template_id()

        self.migrated_sale_order_ids += sale_order_id

        self.message_post(
            body=self.env._(
                "Migrated Sale Order: %s",
                sale_order_id._get_html_link(title=sale_order_id.name),
            ),
            message_type="comment",
        )
        sale_order_id.message_post(
            body=self.env._(
                "Sale Order migrated from: %s", self._get_html_link(title=self.name)
            ),
            message_type="comment",
        )

        return {
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "res_id": sale_order_id.id,
            "view_mode": "form",
        }

    def action_view_source_order(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "res_id": self.source_sale_order_id.id,
            "view_mode": "form",
        }

    def action_view_migrated_orders(self):
        self.ensure_one()
        action = {
            "res_model": "sale.order",
            "type": "ir.actions.act_window",
        }
        if len(self.migrated_sale_order_ids) == 1:
            action.update(
                {
                    "view_mode": "form",
                    "res_id": self.migrated_sale_order_ids.id,
                }
            )
        else:
            action.update(
                {
                    "name": self.env._("Migrated Sale Orders"),
                    "domain": [("id", "in", self.migrated_sale_order_ids.ids)],
                    "view_mode": "list,form",
                }
            )
        return action

    @api.depends("type_id", "type_id.available_template_ids", "company_id")
    def _compute_available_template_ids(self):
        for rec in self:
            if rec.type_id and rec.type_id.template_ids:
                rec.available_template_ids = rec.type_id.template_ids
            else:
                rec.available_template_ids = self.env["sale.order.template"].search(
                    [
                        "|",
                        ("company_id", "=", False),
                        ("company_id", "parent_of", rec.company_id.id),
                    ]
                )
