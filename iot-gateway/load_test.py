"""
Load testing suite for National Water Infrastructure Monitoring System.
Uses Locust to simulate concurrent sensor connections and API requests.

Run with:
    locust -f load_test.py -u 1000 -r 50 -t 10m --headless

Parameters:
    -u: Number of users (concurrent sensors)
    -r: Ramp-up rate (users per second)
    -t: Test duration
    --headless: Run without web UI
"""

import json
import time
import random
from datetime import datetime
from locust import HttpUser, TaskSet, task, constant_throughput, between
from locust.contrib.fasthttp import FastHttpUser


class SensorReadingTaskSet(TaskSet):
    """Task set for sensor reading operations."""
    
    def on_start(self):
        """Initialize user data."""
        self.sensor_id = f"sensor_{self.user.user_id}"
        self.pipeline_id = f"pipeline_{random.randint(1, 5)}"
        self.municipality_id = f"municipality_{random.randint(1, 3)}"
        self.readings_sent = 0
        self.alerts_received = 0
        
    @task(40)
    def ingest_sensor_reading(self):
        """Simulate sensor data ingestion (40% of tasks)."""
        sensor_data = {
            "sensor_id": self.sensor_id,
            "value": random.uniform(20.0, 80.0),
            "unit": "m³/h",
            "sensor_type": random.choice(["flow", "pressure", "quality"]),
            "timestamp": datetime.utcnow().isoformat(),
            "location": {
                "lat": -26.2041 + random.uniform(-0.1, 0.1),
                "lon": 28.0473 + random.uniform(-0.1, 0.1)
            }
        }
        
        with self.client.post(
            "/api/v1/ingest/readings",
            json=sensor_data,
            headers={"Content-Type": "application/json"},
            catch_response=True,
            name="/api/v1/ingest/readings"
        ) as response:
            if response.status_code == 200:
                response.success()
                self.readings_sent += 1
            else:
                response.failure(f"Status: {response.status_code}")
    
    @task(20)
    def get_sensor_details(self):
        """Fetch sensor details (20% of tasks)."""
        with self.client.get(
            f"/api/v1/sensors/{self.sensor_id}",
            catch_response=True,
            name="/api/v1/sensors/{sensor_id}"
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")
    
    @task(15)
    def get_pipeline_sensors(self):
        """Fetch all sensors on a pipeline (15% of tasks)."""
        with self.client.get(
            f"/api/v1/geo/pipelines/{self.pipeline_id}/sensors",
            catch_response=True,
            name="/api/v1/geo/pipelines/{id}/sensors"
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")
    
    @task(15)
    def list_recent_alerts(self):
        """Fetch recent alerts for municipality (15% of tasks)."""
        with self.client.get(
            f"/api/v1/alerts?municipality_id={self.municipality_id}&limit=10",
            catch_response=True,
            name="/api/v1/alerts"
        ) as response:
            if response.status_code == 200:
                response.success()
                try:
                    alerts = response.json()
                    self.alerts_received += len(alerts) if isinstance(alerts, list) else 0
                except:
                    pass
            else:
                response.failure(f"Status: {response.status_code}")
    
    @task(10)
    def get_monitoring_health(self):
        """Health check endpoint (10% of tasks)."""
        with self.client.get(
            "/api/v1/monitoring/health",
            catch_response=True,
            name="/api/v1/monitoring/health"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")


class SensorUser(FastHttpUser):
    """Simulated sensor user for load testing."""
    
    tasks = [SensorReadingTaskSet]
    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_id = random.randint(1, 10000)


class AlertManagementTaskSet(TaskSet):
    """Task set for alert management operations."""
    
    def on_start(self):
        """Initialize alert management data."""
        self.municipality_id = f"municipality_{random.randint(1, 3)}"
        self.alert_id = f"alert_{random.randint(1, 1000)}"
    
    @task(50)
    def list_alerts(self):
        """List alerts (50% of tasks)."""
        params = {
            "municipality_id": self.municipality_id,
            "limit": random.randint(10, 50),
            "skip": random.randint(0, 100)
        }
        with self.client.get(
            "/api/v1/alerts",
            params=params,
            catch_response=True,
            name="/api/v1/alerts"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")
    
    @task(25)
    def get_alert_details(self):
        """Get specific alert (25% of tasks)."""
        with self.client.get(
            f"/api/v1/alerts/{self.alert_id}",
            catch_response=True,
            name="/api/v1/alerts/{id}"
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")
    
    @task(25)
    def get_alert_statistics(self):
        """Get alert statistics (25% of tasks)."""
        with self.client.get(
            f"/api/v1/monitoring/alerts/statistics?municipality_id={self.municipality_id}&days={random.randint(1, 7)}",
            catch_response=True,
            name="/api/v1/monitoring/alerts/statistics"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")


class AlertManagementUser(FastHttpUser):
    """Simulated alert management user."""
    
    tasks = [AlertManagementTaskSet]
    wait_time = between(2, 8)


class DashboardTaskSet(TaskSet):
    """Task set for dashboard operations."""
    
    @task(40)
    def get_dashboard_data(self):
        """Load dashboard (40% of tasks)."""
        endpoints = [
            "/api/v1/monitoring/system-status",
            "/api/v1/monitoring/metrics/summary",
            "/api/v1/sensors",
            "/api/v1/alerts?limit=20",
            "/api/v1/dashboard/overview"
        ]
        
        for endpoint in endpoints:
            with self.client.get(
                endpoint,
                catch_response=True,
                name=endpoint
            ) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Status: {response.status_code}")
    
    @task(30)
    def get_performance_metrics(self):
        """Get performance metrics (30% of tasks)."""
        hours = random.choice([1, 6, 24])
        with self.client.get(
            f"/api/v1/monitoring/performance?hours={hours}",
            catch_response=True,
            name="/api/v1/monitoring/performance"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")
    
    @task(20)
    def get_sensor_health(self):
        """Get sensor health (20% of tasks)."""
        with self.client.get(
            "/api/v1/monitoring/sensors/health",
            catch_response=True,
            name="/api/v1/monitoring/sensors/health"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")
    
    @task(10)
    def get_prometheus_metrics(self):
        """Fetch Prometheus metrics (10% of tasks)."""
        with self.client.get(
            "/api/v1/monitoring/metrics",
            catch_response=True,
            name="/api/v1/monitoring/metrics"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")


class DashboardUser(FastHttpUser):
    """Simulated dashboard user."""
    
    tasks = [DashboardTaskSet]
    wait_time = between(3, 10)


class GeoSpatialTaskSet(TaskSet):
    """Task set for geospatial operations."""
    
    def on_start(self):
        """Initialize geo data."""
        self.municipality_id = f"municipality_{random.randint(1, 3)}"
        self.pipeline_id = f"pipeline_{random.randint(1, 5)}"
    
    @task(35)
    def get_sensors_geojson(self):
        """Get sensor GeoJSON (35% of tasks)."""
        with self.client.get(
            f"/api/v1/geo/sensors/geojson?municipality_id={self.municipality_id}",
            catch_response=True,
            name="/api/v1/geo/sensors/geojson"
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")
    
    @task(25)
    def find_nearby_sensors(self):
        """Find nearby sensors (25% of tasks)."""
        with self.client.get(
            f"/api/v1/geo/nearby?lat={-26.2 + random.uniform(-0.1, 0.1)}&lon={28.0 + random.uniform(-0.1, 0.1)}&radius_km=5",
            catch_response=True,
            name="/api/v1/geo/nearby"
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")
    
    @task(20)
    def get_municipality_bounds(self):
        """Get municipality bounds (20% of tasks)."""
        with self.client.get(
            f"/api/v1/geo/municipalities/{self.municipality_id}/bounds",
            catch_response=True,
            name="/api/v1/geo/municipalities/{id}/bounds"
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")
    
    @task(15)
    def get_pipeline_length(self):
        """Get pipeline length (15% of tasks)."""
        with self.client.get(
            f"/api/v1/geo/pipelines/{self.pipeline_id}/length",
            catch_response=True,
            name="/api/v1/geo/pipelines/{id}/length"
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")
    
    @task(5)
    def get_sensor_clusters(self):
        """Get sensor clusters (5% of tasks)."""
        with self.client.get(
            f"/api/v1/geo/clusters?municipality_id={self.municipality_id}&grid_size_meters=1000",
            catch_response=True,
            name="/api/v1/geo/clusters"
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")


class GeoSpatialUser(FastHttpUser):
    """Simulated geospatial user."""
    
    tasks = [GeoSpatialTaskSet]
    wait_time = between(2, 6)


# Configuration for different load profiles
# Uncomment to use different profiles

# Light load (100 sensors + 50 dashboard users)
# class LightLoadProfile:
#     pass

# Medium load (500 sensors + 200 dashboard users)
# class MediumLoadProfile:
#     pass

# Heavy load (2000 sensors + 500 dashboard users)
# class HeavyLoadProfile:
#     pass

# Spike test (sudden 5000 users)
# class SpikeProfile:
#     pass


if __name__ == "__main__":
    print("""
    Load Testing Suite for National Water Infrastructure Monitoring System
    
    Example commands:
    
    1. Light load test (100 users, 10 per second):
       locust -f load_test.py -u 100 -r 10 -t 10m --headless
    
    2. Medium load test (500 users, 50 per second):
       locust -f load_test.py -u 500 -r 50 -t 20m --headless
    
    3. Heavy load test (2000 sensors):
       locust -f load_test.py -u 2000 -r 100 -t 30m --headless
    
    4. Spike test (rapid 5000 users):
       locust -f load_test.py -u 5000 -r 1000 -t 5m --headless
    
    5. With web UI on localhost:8089:
       locust -f load_test.py --host=http://your-api-url:8000
    
    6. With custom settings:
       locust -f load_test.py \\
         --users 500 \\
         --spawn-rate 50 \\
         --run-time 20m \\
         --host http://localhost:8000 \\
         --headless
    """)
