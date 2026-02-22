import requests
import time
import random
from datetime import datetime

# Configuration
API_URL = "http://localhost:8000/api/v1"
DEVICE_ID = "SENSOR_001"
API_KEY = "your-device-api-key-here"

def send_reading(value, unit="bar"):
    """Send sensor reading via HTTP"""
    url = f"{API_URL}/ingest/sensors/{DEVICE_ID}/data"
    
    payload = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "value": value,
        "unit": unit,
        "quality": random.uniform(0.95, 1.0),
        "battery_level": random.randint(70, 100),
        "signal_strength": random.randint(80, 100)
    }
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            print(f"✅ Reading sent: {value} {unit}")
            return True
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def main():
    print("🌊 HTTP Sensor Client")
    print(f"Device ID: {DEVICE_ID}")
    print(f"API URL: {API_URL}")
    print("=" * 50)
    
    while True:
        # Generate reading (pressure sensor example)
        value = random.uniform(2.5, 4.5)
        
        # Occasionally generate anomaly
        if random.random() < 0.1:
            value = random.uniform(5.5, 7.0)
            print("⚠️  Generating anomaly...")
        
        send_reading(value, "bar")
        time.sleep(10)  # Send every 10 seconds

if __name__ == "__main__":
    main()
