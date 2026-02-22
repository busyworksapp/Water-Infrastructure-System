#!/usr/bin/env python3
"""Multi-protocol sensor simulator for testing IoT ingestion."""
import asyncio
import json
import random
import time
from datetime import datetime
import paho.mqtt.client as mqtt
import requests
import socket
import argparse


class SensorSimulator:
    def __init__(self, api_url="http://localhost:8000", mqtt_broker="localhost", mqtt_port=1883):
        self.api_url = api_url
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        self.sensors = []
        self.running = False
    
    def generate_sensor_data(self, sensor_id, sensor_type="pressure"):
        """Generate realistic sensor data with occasional anomalies."""
        base_values = {
            "pressure": (2.5, 4.5, 0.3),
            "flow": (50, 150, 10),
            "temperature": (15, 25, 2),
            "level": (1.0, 5.0, 0.5)
        }
        
        base, max_val, std = base_values.get(sensor_type, (3.0, 5.0, 0.5))
        
        # 5% chance of anomaly
        if random.random() < 0.05:
            value = random.uniform(max_val * 1.5, max_val * 2.0)
        else:
            value = random.gauss(base, std)
            value = max(0, min(value, max_val))
        
        return {
            "sensor_id": sensor_id,
            "value": round(value, 2),
            "unit": {"pressure": "bar", "flow": "m3/h", "temperature": "°C", "level": "m"}[sensor_type],
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "quality_score": round(random.uniform(0.85, 1.0), 2),
            "battery_level": random.randint(70, 100),
            "signal_strength": random.randint(60, 100)
        }
    
    def simulate_mqtt(self, sensor_id, sensor_type="pressure", count=10, interval=2):
        """Simulate MQTT sensor."""
        print(f"🔵 Starting MQTT simulation for {sensor_id}")
        
        client = mqtt.Client()
        
        try:
            client.connect(self.mqtt_broker, self.mqtt_port, 60)
            client.loop_start()
            
            for i in range(count):
                data = self.generate_sensor_data(sensor_id, sensor_type)
                topic = f"sensors/{sensor_id}/data"
                
                payload = json.dumps(data)
                client.publish(topic, payload)
                
                print(f"  📤 MQTT: {sensor_id} = {data['value']} {data['unit']}")
                time.sleep(interval)
            
            client.loop_stop()
            client.disconnect()
            print(f"✅ MQTT simulation complete for {sensor_id}")
            
        except Exception as e:
            print(f"❌ MQTT error: {e}")
    
    def simulate_http(self, sensor_id, sensor_type="pressure", count=10, interval=2, api_key=None):
        """Simulate HTTP/HTTPS sensor."""
        print(f"🟢 Starting HTTP simulation for {sensor_id}")
        
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["X-API-Key"] = api_key
        
        for i in range(count):
            data = self.generate_sensor_data(sensor_id, sensor_type)
            
            try:
                response = requests.post(
                    f"{self.api_url}/api/v1/sensors/{sensor_id}/readings",
                    json=data,
                    headers=headers,
                    timeout=5
                )
                
                if response.status_code in [200, 201]:
                    print(f"  📤 HTTP: {sensor_id} = {data['value']} {data['unit']} ✅")
                else:
                    print(f"  ❌ HTTP: {sensor_id} failed ({response.status_code})")
                    
            except Exception as e:
                print(f"  ❌ HTTP error: {e}")
            
            time.sleep(interval)
        
        print(f"✅ HTTP simulation complete for {sensor_id}")
    
    def simulate_tcp(self, sensor_id, sensor_type="pressure", count=10, interval=2, host="localhost", port=9999):
        """Simulate TCP sensor."""
        print(f"🟣 Starting TCP simulation for {sensor_id}")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, port))
            
            for i in range(count):
                data = self.generate_sensor_data(sensor_id, sensor_type)
                message = json.dumps(data) + "\n"
                
                sock.sendall(message.encode())
                print(f"  📤 TCP: {sensor_id} = {data['value']} {data['unit']}")
                
                time.sleep(interval)
            
            sock.close()
            print(f"✅ TCP simulation complete for {sensor_id}")
            
        except Exception as e:
            print(f"❌ TCP error: {e}")
    
    def simulate_lorawan(self, device_eui, count=10, interval=5):
        """Simulate LoRaWAN sensor."""
        print(f"🟡 Starting LoRaWAN simulation for {device_eui}")
        
        for i in range(count):
            # Simulate Cayenne LPP payload
            value = random.uniform(2.0, 5.0)
            
            payload = {
                "device_eui": device_eui,
                "payload": self._encode_cayenne_lpp(value),
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "rssi": random.randint(-120, -60),
                    "snr": random.uniform(-20, 10),
                    "frequency": 868.1
                }
            }
            
            try:
                response = requests.post(
                    f"{self.api_url}/api/v1/iot/lorawan/uplink",
                    json=payload,
                    timeout=5
                )
                
                if response.status_code == 200:
                    print(f"  📤 LoRaWAN: {device_eui} = {value:.2f} bar ✅")
                else:
                    print(f"  ❌ LoRaWAN: {device_eui} failed")
                    
            except Exception as e:
                print(f"  ❌ LoRaWAN error: {e}")
            
            time.sleep(interval)
        
        print(f"✅ LoRaWAN simulation complete for {device_eui}")
    
    def simulate_nbiot(self, imei, count=10, interval=5):
        """Simulate NB-IoT sensor."""
        print(f"🔵 Starting NB-IoT simulation for {imei}")
        
        for i in range(count):
            data = {
                "imei": imei,
                "value": round(random.uniform(2.0, 5.0), 2),
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "signal_strength": random.randint(0, 100),
                "battery_level": random.randint(70, 100)
            }
            
            try:
                response = requests.post(
                    f"{self.api_url}/api/v1/iot/nbiot/message",
                    json=data,
                    timeout=5
                )
                
                if response.status_code == 200:
                    print(f"  📤 NB-IoT: {imei} = {data['value']} bar ✅")
                else:
                    print(f"  ❌ NB-IoT: {imei} failed")
                    
            except Exception as e:
                print(f"  ❌ NB-IoT error: {e}")
            
            time.sleep(interval)
        
        print(f"✅ NB-IoT simulation complete for {imei}")
    
    def simulate_gsm(self, phone_number, sensor_id, count=10, interval=10):
        """Simulate GSM/SMS sensor."""
        print(f"📱 Starting GSM simulation for {phone_number}")
        
        for i in range(count):
            value = round(random.uniform(2.0, 5.0), 2)
            sms_message = f"{sensor_id}:{value}:bar"
            
            data = {
                "phone_number": phone_number,
                "message": sms_message,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
            try:
                response = requests.post(
                    f"{self.api_url}/api/v1/iot/gsm/sms",
                    json=data,
                    timeout=5
                )
                
                if response.status_code == 200:
                    print(f"  📤 GSM: {phone_number} = {value} bar ✅")
                else:
                    print(f"  ❌ GSM: {phone_number} failed")
                    
            except Exception as e:
                print(f"  ❌ GSM error: {e}")
            
            time.sleep(interval)
        
        print(f"✅ GSM simulation complete for {phone_number}")
    
    def _encode_cayenne_lpp(self, value):
        """Encode value as Cayenne LPP hex string."""
        channel = 1
        data_type = 0x02  # Analog input
        value_int = int(value * 100)
        
        payload = f"{channel:02x}{data_type:02x}{value_int:04x}"
        return payload
    
    def run_mixed_simulation(self, duration=60):
        """Run mixed protocol simulation."""
        print("=" * 60)
        print("🌊 Multi-Protocol Sensor Simulation")
        print("=" * 60)
        
        sensors = [
            ("SENSOR_001", "mqtt", "pressure"),
            ("SENSOR_002", "http", "flow"),
            ("SENSOR_003", "tcp", "pressure"),
            ("LORAWAN_001", "lorawan", None),
            ("NBIOT_001", "nbiot", None),
            ("+27123456789", "gsm", "pressure"),
        ]
        
        import threading
        threads = []
        
        for sensor_id, protocol, sensor_type in sensors:
            if protocol == "mqtt":
                t = threading.Thread(target=self.simulate_mqtt, args=(sensor_id, sensor_type, duration//2, 2))
            elif protocol == "http":
                t = threading.Thread(target=self.simulate_http, args=(sensor_id, sensor_type, duration//2, 2))
            elif protocol == "tcp":
                t = threading.Thread(target=self.simulate_tcp, args=(sensor_id, sensor_type, duration//2, 2))
            elif protocol == "lorawan":
                t = threading.Thread(target=self.simulate_lorawan, args=(sensor_id, duration//5, 5))
            elif protocol == "nbiot":
                t = threading.Thread(target=self.simulate_nbiot, args=(sensor_id, duration//5, 5))
            elif protocol == "gsm":
                t = threading.Thread(target=self.simulate_gsm, args=(sensor_id, "SENSOR_GSM_001", duration//10, 10))
            
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        print("\n" + "=" * 60)
        print("✅ Simulation Complete")
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="IoT Sensor Simulator")
    parser.add_argument("--api-url", default="http://localhost:8000", help="API URL")
    parser.add_argument("--mqtt-broker", default="localhost", help="MQTT broker host")
    parser.add_argument("--mqtt-port", type=int, default=1883, help="MQTT broker port")
    parser.add_argument("--protocol", choices=["mqtt", "http", "tcp", "lorawan", "nbiot", "gsm", "mixed"], default="mixed")
    parser.add_argument("--sensor-id", default="SENSOR_TEST_001", help="Sensor ID")
    parser.add_argument("--count", type=int, default=10, help="Number of readings")
    parser.add_argument("--interval", type=int, default=2, help="Interval between readings (seconds)")
    parser.add_argument("--duration", type=int, default=60, help="Duration for mixed simulation (seconds)")
    
    args = parser.parse_args()
    
    simulator = SensorSimulator(args.api_url, args.mqtt_broker, args.mqtt_port)
    
    if args.protocol == "mixed":
        simulator.run_mixed_simulation(args.duration)
    elif args.protocol == "mqtt":
        simulator.simulate_mqtt(args.sensor_id, "pressure", args.count, args.interval)
    elif args.protocol == "http":
        simulator.simulate_http(args.sensor_id, "pressure", args.count, args.interval)
    elif args.protocol == "tcp":
        simulator.simulate_tcp(args.sensor_id, "pressure", args.count, args.interval)
    elif args.protocol == "lorawan":
        simulator.simulate_lorawan(args.sensor_id, args.count, args.interval)
    elif args.protocol == "nbiot":
        simulator.simulate_nbiot(args.sensor_id, args.count, args.interval)
    elif args.protocol == "gsm":
        simulator.simulate_gsm("+27123456789", args.sensor_id, args.count, args.interval)


if __name__ == "__main__":
    main()
