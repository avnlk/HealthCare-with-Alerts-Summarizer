import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.summarizer import summarizer, generate_input_text

client = TestClient(app)


class TestHealthEndpoint:
    def test_health_check(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestModelInfoEndpoint:
    def test_get_model_info(self):
        response = client.get("/api/model/info")
        assert response.status_code == 200
        info = response.json()
        assert "name" in info
        assert "version" in info


class TestSummariesEndpoint:
    def test_get_all_summaries(self):
        response = client.get("/api/summaries")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_get_patient_summary(self):
        response = client.get("/api/summaries/P001")
        assert response.status_code == 200
        summary = response.json()
        assert "text" in summary or "patient_id" in summary


class TestInputGeneration:
    def test_generate_input_with_vitals(self):
        vitals = [
            {
                "heart_rate": 80,
                "spo2": 98,
                "systolic_bp": 120,
                "diastolic_bp": 80,
                "temperature": 37.0,
                "respiratory_rate": 16
            }
        ]
        alerts = []
        
        input_text = generate_input_text(vitals, alerts, "John Doe")
        assert "John Doe" in input_text
        assert "Heart rate" in input_text
    
    def test_generate_input_with_alerts(self):
        vitals = [
            {
                "heart_rate": 80,
                "spo2": 85,
                "systolic_bp": 120,
                "diastolic_bp": 80,
                "temperature": 37.0,
                "respiratory_rate": 16
            }
        ]
        alerts = [
            {"severity": "critical", "alert_type": "Hypoxia Alert"},
            {"severity": "warning", "alert_type": "Fever Alert"}
        ]
        
        input_text = generate_input_text(vitals, alerts, "Jane Doe")
        assert "critical" in input_text.lower() or "alert" in input_text.lower()


class TestSummarizer:
    def test_generate_summary(self):
        vitals = [
            {
                "heart_rate": 80,
                "spo2": 98,
                "systolic_bp": 120,
                "diastolic_bp": 80,
                "temperature": 37.0,
                "respiratory_rate": 16
            }
        ]
        alerts = []
        
        summary = summarizer.generate_summary("TEST001", "Test Patient", vitals, alerts)
        assert "text" in summary
        assert len(summary["text"]) > 0
        assert "patient_id" in summary
        assert summary["patient_id"] == "TEST001"
    
    def test_model_info(self):
        info = summarizer.get_model_info()
        assert "name" in info
        assert "version" in info


class TestTriggerSummary:
    def test_trigger_summary(self):
        response = client.post(
            "/api/model/trigger-summary",
            json={"patientId": "P001"}
        )
        assert response.status_code == 200
        result = response.json()
        assert "status" in result
        assert "summary" in result
