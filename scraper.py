import requests
import pandas as pd
import os
import json
from datetime import datetime
import time
from pytz import timezone

DATA_FILE = "egx_data.csv"

CANDIDATE_URLS = [
    "https://www.egx.com.eg/ar/GetIndicesData.aspx",
    "https://www.egx.com.eg/ar/IndicesData.aspx"
]

CAIRO_TZ = timezone('Africa/Cairo')

def get_cairo_time():
    return datetime.now(CAIRO_TZ)

def fetch_json(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0", "X-Requested-With": "XMLHttpRequest"}
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except:
        return None

def parse_data(raw):
    try:
        if isinstance(raw, dict) and 'd' in raw:
            payload = raw['d']
        else:
            payload = raw
        if isinstance(payload, str):
            payload = json.loads(payload)
        if isinstance(payload, list):
            records = []
            for item in payload:
                records.append({
                    "Symbol": item.get("Symbol", "EGX30"),
                    "Date": get_cairo_time().strftime("%Y-%m-%d"),
                    "Open": float(item.get("Open", 0) or 0),
                    "High": float(item.get("High", 0) or 0),
                    "Low": float(item.get("Low", 0) or 0),
                    "Close": float(item.get("Close", 0) or 0),
                    "Volume": int(item.get("Volume", 0) or 0)
                })
            return records
        return None
    except:
        return None

def save_data(data):
    if not data:
        print("⚠ لا توجد بيانات جديدة - الاحتفاظ بالقديم")
        return False
    df_new = pd.DataFrame(data)
    if os.path.exists(DATA_FILE):
        df_old = pd.read_csv(DATA_FILE)
        df_combined = pd.concat([df_old, df_new]).drop_duplicates(['Symbol', 'Date'], keep='last')
    else:
        df_combined = df_new
    df_combined.to_csv(DATA_FILE, index=False)
    print(f"✅ تم حفظ {len(df_new)} سجل جديد (بتوقيت القاهرة)")
    return True

def main():
    for url in CANDIDATE_URLS:
        print(f"🔄 محاولة: {url}")
        raw = fetch_json(url)
        if raw:
            data = parse_data(raw)
            if data and save_data(data):
                return
        time.sleep(1)
    print("❌ فشلت جميع المحاولات، تم الاحتفاظ بالبيانات القديمة")

if __name__ == "__main__":
    main()
