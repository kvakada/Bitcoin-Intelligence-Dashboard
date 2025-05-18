import pandas as pd
from storage.s3_handler import list_data_files, load_json
from config import AWS_BUCKET, DATA_PREFIX

def load_all_btc_data():
    files = list_data_files(f"{AWS_BUCKET}/{DATA_PREFIX}")
    records = []

    for f in files:
        try:
            data = load_json(f)
            records.append({
                'timestamp': pd.to_datetime(data['timestamp'], utc=True),
                'price': float(data['bitcoin']['usd'])
            })
        except Exception:
            continue

    if not records:
        raise ValueError("No valid price records loaded from S3.")

    df = pd.DataFrame(records).sort_values('timestamp')
    df = df[~df['timestamp'].duplicated(keep='last')]
    df.set_index('timestamp', inplace=True)
    df = df.resample('H').mean().interpolate()
    df = df[df['price'].notnull()]
    return df
