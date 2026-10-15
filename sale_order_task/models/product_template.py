# Copyright 2026, Weboffice IT-Service und Marketing GmbH & Co KG

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    service_tracking = fields.Selection(
        selection_add=[
            ("so_project_task_templates", "Merge Task/Project"),
        ],
        ondelete={"so_project_task_templates": "set default"},
    )

    so_task_template_id = fields.Many2one(
        "project.task",
        "Merge Task Template",
        copy=True,
        domain=["|", ("project_id.is_template", "=", True), ("is_template", "=", True)],
    )
