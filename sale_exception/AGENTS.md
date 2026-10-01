# sale_exception

## Purpose

Applies `base_exception` rules to sale orders and order lines: orders with matching
exceptions cannot be confirmed (blocking rules) or need a confirmation (warnings).

## Models

- `sale.order` (inherits `base.exception`): checks on `action_confirm` and on writes of
  the fields from `_fields_trigger_check_exception`; `ignore_exception` lets a user
  confirm anyway; cron/`test_all_draft_orders` re-checks draft orders.
- `sale.order.line` (inherits `base.exception.method`): line rules, summary shown on the
  line (`exceptions_summary`, `is_exception_danger`).
- `exception.rule`: adds `sale.order` / `sale.order.line` to `model`.
- `sale.exception.confirm`: wizard to confirm/ignore exceptions.
- `res.company`: `sale_exception_show_popup`.

## Pitfalls

- Himmelblau adds its own rules (e.g. CRIF credit check for persons) as data in
  `woa_himmelblau_sale`; they depend on `is_company` (see `partner_company_manual`).
- 20.0: security as `security/ir.access.csv`.
