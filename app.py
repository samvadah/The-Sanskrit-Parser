import streamlit as st
import requests
import urllib.parse
import streamlit.components.v1 as components

# Safe Import for Skrutable
try:
    from skrutable.splitting import Splitter
except ImportError:
    Splitter = None

# --- Helpers ---
def transliterate(text, target="IAST"):
    """Converts script using Aksharamukha. Targets: 'Devanagari', 'IAST', 'Telugu', 'Kannada'."""
    if not text: return ""
    # Aksharamukha API expects specific casing for script names
    url = f"https://api.aksharamukha.com/api/public/process?target={target}&text={urllib.parse.quote(text)}"
    try:
        res = requests.get(url, timeout=5)
        return res.text if res.status_code == 200 else text
    except:
        return text

# --- Models ---
def call_dharmamitra(text):
    """Dharmamitra (Byte5) - Matches working curl exactly"""
    url = "https://dharmamitra.org/api-tagging/tagging-parsed/"
    payload = {"texts": [text], "grammar_type": "western"}
    try:
        # Explicitly using json= sets Content-Type to application/json
        res = requests.post(url, json=payload, timeout=15)
        res.raise_for_status()
        data = res.json()
        if data and isinstance(data, list) and len(data) > 0:
            tokens = data[0].get('words', data[0].get('tokens', []))
            return [{"word": t['form'], "root": t['lemma'], "tag": t.get('morphs', '')} for t in tokens]
        return []
    except Exception as e:
        st.sidebar.error(f"Dharmamitra Error: {e}")
        return []

def call_hellwig(text):
    """Hellwig (2018) via Skrutable"""
    if Splitter is None: return []
    try:
        s = Splitter()
        result = s.split(text, splitter_model='splitter_2018')
        # Hellwig only returns segmented strings, no roots or tags
        return [{"word": w} for w in str(result).split()]
    except Exception as e:
        st.sidebar.error(f"Hellwig Error: {e}")
        return []

# --- UI Setup ---
st.set_page_config(page_title="The Sanskrit Parser", layout="wide")
st.title("The Sanskrit Parser")

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Settings")
    script_opt = st.selectbox("Display Script", ["Devanagari", "IAST", "Telugu", "Kannada"])
    model_opt = st.radio("Parser Model", ["Dharmamitra (Byte5)", "Hellwig (2018)"])
    dict_opt = st.radio("Dictionary for Preview", ["Kosha.app", "Ambuda", "SanskritKosha"])
    st.info("Note: Some dictionaries may block internal previews. Use the link provided if the box below is empty.")

# --- Main Interface ---
user_input = st.text_area("Input Sanskrit:", "मृदुलस्मितांशुलहरीज्योत्स्ना")

if st.button("Parse & Preview", type="primary"):
    # 1. Standardize input to IAST for models
    iast_input = transliterate(user_input, "IAST")
    
    # 2. Run selected Model
    is_hellwig = "Hellwig" in model_opt
    if not is_hellwig:
        with st.spinner("Parsing with Dharmamitra..."):
            data = call_dharmamitra(iast_input)
    else:
        with st.spinner("Segmenting with Hellwig..."):
            data = call_hellwig(iast_input)
    
    if data:
        st.subheader("Results")
        
        # We use a selection system for the dictionary preview
        word_labels = [transliterate(item['word'], script_opt) for item in data]
        selected_word_idx = st.selectbox("Select a word to preview in dictionary:", range(len(word_labels)), format_func=lambda x: word_labels[x])
        
        selected_item = data[selected_word_idx]
        
        # Display Word Info
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Selected Word", word_labels[selected_word_idx])
        with col2:
            if not is_hellwig:
                disp_root = transliterate(selected_item['root'], script_opt)
                st.write(f"**Root:** {disp_root}")
                st.write(f"**Grammar:** {selected_item['tag']}")
            else:
                st.write("*Hellwig model provides segmentation only.*")

        st.divider()

        # 3. Dictionary Preview (Internal Iframe)
        # Dictionary lookups MUST be in Devanagari
        # For Dharmamitra we search the Root; for Hellwig we search the Segmented Word
        search_term = selected_item['root'] if not is_hellwig else selected_item['word']
        devanagari_query = transliterate(search_term, "Devanagari")
        q_enc = urllib.parse.quote(devanagari_query)

        if dict_opt == "Kosha.app":
            dict_url = f"https://kosha.app/?q={q_enc}"
        elif dict_opt == "Ambuda":
            dict_url = f"https://ambuda.org/tools/dictionaries/{q_enc}"
        else:
            dict_url = f"https://sanskritkosha.com/dictionary/{q_enc}"

        st.write(f"🔗 [Open {dict_opt} in new tab]({dict_url})")
        
        # Attempting Iframe Preview
        try:
            components.iframe(dict_url, height=600, scrolling=True)
        except:
            st.warning("This dictionary does not allow internal previews. Please use the link above.")

    else:
        st.error("No results found. Please check your connection or try the other model.")
