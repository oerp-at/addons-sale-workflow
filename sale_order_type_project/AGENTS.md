# sale_order_type_project

## Purpose

Project template per sale order type (Weboffice module): confirming an order of such a
type creates the order project from the template, with optional template tasks.

## Models

- `sale.order.type`: `project_template_id`, `optional_task_ids`.
- `project.task`: `optional_task`, `source_template_task_id`; dependencies of optional
  tasks are rebuilt between the created tasks
  (`_reconstruct_optional_template_dependencies`).
- `project.project`: `map_order_type_project_tasks` copies the template tasks.
- `sale.order`: `order_type_project_id`; `_action_confirm` creates the project before
  the lines are processed (`_create_order_type_project`), `_compute_project_ids` adds it
  to the smart button.
- `sale.order.line`: task templates of lines (from `sale_order_task`) go into the same
  project.

## Rules

- Optional template tasks are created only if the order type or an order line asks for
  them.

## Pitfalls

- Depends on `sale_order_task` (mirror tasks) and `sale_order_type_management`.
- 20.0: every new project gets four default stages (see `sale_order_task`).
