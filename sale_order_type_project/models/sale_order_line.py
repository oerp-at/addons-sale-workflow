# Copyright 2026, Weboffice IT-Service und Marketing GmbH & Co KG

from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _so_task_template_create_task(self, project, template_tasks):
        task_ids = super()._so_task_template_create_task(project, template_tasks)
        # The base implementation already dropped dependency links crossing out
        # of the project. For optional tasks merged after the project exists,
        # rebuild their dependencies against the project's own tasks.
        (
            task_ids | task_ids._get_all_subtasks()
        )._reconstruct_optional_template_dependencies()
        return task_ids

    def _get_task_template_so_lines(self, so):
        # If there is a sale order type project and the so line's task is an optional line in this project, it was
        # already created with the creation of the project, so we filter those out
        so_lines = super()._get_task_template_so_lines(so)
        if so.type_id.project_template_id:
            optional_tasks = so.type_id.project_template_id.task_ids.filtered(
                lambda t: t.optional_task
            )
            so_lines = so_lines.filtered(
                lambda line: line.product_id.so_task_template_id not in optional_tasks
            )
        return so_lines
