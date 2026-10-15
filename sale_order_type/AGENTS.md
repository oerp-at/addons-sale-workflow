# sale_order_type

## Purpose

Types for sale orders (`sale.order.type`) that set defaults on the order and its
invoices: sequence, journal, warehouse, picking policy, payment term, pricelist,
incoterm, salesperson/team, quotation validity, analytic distribution, routes.

## Models

- `sale.order.type`: the configuration (company-dependent, multi-company rule).
- `sale.order`: `type_id` (computed from partner/user/team, precomputed, editable);
  applies the type defaults; the order name comes from the type sequence.
- `account.move`: `sale_type_id` computed from the orders, defaults the journal.
- `res.partner`: default `sale_type` per partner.
- Reports: `sale.report.type_id`, `account.invoice.report.sale_type_id`.

## Pitfalls

- 20.0: `account.invoice.report` is built with `_select_list(table)` (list of SQL
  terms), not `_select()`; extend it with `[*super()._select_list(table), ...]`.
- 20.0: the multi-company record rule is a row without group in `ir.access.csv`; the
  `model_id` column needs the model name (`sale.order.type`), not the model xmlid.
- 20.0: `BaseCommon` tests run as a basic test user; `TestSaleOrderType` sets
  `_test_user_groups = ()` to keep the admin environment.
- Quotation validity uses the user's today (`fields.Date.context_today`).
- Himmelblau builds `sale_order_type_management` and `sale_order_type_project` on top.
