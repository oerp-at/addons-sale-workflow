# -*- coding: utf-8 -*-
# Copyright 2026, Weboffice IT-Service und Marketing GmbH & Co KG

from odoo import models, fields


class SaleOrderTypology(models.Model):
    _inherit = "sale.order.type"

    project_template_id = fields.Many2one(
        'project.project', 'Project Template',
        domain='[("is_template", "=", True)]',
        help='Project Template that will be created on Sale Order Confirmation',
    )
    optional_task_ids = fields.Many2many('project.task', string='Optional Tasks to include')
