import streamlit as st
import requests
import urllib.parse
from skrutable.splitting import Splitter

# Initialize Skrutable Splitter once at startup to save time
@st.cache_resource
def load_splitter():
    try:
        return Splitter()
    except Exception as e:
        print(f"Skrutable Init Error: {e}")
        return None

# --- Helpers ---
def transliterate(text, target="IAST"):
    """Auto-detects script and converts to target using Aksharamukha."""
    # Using the standardized Aksharamukha API endpoint
    url = f"https://api.aksharamukha.com/api/public/process?target={target}&text={urllib.parse.quote(text)}"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            return res.text
        return text
    except:
        return text

# --- Models ---
def call_dharmamitra(text):
    """Dharmamitra (Byte5) Tagging API"""
    url = "https://dharmamitra.org/api-tagging/tagging-parsed/"
    payload = {"texts": [text], "grammar_type": "indian"}
    try:
        res = requests.post(url, json=payload, timeout=15)
        res.raise_for_status()
        data = res.json()
        if data and isinstance(data, list) and len(data) > 0:
            words = data[0].get('words', data[0].get('tokens', []))
            return [{"word": t['form'], "root": t['lemma'], "tag": t.get('morphs', '')} for t in words]
        return []
    except Exception as e:
        print(f"Dharmamitra API Error: {e}")
        return []

def call_hellwig(text):
    """Hellwig (2018) via Skrutable Remote API"""
    splitter = load_splitter()
    if not splitter:
        return []
    try:
        # Hellwig model via remote server call
        result = splitter.split(text, split_method="hellwig")
        return [{"word": w, "root": w, "tag": "Segmented"} for w in str(result).split()]
    except Exception as e:
        print(f"Hellwig Model Error: {e}")
        return []

# --- UI Setup ---
st.set_page_config(page_title="The Sanskrit Parser", page_icon="🕉️")
st.title("The Sanskrit Parser")

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Settings")
    script = st.selectbox("Display Script", ["Devanagari", "IAST", "Telugu", "Kannada"])
    model_opt = st.radio("Parser Model", ["Dharmamitra (Byte5)", "Hellwig (2018)"])
    dict_opt = st.radio("Dictionary Lookup", ["Kosha.app", "Ambuda", "SanskritKosha"])

# --- Main Interface ---
user_input = st.text_area("Input Sanskrit (Any script):", "मृदुलस्मितांशुलहरीज्योत्स्ना")

if st.button("Parse & Search", type="primary"):
    # Convert input to IAST for the models
    with st.spinner("Preparing text..."):
        iast_text = transliterate(user_input, "IAST")
    
    # 1. Parsing Logic
    data = []
    if "Dharmamitra" in model_opt:
        with st.spinner("Calling Dharmamitra (Byte5)..."):
            data = call_dharmamitra(iast_text)
    else:
        with st.spinner("Calling Hellwig (2018)..."):
            data = call_hellwig(iast_text)
    
    # 2. Results Display
    if data:
        st.subheader("Results")
        for item in data:
            disp_word = transliterate(item['word'], script)
            disp_root = transliterate(item['root'], script)
            
            # Dictionary searches work best with Devanagari
            query = transliterate(item['root'], "Devanagari")
            q_enc = urllib.parse.quote(query)
            
            # Dictionary routing
            if dict_opt == "Kosha.app":
                link = f"https://kosha.app/?q={q_enc}"
            elif dict_opt == "Ambuda":
                link = f"https://ambuda.org/tools/dictionaries/{q_enc}"
            else:
                link = f"https://sanskritkosha.com/dictionary/{q_enc}"
            
            # Display UI
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{disp_word}**")
                st.caption(f"Root: {disp_root} | Tag: {item['tag']}")
            with col2:
                st.link_button(f"Lookup", link)
    else:
        st.error("Model unavailable. If this persists, please check the 'Manage app' logs for connection errors.")
