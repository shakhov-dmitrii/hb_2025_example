import os

import requests

from config.urls import BASE_SERVICE_URL
from src import report


@report.step
def get_current_price(coin_ids, vs_currencies="usd"):
    return requests.get(
        url=f"{BASE_SERVICE_URL}/simple/price",
        params={
            "ids": coin_ids,
            "vs_currencies": vs_currencies,
            "x_cg_demo_api_key": os.getenv("X_CG_DEMO_API_KEY", "CG-NP9M4QVUvAN5kJVW57yzSTBr"),
        },
    ).json()
