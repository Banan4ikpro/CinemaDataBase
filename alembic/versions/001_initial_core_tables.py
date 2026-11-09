"""initial core tables

Revision ID: 001_core
Revises: 
Create Date: 2026-11-09 10:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = "001_core"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cinemas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("address", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(30), nullable=True),
    )

    op.create_table(
        "halls",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cinema_id", sa.Integer(), sa.ForeignKey("cinemas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.CheckConstraint("capacity > 0", name="chk_hall_capacity"),
        sa.UniqueConstraint("cinema_id", "name", name="uq_cinema_hall_name"),
    )

    op.create_table(
        "seat_categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(50), nullable=False, unique=True),
        sa.Column("price_multiplier", sa.Numeric(4, 2), nullable=False),
        sa.CheckConstraint("price_multiplier > 0", name="chk_seat_cat_multiplier"),
    )

    op.create_table(
        "seats",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("hall_id", sa.Integer(), sa.ForeignKey("halls.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category_id", sa.Integer(), sa.ForeignKey("seat_categories.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("seat_number", sa.Integer(), nullable=False),
        sa.CheckConstraint("row_number > 0 AND seat_number > 0", name="chk_seat_coords"),
        sa.UniqueConstraint("hall_id", "row_number", "seat_number", name="uq_hall_row_seat"),
    )

    op.create_table(
        "distributors",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False, unique=True),
        sa.Column("commission_percent", sa.Numeric(5, 2), nullable=False),
        sa.CheckConstraint("commission_percent >= 0 AND commission_percent <= 100", name="chk_dist_comm"),
    )

    op.create_table(
        "films",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("distributor_id", sa.Integer(), sa.ForeignKey("distributors.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("age_rating", sa.String(5), nullable=False),
        sa.Column("release_date", sa.Date(), nullable=False),
        sa.CheckConstraint("duration_minutes > 0", name="chk_film_duration"),
        sa.CheckConstraint("age_rating IN ('0+', '6+', '12+', '16+', '18+')", name="chk_film_rating"),
    )

    op.create_table(
        "genres",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(80), nullable=False, unique=True),
    )

    op.create_table(
        "film_genres",
        sa.Column("film_id", sa.Integer(), sa.ForeignKey("films.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("genre_id", sa.Integer(), sa.ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "seances",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("film_id", sa.Integer(), sa.ForeignKey("films.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("hall_id", sa.Integer(), sa.ForeignKey("halls.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("start_time", sa.DateTime(), nullable=False),
        sa.Column("base_price", sa.Numeric(8, 2), nullable=False),
        sa.CheckConstraint("base_price > 0", name="chk_seance_base_price"),
    )
    op.create_index("idx_seances_start_time", "seances", ["start_time"])
    op.create_index("idx_seances_film_id", "seances", ["film_id"])


def downgrade() -> None:
    op.drop_index("idx_seances_film_id", table_name="seances")
    op.drop_index("idx_seances_start_time", table_name="seances")
    op.drop_table("seances")
    op.drop_table("film_genres")
    op.drop_table("genres")
    op.drop_table("films")
    op.drop_table("distributors")
    op.drop_table("seats")
    op.drop_table("seat_categories")
    op.drop_table("halls")
    op.drop_table("cinemas")