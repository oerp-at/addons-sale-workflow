# Copyright 2026, Weboffice IT-Service und Marketing GmbH & Co KG

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """mirror_task_id is no longer company_dependent: JSONB -> int4.

    Keep the value of the task's own company, else the only value stored. Links
    with several different values or to deleted tasks are dropped (logged).
    """
    cr.execute(
        """
        SELECT data_type FROM information_schema.columns
         WHERE table_name = 'project_task' AND column_name = 'mirror_task_id'
        """
    )
    row = cr.fetchone()
    if not row or row[0] != "jsonb":
        return
    cr.execute(
        "ALTER TABLE project_task "
        "RENAME COLUMN mirror_task_id TO mirror_task_id_by_company"
    )
    cr.execute("ALTER TABLE project_task ADD COLUMN mirror_task_id int4")
    cr.execute(
        """
        WITH link AS (
            SELECT t.id, COALESCE(
                (t.mirror_task_id_by_company ->> t.company_id::text)::int4,
                (SELECT min(e.value::int4)
                   FROM jsonb_each_text(t.mirror_task_id_by_company) e
                 HAVING count(DISTINCT e.value) = 1)
            ) AS mirror_id
              FROM project_task t
             WHERE jsonb_typeof(t.mirror_task_id_by_company) = 'object'
        )
        UPDATE project_task t
           SET mirror_task_id = link.mirror_id
          FROM link
          JOIN project_task m ON m.id = link.mirror_id
         WHERE t.id = link.id
        """
    )
    _logger.info("sale_order_task: %s mirror task links converted", cr.rowcount)
    cr.execute(
        """
        SELECT id FROM project_task
         WHERE mirror_task_id IS NULL
           AND jsonb_typeof(mirror_task_id_by_company) = 'object'
           AND EXISTS (
               SELECT 1 FROM jsonb_each_text(mirror_task_id_by_company) e
                WHERE e.value IS NOT NULL
           )
        """
    )
    dropped = [r[0] for r in cr.fetchall()]
    if dropped:
        _logger.warning(
            "sale_order_task: mirror task link dropped (ambiguous or deleted) "
            "on tasks %s",
            dropped,
        )
    cr.execute("ALTER TABLE project_task DROP COLUMN mirror_task_id_by_company")
