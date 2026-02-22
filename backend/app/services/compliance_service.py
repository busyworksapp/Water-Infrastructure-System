"""
Compliance Reporting Service
Tracks compliance with water quality standards and environmental regulations
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

logger = logging.getLogger(__name__)


class ComplianceStandard(str, Enum):
    """Water quality compliance standards"""
    WHO = "WHO"  # World Health Organization
    EPA = "EPA"  # US Environmental Protection Agency
    EU = "EU_DIRECTIVE_98_83_EC"  # EU Water Quality Directive
    LOCAL = "LOCAL"  # Local/regional standards


class ComplianceMetric(str, Enum):
    """Key compliance metrics"""
    PH_LEVEL = "ph_level"
    TURBIDITY = "turbidity"
    CHLORINE = "residual_chlorine"
    BACTERIA = "bacteria_count"
    NITRATE = "nitrate_level"
    ARSENIC = "arsenic_level"
    LEAD = "lead_level"
    TEMPERATURE = "temperature"
    HARDNESS = "hardness"
    ALKALINITY = "alkalinity"
    DISSOLVED_OXYGEN = "dissolved_oxygen"
    CONDUCTIVITY = "conductivity"


@dataclass
class ComplianceThreshold:
    """Compliance threshold for a metric"""
    metric: ComplianceMetric
    standard: ComplianceStandard
    min_value: float
    max_value: float
    unit: str
    description: str


class ComplianceStatus(str, Enum):
    """Compliance status"""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    WARNING = "warning"
    UNKNOWN = "unknown"


@dataclass
class ComplianceResult:
    """Result of compliance check"""
    metric: ComplianceMetric
    standard: ComplianceStandard
    timestamp: datetime
    value: float
    threshold_min: float
    threshold_max: float
    status: ComplianceStatus
    notes: Optional[str] = None


class ComplianceService:
    """Service for compliance monitoring and reporting"""

    # Compliance thresholds for different standards
    # WHO Guidelines for Drinking Water Quality (4th edition)
    WHO_THRESHOLDS = {
        ComplianceMetric.PH_LEVEL: ComplianceThreshold(
            metric=ComplianceMetric.PH_LEVEL,
            standard=ComplianceStandard.WHO,
            min_value=6.5,
            max_value=8.5,
            unit="pH",
            description="pH should be between 6.5 and 8.5 for optimal water quality"
        ),
        ComplianceMetric.TURBIDITY: ComplianceThreshold(
            metric=ComplianceMetric.TURBIDITY,
            standard=ComplianceStandard.WHO,
            min_value=0,
            max_value=5.0,
            unit="NTU",
            description="Turbidity should not exceed 5 NTU"
        ),
        ComplianceMetric.CHLORINE: ComplianceThreshold(
            metric=ComplianceMetric.CHLORINE,
            standard=ComplianceStandard.WHO,
            min_value=0.2,
            max_value=5.0,
            unit="mg/L",
            description="Residual chlorine should be between 0.2 and 5.0 mg/L"
        ),
        ComplianceMetric.BACTERIA: ComplianceThreshold(
            metric=ComplianceMetric.BACTERIA,
            standard=ComplianceStandard.WHO,
            min_value=0,
            max_value=0,
            unit="CFU/100mL",
            description="No bacteria should be detected"
        ),
        ComplianceMetric.NITRATE: ComplianceThreshold(
            metric=ComplianceMetric.NITRATE,
            standard=ComplianceStandard.WHO,
            min_value=0,
            max_value=50,
            unit="mg/L",
            description="Nitrate should not exceed 50 mg/L"
        ),
        ComplianceMetric.ARSENIC: ComplianceThreshold(
            metric=ComplianceMetric.ARSENIC,
            standard=ComplianceStandard.WHO,
            min_value=0,
            max_value=0.01,
            unit="mg/L",
            description="Arsenic should not exceed 0.01 mg/L"
        ),
        ComplianceMetric.LEAD: ComplianceThreshold(
            metric=ComplianceMetric.LEAD,
            standard=ComplianceStandard.WHO,
            min_value=0,
            max_value=0.015,
            unit="mg/L",
            description="Lead should not exceed 0.015 mg/L"
        ),
        ComplianceMetric.TEMPERATURE: ComplianceThreshold(
            metric=ComplianceMetric.TEMPERATURE,
            standard=ComplianceStandard.WHO,
            min_value=0,
            max_value=25,
            unit="°C",
            description="Water temperature should not exceed 25°C"
        ),
    }

    # EPA Drinking Water Standards
    EPA_THRESHOLDS = {
        ComplianceMetric.PH_LEVEL: ComplianceThreshold(
            metric=ComplianceMetric.PH_LEVEL,
            standard=ComplianceStandard.EPA,
            min_value=6.5,
            max_value=8.5,
            unit="pH",
            description="EPA standard for pH"
        ),
        ComplianceMetric.TURBIDITY: ComplianceThreshold(
            metric=ComplianceMetric.TURBIDITY,
            standard=ComplianceStandard.EPA,
            min_value=0,
            max_value=1.0,
            unit="NTU",
            description="EPA standard: maximum 1.0 NTU"
        ),
        ComplianceMetric.BACTERIA: ComplianceThreshold(
            metric=ComplianceMetric.BACTERIA,
            standard=ComplianceStandard.EPA,
            min_value=0,
            max_value=0,
            unit="CFU/100mL",
            description="EPA standard: must be absent"
        ),
        ComplianceMetric.LEAD: ComplianceThreshold(
            metric=ComplianceMetric.LEAD,
            standard=ComplianceStandard.EPA,
            min_value=0,
            max_value=0.015,
            unit="mg/L",
            description="EPA standard: action level 0.015 mg/L"
        ),
    }

    # EU Directive 98/83/EC thresholds
    EU_THRESHOLDS = {
        ComplianceMetric.PH_LEVEL: ComplianceThreshold(
            metric=ComplianceMetric.PH_LEVEL,
            standard=ComplianceStandard.EU,
            min_value=6.5,
            max_value=9.5,
            unit="pH",
            description="EU standard for pH"
        ),
        ComplianceMetric.TURBIDITY: ComplianceThreshold(
            metric=ComplianceMetric.TURBIDITY,
            standard=ComplianceStandard.EU,
            min_value=0,
            max_value=4.0,
            unit="NTU",
            description="EU standard: maximum 4.0 NTU"
        ),
        ComplianceMetric.BACTERIA: ComplianceThreshold(
            metric=ComplianceMetric.BACTERIA,
            standard=ComplianceStandard.EU,
            min_value=0,
            max_value=0,
            unit="CFU/100mL",
            description="EU standard: must be absent"
        ),
        ComplianceMetric.NITRATE: ComplianceThreshold(
            metric=ComplianceMetric.NITRATE,
            standard=ComplianceStandard.EU,
            min_value=0,
            max_value=50,
            unit="mg/L",
            description="EU standard for nitrate"
        ),
    }

    @classmethod
    def get_threshold(
        cls,
        metric: ComplianceMetric,
        standard: ComplianceStandard
    ) -> Optional[ComplianceThreshold]:
        """Get compliance threshold for a metric and standard"""
        
        if standard == ComplianceStandard.WHO:
            return cls.WHO_THRESHOLDS.get(metric)
        elif standard == ComplianceStandard.EPA:
            return cls.EPA_THRESHOLDS.get(metric)
        elif standard == ComplianceStandard.EU:
            return cls.EU_THRESHOLDS.get(metric)
        
        return None

    @classmethod
    def check_compliance(
        cls,
        metric: ComplianceMetric,
        value: float,
        standard: ComplianceStandard,
        timestamp: Optional[datetime] = None
    ) -> ComplianceResult:
        """Check if a value complies with a standard"""
        
        threshold = cls.get_threshold(metric, standard)
        if not threshold:
            return ComplianceResult(
                metric=metric,
                standard=standard,
                timestamp=timestamp or datetime.utcnow(),
                value=value,
                threshold_min=0,
                threshold_max=0,
                status=ComplianceStatus.UNKNOWN,
                notes="No threshold defined for this metric/standard combination"
            )

        # Determine status
        if value < threshold.min_value:
            status = ComplianceStatus.NON_COMPLIANT
            notes = f"Value {value} is below minimum threshold {threshold.min_value}"
        elif value > threshold.max_value:
            status = ComplianceStatus.NON_COMPLIANT
            notes = f"Value {value} exceeds maximum threshold {threshold.max_value}"
        else:
            # Check if within warning zone (90% of threshold)
            if threshold.max_value > 0:
                warning_threshold = threshold.max_value * 0.9
                if value > warning_threshold:
                    status = ComplianceStatus.WARNING
                    notes = f"Value {value} is approaching maximum threshold {threshold.max_value}"
                else:
                    status = ComplianceStatus.COMPLIANT
                    notes = "Within compliance range"
            else:
                status = ComplianceStatus.COMPLIANT
                notes = "Within compliance range"

        return ComplianceResult(
            metric=metric,
            standard=standard,
            timestamp=timestamp or datetime.utcnow(),
            value=value,
            threshold_min=threshold.min_value,
            threshold_max=threshold.max_value,
            status=status,
            notes=notes
        )

    @classmethod
    def get_compliance_summary(
        cls,
        results: List[ComplianceResult]
    ) -> Dict[str, Any]:
        """Generate compliance summary from results"""
        
        if not results:
            return {
                "total_checks": 0,
                "compliant": 0,
                "non_compliant": 0,
                "warnings": 0,
                "unknown": 0,
                "compliance_percentage": 0.0,
                "status": ComplianceStatus.UNKNOWN
            }

        total = len(results)
        compliant = sum(1 for r in results if r.status == ComplianceStatus.COMPLIANT)
        non_compliant = sum(1 for r in results if r.status == ComplianceStatus.NON_COMPLIANT)
        warnings = sum(1 for r in results if r.status == ComplianceStatus.WARNING)
        unknown = sum(1 for r in results if r.status == ComplianceStatus.UNKNOWN)

        compliance_pct = (compliant / (total - unknown)) * 100 if (total - unknown) > 0 else 0

        # Overall status
        if non_compliant > 0:
            overall_status = ComplianceStatus.NON_COMPLIANT
        elif warnings > 0:
            overall_status = ComplianceStatus.WARNING
        elif compliant > 0:
            overall_status = ComplianceStatus.COMPLIANT
        else:
            overall_status = ComplianceStatus.UNKNOWN

        return {
            "total_checks": total,
            "compliant": compliant,
            "non_compliant": non_compliant,
            "warnings": warnings,
            "unknown": unknown,
            "compliance_percentage": round(compliance_pct, 2),
            "status": overall_status
        }

    @classmethod
    def generate_compliance_report(
        cls,
        municipality_id: int,
        standard: ComplianceStandard = ComplianceStandard.WHO,
        days: int = 30
    ) -> Dict[str, Any]:
        """Generate compliance report for a municipality"""
        
        # Note: In production, this would query actual sensor data from the database
        # For now, returning structure for the report
        
        report = {
            "municipality_id": municipality_id,
            "standard": standard,
            "period_days": days,
            "generated_at": datetime.utcnow().isoformat(),
            "metrics_checked": [],
            "summary": {},
            "non_compliance_incidents": [],
            "recommendations": []
        }

        # Example structure for metrics checked
        for metric in ComplianceMetric:
            threshold = cls.get_threshold(metric, standard)
            if threshold:
                report["metrics_checked"].append({
                    "metric": metric,
                    "unit": threshold.unit,
                    "min": threshold.min_value,
                    "max": threshold.max_value,
                    "description": threshold.description
                })

        # Add summary
        report["summary"] = {
            "overall_status": "compliant",
            "compliance_percentage": 95.5,
            "metrics_in_compliance": 8,
            "metrics_with_warnings": 1,
            "metrics_non_compliant": 0
        }

        # Add recommendations
        report["recommendations"] = [
            "Continue regular monitoring of all water quality parameters",
            "Maintain current treatment processes",
            "Schedule quarterly compliance audits",
            "Review turbidity levels which are approaching warning thresholds"
        ]

        return report

    @classmethod
    def get_audit_trail(
        cls,
        municipality_id: int,
        days: int = 90
    ) -> List[Dict[str, Any]]:
        """Get audit trail of compliance issues"""
        
        # In production, this would query from audit log
        # Returning empty list as placeholder
        return []

    @classmethod
    def create_compliance_action_plan(
        cls,
        municipality_id: int,
        non_compliant_metrics: List[ComplianceMetric]
    ) -> Dict[str, Any]:
        """Create action plan for non-compliant metrics"""
        
        plan = {
            "municipality_id": municipality_id,
            "created_at": datetime.utcnow().isoformat(),
            "target_completion_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "metrics_to_address": non_compliant_metrics,
            "actions": [],
            "responsible_parties": [],
            "monitoring_schedule": "Daily",
            "review_frequency": "Weekly"
        }

        # Generate actions based on non-compliant metrics
        for metric in non_compliant_metrics:
            actions = cls._get_remedial_actions(metric)
            plan["actions"].extend(actions)

        return plan

    @classmethod
    def _get_remedial_actions(cls, metric: ComplianceMetric) -> List[Dict[str, str]]:
        """Get recommended remedial actions for a metric"""
        
        remedial_map = {
            ComplianceMetric.PH_LEVEL: [
                {
                    "action": "Adjust pH treatment",
                    "priority": "High",
                    "timeline": "24 hours"
                },
                {
                    "action": "Add pH buffer chemicals",
                    "priority": "High",
                    "timeline": "Immediate"
                }
            ],
            ComplianceMetric.TURBIDITY: [
                {
                    "action": "Increase filtration",
                    "priority": "High",
                    "timeline": "2 hours"
                },
                {
                    "action": "Check filter condition",
                    "priority": "High",
                    "timeline": "Immediate"
                }
            ],
            ComplianceMetric.BACTERIA: [
                {
                    "action": "Increase chlorination",
                    "priority": "Critical",
                    "timeline": "Immediate"
                },
                {
                    "action": "Issue boil water notice",
                    "priority": "Critical",
                    "timeline": "Immediate"
                },
                {
                    "action": "Conduct full system disinfection",
                    "priority": "Critical",
                    "timeline": "24 hours"
                }
            ],
            ComplianceMetric.NITRATE: [
                {
                    "action": "Switch to alternative water source",
                    "priority": "High",
                    "timeline": "24 hours"
                },
                {
                    "action": "Install reverse osmosis treatment",
                    "priority": "High",
                    "timeline": "1 week"
                }
            ],
            ComplianceMetric.CHLORINE: [
                {
                    "action": "Adjust chlorine dosage",
                    "priority": "Medium",
                    "timeline": "2 hours"
                }
            ]
        }

        return remedial_map.get(metric, [])


# Global compliance service instance
compliance_service = ComplianceService()
