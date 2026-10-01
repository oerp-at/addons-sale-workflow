# sale_order_task

> Configure project and task templates on products so that confirming a sale order or instantiating a project template populates the project with tasks and automatically mirrors selected tasks into a second project.

## Dependencies

- `sale_management`, `sale_project`

## Models

| Model | Purpose |
|---|---|
| `project.task` (inherit) | Adds mirror/sync fields and bidirectional sync logic. |
| `project.project` (inherit) | `create_mirror_tasks()` + hooks for template instantiation and duplication. |
| `project.task.type.link` (new) | Pairs stages between an original and a mirror project. |
| `product.template` (inherit) | New `service_tracking = so_project_task_templates` + `so_task_template_id`. |
| `sale.order.line` (inherit) | Triggers project/task merging from the SO. |

## Key Fields & Logic

- `project.task.mirror_project_id` (`company_dependent`) — target project for mirroring; configures the relationship.
- `project.task.mirror_task_id` (`company_dependent`) — counterpart task, set by `create_mirror_tasks`.
- `project.task.is_mirror` — `True` on the copy that lives inside the mirror project.
- `project.task.state_sync_direction` — `none` / `original` / `mirror` / `both`; controls who may change stage/state and how it propagates.
- `project.task.state_change_permission` — computed; drives `readonly` on stage/state in views.
- `product.template.so_task_template_id` — single task template merged into the SO project.
- `product.template.service_tracking = 'so_project_task_templates'` — marks products that participate in the merge flow.
- `project.task.type.link.{first,second}_stage_id` — translation table between original- and mirror-project stages.

## Creation paths (both must end up mirrored)

1. SO confirmation — `sale.order.line._timesheet_service_generation()` instantiates project templates, merges task templates into the project, and finally calls `project.create_mirror_tasks(exclude_task_ids=<pre-existing>)`.
2. Direct template instantiation — `project.project.action_create_from_template()` is overridden to call `create_mirror_tasks()` on the new project.

After a single task template is merged, `_so_task_template_create_task` calls `project.task._drop_external_dependencies()` on the copied tasks (and their subtasks). Core's copy keeps the template ids for any dependency whose other end was not part of the same copy; this strips every `depend_on_ids`/`dependent_ids` link pointing at a task in a different project, so the merge never leaves dangling links nor pollutes the template.

`create_mirror_tasks()` is **idempotent**: it only acts on top-level tasks with `mirror_project_id` set and no `mirror_task_id`, so both entry points are safe to coexist.

## Duplication policy

- `project.project.copy()` is overridden to raise `UserError` if the project contains tasks with `mirror_project_id` set or `is_mirror=True`. The mirror relationship cannot be rebuilt safely on a bare `copy()`.
- Exempt paths: `is_template=True` source projects (template-to-template duplication) and any caller that sets `copy_from_template=True` in the context (e.g. `action_create_from_template`).

## Sync semantics on `write`

- Stage/state writes are gated by `state_sync_direction`; forbidden changes raise `ValidationError`.
- Allowed changes propagate to the counterpart with `is_mirror_write=True` to avoid recursion.
- `stage_id` is translated via `project.task.type.link` before propagating.
- `description` is written separately with `ignore_history_divergence=True` to bypass core history checks.
- `_filter_out_non_mirrorable_vals` strips `project_id`, `parent_id`, `child_ids`, `mirror_*`, `sale_*` from mirror writes.

## Views & Menus

- `view_task_form2_inherit`, `view_task_kanban_inherit` — add mirror fields and lock stage/state via `state_change_permission`.
- `project_task_type_link_list` — editable list view for stage links.
- `product_template_form_view_sale_project_inherit` — adds the project/task template fields under `service_tracking`.
- Menu `Project > Configuration > Link Mirror Task Stages` (`menu_project_config_project_task_type_link`).

## File Layout

```
sale_order_task/
  __manifest__.py
  models/
    project_project.py        # create_mirror_tasks, action_create_from_template, copy()
    project_task.py           # mirror fields, write/copy sync logic
    project_task_type_link.py # stage pair model
    product_template.py       # service_tracking + so_task_template_id
    sale_order_line.py        # _timesheet_service_generation
  views/                      # form/list/kanban inherits + menu
  security/ir.model.access.csv
  tests/
    test_sale_order_task.py       # merge + mirror + dependency stripping
    test_project_task_type_link.py
```

## Known Pitfalls / Notes

- `mirror_project_id` and `mirror_task_id` are `company_dependent=True` and therefore have `copy=False` (Odoo default for `company_dependent`); the `copy_data` override re-populates `mirror_project_id` explicitly when copying.
- `create_mirror_tasks` must remain idempotent — the SO flow calls it after `action_create_from_template` has already mirrored part of the project.
- `default` in `project_task.copy_data` is normalised to a dict because `map_tasks` may pass `default=None`.
- Stage link lookup picks the first match (`limit=1`) — keep `project.task.type.link` pairs unique per stage.
- Mirror writes intentionally skip `project_id`, `parent_id`, `sale_line_id`, `sale_order_id`; moving an original task between projects does **not** move its mirror.
- This module is single-/standard-multi-company only. Branch/multi-company support (ancestor-company template visibility via record-rule patch + `_check_company_domain`, and project company realignment on confirmation) lives in `woa_himmelblau_project`, not here.
