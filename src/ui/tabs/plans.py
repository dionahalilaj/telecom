PLAN_LIMITS = {
    "Basic": {
        "data_limit_mb": 3000,
        "voice_limit_min": 200,
        "sms_limit": 100,
        "roaming_limit_mb": 250,
        "roaming_limit_min": 20,
        "base_price_eur": 15,
    },
    "Standard": {
        "data_limit_mb": 8000,
        "voice_limit_min": 500,
        "sms_limit": 200,
        "roaming_limit_mb": 500,
        "roaming_limit_min": 40,
        "base_price_eur": 25,
    },
    "Premium": {
        "data_limit_mb": 15000,
        "voice_limit_min": 1000,
        "sms_limit": 300,
        "roaming_limit_mb": 2000,
        "roaming_limit_min": 100,
        "base_price_eur": 40,
    },
    "SuperPremium": {
        "data_limit_mb": 50000,
        "voice_limit_min": 2000,
        "sms_limit": 1000,
        "roaming_limit_mb": 5000,
        "roaming_limit_min": 200,
        "base_price_eur": 55,
    },
    "Youth": {
        "data_limit_mb": 5000,
        "voice_limit_min": 300,
        "sms_limit": 200,
        "roaming_limit_mb": 500,
        "roaming_limit_min": 30,
        "base_price_eur": 20,
    },
    "Business": {
        "data_limit_mb": 20000,
        "voice_limit_min": 3000,
        "sms_limit": 1000,
        "roaming_limit_mb": 7000,
        "roaming_limit_min": 500,
        "base_price_eur": 70,
    },
}

COSTS = {
    "extra_data_per_mb": 0.001,
    "extra_voice_per_min": 0.02,
    "extra_sms_per_unit": 0.01,
    "extra_roaming_mb": 0.005,
    "extra_roaming_min": 0.10,
}
