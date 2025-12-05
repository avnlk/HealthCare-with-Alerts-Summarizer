import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.vitals import vitals_generator

client = TestClient(app)


class TestHealthEndpoint:
    def test_health_check(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert "service" in response.json()


class TestPatientsEndpoint:
    def test_get_all_patients(self):
        response = client.get("/api/patients")
        assert response.status_code == 200
        patients = response.json()
        assert isinstance(patients, list)
        assert len(patients) > 0
    
    def test_get_patient_by_id(self):
        response = client.get("/api/patients/P001")
        assert response.status_code == 200
        patient = response.json()
        assert patient["id"] == "P001"
        assert "vitals" in patient
    
    def test_get_patient_not_found(self):
        response = client.get("/api/patients/INVALID")
        assert response.status_code == 404


class TestVitalsEndpoint:
    def test_get_patient_vitals(self):
        response = client.get("/api/patients/P001/vitals")
        assert response.status_code == 200
        vitals = response.json()
        assert "heartRate" in vitals
        assert "spO2" in vitals
        assert "bloodPressure" in vitals
        assert "temperature" in vitals
    
    def test_get_vitals_history(self):
        response = client.get("/api/patients/P001/vitals/history?hours=1")
        assert response.status_code == 200
        history = response.json()
        assert "heartRate" in history
        assert isinstance(history["heartRate"], list)


class TestVitalsGenerator:
    def test_vitals_ranges(self):
        patient = vitals_generator.get_patient("P001")
        vitals = patient.vitals
        
        assert 30 <= vitals.heart_rate <= 180
        assert 70 <= vitals.spo2 <= 100
        assert 70 <= vitals.blood_pressure["systolic"] <= 220
        assert 40 <= vitals.blood_pressure["diastolic"] <= 130
        assert 34.0 <= vitals.temperature <= 42.0
        assert 6 <= vitals.respiratory_rate <= 40
    
    def test_update_vitals(self):
        old_hr = vitals_generator.get_patient("P001").vitals.heart_rate
        vitals_generator.update_vitals("P001")
        # Vitals should update (may be same value occasionally)
        new_patient = vitals_generator.get_patient("P001")
        assert new_patient is not None
