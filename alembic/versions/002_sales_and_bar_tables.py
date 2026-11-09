"""sales and bar tables

Revision ID: 002_sales
Revises: 001_core
Create Date: 2026-11-09 10:15:00
"""
from alembic import op
import sqlalchemy as sa

revision = "002_sales"
down_revision = "001_core"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("full_name", sa.String(150), nullable=False),
        sa.Column("phone", sa.String(30), nullable=False, unique=True),
        sa.Column("email", sa.String(150), nullable=True, unique=True),
    )

    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("status", sa.String(20), server_default="PENDING", nullable=False),
        sa.Column("total_amount", sa.Numeric(10, 2), server_default="0.00", nullable=False),
        sa.CheckConstraint("status IN ('PENDING', 'PAID', 'CANCELLED', 'REFUNDED')", name="chk_order_status"),
        sa.CheckConstraint("total_amount >= 0", name="chk_order_total_amount"),
    )
    op.create_index("idx_orders_created_at", "orders", ["created_at"])
    op.create_index("idx_orders_customer_id", "orders", ["customer_id"])

    op.create_table(
        "tickets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("seance_id", sa.Integer(), sa.ForeignKey("seances.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("seat_id", sa.Integer(), sa.ForeignKey("seats.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("price", sa.Numeric(8, 2), nullable=False),
        sa.CheckConstraint("price > 0", name="chk_ticket_price"),
        sa.UniqueConstraint("seance_id", "seat_id", name="uq_seance_seat"),
    )
    op.create_index("idx_tickets_seance_id", "tickets", ["seance_id"])
    op.create_index("idx_tickets_order_id", "tickets", ["order_id"])

    op.create_table(
        "bar_products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False, unique=True),
        sa.Column("price", sa.Numeric(8, 2), nullable=False),
        sa.Column("stock_quantity", sa.Integer(), server_default="0", nullable=False),
        sa.CheckConstraint("price > 0", name="chk_bar_product_price"),
        sa.CheckConstraint("stock_quantity >= 0", name="chk_bar_product_stock"),
    )

    op.create_table(
        "order_bar_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("bar_products.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(8, 2), nullable=False),
        sa.CheckConstraint("quantity > 0", name="chk_bar_item_qty"),
        sa.CheckConstraint("unit_price > 0", name="chk_bar_item_price"),
    )


def downgrade() -> None:
    op.drop_table("order_bar_items")
    op.drop_table("bar_products")
    op.drop_index("idx_tickets_order_id", table_name="tickets")
    op.drop_index("idx_tickets_seance_id", table_name="tickets")
    op.drop_table("tickets")
    op.drop_index("idx_orders_customer_id", table_name="orders")
    op.drop_index("idx_orders_created_at", table_name="orders")
    op.drop_table("orders")
    op.drop_table("customers")