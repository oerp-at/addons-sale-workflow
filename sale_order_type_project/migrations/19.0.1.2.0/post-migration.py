# -*- coding: utf-8 -*-
# Copyright 2026, Weboffice IT-Service und Marketing GmbH & Co KG

"""Restore the values stashed by ``pre-migration.py`` into the new
plain ``project_template_id`` column.

Selection strategy when the legacy JSONB had several per-company values:

1. Prefer the value associated with the ``sale.order.type``'s own
   ``company_id`` (the most likely intended one for the record).
2. Otherwise fall back to the first non-null value in the JSONB.

We log a warning whenever multiple distinct values existed, so the
operator can review such cases.
"""

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    cr.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'sale_order_type'
          AND column_name = 'project_template_id_legacy'
        """
    )
    if not cr.fetchone():
        return

    cr.execute(
        """
        SELECT id, company_id, project_template_id_legacy
        FROM sale_order_type
        WHERE project_template_id_legacy IS NOT NULL
        """
    )
    rows = cr.fetchall()

    updates = []
    for sot_id, sot_company_id, jsonb_val in rows:
        if not isinstance(jsonb_val, dict) or not jsonb_val:
            continue
        # Drop empty entries up front.
        clean = {cid: pid for cid, pid in jsonb_val.items() if pid}
        if not clean:
            continue
        chosen = None
        if sot_company_id is not None:
            chosen = clean.get(str(sot_company_id))
        if chosen is None:
            chosen = next(iter(clean.values()))
        distinct = set(clean.values())
        if len(distinct) > 1:
            _logger.warning(
                "sale.order.type id=%s: multiple per-company project "
                "templates found (%s); kept project.project id=%s.",
                sot_id, clean, chosen,
            )
        updates.append((int(chosen), sot_id))

    if updates:
        cr.executemany(
            "UPDATE sale_order_type SET project_template_id = %s WHERE id = %s",
            updates,
        )
        _logger.info(
            "sale.order.type.project_template_id: restored %s values from "
            "the legacy JSONB column.", len(updates),
        )

    cr.execute("ALTER TABLE sale_order_type DROP COLUMN project_template_id_legacy")
