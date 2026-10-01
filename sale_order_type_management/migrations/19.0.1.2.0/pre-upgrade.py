# Copyright 2025, Weboffice IT-Service und Marketing GmbH & Co KG


def migrate(cr, version):
    cr.execute("""
        ALTER TABLE sale_order_type
        RENAME COLUMN no_delivery_address TO no_delivery;
    """)
