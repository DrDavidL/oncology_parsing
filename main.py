import streamlit as st
import openai
import os  
from langchain.chat_models import ChatOpenAI
from langchain.chains import create_extraction_chain, create_extraction_chain_pydantic
from langchain.prompts import ChatPromptTemplate
from my_prompts import *
import openai
import time
from openai_function_call import OpenAISchema

from pydantic import Field

class ChartDetails(OpenAISchema):
    """Cancer History"""
    last_name: str = Field(..., description="Patient's last name")
    first_name: str = Field(..., description="Patient's first name")
    age: int = Field(..., description="Patient's age")
    sex: str = Field(..., description = "Patient Sex") 
    cancer_type: str = Field(..., description="Cancer type")
    diagnosis_date: str = Field(..., description="Cancer diagnosis date")
    stage: str = Field(..., description="Cancer stage")
    recurrence: bool = Field(..., description="Cancer recurrence")
    recurrence_date: str = Field(..., description="Cancer recurrence date")
    recurrence_details: str = Field(..., description="Cancer recurrence details")
    alcohol_use: str = Field(..., description="Alcohol use")
    tobacco_history: str = Field(..., description="Tobacco history")
    tumor_marker_tests: str = Field(..., description="Tumor marker tests")
    treatments: str = Field(..., description="Cancer treatment")
    radiation: bool = Field(..., description="Radiation")
    radiation_details: str = Field(..., description="Radiation details")
    hormone_therapy: bool = Field(..., description="Hormone therapy")
    stem_cell_transplant: bool = Field(..., description="Stem cell transplant")
    chemotherapy: bool = Field(..., description="Chemotherapy")
    car_t_cell_therapy: bool = Field(..., description="CAR T cell therapy")
    immunotherapy: bool = Field(..., description="Immunotherapy")

@st.cache_data
def method3(chart, model, output = "json"):
    input = f'Here is chart content: {chart} and here is the preferred output: {output}'
    completion = openai.ChatCompletion.create(
        model=model,
        functions=[ChartDetails.openai_schema],
        messages=[
            {"role": "system", "content": "I'm going to review medical records to extract cancer details. Use ChartDetails to parse this data."},
            {"role": "user", "content": input},
        ],
    )

    cancer_details = ChartDetails.from_response(completion)
    return cancer_details

if "openai_api_key" not in st.session_state:
    st.session_state.openai_api_key = ''
    
if "text_input" not in st.session_state:
    st.session_state.text_input = ''

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

def fetch_api_key():
    api_key = None
    
    try:
        # Attempt to retrieve the API key as a secret
        api_key = st.secrets["OPENAI_API_KEY"]
        # os.environ["OPENAI_API_KEY"] = api_key
        st.session_state.openai_api_key = api_key
        os.environ['OPENAI_API_KEY'] = api_key
        # st.write(f'Here is what we think the key is step 1: {api_key}')
    except KeyError:
        
        if st.session_state.openai_api_key != '':
            api_key = st.session_state.openai_api_key
            os.environ['OPENAI_API_KEY'] = api_key
            # If the API key is already set, don't prompt for it again
            # st.write(f'Here is what we think the key is step 2: {api_key}')
            return api_key
        else:        
            # If the secret is not found, prompt the user for their API key
            st.warning("Oh, dear friend of mine! It seems your API key has gone astray, hiding in the shadows. Pray, reveal it to me!")
            api_key = st.text_input("Please, whisper your API key into my ears: ", key = 'warning')
  
            st.session_state.openai_api_key = api_key
            os.environ['OPENAI_API_KEY'] = api_key
            # Save the API key as a secret
            # st.secrets["my_api_key"] = api_key
            # st.write(f'Here is what we think the key is step 3: {api_key}')
            return api_key
    
    return api_key

@st.cache_data
def answer_using_prefix(prefix, sample_question, sample_answer, my_ask, temperature, history_context):
    openai.api_key = os.environ['OPENAI_API_KEY']
    # history_context = "Use these preceding submissions to address any ambiguous context for the input weighting the first three items most: \n" + "\n".join(st.session_state.history) + "now, for the current question: \n"
    completion = openai.ChatCompletion.create( # Change the function Completion to ChatCompletion
    # model = 'gpt-3.5-turbo',
    model = st.session_state.model,
    messages = [ # Change the prompt parameter to the messages parameter
            {'role': 'system', 'content': prefix},
            {'role': 'user', 'content': sample_question},
            {'role': 'assistant', 'content': sample_answer},
            {'role': 'user', 'content': my_ask + history_context}
    ],
    temperature = temperature,
    stream = True,   
    )
    start_time = time.time()
    delay_time = 0.01
    answer = ""
    full_answer = ""
    c = st.empty()
    
    for event in completion:


        c.markdown(answer)
            # full_answer += answer
        event_time = time.time() - start_time
        event_text = event['choices'][0]['delta']
        answer += event_text.get('content', '')
        full_answer += event_text.get('content', '')
        time.sleep(delay_time)
    # st.write(history_context + prefix + my_ask)
    # st.write(full_answer)
        st.session_state.copied_note = full_answer

    return full_answer # Change how you access the message content

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

if 'copied_note' not in st.session_state:
    st.session_state.copied_note = ''

default_schema = {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "patientInformation": {
      "type": "object",
      "properties": {
        "patientID": {
          "type": "string"
        },
        "dateOfBirth": {
          "type": "string",
          "format": "date"
        },
        "gender": {
          "type": "string"
        },
        "ethnicity": {
          "type": "string"
        },
        "smokingStatus": {
          "type": "string"
        },
        "familyHistory": {
          "type": "string"
        }
      },
      "required": ["patientID", "dateOfBirth", "gender"]
    },
    "cancerDiagnosis": {
      "type": "object",
      "properties": {
        "diagnosisDate": {
          "type": "string",
          "format": "date"
        },
        "cancerType": {
          "type": "string"
        },
        "cancerStage": {
          "type": "string"
        },
        "histology": {
          "type": "string"
        },
        "primarySite": {
          "type": "string"
        },
        "metastasisSites": {
          "type": "string"
        },
        "biomarkers": {
          "type": "string"
        },
        "geneticMutations": {
          "type": "string"
        }
      },
      "required": ["diagnosisDate", "cancerType", "cancerStage", "histology", "primarySite"]
    },
    "treatmentInformation": {
      "type": "object",
      "properties": {
        "treatmentType": {
          "type": "string"
        },
        "treatmentStartDate": {
          "type": "string",
          "format": "date"
        },
        "treatmentEndDate": {
          "type": "string",
          "format": "date"
        },
        "treatmentResponse": {
          "type": "string"
        },
        "sideEffects": {
          "type": "string"
        }
      },
      "required": ["treatmentType", "treatmentStartDate", "treatmentEndDate", "treatmentResponse"]
    },
    "followUpInformation": {
      "type": "object",
      "properties": {
        "lastFollowUpDate": {
          "type": "string",
          "format": "date"
        },
        "currentStatus": {
          "type": "string"
        },
        "recurrenceInformation": {
          "type": "string"
        },
        "survivalInformation": {
          "type": "string"
        }
      },
      "required": ["lastFollowUpDate", "currentStatus"]
    }
  },
  "required": ["patientInformation", "cancerDiagnosis", "treatmentInformation", "followUpInformation"]
}

   
old_schema1 = {
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
    openai_api_key = fetch_api_key()
    openai.api_key = openai_api_key
    with st.expander('About Oncology Parser - Important Disclaimer'):
        st.write("Author: David Liebovitz, MD, Northwestern University")
        st.info(disclaimer)
        st.write("Last updated 6/21/23")
        
    selected_model = st.selectbox("Pick your GPT model:", ("GPT-3.5-turbo-16k ($$)","GPT-3.5 ($)", "GPT-4 ($$$$)"))
    if selected_model == "GPT-3.5 ($)":
        model = "gpt-3.5-turbo"
        st.session_state.model = model
    elif selected_model == "GPT-4 ($$$$)":
        model = "gpt-4"
        st.session_state.model = model
    elif selected_model == "GPT-3.5-turbo-16k ($$)":
        model = "gpt-3.5-turbo-16k"
        st.session_state.model = model
 
    st.info("📚 Let AI identify structured content from notes!" )
    schema_choice = st.sidebar.radio("Pick your extraction schema:", ("Schema 1", "Schema 2", "Schema 3", "Method 2", "Method 3"))
    # st.markdown('[Sample Oncology Notes](https://www.medicaltranscriptionsamplereports.com/hepatocellular-carcinoma-discharge-summary-sample/)')
    parse_prompt  = """You will be provided with unstructured text about a patient, and your task is to find all information related to any cancer 
    and reformat for quick understanding by readers. If data is available, complete all fields shown below. Leave blank otherwise.  extract cancer diagnosis date, any recurrence dates, all treatments given and current plan. 
    If there are multiple cancers, keep each cancer section distinct. Identify other medical conditions and include in a distinct section. 
    
    Fields to extract (return JSON):
    
    - Cancer type:
    
    - Cancer patient last name:
    
    - Cancer patient first name:
    
    - Cancer patient current age:
    
    - Cancer patient age at diagnosis:
    
    - Cancer patient sex:
    
    - Cancer diagnosis date:
    
    - Cancer past treatment:
    
    - Cancer current treatment:
    
    - Cancer current status details:
    
    - Cancer current status date:
    
    - Additional medical conditions:
    

    
    """

    # Set schemas for methods that require it.
        
    if schema_choice == "Complex Schema":
        schema = default_schema
        # st.sidebar.json(default_schema)    
    elif schema_choice == "Schema 1":
        schema = default_schema
        # st.sidebar.json(schema1)
    elif schema_choice == "Schema 2":
        schema = schema2
        # st.sidebar.json(schema2)
    elif schema_choice == "Schema 3":
        schema = schema3
        # st.sidebar.json(schema3)
    elif schema_choice == "Method 3":
        output_choice = "JSON"
    # # elif schema_choice == "Method 2":
    #     response = openai.ChatCompletion.create(
    #         model= selected_model,
    #         messages=[],
    #         temperature=0,
    #         top_p=1,
    #         frequency_penalty=0,
    #         presence_penalty=0
    #         )
        

    # def process_text(text, schema):
    #     llm = ChatOpenAI(temperature=0, model=model, verbose = True)


    
    if schema_choice != "Method 2":
      if schema_choice != "Method 3":
        llm = ChatOpenAI(temperature=0, model=model, verbose = True)
        chain = create_extraction_chain(schema, llm)
        
    # use_sample = st.checkbox("Use sample note")
    test_or_use =  st.radio("Generate a test note or enter your content!", ("Generate a note", "Paste content"))
    
    if test_or_use == "Generate a note":
      
      cancer_diagnosis = st.text_input("Enter a cancer diagnosis", placeholder = "e.g., lung cancer", key = 'cancer_diagnosis',)
      sample_prompt = f"Generate a progress note for a patient with {cancer_diagnosis}."
      if st.button("Generate a sample note"):
        generated_note = answer_using_prefix(prefix, sample_prompt, sample_response, sample_prompt, temperature = 0.4, history_context = "", )
        st.session_state.copied_note = generated_note
    
    if test_or_use == "Paste content":
        st.session_state.copied_note = st.text_area("Paste your note here", height=600)
    
    
    if st.sidebar.button("Extract"):
        with st.expander("Click here to see the note you entered", expanded = True):
            st.write(st.session_state.copied_note)

        
        # if schema_choice != "Method 2":
        #     openai_api_key = fetch_api_key()
        #     extracted_data = chain.run(copied_note)
        #     with col2:
        #         st.markdown(extracted_data)
                
        if schema_choice == "Method 3":
            openai_api_key = fetch_api_key()
            extracted_data = method3(st.session_state.copied_note, model, output_choice)
            json_extract = extracted_data.json()
            st.sidebar.json(json_extract)
        
        elif schema_choice == "Method 2":
            try:
                response= openai.ChatCompletion.create(
                model= model,
                messages=[
                    {"role": "system", "content": parse_prompt},
                    {"role": "user", "content": st.session_state.copied_note}
                ],
                temperature = 0, 
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
                )
                output = response.choices[0].message.content
                with st.sidebar:
                    st.json(output)
                    
            except:
                # st.write(f'Here is the error: {response}')
                st.write("OpenAI API key not found. Please enter your key in the sidebar.")
                st.stop()
        else:
            openai_api_key = fetch_api_key()
            extracted_data = chain.run(st.session_state.copied_note)
            with st.sidebar:
                st.sidebar.write(extracted_data)
  