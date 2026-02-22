from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel
from geoalchemy2.shape import to_shape
from geoalchemy2.elements import WKTElement
from shapely.geometry import mapping, LineString
from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..models.pipeline import Pipeline, PipelineStatus, PipelineMaterial

router = APIRouter(prefix="/pipelines", tags=["Pipelines"])


def _get_geometry(geom):
    if not geom:
        return None
    try:
        return mapping(to_shape(geom))
    except Exception:
        return None


class CreatePipelineRequest(BaseModel):
    name: str
    code: Optional[str] = None
    municipality_id: str
    coordinates: List[List[float]]
    length_km: Optional[float] = None
    diameter_mm: Optional[float] = None
    material: Optional[str] = None
    max_pressure_bar: Optional[float] = None
    max_flow_rate: Optional[float] = None
    description: Optional[str] = None
    installation_date: Optional[str] = None


class UpdatePipelineRequest(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    diameter_mm: Optional[float] = None
    material: Optional[str] = None
    max_pressure_bar: Optional[float] = None
    max_flow_rate: Optional[float] = None
    description: Optional[str] = None
    extra_data: Optional[dict] = None


@router.get("/")
async def get_pipelines(
    municipality_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Pipeline)

    if not current_user.is_super_admin:
        query = query.filter(Pipeline.municipality_id == current_user.municipality_id)
    elif municipality_id:
        query = query.filter(Pipeline.municipality_id == municipality_id)

    pipelines = query.all()

    return [{
        "id": p.id,
        "name": p.name,
        "code": p.code,
        "municipality_id": p.municipality_id,
        "geometry": _get_geometry(p.geometry),
        "length_km": p.length_km,
        "diameter_mm": p.diameter_mm,
        "material": p.material.value if p.material else None,
        "status": p.status.value,
        "max_pressure_bar": p.max_pressure_bar,
        "installation_date": p.installation_date.isoformat() if p.installation_date else None
    } for p in pipelines]


@router.post("/")
async def create_pipeline(
    request: CreatePipelineRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_super_admin and request.municipality_id != current_user.municipality_id:
        raise HTTPException(status_code=403, detail="Access denied")

    if request.code:
        existing = db.query(Pipeline).filter(Pipeline.code == request.code).first()
        if existing:
            raise HTTPException(status_code=400, detail="Pipeline code already exists")

    line = LineString(request.coordinates)
    wkt = line.wkt
    geom = WKTElement(wkt, srid=4326)

    pipeline = Pipeline(
        name=request.name,
        code=request.code,
        municipality_id=request.municipality_id,
        geometry=geom,
        length_km=request.length_km,
        diameter_mm=request.diameter_mm,
        material=PipelineMaterial(request.material.lower()) if request.material else None,
        max_pressure_bar=request.max_pressure_bar,
        max_flow_rate=request.max_flow_rate,
        description=request.description,
        status=PipelineStatus.OPERATIONAL,
        installation_date=datetime.fromisoformat(request.installation_date) if request.installation_date else None
    )

    db.add(pipeline)
    db.commit()
    db.refresh(pipeline)

    return {"id": pipeline.id, "name": pipeline.name, "status": pipeline.status.value}


@router.get("/{pipeline_id}")
async def get_pipeline(
    pipeline_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    pipeline = db.query(Pipeline).filter(Pipeline.id == pipeline_id).first()

    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    if not current_user.is_super_admin and pipeline.municipality_id != current_user.municipality_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return {
        "id": pipeline.id,
        "name": pipeline.name,
        "code": pipeline.code,
        "municipality_id": pipeline.municipality_id,
        "geometry": _get_geometry(pipeline.geometry),
        "length_km": pipeline.length_km,
        "diameter_mm": pipeline.diameter_mm,
        "material": pipeline.material.value if pipeline.material else None,
        "status": pipeline.status.value,
        "max_pressure_bar": pipeline.max_pressure_bar,
        "max_flow_rate": pipeline.max_flow_rate,
        "installation_date": pipeline.installation_date.isoformat() if pipeline.installation_date else None,
        "description": pipeline.description,
        "extra_data": pipeline.extra_data
    }


@router.put("/{pipeline_id}")
async def update_pipeline(
    pipeline_id: str,
    request: UpdatePipelineRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    pipeline = db.query(Pipeline).filter(Pipeline.id == pipeline_id).first()

    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    if not current_user.is_super_admin and pipeline.municipality_id != current_user.municipality_id:
        raise HTTPException(status_code=403, detail="Access denied")

    update_data = request.dict(exclude_unset=True)

    if "status" in update_data:
        update_data["status"] = PipelineStatus(update_data["status"].lower())

    if "material" in update_data and update_data["material"]:
        update_data["material"] = PipelineMaterial(update_data["material"].lower())

    for field, value in update_data.items():
        setattr(pipeline, field, value)

    pipeline.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "Pipeline updated", "id": pipeline.id}


@router.delete("/{pipeline_id}")
async def delete_pipeline(
    pipeline_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    pipeline = db.query(Pipeline).filter(Pipeline.id == pipeline_id).first()

    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    if not current_user.is_super_admin:
        raise HTTPException(status_code=403, detail="Super admin access required")

    db.delete(pipeline)
    db.commit()

    return {"message": "Pipeline deleted"}


@router.get("/{pipeline_id}/sensors")
async def get_pipeline_sensors(
    pipeline_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    pipeline = db.query(Pipeline).filter(Pipeline.id == pipeline_id).first()

    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    if not current_user.is_super_admin and pipeline.municipality_id != current_user.municipality_id:
        raise HTTPException(status_code=403, detail="Access denied")

    from geoalchemy2.shape import to_shape

    return [{
        "id": s.id,
        "device_id": s.device_id,
        "name": s.name,
        "status": s.status.value,
        "sensor_type": s.sensor_type.name if s.sensor_type else None,
        "location": {
            "type": "Point",
            "coordinates": _get_geometry(s.location)["coordinates"] if s.location else None
        }
    } for s in pipeline.sensors]


@router.get("/geojson/all")
async def get_pipelines_geojson(
    municipality_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Pipeline)

    if not current_user.is_super_admin:
        query = query.filter(Pipeline.municipality_id == current_user.municipality_id)
    elif municipality_id:
        query = query.filter(Pipeline.municipality_id == municipality_id)

    pipelines = query.all()

    features = []
    for p in pipelines:
        geom = _get_geometry(p.geometry)
        if geom:
            features.append({
                "type": "Feature",
                "geometry": geom,
                "properties": {
                    "id": p.id,
                    "name": p.name,
                    "status": p.status.value,
                    "material": p.material.value if p.material else None,
                    "diameter_mm": p.diameter_mm,
                    "length_km": p.length_km
                }
            })

    return {
        "type": "FeatureCollection",
        "features": features
    }

