# Copyright 2026, Weboffice IT-Service und Marketing GmbH & Co KG

# noinspection PyStatementEffect
{
    "name": "Sale Order Task",
    "summary": "Configure Task Templates that will be created in the sale order project",
    "author": "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/sale-workflow",
    "category": "Sales Management",
    "version": "20.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["sale_management", "sale_project"],
    "data": [
        "views/project_task_views.xml",
        "views/project_task_type_link_views.xml",
        "views/project_menus.xml",
        "views/product_views.xml",
        "security/ir.access.csv",
    ],
    "installable": True,
}
