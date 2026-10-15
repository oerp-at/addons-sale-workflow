# Copyright 2026, Weboffice IT-Service und Marketing GmbH & Co KG

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestProjectTaskTypeLink(TransactionCase):
    def test_self_link_raises(self):
        """A stage cannot be linked to itself."""
        stage = self.env["project.task.type"].create({"name": "Stage"})
        with self.assertRaises(ValidationError):
            self.env["project.task.type.link"].create(
                {
                    "first_stage_id": stage.id,
                    "second_stage_id": stage.id,
                }
            )

    def test_computes_expose_stages_and_projects(self):
        """The link computes expose its stages and the (company-visible)
        projects of each stage."""
        project = self.env["project.project"].create({"name": "Link Project"})
        first_stage, second_stage = self.env["project.task.type"].create(
            [
                {"name": "First", "project_ids": [project.id]},
                {"name": "Second", "project_ids": [project.id]},
            ]
        )
        link = self.env["project.task.type.link"].create(
            {
                "first_stage_id": first_stage.id,
                "second_stage_id": second_stage.id,
            }
        )

        self.assertIn(first_stage, link.used_stage_ids)
        self.assertIn(second_stage, link.used_stage_ids)
        self.assertIn(project, link.first_stage_project_ids)
        self.assertIn(project, link.second_stage_project_ids)
