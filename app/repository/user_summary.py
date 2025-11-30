from typing import Optional

from psycopg import Connection


def upsert_user_summary(
    conn: Connection,
    user_id: str,
    delta_rides: int = 0,
    delta_debt: int = 0,
    last_payment_status: Optional[str] = None,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO user_summary (user_id, rides_count, current_debt, last_payment_status)
            VALUES (%(user_id)s, %(delta_rides)s, %(delta_debt)s, %(last_payment_status)s)
            ON CONFLICT (user_id) DO UPDATE
            SET rides_count = user_summary.rides_count + EXCLUDED.rides_count,
                current_debt = user_summary.current_debt + EXCLUDED.current_debt,
                last_payment_status = COALESCE(EXCLUDED.last_payment_status, user_summary.last_payment_status)
            """,
            {
                "user_id": user_id,
                "delta_rides": delta_rides,
                "delta_debt": delta_debt,
                "last_payment_status": last_payment_status,
            },
        )


def get_user_summary(conn: Connection, user_id: str) -> Optional[dict]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT user_id, rides_count, current_debt, last_payment_status FROM user_summary WHERE user_id = %(user_id)s",
            {"user_id": user_id},
        )
        return cur.fetchone()
