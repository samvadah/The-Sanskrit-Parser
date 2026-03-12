import streamlit as st
import requests
import urllib.parse
import streamlit.components.v1 as components

# --- State Initialization ---
# Prevents UI from resetting when a widget is changed.
if 'parsed_data' not in st.session_state:
    st.session_state.parsed_data = []

# --- Helpers ---
def transliterate(text, target="Devanagari"):
    """Converts script using Aksharamukha. Defaults to Devanagari."""
    if not text: return ""
    url = f"https://api.aksharamukha.com/api/public/process?target={target}&text={urllib.parse.quote(text)}"
    try:
        res = requests.get(url, timeout=10)
        return res.text if res.status_code == 200 else text
    except:
        return text

# --- Models ---
def call_dharmamitra(iast_text):
    """Dharmamitra (Byte5) - using the stable 'western' grammar type."""
    url = "https://dharmamitra.org/api-tagging/tagging-parsed/"
    payload = {"texts": [iast_text], "grammar_type": "western"}
    try:
        res = requests.post(url, json=payload, timeout=15)
        res.raise_for_status() # This will raise an error for 4xx or 5xx responses
        data = res.json()
        if data and data[0].get('words'):
            tokens = data[0]['words']
            return [{"word": t['form'], "root": t['lemma'], "tag": t.get('morphs', '')} for t in tokens]
        return []
    except Exception as e:
        st.sidebar.error(f"Dharmamitra Error: Could not connect or process. Details: {e}")
        return []

def call_hellwig(iast_text):
    """Hellwig (2018) via Skrutable. Corrected based on source code."""
    try:
        from skrutable.splitting import Splitter
        # Correct Usage: Model is specified during initialization.
        s = Splitter(splitter_model="splitter_2018")
        result = s.split(iast_text)
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
    st.info("Output is permanently set to Devanagari for dictionary compatibility.")

# --- Main Interface ---
user_input = st.text_area("Input Sanskrit (any script):", "mṛdulasmitāṃśulaharījyotsnā")

if st.button("Parse Text", type="primary"):
    # Always convert input to IAST for the models
    iast_input = transliterate(user_input, "IAST")
    
    # Run selected Model and save results to prevent them from disappearing
    if "Dharmamitra" in model_opt:
        st.session_state.parsed_data = call_dharmamitra(iast_input)
    else:
        st.session_state.parsed_data = call_hellwig(iast_input)
    
    # Clear previous selection index to avoid errors
    if 'selected_word_idx' in st.session_state:
        del st.session_state.selected_word_idx

# --- Display Results ---
if st.session_state.parsed_data:
    st.subheader("Results")
    
    # All display words are now hardcoded to Devanagari
    word_labels = [transliterate(item['word'], "Devanagari") for item in st.session_state.parsed_data]
    
    selected_word_idx = st.selectbox(
        "Select a parsed word for dictionary lookup:", 
        range(len(word_labels)), 
        format_func=lambda x: word_labels[x],
        key='selected_word_idx'
    )
    
    selected_item = st.session_state.parsed_data[selected_word_idx]
    
    # Display Word Info
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Selected Word", word_labels[selected_word_idx])
    with col2:
        if 'root' in selected_item: # This correctly identifies Dharmamitra's output
            st.write(f"**Root:** {transliterate(selected_item['root'], 'Devanagari')}")
            st.write(f"**Grammar:** {selected_item['tag']}")
        else:
            st.write("*(Segmentation only)*")

    st.divider()

    # --- Dictionary Preview ---
    # Determine the search term (root for Dharmamitra, word for Hellwig)
    search_term_iast = selected_item.get('root') or selected_item.get('word')
    devanagari_query = transliterate(search_term_iast, "Devanagari")
    q_enc = urllib.parse.quote(devanagari_query)

    # Build dictionary URLs with corrected formats
    if dict_opt == "Kosha.app":
        # Using the new, correct Kosha.app URL format
        dict_url = f"https://kosha.app/word/sa/{q_enc}"
    elif dict_opt == "Ambuda":
        dict_url = f"https://ambuda.org/tools/dictionaries/apte-sh,shabdartha-kaustubha,shabdakalpadruma,apte,mw,shabdasagara,vacaspatyam,amara/{q_enc}"
    else:
        dict_url = f"https://sanskritkosha.com/dictionary/{q_enc}"

    st.write(f"🔗 [Open {dict_opt} in new tab]({dict_url})")
    
    # Iframe for preview
    components.iframe(dict_url, height=600, scrolling=True)

elif not user_input:
    st.info("Enter Sanskrit text above and click 'Parse Text'.")
