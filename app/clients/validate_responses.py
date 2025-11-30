import json
import requests

def validate_scooter_data(raw_data: requests.Response) -> bool:
    json_obj = raw_data.json()
    zone_id = json_obj.get("zone_id", None)
    charge = json_obj.get("charge", None)
    if zone_id:
        try:
            int(zone_id)
        except ValueError:
            return False
    if charge:
        try:
            int(charge)
        except ValueError:
            return False
    return True

def validate_tariff_zone(raw_data: requests.Response) -> bool:
    json_obj = raw_data.json()
    price_per_minute = json_obj.get("price_per_minute", None)
    price_unlock = json_obj.get("price_unlock", None)
    default_deposit = json_obj.get("default_deposit", None)
    if price_per_minute:
        try:
            int(price_per_minute)
        except ValueError:
            return False
    if price_unlock:
        try:
            int(price_unlock)
        except ValueError:
            return False
    if default_deposit:
        try:
            int(default_deposit)
        except ValueError:
            return False
    return True

def validate_user_profile(raw_data: requests.Response) -> bool:
    json_obj = raw_data.json()
    has_subscribtion = json_obj.get("has_subscribtion", None)
    trusted = json_obj.get("trusted", None)
    rides_count = json_obj.get("rides_count", None)
    total_debt = json_obj.get("total_debt", None)
    current_debt = json_obj.get("current_debt", None)
    last_payment_status = json_obj.get("last_payment_status", None)
    if not has_subscribtion:
        return False
    if not trusted:
        return False
    if not last_payment_status:
        return False
    if rides_count:
        try:
            int(rides_count)
        except ValueError:
            return False
    if total_debt:
        try:
            int(total_debt)
        except ValueError:
            return False
    if current_debt:
        try:
            int(current_debt)
        except ValueError:
            return False
    return True

    