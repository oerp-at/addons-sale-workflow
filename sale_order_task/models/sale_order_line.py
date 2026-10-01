# Copyright 2026, Weboffice IT-Service und Marketing GmbH & Co KG

from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _timesheet_service_generation(self):
        res = super()._timesheet_service_generation()

        service_template_lines = self.filtered(
            lambda sol: (
                sol.is_service
                and sol.product_id.service_tracking == "so_project_task_templates"
            )
        )

        if service_template_lines:
            so_ids = service_template_lines.mapped("order_id")
            for so in so_ids:
                project_id = so.project_id
                # If there already is a project for the sale order, we exclude those tasks when mirroring to avoid duplicates
                # Especially important for sale_order_type_project, where we create a project and its mirror tasks
                # before all the sale order lines
                exclude_mirror_task_ids = project_id.task_ids

                project_template_so_lines = self._get_project_template_so_lines(so)
                used_project_template_ids = []
                # If there is a project already, we merge the tasks of the project template into that project, otherwise
                # we create a project first if there is a project template line and then use that one for merging
                for sol in project_template_so_lines:
                    if not project_id:
                        project_id = sol.with_context(
                            copy_from_so_project_template=True
                        )._timesheet_create_project()
                        used_project_template_ids.append(
                            sol.product_id.project_template_id
                        )
                    elif (
                        sol.product_id.project_template_id
                        not in used_project_template_ids
                    ):
                        sol._so_task_template_create_task(
                            project_id,
                            sol.product_id.project_template_id.tasks.filtered(
                                lambda t: not t.parent_id
                            ),
                        )
                        used_project_template_ids.append(
                            sol.product_id.project_template_id
                        )
                task_template_so_lines = self._get_task_template_so_lines(so)
                for sol in task_template_so_lines:
                    if not project_id:
                        project_id = sol._timesheet_create_project()
                    else:
                        sol._so_task_template_create_task(
                            project_id, sol.product_id.so_task_template_id
                        )

                if project_id:
                    project_id.create_mirror_tasks(
                        exclude_task_ids=exclude_mirror_task_ids
                    )

        return res

    def _so_task_template_create_task(self, project, template_tasks):
        vals = self._prepare_so_task_template_vals(project)
        task_ids = template_tasks.with_context(
            copy_from_template=True,
        ).copy(vals)
        if len(task_ids) == 1:
            self.task_id = task_ids

        task_ids.map_copied_tasks(project)

        # Strip dependency links that still point at the template (or any other
        # project), so the merge never pollutes the template nor leaves the new
        # task depending on template tasks.
        (task_ids | task_ids._get_all_subtasks())._drop_external_dependencies()

        return task_ids

    def _prepare_so_task_template_vals(self, project):
        return {
            "project_id": project.id,
            "sale_line_id": self.id,
            "sale_order_id": self.order_id.id,
            "partner_id": self.order_id.partner_id.id,
        }

    def _get_project_template_so_lines(self, so):
        return so.order_line.filtered(
            lambda sol: (
                sol.product_id.service_tracking == "so_project_task_templates"
                and sol.product_id.project_template_id
            )
        )

    def _get_task_template_so_lines(self, so):
        return so.order_line.filtered(
            lambda sol: (
                sol.product_id.service_tracking == "so_project_task_templates"
                and sol.product_id.so_task_template_id
            )
        )
