import streamlit as st
import openai
import os  
from langchain.chat_models import ChatOpenAI
from langchain.chains import create_extraction_chain, create_extraction_chain_pydantic
from langchain.prompts import ChatPromptTemplate

def is_valid_api_key(api_key):
    openai.api_key = api_key

    try:
        # Send a test request to the OpenAI API
        response = openai.Completion.create(model="text-davinci-003",                     
                    prompt="Hello world")['choices'][0]['text']
        return True
    except Exception:
        pass

    return False

def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.write("*Please contact David Liebovitz, MD if you need an updated password for access.*")
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct.
        return True

if check_password():

    if 'history' not in st.session_state:
                st.session_state.history = []

    if 'output_history' not in st.session_state:
                st.session_state.output_history = []
                
    if 'mcq_history' not in st.session_state:
                st.session_state.mcq_history = []

    # API_O = st.secrets["OPENAI_API_KEY"]
    # Define Streamlit app layout

    st.set_page_config(page_title='Oncology Parser Assistant', layout = 'centered', page_icon = ':stethoscope:', initial_sidebar_state = 'auto')
    st.title("Oncology Parser Assistant")
    st.write("ALPHA version 0.2")
    disclaimer = """**Disclaimer:** This is a tool to assist chart abstraction for cancer related diagnoses. \n 
2. This tool is not a real doctor. \n    
3. You will not take any medical action based on the output of this tool. \n   
    """
    with st.expander('About Oncology Parser - Important Disclaimer'):
        st.write("Author: David Liebovitz, MD, Northwestern University")
        st.info(disclaimer)
        st.write("Last updated 6/21/23")
    try:  
        openai.api_key = st.secrets['OPENAI_API_KEY']
        st.write("*API key active - ready to respond!*")
    except:        
        st.warning("API key not found as an environmental variable.")
        api_key = st.text_input("Enter your OpenAI API key:")

        if st.button("Save"):
            if is_valid_api_key(api_key):
                os.environ["OPENAI_API_KEY"] = api_key
                st.success("API key saved as an environmental variable!")
            else:
                st.error("Invalid API key. Please enter a valid API key.")


    st.info("📚 Let AI identify structured content from notes!" )
    
    schema = {
    "properties": {
        "patient_name": {"type": "string"},
        "age_at_visit": {"type": "integer"},
        "cancer_type": {"type": "string"},
        "age_at_diagnosis": {"type": "integer"},
        "treatment_history": {"type": "array"},
        "recurrence_status": {"type": "boolean"},
        "age_at_recurrence": {"type": "integer"},
        "recurrence_treatment": {"type": "array"},
    },
    "required": ["patient_name", "age_at_visit", "cancer_type", "age_at_diagnosis"],
    }
    
    schema2 = {
    "properties": {
        "patient_last_name": {"type": "string"},
        "patient_first_name": {"type": "string"},
        "age_at_cancer_diagnosis": {"type": "integer"},
        "age_at_cancer_recurrence": {"type": "integer"},
        "age_at_visit": {"type": "integer"},
        "specific_cancer_type": {"type": "string"},
        "cancer_stage_at_diagnosis": {"type": "string"},        
        "cancer_treatment_history": {"type": "string"},
        "cancer_treatment_current": {"type": "string"},
        "cancer_recurrence_status": {"type": "string"},   
        "cancer_recurrence_date": {"type": "string"},     
        "cancer_recurrence_treatment": {"type": "string"},
        "cancer_current_status": {"type": "string"},
        "cancer_current_status_date": {"type": "string"},
        "cancer_current_status_details": {"type": "string"},        
    },
    "required": ["patient_last_name", "patient_first_name"],
    }
    
    schema3 = {
    "properties": {
        "patient_last_name": {"type": "string"},
        "patient_first_name": {"type": "string"},
        "patient_age": {"type": "integer"},
        "patient_sex": {"type": "string"},
        "race": {"type": "string"},
        "cancer_primary_site": {"type": "string"},
        "laterality": {"type": "string"},
        "histologic_type": {"type": "string"},
        "behavior_code_ICD_O3": {"type": "string"},
        "grade": {"type": "string"},
        "diagnosis_confirmation": {"type": "string"},
        "diagnosis_date": {"type": "string"}, # ISO date format (yyyy-mm-dd) is recommended
        "sequence_number": {"type": "string"},
        "tumor_size": {"type": "integer"},
        "extension": {"type": "string"},
        "lymph_nodes": {"type": "string"},
        "prognostic_factors": {"type": "string"},
        "metastases": {"type": "string"},
        "surgery_of_primary_site": {"type": "string"},
        "surgery_to_other_regions": {"type": "string"},
        "treatment_start_date": {"type": "string"}, # ISO date format (yyyy-mm-dd) is recommended
        "treatment_end_date": {"type": "string"}, # ISO date format (yyyy-mm-dd) is recommended
        "radiation": {"type": "string"},
        "chemotherapy": {"type": "string"},
        "immunotherapy": {"type": "string"},
        "hormone_therapy": {"type": "string"},
        "stem_cell_transplant": {"type": "string"},
        "tumor_marker_tests": {"type": "string"},
        "patient_survival_time": {"type": "integer"},
        "cancer_status_at_last_followup": {"type": "string"},
        "last_followup_date": {"type": "string"}, # ISO date format (yyyy-mm-dd) is recommended
        "cause_of_death": {"type": "string"},
        "tobacco_history": {"type": "string"},
        "alcohol_use": {"type": "string"},
    },
    "required": ["patient_last_name", "patient_first_name"],
    }




    
    if openai.api_key:
        llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo-0613")
        chain = create_extraction_chain(schema3, llm)
    
    copied_note = st.text_area("Paste your note here", height=600)
    
    if st.button("Extract"):
        extracted_data = chain.run(copied_note)
        st.write(extracted_data)
       
    
 