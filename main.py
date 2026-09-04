import streamlit as st
import os
from PIL import Image
import easyocr
import numpy as np
from dotenv import load_dotenv

# Import our custom modules
import importlib
from modules import file_reader, doc_generator, llm_connector
importlib.reload(file_reader)
importlib.reload(doc_generator)
importlib.reload(llm_connector)

from modules.file_reader import read_pdf, read_docx
from modules.doc_generator import create_pdd_docx
from modules.llm_connector import (
    generate_documentation_from_text,
    get_ollama_models,
    check_ollama_health,
    pull_ollama_model,
    call_ollama_stream,
    parse_llm_response,
)

# Load environment variables (for OpenAI API key)
load_dotenv("D:/PythonProject/.env")

# ---------------------------------
# PAGE CONFIG
# ---------------------------------
st.set_page_config(
    page_title="AI Automation Documentation Generator",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------
# PREMIUM ENTERPRISE CSS
# ---------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Outfit:wght@300;400;600;800&display=swap');
    :root {
        --blue-900:#0d2137;--blue-800:#1a3a5c;--blue-700:#1f4e79;
        --blue-600:#2563a8;--blue-400:#4a90d9;
        --teal-600:#0d9488;--teal-500:#14b8a6;--teal-400:#2dd4bf;--teal-300:#5eead4;
        --card-bg:rgba(255,255,255,0.72);--card-border:rgba(37,99,168,0.14);
        --text-primary:#0d2137;--text-muted:#94a3b8;
        --radius-lg:16px;--radius-md:12px;--radius-sm:8px;
        --shadow-sm:0 1px 3px rgba(13,33,55,0.08),0 1px 2px rgba(13,33,55,0.04);
        --shadow-md:0 4px 16px rgba(13,33,55,0.10),0 2px 6px rgba(13,33,55,0.06);
        --shadow-lg:0 12px 40px rgba(13,33,55,0.14),0 4px 12px rgba(13,33,55,0.08);
        --glow-teal:0 0 20px rgba(20,184,166,0.25);
    }
    html,body,[class*="css"]{font-family:'Inter','Outfit',sans-serif;color:var(--text-primary);}
    .main{background:linear-gradient(135deg,#e8f0fa 0%,#f0f9ff 35%,#e6faf8 100%);min-height:100vh;}
    .main .block-container{padding:1.5rem 2.5rem 3rem 2.5rem;max-width:1280px;}

    section[data-testid="stSidebar"]{background:linear-gradient(180deg,#0d2137 0%,#1a3a5c 60%,#0d4a4a 100%);border-right:none;box-shadow:4px 0 24px rgba(13,33,55,0.18);}
    section[data-testid="stSidebar"] *{color:#e2eaf4 !important;}
    section[data-testid="stSidebar"] h1,section[data-testid="stSidebar"] h2,section[data-testid="stSidebar"] h3{color:#ffffff !important;font-weight:700 !important;}
    section[data-testid="stSidebar"] .stTextInput input,section[data-testid="stSidebar"] .stSelectbox select{background:rgba(255,255,255,0.08) !important;border:1px solid rgba(148,212,232,0.25) !important;border-radius:var(--radius-sm) !important;color:#ffffff !important;}
    section[data-testid="stSidebar"] hr{border-color:rgba(148,212,232,0.2) !important;margin:1.25rem 0 !important;}
    .sidebar-tip{background:rgba(20,184,166,0.12);border:1px solid rgba(45,212,191,0.25);border-radius:var(--radius-md);padding:1rem;margin-top:0.5rem;}
    .sidebar-tip p,.sidebar-tip li{color:#a5f3ec !important;font-size:0.82rem !important;line-height:1.6 !important;}

    .hero-header{background:linear-gradient(135deg,var(--blue-800) 0%,var(--blue-700) 40%,var(--teal-600) 100%);border-radius:var(--radius-lg);padding:2.2rem 2.5rem;margin-bottom:1.75rem;position:relative;overflow:hidden;box-shadow:var(--shadow-lg);}
    .hero-header::before{content:'';position:absolute;top:-60px;right:-60px;width:260px;height:260px;background:radial-gradient(circle,rgba(45,212,191,0.18) 0%,transparent 70%);border-radius:50%;}
    .hero-header::after{content:'';position:absolute;bottom:-80px;left:-40px;width:220px;height:220px;background:radial-gradient(circle,rgba(74,144,217,0.15) 0%,transparent 70%);border-radius:50%;}
    .hero-badge{display:inline-block;background:rgba(45,212,191,0.22);border:1px solid rgba(45,212,191,0.4);color:#5eead4;font-size:0.68rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;padding:0.25rem 0.7rem;border-radius:20px;margin-bottom:0.75rem;position:relative;z-index:1;}
    .hero-title{font-size:2rem;font-weight:800;color:#ffffff;margin:0 0 0.35rem 0;letter-spacing:-0.02em;position:relative;z-index:1;}
    .hero-subtitle{font-size:0.95rem;color:rgba(255,255,255,0.75);margin:0;font-weight:400;max-width:640px;line-height:1.55;position:relative;z-index:1;}

    .kpi-row{display:flex;gap:1rem;margin-bottom:1.75rem;}
    .kpi-card{flex:1;background:var(--card-bg);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);border:1px solid var(--card-border);border-radius:var(--radius-md);padding:1.1rem 1.25rem;box-shadow:var(--shadow-sm);transition:box-shadow 0.2s,transform 0.2s;position:relative;overflow:hidden;}
    .kpi-card:hover{box-shadow:var(--shadow-md);transform:translateY(-2px);}
    .kpi-card::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;border-radius:var(--radius-md) var(--radius-md) 0 0;}
    .kpi-card.blue::before{background:linear-gradient(90deg,var(--blue-700),var(--blue-400));}
    .kpi-card.teal::before{background:linear-gradient(90deg,var(--teal-600),var(--teal-300));}
    .kpi-card.green::before{background:linear-gradient(90deg,#059669,#34d399);}
    .kpi-card.amber::before{background:linear-gradient(90deg,#d97706,#fbbf24);}
    .kpi-icon{font-size:1.4rem;margin-bottom:0.4rem;display:block;}
    .kpi-value{font-size:1.55rem;font-weight:800;color:var(--text-primary);line-height:1;}
    .kpi-label{font-size:0.72rem;font-weight:600;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.09em;margin-top:0.2rem;}

    .glass-card{background:var(--card-bg);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);border:1px solid var(--card-border);border-radius:var(--radius-lg);padding:1.5rem;box-shadow:var(--shadow-sm);margin-bottom:1.25rem;transition:box-shadow 0.25s,transform 0.25s;}
    .glass-card:hover{box-shadow:var(--shadow-md);}

    .stFileUploader{border:2px dashed rgba(37,99,168,0.3) !important;border-radius:var(--radius-md) !important;background:rgba(37,99,168,0.03) !important;padding:0.5rem !important;transition:all 0.3s ease !important;}
    .stFileUploader:hover{border-color:var(--teal-500) !important;background:rgba(20,184,166,0.04) !important;box-shadow:var(--glow-teal) !important;}

    .stTextArea textarea{border-radius:var(--radius-md) !important;border:1px solid rgba(37,99,168,0.2) !important;background:rgba(255,255,255,0.85) !important;font-size:0.88rem !important;transition:border-color 0.2s,box-shadow 0.2s;resize:vertical !important;}
    .stTextArea textarea:focus{border-color:var(--teal-500) !important;box-shadow:0 0 0 3px rgba(20,184,166,0.12) !important;}

    div.stButton>button{background:linear-gradient(135deg,var(--blue-700) 0%,var(--teal-600) 100%) !important;color:white !important;font-weight:700 !important;font-size:0.95rem !important;border:none !important;padding:0.75rem 2.5rem !important;border-radius:50px !important;box-shadow:0 4px 18px rgba(31,78,121,0.28) !important;transition:all 0.3s cubic-bezier(0.4,0,0.2,1) !important;width:100%;}
    div.stButton>button:hover{transform:translateY(-2px) !important;box-shadow:0 8px 28px rgba(31,78,121,0.38) !important;background:linear-gradient(135deg,#2563a8 0%,#0d9488 100%) !important;}
    div.stButton>button:active{transform:translateY(0px) !important;}

    div[data-testid="stDownloadButton"]>button{background:var(--card-bg) !important;backdrop-filter:blur(10px) !important;color:var(--blue-700) !important;border:1.5px solid var(--card-border) !important;font-weight:600 !important;font-size:0.85rem !important;border-radius:50px !important;padding:0.6rem 1.5rem !important;box-shadow:var(--shadow-sm) !important;transition:all 0.25s ease !important;}
    div[data-testid="stDownloadButton"]>button:hover{background:var(--blue-700) !important;color:white !important;border-color:var(--blue-700) !important;box-shadow:var(--shadow-md) !important;transform:translateY(-1px) !important;}

    h1{font-weight:800 !important;color:var(--blue-900) !important;margin-bottom:0.3rem !important;}
    h2,h3{font-weight:700 !important;color:var(--blue-800) !important;}
    h2{font-size:1.25rem !important;}h3{font-size:1.05rem !important;}

    .status-dot-green{width:8px;height:8px;background:#10b981;border-radius:50%;animation:pulse-g 2s infinite;display:inline-block;}
    .status-dot-red{width:8px;height:8px;background:#ef4444;border-radius:50%;display:inline-block;}
    @keyframes pulse-g{0%,100%{box-shadow:0 0 0 0 rgba(16,185,129,0.5);}50%{box-shadow:0 0 0 5px rgba(16,185,129,0);}}

    .timeline{display:flex;align-items:center;margin-bottom:1.5rem;padding:1rem 1.5rem;background:var(--card-bg);backdrop-filter:blur(12px);border:1px solid var(--card-border);border-radius:var(--radius-md);box-shadow:var(--shadow-sm);overflow-x:auto;}
    .tl-step{display:flex;flex-direction:column;align-items:center;gap:0.3rem;min-width:80px;position:relative;z-index:1;}
    .tl-step+.tl-step::before{content:'';position:absolute;left:calc(-50% + 12px);top:14px;width:calc(100% - 24px);height:2px;background:linear-gradient(90deg,var(--blue-400),var(--teal-400));z-index:0;}
    .tl-circle{width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:0.7rem;font-weight:700;position:relative;z-index:2;}
    .tl-circle.active{background:linear-gradient(135deg,var(--blue-700),var(--teal-500));color:white;box-shadow:0 0 12px rgba(20,184,166,0.4);}
    .tl-circle.pending{background:#e2e8f0;color:#94a3b8;}
    .tl-label{font-size:0.65rem;font-weight:600;color:var(--text-muted);text-align:center;text-transform:uppercase;letter-spacing:0.06em;white-space:nowrap;}
    .tl-label.active{color:var(--blue-600);}

    .output-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:1.25rem;padding-bottom:0.75rem;border-bottom:1px solid var(--card-border);}
    .output-badge{background:linear-gradient(135deg,var(--blue-700),var(--teal-500));color:white;font-size:0.68rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;padding:0.25rem 0.75rem;border-radius:20px;}

    details[data-testid="stExpander"]{border:1px solid var(--card-border) !important;border-radius:var(--radius-md) !important;background:var(--card-bg) !important;backdrop-filter:blur(12px) !important;margin-bottom:0.75rem !important;box-shadow:var(--shadow-sm) !important;overflow:hidden;}
    details[data-testid="stExpander"]:hover{box-shadow:var(--shadow-md) !important;}
    details[data-testid="stExpander"] summary{font-weight:600 !important;color:var(--blue-800) !important;padding:0.9rem 1.1rem !important;font-size:0.9rem !important;cursor:pointer;}
    details[data-testid="stExpander"][open] summary{border-bottom:1px solid var(--card-border);color:var(--teal-600) !important;}
    details[data-testid="stExpander"]>div{padding:1rem 1.1rem !important;}

    .section-pill{display:inline-flex;align-items:center;gap:0.35rem;background:linear-gradient(135deg,rgba(31,78,121,0.08),rgba(20,184,166,0.08));border:1px solid rgba(37,99,168,0.15);border-radius:20px;padding:0.3rem 0.85rem;font-size:0.72rem;font-weight:700;color:var(--blue-700);text-transform:uppercase;letter-spacing:0.09em;margin-bottom:0.6rem;}
    .stAlert{border-radius:var(--radius-md) !important;}
    hr{border:none !important;border-top:1px solid rgba(37,99,168,0.12) !important;margin:1.5rem 0 !important;}
    @media(max-width:768px){.main .block-container{padding:1rem !important;}.kpi-row{flex-wrap:wrap;}.kpi-card{min-width:calc(50% - 0.5rem);}.hero-title{font-size:1.4rem;}}
</style>
""", unsafe_allow_html=True)

# ---------------------------------
# CACHED OCR MODEL (EasyOCR)
# ---------------------------------
@st.cache_resource
def get_ocr_reader():
    # Cache the reader so it initializes once and persists
    return easyocr.Reader(['en'], gpu=False)

try:
    reader = get_ocr_reader()
except Exception as e:
    st.error(f"Failed to initialize EasyOCR: {e}")

# ---------------------------------
# OCR FUNCTION
# ---------------------------------
def read_images(image_files):
    text = ""
    if image_files:
        for idx, img_file in enumerate(image_files):
            try:
                image = Image.open(img_file).convert("RGB")
                image_np = np.array(image)
                result = reader.readtext(image_np, detail=0)
                text += f"\n\n========== SCREENSHOT {idx+1}: {img_file.name} ==========\n"
                text += "\n".join(result)
            except Exception as e:
                text += f"\n\n[Error reading screenshot {img_file.name}: {str(e)}]\n"
    return text

# ---------------------------------
# SIDEBAR
# ---------------------------------
with st.sidebar:
    st.markdown("""
    <div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:1.5rem;">
      <span style="font-size:1.6rem;">🤖</span>
      <div>
        <div style="font-size:1rem;font-weight:800;color:#fff;">AI Doc Generator</div>
        <div style="font-size:0.68rem;color:#94d4e8;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;">Enterprise Suite</div>
      </div>
    </div>""", unsafe_allow_html=True)

    # Load LLM settings from environment variables or .env file
    provider_env = os.getenv("LLM_PROVIDER")
    azure_key = os.getenv("AZURE_AI_FOUNDRY_API_KEY", os.getenv("AZURE_OPENAI_API_KEY", ""))
    azure_endpoint = os.getenv("AZURE_AI_FOUNDRY_ENDPOINT", os.getenv("AZURE_OPENAI_ENDPOINT", ""))
    azure_deployment = os.getenv("AZURE_AI_FOUNDRY_DEPLOYMENT", os.getenv("AZURE_OPENAI_DEPLOYMENT", ""))
    azure_api_version = os.getenv("AZURE_AI_FOUNDRY_API_VERSION", os.getenv("AZURE_OPENAI_API_VERSION", "2024-05-01-preview"))
    openai_key = os.getenv("OPENAI_API_KEY", "")
    gemini_key = os.getenv("GEMINI_API_KEY", "")

    if gemini_key:
        openai_key = gemini_key
    openai_base_url = os.getenv("OPENAI_BASE_URL", "").strip()  # Custom base URL for Gemini/Groq

    # Auto-detect provider if not explicitly configured in environment
    if provider_env in ["Azure AI Foundry", "OpenAI", "Ollama (Local)"]:
        provider = provider_env
    else:
        if azure_key and azure_endpoint and azure_deployment:
            provider = "Azure AI Foundry"
        elif openai_key:
            provider = "OpenAI"
        else:
            provider = "Ollama (Local)"

    is_online = False
    use_streaming = False
    api_version = None
    openai_provider_label = "OpenAI Cloud"  # display label — updated below for Gemini/Groq

    if provider == "Azure AI Foundry":
        api_key = azure_key
        base_url = azure_endpoint
        model_name = azure_deployment
        api_version = azure_api_version
    elif provider == "OpenAI":
        api_key = openai_key
        # Prefer GEMINI model name if GEMINI key is set, otherwise fallback
        model_name = os.getenv(
            "GEMINI_MODEL_NAME",
            os.getenv("OPENAI_MODEL_NAME", "gemini-3.6-flash")
        )
        # Base URL: use GEMINI_BASE_URL when GEMINI key is present, else OPENAI_BASE_URL
        if gemini_key:
            base_url = os.getenv("GEMINI_BASE_URL", "").strip()
        else:
            base_url = openai_base_url if openai_base_url else None
        # Detect which compatible provider is in use for the sidebar label
        if base_url and "generativelanguage.googleapis.com" in base_url:
            openai_provider_label = "Google Gemini (AI Studio)"
        elif base_url and "groq.com" in base_url:
            openai_provider_label = "Groq (Free Tier)"
        else:
            openai_provider_label = "OpenAI Cloud"
    else:  # Ollama (Local)
        provider = "Ollama (Local)"
        base_url = os.getenv("OLLAMA_SERVER_URL", "http://localhost:11434")
        is_online, _ = check_ollama_health(base_url)
        available_models = get_ollama_models(base_url) if is_online else []
        if available_models:
            default_index = 0
            for idx, m in enumerate(available_models):
                if "llama3.2" in m.lower():
                    default_index = idx
                    break
            model_name = available_models[default_index]
        else:
            model_name = os.getenv("OLLAMA_MODEL_NAME", "llama3.2")
        use_streaming = True
        api_key = None

    st.markdown('<hr style="border-color:rgba(148,212,232,0.2);margin:1.25rem 0;">', unsafe_allow_html=True)

    if provider == "OpenAI":
        active_icon = "🟢" if openai_key else "🔴"
        status_label = openai_provider_label if openai_key else f"{openai_provider_label} · Key Missing"
    elif provider == "Azure AI Foundry":
        active_icon = "🟢" if (api_key and base_url and model_name) else "🟡"
        status_label = "Azure AI Foundry"
    else:
        active_icon = "🟢" if is_online else "🔴"
        status_label = "Local · Ollama"

    st.markdown('<hr style="border-color:rgba(148,212,232,0.2);margin:1.25rem 0;">', unsafe_allow_html=True)

    st.markdown(f"""
    <div style="background:rgba(20,184,166,0.1);border:1px solid rgba(45,212,191,0.25);
        border-radius:10px;padding:0.7rem 0.85rem;margin-bottom:1rem;">
        <div style="font-size:0.65rem;font-weight:700;color:#5eead4;text-transform:uppercase;
            letter-spacing:0.1em;margin-bottom:0.25rem;">Active Configuration</div>
        <div style="font-size:0.85rem;font-weight:600;color:#fff;">{active_icon} {model_name}</div>
        <div style="font-size:0.68rem;color:#94d4e8;margin-top:0.1rem;">{status_label}</div>
    </div>""", unsafe_allow_html=True)

    if provider == "OpenAI" and not openai_key:
        st.markdown(
            '<div style="background:rgba(239,68,68,0.15);border:1px solid rgba(239,68,68,0.35);'
            'border-radius:10px;padding:0.7rem 0.85rem;margin-bottom:1rem;color:#fca5a5;font-size:0.78rem;line-height:1.4;">'
            '<strong>⚠️ API Key Required</strong><br>'
            'Please add your <code>OPENAI_API_KEY</code> to the <code>.env</code> file in the project folder.'
            '</div>',
            unsafe_allow_html=True
        )

    st.markdown('<div class="sidebar-tip">', unsafe_allow_html=True)
    st.markdown("""
    **💡 Quick Guide**

    - Upload SOPs (PDF/DOCX) and interface screenshots
    - Add extra process context in the notes box
    - Click **Generate** to get a full structured PDD
    - Download as Word Document or Markdown
    """)
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------
# HERO HEADER
# ---------------------------------
st.markdown("""
<div class="hero-header">
  <div class="hero-badge">✦ AI-Powered &nbsp;·&nbsp; Enterprise Grade</div>
  <div class="hero-title">🤖 Automation Documentation Generator</div>
  <div class="hero-subtitle">
    Transform raw SOPs, process screenshots, and notes into fully structured
    Process Definition Documents (PDDs) — Google Gemini (AI Studio).
  </div>
</div>""", unsafe_allow_html=True)

# ---------------------------------
# KPI METRICS
# ---------------------------------
st.markdown("""
<div class="kpi-row">
  <div class="kpi-card blue">
    <span class="kpi-icon">📄</span>
    <div class="kpi-value">PDF · DOCX</div>
    <div class="kpi-label">Document Formats</div>
  </div>
  <div class="kpi-card teal">
    <span class="kpi-icon">📸</span>
    <div class="kpi-value">OCR</div>
    <div class="kpi-label">Screenshot Extraction</div>
  </div>
  <div class="kpi-card green">
    <span class="kpi-icon">🧠</span>
    <div class="kpi-value">gemini-3.6-flash</div>
    <div class="kpi-label">AI Synthesis Engines</div>
  </div>
  <div class="kpi-card amber">
    <span class="kpi-icon">⚡</span>
    <div class="kpi-value">&lt; 60s</div>
    <div class="kpi-label">Avg. Generation Time</div>
  </div>
</div>""", unsafe_allow_html=True)

# ---------------------------------
# PROGRESS TIMELINE
# ---------------------------------
st.markdown("""
<div class="timeline">
  <div class="tl-step"><div class="tl-circle active">1</div><div class="tl-label active">Upload Sources</div></div>
  <div class="tl-step"><div class="tl-circle active">2</div><div class="tl-label active">Add Context</div></div>
  <div class="tl-step"><div class="tl-circle active">3</div><div class="tl-label active">Generate PDD</div></div>
  <div class="tl-step"><div class="tl-circle active">4</div><div class="tl-label active">Download</div></div>
</div>""", unsafe_allow_html=True)

# ---------------------------------
# UPLOAD SECTION
# ---------------------------------
col1, col2 = st.columns(2, gap="medium")

with col1:
    st.markdown('<div class="section-pill"> Step 1 &nbsp;·&nbsp; SOP Documents</div>', unsafe_allow_html=True)
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("**Upload SOP Documents**")
    st.caption("Supported formats: PDF, Word (.docx)")
    pdf = st.file_uploader("Upload SOP PDF", type=["pdf"], label_visibility="collapsed")
    st.markdown('<div style="margin-top:0.6rem;"></div>', unsafe_allow_html=True)
    docx_file = st.file_uploader("Upload Word Document", type=["docx"], label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="section-pill"> Step 2 &nbsp;·&nbsp; Screenshots</div>', unsafe_allow_html=True)
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("Upload Interface Screenshots")
    st.caption("PNG, JPG, JPEG — multiple files supported")
    images = st.file_uploader("Upload Screenshots (GUI steps)", type=["png","jpg","jpeg"],
        accept_multiple_files=True, label_visibility="collapsed")
    if images:
        st.markdown(f"""<div style="display:flex;align-items:center;gap:0.4rem;margin-top:0.5rem;">
            <span class="status-dot-green"></span>
            <span style="font-size:0.78rem;color:#059669;font-weight:600;">{len(images)} file(s) ready for OCR</span>
        </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------
# PROCESS NOTES
# ---------------------------------
st.markdown('<div class="section-pill">📝 Step 3 &nbsp;·&nbsp; Process Context</div>', unsafe_allow_html=True)
st.markdown('<div class="glass-card">', unsafe_allow_html=True)
st.markdown("**Process Notes & Additional Context**")
st.caption("Describe rule variations, system credentials, decision logic, or any extra details.")
notes = st.text_area("Process Notes",
    placeholder="e.g. 'Log in to SAP using transaction code FI01. If customer ID starts with A, route to queue 1, otherwise queue 2.'",
    height=120, label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------
# GENERATE BUTTON
# ---------------------------------
st.markdown('<div style="margin:1.5rem 0 0.5rem 0;">', unsafe_allow_html=True)
g1, g2, g3 = st.columns([1, 2, 1])
with g2:
    generate_clicked = st.button(" Generate Automation Documentation", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------
# RUNNING PROCESS
# ---------------------------------
if generate_clicked:
    if not (pdf or docx_file or images or notes.strip()):
        st.warning("Please provide at least one source (PDF, Word Document, Screenshots, or Process Notes).")
    elif provider == "OpenAI" and not api_key:
        st.error(" Please configure your OpenAI API Key in the `.env` file.")
    elif provider == "Azure AI Foundry" and (not api_key or not base_url or not model_name):
        st.error(" Please configure your Azure AI Foundry API Key, Endpoint URL, and Deployment Name in the `.env` file.")
    elif provider == "Ollama (Local)" and not is_online:
        st.error(" Ollama server is offline. Please start Ollama and refresh the page.")
    else:
        full_text = ""

        with st.status("Extracting information from uploaded sources...", expanded=True) as status:
            if pdf is not None:
                status.write("Reading PDF text...")
                full_text += f"\n\n========== PDF: {pdf.name} ==========\n"
                full_text += read_pdf(pdf)
            if docx_file is not None:
                status.write("Reading Word document text...")
                full_text += f"\n\n========== DOCX: {docx_file.name} ==========\n"
                full_text += read_docx(docx_file)
            if images:
                status.write(f"Performing OCR on {len(images)} screenshots (this may take a few seconds)...")
                full_text += read_images(images)
            if notes.strip():
                status.write("Integrating custom process notes...")
                full_text += "\n\n========== USER PROCESS NOTES ==========\n"
                full_text += notes
            status.update(label=" All source texts extracted successfully!", state="complete")

        # Generation — streaming for Ollama, batch for OpenAI
        if provider == "Ollama (Local)" and use_streaming:
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.75rem;">'
                f'<span class="status-dot-green"></span>'
                f'<span style="font-size:0.82rem;font-weight:600;color:#0d9488;">'
                f'Streaming from Ollama · <em>{model_name}</em></span></div>',
                unsafe_allow_html=True)
            stream_box = st.empty()
            raw_output = ""
            try:
                for chunk in call_ollama_stream(model_name, full_text, base_url):
                    if chunk:
                        raw_output += chunk
                        stream_box.markdown(
                            f'<div style="background:rgba(255,255,255,0.6);border:1px solid rgba(37,99,168,0.12);'
                            f'border-radius:12px;padding:1rem;font-size:0.83rem;max-height:320px;overflow-y:auto;'
                            f'white-space:pre-wrap;font-family:monospace;color:#0d2137;">{raw_output}</div>',
                            unsafe_allow_html=True)
                stream_box.empty()
                sections = parse_llm_response(raw_output)
                st.session_state["generated_sections"] = sections
                st.session_state["full_extracted_text"] = full_text
                st.success(" Process documentation generated successfully!")
            except Exception as e:
                st.error(f" Streaming failed: {str(e)}")
        else:
            with st.spinner("AI is synthesizing automation details and drafting PDD sections..."):
                try:
                    sections = generate_documentation_from_text(
                        provider=provider, model_name=model_name,
                        api_key=api_key, base_url=base_url, full_text=full_text,
                        api_version=api_version if api_version else "2024-05-01-preview")
                    st.session_state["generated_sections"] = sections
                    st.session_state["full_extracted_text"] = full_text
                    st.success(" Process documentation generated successfully!")
                except Exception as e:
                    st.error(f"Generation failed: {str(e)}")
                    if "insufficient_quota" in str(e).lower():
                        st.info("OpenAI quota exceeded. Please configure Ollama (Local) or another provider in your `.env` file.")

# ---------------------------------
# RENDER GENERATED DOCUMENTATION
# ---------------------------------
if "generated_sections" in st.session_state:
    sections = st.session_state["generated_sections"]

    st.markdown('<hr>', unsafe_allow_html=True)
    st.markdown("""
    <div class="output-header">
      <div>
        <div style="font-size:0.7rem;font-weight:700;color:#2563a8;text-transform:uppercase;
            letter-spacing:0.1em;margin-bottom:0.2rem;">📋 Output</div>
        <div style="font-size:1.2rem;font-weight:800;color:#0d2137;">Generated Documentation Package</div>
      </div>
      <span class="output-badge">✓ Ready to Download</span>
    </div>""", unsafe_allow_html=True)

    dl1, dl2 = st.columns(2, gap="medium")

    try:
        docx_buffer = create_pdd_docx(sections)
        with dl1:
            st.download_button(
                label=" Download Process Definition Document (.docx)",
                data=docx_buffer,
                file_name="Process_Definition_Document_PDD.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True)
    except Exception as e:
        st.error(f"Could not prepare DOCX file: {e}")

    md_content = ""
    for title, content in sections.items():
        md_content += f"# {title}\n\n{content}\n\n"

    with dl2:
        st.download_button(
            label=" Download PDD Content as Markdown (.md)",
            data=md_content,
            file_name="Process_Definition_Document_PDD.md",
            mime="text/markdown",
            use_container_width=True)

    st.markdown('<div style="margin-top:1.25rem;"></div>', unsafe_allow_html=True)
    st.markdown("""<div style="font-size:0.72rem;font-weight:700;color:#94a3b8;text-transform:uppercase;
        letter-spacing:0.1em;margin-bottom:0.75rem;">📂 Document Sections — click to expand</div>""",
        unsafe_allow_html=True)

    section_icons = ["📌", "🔄", "🖥️", "⚙️", "📊", "🔑", "📋", "✅", "⚠️", "📎"]
    for idx, (title, content) in enumerate(sections.items()):
        icon = section_icons[idx % len(section_icons)]
        with st.expander(f"{icon} {title}", expanded=(idx == 0)):
            st.markdown(content)

    st.markdown('<div style="margin-top:0.75rem;"></div>', unsafe_allow_html=True)
    with st.expander(" View Raw Extracted Source Text", expanded=False):
        st.text_area("Extracted Sources Context",
            st.session_state.get("full_extracted_text", ""), height=300, disabled=True)
