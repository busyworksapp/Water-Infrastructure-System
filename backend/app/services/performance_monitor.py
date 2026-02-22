"""Real-time performance monitoring and profiling."""
from typing import Dict, List
from datetime import datetime, timedelta
from collections import defaultdict, deque
import time
import threading

class PerformanceMonitor:
    """Monitor API and system performance metrics."""
    
    def __init__(self, max_samples: int = 1000):
        self.max_samples = max_samples
        self.metrics = defaultdict(lambda: deque(maxlen=max_samples))
        self.lock = threading.Lock()
    
    def record_request(self, endpoint: str, method: str, duration: float, status: int):
        """Record API request metrics."""
        with self.lock:
            self.metrics[f"{method}:{endpoint}"].append({
                "timestamp": datetime.utcnow(),
                "duration": duration,
                "status": status
            })
    
    def record_db_query(self, query_type: str, duration: float):
        """Record database query metrics."""
        with self.lock:
            self.metrics[f"db:{query_type}"].append({
                "timestamp": datetime.utcnow(),
                "duration": duration
            })
    
    def get_endpoint_stats(self, endpoint: str, method: str = "GET") -> Dict:
        """Get statistics for specific endpoint."""
        key = f"{method}:{endpoint}"
        with self.lock:
            data = list(self.metrics.get(key, []))
        
        if not data:
            return {"error": "No data available"}
        
        durations = [d["duration"] for d in data]
        return {
            "endpoint": endpoint,
            "method": method,
            "total_requests": len(durations),
            "avg_duration_ms": round(sum(durations) / len(durations) * 1000, 2),
            "min_duration_ms": round(min(durations) * 1000, 2),
            "max_duration_ms": round(max(durations) * 1000, 2),
            "p95_duration_ms": round(self._percentile(durations, 95) * 1000, 2),
            "p99_duration_ms": round(self._percentile(durations, 99) * 1000, 2)
        }
    
    def get_slow_endpoints(self, threshold_ms: float = 1000) -> List[Dict]:
        """Get endpoints with slow response times."""
        slow = []
        with self.lock:
            for key, data in self.metrics.items():
                if not key.startswith("db:"):
                    durations = [d["duration"] for d in data]
                    avg = sum(durations) / len(durations) if durations else 0
                    if avg * 1000 > threshold_ms:
                        method, endpoint = key.split(":", 1)
                        slow.append({
                            "endpoint": endpoint,
                            "method": method,
                            "avg_duration_ms": round(avg * 1000, 2)
                        })
        return sorted(slow, key=lambda x: x["avg_duration_ms"], reverse=True)
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile value."""
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]

performance_monitor = PerformanceMonitor()
