# -*- coding: utf-8 -*-
# Copyright 2026, Weboffice IT-Service und Marketing GmbH & Co KG

from odoo import models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # Prevent creation of delivery when sale order type has 'no delivery' checked
    def _action_launch_stock_rule(self, **kwargs):
        return super(SaleOrderLine, self.filtered(
            lambda r: not r.order_id.type_id.no_delivery
        ))._action_launch_stock_rule(**kwargs)
