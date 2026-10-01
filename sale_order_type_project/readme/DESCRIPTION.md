Sets a project template on sale order types. Confirming an order of such a type
creates the order project from that template.

- Template tasks can be marked *optional*; they are only created when the order type
  or an order line (task template) asks for them.
- Task dependencies of optional template tasks are rebuilt between the created tasks.
