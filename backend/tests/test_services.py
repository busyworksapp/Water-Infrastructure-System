import sys
from types import SimpleNamespace

sys.path.insert(0, "backend")

from app.models.system import ProtocolType
from app.services.alert_service import AlertService
from app.services.anomaly_detector import anomaly_detector
from app.services.protocol_service import ProtocolService


def test_rule_condition_evaluation_gt():
    reading = SimpleNamespace(value=7.5, raw_data={"delta": 1.2})
    condition = {"operator": "gt", "field": "value", "threshold": 6}
    assert anomaly_detector._evaluate_condition(condition, reading) is True


def test_rule_condition_evaluation_between():
    reading = SimpleNamespace(value=4.2, raw_data={})
    condition = {"operator": "between", "min": 3.5, "max": 5.0}
    assert anomaly_detector._evaluate_condition(condition, reading) is True


def test_protocol_normalization():
    service = ProtocolService()
    assert service.normalize_protocol("MQTT") == ProtocolType.MQTT
    assert service.normalize_protocol("nbiot") == ProtocolType.NBIOT


def test_alert_severity_mapping():
    service = AlertService()
    assert service._determine_severity(0.95).value == "critical"
    assert service._determine_severity(0.75).value == "high"
    assert service._determine_severity(0.10).value == "info"
