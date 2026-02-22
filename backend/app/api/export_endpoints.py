"""
Advanced Data Export API Endpoints
Supports exporting sensor data, reports, and audit logs in multiple formats
"""

from datetime import datetime, timedelta
from typing import Optional
from enum import Enum

from fastapi import APIRouter, Depends, Query, Response, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.report_service import (
    AdvancedReportService,
    ReportFormat,
    ReportType
)
from app.services.audit_service import audit_service

router = APIRouter(prefix="/api/v1/export", tags=["Export"])


class ExportFormat(str, Enum):
    """Export format options"""
    CSV = "csv"
    JSON = "json"
    EXCEL = "excel"
    PDF = "pdf"


@router.get("/sensors/{sensor_id}/data")
async def export_sensor_data(
    sensor_id: int,
    format: ExportFormat = Query(ExportFormat.CSV),
    days: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export sensor data in multiple formats
    
    - **sensor_id**: Sensor ID to export
    - **format**: Export format (csv, json, excel, pdf)
    - **days**: Number of days of historical data
    """
    
    try:
        # Check permissions
        # In production, verify user has access to this sensor
        
        # Generate report
        report_format = ReportFormat(format.value)
        report_data = AdvancedReportService.create_sensor_data_report(
            db=db,
            sensor_id=sensor_id,
            days=days,
            format=report_format
        )

        # Determine content type and filename
        content_type_map = {
            ExportFormat.CSV: "text/csv",
            ExportFormat.JSON: "application/json",
            ExportFormat.EXCEL: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ExportFormat.PDF: "application/pdf",
        }

        filename_map = {
            ExportFormat.CSV: f"sensor_{sensor_id}_{datetime.utcnow().strftime('%Y%m%d')}.csv",
            ExportFormat.JSON: f"sensor_{sensor_id}_{datetime.utcnow().strftime('%Y%m%d')}.json",
            ExportFormat.EXCEL: f"sensor_{sensor_id}_{datetime.utcnow().strftime('%Y%m%d')}.xlsx",
            ExportFormat.PDF: f"sensor_{sensor_id}_{datetime.utcnow().strftime('%Y%m%d')}.pdf",
        }

        # Log the export action
        await audit_service.log(
            user_id=current_user.id,
            action="export_sensor_data",
            resource_type="sensor",
            resource_id=str(sensor_id),
            changes={"format": format.value, "days": days},
            ip_address="",  # Would be extracted from request
            user_agent=""  # Would be extracted from request
        )

        return Response(
            content=report_data,
            media_type=content_type_map[format],
            headers={
                "Content-Disposition": f"attachment; filename={filename_map[format]}"
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Export generation failed")


@router.get("/alerts/report")
async def export_alerts_report(
    format: ExportFormat = Query(ExportFormat.CSV),
    municipality_id: Optional[int] = None,
    days: int = Query(30, ge=1, le=365),
    severity: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export alerts report in multiple formats
    
    - **format**: Export format (csv, json, excel, pdf)
    - **municipality_id**: Filter by municipality (optional)
    - **days**: Number of days of historical data
    - **severity**: Filter by severity (critical, high, medium, low)
    """
    
    try:
        # Check permissions
        if not current_user.is_super_admin and municipality_id is None:
            municipality_id = current_user.municipality_id

        # Generate report
        report_format = ReportFormat(format.value)
        report_data = AdvancedReportService.create_alert_summary_report(
            db=db,
            municipality_id=municipality_id,
            days=days,
            format=report_format
        )

        content_type_map = {
            ExportFormat.CSV: "text/csv",
            ExportFormat.JSON: "application/json",
            ExportFormat.EXCEL: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ExportFormat.PDF: "application/pdf",
        }

        filename = f"alerts_report_{datetime.utcnow().strftime('%Y%m%d')}.{format.value}"

        # Log the export action
        await audit_service.log(
            user_id=current_user.id,
            action="export_alerts",
            resource_type="alert",
            resource_id="batch",
            changes={
                "format": format.value,
                "municipality_id": municipality_id,
                "days": days,
                "severity": severity
            },
            ip_address="",
            user_agent=""
        )

        return Response(
            content=report_data,
            media_type=content_type_map[format],
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Report generation failed")


@router.get("/water-usage/report")
async def export_water_usage_report(
    format: ExportFormat = Query(ExportFormat.CSV),
    municipality_id: Optional[int] = None,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export water usage report in multiple formats
    
    - **format**: Export format (csv, json, excel, pdf)
    - **municipality_id**: Municipality to export (required for non-admin)
    - **days**: Number of days of historical data
    """
    
    try:
        # Check permissions
        if not current_user.is_super_admin:
            if municipality_id is None:
                municipality_id = current_user.municipality_id
            elif municipality_id != current_user.municipality_id:
                raise HTTPException(status_code=403, detail="Unauthorized")
        
        if municipality_id is None:
            raise HTTPException(status_code=400, detail="municipality_id is required")

        # Generate report
        report_format = ReportFormat(format.value)
        report_data = AdvancedReportService.create_water_usage_report(
            db=db,
            municipality_id=municipality_id,
            days=days,
            format=report_format
        )

        content_type_map = {
            ExportFormat.CSV: "text/csv",
            ExportFormat.JSON: "application/json",
            ExportFormat.EXCEL: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ExportFormat.PDF: "application/pdf",
        }

        filename = f"water_usage_{municipality_id}_{datetime.utcnow().strftime('%Y%m%d')}.{format.value}"

        # Log the export action
        await audit_service.log(
            user_id=current_user.id,
            action="export_water_usage",
            resource_type="municipality",
            resource_id=str(municipality_id),
            changes={"format": format.value, "days": days},
            ip_address="",
            user_agent=""
        )

        return Response(
            content=report_data,
            media_type=content_type_map[format],
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Report generation failed")


@router.get("/system-health/report")
async def export_system_health_report(
    format: ExportFormat = Query(ExportFormat.CSV),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export system health report in multiple formats
    
    - **format**: Export format (csv, json, excel, pdf)
    
    Requires admin access
    """
    
    if not current_user.is_super_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        # Generate report
        report_format = ReportFormat(format.value)
        report_data = AdvancedReportService.create_system_health_report(
            db=db,
            format=report_format
        )

        content_type_map = {
            ExportFormat.CSV: "text/csv",
            ExportFormat.JSON: "application/json",
            ExportFormat.EXCEL: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ExportFormat.PDF: "application/pdf",
        }

        filename = f"system_health_{datetime.utcnow().strftime('%Y%m%d')}.{format.value}"

        # Log the export action
        await audit_service.log(
            user_id=current_user.id,
            action="export_system_health",
            resource_type="system",
            resource_id="global",
            changes={"format": format.value},
            ip_address="",
            user_agent=""
        )

        return Response(
            content=report_data,
            media_type=content_type_map[format],
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Report generation failed")


@router.get("/audit-log/export")
async def export_audit_logs(
    format: ExportFormat = Query(ExportFormat.CSV),
    days: int = Query(30, ge=1, le=365),
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export audit logs in multiple formats
    
    - **format**: Export format (csv, json, excel, pdf)
    - **days**: Number of days of historical data
    - **action**: Filter by action type
    - **resource_type**: Filter by resource type
    - **user_id**: Filter by user ID
    
    Requires admin access
    """
    
    if not current_user.is_super_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        # In production, would query actual audit logs from database
        # For now, returning a simple export structure
        
        if format == ExportFormat.CSV:
            csv_data = "timestamp,user_id,action,resource_type,resource_id,status\n"
            # Add actual audit log data
            response_content = csv_data.encode('utf-8')
            media_type = "text/csv"
        elif format == ExportFormat.JSON:
            json_data = '{"audit_logs": []}'
            response_content = json_data.encode('utf-8')
            media_type = "application/json"
        else:
            # Would use report service for Excel/PDF
            response_content = b""
            media_type = "application/octet-stream"

        # Log the export action
        await audit_service.log(
            user_id=current_user.id,
            action="export_audit_logs",
            resource_type="audit_log",
            resource_id="batch",
            changes={
                "format": format.value,
                "days": days,
                "action": action,
                "resource_type": resource_type
            },
            ip_address="",
            user_agent=""
        )

        filename = f"audit_logs_{datetime.utcnow().strftime('%Y%m%d')}.{format.value}"

        return Response(
            content=response_content,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail="Export generation failed")


@router.get("/bulk-export")
async def bulk_export(
    format: ExportFormat = Query(ExportFormat.JSON),
    include_sensors: bool = Query(True),
    include_alerts: bool = Query(True),
    include_incidents: bool = Query(False),
    days: int = Query(7, ge=1, le=365),
    municipality_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export multiple data types in a single request
    
    - **format**: Export format (json, excel)
    - **include_sensors**: Include sensor data
    - **include_alerts**: Include alert data
    - **include_incidents**: Include incident data
    - **days**: Historical data range
    - **municipality_id**: Filter by municipality
    """
    
    try:
        # Check permissions
        if not current_user.is_super_admin and municipality_id is None:
            municipality_id = current_user.municipality_id

        # Create bulk export (in production, would compile data from database)
        export_data = {
            "export_timestamp": datetime.utcnow().isoformat(),
            "format": format.value,
            "municipality_id": municipality_id,
            "period_days": days,
            "includes": {
                "sensors": include_sensors,
                "alerts": include_alerts,
                "incidents": include_incidents
            },
            "data": {}
        }

        if format == ExportFormat.JSON:
            response_content = str(export_data).encode('utf-8')
            media_type = "application/json"
        else:
            response_content = b""
            media_type = "application/octet-stream"

        # Log the export action
        await audit_service.log(
            user_id=current_user.id,
            action="bulk_export",
            resource_type="system",
            resource_id="bulk",
            changes={
                "format": format.value,
                "includes": export_data["includes"]
            },
            ip_address="",
            user_agent=""
        )

        filename = f"bulk_export_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.{format.value}"

        return Response(
            content=response_content,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail="Bulk export failed")
