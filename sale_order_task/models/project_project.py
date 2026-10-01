# Copyright 2026, Weboffice IT-Service und Marketing GmbH & Co KG

from odoo import models
from odoo.exceptions import UserError


class ProjectProject(models.Model):
    _inherit = "project.project"

    def create_mirror_tasks(self, exclude_task_ids=False):
        self.ensure_one()

        # Idempotent: only act on tasks that are configured for mirroring
        # (mirror_project_id set) and don't already have a mirror counterpart.
        # Subtasks are mirrored independently too, unless one of their ancestors
        # is itself mirrored - in that case the ancestor's subtree copy already
        # produces the subtask's mirror and a second one would be a duplicate.
        def _has_mirrored_ancestor(task):
            parent = task.parent_id
            while parent:
                if parent.mirror_project_id:
                    return True
                parent = parent.parent_id
            return False

        def _needs_mirror(task):
            if not task.mirror_project_id or task.mirror_task_id:
                return False
            if _has_mirrored_ancestor(task):
                return False
            return not (exclude_task_ids and task in exclude_task_ids)

        task_ids = self.task_ids.filtered(_needs_mirror)
        if not task_ids:
            return
        mirror_task_ids = task_ids.with_context(mirror_task_copy=True).copy(
            {
                "sale_line_id": False,
                "sale_order_id": False,
                "is_mirror": True,
            }
        )
        for original, copy in zip(task_ids, mirror_task_ids, strict=True):
            copy.with_context(is_mirror_write=True).write(
                {
                    "name": original.name,
                    "project_id": original.mirror_project_id.id,
                    "mirror_project_id": original.project_id.id,
                    "mirror_task_id": original.id,
                    "parent_id": original.parent_id.mirror_task_id.id
                    if original.parent_id.mirror_task_id
                    else False,
                    "sale_line_id": False,
                    "sale_order_id": False,
                    "is_mirror": True,
                }
            )
            original.with_context(is_mirror_write=True).write(
                {
                    "mirror_project_id": copy.mirror_project_id.id,
                    "mirror_task_id": copy.id,
                }
            )
        # Set the project_id and mirror fields on subtasks
        for task in mirror_task_ids:
            task.map_copied_tasks(task.project_id, mirror_copy=True)

    def action_create_from_template(self, values=None, role_to_users_mapping=None):
        project = super().action_create_from_template(
            values=values,
            role_to_users_mapping=role_to_users_mapping,
        )
        project.create_mirror_tasks()
        # The base method propagates `copy_from_template` / `copy_from_project_template`
        # on the returned recordset; that would let callers accidentally bypass the
        # duplication guard below. Re-attach the original caller env.
        return project.with_env(self.env)

    def copy(self, default=None):
        # Block plain duplication of projects that participate in mirroring; the
        # relationship
        # cannot be reconstructed safely. Template instantiation and template-to-
        # template
        # duplication are exempt.
        if not self.env.context.get("copy_from_template"):
            for project in self:
                if project.is_template:
                    continue
                # Iterate in Python because `mirror_project_id` / `mirror_task_id` are
                # company_dependent JSONB fields and can't be filtered via a plain
                # domain.
                tasks = (
                    self.env["project.task"]
                    .with_context(active_test=False)
                    .search(
                        [
                            ("project_id", "=", project.id),
                        ]
                    )
                )
                if any(t.mirror_project_id or t.is_mirror for t in tasks):
                    raise UserError(
                        self.env._(
                            "This project contains mirrored tasks and cannot be "
                            "duplicated. "
                            "Remove the mirror configuration on its tasks first, "
                            "or create a new project from the underlying template "
                            "instead."
                        )
                    )
        # ``documents_project.copy`` always duplicates the template folder while
        # keeping its source ``company_id``. When the new project lives in a
        # different (e.g. child branch) company, the assignment trips the
        # ``_check_company_is_folders_company`` constraint inside super().
        # Skip that copy via ``no_create_folder`` and recreate a fresh folder
        # on the new project's company afterwards.
        cross_company_template_copy = "documents_folder_id" in self._fields and any(
            p.documents_folder_id and p.company_id != self.env.company for p in self
        )
        if cross_company_template_copy:
            copied = (
                super(ProjectProject, self.with_context(no_create_folder=True))
                .copy(default=default)
                .with_env(self.env)
            )
            copied.sudo()._create_missing_folders()
            return copied
        return super().copy(default=default)
