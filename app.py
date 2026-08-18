import ast
# Patch for Python 3.14+ to prevent Aksharamukha ImportError
if not hasattr(ast, 'Str'):
    ast.Str = ast.Constant
    ast.Num = ast.Constant
    ast.Bytes = ast.Constant
    ast.NameConstant = ast.Constant

import streamlit as st
import requests
import re
import urllib.parse
from aksharamukha import transliterate
import akshara.varnakaarya as vk

# Cloudflare Proxy URL from dharmamitra_ui
API_URL = "https://dharmamitra-proxy.avinash-varna.workers.dev"

AKSHARAMUKHA_SCHEMES = [
    "IAST", "ISO", "Harvard-Kyoto", "SLP1", "ITRANS", "Velthuis", "WX",
    "Devanagari", "Bengali", "Gujarati", "Gurmukhi", "Kannada", "Malayalam", 
    "Oriya", "Tamil", "Telugu", "Brahmi", "Grantha", "Sharada", "Siddham"
]

def preprocess(text):
    text = text.replace("-\n", "")
    text = text.replace("\n", " ")
    text = text.replace("।", "\n")
    text = text.replace("॥", "\n")
    return text

def split_into_lines(text):
    return [s.strip() for s in text.split("\n") if s.strip()]

def call_api(texts):
    # If using a custom Hellwig API endpoint, you could route it here based on st.session_state
    resp = requests.post(
        API_URL,
        json={"texts": texts, "grammar_type": "indic"},
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    resp.raise_for_status()
    return resp.json()

def post_process_tags(word, ml_tags):
    if not ml_tags or not ml_tags.strip():
        return "अव्यय"

    tags = ml_tags
    word_clean = word.strip()
    tags = tags.replace("Mood=साधारण रूप", "")

    if "लोट्)f" in tags and (word_clean.startswith("अ") or word_clean.startswith("आ")):
        tags = tags.replace("आज्ञार्थक (लोट्)f", "लङ्")
        tags = tags.replace("लोट्)f", "लङ्")

    if "Formation=peri" in tags:
        tags = re.sub(r'Tense=[^,|]+', "", tags)
        tags = tags.replace("Formation=peri", "लुट्")
        
    if "Formation=s" in tags:
        tags = re.sub(r'Tense=[^,|]+', "", tags)
        tags = tags.replace("Formation=s", "लुङ्")

    if "Mood=" in tags:
        tags = re.sub(r'Tense=[^,|]+', "", tags)
        if "विधिलिङ्" in tags:
            is_ashirlin = False
            ashirlin_suffixes = ["ियात्", "ीयात्", "ुयात्", "ूयात्", "ेयात्", "ैयात्", "ोयात्", "ौयात्", "ृयात्"]
            if any(word_clean.endswith(s) for s in ashirlin_suffixes):
                is_ashirlin = True
            
            if is_ashirlin:
                tags = tags.replace("Mood=विधिलिङ् (लिङ्)", "आशीर्लिङ्")
                tags = tags.replace("Mood=विधिलिङ्", "आशीर्लिङ्")
            else:
                tags = tags.replace("Mood=विधिलिङ् (लिङ्)", "विधिलिङ्")
                tags = tags.replace("Mood=विधिलिङ्", "विधिलिङ्")

        tags = tags.replace("Mood=आज्ञार्थक (लोट्)", "लोट्")
        tags = re.sub(r'Mood=Con', "लृङ्", tags)
        tags = re.sub(r'Mood=Sub', "लेट्", tags)
        tags = re.sub(r'Mood=Jus', "आशीर्लिङ्", tags)

    if "भूतकाल (लङ्)" in tags:
        if word_clean.startswith("अ") or word_clean.startswith("आ"):
            tags = tags.replace("भूतकाल (लङ्)", "लङ्")
        else:
            tags = tags.replace("भूतकाल (लङ्)", "लिट्")

    tags = tags.replace("वर्तमान (लट्)", "लट्")
    tags = tags.replace("भविष्यत्काल (लृट्)", "लृट्")

    keys_to_strip = ["Tense=", "Mood=", "Formation=", "Number=", "Case=", "Gender=", "Person=", "Voice=", "VerbForm="]
    for key in keys_to_strip:
        tags = tags.replace(key, "")

    tags = re.sub(r'प्रथामा', "प्रथमा", tags)
    tags = re.sub(r'साधारण। रूप', "", tags)
    tags = re.sub(r'is', "", tags)
    tags = re.sub(r'Gdv', "विध्यर्थक कृदन्त", tags)
    tags = re.sub(r'Conv', "पूर्वकालीन कृदन्त", tags)
    tags = re.sub(r'Inf', "हेत्वर्थक कृदन्त", tags)
    tags = re.sub(r'Part', "भूत/वर्तमान कृदन्त", tags)

    tokens = re.split(r'[,|;]+', tags)
    clean_tokens = [t.strip() for t in tokens if t.strip()]

    if "Case=" not in ml_tags:
        atmanepada_suffixes = ["ते", "इते", "न्ते", "से", "ध्वे", "महे", "वहे", "ताम्", "थाः", "ध्वम्", "वहि", "महि", "हे", "ष्ट", "\u0947"]
        is_atmanepada = any(word_clean.endswith(s) for s in atmanepada_suffixes)
        if word_clean.endswith("त") and "एकवचन" in ml_tags:
            is_atmanepada = True
            
        pada = "आत्मनेपद" if is_atmanepada else "परस्मैपद"
        clean_tokens.append(pada)

    final_output = " । ".join(clean_tokens) + " ।"
    return final_output.replace("-", " ")


def get_dict_url(word_dev_encoded, choice):
    if choice == "Ambuda":
        return f"https://ambuda.org/tools/dictionaries/{word_dev_encoded}"
    elif choice == "Sanskrit Kosha":
        return f"https://kosha.sanskrit.today/word/sa/{word_dev_encoded}"
    else:
        return f"https://kosha.app/word/sa/{word_dev_encoded}"

def main():
    st.set_page_config(page_title="सखा - Dharmamitra Analyzer", page_icon="🕉️", layout="wide")

    # --- SIDEBAR SETTINGS ---
    st.sidebar.title("⚙️ Settings")
    model_choice = st.sidebar.selectbox("Model", ["Dharmamitra (Full Analysis)", "Hellwig (Segmentation Only)"])
    dict_choice = st.sidebar.selectbox("Dictionary Website", ["Kosha.app", "Ambuda", "Sanskrit Kosha"])
    
    st.sidebar.markdown("---")
    st.sidebar.caption("Transliteration Preferences")
    input_options = ["Auto-Detect"] + AKSHARAMUKHA_SCHEMES
    input_script_sel = st.sidebar.selectbox("Input Script", input_options, index=0)
    output_script_sel = st.sidebar.selectbox("Output Script", AKSHARAMUKHA_SCHEMES, index=AKSHARAMUKHA_SCHEMES.index("Devanagari"))

    # --- MAIN UI ---
    st.title("सखा - UI for Dharmamitra")
    st.caption("NOTE: AI/ML tools can make mistakes. Please use this as a learning aid.")

    raw_text = st.text_area("Enter Sanskrit text (e.g. वाग्देव्यै नमः)", height=100)

    if st.button("Analyze", type="primary"):
        if not raw_text.strip():
            st.error("Please enter some Sanskrit text.")
            return

        with st.spinner(f"Analyzing with {model_choice.split()[0]}..."):
            try:
                # 1. Transliteration Setup
                if input_script_sel == "Auto-Detect":
                    detected_script = transliterate.auto_detect(raw_text)
                    input_script = detected_script if detected_script else "IAST"
                else:
                    input_script = input_script_sel

                iast_text = transliterate.process(input_script, "IAST", raw_text)
                dev_text = transliterate.process(input_script, "Devanagari", raw_text)
                
                # 2. Akshara Analysis (Collapsible)
                with st.expander("🔤 Varna & Akshara Analysis (Powered by Akshara)", expanded=False):
                    try:
                        vinyaasa = vk.get_vinyaasa(dev_text)
                        aksharas = vk.get_akshara(dev_text)
                        st.markdown(f"**Syllables (Akshara):** `{', '.join(aksharas)}`")
                        st.markdown(f"**Spelling Breakdown (Vinyaasa):** `{', '.join(vinyaasa)}`")
                        
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Svaras (Vowels)", vk.count_svaras(dev_text))
                        c2.metric("Vyanjanas (Consonants)", vk.count_vyanjanas(dev_text))
                        c3.metric("Total Varnas", vk.count_varnas(dev_text))
                    except Exception as e:
                        st.warning(f"Akshara analysis could not process this string entirely. ({e})")

                # 3. API Processing
                texts = split_into_lines(preprocess(iast_text))
                if not texts:
                    return
                
                data = call_api(texts)
                
                # 4. Extract Grammatical Data
                all_unsandhied = []
                all_lemmas = []
                all_tags = []
                
                for j in range(len(texts)):
                    entry = data[j] if j < len(data) else {}
                    gram_analysis = entry.get("grammatical_analysis", [])
                    
                    for g in gram_analysis:
                        all_unsandhied.append(g.get("unsandhied", "").rstrip("-"))
                        all_lemmas.append(g.get("lemma", "").rstrip("-"))
                        all_tags.append(g.get("tag", ""))
                        
                def to_output(txt):
                    return transliterate.process("IAST", output_script_sel, txt)
                    
                def to_dev(txt):
                    return transliterate.process("IAST", "Devanagari", txt)
                
                # Main Segmentation Output (Copiable)
                st.subheader("Padaccheda (Segmentation)")
                seg_output = " ".join(to_output(u) for u in all_unsandhied)
                st.code(seg_output, language="text") # st.code allows one-click copy on hover!
                
                # Render table ONLY if Dharmamitra is selected
                if "Hellwig" not in model_choice:
                    st.subheader("Word Analysis")
                    table_html = "<div style='overflow-x:auto;'><table style='width:100%; border-collapse: collapse;'>"
                    table_html += "<tr><th style='text-align:left; border-bottom:1px solid #e5e5e5; padding:10px;'>#</th>"
                    table_html += "<th style='text-align:left; border-bottom:1px solid #e5e5e5; padding:10px;'>Word</th>"
                    table_html += "<th style='text-align:left; border-bottom:1px solid #e5e5e5; padding:10px;'>Lemma</th>"
                    table_html += "<th style='text-align:left; border-bottom:1px solid #e5e5e5; padding:10px;'>Grammar</th></tr>"
                    
                    for i in range(len(all_unsandhied)):
                        uns_out = to_output(all_unsandhied[i])
                        lem_out = to_output(all_lemmas[i])
                        uns_dev = to_dev(all_unsandhied[i])
                        lem_dev = to_dev(all_lemmas[i])
                        
                        tag_result = post_process_tags(uns_dev, all_tags[i])
                        if output_script_sel != "Devanagari":
                            tag_result = transliterate.process("Devanagari", output_script_sel, tag_result)
                            
                        uns_dev_encoded = urllib.parse.quote(uns_dev)
                        lem_dev_encoded = urllib.parse.quote(lem_dev)
                        
                        # Apply Dictionary routing logic
                        lemma_link = get_dict_url(lem_dev_encoded, dict_choice)
                        lemma_html = f'<a href="{lemma_link}" target="_blank" style="text-decoration:none; color:#1d4ed8;">{lem_out}</a>'
                        
                        is_verb = any(x in all_tags[i] for x in ["Tense=", "Mood=", "VerbForm"])
                        word_html = f'<a href="https://ashtadhyayi.com/dhatu?search={uns_dev_encoded}" target="_blank" style="text-decoration:none; color:#1d4ed8;">{uns_out}</a>' if is_verb else uns_out
                        
                        table_html += f"<tr><td style='border-bottom:1px solid #eee; padding:10px;'>{i+1}</td>"
                        table_html += f"<td style='border-bottom:1px solid #eee; padding:10px;'>{word_html}</td>"
                        table_html += f"<td style='border-bottom:1px solid #eee; padding:10px;'>{lemma_html}</td>"
                        table_html += f"<td style='border-bottom:1px solid #eee; padding:10px;'>{tag_result}</td></tr>"
                        
                    table_html += "</table></div>"
                    st.markdown(table_html, unsafe_allow_html=True)
                else:
                    st.info("Hellwig mode active: Skipping morphological/lemma analysis. Showing segmentation only.")
                
            except Exception as e:
                st.error(f"Analysis failed: {e}")

    # --- COLLAPSIBLE FOOTER ---
    st.markdown("---")
    with st.expander("🔗 Try these too", expanded=False):
        st.markdown("""
        * 🧮 [**Sankhya**](https://sankhya.streamlit.app) - Sanskrit Numerals Converter
        * 🧩 [**Sandhify**](https://sandhify.streamlit.app) - Sandhi Joiner/Splitter
        * 📰 [**Sanskrit News**](https://sanskritnews.streamlit.app) - Daily News Reader
        * 📚 [**Annotated List of Sanskrit Websites**](https://anotepad.com/note/read/qx4598pk)
        """)

if __name__ == "__main__":
    main()
