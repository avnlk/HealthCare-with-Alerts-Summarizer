import random
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pydantic import BaseModel


class VitalSigns(BaseModel):
    """Model for patient vital signs."""
    heart_rate: int
    spo2: int
    blood_pressure: Dict[str, int]
    temperature: float
    respiratory_rate: int
    timestamp: str


class Patient(BaseModel):
    """Model for patient data."""
    id: str
    name: str
    bed_number: str
    age: int
    gender: str
    admission_date: str
    diagnosis: Optional[str] = None
    attending_physician: Optional[str] = None
    vitals: VitalSigns
    alert_severity: str


# Clinical normal ranges
VITAL_RANGES = {
    "heart_rate": {"min": 60, "max": 100, "critical_low": 40, "critical_high": 150},
    "spo2": {"min": 95, "max": 100, "critical_low": 88, "warning_low": 92},
    "systolic": {"min": 90, "max": 120, "warning_high": 140, "critical_high": 180},
    "diastolic": {"min": 60, "max": 80, "warning_high": 90, "critical_high": 110},
    "temperature": {"min": 36.1, "max": 37.2, "warning_high": 38.0, "critical_high": 39.0},
    "respiratory_rate": {"min": 12, "max": 20, "warning_high": 24, "critical_high": 30}
}

# Sample patient data
PATIENT_DATA = [
    {"id": "P001", "name": "John Smith", "bed": "ICU-101", "age": 65, "gender": "Male", "condition": "stable"},
    {"id": "P002", "name": "Sarah Johnson", "bed": "ICU-102", "age": 45, "gender": "Female", "condition": "moderate"},
    {"id": "P003", "name": "Michael Brown", "bed": "ICU-103", "age": 72, "gender": "Male", "condition": "critical"},
    {"id": "P004", "name": "Emily Davis", "bed": "ICU-104", "age": 38, "gender": "Female", "condition": "stable"},
    {"id": "P005", "name": "Robert Wilson", "bed": "ICU-105", "age": 58, "gender": "Male", "condition": "moderate"},
    {"id": "P006", "name": "Jennifer Martinez", "bed": "ICU-106", "age": 51, "gender": "Female", "condition": "stable"},
    {"id": "P007", "name": "David Lee", "bed": "ICU-107", "age": 69, "gender": "Male", "condition": "stable"},
    {"id": "P008", "name": "Lisa Anderson", "bed": "ICU-108", "age": 43, "gender": "Female", "condition": "critical"},
    {"id": "P009", "name": "James Taylor", "bed": "ICU-109", "age": 55, "gender": "Male", "condition": "moderate"},
    {"id": "P010", "name": "Maria Garcia", "bed": "ICU-110", "age": 62, "gender": "Female", "condition": "stable"},
]

DIAGNOSES = [
    "Acute Respiratory Distress Syndrome (ARDS)",
    "Sepsis",
    "Pneumonia",
    "Acute Myocardial Infarction",
    "Congestive Heart Failure",
    "Diabetic Ketoacidosis",
    "Stroke",
    "Acute Kidney Injury",
    "Post-operative monitoring",
    "Multi-organ failure"
]

PHYSICIANS = [
    "Dr. James Wilson", "Dr. Sarah Chen", "Dr. Michael Roberts",
    "Dr. Emily Thompson", "Dr. David Kim", "Dr. Jennifer Adams"
]


class VitalsGenerator:
    """Generates realistic medical vitals for simulated patients."""
    
    def __init__(self):
        self.patients: Dict[str, Patient] = {}
        self.patient_states: Dict[str, Dict] = {}
        self._initialize_patients()
    
    def _initialize_patients(self):
        """Initialize patient data with realistic vitals."""
        admission_base = datetime.now() - timedelta(days=10)
        
        for i, data in enumerate(PATIENT_DATA):
            patient_id = data["id"]
            condition = data["condition"]
            
            # Set base vitals based on patient condition
            self.patient_states[patient_id] = self._get_initial_state(condition)
            
            vitals = self._generate_vitals(patient_id)
            severity = self._calculate_severity(vitals)
            
            patient = Patient(
                id=patient_id,
                name=data["name"],
                bed_number=data["bed"],
                age=data["age"],
                gender=data["gender"],
                admission_date=(admission_base + timedelta(days=random.randint(0, 10))).isoformat(),
                diagnosis=random.choice(DIAGNOSES),
                attending_physician=random.choice(PHYSICIANS),
                vitals=vitals,
                alert_severity=severity
            )
            self.patients[patient_id] = patient
    
    def _get_initial_state(self, condition: str) -> Dict:
        """Get initial vital parameters based on patient condition."""
        if condition == "critical":
            return {
                "hr_base": random.choice([45, 55, 115, 130]),
                "hr_variance": 15,
                "spo2_base": random.randint(84, 90),
                "spo2_variance": 4,
                "sys_base": random.choice([85, 175, 190]),
                "sys_variance": 15,
                "dias_base": random.choice([55, 100, 110]),
                "dias_variance": 10,
                "temp_base": random.choice([35.5, 38.5, 39.5]),
                "temp_variance": 0.5,
                "resp_base": random.choice([8, 10, 28, 32]),
                "resp_variance": 4,
                "trend": random.choice(["declining", "unstable"])
            }
        elif condition == "moderate":
            return {
                "hr_base": random.randint(85, 105),
                "hr_variance": 10,
                "spo2_base": random.randint(91, 94),
                "spo2_variance": 3,
                "sys_base": random.randint(135, 155),
                "sys_variance": 10,
                "dias_base": random.randint(85, 95),
                "dias_variance": 8,
                "temp_base": round(random.uniform(37.3, 38.2), 1),
                "temp_variance": 0.3,
                "resp_base": random.randint(20, 25),
                "resp_variance": 3,
                "trend": "fluctuating"
            }
        else:  # stable
            return {
                "hr_base": random.randint(65, 85),
                "hr_variance": 8,
                "spo2_base": random.randint(96, 99),
                "spo2_variance": 2,
                "sys_base": random.randint(110, 130),
                "sys_variance": 8,
                "dias_base": random.randint(65, 80),
                "dias_variance": 5,
                "temp_base": round(random.uniform(36.4, 37.0), 1),
                "temp_variance": 0.2,
                "resp_base": random.randint(14, 18),
                "resp_variance": 2,
                "trend": "stable"
            }
    
    def _generate_vitals(self, patient_id: str) -> VitalSigns:
        """Generate realistic vitals with natural variation."""
        state = self.patient_states[patient_id]
        
        # Add some temporal variation (sine wave for natural rhythm)
        time_factor = math.sin(datetime.now().timestamp() / 60) * 0.3
        
        heart_rate = int(state["hr_base"] + random.gauss(0, state["hr_variance"] / 2) + time_factor * 5)
        heart_rate = max(30, min(180, heart_rate))
        
        spo2 = int(state["spo2_base"] + random.gauss(0, state["spo2_variance"] / 2))
        spo2 = max(70, min(100, spo2))
        
        systolic = int(state["sys_base"] + random.gauss(0, state["sys_variance"] / 2))
        systolic = max(70, min(220, systolic))
        
        diastolic = int(state["dias_base"] + random.gauss(0, state["dias_variance"] / 2))
        diastolic = max(40, min(130, diastolic))
        
        # Ensure diastolic < systolic
        if diastolic >= systolic:
            diastolic = systolic - 20
        
        temperature = round(state["temp_base"] + random.gauss(0, state["temp_variance"] / 2), 1)
        temperature = max(34.0, min(42.0, temperature))
        
        respiratory = int(state["resp_base"] + random.gauss(0, state["resp_variance"] / 2))
        respiratory = max(6, min(40, respiratory))
        
        return VitalSigns(
            heart_rate=heart_rate,
            spo2=spo2,
            blood_pressure={"systolic": systolic, "diastolic": diastolic},
            temperature=temperature,
            respiratory_rate=respiratory,
            timestamp=datetime.now().isoformat()
        )
    
    def _calculate_severity(self, vitals: VitalSigns) -> str:
        """Calculate alert severity based on vitals."""
        critical_count = 0
        warning_count = 0
        
        # Heart rate
        if vitals.heart_rate < 40 or vitals.heart_rate > 150:
            critical_count += 1
        elif vitals.heart_rate < 50 or vitals.heart_rate > 120:
            warning_count += 1
        
        # SpO2
        if vitals.spo2 < 88:
            critical_count += 1
        elif vitals.spo2 < 92:
            warning_count += 1
        
        # Blood pressure
        if vitals.blood_pressure["systolic"] > 180 or vitals.blood_pressure["systolic"] < 80:
            critical_count += 1
        elif vitals.blood_pressure["systolic"] > 140 or vitals.blood_pressure["systolic"] < 90:
            warning_count += 1
        
        # Temperature
        if vitals.temperature > 39.0 or vitals.temperature < 35.0:
            critical_count += 1
        elif vitals.temperature > 38.0:
            warning_count += 1
        
        # Respiratory
        if vitals.respiratory_rate > 30 or vitals.respiratory_rate < 8:
            critical_count += 1
        elif vitals.respiratory_rate > 24 or vitals.respiratory_rate < 10:
            warning_count += 1
        
        if critical_count > 0:
            return "critical"
        elif warning_count >= 2:
            return "warning"
        elif warning_count == 1:
            return "info"
        return "normal"
    
    def update_vitals(self, patient_id: str) -> Optional[Patient]:
        """Update vitals for a specific patient."""
        if patient_id not in self.patients:
            return None
        
        vitals = self._generate_vitals(patient_id)
        severity = self._calculate_severity(vitals)
        
        patient = self.patients[patient_id]
        patient.vitals = vitals
        patient.alert_severity = severity
        
        return patient
    
    def update_all_vitals(self) -> List[Patient]:
        """Update vitals for all patients."""
        updated = []
        for patient_id in self.patients:
            patient = self.update_vitals(patient_id)
            if patient:
                updated.append(patient)
        return updated
    
    def get_patient(self, patient_id: str) -> Optional[Patient]:
        """Get patient by ID."""
        return self.patients.get(patient_id)
    
    def get_all_patients(self) -> List[Patient]:
        """Get all patients."""
        return list(self.patients.values())
    
    def get_patient_vitals_history(self, patient_id: str, hours: int = 1) -> List[VitalSigns]:
        """Generate historical vitals data for a patient."""
        if patient_id not in self.patients:
            return []
        
        history = []
        now = datetime.now()
        interval_minutes = 1
        total_points = (hours * 60) // interval_minutes
        
        state = self.patient_states[patient_id]
        
        for i in range(total_points):
            timestamp = now - timedelta(minutes=i * interval_minutes)
            time_factor = math.sin(timestamp.timestamp() / 60) * 0.3
            
            vitals = VitalSigns(
                heart_rate=int(state["hr_base"] + random.gauss(0, state["hr_variance"]) + time_factor * 5),
                spo2=int(state["spo2_base"] + random.gauss(0, state["spo2_variance"])),
                blood_pressure={
                    "systolic": int(state["sys_base"] + random.gauss(0, state["sys_variance"])),
                    "diastolic": int(state["dias_base"] + random.gauss(0, state["dias_variance"]))
                },
                temperature=round(state["temp_base"] + random.gauss(0, state["temp_variance"]), 1),
                respiratory_rate=int(state["resp_base"] + random.gauss(0, state["resp_variance"])),
                timestamp=timestamp.isoformat()
            )
            history.append(vitals)
        
        return list(reversed(history))


# Singleton instance
vitals_generator = VitalsGenerator()
