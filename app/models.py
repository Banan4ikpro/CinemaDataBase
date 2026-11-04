from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import (
    String, Integer, Numeric, ForeignKey, DateTime, Date,
    CheckConstraint, UniqueConstraint, Index, Table, Column
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


film_genres = Table(
    "film_genres",
    Base.metadata,
    Column("film_id", ForeignKey("films.id", ondelete="CASCADE"), primary_key=True),
    Column("genre_id", ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="CASHIER")
    is_blocked: Mapped[bool] = mapped_column(default=False, nullable=False)

    __table_args__ = (
        CheckConstraint("role IN ('ADMIN', 'MANAGER', 'CASHIER')", name="chk_user_role"),
    )


class Cinema(Base):
    __tablename__ = "cinemas"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30))

    halls: Mapped[list["Hall"]] = relationship(back_populates="cinema", cascade="all, delete-orphan")


class Hall(Base):
    __tablename__ = "halls"

    id: Mapped[int] = mapped_column(primary_key=True)
    cinema_id: Mapped[int] = mapped_column(ForeignKey("cinemas.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)

    cinema: Mapped["Cinema"] = relationship(back_populates="halls")
    seats: Mapped[list["Seat"]] = relationship(back_populates="hall", cascade="all, delete-orphan")
    seances: Mapped[list["Seance"]] = relationship(back_populates="hall")

    __table_args__ = (
        CheckConstraint("capacity > 0", name="chk_hall_capacity"),
        UniqueConstraint("cinema_id", "name", name="uq_cinema_hall_name"),
    )


class SeatCategory(Base):
    __tablename__ = "seat_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    price_multiplier: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)

    seats: Mapped[list["Seat"]] = relationship(back_populates="category")

    __table_args__ = (
        CheckConstraint("price_multiplier > 0", name="chk_seat_cat_multiplier"),
    )


class Seat(Base):
    __tablename__ = "seats"

    id: Mapped[int] = mapped_column(primary_key=True)
    hall_id: Mapped[int] = mapped_column(ForeignKey("halls.id", ondelete="CASCADE"), nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("seat_categories.id", ondelete="RESTRICT"), nullable=False)
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    seat_number: Mapped[int] = mapped_column(Integer, nullable=False)

    hall: Mapped["Hall"] = relationship(back_populates="seats")
    category: Mapped["SeatCategory"] = relationship(back_populates="seats")
    tickets: Mapped[list["Ticket"]] = relationship(back_populates="seat")

    __table_args__ = (
        CheckConstraint("row_number > 0 AND seat_number > 0", name="chk_seat_coords"),
        UniqueConstraint("hall_id", "row_number", "seat_number", name="uq_hall_row_seat"),
    )


class Distributor(Base):
    __tablename__ = "distributors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    commission_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)

    films: Mapped[list["Film"]] = relationship(back_populates="distributor")

    __table_args__ = (
        CheckConstraint("commission_percent >= 0 AND commission_percent <= 100", name="chk_dist_comm"),
    )


class Film(Base):
    __tablename__ = "films"

    id: Mapped[int] = mapped_column(primary_key=True)
    distributor_id: Mapped[int] = mapped_column(ForeignKey("distributors.id", ondelete="RESTRICT"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    age_rating: Mapped[str] = mapped_column(String(5), nullable=False)
    release_date: Mapped[date] = mapped_column(Date, nullable=False)

    distributor: Mapped["Distributor"] = relationship(back_populates="films")
    genres: Mapped[list["Genre"]] = relationship(secondary=film_genres, back_populates="films")
    seances: Mapped[list["Seance"]] = relationship(back_populates="film")

    __table_args__ = (
        CheckConstraint("duration_minutes > 0", name="chk_film_duration"),
        CheckConstraint("age_rating IN ('0+', '6+', '12+', '16+', '18+')", name="chk_film_rating"),
    )


class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)

    films: Mapped[list["Film"]] = relationship(secondary=film_genres, back_populates="genres")


class Seance(Base):
    __tablename__ = "seances"

    id: Mapped[int] = mapped_column(primary_key=True)
    film_id: Mapped[int] = mapped_column(ForeignKey("films.id", ondelete="RESTRICT"), nullable=False)
    hall_id: Mapped[int] = mapped_column(ForeignKey("halls.id", ondelete="RESTRICT"), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    base_price: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)

    film: Mapped["Film"] = relationship(back_populates="seances")
    hall: Mapped["Hall"] = relationship(back_populates="seances")
    tickets: Mapped[list["Ticket"]] = relationship(back_populates="seance")

    __table_args__ = (
        CheckConstraint("base_price > 0", name="chk_seance_base_price"),
        Index("idx_seances_start_time", "start_time"),
        Index("idx_seances_film_id", "film_id"),
    )


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    phone: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(150), unique=True)

    orders: Mapped[list["Order"]] = relationship(back_populates="customer")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)

    customer: Mapped["Customer | None"] = relationship(back_populates="orders")
    tickets: Mapped[list["Ticket"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    bar_items: Mapped[list["OrderBarItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("status IN ('PENDING', 'PAID', 'CANCELLED', 'REFUNDED')", name="chk_order_status"),
        CheckConstraint("total_amount >= 0", name="chk_order_total_amount"),
        Index("idx_orders_created_at", "created_at"),
        Index("idx_orders_customer_id", "customer_id"),
    )


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    seance_id: Mapped[int] = mapped_column(ForeignKey("seances.id", ondelete="RESTRICT"), nullable=False)
    seat_id: Mapped[int] = mapped_column(ForeignKey("seats.id", ondelete="RESTRICT"), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)

    order: Mapped["Order"] = relationship(back_populates="tickets")
    seance: Mapped["Seance"] = relationship(back_populates="tickets")
    seat: Mapped["Seat"] = relationship(back_populates="tickets")

    __table_args__ = (
        CheckConstraint("price > 0", name="chk_ticket_price"),
        UniqueConstraint("seance_id", "seat_id", name="uq_seance_seat"),
        Index("idx_tickets_seance_id", "seance_id"),
        Index("idx_tickets_order_id", "order_id"),
    )


class BarProduct(Base):
    __tablename__ = "bar_products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    order_items: Mapped[list["OrderBarItem"]] = relationship(back_populates="product")

    __table_args__ = (
        CheckConstraint("price > 0", name="chk_bar_product_price"),
        CheckConstraint("stock_quantity >= 0", name="chk_bar_product_stock"),
    )


class OrderBarItem(Base):
    __tablename__ = "order_bar_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("bar_products.id", ondelete="RESTRICT"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)

    order: Mapped["Order"] = relationship(back_populates="bar_items")
    product: Mapped["BarProduct"] = relationship(back_populates="order_items")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="chk_bar_item_qty"),
        CheckConstraint("unit_price > 0", name="chk_bar_item_price"),
    )