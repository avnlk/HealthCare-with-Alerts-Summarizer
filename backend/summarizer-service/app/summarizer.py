import logging
import time
from typing import Optional, List, Dict
from datetime import datetime

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Global model instance
_model = None
_tokenizer = None


def load_model():
    """Load the DistilBART model for summarization."""
    global _model, _tokenizer
    
    if _model is not None:
        return _model, _tokenizer
    
    try:
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        
        logger.info(f"Loading summarization model: {settings.model_name}")
        
        _tokenizer = AutoTokenizer.from_pretrained(settings.model_name)
        _model = AutoModelForSeq2SeqLM.from_pretrained(settings.model_name)
        
        logger.info("Model loaded successfully")
        return _model, _tokenizer
        
    except Exception as e:
        logger.warning(f"Failed to load model: {e}. Using fallback summarization.")
        return None, None


def generate_input_text(vitals: List[Dict], alerts: List[Dict], patient_name: str = "Patient") -> str:
    """Generate input text from vitals and alerts data."""
    
    parts = [f"Clinical data for {patient_name}:"]
    
    # Vitals summary
    if vitals:
        latest = vitals[0]
        hr = latest.get("heart_rate", "N/A")
        spo2 = latest.get("spo2", "N/A")
        sys_bp = latest.get("systolic_bp", "N/A")
        dia_bp = latest.get("diastolic_bp", "N/A")
        temp = latest.get("temperature", "N/A")
        resp = latest.get("respiratory_rate", "N/A")
        
        parts.append(f"Current vitals: Heart rate {hr} bpm, SpO2 {spo2}%, Blood pressure {sys_bp}/{dia_bp} mmHg, Temperature {temp}°C, Respiratory rate {resp}/min.")
        
        # Calculate averages
        if len(vitals) > 1:
            avg_hr = sum(v.get("heart_rate", 0) for v in vitals if v.get("heart_rate")) / len([v for v in vitals if v.get("heart_rate")])
            avg_spo2 = sum(v.get("spo2", 0) for v in vitals if v.get("spo2")) / len([v for v in vitals if v.get("spo2")])
            parts.append(f"Average over monitoring period: Heart rate {avg_hr:.0f} bpm, SpO2 {avg_spo2:.0f}%.")
    
    # Alerts summary
    if alerts:
        critical_alerts = [a for a in alerts if a.get("severity") == "critical"]
        warning_alerts = [a for a in alerts if a.get("severity") == "warning"]
        
        if critical_alerts:
            critical_types = list(set(a.get("alert_type", "Unknown") for a in critical_alerts))
            parts.append(f"Critical alerts detected: {', '.join(critical_types)}.")
        
        if warning_alerts:
            warning_types = list(set(a.get("alert_type", "Unknown") for a in warning_alerts))
            parts.append(f"Warning alerts: {', '.join(warning_types)}.")
        
        parts.append(f"Total alerts in monitoring period: {len(alerts)} ({len(critical_alerts)} critical, {len(warning_alerts)} warnings).")
    else:
        parts.append("No alerts detected during monitoring period.")
    
    return " ".join(parts)


def summarize_text(text: str) -> str:
    """Generate summary using the loaded model."""
    model, tokenizer = load_model()
    
    if model is None or tokenizer is None:
        # Fallback summarization
        return fallback_summarize(text)
    
    try:
        inputs = tokenizer(
            text, 
            return_tensors="pt", 
            max_length=settings.max_input_length, 
            truncation=True
        )
        
        summary_ids = model.generate(
            inputs["input_ids"],
            max_length=settings.max_output_length,
            min_length=settings.min_output_length,
            length_penalty=2.0,
            num_beams=4,
            early_stopping=True
        )
        
        summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        return summary
        
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        return fallback_summarize(text)


def fallback_summarize(text: str) -> str:
    """Fallback summarization when model is not available."""
    # Simple extractive summarization
    sentences = text.split(". ")
    
    # Always include first sentence and key information
    key_sentences = [sentences[0]] if sentences else []
    
    keywords = ["critical", "warning", "alert", "detected", "average", "total"]
    for sentence in sentences[1:]:
        if any(kw in sentence.lower() for kw in keywords):
            key_sentences.append(sentence)
    
    # Limit summary length
    summary = ". ".join(key_sentences[:5])
    if not summary.endswith("."):
        summary += "."
    
    return summary


class MedicalSummarizer:
    """Medical data summarization engine."""
    
    def __init__(self):
        self.summaries: Dict[str, Dict] = {}
        # Pre-load model
        load_model()
    
    def generate_summary(self, patient_id: str, patient_name: str, 
                        vitals: List[Dict], alerts: List[Dict]) -> Dict:
        """Generate a clinical summary for a patient."""
        
        start_time = time.time()
        
        # Generate input text
        input_text = generate_input_text(vitals, alerts, patient_name)
        
        # Generate summary
        summary_text = summarize_text(input_text)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        result = {
            "patient_id": patient_id,
            "patient_name": patient_name,
            "text": summary_text,
            "vitals_count": len(vitals),
            "alerts_count": len(alerts),
            "processing_time_ms": processing_time,
            "timestamp": datetime.now().isoformat(),
            "model_name": settings.model_name,
            "model_version": settings.model_version
        }
        
        # Cache the summary
        self.summaries[patient_id] = result
        
        return result
    
    def get_summary(self, patient_id: str) -> Optional[Dict]:
        """Get cached summary for a patient."""
        return self.summaries.get(patient_id)
    
    def get_all_summaries(self) -> List[Dict]:
        """Get all cached summaries."""
        return list(self.summaries.values())
    
    def get_model_info(self) -> Dict:
        """Get model information."""
        model, tokenizer = load_model()
        
        return {
            "name": settings.model_name.split("/")[-1],
            "version": settings.model_version,
            "full_name": settings.model_name,
            "loaded": model is not None,
            "max_input_length": settings.max_input_length,
            "max_output_length": settings.max_output_length,
            "lastUpdated": datetime.now().strftime("%Y-%m-%d")
        }


# Singleton instance
summarizer = MedicalSummarizer()
