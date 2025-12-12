# healthcare_scribe_app_streamlit.py

import streamlit as st
import pandas as pd
import spacy
import sqlite3
from datetime import datetime
import re
import json
import random

# ===============================
# Page config — must be first Streamlit command
# ===============================
st.set_page_config(
    page_title="Healthcare Scribe App",
    page_icon="🏥",
    layout="wide"
)

# ===============================
# App Class
# ===============================
class HealthcareScribeApp:
    def __init__(self, db_path: str = 'healthcare_emr.db'):
        self.db_path = db_path
        self.nlp = self._initialize_nlp()
        self.init_database()
        self.medical_terms = self.load_medical_terminology()
    
    def _initialize_nlp(self):
        """Initialize spaCy NLP model with error handling"""
        try:
            return spacy.load("en_core_web_sm")
        except OSError:
            st.warning("⚠️ spaCy model not found. Please run: `python -m spacy download en_core_web_sm`")
            return None
    
    def init_database(self):
        """Initialize SQLite database for patient records"""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.cursor = self.conn.cursor()
            
            # Create tables
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS patients (
                    patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    first_name TEXT, last_name TEXT, date_of_birth DATE,
                    gender TEXT, created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS visits (
                    visit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id INTEGER, visit_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    medical_specialty TEXT, subjective_note TEXT, objective_note TEXT,
                    assessment_note TEXT, plan_note TEXT, structured_data TEXT,
                    FOREIGN KEY (patient_id) REFERENCES patients (patient_id)
                )
            ''')
            
            self.conn.commit()
        except Exception as e:
            st.error(f"Database error: {e}")
    
    def load_medical_terminology(self):
        """Load medical terminology"""
        return {
            'symptoms': ['chest pain', 'headache', 'fever', 'cough', 'shortness of breath', 'fatigue'],
            'medications': ['ibuprofen', 'aspirin', 'claritin', 'zyrtec', 'allegra'],
            'diagnoses': ['allergic rhinitis', 'hypertension', 'diabetes', 'asthma', 'angina'],
            'procedures': ['echocardiogram', 'gastric bypass', 'endoscopy']
        }
    
    def generate_mock_transcription(self):
        """Generate realistic, specialty-specific synthetic transcription dictation."""
        specialties = {
            "Cardiology": [
                "So the patient is telling me they've been having this pressure-like chest discomfort for the past two days. They also report shortness of breath when climbing stairs. Vitals today: BP about 122 over 78, heart rate around 84. No radiating arm pain. My initial thought is possible angina, so I’m planning an EKG and ordering a stress test. I’ll start them on low-dose aspirin once daily."
            ],
            "Allergy/Immunology": [
                "The patient states they’ve had constant sneezing, itchy eyes, and sinus pressure for about a week. They tried Claritin with mild relief. No fever reported. Vitals are stable. This sounds like seasonal allergic rhinitis. My plan is to start them on Zyrtec and Flonase, and recommend allergen avoidance strategies."
            ],
            "Family Medicine": [
                "Patient reports feeling fatigued for the last five days, along with mild dizziness. They deny chest pain or shortness of breath. Vitals: BP 110 over 72, HR 78. This could be mild dehydration or viral illness. Recommended hydration and electrolyte supplementation, and we’ll recheck if symptoms don’t improve."
            ],
            "Bariatrics": [
                "The patient is here for follow-up on their weight management plan. They mention struggling with late-night snacking and feeling low energy. Vitals look good today. They’ve lost about 3 pounds since the last visit. I’m encouraging continuation of their current plan and adding a referral for nutritional counseling."
            ]
        }
        
        filler_phrases = [
            "uh let me see here",
            "so what they're saying is",
            "honestly it sounds like",
            "from what I can tell",
            "they also mentioned that"
        ]

        specialty = random.choice(list(specialties.keys()))
        base_text = random.choice(specialties[specialty])
        filler = random.choice(filler_phrases)
        
        return f"{filler}, {base_text}"

    def extract_medical_entities(self, text: str):
        """Extract medical entities from text"""
        entities = {category: [] for category in self.medical_terms.keys()}
        entities.update({'vitals': [], 'dates': []})
        
        if not self.nlp:
            return entities
        
        text_lower = text.lower()
        
        # Basic entity extraction
        for category, terms in self.medical_terms.items():
            for term in terms:
                if term in text_lower:
                    entities[category].append(term)
        
        # Medications with dosage
        med_pattern = r'(\w+)\s+(\d+mg)'
        for match in re.finditer(med_pattern, text_lower):
            entities['medications'].append(f"{match.group(1)} {match.group(2)}")
        
        # Vitals
        bp_match = re.search(r'bp\s+(\d+/\d+)', text_lower)
        hr_match = re.search(r'hr\s+(\d+)', text_lower)
        
        if bp_match:
            entities['vitals'].append(f"BP: {bp_match.group(1)}")
        if hr_match:
            entities['vitals'].append(f"HR: {hr_match.group(1)}")
        
        return entities
    
    def structure_clinical_note(self, text: str, medical_specialty: str):
        """Structure clinical note into SOAP format"""
        entities = self.extract_medical_entities(text)
        sections = {
            'subjective': self._extract_section(text, ['presents', 'complains', 'reports']),
            'objective': self._extract_section(text, ['vitals', 'exam', 'bp', 'hr']),
            'assessment': self._extract_section(text, ['assessment', 'diagnosis', 'impression']),
            'plan': self._extract_section(text, ['plan', 'prescribed', 'follow up'])
        }
        return {
            'subjective': sections['subjective'] or "No subjective information documented.",
            'objective': sections['objective'] or "No objective findings documented.",
            'assessment': sections['assessment'] or "No assessment documented.",
            'plan': sections['plan'] or "No plan documented.",
            'medical_specialty': medical_specialty,
            'extracted_entities': entities,
            'timestamp': datetime.now().isoformat()
        }
    
    def _extract_section(self, text: str, keywords: list):
        sentences = text.split('.')
        relevant = [s.strip() for s in sentences if any(k in s.lower() for k in keywords)]
        return '. '.join(relevant) if relevant else ""
    
    def create_patient(self, first_name, last_name, dob, gender):
        try:
            self.cursor.execute(
                'INSERT INTO patients (first_name, last_name, date_of_birth, gender) VALUES (?, ?, ?, ?)',
                (first_name, last_name, dob, gender)
            )
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
            st.error(f"Error creating patient: {e}")
            return None
    
    def create_visit(self, patient_id, transcribed_text, specialty):
        try:
            note = self.structure_clinical_note(transcribed_text, specialty)
            self.cursor.execute('''
                INSERT INTO visits (patient_id, medical_specialty, subjective_note, objective_note, 
                                    assessment_note, plan_note, structured_data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                patient_id, specialty, note['subjective'], note['objective'],
                note['assessment'], note['plan'], json.dumps(note)
            ))
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
            st.error(f"Error creating visit: {e}")
            return None

# ===============================
# Main Streamlit App
# ===============================
def main():
    st.title("🏥 Healthcare Scribe & EMR System")
    st.markdown("AI-powered clinical documentation assistant")

    # Initialize app
    if "app" not in st.session_state:
        st.session_state.app = HealthcareScribeApp()
    app = st.session_state.app

    # Transcription
    st.header("🎤 Clinical Documentation")
    if "transcription_text" not in st.session_state:
        st.session_state.transcription_text = ""

    if st.button("🎙️ Generate Sample Transcription"):
        st.session_state.transcription_text = app.generate_mock_transcription()

    clinical_text = st.text_area(
        "Transcription / Clinical Note (editable)",
        height=180,
        key="transcription_text",
        value=st.session_state.transcription_text
    )

    st.markdown("---")

    # Patient info and visit details
    col1, col2 = st.columns([1,1])
    with col1:
        st.subheader("Patient Information")
        first_name = st.text_input("First Name", "John")
        last_name = st.text_input("Last Name", "Doe")
        dob = st.date_input("Date of Birth", datetime(1985,5,15))
        gender = st.selectbox("Gender", ["Male","Female","Other"])
        st.subheader("Visit Details")
        specialty = st.selectbox("Medical Specialty", [
            "Cardiology","Allergy/Immunology","Bariatrics","Family Medicine"
        ])
    with col2:
        st.subheader("Structured Output")
        if st.button("🔄 Process Clinical Note", type="primary"):
            if clinical_text.strip():
                with st.spinner("Processing clinical note..."):
                    patient_id = app.create_patient(
                        first_name, last_name, dob.strftime("%Y-%m-%d"), gender
                    )
                    if patient_id:
                        structured_note = app.structure_clinical_note(clinical_text, specialty)
                        st.success("✅ Clinical note processed successfully!")

                        # SOAP
                        soap_col1, soap_col2 = st.columns(2)
                        with soap_col1:
                            st.text_area("Subjective", structured_note['subjective'], height=100)
                            st.text_area("Assessment", structured_note['assessment'], height=100)
                        with soap_col2:
                            st.text_area("Objective", structured_note['objective'], height=100)
                            st.text_area("Plan", structured_note['plan'], height=100)

                        # Entities
                        st.subheader("🔍 Extracted Medical Entities")
                        for category, items in structured_note['extracted_entities'].items():
                            if items:
                                st.write(f"**{category.title()}:** {', '.join(items)}")

                        # Save visit
                        visit_id = app.create_visit(patient_id, clinical_text, specialty)
                        if visit_id:
                            st.session_state.last_patient_id = patient_id
                            st.session_state.last_visit_id = visit_id
                            st.session_state.last_specialty = specialty
                            st.info(f"💾 Saved to database - Patient ID: {patient_id}, Visit ID: {visit_id}")
            else:
                st.warning("Please enter clinical text to process.")

    # Visit Overview / Demo
    st.header("🚀 Visit Overview / Demo")
    if st.button("Show Last Processed Note"):
        if st.session_state.get("transcription_text","").strip():
            clinical_text = st.session_state["transcription_text"]
            specialty = st.session_state.get("last_specialty", "General Medicine")
            structured_note = app.structure_clinical_note(clinical_text, specialty)

            st.subheader("📋 Structured SOAP Note (Last Processed)")
            soap_col1, soap_col2 = st.columns(2)
            with soap_col1:
                st.text_area("Subjective", structured_note['subjective'], height=100)
                st.text_area("Assessment", structured_note['assessment'], height=100)
            with soap_col2:
                st.text_area("Objective", structured_note['objective'], height=100)
                st.text_area("Plan", structured_note['plan'], height=100)

            st.subheader("🔍 Extracted Medical Entities")
            for category, items in structured_note['extracted_entities'].items():
                if items:
                    st.write(f"**{category.title()}:** {', '.join(items)}")

            last_patient_id = st.session_state.get("last_patient_id")
            last_visit_id = st.session_state.get("last_visit_id")
            if last_patient_id and last_visit_id:
                st.info(f"💾 Patient ID: {last_patient_id} | Visit ID: {last_visit_id}")
        else:
            st.warning("No transcription available. Process a clinical note first.")

# ===============================
# LEARN MORE
# ===============================
with st.expander("📖 Learn More About This App"):
    st.markdown("""
    **Healthcare Scribe & EMR System** is an AI-assisted clinical documentation assistant that helps medical providers:
    
    - **Transcribe and Review Notes**: Generate synthetic demo transcriptions or paste your own clinical notes for review.
    - **Organize Notes into SOAP Format**: Automatically structures notes into **Subjective, Objective, Assessment, and Plan** sections using keyword-based extraction.
    - **Extract Key Medical Entities**: Identifies symptoms, medications (with dosages), diagnoses, procedures, and vital signs from the clinical text.
    - **Patient & Visit Management**: Create patient records and visits in a SQLite database for documentation and future reference.
    - **Visit Overview / Demo**: Quickly review the last processed clinical note, including structured SOAP sections and extracted entities.
    
    ⚠️ **Note:** The summarization is currently rule-based using keywords. It does **not** use an AI language model to generate summaries, but it organizes and highlights clinical information effectively for documentation purposes.
    
    This tool is ideal for **training, demonstrations, or streamlining note-taking** in medical workflows.
    """)


if __name__ == "__main__":
    main()

