from app.models import TariffZone, UserProfile


def calc_deposit(
    user_profile: UserProfile,
    tariff: TariffZone,
    deposit_multiplier: float,
    deposit_debt_threshold: int,
) -> int:
    if user_profile.trusted:
        return 0
    multiplier = deposit_multiplier if user_profile.total_debt > deposit_debt_threshold else 1.0
    return int(tariff.default_deposit * multiplier)
