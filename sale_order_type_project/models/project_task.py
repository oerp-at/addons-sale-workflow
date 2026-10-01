# -*- coding: utf-8 -*-
# Copyright 2026, Weboffice IT-Service und Marketing GmbH & Co KG

from odoo import models, fields, Command


class ProjectTask(models.Model):
    _inherit = "project.task"

    optional_task = fields.Boolean(help='Tasks marked as optional will not be created in Sale Order Type Project unless '
                                        'explicitly included')

    # Back-reference to the template task a task was instantiated from. Used to
    # reconnect dependencies of optional tasks that are merged into a project
    # after it was already created (the template task's dependency neighbours
    # are no longer part of the same copy operation).
    source_template_task_id = fields.Many2one('project.task', copy=False, index='btree_not_null')

    def copy_data(self, default=None):
        vals_list = super().copy_data(default=default)
        for task, vals in zip(self, vals_list):
            # Only record the origin when copying from a template - either a
            # template project (the SO type project template) or a template
            # task - so a plain project/task duplication doesn't get spurious
            # references.
            if task.project_id.is_template or task.has_template_ancestor:
                vals['source_template_task_id'] = task.id
        return vals_list

    def _reconstruct_optional_template_dependencies(self):
        """Reconnect an optional task's dependencies to the project's tasks.

        When an optional template task is merged into a project after the
        project already exists, core's copy keeps the template ids for any
        dependency whose other end was not part of the same copy. For optional
        tasks we instead remap those template relations onto the project tasks
        instantiated from the same template (matched via
        ``source_template_task_id``), dropping any link without a counterpart.
        This also removes the template pollution left on the template tasks.
        """
        for task in self:
            template_task = task.source_template_task_id
            if not template_task or not template_task.optional_task:
                continue
            target = task.project_id
            depends = target.task_ids.filtered(
                lambda t: t.source_template_task_id in template_task.depend_on_ids
            )
            dependents = target.task_ids.filtered(
                lambda t: t.source_template_task_id in template_task.dependent_ids
            )
            task.depend_on_ids = [Command.set(depends.ids)]
            task.dependent_ids = [Command.set(dependents.ids)]
