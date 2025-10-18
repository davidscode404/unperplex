import streamlit as st
import requests
import json
import os
from datetime import datetime
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration - must be first Streamlit command
st.set_page_config(
    page_title="Disease Q&A Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for flashy styling
st.markdown("""
<style>
    /* Main container styling */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 0.5rem;
    }
    
    /* Card styling */
    .info-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        margin: 0.5rem 0;
        animation: slideIn 0.5s ease-out;
        color: white;
        height: 200px;
        overflow-y: auto;
    }
    
    .info-card.empty {
        background: rgba(255, 255, 255, 0.3);
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Header styling */
    .main-header {
        text-align: center;
        color: white;
        font-size: 2.5rem;
        font-weight: bold;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        margin-bottom: 0.5rem;
        margin-top: 0;
        animation: fadeIn 1s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    .sub-header {
        text-align: center;
        color: #f0f0f0;
        font-size: 1rem;
        margin-bottom: 0.5rem;
    }
    
    /* Result cards */
    .result-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        height: 200px;
        overflow-y: auto;
    }
    
    .result-card.empty {
        background: rgba(255, 255, 255, 0.3);
    }
    
    .result-title {
        font-size: 1.3rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
    }
    
    .result-content {
        font-size: 1rem;
        line-height: 1.5;
    }
    
    /* Citation styling */
    .citation-item {
        background: rgba(255, 255, 255, 0.2);
        padding: 0.5rem;
        border-left: 4px solid white;
        margin: 0.3rem 0;
        border-radius: 5px;
        font-size: 0.9rem;
        color: white;
    }
    
    .citation-item a {
        color: white !important;
        text-decoration: underline;
    }
    
    /* Button styling */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-size: 1.1rem;
        font-weight: bold;
        padding: 0.5rem 1.5rem;
        border-radius: 50px;
        border: none;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.3);
    }
    
    /* Input styling */
    .stTextInput>div>div>input {
        font-size: 1rem;
        padding: 0.5rem;
        border-radius: 10px;
        border: 2px solid #667eea;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Success/Error messages */
    .success-box {
        background: #d4edda;
        color: #155724;
        padding: 0.5rem;
        border-radius: 10px;
        border-left: 5px solid #28a745;
    }
    
    .error-box {
        background: #f8d7da;
        color: #721c24;
        padding: 0.5rem;
        border-radius: 10px;
        border-left: 5px solid #dc3545;
    }
    
    /* Compact spacing */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
    }
    
    h2 {
        font-size: 1.3rem;
        margin-top: 0;
        margin-bottom: 0.5rem;
    }
    
    /* Hide extra spacing */
    .element-container {
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'question_cache' not in st.session_state:
    st.session_state.question_cache = {}
if 'current_result' not in st.session_state:
    st.session_state.current_result = None

# API Configuration
API_ENDPOINT = 'https://api.perplexity.ai/chat/completions'
API_KEY = os.getenv('PERPLEXITY_API_KEY', '')

def ask_disease_question(question: str, api_key: str) -> dict:
    """Query the Perplexity API with caching"""
    
    # Check cache first
    if question in st.session_state.question_cache:
        return st.session_state.question_cache[question]
    
    prompt = f"""
You are a medical assistant. Answer the following question about a disease and provide ONLY valid JSON output with no other text.
The JSON must have exactly four keys: "overview", "causes", "treatments", and "citations".

Example format:
{{
  "overview": "A brief description of the disease.",
  "causes": "The causes of the disease.",
  "treatments": "Possible treatments for the disease.",
  "citations": ["https://example.com/citation1", "https://example.com/citation2"]
}}

Question: {question}

Respond with ONLY the JSON object, no other text before or after.
    """.strip()
    
    payload = {
        "model": "sonar-pro",
        "messages": [
            {"role": "system", "content": "You are a medical assistant that responds only in valid JSON format."},
            {"role": "user", "content": prompt}
        ]
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(API_ENDPOINT, headers=headers, json=payload, timeout=30)
    
    if response.status_code != 200:
        raise Exception(f"API request failed with status code {response.status_code}: {response.text}")
    
    result = response.json()
    
    if result.get("choices") and len(result["choices"]) > 0:
        content = result["choices"][0]["message"]["content"].strip()
        
        # Try to extract JSON if it's wrapped in code blocks
        if content.startswith("```"):
            # Remove markdown code blocks
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:].strip()
        
        try:
            parsed_data = json.loads(content)
        except json.JSONDecodeError as e:
            # Log the actual content for debugging
            raise Exception(f"Failed to parse JSON. Raw content: {content[:500]}...")
        
        # Cache the result
        st.session_state.question_cache[question] = parsed_data
        
        return parsed_data
    else:
        raise Exception("No answer provided in the response")

# Sidebar
with st.sidebar:
    st.markdown("### 📊 Stats")
    st.metric("Cached", len(st.session_state.question_cache))
    
    st.markdown("---")
    st.markdown("### 💡 Examples")
    st.markdown("""
    - What is diabetes?
    - Tell me about stroke
    - What causes heart disease?
    """)
    
    st.markdown("---")
    st.markdown("### 📚 About")
    st.markdown("""
    Powered by **Perplexity Sonar API**
    
    *Built with Streamlit* 🎈
    """)

# Main content
st.markdown('<h1 class="main-header">Unperplex</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Instant, reliable diagnosis.</p>', unsafe_allow_html=True)

# Create a compact input section with button next to input
col1, col2, col3, col4 = st.columns([1, 4, 1, 1])

with col2:
    question = st.text_input(
        "Question",
        placeholder="Ask a question about a disease (e.g., 'What is stroke?')",
        label_visibility="collapsed",
        key="question_input"
    )

with col3:
    ask_button = st.button("🔍 Ask", use_container_width=True)

# Process the question
if ask_button and question:
    if not API_KEY:
        st.error("⚠️ Please set your PERPLEXITY_API_KEY in your .env file!")
    else:
        with st.spinner("🔬 Researching your question..."):
            try:
                # Add a progress bar for visual effect
                progress_bar = st.progress(0)
                for i in range(100):
                    time.sleep(0.01)
                    progress_bar.progress(i + 1)
                
                result = ask_disease_question(question, API_KEY)
                progress_bar.empty()
                
                # Store result in session state
                st.session_state.current_result = result
                
            except json.JSONDecodeError as e:
                st.error(f"❌ Failed to parse response: {str(e)}")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

elif ask_button and not question:
    st.warning("⚠️ Please enter a question about a disease!")

# Always display the result boxes (empty or filled)
left_col, right_col = st.columns([1, 1])

# Get current result or None
result = st.session_state.current_result

# Left column - Overview and Sources
with left_col:
    st.markdown("## 📋 Overview")
    if result:
        st.markdown(f"""
        <div class="info-card">
            <p style="font-size: 1rem; line-height: 1.6; color: white;">{result.get('overview', 'N/A')}</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="info-card empty">
        </div>
        """, unsafe_allow_html=True)
    
    # Sources
    st.markdown("## 📚 Sources")
    if result:
        citations = result.get('citations', [])
        if citations and isinstance(citations, list) and len(citations) > 0:
            citations_html = ""
            for i, citation in enumerate(citations, 1):
                citations_html += f"""
                <div class="citation-item">
                    <strong>{i}.</strong> <a href="{citation}" target="_blank">{citation}</a>
                </div>
                """
            st.markdown(citations_html, unsafe_allow_html=True)
        else:
            st.info("No citations provided for this query.")

# Right column - Causes and Treatments
with right_col:
    # Causes
    st.markdown("## 🔬 Causes")
    if result:
        st.markdown(f"""
        <div class="result-card">
            <p class="result-content">{result.get('causes', 'N/A')}</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="result-card empty">
        </div>
        """, unsafe_allow_html=True)
    
    # Treatments
    st.markdown("## 💊 Treatments")
    if result:
        st.markdown(f"""
        <div class="result-card">
            <p class="result-content">{result.get('treatments', 'N/A')}</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="result-card empty">
        </div>
        """, unsafe_allow_html=True)