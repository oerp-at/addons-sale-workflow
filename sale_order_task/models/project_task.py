# Copyright 2026, Weboffice IT-Service und Marketing GmbH & Co KG

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.fields import Command


class ProjectTask(models.Model):
    _inherit = "project.task"

    def _drop_external_dependencies(self):
        """Remove dependency links that cross out of the task's own project.

        When a template task is merged into a project on its own, core's copy
        keeps the template ids for any dependency whose other end was not part
        of the same copy. That leaves the new task depending on template tasks
        and - via ``dependent_ids`` - writes the new task onto the template
        tasks' ``depend_on_ids`` (polluting the template). Dropping every link
        that points at a task in a different project fixes both.
        """
        for task in self:
            project = task.project_id
            commands = {}
            external_depends = task.depend_on_ids.filtered(
                lambda dependency, project=project: dependency.project_id != project
            )
            if external_depends:
                commands["depend_on_ids"] = [
                    Command.unlink(rec.id) for rec in external_depends
                ]
            external_dependents = task.dependent_ids.filtered(
                lambda dependent, project=project: dependent.project_id != project
            )
            if external_dependents:
                commands["dependent_ids"] = [
                    Command.unlink(rec.id) for rec in external_dependents
                ]
            if commands:
                task.write(commands)

    # pylint: disable=missing-return
    @api.depends(
        "sale_line_id",
        "project_id",
        "allow_billable",
        "project_id.reinvoiced_sale_order_id",
    )
    def _compute_sale_order_id(self):
        """Fill ``sale_order_id`` from ``project.reinvoiced_sale_order_id``.

        The standard compute clears ``sale_order_id`` whenever the task
        has no ``sale_line_id``. Tasks copied from a project template via
        ``sale_order_type_project._create_order_type_project`` do not get
        a SOL assigned (they belong to the order as a whole), so they
        would lose the link to ``sale.order`` and disappear from
        ``sale.order.tasks_ids`` and the related billing flows.
        Re-apply the project's ``reinvoiced_sale_order_id`` for those.
        """
        super()._compute_sale_order_id()
        for task in self:
            if task.sale_order_id or not task.allow_billable:
                continue
            sale_order = task.project_id.reinvoiced_sale_order_id
            if not sale_order:
                continue
            if not task.partner_id:
                task.partner_id = sale_order.partner_id
            consistent_partners = (
                sale_order.partner_id
                | sale_order.partner_invoice_id
                | sale_order.partner_shipping_id
            ).commercial_partner_id
            if task.partner_id.commercial_partner_id in consistent_partners:
                task.sale_order_id = sale_order

    mirror_project_id = fields.Many2one("project.project", company_dependent=True)
    mirror_task_id = fields.Many2one("project.task", company_dependent=True)
    is_mirror = fields.Boolean()
    state_sync_direction = fields.Selection(
        string="Status Sync",
        selection=[
            ("none", "No Synchronization"),
            ("original", "Original Task"),
            ("mirror", "Mirror Task"),
            ("both", "Both Tasks"),
        ],
        default="none",
        help="Chooses which task is allowed to set and synchronize the stage and status of the task. "
        '"No Synchronization" means both tasks have their own stage and status.',
    )
    state_change_permission = fields.Boolean(compute="_compute_state_change_permission")

    def write(self, vals):
        if self.env.context.get("ignore_history_divergence"):
            # the write function of project.task calls handle_history_divergence and throws an error, so we bypass it
            return super(
                models.Model, self.with_context(ignore_history_divergence=False)
            ).write(vals)
        if not self.env.context.get("is_mirror_write") and (
            "stage_id" in vals or "state" in vals
        ):
            for task in self:
                if (
                    task.state_sync_direction == "original"
                    and task.is_mirror
                    or task.state_sync_direction == "mirror"
                    and not task.is_mirror
                ):
                    raise ValidationError(
                        self.env._(
                            "You do not have the permission to change the stage and status of this task."
                        )
                    )

        res = super().write(vals)
        for task in self:
            if task.mirror_task_id and not self.env.context.get("is_mirror_write"):
                # Some fields shouldn't be mirrored and for description we have to do some special handling
                mirror_vals = self._filter_out_non_mirrorable_vals(vals.copy())
                description = mirror_vals.pop("description", None)

                if task.state_sync_direction == "none":
                    mirror_vals.pop("state", None)
                    mirror_vals.pop("stage_id", None)
                elif mirror_vals.get("stage_id"):
                    # Sync via link defined in project.task.type.link records
                    new_stage = self.env["project.task.type"].browse(
                        mirror_vals.get("stage_id")
                    )
                    link_id = self.env["project.task.type.link"].search(
                        [
                            "|",
                            ("first_stage_id", "=", new_stage.id),
                            ("second_stage_id", "=", new_stage.id),
                        ],
                        limit=1,
                    )
                    if link_id:
                        new_mirror_stage = (
                            link_id.second_stage_id.id
                            if link_id.first_stage_id == new_stage
                            else link_id.first_stage_id.id
                        )
                        mirror_vals["stage_id"] = new_mirror_stage
                    else:
                        mirror_vals.pop("stage_id", None)

                if mirror_vals:
                    # With context is_mirror_write, so we don't fall into an endless write loop
                    task.mirror_task_id.with_context(is_mirror_write=True).write(
                        mirror_vals
                    )

                if description:
                    # the write function of project.task calls handle_history_divergence and throws an error,
                    # so we call a separate write with only the description and bypass it
                    task.mirror_task_id.with_context(
                        ignore_history_divergence=True
                    ).write({"description": description})
        return res

    def copy_data(self, default=None):
        if default is None:
            default = {}
        vals_list = super().copy_data(default=default)
        for task, vals in zip(self, vals_list):
            if not default.get("mirror_project_id"):
                vals["mirror_project_id"] = task.mirror_project_id.id
            if self.env.context.get("mirror_task_copy"):
                vals["sale_line_id"] = False
                vals["sale_order_id"] = False
                vals["mirror_project_id"] = task.project_id.id
                vals["mirror_task_id"] = task.id
                stage_id = vals.get("stage_id")
                if stage_id:
                    link_id = self.env["project.task.type.link"].search(
                        [
                            "|",
                            ("first_stage_id", "=", stage_id),
                            ("second_stage_id", "=", stage_id),
                        ],
                        limit=1,
                    )
                    if link_id:
                        new_mirror_stage = (
                            link_id.second_stage_id.id
                            if link_id.first_stage_id.id == stage_id
                            else link_id.first_stage_id.id
                        )
                        vals["stage_id"] = new_mirror_stage
        return vals_list

    def _filter_out_non_mirrorable_vals(self, vals):
        """Filters out values we don't want to mirror"""
        vals.pop("project_id", None)
        vals.pop("parent_id", None)
        vals.pop("child_ids", None)
        vals.pop("mirror_project_id", None)
        vals.pop("mirror_task_id", None)
        vals.pop("sale_line_id", None)
        vals.pop("sale_order_id", None)
        return vals

    def map_copied_tasks(self, new_project, mirror_copy=False):
        """Corrects some values on copied subtasks (otherwise subtasks are assigned to the wrong project for example)"""
        vals = {"project_id": new_project.id}
        if mirror_copy:
            vals["sale_order_id"] = False
        all_subtasks = self._get_all_subtasks()
        all_subtasks.write(vals)
        if mirror_copy:
            for task in all_subtasks:
                task.mirror_task_id.write(
                    {
                        "mirror_project_id": task.project_id,
                        "mirror_task_id": task.id,
                    }
                )

    @api.depends("state_sync_direction", "is_mirror")
    def _compute_state_change_permission(self):
        for rec in self:
            if (
                rec.state_sync_direction in ["both", "none"]
                or rec.state_sync_direction == "original"
                and not rec.is_mirror
                or rec.state_sync_direction == "mirror"
                and rec.is_mirror
            ):
                rec.state_change_permission = True
            else:
                rec.state_change_permission = False
