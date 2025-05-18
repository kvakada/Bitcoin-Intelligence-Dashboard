import requests
from datetime import datetime, timezone
from storage.s3_handler import upload_json_to_s3
from config import AWS_BUCKET, DATA_PREFIX, COINGECKO_API_URL, COINGECKO_API_PARAMS

def fetch_bitcoin():
    try:
        response = requests.get(COINGECKO_API_URL, params=COINGECKO_API_PARAMS, timeout=10)
        response.raise_for_status()
        result = response.json()

        price = result.get('bitcoin', {}).get('usd')
        if price is None:
            raise ValueError("Missing 'usd' field in API response.")

        timestamp = datetime.now(timezone.utc).isoformat()
        data = {
            "timestamp": timestamp,
            "bitcoin": {"usd": float(price)}
        }

        filename = f"{DATA_PREFIX}price_{timestamp}.json"
        full_path = f"{AWS_BUCKET}/{filename}"

        upload_json_to_s3(full_path, data)

    except Exception as e:
        print(f"❌ Ingestion failed: {e}")
