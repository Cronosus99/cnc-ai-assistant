"""
CNC AI Assistant
================
A Streamlit web application powered by a fine-tuned GPT-4o Mini model
trained on Fanuc-style CNC G-code explanation, debugging, and manufacturing
data analysis tasks.
 
Author: Kevin
"""

# Import necessary libraries
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

# Getting key secret variables
# Support both local .env and Streamlit Cloud st.secrets
def get_secret(key: str) -> str | None:
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError):
        return os.getenv(key)
 
api_key    = get_secret("OPENAI_KEY")
model_name = get_secret("MODEL_NAME")

# Create OpenAI client
client = OpenAI(api_key=api_key)

# System prompts - one per tab, matching fine-tuning task categories
EXPLAIN_SYSTEM = """You are an expert CNC machinist and Fanuc G-code instructor.
When given a G-code program, explain each line clearly and concisely in plain English.
Cover what each command does, why it matters operationally, and any safety considerations.
Format your response with the original line followed by its explanation."""
 
DEBUG_SYSTEM = """You are an expert CNC programmer specializing in Fanuc G-code safety and correctness.
When given a G-code program, identify ALL problems — including safety hazards, missing commands,
incorrect sequencing, and best-practice violations. Then provide a corrected version of the full program.
 
Format your response exactly like this:
Problems Found:
1. [problem description]
2. [problem description]
...
 
Suggested Fix:
[corrected G-code program with inline comments]"""
 
ANALYZE_SYSTEM = """You are a manufacturing process engineer with expertise in CNC data analysis.
When given tabular manufacturing data (CSV format), analyze it for trends, anomalies, correlations,
and actionable insights. Focus on tool wear progression, cycle time efficiency, and error patterns.
Provide specific, quantitative observations where possible and practical recommendations."""

# Helpers that are default prompts as examples or to test the model
PLACEHOLDER_GCODE = """\
G21           ; metric mode
G90           ; absolute positioning
T02 M06       ; tool change to tool 2
G01 X50 Y50 F200
M03 S800      ; spindle start
M30           ; program end"""
 
PLACEHOLDER_FLAWED = """\
G21
G90
T01 M06
G01 Z-5 F100
G01 X50 Y50 F200
M03 S1000
M30"""
 
PLACEHOLDER_DATA = """\
Tool_Wear,Cycle_Time,Errors
95,8.4,7
88,7.8,6
72,6.9,3
65,6.5,2
58,6.2,1
45,5.8,0
30,5.5,0"""

# Function that takes system prompt and user input to the fine-tuned model and returns a generator using yield
def stream_response(system_prompt: str, user_content: str):
    """Yield streamed tokens from the fine-tuned model."""
    stream = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system",  "content": system_prompt},
            {"role": "user",    "content": user_content},
        ],
        stream=True,
        temperature=0.2,
        max_tokens=1024,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
        
# Page config
st.set_page_config(
    page_title="CNC AI Assistant",
    page_icon="⚙️",
    layout="wide",
)

# Sidebar
with st.sidebar:
    st.markdown("## ⚙️ CNC AI Assistant")
    st.markdown("---")
    st.markdown(
        "This app is powered by a **fine-tuned GPT-4o Mini** model trained on "
        "Fanuc-style CNC G-code tasks across three categories:\n\n"
        "- G-code explanation\n"
        "- Flaw detection & correction\n"
        "- Manufacturing data analysis"
    )
    st.markdown("---")
    st.markdown(f"**Model:** `{model_name}`")
    st.markdown("**Dialect:** Fanuc")
    st.markdown("**Training records:** 56 JSONL examples")
    st.markdown("---")
    st.caption("Built with Streamlit + OpenAI Fine-Tuning")

# Title   
st.title("⚙️ CNC AI Assistant")
st.markdown(
    "An AI assistant for CNC machinists — powered by a fine-tuned model trained on "
    "Fanuc G-code explanation, debugging, and manufacturing data analysis."
)
st.markdown("---")

# Tabs
tab1, tab2, tab3 = st.tabs([
    "🔍 Explain G-Code",
    "🐛 Debug G-Code",
    "📊 Analyze Manufacturing Data",
])

# Tab 1: Explain G-Code
with tab1:
    st.subheader("Explain G-Code")
    st.markdown(
        "Paste a Fanuc G-code program below. The model will explain each line "
        "in plain English, including safety considerations."
    )
 
    gcode_input = st.text_area(
        "G-Code Program",
        value=PLACEHOLDER_GCODE,
        height=200,
        placeholder="Paste your G-code here...",
        key="explain_input",
    )
 
    if st.button("Explain G-Code", type="primary", key="explain_btn"):
        if not gcode_input.strip():
            st.warning("Please paste a G-code program first.")
        else:
            with st.spinner("Analyzing..."):
                st.markdown("### Explanation")
                response_box = st.empty()
                full_text = ""
                for token in stream_response(EXPLAIN_SYSTEM, gcode_input):
                    full_text += token
                    response_box.markdown(full_text)
                
 
# Tab 2: Debug G-Code
with tab2:
    st.subheader("Debug G-Code")
    st.markdown(
        "Paste a G-code program that may contain errors, unsafe sequences, or "
        "missing commands. The model will identify all problems and provide a corrected version."
    )
 
    col1, col2 = st.columns(2)
 
    with col1:
        st.markdown("**Input — Flawed Program**")
        flawed_input = st.text_area(
            "Flawed G-Code",
            value=PLACEHOLDER_FLAWED,
            height=250,
            label_visibility="collapsed",
            key="debug_input",
        )
        debug_btn = st.button("Debug G-Code", type="primary", key="debug_btn")
 
    with col2:
        st.markdown("**Output — Diagnosis & Fix**")
        debug_output = st.empty()
 
    if debug_btn:
        if not flawed_input.strip():
            st.warning("Please paste a G-code program first.")
        else:
            with debug_output:
                with st.spinner("Diagnosing..."):
                    full_text = ""
                    for token in stream_response(DEBUG_SYSTEM, flawed_input):
                        full_text += token
                        debug_output.markdown(full_text)
 
 
# Tab 3: Analyze Manufacturing Data
 
with tab3:
    st.subheader("Analyze Manufacturing Data")
    st.markdown(
        "Paste CSV-formatted manufacturing data (tool wear, cycle times, error counts, etc.). "
        "The model will surface trends, correlations, and actionable recommendations."
    )
 
    data_input = st.text_area(
        "Manufacturing Data (CSV)",
        value=PLACEHOLDER_DATA,
        height=220,
        key="analyze_input",
    )
 
    if st.button("Analyze Data", type="primary", key="analyze_btn"):
        if not data_input.strip():
            st.warning("Please paste manufacturing data first.")
        else:
            with st.spinner("Analyzing data..."):
                st.markdown("### Analysis")
                analysis_output = st.empty()
                full_text = ""
                for token in stream_response(ANALYZE_SYSTEM, data_input):
                    full_text += token
                    analysis_output.markdown(full_text)