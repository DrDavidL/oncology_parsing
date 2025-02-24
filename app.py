import streamlit as st
import json
import pandas as pd
from datetime import datetime
import anthropic
import os
from io import StringIO

# Initialize Anthropic client - you'll need to set your API key
# Either set as environment variable or input directly (less secure)
api_key = os.environ.get("ANTHROPIC_API_KEY", "")
if not api_key:
    if 'ANTHROPIC_API_KEY' not in st.session_state:
        st.session_state.ANTHROPIC_API_KEY = ""
    
    if not st.session_state.ANTHROPIC_API_KEY:
        api_key = st.text_input("Enter your Anthropic API Key:", type="password")
        if api_key:
            st.session_state.ANTHROPIC_API_KEY = api_key
    else:
        api_key = st.session_state.ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=api_key) if api_key else None

def generate_progress_note(patient_data):
    """Use Claude to generate an oncology progress note based on minimal patient data"""
    
    prompt = f"""
    You are an expert oncologist. Create a detailed oncology progress note based on the following patient information:
    
    Patient Name: {patient_data['name']}
    Date of Birth: {patient_data['dob']}
    MRN: {patient_data['mrn']}
    Cancer Type: {patient_data['cancer_type']}
    Stage: {patient_data['stage']}
    Current Treatment: {patient_data['current_treatment']}
    Chief Complaint: {patient_data['chief_complaint']}
    
    Additional context: {patient_data['additional_context']}
    
    Format the note with standard oncology progress note sections including:
    - Chief Complaint
    - History of Present Illness
    - Cancer Diagnosis (including histology details)
    - Cancer-Related Procedures
    - Medications
    - Review of Systems
    - Physical Examination
    - Laboratory and Imaging Studies
    - Assessment
    - Plan
    - Next Appointment
    
    Include realistic clinical details that would be appropriate for this patient's condition.
    Use medical terminology appropriate for an oncology note.
    """
    
    try:
        response = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=4000,
            temperature=0.2,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.content[0].text
    except Exception as e:
        return f"Error generating progress note: {str(e)}"

def extract_mcode_elements(progress_note):
    """Use Claude to extract structured mCODE elements from the progress note"""
    
    prompt = f"""
    You are an expert in oncology data standardization using the mCODE (minimal Common Oncology Data Elements) framework.
    
    Extract structured mCODE data elements from the following oncology progress note. Format your response as a JSON object with the following categories:
    
    1. Patient
    2. PrimaryCancerCondition (include conditionName, histologyMorphologyBehavior, clinicalStatus, stage, dateOfDiagnosis)
    3. CancerRelatedProcedures (list all procedures with dates when available)
    4. CancerRelatedMedications (list all cancer medications with dosages)
    5. TumorMarkers (extract any tumor marker values mentioned)
    6. VisitInformation (visitDate, reasonForVisit, nextAppointment)
    7. TreatmentPlan (treatmentIntent, treatmentSummary)
    
    Progress Note:
    {progress_note}
    
    Return ONLY the JSON object with no additional text or explanation.
    """
    
    try:
        response = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=2000,
            temperature=0.1,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Extract JSON from the response
        json_text = response.content[0].text
        
        # Handle potential markdown code block formatting
        if "```json" in json_text:
            json_text = json_text.split("```json")[1].split("```")[0].strip()
        elif "```" in json_text:
            json_text = json_text.split("```")[1].split("```")[0].strip()
            
        mcode_data = json.loads(json_text)
        return mcode_data
    except Exception as e:
        return {"error": f"Error extracting mCODE elements: {str(e)}"}

def check_password():
    """Returns `True` if the user entered the correct password."""
    
    # Check if authentication has already been completed successfully
    if st.session_state.get("password_correct", False):
        return True
        
    # Define password validation function
    def validate_password():
        """Validates the entered password against stored secret."""
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            # Clear password from session state for security
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False
    
    # Display password input field
    st.text_input(
        "Password", 
        type="password", 
        on_change=validate_password, 
        key="password"
    )
    
    # Show error message if password was incorrect
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("😕 Password incorrect")
    
    # Show contact information for password assistance
    st.write("*Please contact David Liebovitz, MD if you need an updated password for access.*")
    
    # Return authentication status
    return st.session_state.get("password_correct", False)

def main():
    st.title("AI-Powered Oncology Progress Note Generator with mCODE Integration")
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Input Patient Data", "Review Progress Note", "Review mCODE Data", "Export JSON"])
    
    if check_password():
        
        # Initialize session state
        if 'patient_data' not in st.session_state:
            st.session_state.patient_data = {
                'name': '',
                'dob': '',
                'mrn': '',
                'cancer_type': '',
                'stage': '',
                'current_treatment': '',
                'chief_complaint': '',
                'additional_context': ''
            }
        
        if 'progress_note' not in st.session_state:
            st.session_state.progress_note = ""
            
        if 'mcode_data' not in st.session_state:
            st.session_state.mcode_data = {}
            
        if 'approved_mcode_data' not in st.session_state:
            st.session_state.approved_mcode_data = {}
        
        # Page 1: Input Patient Data
        if page == "Input Patient Data":
            st.header("Enter Minimal Patient Information")
            st.info("Claude AI will generate a complete oncology progress note from these key details.")
            
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.patient_data['name'] = st.text_input("Patient Name", st.session_state.patient_data['name'])
                st.session_state.patient_data['dob'] = st.text_input("Date of Birth", st.session_state.patient_data['dob'])
                st.session_state.patient_data['mrn'] = st.text_input("Medical Record Number", st.session_state.patient_data['mrn'])
            
            with col2:
                st.session_state.patient_data['cancer_type'] = st.text_input("Cancer Type", st.session_state.patient_data['cancer_type'])
                st.session_state.patient_data['stage'] = st.text_input("Clinical Stage", st.session_state.patient_data['stage'])
                st.session_state.patient_data['current_treatment'] = st.text_input("Current Treatment", st.session_state.patient_data['current_treatment'])
            
            st.session_state.patient_data['chief_complaint'] = st.text_area("Chief Complaint", st.session_state.patient_data['chief_complaint'])
            st.session_state.patient_data['additional_context'] = st.text_area("Additional Context (optional)", 
                                                                            st.session_state.patient_data['additional_context'],
                                                                            help="Add any additional information that should be included in the note")
            
            if st.button("Generate Progress Note with Claude AI"):
                with st.spinner("Claude AI is generating your oncology progress note..."):
                    if not client:
                        st.error("Please enter a valid Anthropic API key to continue.")
                    else:
                        st.session_state.progress_note = generate_progress_note(st.session_state.patient_data)
                        st.success("Progress note generated! Navigate to 'Review Progress Note' to view.")
        
        # Page 2: Review Progress Note
        elif page == "Review Progress Note":
            st.header("Generated Oncology Progress Note")
            
            if st.session_state.progress_note:
                st.markdown(st.session_state.progress_note)
                
                if st.button("Edit Patient Data"):
                    st.session_state.current_page = "Input Patient Data"
                    st.experimental_rerun()
                    
                if st.button("Extract mCODE Elements"):
                    with st.spinner("Claude AI is extracting mCODE elements..."):
                        if not client:
                            st.error("Please enter a valid Anthropic API key to continue.")
                        else:
                            st.session_state.mcode_data = extract_mcode_elements(st.session_state.progress_note)
                            st.success("mCODE elements extracted! Navigate to 'Review mCODE Data' to view.")
            else:
                st.warning("No progress note has been generated yet. Please input patient data first.")
        
        # Page 3: Review mCODE Data
        elif page == "Review mCODE Data":
            st.header("AI-Extracted mCODE Data Elements")
            
            if st.session_state.mcode_data:
                if "error" in st.session_state.mcode_data:
                    st.error(st.session_state.mcode_data["error"])
                else:
                    st.info("Review and edit the extracted mCODE elements below:")
                    
                    # Display and allow editing of each mCODE category
                    categories = [
                        "Patient", 
                        "PrimaryCancerCondition", 
                        "CancerRelatedProcedures", 
                        "CancerRelatedMedications",
                        "TumorMarkers", 
                        "VisitInformation", 
                        "TreatmentPlan"
                    ]
                    
                    edited_data = {}
                    
                    for category in categories:
                        st.subheader(category)
                        if category in st.session_state.mcode_data:
                            data = st.session_state.mcode_data[category]
                            
                            # Handle list data differently from dictionary data
                            if isinstance(data, list):
                                if data:
                                    df = pd.DataFrame(data)
                                    edited_df = st.data_editor(df, key=f"edit_{category}")
                                    edited_data[category] = edited_df.to_dict('records')
                                else:
                                    st.info(f"No {category} data found.")
                                    edited_data[category] = []
                            else:
                                df = pd.DataFrame([data])
                                edited_df = st.data_editor(df, key=f"edit_{category}")
                                edited_data[category] = edited_df.iloc[0].to_dict()
                        else:
                            st.info(f"No {category} data found.")
                            edited_data[category] = {} if category not in ["CancerRelatedProcedures", "CancerRelatedMedications", "TumorMarkers"] else []
                    
                    if st.button("Approve mCODE Data"):
                        st.session_state.approved_mcode_data = edited_data
                        st.success("mCODE data approved! Navigate to 'Export JSON' to download the data.")
            else:
                st.warning("No mCODE data has been extracted yet. Please generate a progress note and extract mCODE elements first.")
        
        # Page 4: Export JSON
        elif page == "Export JSON":
            st.header("Export Approved mCODE Data as JSON")
            
            if st.session_state.approved_mcode_data:
                # Display the approved mCODE data
                st.json(st.session_state.approved_mcode_data)
                
                # Create a download button for the JSON file
                json_str = json.dumps(st.session_state.approved_mcode_data, indent=2)
                
                patient_name = st.session_state.patient_data['name'].replace(" ", "_")
                visit_date = datetime.now().strftime("%Y%m%d")
                filename = f"{patient_name}_mCODE_{visit_date}.json"
                
                st.download_button(
                    label="Download JSON",
                    data=json_str,
                    file_name=filename,
                    mime="application/json"
                )
                
                st.success("The structured mCODE data is now ready for integration with your electronic health record system or cancer registry.")
            else:
                st.warning("No approved mCODE data available. Please review and approve the extracted data first.")

if __name__ == "__main__":
    main()