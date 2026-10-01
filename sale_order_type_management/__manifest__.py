# -*- coding: utf-8 -*-
# Copyright 2026, Weboffice IT-Service und Marketing GmbH & Co KG
# noinspection PyStatementEffect
{
    'name': 'Sale Order Type Management',

    'summary': 'Configure Sale Order Types and migrate them into a new Sale Order for workflows',

    'author': 'Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/sale-workflow',
    'category': 'Sales Management',
    'version': '19.0.3.0.0',
    "license": "AGPL-3",

    'depends': ['sale_order_type', 'sale_management', 'sale_stock'],

    'data': [
        'views/sale_order_view.xml',
        'views/sale_order_type_view.xml',
    ],

    'installable': True
}
