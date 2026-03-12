import streamlit as st
import requests
import urllib.parse
from skrutable.splitter.wrapper import Splitter

# --- Helpers ---
def transliterate(text, target="IAST"):
    """Auto-detects script and converts to target using Aksharamukha."""
    url = f"https://api.aksharamukha.com/api/public/process?target={target}&text={urllib.parse.quote(text)}"
    try:
        return requests.get(url, timeout=5).text
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
        s = Splitter()
        result = s.split(text, split_method="hellwig")
        return [{"word": w, "root": w, "tag": "Segmented"} for w in str(result).split()]
    except:
        return []

# --- UI Setup ---
st.set_page_config(page_title="Sanskrit Parser", page_icon="🕉️")
st.title("🕉️ Sanskrit Multi-Parser")

# --- User Options ---
with st.sidebar:
    st.header("⚙️ Settings")
    script = st.selectbox("Display Script", ["Devanagari", "IAST", "Telugu", "Kannada"])
    model_opt = st.radio("Parser Model", ["Dharmamitra (Morphology)", "Hellwig (Segmentation)"])
    dict_opt = st.radio("Dictionary Lookup", ["Kosha.app", "Ambuda", "SanskritKosha"])

# --- Main Input ---
user_input = st.text_area("Input Sanskrit (Any script):", "मृदुलस्मितांशुलहरीज्योत्स्ना")

if st.button("Parse & Search", type="primary"):
    iast_text = transliterate(user_input, "IAST")
    
    # 1. Parsing
    data = call_dharmamitra(iast_text) if "Dharmamitra" in model_opt else call_hellwig(iast_text)
    
    if data:
        st.subheader("Results")
        # Display as readable items
        for item in data:
            disp_word = transliterate(item['word'], script)
            disp_root = transliterate(item['root'], script)
            
            # Dictionary Routing Logic
            # Dictionaries prefer Devanagari queries for accuracy
            query = transliterate(item['root'], "Devanagari")
            q_enc = urllib.parse.quote(query)
            
            if dict_opt == "Kosha.app":
                link = f"https://kosha.app/?q={q_enc}"
            elif dict_opt == "Ambuda":
                link = f"https://ambuda.org/tools/dictionaries/{q_enc}"
            else:
                link = f"https://sanskritkosha.com/dictionary/{q_enc}"
            
            # Show word with grammar and lookup button
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{disp_word}** ({item['tag']})")
                st.caption(f"Root: {disp_root}")
            with col2:
                st.link_button(f"Open {dict_opt}", link)
    else:
        st.error("Model unavailable. Please try the other parser.")