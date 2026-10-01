# Copyright 2026, Weboffice IT-Service und Marketing GmbH & Co KG

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    order_type_project_id = fields.Many2one("project.project")

    def _action_confirm(self):
        for order in self.sudo():
            if order.type_id and order.type_id.project_template_id:
                # If a project template is set in the sale order type, we create a
                # project for the sale order
                # independent of a sale order line
                order.with_company(order.company_id)._create_order_type_project()
        return super()._action_confirm()

    def _create_order_type_project(self):
        self.ensure_one()
        values = self._order_type_project_values()
        project_template = self.type_id.project_template_id
        values["name"] = self._get_so_project_name(values["name"], project_template)

        tasks_to_copy = self._handle_tasks_to_copy(project_template)
        project = project_template.action_create_from_template(values)

        self.env["project.project"].map_order_type_project_tasks(project, tasks_to_copy)

        # Set the partner on every task; ``sale_order_id`` is a stored
        # compute that follows ``project.reinvoiced_sale_order_id`` (set
        # via ``_order_type_project_values``), so we don't write it here.
        project.tasks.write(
            {
                "partner_id": self.partner_id.id,
            }
        )

        # Avoid new tasks to go to 'Undefined Stage'
        if not project.type_ids:
            project.type_ids = self.env["project.task.type"].create(
                [
                    {
                        "name": name,
                        "fold": fold,
                        "sequence": sequence,
                    }
                    for name, fold, sequence in [
                        (self.env._("To Do"), False, 5),
                        (self.env._("In Progress"), False, 10),
                        (self.env._("Done"), False, 15),
                        (self.env._("Cancelled"), True, 20),
                    ]
                ]
            )

        # Link the project to the sale order
        self.write(
            {
                "project_id": project.id,
                "order_type_project_id": project.id,
            }
        )

        # Drop dependency links still pointing at the template (or another
        # project) - e.g. towards optional tasks that were not included - and
        # rebuild optional tasks' dependencies against the project's own tasks.
        project.task_ids._drop_external_dependencies()
        project.task_ids._reconstruct_optional_template_dependencies()

        project.create_mirror_tasks()

    def _order_type_project_values(self):
        """Generate project values"""
        return {
            "name": f"{self.client_order_ref} - {self.name}"
            if self.client_order_ref
            else self.name,
            "account_id": self.env.context.get("project_account_id")
            or self.project_account_id.id
            or self.env["account.analytic.account"]
            .create(self._prepare_analytic_account_data())
            .id,
            "partner_id": self.partner_id.id,
            "active": True,
            "company_id": self.company_id.id,
            "allow_billable": True,
            "reinvoiced_sale_order_id": self.id,
            "user_id": self.type_id.project_template_id.user_id.id,
            "tasks": False,
        }

    def _get_so_project_name(self, name, project_template):
        return f"{name} - {project_template.name}"

    def _handle_tasks_to_copy(self, project):
        """Filter out optional tasks except for those defined in the sale order
        type or those that have a sale order line with this task as a template.
        """
        optional_tasks_to_include = self.type_id.optional_task_ids
        # Include optional tasks of individual sale order lines if they have a so task
        # template with the same project template id
        order_lines = self.order_line.filtered(
            lambda sol: (
                sol.product_id.service_tracking == "so_project_task_templates"
                and sol.product_id.so_task_template_id.project_id
                == self.type_id.project_template_id
            )
        )
        optional_tasks_to_include |= order_lines.product_id.mapped(
            "so_task_template_id"
        )
        tasks_to_copy = project.task_ids.filtered(
            lambda t: not t.optional_task or t in optional_tasks_to_include
        )
        tasks_to_copy |= tasks_to_copy._get_all_subtasks()
        return tasks_to_copy

    @api.depends(
        "order_type_project_id", "order_line.product_id", "order_line.project_id"
    )
    def _compute_project_ids(self):
        result = super()._compute_project_ids()
        for order in self:
            if order.order_type_project_id:
                # Add the order_type_project_id to the project_ids for the smart button
                order.project_ids |= order.order_type_project_id
                order.project_count = len(order.project_ids.filtered("active"))
        return result

    def action_view_project_ids(self):
        """
        Overwrite of the original method, except the check for order lines -
        otherwise empty lines meant you couldn't click the button to view your
        sale order project.
        """
        self.ensure_one()

        sorted_line = self.order_line.sorted("sequence")
        default_sale_line = next(
            (sol for sol in sorted_line if sol.product_id.type == "service"),
            self.env["sale.order.line"],
        )
        project_ids = self.project_ids
        partner = self.partner_shipping_id or self.partner_id
        if len(project_ids) == 1:
            action = (
                self.env["ir.actions.actions"]
                .with_context(
                    active_id=self.project_ids.id,
                )
                ._for_xml_id("project.act_project_project_2_project_task_all")
            )
            action["context"] = {
                "active_id": project_ids.id,
                "default_partner_id": partner.id,
                "default_project_id": self.project_ids.id,
                "default_sale_line_id": default_sale_line.id,
                "default_user_ids": [self.env.uid],
                "search_default_sale_order_id": self.id,
            }
            return action
        else:
            action = self.env["ir.actions.actions"]._for_xml_id(
                "project.open_view_project_all"
            )
            action["domain"] = [
                "|",
                ("sale_order_id", "=", self.id),
                ("id", "in", project_ids.ids),
            ]
            action["context"] = {
                **self.env.context,
                "default_partner_id": partner.id,
                "default_reinvoiced_sale_order_id": self.id,
                "default_sale_line_id": default_sale_line.id,
                "default_allow_billable": 1,
                "from_sale_order_action": True,
            }
            return action
