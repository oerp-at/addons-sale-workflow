# Copyright 2026, Weboffice IT-Service und Marketing GmbH & Co KG

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.fields import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestSaleOrderTask(TransactionCase):
    def _setup_templates_and_link_stages(self):
        """Common fixture used by multiple tests:
        - one mirror project with 3 stages,
        - one project template with 3 stages,
        - 3 stage links between them,
        - two tasks in the template (one with mirror_project_id set).
        """
        mirror_project = self.env["project.project"].create(
            {
                "name": "Mirror Project",
                "type_ids": [Command.clear()],  # no 20.0 default stages
            }
        )
        project_template = self.env["project.project"].create(
            {
                "name": "Project Template",
                "type_ids": [Command.clear()],  # no 20.0 default stages
                "is_template": True,
            }
        )

        first_tpl, second_tpl, third_tpl = self.env["project.task.type"].create(
            [
                {
                    "name": "New",
                    "sequence": 1,
                    "project_ids": [project_template.id],
                },
                {
                    "name": "In Progress",
                    "sequence": 10,
                    "project_ids": [project_template.id],
                },
                {
                    "name": "Won",
                    "sequence": 20,
                    "project_ids": [project_template.id],
                },
            ]
        )
        first_mir, second_mir, third_mir = self.env["project.task.type"].create(
            [
                {
                    "name": "New and Shiny",
                    "sequence": 1,
                    "project_ids": [mirror_project.id],
                },
                {
                    "name": "Production",
                    "sequence": 10,
                    "project_ids": [mirror_project.id],
                },
                {
                    "name": "Finished",
                    "sequence": 20,
                    "project_ids": [mirror_project.id],
                },
            ]
        )
        self.env["project.task.type.link"].create(
            [
                {
                    "first_stage_id": first_tpl.id,
                    "second_stage_id": first_mir.id,
                },
                {
                    "first_stage_id": second_tpl.id,
                    "second_stage_id": second_mir.id,
                },
                {
                    "first_stage_id": third_tpl.id,
                    "second_stage_id": third_mir.id,
                },
            ]
        )
        self.env["project.task"].create(
            [
                {
                    "name": "Template Task One",
                    "project_id": project_template.id,
                    "stage_id": first_tpl.id,
                },
                {
                    "name": "Template Task Two",
                    "project_id": project_template.id,
                    "mirror_project_id": mirror_project.id,
                    "state_sync_direction": "original",
                    "stage_id": second_tpl.id,
                },
            ]
        )
        return {
            "mirror_project": mirror_project,
            "project_template": project_template,
            "first_tpl": first_tpl,
            "second_tpl": second_tpl,
            "third_tpl": third_tpl,
            "first_mir": first_mir,
            "second_mir": second_mir,
            "third_mir": third_mir,
        }

    def _confirm_full_so(self):
        """Build the full template/mirror/product scenario, confirm the sale
        order and return the key records for assertions.

        The order has three lines:
        - a product creating ``project_template_one`` (2 tasks, one mirrored),
        - a product creating ``project_template_two`` (2 tasks, one mirrored),
        - a product merging a standalone task template (1 task).
        """
        mirror_project = self.env["project.project"].create(
            {
                "name": "Mirror Project",
                "type_ids": [Command.clear()],  # no 20.0 default stages
            }
        )
        project_template_one, project_template_two = self.env["project.project"].create(
            [
                {
                    "name": "Project Template One",
                    "type_ids": [Command.clear()],  # no 20.0 default stages
                    "is_template": True,
                },
                {
                    "name": "Project Template Two",
                    "type_ids": [Command.clear()],  # no 20.0 default stages
                    "is_template": True,
                },
            ]
        )

        first_stage_template, second_stage_template, third_stage_template = self.env[
            "project.task.type"
        ].create(
            [
                {
                    "name": "New",
                    "sequence": 1,
                    "project_ids": [project_template_one.id],
                },
                {
                    "name": "In Progress",
                    "sequence": 10,
                    "project_ids": [project_template_one.id],
                },
                {
                    "name": "Won",
                    "sequence": 20,
                    "project_ids": [project_template_one.id],
                },
            ]
        )

        first_stage_mirror, second_stage_mirror, third_stage_mirror = self.env[
            "project.task.type"
        ].create(
            [
                {
                    "name": "New and Shiny",
                    "sequence": 1,
                    "project_ids": [mirror_project.id],
                },
                {
                    "name": "Production",
                    "sequence": 10,
                    "project_ids": [mirror_project.id],
                },
                {
                    "name": "Finished",
                    "sequence": 20,
                    "project_ids": [mirror_project.id],
                },
            ]
        )

        self.env["project.task"].create(
            [
                {
                    "name": "Project One Task One",
                    "project_id": project_template_one.id,
                    "stage_id": project_template_one.type_ids[0].id,
                },
                {
                    "name": "Project One Task Two",
                    "project_id": project_template_one.id,
                    "mirror_project_id": mirror_project.id,
                    "state_sync_direction": "original",
                    "stage_id": project_template_one.type_ids[1].id,
                },
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

        self.env["project.task.type.link"].create(
            [
                {
                    "first_stage_id": first_stage_template.id,
                    "second_stage_id": first_stage_mirror.id,
                },
                {
                    "first_stage_id": second_stage_template.id,
                    "second_stage_id": second_stage_mirror.id,
                },
                {
                    "first_stage_id": third_stage_template.id,
                    "second_stage_id": third_stage_mirror.id,
                },
            ]
        )

        task_template = self.env["project.task"].create(
            {"name": "Task Template", "is_template": True}
        )

        product_one, product_two, product_three = self.env["product.product"].create(
            [
                {
                    "name": "Product One",
                    "type": "service",
                    "service_tracking": "so_project_task_templates",
                    "project_template_id": project_template_one.id,
                },
                {
                    "name": "Product Two",
                    "type": "service",
                    "service_tracking": "so_project_task_templates",
                    "project_template_id": project_template_two.id,
                },
                {
                    "name": "Product Three",
                    "type": "service",
                    "service_tracking": "so_project_task_templates",
                    "so_task_template_id": task_template.id,
                },
            ]
        )

        res_partner = self.env["res.partner"].create({"name": "Max Megaman"})

        sale_order = self.env["sale.order"].create(
            {
                "name": "Test Sale Order",
                "partner_id": res_partner.id,
                "order_line": [
                    Command.create({"product_id": product_one.id}),
                    Command.create({"product_id": product_two.id}),
                    Command.create({"product_id": product_three.id}),
                ],
            }
        )
        sale_order.action_confirm()

        mirror_task = mirror_project.task_ids.filtered(
            lambda t: t.state_sync_direction == "original"
        )
        original_task = mirror_task.mirror_task_id
        return {
            "sale_order": sale_order,
            "mirror_project": mirror_project,
            "mirror_task": mirror_task,
            "original_task": original_task,
            "first_stage_template": first_stage_template,
            "second_stage_template": second_stage_template,
            "third_stage_template": third_stage_template,
            "first_stage_mirror": first_stage_mirror,
            "second_stage_mirror": second_stage_mirror,
            "third_stage_mirror": third_stage_mirror,
        }

    def test_so_confirm_creates_tasks_and_mirrors(self):
        """Confirming the order creates one project with all tasks, mirrors the
        configured ones and starts them in the expected (linked) stages."""
        data = self._confirm_full_so()
        sale_order = data["sale_order"]

        self.assertEqual(len(sale_order.project_ids), 1)
        self.assertEqual(len(sale_order.tasks_ids), 5)
        self.assertEqual(len(sale_order.project_id.task_ids), 5)
        self.assertEqual(len(data["mirror_project"].task_ids), 2)

        self.assertTrue(data["original_task"])
        self.assertEqual(data["original_task"].stage_id, data["second_stage_template"])
        self.assertEqual(data["mirror_task"].stage_id, data["second_stage_mirror"])

    def test_stage_change_denied_on_synced_mirror(self):
        """A mirror task whose sync is driven by the original must reject direct
        stage/state changes."""
        data = self._confirm_full_so()
        mirror_task = data["mirror_task"]

        with self.assertRaises(ValidationError):
            mirror_task.stage_id = data["first_stage_mirror"]

        with self.assertRaises(ValidationError):
            mirror_task.state = "03_approved"

    def test_stage_sync_original_drives_mirror(self):
        """With direction 'original', the original task's stage change is mapped
        onto the mirror via the configured stage links."""
        data = self._confirm_full_so()

        data["original_task"].stage_id = data["first_stage_template"]
        self.assertEqual(data["mirror_task"].stage_id, data["first_stage_mirror"])

    def test_stage_and_state_sync_both_directions(self):
        """With direction 'both', stage and state changes propagate either way."""
        data = self._confirm_full_so()
        original_task = data["original_task"]
        mirror_task = data["mirror_task"]

        mirror_task.state_sync_direction = "both"
        original_task.state_sync_direction = "both"

        original_task.stage_id = data["third_stage_template"]
        self.assertEqual(original_task.stage_id, data["third_stage_template"])
        self.assertEqual(mirror_task.stage_id, data["third_stage_mirror"])

        mirror_task.stage_id = data["second_stage_mirror"]
        self.assertEqual(original_task.stage_id, data["second_stage_template"])
        self.assertEqual(mirror_task.stage_id, data["second_stage_mirror"])

        original_task.state = "03_approved"
        self.assertEqual(original_task.state, "03_approved")
        self.assertEqual(mirror_task.state, "03_approved")

    def test_stage_sync_none_disables_sync(self):
        """With direction 'none', stage changes are not propagated."""
        data = self._confirm_full_so()
        original_task = data["original_task"]
        mirror_task = data["mirror_task"]

        mirror_task.state_sync_direction = "none"
        original_task.state_sync_direction = "none"

        original_task.stage_id = data["first_stage_template"]
        self.assertEqual(original_task.stage_id, data["first_stage_template"])
        self.assertEqual(mirror_task.stage_id, data["second_stage_mirror"])

    def test_description_sync_both_ways(self):
        """The description is always mirrored, independent of the sync
        direction, in both directions."""
        data = self._confirm_full_so()
        original_task = data["original_task"]
        mirror_task = data["mirror_task"]

        original_task.description = "Test Test Test"
        self.assertEqual(original_task.description, mirror_task.description)

        mirror_task.description = "Test description from mirror task"
        self.assertEqual(mirror_task.description, original_task.description)

    def test_original_task_project_move_keeps_mirror(self):
        """Moving the original task to another project must not drag its mirror
        along."""
        data = self._confirm_full_so()
        new_project = self.env["project.project"].create({"name": "New Project"})

        data["original_task"].project_id = new_project
        self.assertNotEqual(data["mirror_task"].project_id, new_project)

    def test_create_from_project_template_directly(self):
        """Mirror tasks must be created when a project is created directly from a
        template via action_create_from_template (not via Sale Order).
        """
        fixture = self._setup_templates_and_link_stages()
        mirror_project = fixture["mirror_project"]
        project_template = fixture["project_template"]
        second_mir = fixture["second_mir"]

        self.assertEqual(len(mirror_project.task_ids), 0)

        new_project = project_template.action_create_from_template()
        self.assertFalse(new_project.is_template)
        self.assertEqual(len(new_project.task_ids), 2)

        new_mirrors = mirror_project.task_ids
        self.assertEqual(len(new_mirrors), 1)
        new_mirror = new_mirrors[0]
        self.assertTrue(new_mirror.is_mirror)
        self.assertEqual(new_mirror.stage_id, second_mir)

        # The corresponding original in new_project must be linked back to the mirror.
        original = new_project.task_ids.filtered(lambda t: t.mirror_project_id)
        self.assertEqual(len(original), 1)
        self.assertEqual(original.mirror_task_id, new_mirror)
        self.assertEqual(new_mirror.mirror_task_id, original)
        self.assertEqual(new_mirror.mirror_project_id, new_project)

        # Idempotency: a second creation produces a second project with its own mirror,
        # but the first project's mirror is left untouched.
        second_project = project_template.action_create_from_template()
        self.assertEqual(len(mirror_project.task_ids), 2)
        self.assertEqual(original.mirror_task_id, new_mirror)

        # The second project also gets a properly linked mirror.
        second_original = second_project.task_ids.filtered(
            lambda t: t.mirror_project_id
        )
        self.assertEqual(len(second_original), 1)
        self.assertTrue(second_original.mirror_task_id)
        self.assertNotEqual(second_original.mirror_task_id, new_mirror)

    def test_duplicate_project_with_originals_is_blocked(self):
        """Duplicating a non-template project that contains tasks configured for
        mirroring must raise UserError.
        """
        fixture = self._setup_templates_and_link_stages()
        project_template = fixture["project_template"]

        new_project = project_template.action_create_from_template()
        self.assertTrue(new_project.task_ids.filtered(lambda t: t.mirror_project_id))

        with self.assertRaises(UserError):
            new_project.copy()

    def test_duplicate_mirror_project_is_blocked(self):
        """Duplicating a project that contains mirror tasks (is_mirror=True)
        must raise UserError."""
        fixture = self._setup_templates_and_link_stages()
        mirror_project = fixture["mirror_project"]

        project_template = fixture["project_template"]
        project_template.action_create_from_template()
        self.assertTrue(mirror_project.task_ids.filtered(lambda t: t.is_mirror))

        with self.assertRaises(UserError):
            mirror_project.copy()

    def test_duplicate_template_is_allowed(self):
        """Template duplication remains allowed even if the template contains tasks
        configured for mirroring.
        """
        fixture = self._setup_templates_and_link_stages()
        project_template = fixture["project_template"]

        copied_template = project_template.copy()
        self.assertTrue(copied_template.is_template)
        self.assertEqual(len(copied_template.task_ids), 2)

    def _merge_target_project(self):
        return self.env["project.project"].create(
            {
                "name": "Target Project",
                "allow_billable": True,
                "allow_task_dependencies": True,
            }
        )

    def _merge_so(self, target_project, so_task_template):
        product = self.env["product.product"].create(
            {
                "name": "Merge Product",
                "type": "service",
                "service_tracking": "so_project_task_templates",
                "so_task_template_id": so_task_template.id,
            }
        )
        partner = self.env["res.partner"].create({"name": "Merge Partner"})
        sale_order = self.env["sale.order"].create(
            {
                "name": "Merge SO",
                "partner_id": partner.id,
                "project_id": target_project.id,
                "order_line": [Command.create({"product_id": product.id})],
            }
        )
        sale_order.action_confirm()
        return sale_order

    def test_merge_task_does_not_pollute_template(self):
        """Merging a template task that *depends on* a non-copied template task
        must drop the dangling depend_on link and not pollute the template."""
        template = self.env["project.project"].create(
            {
                "name": "Dep Template",
                "is_template": True,
                "allow_task_dependencies": True,
            }
        )
        task_a, task_b = self.env["project.task"].create(
            [
                {
                    "name": "Template Task A",
                    "project_id": template.id,
                },
                {
                    "name": "Template Task B",
                    "project_id": template.id,
                },
            ]
        )
        task_b.depend_on_ids = task_a

        target_project = self._merge_target_project()
        self._merge_so(target_project, task_b)

        merged = target_project.task_ids
        self.assertEqual(len(merged), 1)
        # task_a was not copied, so the merged task must not depend on it.
        self.assertFalse(
            merged.depend_on_ids,
            "Merged task must not keep a dependency on a template task.",
        )
        # The template must be left exactly as it was.
        self.assertEqual(task_b.depend_on_ids, task_a)
        self.assertEqual(task_a.dependent_ids, task_b)

    def test_merge_task_strips_dependent_links(self):
        """Merging a template task that *is depended on by* a non-copied
        template task must drop the dangling dependent link (the
        ``dependent_ids`` branch) and not pollute the template."""
        template = self.env["project.project"].create(
            {
                "name": "Dependent Template",
                "is_template": True,
                "allow_task_dependencies": True,
            }
        )
        task_a, task_b = self.env["project.task"].create(
            [
                {
                    "name": "Template Task A",
                    "project_id": template.id,
                },
                {
                    "name": "Template Task B",
                    "project_id": template.id,
                },
            ]
        )
        # task_a depends on task_b, so task_b.dependent_ids == task_a.
        task_a.depend_on_ids = task_b

        target_project = self._merge_target_project()
        self._merge_so(target_project, task_b)

        merged = target_project.task_ids
        self.assertEqual(len(merged), 1)
        # task_a was not copied, so the merged task must not list it as dependent.
        self.assertFalse(
            merged.dependent_ids,
            "Merged task must not keep a dependent pointing at a template task.",
        )
        # The template must be left exactly as it was (no new depend_on entry).
        self.assertEqual(task_a.depend_on_ids, task_b)
        self.assertEqual(task_b.dependent_ids, task_a)

    def test_merge_task_with_subtask_strips_cross_template_deps(self):
        """When a merged task has subtasks with dependencies on non-copied
        template tasks, those dangling links are stripped on the subtasks too."""
        template = self.env["project.project"].create(
            {
                "name": "Subtask Template",
                "is_template": True,
                "allow_task_dependencies": True,
            }
        )
        parent_task, other_task = self.env["project.task"].create(
            [
                {
                    "name": "Parent Task",
                    "project_id": template.id,
                },
                {
                    "name": "Other Task",
                    "project_id": template.id,
                },
            ]
        )
        subtask = self.env["project.task"].create(
            {
                "name": "Subtask",
                "project_id": template.id,
                "parent_id": parent_task.id,
            }
        )
        subtask.depend_on_ids = other_task

        target_project = self._merge_target_project()
        self._merge_so(target_project, parent_task)

        merged_subtask = target_project.task_ids.filtered(lambda t: t.parent_id)
        self.assertEqual(len(merged_subtask), 1)
        self.assertFalse(
            merged_subtask.depend_on_ids,
            "Merged subtask must not keep a dependency on a template task.",
        )
        # The template is untouched.
        self.assertEqual(subtask.depend_on_ids, other_task)
        self.assertEqual(other_task.dependent_ids, subtask)

    def test_mirror_copy_keeps_dates(self):
        """Deadline and (with project_enterprise) start date are copy=False, but the
        mirror task must start with the dates of its original."""
        mirror_project = self.env["project.project"].create({"name": "Mirror"})
        project = self.env["project.project"].create({"name": "Original"})
        task_model = self.env["project.task"]
        dates = {"date_deadline": "2026-10-20 16:00:00"}
        if "planned_date_begin" in task_model._fields:
            dates["planned_date_begin"] = "2026-10-20 08:00:00"
        original = task_model.create(
            dict(
                dates,
                name="Dated Task",
                project_id=project.id,
                mirror_project_id=mirror_project.id,
            )
        )

        project.create_mirror_tasks()

        mirror = original.mirror_task_id
        self.assertEqual(mirror.project_id, mirror_project)
        for fname, value in dates.items():
            self.assertEqual(mirror[fname], fields.Datetime.to_datetime(value))
        # The original is left untouched
        for fname, value in dates.items():
            self.assertEqual(original[fname], fields.Datetime.to_datetime(value))
