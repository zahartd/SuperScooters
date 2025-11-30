from app.models import ConfigMap

static_config = ConfigMap({
    "price_coeff_settings": {
        "surge": 2.5,
        "low_charge_discount": 0.5,
    }
})
