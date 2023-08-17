import streamlit as st
import openai
import os  
# from langchain.chat_models import ChatOpenAI
# from langchain.chains import create_extraction_chain, create_extraction_chain_pydantic
# from langchain.prompts import ChatPromptTemplate

import openai
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
def parse(chart, model, output):
    input = f'Here is chart content: {chart} and here is the preferred output: {output}'
    completion = openai.ChatCompletion.create(
        model=model,
        functions=[ChartDetails.openai_schema],
        messages=[
            {"role": "system", "content": "Carefully for accuracy, extract cancer details from medical records. Use ChartDetails to parse this data."},
            {"role": "user", "content": chart},
        ],
    )

    cancer_details = ChartDetails.from_response(completion)
    
    return cancer_details

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
    st.write("Last updated 8/16/23")
    
if check_password():
    selected_model = st.selectbox("Pick your GPT model:", ("GPT-3.5 ($)", "GPT-3.5-turbo-16k ($$)", "GPT-4 ($$$$)"))
    if selected_model == "GPT-3.5 ($)":
        model = "gpt-3.5-turbo"
    elif selected_model == "GPT-3.5-turbo-16k ($$)":
        model = "gpt-3.5-turbo-16k"
    elif selected_model == "GPT-4 ($$$$)":
        model = "gpt-4"