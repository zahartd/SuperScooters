from typing import Optional
from psycopg import Connection
import structlog

logger = structlog.get_logger(__name__)


def upsert_user_summary(
    conn: Connection,
    user_id: str,
    delta_rides: int = 0,
    delta_debt: int = 0,
    last_payment_status: Optional[str] = None,
) -> None:
    try:
        logger.info(
            "db: upsert user_summary",
            user_id=user_id,
            rides=delta_rides,
            debt=delta_debt,
            payment_status=last_payment_status,
        )
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
            logger.debug(
                "db: user_summary updated successfully",
                user_id=user_id,
            )
    except Exception as e:
        logger.error(
            "db: failed to upsert user_summary",
            user_id=user_id,
            error=str(e),
        )
        raise


def get_user_summary(conn: Connection, user_id: str) -> Optional[dict]:
    logger.debug("db: get user_summary", user_id=user_id)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT user_id, rides_count, current_debt, last_payment_status FROM user_summary WHERE user_id = %(user_id)s",
                {"user_id": user_id},
            )
            result = cur.fetchone()
            logger.debug(
                "db: user_summary fetched successfully",
                user_id=user_id,
                result=result,
            )
            return result
    except Exception as e:
        logger.error(
            "db: failed to get user_summary",
            user_id=user_id,
            error=str(e),
        )
        raise
