"""seed reference data (data migration for Task 11)

Revision ID: 005_data_seed
Revises: 004_db_logic
Create Date: 2026-11-09 11:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = "005_data_seed"
down_revision = "004_db_logic"
branch_labels = None
depends_on = None


def upgrade() -> None:
    seat_categories_table = sa.table(
        "seat_categories",
        sa.column("name", sa.String),
        sa.column("price_multiplier", sa.Numeric),
    )
    op.bulk_insert(
        seat_categories_table,
        [
            {"name": "Стандарт", "price_multiplier": 1.00},
            {"name": "Комфорт", "price_multiplier": 1.25},
            {"name": "VIP", "price_multiplier": 1.60},
            {"name": "Love Seat (Диван)", "price_multiplier": 2.00},
        ],
    )

    genres_table = sa.table("genres", sa.column("name", sa.String))
    op.bulk_insert(
        genres_table,
        [
            {"name": "Фантастика"},
            {"name": "Боевик"},
            {"name": "Драма"},
            {"name": "Комедия"},
            {"name": "Триллер"},
            {"name": "Анимация"},
            {"name": "Ужасы"},
            {"name": "Приключения"},
        ],
    )


def downgrade() -> None:
    op.execute(
        "DELETE FROM seat_categories WHERE name IN ('Стандарт', 'Комфорт', 'VIP', 'Love Seat (Диван)');"
    )
    op.execute(
        "DELETE FROM genres WHERE name IN ('Фантастика', 'Боевик', 'Драма', 'Комедия', 'Триллер', 'Анимация', 'Ужасы', 'Приключения');"
    )