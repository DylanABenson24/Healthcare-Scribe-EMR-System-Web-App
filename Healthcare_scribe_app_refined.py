# healthcare_scribe_app_streamlit.py

import streamlit as st
import pandas as pd
import spacy
import sqlite3
from datetime import datetime
import re
import json

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
    
    def transcribe_audio_to_text(self, audio_file_path: str) -> str:
        """Simulate audio transcription"""
        return "Patient presents with chest pain and shortness of breath. Vitals: BP 120/80, HR 85. Assessment: Possible angina. Plan: Prescribed ibuprofen 200mg twice daily."
    
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
        
        # Extract medications with dosage
        med_pattern = r'(\w+)\s+(\d+mg)'
        for match in re.finditer(med_pattern, text_lower):
            entities['medications'].append(f"{match.group(1)} {match.group(2)}")
        
        # Extract vitals
        bp_pattern = r'bp\s+(\d+/\d+)'
        hr_pattern = r'hr\s+(\d+)'
        
        bp_match = re.search(bp_pattern, text_lower)
        hr_match = re.search(hr_pattern, text_lower)
        
        if bp_match:
            entities['vitals'].append(f"BP: {bp_match.group(1)}")
        if hr_match:
            entities['vitals'].append(f"HR: {hr_match.group(1)}")
        
        return entities
    
    def structure_clinical_note(self, text: str, medical_specialty: str):
        """Structure clinical note into SOAP format"""
        entities = self.extract_medical_entities(text)
        
        # Simple SOAP extraction
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
        """Extract section based on keywords"""
        sentences = text.split('.')
        relevant_sentences = []
        
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in keywords):
                relevant_sentences.append(sentence.strip())
        
        return '. '.join(relevant_sentences) if relevant_sentences else ""
    
    def create_patient(self, first_name: str, last_name: str, date_of_birth: str, gender: str) -> int:
        """Create new patient"""
        try:
            self.cursor.execute(
                'INSERT INTO patients (first_name, last_name, date_of_birth, gender) VALUES (?, ?, ?, ?)',
                (first_name, last_name, date_of_birth, gender)
            )
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
            st.error(f"Error creating patient: {e}")
            return None
    
    def create_visit(self, patient_id: int, transcribed_text: str, medical_specialty: str) -> int:
        """Create new visit"""
        try:
            structured_note = self.structure_clinical_note(transcribed_text, medical_specialty)
            
            self.cursor.execute('''
                INSERT INTO visits (patient_id, medical_specialty, subjective_note, objective_note, 
                                  assessment_note, plan_note, structured_data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                patient_id, medical_specialty,
                structured_note['subjective'], structured_note['objective'],
                structured_note['assessment'], structured_note['plan'],
                json.dumps(structured_note)
            ))
            
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
            st.error(f"Error creating visit: {e}")
            return None

def main():
    """Main Streamlit app"""
    st.set_page_config(
        page_title="Healthcare Scribe App",
        page_icon="🏥",
        layout="wide"
    )
    
    st.title("🏥 Healthcare Scribe & EMR System")
    st.markdown("AI-powered clinical documentation assistant")
    
    # Initialize app
    if 'app' not in st.session_state:
        st.session_state.app = HealthcareScribeApp()
    
    app = st.session_state.app
    
    # Main interface
    st.header("🎤 Clinical Documentation")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Patient Information")
        first_name = st.text_input("First Name", "John")
        last_name = st.text_input("Last Name", "Doe")
        dob = st.date_input("Date of Birth", datetime(1985, 5, 15))
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        
        st.subheader("Visit Details")
        specialty = st.selectbox("Medical Specialty", [
            "Cardiology", "Allergy/Immunology", "Bariatrics", "Family Medicine"
        ])
        
        st.subheader("Clinical Input")
        clinical_text = st.text_area(
            "Enter clinical note text:",
            height=150,
            value="Patient presents with chest pain and shortness of breath. Vitals: BP 120/80, HR 85. Assessment: Possible angina. Plan: Prescribed ibuprofen 200mg twice daily and follow up in 2 weeks."
        )
    
    with col2:
        st.subheader("Structured Output")
        
        if st.button("🔄 Process Clinical Note", type="primary"):
            if clinical_text.strip():
                with st.spinner("Processing clinical note..."):
                    try:
                        # Create patient
                        patient_id = app.create_patient(
                            first_name, last_name, 
                            dob.strftime("%Y-%m-%d"), gender
                        )
                        
                        if patient_id:
                            # Process note
                            structured_note = app.structure_clinical_note(clinical_text, specialty)
                            
                            st.success("✅ Clinical note processed successfully!")
                            
                            # Display SOAP note
                            st.subheader("📋 Structured SOAP Note")
                            
                            soap_col1, soap_col2 = st.columns(2)
                            
                            with soap_col1:
                                st.text_area(
                                    "Subjective", 
                                    structured_note['subjective'],
                                    height=100,
                                    key="subjective"
                                )
                                st.text_area(
                                    "Assessment",
                                    structured_note['assessment'],
                                    height=100,
                                    key="assessment"
                                )
                            
                            with soap_col2:
                                st.text_area(
                                    "Objective",
                                    structured_note['objective'],
                                    height=100,
                                    key="objective"
                                )
                                st.text_area(
                                    "Plan",
                                    structured_note['plan'],
                                    height=100,
                                    key="plan"
                                )
                            
                            # Display extracted entities
                            st.subheader("🔍 Extracted Medical Entities")
                            entities = structured_note['extracted_entities']
                            
                            for category, items in entities.items():
                                if items:
                                    st.write(f"**{category.title()}:** {', '.join(items)}")
                            
                            # Save to database
                            visit_id = app.create_visit(patient_id, clinical_text, specialty)
                            if visit_id:
                                st.info(f"💾 Saved to database - Patient ID: {patient_id}, Visit ID: {visit_id}")
                        
                    except Exception as e:
                        st.error(f"Error processing note: {e}")
            else:
                st.warning("Please enter clinical text to process.")
    
    # Demo section
    st.header("🚀 Quick Demo")
    if st.button("Run Demo with Sample Data"):
        sample_text = "Patient presents with allergic rhinitis and asthma. Has tried Claritin and Zyrtec. Vitals normal. Assessment: Allergic rhinitis. Plan: Continue Claritin and follow up in 1 month."
        
        with st.spinner("Running demo..."):
            demo_note = app.structure_clinical_note(sample_text, "Allergy/Immunology")
            
            st.subheader("Demo Results")
            st.json(demo_note)

if __name__ == "__main__":
    main()