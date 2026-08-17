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

# ... [rest of your code remains exactly the same] ...
import streamlit as st
import requests
import re
import urllib.parse
from aksharamukha import transliterate

# Cloudflare Proxy URL from dharmamitra_ui
API_URL = "https://dharmamitra-proxy.avinash-varna.workers.dev"

# Complete list of scripts supported by Aksharamukha
AKSHARAMUKHA_SCHEMES = [
    "IAST", "ISO", "Harvard-Kyoto", "SLP1", "ITRANS", "Velthuis", "WX",
    "Devanagari", "Bengali", "Gujarati", "Gurmukhi", "Kannada", "Malayalam", 
    "Oriya", "Tamil", "Telugu", "Assamese", "Manipuri", "Brahmi", "Grantha", 
    "Kharoshthi", "Siddham", "Sharada", "Newa", "Modi", "Mahajani", "Multani", 
    "Takri", "Dogra", "Tirhuta", "Ranjana", "Khudawadi", "Ahom", "Bhaiksuki", 
    "Burmese", "Cham", "Javanese", "Khmer", "KhomThai", "Lao", "Mon", "Thai", 
    "Tibetan", "Balinese", "PhagsPa", "Lepcha", "Limbu", "Santali", "SoraSompeng", 
    "Wancho", "WarangCiti", "ZanabazarSquare", "Marchen", "Cyrillic", "Avestan", 
    "OldPersian", "Urdu", "Sinhala"
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
            ashirlin_suffixes = [
                "ियात्", "ीयात्", "ुयात्", "ूयात्",
                "ेयात्", "ैयात्", "ोयात्", "ौयात्", "ृयात्"
            ]
            for suffix in ashirlin_suffixes:
                if word_clean.endswith(suffix):
                    is_ashirlin = True
                    break
            
            if is_ashirlin:
                tags = tags.replace("Mood=विधिलिङ् (लिङ्)", "आशीर्लिङ्")
                tags = tags.replace("Mood=विधिलिङ्", "आशीर्लिङ्")
            else:
                tags = tags.replace("Mood=विधिलिङ् (लिङ्)", "विधिलिङ्")
                tags = tags.replace("Mood=विधिलिङ्", "विधिलिङ्")
                tags = tags.replace("Mood=आशीर्लिङ् (लिङ्)", "विधिलिङ्")
                tags = tags.replace("Mood=आशीर्लिङ्", "विधिलिङ्")

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
        atmanepada_suffixes = [
            "ते", "इते", "न्ते", "से", "ध्वे", "महे", "वहे",
            "ताम्", "थाः", "ध्वम्", "वहि", "महि", "हे", "ष्ट",
            "\u0947"
        ]
        is_atmanepada = any(word_clean.endswith(s) for s in atmanepada_suffixes)
        
        if word_clean.endswith("त") and "एकवचन" in ml_tags:
            is_atmanepada = True
            
        pada = "आत्मनेपद" if is_atmanepada else "परस्मैपद"
        clean_tokens.append(pada)

    final_output = " । ".join(clean_tokens) + " ।"
    final_output = final_output.replace("-", " ")
    
    return final_output


def main():
    st.set_page_config(page_title="सखा - Dharmamitra Analyzer (Aksharamukha)", page_icon="🕉️", layout="wide")

    st.title("सखा - UI for Dharmamitra")
    st.markdown("**Sanskrit Grammatical Analyzer with Aksharamukha Transliteration**")
    st.caption("NOTE: Dharmamitra is AI/ML and can make mistakes. Please use this as a learning tool only.")

    raw_text = st.text_area("Enter Sanskrit text (e.g. वाग्देव्यै नमः or vāgdevyai namaḥ)", height=140)

    col1, col2 = st.columns(2)
    with col1:
        input_options = ["Auto-Detect"] + AKSHARAMUKHA_SCHEMES
        input_script_sel = st.selectbox("Input Script / Scheme", input_options, index=0)

    with col2:
        default_idx = AKSHARAMUKHA_SCHEMES.index("Devanagari")
        output_script_sel = st.selectbox("Output Script / Scheme", AKSHARAMUKHA_SCHEMES, index=default_idx)

    if st.button("Analyze", type="primary"):
        if not raw_text.strip():
            st.error("Please enter some Sanskrit text.")
            return

        with st.spinner("Analyzing with Aksharamukha & Dharmamitra..."):
            try:
                # 1. Detect or map input script via Aksharamukha
                if input_script_sel == "Auto-Detect":
                    detected_script = transliterate.auto_detect(raw_text)
                    input_script = detected_script if detected_script else "IAST"
                    st.info(f"Detected Input Script: **{input_script}**")
                else:
                    input_script = input_script_sel

                # 2. Transliterate to IAST for the Dharmamitra backend
                iast_text = transliterate.process(input_script, "IAST", raw_text)
                
                # 3. Preprocess and split
                preprocessed = preprocess(iast_text)
                texts = split_into_lines(preprocessed)
                
                if not texts:
                    st.error("No valid text to analyze.")
                    return
                
                # 4. Call Dharmamitra API
                data = call_api(texts)
                
                # 5. Process grammatical analysis
                warning = False
                all_unsandhied = []
                all_lemmas = []
                all_tags = []
                
                for j, orig in enumerate(texts):
                    entry = data[j] if j < len(data) else {}
                    gram_analysis = entry.get("grammatical_analysis", [])
                    
                    unsandhied_parts = []
                    for g in gram_analysis:
                        u_val = g.get("unsandhied", "").rstrip("-")
                        l_val = g.get("lemma", "").rstrip("-")
                        t_val = g.get("tag", "")
                        
                        all_unsandhied.append(u_val)
                        all_lemmas.append(l_val)
                        all_tags.append(t_val)
                        unsandhied_parts.append(u_val)
                        
                    unsandhied_joined = " ".join(unsandhied_parts)
                    if len(orig) > len(unsandhied_joined):
                        warning = True
                        
                if not all_unsandhied:
                    st.error("No grammatical analysis returned. Try a different input.")
                    return
                
                if warning:
                    st.warning("Some words may have been lost during sandhi segmentation.")
                    
                # Aksharamukha conversion helpers
                def to_output(txt):
                    return transliterate.process("IAST", output_script_sel, txt)
                    
                def to_devanagari(txt):
                    return transliterate.process("IAST", "Devanagari", txt)
                
                st.subheader("Input")
                st.info(" ".join(to_output(t) for t in texts))
                
                st.subheader("Padaccheda (Segmentation)")
                st.info(" ".join(to_output(u) for u in all_unsandhied))
                
                st.subheader("Word Analysis")
                
                # Render table
                table_html = "<div style='overflow-x:auto;'><table style='width:100%; border-collapse: collapse;'>"
                table_html += "<tr><th style='text-align:left; border-bottom:1px solid #e5e5e5; padding:10px;'>#</th>"
                table_html += "<th style='text-align:left; border-bottom:1px solid #e5e5e5; padding:10px;'>Word</th>"
                table_html += "<th style='text-align:left; border-bottom:1px solid #e5e5e5; padding:10px;'>Lemma</th>"
                table_html += "<th style='text-align:left; border-bottom:1px solid #e5e5e5; padding:10px;'>Grammar</th></tr>"
                
                for i in range(len(all_unsandhied)):
                    uns_out = to_output(all_unsandhied[i])
                    lem_out = to_output(all_lemmas[i])
                    
                    uns_dev = to_devanagari(all_unsandhied[i])
                    lem_dev = to_devanagari(all_lemmas[i])
                    raw_tag = all_tags[i]
                    
                    tag_result = post_process_tags(uns_dev, raw_tag)
                    if output_script_sel != "Devanagari":
                        tag_result = transliterate.process("Devanagari", output_script_sel, tag_result)
                        
                    uns_dev_encoded = urllib.parse.quote(uns_dev)
                    lem_dev_encoded = urllib.parse.quote(lem_dev)
                    
                    is_verb = any(x in raw_tag for x in ["Tense=", "Mood=", "VerbForm"])
                    if is_verb:
                        word_html = f'<a href="https://ashtadhyayi.com/dhatu?search={uns_dev_encoded}" target="_blank" style="text-decoration:none; color:#1d4ed8;">{uns_out}</a>'
                    else:
                        word_html = uns_out
                        
                    lemma_html = f'<a href="https://kosha.app/word/sa/{lem_dev_encoded}" target="_blank" style="text-decoration:none; color:#1d4ed8;">{lem_out}</a>'
                    
                    table_html += f"<tr><td style='border-bottom:1px solid #eee; padding:10px;'>{i+1}</td>"
                    table_html += f"<td style='border-bottom:1px solid #eee; padding:10px;'>{word_html}</td>"
                    table_html += f"<td style='border-bottom:1px solid #eee; padding:10px;'>{lemma_html}</td>"
                    table_html += f"<td style='border-bottom:1px solid #eee; padding:10px;'>{tag_result}</td></tr>"
                    
                table_html += "</table></div>"
                st.markdown(table_html, unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"Analysis failed: {e}. Check your connection or input.")
                
    st.markdown("---")
    st.markdown('''
        <div style="text-align: center; font-size: 0.8rem; color: #6b7280;">
            Powered by <a href="https://dharmamitra.org" target="_blank" rel="noopener">Dharmamitra</a>
            &middot; Transliteration by <a href="https://github.com/virtualvinodh/aksharamukha" target="_blank" rel="noopener">Aksharamukha</a>
        </div>
    ''', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
