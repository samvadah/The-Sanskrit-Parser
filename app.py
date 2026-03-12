import streamlit as st
import requests
import urllib.parse
# Corrected import for skrutable v2.0+
from skrutable.splitting import Splitter

# --- Helpers ---
def transliterate(text, target="IAST"):
    """Auto-detects script and converts to target using Aksharamukha."""
    url = f"https://api.aksharamukha.com/api/public/process?target={target}&text={urllib.parse.quote(text)}"
    try:
        res = requests.get(url, timeout=5)
        return res.text
    except:
        return text

# --- Models ---
def call_dharmamitra(text):
    """Dharmamitra Tagging API"""
    url = "https://dharmamitra.org/api-tagging/tagging-parsed/"
    payload = {"texts": [text], "grammar_type": "indian"}
    try:
        res = requests.post(url, json=payload, timeout=10).json()
        if res and isinstance(res, list):
            return [{"word": t['form'], "root": t['lemma'], "tag": t.get('morphs', '')} for t in res[0].get('words', [])]
    except:
        return []

def call_hellwig(text):
    """Hellwig via Skrutable Remote API"""
    try:
        # Initialize the Splitter
        s = Splitter()
        # This calls the remote server for the Hellwig model
        result = s.split(text, split_method="hellwig")
        # Ensure we return a list of words
        return [{"word": w, "root": w, "tag": "Segmented"} for w in str(result).split()]
    except Exception as e:
        return []

# --- UI Setup ---
st.set_page_config(page_title="Sanskrit Multi-Parser", page_icon="🕉️")
st.title("🕉️ Sanskrit Multi-Parser")

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Settings")
    script = st.selectbox("Display Script", ["Devanagari", "IAST", "Telugu", "Kannada"])
    model_opt = st.radio("Parser Model", ["Dharmamitra (Morphology)", "Hellwig (Segmentation)"])
    dict_opt = st.radio("Dictionary Lookup", ["Kosha.app", "Ambuda", "SanskritKosha"])

# --- Main Interface ---
user_input = st.text_area("Input Sanskrit (Any script):", "मृदुलस्मितांशुलहरीज्योत्स्ना")

if st.button("Parse & Search", type="primary"):
    # Convert any script to IAST for processing
    iast_text = transliterate(user_input, "IAST")
    
    # 1. Parsing Logic
    if "Dharmamitra" in model_opt:
        with st.spinner("Calling Dharmamitra API..."):
            data = call_dharmamitra(iast_text)
    else:
        with st.spinner("Calling Hellwig Model (via Skrutable)..."):
            data = call_hellwig(iast_text)
    
    if data:
        st.subheader("Results")
        for item in data:
            disp_word = transliterate(item['word'], script)
            disp_root = transliterate(item['root'], script)
            
            # Use Devanagari for dictionary search queries
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
                st.markdown(f"**{disp_word}** ({item['tag']})")
                st.caption(f"Root: {disp_root}")
            with col2:
                st.link_button(f"Search", link)
    else:
        st.error("Model unavailable. Please try the other parser or check your connection.")
