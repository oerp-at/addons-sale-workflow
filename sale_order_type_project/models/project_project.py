# Copyright 2026, Weboffice IT-Service und Marketing GmbH & Co KG

from odoo import models


class ProjectProject(models.Model):
    _inherit = "project.project"

    def map_order_type_project_tasks(self, new_project, tasks_to_copy):
        """Copy and map tasks from template to new project"""
        # We want to copy archived task, but do not propagate an active_test context key
        tasks = tasks_to_copy.with_context(active_test=False).filtered(
            lambda t: not t.parent_id
        )

        if self.allow_task_dependencies and "task_mapping" not in self.env.context:
            self = self.with_context(task_mapping={})  # noqa: PLW0642
        # preserve task name and stage, normally altered during copy
        defaults = self._map_tasks_default_values(new_project)
        new_tasks = tasks.with_context(copy_project=True).copy(defaults)
        all_subtasks = new_tasks._get_all_subtasks()
        all_subtasks.filtered(lambda child: child.project_id != new_project).write(
            {"project_id": new_project.id}
        )

        return True
