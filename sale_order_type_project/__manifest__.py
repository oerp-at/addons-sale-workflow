# -*- coding: utf-8 -*-
# Copyright 2026, Weboffice IT-Service und Marketing GmbH & Co KG

# noinspection PyStatementEffect
{
    'name': 'Sale Order Type Project',

    'summary': 'Set a Project Template for Sale Order Types and gain the ability to set optional Tasks',

    'author': 'Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/sale-workflow',
    'category': 'Sales Management',
    'version': '19.0.1.3.2',
    "license": "AGPL-3",

    'depends': ['sale_order_type_management', 'sale_order_task', 'sale_project'],

    'data': [
        'views/project_task_views.xml',
        'views/sale_order_type_view.xml',
    ],

    'installable': True
}
