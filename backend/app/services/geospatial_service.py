import logging
import math
from typing import Optional

from geoalchemy2.shape import to_shape
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.pipeline import Pipeline
from app.models.sensor import Sensor
from app.models.user import User

logger = logging.getLogger(__name__)

EARTH_RADIUS_KM = 6371.0


def _haversine_km(lat1, lon1, lat2, lon2):
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return EARTH_RADIUS_KM * c


class GeospatialService:
    def find_nearby_sensors(
        self,
        db: Session,
        lat: float,
        lon: float,
        radius_km: float = 5,
        municipality_id: Optional[str] = None,
    ):
        deg_lat = radius_km / EARTH_RADIUS_KM * (180 / math.pi)
        deg_lon = radius_km / (EARTH_RADIUS_KM * max(math.cos(math.radians(lat)), 0.00001)) * (180 / math.pi)
        min_lat, max_lat = lat - deg_lat, lat + deg_lat
        min_lon, max_lon = lon - deg_lon, lon + deg_lon

        query = db.query(Sensor).filter(
            Sensor.location.isnot(None),
            func.ST_Y(Sensor.location).between(min_lat, max_lat),
            func.ST_X(Sensor.location).between(min_lon, max_lon),
        )
        if municipality_id:
            query = query.filter(Sensor.municipality_id == municipality_id)

        sensors = query.all()

        result = []
        for sensor in sensors:
            try:
                shape = to_shape(sensor.location)
                distance_km = _haversine_km(lat, lon, float(shape.y), float(shape.x))
                if distance_km <= radius_km:
                    result.append(
                        {
                            "sensor_id": sensor.id,
                            "name": sensor.name,
                            "distance_meters": round(distance_km * 1000, 2),
                            "lat": float(shape.y),
                            "lon": float(shape.x),
                        }
                    )
            except Exception as exc:
                logger.warning("Nearby sensor calc failed for sensor=%s: %s", sensor.id, exc)

        result.sort(key=lambda item: item["distance_meters"])
        return result

    def find_sensors_on_pipeline(
        self,
        db: Session,
        pipeline_id: str,
        buffer_meters: float = 100,
        user: Optional[User] = None,
    ):
        pipeline = db.query(Pipeline).filter(Pipeline.id == pipeline_id).first()
        if not pipeline or not pipeline.geometry:
            return []
        if user and not user.is_super_admin and pipeline.municipality_id != user.municipality_id:
            return []

        sensors = db.query(Sensor).filter(Sensor.location.isnot(None)).all()
        result = []

        try:
            pipeline_shape = to_shape(pipeline.geometry)
            buffer_deg = buffer_meters / 111000.0
            for sensor in sensors:
                if user and not user.is_super_admin and sensor.municipality_id != user.municipality_id:
                    continue
                try:
                    sensor_shape = to_shape(sensor.location)
                    dist = pipeline_shape.distance(sensor_shape)
                    if dist <= buffer_deg:
                        result.append(
                            {
                                "sensor_id": sensor.id,
                                "name": sensor.name,
                                "type": sensor.sensor_type.name if sensor.sensor_type else None,
                                "distance_approx_m": round(dist * 111000, 2),
                            }
                        )
                except Exception:
                    continue
        except Exception as exc:
            logger.error("Error finding pipeline sensors: %s", exc)

        return result

    def calculate_pipeline_length(self, db: Session, pipeline_id: str, user: Optional[User] = None):
        pipeline = db.query(Pipeline).filter(Pipeline.id == pipeline_id).first()
        if not pipeline or not pipeline.geometry:
            return 0
        if user and not user.is_super_admin and pipeline.municipality_id != user.municipality_id:
            return 0

        try:
            shape = to_shape(pipeline.geometry)
            coords = list(shape.coords)
            total_km = 0.0
            for idx in range(len(coords) - 1):
                lon1, lat1 = coords[idx]
                lon2, lat2 = coords[idx + 1]
                total_km += _haversine_km(lat1, lon1, lat2, lon2)
            return round(total_km, 3)
        except Exception as exc:
            logger.error("Error calculating pipeline length: %s", exc)
            return 0

    def get_municipality_bounds(self, db: Session, municipality_id: str):
        results = (
            db.query(
                func.min(func.ST_Y(Sensor.location)).label("min_lat"),
                func.max(func.ST_Y(Sensor.location)).label("max_lat"),
                func.min(func.ST_X(Sensor.location)).label("min_lon"),
                func.max(func.ST_X(Sensor.location)).label("max_lon"),
            )
            .filter(Sensor.municipality_id == municipality_id, Sensor.location.isnot(None))
            .first()
        )

        if results and results.min_lat is not None:
            return {
                "southwest": {"lat": float(results.min_lat), "lon": float(results.min_lon)},
                "northeast": {"lat": float(results.max_lat), "lon": float(results.max_lon)},
            }
        return None

    def cluster_sensors(self, db: Session, municipality_id: str = None, grid_size_meters: int = 1000):
        query = db.query(Sensor).filter(Sensor.location.isnot(None))
        if municipality_id:
            query = query.filter(Sensor.municipality_id == municipality_id)
        sensors = query.all()

        clusters = {}
        grid_deg = grid_size_meters / 111000.0

        for sensor in sensors:
            try:
                shape = to_shape(sensor.location)
                lat, lon = shape.y, shape.x
                cell_lat = round(lat / grid_deg) * grid_deg
                cell_lon = round(lon / grid_deg) * grid_deg
                key = (cell_lat, cell_lon)
                if key not in clusters:
                    clusters[key] = {"lats": [], "lons": [], "count": 0}
                clusters[key]["lats"].append(lat)
                clusters[key]["lons"].append(lon)
                clusters[key]["count"] += 1
            except Exception:
                continue

        return [
            {
                "center": {
                    "lat": sum(cluster["lats"]) / cluster["count"],
                    "lon": sum(cluster["lons"]) / cluster["count"],
                },
                "count": cluster["count"],
            }
            for cluster in clusters.values()
        ]

    def get_all_sensors_geojson(self, db: Session, municipality_id: str = None):
        query = db.query(Sensor).filter(Sensor.location.isnot(None))
        if municipality_id:
            query = query.filter(Sensor.municipality_id == municipality_id)

        sensors = query.all()
        features = []
        for sensor in sensors:
            try:
                shape = to_shape(sensor.location)
                features.append(
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [shape.x, shape.y]},
                        "properties": {
                            "id": sensor.id,
                            "name": sensor.name,
                            "device_id": sensor.device_id,
                            "status": sensor.status.value,
                            "sensor_type": sensor.sensor_type.name if sensor.sensor_type else None,
                            "battery_level": sensor.battery_level,
                            "last_reading_at": sensor.last_reading_at.isoformat() if sensor.last_reading_at else None,
                        },
                    }
                )
            except Exception:
                continue
        return {"type": "FeatureCollection", "features": features}


geospatial_service = GeospatialService()
