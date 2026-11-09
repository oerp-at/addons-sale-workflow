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
  `_create_invoices` skips orders of `no_invoice` types, `_check_no_invoice_order_type`
  raises naming every blocked order (`<order> (<type>)`);
  `_create_down_payment_section_line_if_needed` and
  `_create_down_payment_lines_from_base_lines` call it first.
- `sale.advance.payment.inv` (`wizards/sale_make_invoice_advance.py`): `create_invoices`
  refuses the whole selection if it holds a `no_invoice` order (no partial invoicing).
- `sale.order.line`: `_action_launch_stock_rule` skips lines of `no_delivery` types.

## Rules

- `no_invoice` must hold on every path (wizard, list action, code), not only by hiding
  buttons, hence the `_create_invoices` override.
- Down payments: the invoicing wizard creates down payment invoices itself via
  `account.move.create`, bypassing `_create_invoices`. Every down payment path (core and
  modules rebuilding it without super) adds the section and the lines to the order
  first, so the order hooks stop it before anything is written.

## Pitfalls

- 20.0: `sale.order._create_invoices(final=False, grouped=False)` has no `date` argument
  anymore; keep the override signature in sync with core.
- The form view replaces `route_ids` of `sale_order_type` and moves it into a notebook
  page; the view has priority 99 so other extensions apply first.
- The de.po entry of the `no_invoice` message needs the `#. odoo-python` flag, otherwise
  the code translation is not loaded (`test_message_translated`).

## Tests

- `tests/test_sale_order_type_management.py`: migration, templates, `_create_invoices`.
- `tests/test_no_invoice_down_payment.py`: percentage/fixed down payment via the wizard
  and its `_create_invoices`, the order hooks directly, mixed selection creates nothing,
  regular orders still invoiced, German message.
