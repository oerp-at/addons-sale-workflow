# Copyright 2026, Weboffice IT-Service und Marketing GmbH & Co KG

from odoo.fields import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestSaleOrderTypeProject(TransactionCase):
    def test_sale_order_task(self):
        # Project for mirror tasks
        mirror_project = self.env["project.project"].create(
            {
                "name": "Mirror Project",
            }
        )

        # Project Templates
        project_template_one, project_template_two = self.env["project.project"].create(
            [
                {
                    "name": "Project Template One",
                    "allow_task_dependencies": True,
                    "is_template": True,
                },
                {
                    "name": "Project Template Two",
                    "allow_task_dependencies": True,
                    "is_template": True,
                },
            ]
        )

        # Parent tasks for first project template
        task_one, task_two, task_three, task_four = self.env["project.task"].create(
            [
                {
                    "name": "Project One Task One",
                    "project_id": project_template_one.id,
                    "optional_task": True,
                },
                {
                    "name": "Project One Task Two",
                    "project_id": project_template_one.id,
                    "mirror_project_id": mirror_project.id,
                    "optional_task": True,
                },
                {
                    "name": "Project One Task Three",
                    "project_id": project_template_one.id,
                    "optional_task": True,
                },
                {
                    "name": "Project One Task Four",
                    "project_id": project_template_one.id,
                    "mirror_project_id": mirror_project.id,
                },
            ]
        )

        # Dependencies
        task_three.depend_on_ids = task_two
        task_four.depend_on_ids = task_three

        # Subtasks of task four in project one
        subtask_one, _subtask_two = self.env["project.task"].create(
            [
                {
                    "name": "Subtask One",
                    "project_id": project_template_one.id,
                    "parent_id": task_four.id,
                },
                {
                    "name": "Subtask Two",
                    "project_id": project_template_one.id,
                    "parent_id": task_four.id,
                },
            ]
        )

        # Subtask of subtask
        self.env["project.task"].create(
            {
                "name": "Sub-sub Task",
                "project_id": project_template_one.id,
                "parent_id": subtask_one.id,
            }
        )

        # Tasks for second project template
        self.env["project.task"].create(
            [
                {
                    "name": "Project Two Task One",
                    "project_id": project_template_two.id,
                },
                {
                    "name": "Project Two Task Two",
                    "project_id": project_template_two.id,
                    "mirror_project_id": mirror_project.id,
                },
            ]
        )

        # Sale order type with SOT project and an optional task
        sale_order_type = self.env["sale.order.type"].create(
            {
                "name": "Sale Order Type",
                "project_template_id": project_template_one.id,
                "optional_task_ids": task_one.ids,
            }
        )

        # Products, one with a project to merge, one with an optional task
        product_one, product_two = self.env["product.product"].create(
            [
                {
                    "name": "Product One",
                    "type": "service",
                    "service_tracking": "so_project_task_templates",
                    "project_template_id": project_template_two.id,
                },
                {
                    "name": "Product Two",
                    "type": "service",
                    "service_tracking": "so_project_task_templates",
                    "so_task_template_id": task_three.id,
                },
            ]
        )

        res_partner = self.env["res.partner"].create({"name": "Max Megaman"})

        # Sale Order with sale order type that has a project set
        sale_order = self.env["sale.order"].create(
            {
                "name": "Test Sale Order",
                "partner_id": res_partner.id,
                "type_id": sale_order_type.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": product_one.id,
                        }
                    ),
                    Command.create(
                        {
                            "product_id": product_two.id,
                        }
                    ),
                ],
            }
        )

        sale_order.action_confirm()

        self.assertEqual(len(sale_order.project_ids), 1)
        self.assertEqual(len(sale_order.tasks_ids), 8)
        self.assertEqual(len(sale_order.project_id.task_ids), 8)
        self.assertEqual(len(mirror_project.task_ids), 5)

        # Dependency outcome inside the created project: the optional task_two
        # was excluded, so the link task_two <- task_three must be dropped, and
        # the task_three <- task_four chain rebuilt against the project's tasks.
        project = sale_order.order_type_project_id
        proj_task_three = project.task_ids.filtered(
            lambda t: t.source_template_task_id == task_three
        )
        proj_task_four = project.task_ids.filtered(
            lambda t: t.source_template_task_id == task_four
        )
        self.assertEqual(len(proj_task_three), 1)
        self.assertEqual(len(proj_task_four), 1)
        self.assertFalse(
            proj_task_three.depend_on_ids,
            "Excluded optional task_two must not leave a dangling dependency.",
        )
        self.assertEqual(
            proj_task_four.depend_on_ids,
            proj_task_three,
            "task_three <- task_four chain must be rebuilt inside the project.",
        )

    def test_product_optional_task(self):
        # Project Template
        project_template_one = self.env["project.project"].create(
            [
                {
                    "name": "Project Template",
                    "allow_task_dependencies": True,
                    "is_template": True,
                }
            ]
        )

        # Tasks for project template
        task_one, _task_two, _task_three, _task_four = self.env["project.task"].create(
            [
                {
                    "name": "Project Task One",
                    "project_id": project_template_one.id,
                    "optional_task": True,
                },
                {
                    "name": "Project Task Two",
                    "project_id": project_template_one.id,
                },
                {
                    "name": "Project Task Three",
                    "project_id": project_template_one.id,
                },
                {
                    "name": "Project Task Four",
                    "project_id": project_template_one.id,
                },
            ]
        )

        # Sale order type with SOT project
        sale_order_type = self.env["sale.order.type"].create(
            {
                "name": "Sale Order Type",
                "project_template_id": project_template_one.id,
            }
        )

        # Product with an optional task
        product = self.env["product.product"].create(
            [
                {
                    "name": "Product",
                    "type": "service",
                    "service_tracking": "so_project_task_templates",
                    "so_task_template_id": task_one.id,
                }
            ]
        )

        # Partner
        res_partner = self.env["res.partner"].create({"name": "Max Megaman"})

        # Sale Order
        sale_order = self.env["sale.order"].create(
            {
                "name": "Test Sale Order",
                "partner_id": res_partner.id,
                "type_id": sale_order_type.id,
            }
        )

        sale_order.action_confirm()

        self.assertEqual(len(sale_order.project_ids), 1)
        self.assertEqual(len(sale_order.tasks_ids), 3)
        self.assertEqual(len(sale_order.project_id.task_ids), 3)

        sale_order_two = self.env["sale.order"].create(
            {
                "name": "Test Sale Order",
                "partner_id": res_partner.id,
                "type_id": sale_order_type.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": product.id,
                        }
                    ),
                ],
            }
        )

        sale_order_two.action_confirm()

        self.assertEqual(len(sale_order_two.project_ids), 1)
        self.assertEqual(len(sale_order_two.tasks_ids), 4)
        self.assertEqual(len(sale_order_two.project_id.task_ids), 4)

    def test_optional_task_merge_reconstructs_dependencies(self):
        """An optional task merged into an existing project after creation must
        rebuild its dependencies against the project's own tasks (not the
        template) and re-link the dependents, while leaving the template
        completely untouched.

        Template chain: task1 <- task2 <- task3, with task2 optional. The first
        order creates the project without task2 (so task3 loses its dependency);
        a second order merges task2 in and the chain is restored inside the
        project.
        """
        template = self.env["project.project"].create(
            {
                "name": "Chain Template",
                "is_template": True,
                "allow_task_dependencies": True,
            }
        )
        task_one, task_two, task_three = self.env["project.task"].create(
            [
                {
                    "name": "Chain Task One",
                    "project_id": template.id,
                },
                {
                    "name": "Chain Task Two",
                    "project_id": template.id,
                    "optional_task": True,
                },
                {
                    "name": "Chain Task Three",
                    "project_id": template.id,
                },
            ]
        )
        task_two.depend_on_ids = task_one
        task_three.depend_on_ids = task_two

        sale_order_type = self.env["sale.order.type"].create(
            {
                "name": "Chain Type",
                "project_template_id": template.id,
            }
        )
        partner = self.env["res.partner"].create({"name": "Chain Partner"})

        # First order creates the project without the optional task2.
        first_order = self.env["sale.order"].create(
            {
                "name": "Chain SO 1",
                "partner_id": partner.id,
                "type_id": sale_order_type.id,
            }
        )
        first_order.action_confirm()
        project = first_order.order_type_project_id

        proj_one = project.task_ids.filtered(
            lambda t: t.source_template_task_id == task_one
        )
        proj_three = project.task_ids.filtered(
            lambda t: t.source_template_task_id == task_three
        )
        self.assertEqual(len(project.task_ids), 2)
        self.assertEqual(len(proj_one), 1)
        self.assertEqual(len(proj_three), 1)
        self.assertFalse(
            proj_three.depend_on_ids,
            "task3 should have lost its dependency when optional task2 was excluded.",
        )

        # Second order merges the optional task2 into the existing project.
        plain_type = self.env["sale.order.type"].create({"name": "Plain Type"})
        product = self.env["product.product"].create(
            {
                "name": "Merge Optional Task",
                "type": "service",
                "service_tracking": "so_project_task_templates",
                "so_task_template_id": task_two.id,
            }
        )
        second_order = self.env["sale.order"].create(
            {
                "name": "Chain SO 2",
                "partner_id": partner.id,
                "type_id": plain_type.id,
                "project_id": project.id,
                "order_line": [Command.create({"product_id": product.id})],
            }
        )
        second_order.action_confirm()

        proj_two = project.task_ids.filtered(
            lambda t: t.source_template_task_id == task_two
        )
        self.assertEqual(len(proj_two), 1)
        self.assertEqual(len(project.task_ids), 3)
        # Chain rebuilt against the project's tasks.
        self.assertEqual(proj_two.depend_on_ids, proj_one)
        self.assertEqual(proj_three.depend_on_ids, proj_two)
        # Template left untouched (no pollution, no dangling links).
        self.assertEqual(task_two.depend_on_ids, task_one)
        self.assertEqual(task_three.depend_on_ids, task_two)
        self.assertEqual(task_one.dependent_ids, task_two)

    def test_batch_confirm_creates_projects(self):
        """Confirming several orders at once must create an order-type project
        for each (guards against the ``self.type_id`` singleton bug).
        """
        template = self.env["project.project"].create(
            {
                "name": "Batch Template",
                "is_template": True,
            }
        )
        self.env["project.task"].create(
            {
                "name": "Batch Task",
                "project_id": template.id,
            }
        )
        sale_order_type = self.env["sale.order.type"].create(
            {
                "name": "Batch Type",
                "project_template_id": template.id,
            }
        )
        partner = self.env["res.partner"].create({"name": "Batch Partner"})

        orders = self.env["sale.order"].create(
            [
                {
                    "name": "Batch SO 1",
                    "partner_id": partner.id,
                    "type_id": sale_order_type.id,
                },
                {
                    "name": "Batch SO 2",
                    "partner_id": partner.id,
                    "type_id": sale_order_type.id,
                },
            ]
        )

        # Call ``_action_confirm`` on the multi-record set directly: the public
        # ``action_confirm`` is singleton-only in this stack (downstream CRIF
        # check), but the project creation we fixed lives in ``_action_confirm``.
        orders._action_confirm()

        self.assertTrue(all(orders.mapped("order_type_project_id")))
        projects = orders.mapped("order_type_project_id")
        self.assertEqual(len(projects), 2, "Each order must get its own project.")

    def test_action_view_project_ids_single_project(self):
        """The smart-button action for an order with a single project must
        target that project (single-project branch of the override).
        """
        template = self.env["project.project"].create(
            {
                "name": "View Template",
                "is_template": True,
            }
        )
        self.env["project.task"].create(
            {
                "name": "View Task",
                "project_id": template.id,
            }
        )
        sale_order_type = self.env["sale.order.type"].create(
            {
                "name": "View Type",
                "project_template_id": template.id,
            }
        )
        partner = self.env["res.partner"].create({"name": "View Partner"})

        order = self.env["sale.order"].create(
            {
                "name": "View SO",
                "partner_id": partner.id,
                "type_id": sale_order_type.id,
            }
        )
        order.action_confirm()

        self.assertEqual(len(order.project_ids), 1)
        action = order.action_view_project_ids()
        # The single-project branch targets the order's project. Assert
        # agnostically (``res_id`` or ``default_project_id``) so the test holds
        # regardless of which override wins in the assembled registry.
        targeted = action.get("res_id") or action.get("context", {}).get(
            "default_project_id"
        )
        self.assertEqual(targeted, order.order_type_project_id.id)
