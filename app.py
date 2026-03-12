import streamlit as st
import requests
import urllib.parse
import streamlit.components.v1 as components

# --- State Initialization ---
# This is crucial to prevent results from disappearing when a widget is changed.
if 'parsed_data' not in st.session_state:
    st.session_state.parsed_data = []

# --- Helpers ---
def transliterate(text, target="IAST"):
    """Converts script using Aksharamukha."""
    if not text: return ""
    url = f"https://api.aksharamukha.com/api/public/process?target={target}&text={urllib.parse.quote(text)}"
    try:
        res = requests.get(url, timeout=10)
        return res.text if res.status_code == 200 else text
    except:
        return text

# --- Models ---
def call_dharmamitra(text):
    """Dharmamitra (Byte5) - using the confirmed working curl payload."""
    url = "https://dharmamitra.org/api-tagging/tagging-parsed/"
    # The 'western' grammar_type is the stable one. "Byte5" refers to their backend engine.
    payload = {"texts": [text], "grammar_type": "western"}
    try:
        res = requests.post(url, json=payload, timeout=15)
        res.raise_for_status()
        data = res.json()
        if data and isinstance(data, list) and len(data) > 0:
            tokens = data[0].get('words', [])
            return [{"word": t['form'], "root": t['lemma'], "tag": t.get('morphs', '')} for t in tokens]
        return []
    except Exception as e:
        st.sidebar.error(f"Dharmamitra Error: {e}")
        return []

def call_hellwig(text):
    """Hellwig (2018) via Skrutable. Skrutable library must be installed."""
    try:
        from skrutable.splitting import Splitter
        s = Splitter()
        result = s.split(text, splitter_model='splitter_2018')
        return [{"word": w} for w in str(result).split()]
    except Exception as e:
        st.sidebar.error(f"Hellwig/Skrutable Error: {e}")
        return []

# --- UI Setup ---
st.set_page_config(page_title="The Sanskrit Parser", layout="wide")
st.title("The Sanskrit Parser")

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Settings")
    model_opt = st.radio("Parser Model", ["Dharmamitra (Byte5)", "Hellwig (2018)"])
    dict_opt = st.radio("Dictionary for Preview", ["Kosha.app", "Ambuda", "SanskritKosha"])
    st.info("Output is always in Devanagari for clarity and dictionary compatibility.")

# --- Main Interface ---
user_input = st.text_area("Input Sanskrit (any script):", "mṛdulasmitāṃśulaharījyotsnā")

if st.button("Parse Text", type="primary"):
    # 1. Standardize input to IAST for models
    iast_input = transliterate(user_input, "IAST")
    
    # 2. Run selected Model and store results in session_state
    is_hellwig = "Hellwig" in model_opt
    if not is_hellwig:
        with st.spinner("Parsing with Dharmamitra..."):
            st.session_state.parsed_data = call_dharmamitra(iast_input)
    else:
        with st.spinner("Segmenting with Hellwig..."):
            st.session_state.parsed_data = call_hellwig(iast_input)
    
    # After parsing, clear previous selections if any, to prevent errors
    if 'selected_word_idx' in st.session_state:
        del st.session_state.selected_word_idx

# --- Display Results (This block runs independently of the button) ---
if st.session_state.parsed_data:
    st.subheader("Results")
    
    # All display and lookup words are converted to Devanagari
    word_labels = [transliterate(item['word'], "Devanagari") for item in st.session_state.parsed_data]
    
    # Using session_state to remember the selection
    selected_word_idx = st.selectbox(
        "Select a word to preview in dictionary:", 
        range(len(word_labels)), 
        format_func=lambda x: word_labels[x],
        key='selected_word_idx' # Key to store the index in session_state
    )
    
    selected_item = st.session_state.parsed_data[selected_word_idx]
    
    # Display Word Info
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Selected Word", word_labels[selected_word_idx])
    with col2:
        if 'root' in selected_item: # Check if the key exists (i.e., not Hellwig)
            st.write(f"**Root:** {transliterate(selected_item['root'], 'Devanagari')}")
            st.write(f"**Grammar:** {selected_item['tag']}")
        else:
            st.write("*Hellwig model provides segmentation only.*")

    st.divider()

    # 3. Dictionary Preview (Internal Iframe)
    # Search term is the root for Dharmamitra, or the word itself for Hellwig
    search_term_iast = selected_item.get('root', selected_item.get('word'))
    devanagari_query = transliterate(search_term_iast, "Devanagari")
    q_enc = urllib.parse.quote(devanagari_query)

    # Building the correct dictionary URL
    if dict_opt == "Ambuda":
        # Using the new, correct Ambuda URL
        dict_url = f"https://ambuda.org/tools/dictionaries/apte-sh,shabdartha-kaustubha,shabdakalpadruma,apte,mw,shabdasagara,vacaspatyam,amara/{q_enc}"
    elif dict_opt == "Kosha.app":
        dict_url = f"https://kosha.app/?q={q_enc}"
    else:
        dict_url = f"https://sanskritkosha.com/dictionary/{q_enc}"

    st.write(f"🔗 [Open {dict_opt} in new tab]({dict_url})")
    
    # Attempting Iframe Preview
    components.iframe(dict_url, height=600, scrolling=True)

# If the button has not been pressed and there's no data, show a message.
elif not user_input:
    st.info("Please enter some Sanskrit text and click 'Parse Text'.")
