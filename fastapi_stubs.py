from typing import Optional
from pydantic import BaseModel
from fastapi import FastAPI, Query, HTTPException

from model import ScooterData, TariffZone, UserProfile

app = FastAPI()


@app.get("/scooter-data")
async def get_scooter_data(id: Optional[str] = Query(None, description="An optional ID parameter")):
    if id is None:
        raise HTTPException(status_code=400, detail="ID parameter is required and cannot be empty.")

    return ScooterData(id, 'korolev', 57)


@app.get("/tariff-zone-data")
async def get_tariff_zone_data(id: Optional[str] = Query(None, description="An optional ID parameter")):
    if id is None:
        raise HTTPException(status_code=400, detail="ID parameter is required and cannot be empty.")

    return TariffZone(id, price_per_minute=12, price_unlock=45, default_deposit=300)


@app.get("/user-profile")
async def get_user_profile(id: Optional[str] = Query(None, description="An optional ID parameter")):
    if id is None:
        raise HTTPException(status_code=400, detail="ID parameter is required and cannot be empty.")

    return UserProfile(id, has_subscribtion=False, trusted=False, rides_count=10, current_debt=0, total_debt=0, last_payment_status='success')


@app.get("/configs")
async def get_configs():
    return {'price_coeff_settings': {'surge': 2, 'low_charge_discount': 0.75}}


class MoneyRequest(BaseModel):
    user_id: str
    order_id: str
    amount: int


@app.post("/hold-money-for-order")
async def hold_money_for_order(request: MoneyRequest):
    if request.user_id is None:
        raise HTTPException(status_code=400, detail="user_id parameter is required and cannot be empty.")
    return {'status': 'success'}


@app.post("/clear-money-for-order")
async def clear_money_for_order(request: MoneyRequest):
    if request.user_id is None:
        raise HTTPException(status_code=400, detail="user_id parameter is required and cannot be empty.")
    return {'status': 'success'}


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host='0.0.0.0', port=3629, log_level='info')
