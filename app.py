import streamlit as st
from google import genai
from google.genai import types
import tempfile
import json
import os
import re
import time
import random

# --- Page Configuration ---
st.set_page_config(
    page_title="ThesisLab AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Inject Custom CSS for UI Aesthetics ---
custom_css = """
<style>
    /* Dark Theme Background */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
        color: #f8fafc;
    }
    
    /* Header Container Styling */
    .hero-container {
        padding: 1.5rem 2rem;
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }
    
    /* Custom Metric Badges */
    .metric-card {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(108, 92, 231, 0.3);
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
    }
    .metric-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #a78bfa;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #94a3b8;
    }
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: rgba(30, 41, 59, 0.5);
        border-radius: 8px 8px 0px 0px;
        padding: 10px 20px;
        color: #94a3b8;
        border: none;
    }
    .stTabs [aria-selected="true"] {
        background-color: #6c5ce7 !important;
        color: #ffffff !important;
        font-weight: bold;
    }
    
    /* Custom Expanders for Flashcards */
    .streamlit-expanderHeader {
        background-color: rgba(30, 41, 59, 0.8) !important;
        border-radius: 8px !important;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- Hero Section ---
st.markdown(
    """
    <div class="hero-container">
        <h1 style="margin:0; font-size: 2.4rem; color: #ffffff;">🎓 ThesisLab AI</h1>
        <p style="margin:5px 0 0 0; color: #cbd5e1; font-size: 1.1rem;">
            Turn static academic papers into interactive labs, executable python notebooks, and critical review strategies.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# 1. API Key Setup
api_key = st.sidebar.text_input("Gemini API Key", type="password") or os.getenv("GEMINI_API_KEY")

if not api_key:
    st.info("💡 Enter your Gemini API Key in the sidebar to begin processing papers.")
    st.stop()

client = genai.Client(api_key=api_key)

# Robust Fallback Engine
def safe_generate(contents, prompt_text, config=None):
    models_to_try = ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.1-flash-lite"]
    max_retries = 3

    for model_name in models_to_try:
        for attempt in range(max_retries):
            try:
                return client.models.generate_content(
                    model=model_name,
                    contents=[contents, prompt_text],
                    config=config
                )
            except Exception as e:
                err_msg = str(e)
                if "503" in err_msg or "UNAVAILABLE" in err_msg or "high demand" in err_msg.lower():
                    delay = (2 ** attempt) + random.uniform(0.5, 1.5)
                    st.warning(f"Server busy on {model_name}. Retrying in {delay:.1f}s...")
                    time.sleep(delay)
                    continue
                elif "404" in err_msg or "NOT_FOUND" in err_msg:
                    break
                else:
                    raise e
    st.error("Gemini services are temporarily busy. Please try again.")
    st.stop()

def clean_code_block(text):
    match = re.search(r"```python\n(.*?)\n```", text, re.DOTALL)
    if match:
        return match.group(1)
    return text.replace("```python", "").replace("```", "").strip()

# Sidebar Info Dashboard
st.sidebar.markdown("### ⚙️ Workspace Settings")
uploaded_file = st.sidebar.file_uploader("Upload Academic Paper (PDF)", type=["pdf"])

if uploaded_file:
    if "pdf_file" not in st.session_state:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.read())
            temp_path = tmp_file.name

        with st.spinner("Processing PDF context with Gemini..."):
            pdf_file = client.files.upload(file=temp_path)
            st.session_state["pdf_file"] = pdf_file
            st.sidebar.success("PDF ready for processing!")

    # Top Analytics Banner
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.markdown('<div class="metric-card"><div class="metric-value">1M+</div><div class="metric-label">Token Context Window</div></div>', unsafe_allow_html=True)
    with col_m2:
        st.markdown('<div class="metric-card"><div class="metric-value">Multimodal</div><div class="metric-label">Parsing Engine</div></div>', unsafe_allow_html=True)
    with col_m3:
        st.markdown('<div class="metric-card"><div class="metric-value">Live Code</div><div class="metric-label">Execution Sandbox</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Main Application Navigation Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Executive Breakdown", 
        "🎴 Study Deck", 
        "🐍 Interactive Code Lab",
        "🔬 Academic Defense & Research QA"
    ])

    # --- TAB 1: EXECUTIVE BREAKDOWN ---
    with tab1:
        st.subheader("Paper Overview & Core Findings")
        if st.button("Generate Executive Summary", type="primary"):
            with st.spinner("Extracting methodology and insights..."):
                prompt = (
                    "Provide a clear breakdown of this paper. "
                    "Use markdown with headers for: "
                    "1. Core Objective & Novelty "
                    "2. Key Methodology & Formulas/Models Used "
                    "3. Main Results & Practical Applications."
                )
                response = safe_generate(st.session_state["pdf_file"], prompt)
                st.markdown(response.text)

    # --- TAB 2: FLASHCARDS ---
    with tab2:
        st.subheader("Interactive Concepts Deck")
        if st.button("Generate Study Cards", type="primary"):
            with st.spinner("Parsing key terms into JSON..."):
                prompt = "Extract 6 key technical terms or concepts from this paper with clear definitions."
                json_config = types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema={
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "concept": {"type": "STRING"},
                                "definition": {"type": "STRING"}
                            },
                            "required": ["concept", "definition"]
                        }
                    }
                )
                response = safe_generate(st.session_state["pdf_file"], prompt, config=json_config)
                try:
                    cards = json.loads(response.text)
                    st.session_state["cards"] = cards
                except Exception:
                    st.error("Failed to format cards. Retry.")

        if "cards" in st.session_state:
            cols = st.columns(2)
            for idx, item in enumerate(st.session_state["cards"]):
                col = cols[idx % 2]
                with col:
                    with st.expander(f"💡 {item['concept']}"):
                        st.write(item['definition'])

    # --- TAB 3: CODE LAB ---
    with tab3:
        st.subheader("Simulation & Data Visualization Playground")
        user_prompt = st.text_input("Prompt the AI to build or plot:", placeholder="e.g., Plot selective ion removal efficiency of Na+ vs Mg2+ using matplotlib.")
        
        if user_prompt and st.button("Generate Live Plot", type="primary"):
            with st.spinner("Building custom executable Python visualization..."):
                code_instruction = (
                    f"Based on the paper context, write standalone executable Python code for: '{user_prompt}'. "
                    f"1. Generate realistic data fitting the paper.\n"
                    f"2. Store a matplotlib or plotly figure in a variable named `fig`.\n"
                    f"3. Return ONLY Python code inside ```python ```."
                )
                response = safe_generate(st.session_state["pdf_file"], code_instruction)
                executable_code = clean_code_block(response.text)
                
                st.markdown("##### Generated Source Code")
                st.code(executable_code, language="python")

                st.markdown("##### Dynamic Render Output")
                try:
                    exec_globals = {}
                    exec(executable_code, exec_globals)
                    if "fig" in exec_globals:
                        fig_obj = exec_globals["fig"]
                        if hasattr(fig_obj, "write_html"):
                            st.plotly_chart(fig_obj, use_container_width=True)
                        else:
                            st.pyplot(fig_obj)
                except Exception as err:
                    st.error(f"Execution Output Error: {err}")

    # --- TAB 4: ACADEMIC DEFENSE & QA ---
    with tab4:
        st.subheader("Cross-Examination & Comparative Defense")
        
        persona = st.radio(
            "Select AI Inquiry Persona:",
            ["🧐 Critical Peer Reviewer", "🚀 Research Collaborator", "⚖️ Comparative Analyst"],
            horizontal=True
        )

        qa_input = st.text_input("Enter your research question or thesis defense point:")

        if qa_input and st.button("Submit Inquiry for Analysis", type="primary"):
            with st.spinner("Synthesizing context-aware defense response..."):
                if "Peer Reviewer" in persona:
                    role_prompt = f"Act as a strict peer reviewer. Evaluate: '{qa_input}'. Identify assumptions or missing controls."
                elif "Collaborator" in persona:
                    role_prompt = f"Act as a research collaborator. Evaluate: '{qa_input}'. Suggest 3 concrete next-step experiments."
                else:
                    role_prompt = f"Act as a material scientist. Evaluate: '{qa_input}'. Compare against benchmark methodologies."

                qa_response = safe_generate(st.session_state["pdf_file"], role_prompt)
                st.markdown(f"#### Persona Output: {persona}")
                st.write(qa_response.text)
else:
    st.info("👈 Upload an academic PDF in the sidebar to launch the research workspace.")
