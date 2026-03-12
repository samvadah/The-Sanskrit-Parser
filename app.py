import streamlit as st
import requests
import urllib.parse

# Safe Import for Skrutable
try:
    from skrutable.splitting import Splitter
except ImportError:
    Splitter = None

# --- Helpers ---
def transliterate(text, target="IAST"):
    """Auto-detects script and converts to target using Aksharamukha."""
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
    # Payload changed to 'western' to fix the 422 error
    payload = {
        "texts": [text], 
        "grammar_type": "western" 
    }
    headers = {"Content-Type": "application/json"}
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=15)
        res.raise_for_status()
        data = res.json()
        if data and isinstance(data, list) and len(data) > 0:
            words = data[0].get('words', data[0].get('tokens', []))
            return [{"word": t['form'], "root": t['lemma'], "tag": t.get('morphs', 'N/A')} for t in words]
        return []
    except Exception as e:
        st.sidebar.error(f"Dharmamitra Error: {e}")
        return []

def call_hellwig(text):
    """Hellwig (2018) via Skrutable Remote API"""
    if Splitter is None:
        st.error("Skrutable library missing.")
        return []
    
    try:
        # Initialize Splitter (v2.x method)
        s = Splitter()
        # In Skrutable v2.x, use splitter_model='splitter_2018' instead of split_method
        result = s.split(text, splitter_model='splitter_2018')
        return [{"word": w, "root": w, "tag": "Segmented"} for w in str(result).split()]
    except Exception as e:
        st.sidebar.error(f"Hellwig Error: {e}")
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
    with st.spinner("Transliterating..."):
        iast_text = transliterate(user_input, "IAST")
    
    data = []
    if "Dharmamitra" in model_opt:
        with st.spinner("Fetching from Dharmamitra (Byte5)..."):
            data = call_dharmamitra(iast_text)
    else:
        with st.spinner("Fetching from Hellwig (2018)..."):
            data = call_hellwig(iast_text)
    
    if data:
        st.subheader("Results")
        for item in data:
            disp_word = transliterate(item['word'], script)
            disp_root = transliterate(item['root'], script)
            
            # Prepare search query in Devanagari
            query = transliterate(item['root'], "Devanagari")
            q_enc = urllib.parse.quote(query)
            
            if dict_opt == "Kosha.app":
                link = f"https://kosha.app/?q={q_enc}"
            elif dict_opt == "Ambuda":
                link = f"https://ambuda.org/tools/dictionaries/{q_enc}"
            else:
                link = f"https://sanskritkosha.com/dictionary/{q_enc}"
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{disp_word}**")
                st.caption(f"Root: {disp_root} | Tag: {item['tag']}")
            with col2:
                st.link_button(f"Lookup", link)
    else:
        st.error("No results found. Check sidebar for errors.")
