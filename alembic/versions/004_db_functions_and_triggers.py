"""db functions and triggers (Task 6)

Revision ID: 004_db_logic
Revises: 003_users_roles
Create Date: 2026-11-09 10:45:00
"""
from alembic import op

revision = "004_db_logic"
down_revision = "003_users_roles"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Функция 1: Расчет стоимости билета 
    op.execute("""
    CREATE OR REPLACE FUNCTION fn_calculate_ticket_price(p_seance_id INT, p_seat_id INT)
    RETURNS NUMERIC(8, 2) AS $$
    DECLARE
        v_base_price NUMERIC(8, 2);
        v_multiplier NUMERIC(4, 2);
    BEGIN
        SELECT base_price INTO v_base_price FROM seances WHERE id = p_seance_id;
        SELECT sc.price_multiplier INTO v_multiplier
        FROM seats s
        JOIN seat_categories sc ON s.category_id = sc.id
        WHERE s.id = p_seat_id;

        IF v_base_price IS NULL OR v_multiplier IS NULL THEN
            RAISE EXCEPTION 'Не найден сеанс или место для расчета цены';
        END IF;

        RETURN ROUND(v_base_price * v_multiplier, 2);
    END;
    $$ LANGUAGE plpgsql;
    """)

    # Функция 2: Проверка отсутствия накладок в расписании зала 
    op.execute("""
    CREATE OR REPLACE FUNCTION fn_check_hall_schedule_conflict(
        p_hall_id INT, p_start_time TIMESTAMP, p_film_id INT
    ) RETURNS BOOLEAN AS $$
    DECLARE
        v_duration INT;
        v_end_time TIMESTAMP;
        v_conflict_count INT;
    BEGIN
        SELECT duration_minutes INTO v_duration FROM films WHERE id = p_film_id;
        v_end_time := p_start_time + (v_duration + 15) * INTERVAL '1 minute';

        SELECT COUNT(*) INTO v_conflict_count
        FROM seances s
        JOIN films f ON s.film_id = f.id
        WHERE s.hall_id = p_hall_id
          AND (p_start_time < (s.start_time + (f.duration_minutes + 15) * INTERVAL '1 minute')
               AND v_end_time > s.start_time);

        RETURN v_conflict_count = 0;
    END;
    $$ LANGUAGE plpgsql;
    """)

    # Функция 3: Расчет выручки и вознаграждения прокатчика за период
    op.execute("""
    CREATE OR REPLACE FUNCTION fn_calculate_distributor_payout(
        p_distributor_id INT, p_start_date TIMESTAMP, p_end_date TIMESTAMP
    ) RETURNS TABLE(gross_revenue NUMERIC, payout_amount NUMERIC, tickets_sold BIGINT) AS $$
    BEGIN
        RETURN QUERY
        SELECT 
            COALESCE(SUM(t.price), 0.00) AS gross_revenue,
            ROUND(COALESCE(SUM(t.price), 0.00) * (d.commission_percent / 100.0), 2) AS payout_amount,
            COUNT(t.id) AS tickets_sold
        FROM distributors d
        LEFT JOIN films f ON f.distributor_id = d.id
        LEFT JOIN seances s ON s.film_id = f.id
        LEFT JOIN tickets t ON t.seance_id = s.id
        LEFT JOIN orders o ON t.order_id = o.id
            AND o.status = 'PAID'
            AND o.created_at BETWEEN p_start_date AND p_end_date
        WHERE d.id = p_distributor_id
        GROUP BY d.id, d.commission_percent;
    END;
    $$ LANGUAGE plpgsql;
    """)

    # Триггер 1: Контроль принадлежности места залу и автозаполнение цены билета
    op.execute("""
    CREATE OR REPLACE FUNCTION trg_fn_prepare_ticket()
    RETURNS TRIGGER AS $$
    DECLARE
        v_seance_hall INT;
        v_seat_hall INT;
    BEGIN
        SELECT hall_id INTO v_seance_hall FROM seances WHERE id = NEW.seance_id;
        SELECT hall_id INTO v_seat_hall FROM seats WHERE id = NEW.seat_id;

        IF v_seance_hall != v_seat_hall THEN
            RAISE EXCEPTION 'Место (ID=%) не принадлежит залу сеанса (ID=%)', NEW.seat_id, NEW.seance_id;
        END IF;

        IF NEW.price IS NULL OR NEW.price <= 0 THEN
            NEW.price := fn_calculate_ticket_price(NEW.seance_id, NEW.seat_id);
        END IF;

        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;

    CREATE TRIGGER trg_before_insert_ticket
    BEFORE INSERT ON tickets
    FOR EACH ROW EXECUTE FUNCTION trg_fn_prepare_ticket();
    """)

    # Триггер 2: Пересчет итоговой суммы заказа и контроль остатков бара
    op.execute("""
    CREATE OR REPLACE FUNCTION trg_fn_update_order_and_stock()
    RETURNS TRIGGER AS $$
    DECLARE
        v_order_id INT;
        v_tickets_sum NUMERIC(10, 2);
        v_bar_sum NUMERIC(10, 2);
    BEGIN
        IF TG_TABLE_NAME = 'order_bar_items' THEN
            IF TG_OP = 'INSERT' THEN
                UPDATE bar_products
                SET stock_quantity = stock_quantity - NEW.quantity
                WHERE id = NEW.product_id;
            ELSIF TG_OP = 'DELETE' THEN
                UPDATE bar_products
                SET stock_quantity = stock_quantity + OLD.quantity
                WHERE id = OLD.product_id;
            END IF;
        END IF;

        v_order_id := COALESCE(NEW.order_id, OLD.order_id);

        SELECT COALESCE(SUM(price), 0.00) INTO v_tickets_sum FROM tickets WHERE order_id = v_order_id;
        SELECT COALESCE(SUM(quantity * unit_price), 0.00) INTO v_bar_sum FROM order_bar_items WHERE order_id = v_order_id;

        UPDATE orders SET total_amount = v_tickets_sum + v_bar_sum WHERE id = v_order_id;
        RETURN NULL;
    END;
    $$ LANGUAGE plpgsql;

    CREATE TRIGGER trg_after_change_tickets
    AFTER INSERT OR UPDATE OR DELETE ON tickets
    FOR EACH ROW EXECUTE FUNCTION trg_fn_update_order_and_stock();

    CREATE TRIGGER trg_after_change_bar_items
    AFTER INSERT OR UPDATE OR DELETE ON order_bar_items
    FOR EACH ROW EXECUTE FUNCTION trg_fn_update_order_and_stock();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_after_change_bar_items ON order_bar_items;")
    op.execute("DROP TRIGGER IF EXISTS trg_after_change_tickets ON tickets;")
    op.execute("DROP FUNCTION IF EXISTS trg_fn_update_order_and_stock();")
    op.execute("DROP TRIGGER IF EXISTS trg_before_insert_ticket ON tickets;")
    op.execute("DROP FUNCTION IF EXISTS trg_fn_prepare_ticket();")
    op.execute("DROP FUNCTION IF EXISTS fn_calculate_distributor_payout(INT, TIMESTAMP, TIMESTAMP);")
    op.execute("DROP FUNCTION IF EXISTS fn_check_hall_schedule_conflict(INT, TIMESTAMP, INT);")
    op.execute("DROP FUNCTION IF EXISTS fn_calculate_ticket_price(INT, INT);")