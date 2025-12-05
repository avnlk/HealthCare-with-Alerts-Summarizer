import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.alerts import alert_engine, AlertType, AlertSeverity

client = TestClient(app)


class TestHealthEndpoint:
    def test_health_check(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestAlertsEndpoint:
    def test_get_all_alerts(self):
        response = client.get("/api/alerts")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_get_patient_alerts(self):
        response = client.get("/api/alerts/P001")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestAlertEngine:
    def test_tachycardia_detection(self):
        vitals = {
            "heartRate": 135,
            "spO2": 98,
            "bloodPressure": {"systolic": 120, "diastolic": 80},
            "temperature": 37.0,
            "respiratory": 16
        }
        alerts = alert_engine.analyze_vitals("TEST001", vitals)
        alert_types = [a.type for a in alerts]
        assert AlertType.TACHYCARDIA.value in alert_types
    
    def test_hypoxia_detection(self):
        vitals = {
            "heartRate": 80,
            "spO2": 85,
            "bloodPressure": {"systolic": 120, "diastolic": 80},
            "temperature": 37.0,
            "respiratory": 16
        }
        alerts = alert_engine.analyze_vitals("TEST002", vitals)
        alert_types = [a.type for a in alerts]
        assert AlertType.HYPOXIA.value in alert_types
    
    def test_hypertensive_crisis_detection(self):
        vitals = {
            "heartRate": 80,
            "spO2": 98,
            "bloodPressure": {"systolic": 190, "diastolic": 110},
            "temperature": 37.0,
            "respiratory": 16
        }
        alerts = alert_engine.analyze_vitals("TEST003", vitals)
        alert_types = [a.type for a in alerts]
        assert AlertType.HYPERTENSIVE_CRISIS.value in alert_types
    
    def test_fever_detection(self):
        vitals = {
            "heartRate": 80,
            "spO2": 98,
            "bloodPressure": {"systolic": 120, "diastolic": 80},
            "temperature": 39.5,
            "respiratory": 16
        }
        alerts = alert_engine.analyze_vitals("TEST004", vitals)
        alert_types = [a.type for a in alerts]
        assert AlertType.FEVER.value in alert_types
    
    def test_normal_vitals_no_alerts(self):
        vitals = {
            "heartRate": 75,
            "spO2": 98,
            "bloodPressure": {"systolic": 118, "diastolic": 76},
            "temperature": 36.8,
            "respiratory": 15
        }
        alerts = alert_engine.analyze_vitals("TEST005", vitals)
        assert len(alerts) == 0
    
    def test_multiple_alerts(self):
        vitals = {
            "heartRate": 140,
            "spO2": 85,
            "bloodPressure": {"systolic": 190, "diastolic": 110},
            "temperature": 39.5,
            "respiratory": 32
        }
        alerts = alert_engine.analyze_vitals("TEST006", vitals)
        assert len(alerts) >= 3  # Should have multiple alerts


class TestAnalyzeEndpoint:
    def test_analyze_vitals(self):
        response = client.post(
            "/api/analyze",
            params={"patient_id": "TEST007"},
            json={
                "heartRate": 150,
                "spO2": 85,
                "bloodPressure": {"systolic": 200, "diastolic": 115},
                "temperature": 40.0,
                "respiratory": 35
            }
        )
        assert response.status_code == 200
        result = response.json()
        assert "alerts" in result
        assert len(result["alerts"]) > 0
