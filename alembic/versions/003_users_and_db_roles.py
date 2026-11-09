"""users table and database roles

Revision ID: 003_users_roles
Revises: 002_sales
Create Date: 2026-11-09 10:30:00
"""
from alembic import op
import sqlalchemy as sa

revision = "003_users_roles"
down_revision = "002_sales"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(50), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), server_default="CASHIER", nullable=False),
        sa.Column("is_blocked", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.CheckConstraint("role IN ('ADMIN', 'MANAGER', 'CASHIER')", name="chk_user_role"),
    )

    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'role_cinema_cashier') THEN
            CREATE ROLE role_cinema_cashier;
        END IF;
        IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'role_cinema_manager') THEN
            CREATE ROLE role_cinema_manager;
        END IF;
        IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'role_cinema_admin') THEN
            CREATE ROLE role_cinema_admin;
        END IF;
    END
    $$;

    -- Привилегии Кассира: чтение репертуара и оформление продаж
    GRANT SELECT ON cinemas, halls, seat_categories, seats, films, genres, film_genres, seances, bar_products TO role_cinema_cashier;
    GRANT SELECT, INSERT, UPDATE ON customers, orders, tickets, order_bar_items TO role_cinema_cashier;
    GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO role_cinema_cashier;

    -- Привилегии Менеджера: управление фильмами, сеансами, товарами бара
    GRANT role_cinema_cashier TO role_cinema_manager;
    GRANT INSERT, UPDATE, DELETE ON distributors, films, genres, film_genres, seances, bar_products TO role_cinema_manager;

    -- Привилегии Администратора: полный доступ к таблицам предметной области и пользователям
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO role_cinema_admin;
    GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO role_cinema_admin;
    """)


def downgrade() -> None:
    op.execute("""
    REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM role_cinema_cashier, role_cinema_manager, role_cinema_admin;
    REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public FROM role_cinema_cashier, role_cinema_manager, role_cinema_admin;
    DROP ROLE IF EXISTS role_cinema_admin;
    DROP ROLE IF EXISTS role_cinema_manager;
    DROP ROLE IF EXISTS role_cinema_cashier;
    """)
    op.drop_table("users")