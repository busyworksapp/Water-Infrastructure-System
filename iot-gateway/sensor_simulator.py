import paho.mqtt.client as mqtt
import json
import time
import random
from datetime import datetime

# Configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_USERNAME = None
MQTT_PASSWORD = None

# Simulated sensors
SENSORS = [
    {"device_id": "PRESSURE_001", "type": "pressure", "unit": "bar", "normal_range": (2.5, 4.5)},
    {"device_id": "FLOW_001", "type": "flow", "unit": "m3/h", "normal_range": (50, 150)},
    {"device_id": "PRESSURE_002", "type": "pressure", "unit": "bar", "normal_range": (3.0, 5.0)},
    {"device_id": "LEAK_001", "type": "leak", "unit": "boolean", "normal_range": (0, 0)},
]

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT broker")
    else:
        print(f"❌ Connection failed with code {rc}")

def generate_reading(sensor, anomaly_chance=0.05):
    """Generate sensor reading with optional anomaly"""
    is_anomaly = random.random() < anomaly_chance
    
    if sensor["type"] == "leak":
        value = 1 if is_anomaly else 0
    else:
        min_val, max_val = sensor["normal_range"]
        if is_anomaly:
            # Generate anomalous value
            if random.random() > 0.5:
                value = max_val + random.uniform(0.5, 2.0)
            else:
                value = min_val - random.uniform(0.5, 2.0)
        else:
            value = random.uniform(min_val, max_val)
    
    return {
        "device_id": sensor["device_id"],
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "value": round(value, 2),
        "unit": sensor["unit"],
        "quality": random.uniform(0.95, 1.0),
        "battery_level": random.randint(70, 100),
        "signal_strength": random.randint(80, 100)
    }

def main():
    print("🌊 Water Monitoring IoT Sensor Simulator")
    print("=" * 50)
    
    # Create MQTT client
    client = mqtt.Client(client_id="sensor_simulator")
    client.on_connect = on_connect
    
    if MQTT_USERNAME and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        
        print(f"\n📡 Simulating {len(SENSORS)} sensors...")
        print("Press Ctrl+C to stop\n")
        
        iteration = 0
        while True:
            iteration += 1
            print(f"\n--- Iteration {iteration} ---")
            
            for sensor in SENSORS:
                # Generate reading
                reading = generate_reading(sensor, anomaly_chance=0.1)
                
                # Publish to MQTT
                topic = f"sensors/{sensor['device_id']}/data"
                payload = json.dumps(reading)
                
                result = client.publish(topic, payload)
                
                status = "⚠️ ANOMALY" if reading["value"] < sensor["normal_range"][0] or reading["value"] > sensor["normal_range"][1] else "✅ NORMAL"
                print(f"{sensor['device_id']}: {reading['value']} {reading['unit']} - {status}")
                
                # Send heartbeat
                heartbeat_topic = f"sensors/{sensor['device_id']}/heartbeat"
                heartbeat = {"device_id": sensor['device_id'], "timestamp": datetime.utcnow().isoformat() + "Z"}
                client.publish(heartbeat_topic, json.dumps(heartbeat))
            
            time.sleep(5)  # Send readings every 5 seconds
            
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping simulator...")
        client.loop_stop()
        client.disconnect()
        print("✅ Disconnected")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
