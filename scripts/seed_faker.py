import sys
import os
import random
from datetime import datetime, timedelta, date
from decimal import Decimal

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from faker import Faker
from passlib.context import CryptContext
from sqlalchemy import select, func

from app.database import SessionLocal
from app.models import (
    User, Cinema, Hall, SeatCategory, Seat,
    Distributor, Film, Genre, Seance,
    Customer, Order, Ticket, BarProduct, OrderBarItem
)

fake = Faker("ru_RU")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def seed_database():
    session = SessionLocal()
    try:
        existing_orders = session.scalar(select(func.count(Order.id)))
        if existing_orders and existing_orders >= 1000:
            print(f"[INFO] База уже наполнена ({existing_orders} заказов). Пропуск генерации.")
            return

        print("[1/8] Создание демонстрационных пользователей (Задание 1)...")
        demo_users = [
            User(
                username="admin",
                password_hash=pwd_context.hash("admin123"),
                role="ADMIN",
                is_blocked=False,
            ),
            User(
                username="manager",
                password_hash=pwd_context.hash("manager123"),
                role="MANAGER",
                is_blocked=False,
            ),
            User(
                username="cashier",
                password_hash=pwd_context.hash("cashier123"),
                role="CASHIER",
                is_blocked=False,
            ),
        ]
        session.add_all(demo_users)
        session.flush()

        print("[2/8] Создание кинотеатров, залов и мест...")
        categories = list(session.scalars(select(SeatCategory)).all())
        cat_map = {c.name: c.id for c in categories}

        cinemas_data = [
            {"name": "Синема Парк Сити Молл", "city": "Белгород", "address": "ул. Щорса, 64", "phone": "+7 (4722) 20-50-10"},
            {"name": "Русич", "city": "Белгород", "address": "пр-т Ватутина, 8", "phone": "+7 (4722) 52-97-52"},
            {"name": "Победа", "city": "Белгород", "address": "ул. 50-летия Белгородской области, 8Б", "phone": "+7 (4722) 32-42-11"},
            {"name": "ГриннФильм", "city": "Белгород", "address": "пр-т Богдана Хмельницкого, 137Т", "phone": "+7 (4722) 78-72-22"},
        ]

        halls_list = []
        seats_by_hall = {}

        for c_data in cinemas_data:
            cinema = Cinema(**c_data)
            session.add(cinema)
            session.flush()

            for h_idx in range(1, 4):
                rows_count = 6
                seats_per_row = 10
                hall = Hall(
                    cinema_id=cinema.id,
                    name=f"Зал {h_idx}" if h_idx < 3 else "VIP IMAX Зал",
                    capacity=rows_count * seats_per_row,
                )
                session.add(hall)
                session.flush()
                halls_list.append(hall)
                seats_by_hall[hall.id] = []

                for r in range(1, rows_count + 1):
                    for s in range(1, seats_per_row + 1):
                        if r == rows_count:
                            cat_id = cat_map.get("Love Seat (Диван)", categories[-1].id)
                        elif r in (3, 4) and 3 <= s <= 8:
                            cat_id = cat_map.get("VIP", categories[0].id)
                        elif r >= 2:
                            cat_id = cat_map.get("Комфорт", categories[0].id)
                        else:
                            cat_id = cat_map.get("Стандарт", categories[0].id)

                        seat = Seat(
                            hall_id=hall.id,
                            category_id=cat_id,
                            row_number=r,
                            seat_number=s,
                        )
                        session.add(seat)
                        seats_by_hall[hall.id].append(seat)

        session.flush()

        print("[3/8] Создание дистрибьюторов и фильмов...")
        distributors_data = [
            ("Централ Партнершип", Decimal("45.00")),
            ("Каропрокат", Decimal("42.50")),
            ("Вольга", Decimal("40.00")),
            ("Атмосфера Кино", Decimal("48.00")),
            ("Наше Кино", Decimal("38.00")),
        ]
        distributors = []
        for name, comm in distributors_data:
            d = Distributor(name=name, commission_percent=comm)
            session.add(d)
            distributors.append(d)
        session.flush()

        genres = list(session.scalars(select(Genre)).all())

        films_titles = [
            ("Дюна: Мессия", 155, "16+"),
            ("Мастер и Маргарита", 157, "18+"),
            ("Холоп 3", 110, "12+"),
            ("Майор Гром: Игра", 168, "16+"),
            ("Бременские музыканты", 116, "6+"),
            ("Сто лет тому вперёд", 142, "12+"),
            ("Лёд 3", 134, "6+"),
            ("Вызов: Возвращение", 160, "12+"),
            ("Чебурашка 2", 115, "6+"),
            ("Оппенгеймер", 180, "16+"),
            ("Интерстеллар (Перевыпуск)", 169, "16+"),
            ("Головоломка 2", 96, "6+"),
        ]

        films = []
        for title, duration, rating in films_titles:
            film = Film(
                distributor_id=random.choice(distributors).id,
                title=title,
                duration_minutes=duration,
                age_rating=rating,
                release_date=date.today() - timedelta(days=random.randint(10, 120)),
            )
            film.genres = random.sample(genres, k=random.randint(1, 3))
            session.add(film)
            films.append(film)
        session.flush()

        print("[4/8] Создание ассортимента кинобара...")
        bar_items_data = [
            ("Попкорн солёный (Большой)", Decimal("450.00"), 5000),
            ("Попкорн карамельный (Средний)", Decimal("380.00"), 5000),
            ("Попкорн сырный (Малый)", Decimal("290.00"), 5000),
            ("Начос с сырным соусом", Decimal("420.00"), 5000),
            ("Кола Разливная 0.5л", Decimal("220.00"), 5000),
            ("Кола Разливная 0.8л", Decimal("290.00"), 5000),
            ("Вода негазированная 0.5л", Decimal("150.00"), 5000),
            ("Комбо-набор Для двоих", Decimal("950.00"), 5000),
        ]
        bar_products = []
        for name, price, stock in bar_items_data:
            bp = BarProduct(name=name, price=price, stock_quantity=stock)
            session.add(bp)
            bar_products.append(bp)
        session.flush()

        print("[5/8] Генерация расписания сеансов...")
        seances = []
        base_dt = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0) - timedelta(days=30)

        for day_offset in range(35):  
            current_day = base_dt + timedelta(days=day_offset)
            for hall in halls_list:
                for hour, minute, base_p in [(10, 0, "250.00"), (14, 0, "350.00"), (18, 0, "450.00"), (21, 30, "500.00")]:
                    seance = Seance(
                        film_id=random.choice(films).id,
                        hall_id=hall.id,
                        start_time=current_day.replace(hour=hour, minute=minute),
                        base_price=Decimal(base_p),
                    )
                    session.add(seance)
                    seances.append(seance)
        session.flush()

        print("[6/8] Генерация 300 покупателей через Faker...")
        customers = []
        used_phones = set()
        used_emails = set()

        for i in range(300):
            phone = f"+7 (9{random.randint(10, 99)}) {random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(10, 99)}"
            while phone in used_phones:
                phone = f"+7 (9{random.randint(10, 99)}) {random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(10, 99)}"
            used_phones.add(phone)

            email = f"user_{i}_{fake.lexify(text='????')}@example.com"
            used_emails.add(email)

            c = Customer(
                full_name=fake.name(),
                phone=phone,
                email=email,
            )
            session.add(c)
            customers.append(c)
        session.flush()

        print("[7/8] Генерация 1200 заказов, ~2400 билетов и ~1200 позиций бара...")
        occupied_seats = {s.id: set() for s in seances}

        orders_created = 0
        tickets_created = 0
        bar_items_created = 0

        for _ in range(1200):
            seance = random.choice(seances)
            hall_seats = seats_by_hall[seance.hall_id]
            available_seats = [s for s in hall_seats if s.id not in occupied_seats[seance.id]]

            if len(available_seats) < 2:
                continue

            order_dt = seance.start_time - timedelta(hours=random.randint(1, 48))
            status = random.choices(
                ["PAID", "PENDING", "CANCELLED", "REFUNDED"],
                weights=[82, 8, 6, 4],
                k=1
            )[0]

            order = Order(
                customer_id=random.choice(customers).id if random.random() < 0.85 else None,
                created_at=order_dt,
                status=status,
                total_amount=Decimal("0.00"),  
            )
            session.add(order)
            session.flush()
            orders_created += 1

            chosen_seats = random.sample(available_seats, k=random.randint(1, min(3, len(available_seats))))
            for seat in chosen_seats:
                occupied_seats[seance.id].add(seat.id)
                ticket = Ticket(
                    order_id=order.id,
                    seance_id=seance.id,
                    seat_id=seat.id,
                    price=Decimal("0.00"),  
                )
                session.add(ticket)
                tickets_created += 1

            chosen_products = random.sample(bar_products, k=random.randint(1, 2))
            for prod in chosen_products:
                bar_item = OrderBarItem(
                    order_id=order.id,
                    product_id=prod.id,
                    quantity=random.randint(1, 2),
                    unit_price=prod.price,
                )
                session.add(bar_item)
                bar_items_created += 1

        print("[8/8] Фиксация транзакции в СУБД...")
        session.commit()
        print(
            f"[SUCCESS] Генерация завершена успешно!\n"
            f"  - Заказов (orders): {orders_created}\n"
            f"  - Билетов (tickets): {tickets_created}\n"
            f"  - Позиций бара (order_bar_items): {bar_items_created}"
        )

    except Exception as e:
        session.rollback()
        print(f"[ERROR] Ошибка при заполнении БД: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed_database()