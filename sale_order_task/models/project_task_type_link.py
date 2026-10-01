# Copyright 2026, Weboffice IT-Service und Marketing GmbH & Co KG

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ProjectTaskTypeLink(models.Model):
    _name = "project.task.type.link"
    _description = "Project Task Type Link"

    sequence = fields.Integer("Sequence")
    first_stage_id = fields.Many2one(
        "project.task.type", "First Linked Stage", required=True
    )
    second_stage_id = fields.Many2one(
        "project.task.type", "Second Linked Stage", required=True
    )

    first_stage_project_ids = fields.Many2many(
        "project.project",
        string="First Stage Projects",
        compute="_compute_first_stage_project_ids",
    )
    second_stage_project_ids = fields.Many2many(
        related="second_stage_id.project_ids",
        string="Second Stage Projects",
        compute="_compute_second_stage_project_ids",
    )

    used_stage_ids = fields.Many2many(
        "project.task.type", compute="_compute_used_stage_ids"
    )

    @api.depends("first_stage_id")
    def _compute_first_stage_project_ids(self):
        for rec in self:
            if rec.first_stage_id:
                rec.first_stage_project_ids = rec.first_stage_id.project_ids.filtered(
                    lambda p: (
                        p.company_id in rec.env.user.company_ids
                        or p.company_id == False
                    )
                )
            else:
                rec.first_stage_project_ids = False

    @api.depends("second_stage_id")
    def _compute_second_stage_project_ids(self):
        for rec in self:
            if rec.second_stage_id:
                rec.second_stage_project_ids = rec.second_stage_id.project_ids.filtered(
                    lambda p: (
                        p.company_id in rec.env.user.company_ids
                        or p.company_id == False
                    )
                )
            else:
                rec.second_stage_project_ids = False

    @api.depends("first_stage_id", "second_stage_id")
    def _compute_used_stage_ids(self):
        used_stage_ids = (
            self.env["project.task.type.link"]
            .search([])
            .mapped(lambda r: r.first_stage_id | r.second_stage_id)
        )

        for record in self:
            record.used_stage_ids = used_stage_ids

    @api.constrains("first_stage_id", "second_stage_id")
    def _check_stages(self):
        for rec in self:
            if rec.first_stage_id == rec.second_stage_id:
                raise ValidationError("Stages cannot be linked to themselves.")
