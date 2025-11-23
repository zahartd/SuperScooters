import time
import uuid
from datetime import datetime

import data_requests as dr
from model import OfferData, OrderData

# amazingly fast and totally inreliable databases
offers_database = {}
orders_database = {}

MAGIC_CONSTANT = 28
MAGIC_CONSTANT2 = 5


def handle_create_offer_request(scooter_id: str, user_id: str):
    # quite a sequential execution of requests, could be improved!
    scooter_data = dr.get_scooter_data(scooter_id)

    tariff = dr.get_tariff_zone(scooter_data.zone_id)

    user_profile = dr.get_user_profile(user_id)

    configs = dr.get_configs()

    # all fetching is done, finally....
    # start building actual response

    # adjust price_per_minute with configuration settings
    actual_price_per_min = tariff.price_per_minute
    if configs.price_coeff_settings is not None:
        actual_price_per_min = int(actual_price_per_min * float(configs.price_coeff_settings['surge']))
        if scooter_data.charge < MAGIC_CONSTANT:
            actual_price_per_min = int(actual_price_per_min * float(configs.price_coeff_settings['low_charge_discount']))

    actual_price_unlock = 0 if user_profile.has_subscribtion else tariff.price_unlock

    offer = OfferData(
        str(uuid.uuid4()),
        user_id=user_id,
        scooter_id=scooter_id,
        zone_id=scooter_data.zone_id,
        price_per_minute=actual_price_per_min,
        price_unlock=actual_price_unlock,
        deposit=0 if user_profile.trusted else tariff.default_deposit
    )

    print(f'>> New offer! {offer}')

    # save it immediately
    offers_database[offer.id] = offer
    return offer


def handle_start_order_request(offer_id: str):
    offer = offers_database.pop(offer_id)
    # race condition is possible here!

    order = OrderData(
        str(uuid.uuid4()),
        user_id=offer.user_id,
        scooter_id=offer.scooter_id,
        price_per_minute=offer.price_per_minute,
        price_unlock=offer.price_unlock,
        deposit=offer.deposit,
        total_amount=0,
        start_time=datetime.now(),
        finish_time=None
    )
    # money is very important thing!
    dr.hold_money_for_order(offer.user_id, order.id, offer.deposit)

    print(f'>> Order was started!')

    orders_database[order.id] = order
    return order


def handle_finish_order_request(order_id: str):
    order = orders_database.pop(order_id)

    order.finish_time = datetime.now()
    if (order.finish_time - order.start_time).total_seconds() < MAGIC_CONSTANT2:
        dr.clear_money_for_order(order.user_id, order_id, 0)
        print(f'>> Order was cancelled!')
    else:
        order.total_amount = int((order.finish_time - order.start_time).total_seconds()) * order.price_per_minute // 60 + order.price_unlock
        dr.clear_money_for_order(order.user_id, order_id, order.total_amount)
        print(f'>> Order was finished! Total amount: {order.total_amount}')

    orders_database[order.id] = order


if __name__ == '__main__':
    print('> Starting first scenario! <')
    offer1 = handle_create_offer_request('some-scooter-id', 'some-user-id')
    order1 = handle_start_order_request(offer1.id)

    time.sleep(1)
    handle_finish_order_request(order1.id)
    print('< First scenario is over!\n\n')

    print('> Starting second scenario! <')
    offer2 = handle_create_offer_request('some-scooter-id', 'some-user-id')
    order2 = handle_start_order_request(offer2.id)

    time.sleep(8)
    handle_finish_order_request(order2.id)
    print('< Second scenario is over!\n\n')
