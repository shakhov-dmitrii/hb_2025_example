import os

BASE_SERVICE_URL: str = os.getenv(
    key="BASE_SERVICE_URL", default="https://api.coingecko.com/api/v3/"
)
