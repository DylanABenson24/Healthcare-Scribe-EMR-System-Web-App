# 🏥 Healthcare Scribe & EMR System  
### AI-Assisted Clinical Documentation (Streamlit App)

---

## 📌 Overview
The **Healthcare Scribe & EMR System** is a Streamlit-based application designed to assist clinicians, students, and researchers with structured clinical documentation.  
It converts raw clinical dictation or transcription into a structured **SOAP note**, extracts medical entities, and stores patients + visit notes in an EMR-style SQLite database.

This project is ideal for:
- Healthcare informatics demonstrations  
- Machine learning / NLP coursework  
- EMR workflow simulations  
- Medical documentation training  

---

## 🚀 Features

### 🔊 **1. Transcription Input**
- Paste your own clinical dictation OR generate a built-in synthetic sample.
- Editable text area for reviewing or correcting the transcription.

### 🧱 **2. Automatic SOAP Note Structuring**
The system organizes clinical text into:
- **Subjective**  
- **Objective**  
- **Assessment**  
- **Plan**  

Uses rule-based keyword logic (not AI summarization).

### 🧠 **3. Medical Entity Extraction**
Automatically identifies:
- **Symptoms**
- **Diagnoses**
- **Medications** (including dosage patterns)
- **Procedures**
- **Vitals** (BP, HR, etc.)

### 👤 **4. Patient & Visit Management**
- Create patient records with name, DOB, and gender.
- Save visit notes tied to each patient.
- Stores structured SOAP output + raw transcription into a SQLite database.

### 📄 **5. Visit Overview / Demo Mode**
- Re-display the last processed note.
- Shows all structured fields + extracted entities.

### 📘 **6. “Learn More” Toggle Section**
- Built-in expandable panel describing the app’s functionality and workflow.

---

## 🛠️ How It Works

### 🔍 **Summarization Method**
This version **does NOT use AI or LLM summarization**.  
Instead, it relies on:
- Pattern matching  
- Keyword detection  
- Rule-based segmentation  

### 🧬 **Entity Extraction**
Regular expressions + curated medical term lists.

### 🗄️ **Database**
All patients and visit notes are stored in database.


### 🗺️ Roadmap / Future Enhancements ###
- AI-powered SOAP summarization (OpenAI, Claude, etc.)
- Speech-to-text (Whisper)
- Visit history + patient search
- Export to FHIR or HL7
- User authentication
- Public Streamlit Cloud deployment

### 📄 License ###
Licensed under the MIT License.
