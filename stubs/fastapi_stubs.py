import logging
import os
from typing import Optional
import sys
from pathlib import Path
from pydantic import BaseModel
from fastapi import FastAPI, Query, HTTPException

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from app.models import ScooterData, TariffZone, UserProfile

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE = os.getenv("LOG_FILE")

handlers: list[logging.Handler] = [logging.StreamHandler()]
if LOG_FILE:
    log_path = Path(LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    handlers.append(logging.FileHandler(log_path))

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=handlers,
    force=True,
)

app = FastAPI()
logger = logging.getLogger(__name__)


@app.get("/scooter-data")
async def get_scooter_data(id: Optional[str] = Query(None, description="An optional ID parameter")):
    if id is None:
        raise HTTPException(status_code=400, detail="ID parameter is required and cannot be empty.")

    logger.info("stubs: scooter-data id=%s", id)
    return ScooterData(id, 'korolev', 57)


@app.get("/tariff-zone-data")
async def get_tariff_zone_data(id: Optional[str] = Query(None, description="An optional ID parameter")):
    if id is None:
        raise HTTPException(status_code=400, detail="ID parameter is required and cannot be empty.")

    logger.info("stubs: tariff-zone-data id=%s", id)
    return TariffZone(id, price_per_minute=12, price_unlock=45, default_deposit=300)


@app.get("/user-profile")
async def get_user_profile(id: Optional[str] = Query(None, description="An optional ID parameter")):
    if id is None:
        raise HTTPException(status_code=400, detail="ID parameter is required and cannot be empty.")

    logger.info("stubs: user-profile id=%s", id)
    return UserProfile(id, has_subscribtion=False, trusted=False, rides_count=10, current_debt=0, total_debt=0, last_payment_status='success')


@app.get("/configs")
async def get_configs():
    logger.info("stubs: configs")
    return {'price_coeff_settings': {'surge': 2, 'low_charge_discount': 0.75}}


class MoneyRequest(BaseModel):
    user_id: str
    order_id: str
    amount: int


@app.post("/hold-money-for-order")
async def hold_money_for_order(request: MoneyRequest):
    if request.user_id is None:
        raise HTTPException(status_code=400, detail="user_id parameter is required and cannot be empty.")
    logger.info("stubs: hold money user_id=%s order_id=%s amount=%s", request.user_id, request.order_id, request.amount)
    return {'status': 'success'}


@app.post("/clear-money-for-order")
async def clear_money_for_order(request: MoneyRequest):
    if request.user_id is None:
        raise HTTPException(status_code=400, detail="user_id parameter is required and cannot be empty.")
    logger.info(
        "stubs: clear money user_id=%s order_id=%s amount=%s", request.user_id, request.order_id, request.amount
    )
    return {'status': 'success'}


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host='0.0.0.0', port=3629, log_level='info')
