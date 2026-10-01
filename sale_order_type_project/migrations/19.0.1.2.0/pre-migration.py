# Copyright 2026, Weboffice IT-Service und Marketing GmbH & Co KG

"""Convert ``sale.order.type.project_template_id`` from ``company_dependent``
(JSONB) to a plain Many2one (int).

The JSONB column is moved aside into ``project_template_id_legacy`` so the
ORM can recreate ``project_template_id`` as ``int4`` cleanly. The
``post-migration`` script then writes the preserved values back into the
new column and drops the legacy column.
"""

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    cr.execute(
        """
        SELECT data_type
        FROM information_schema.columns
        WHERE table_name = 'sale_order_type'
          AND column_name = 'project_template_id'
        """
    )
    row = cr.fetchone()
    if not row:
        # Column missing entirely (e.g. fresh install path) – nothing to do.
        return
    if row[0] != "jsonb":
        # Already migrated by a prior run.
        return

    cr.execute(
        """
        ALTER TABLE sale_order_type
        ADD COLUMN IF NOT EXISTS project_template_id_legacy jsonb
        """
    )
    cr.execute(
        """
        UPDATE sale_order_type
        SET project_template_id_legacy = project_template_id
        WHERE project_template_id IS NOT NULL
        """
    )
    cr.execute("ALTER TABLE sale_order_type DROP COLUMN project_template_id")
    _logger.info(
        "sale.order.type.project_template_id: jsonb values stashed in "
        "project_template_id_legacy; column dropped so Odoo can recreate "
        "it as a plain Many2one."
    )
