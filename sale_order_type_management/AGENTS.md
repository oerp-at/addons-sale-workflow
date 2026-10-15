# sale_order_type_management

## Purpose

Workflow options on sale order types (Weboffice module): types without invoice or
delivery, allowed/default quotation templates and migration of an order into a new order
of another type.

## Models

- `sale.order.type`: `no_invoice`, `no_delivery`, `template_ids`, `default_template_id`,
  `available_template_ids` (computed), `migration_order_type_ids`.
- `sale.order`: `order_type_no_invoice` (related), migration action
  (`action_migrate_sale_order`) with links to source and migrated orders,
  `_create_invoices` skips orders of `no_invoice` types.
- `sale.order.line`: `_action_launch_stock_rule` skips lines of `no_delivery` types.

## Rules

- `no_invoice` must hold on every path (wizard, list action, code), not only by hiding
  buttons, hence the `_create_invoices` override.

## Pitfalls

- 20.0: `sale.order._create_invoices(final=False, grouped=False)` has no `date` argument
  anymore; keep the override signature in sync with core.
- The form view replaces `route_ids` of `sale_order_type` and moves it into a notebook
  page; the view has priority 99 so other extensions apply first.
