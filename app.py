import streamlit as st
import requests
import re
import urllib.parse
from indic_transliteration import sanscript, detect

# API Backend from app.js
API_URL = "https://dharmamitra-proxy.avinash-varna.workers.dev"
DETECT_TO_SCHEME = {"kolkata": "kolkata_v2", "slp": "slp1"}

def format_scheme(s):
    return s.replace("_", " ").title()

def normalize_script(name):
    if not name:
        return sanscript.IAST
    name = name.lower()
    return DETECT_TO_SCHEME.get(name, name)

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

    # CORRECTED: Delete "Mood=साधारण रूप" FIRST to protect standard Tenses
    tags = tags.replace("Mood=साधारण रूप", "")

    # RULE 5: Patch Pipeline Typos & Hallucinations
    if "लोट्)f" in tags and (word_clean.startswith("अ") or word_clean.startswith("आ")):
        tags = tags.replace("आज्ञार्थक (लोट्)f", "लङ्")
        tags = tags.replace("लोट्)f", "लङ्")

    # RULE 2: Disambiguate "Formation" Tags into True Lakāras
    if "Formation=peri" in tags:
        tags = re.sub(r'Tense=[^,|]+', "", tags)
        tags = tags.replace("Formation=peri", "लुट्")
        
    if "Formation=s" in tags:
        tags = re.sub(r'Tense=[^,|]+', "", tags)
        tags = tags.replace("Formation=s", "लुङ्")

    # RULE 3: Override Nonsensical "Tense + Mood" Combinations
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

        # Apply specific Mood overrides
        tags = tags.replace("Mood=आज्ञार्थक (लोट्)", "लोट्")
        tags = re.sub(r'Mood=Con', "लृङ्", tags)
        tags = re.sub(r'Mood=Sub', "लेट्", tags)
        tags = re.sub(r'Mood=Jus', "आशीर्लिङ्", tags)

    # RULE 4: Disambiguate Overlapped Past Tenses (लङ् vs. लिट्)
    if "भूतकाल (लङ्)" in tags:
        if word_clean.startswith("अ") or word_clean.startswith("आ"):
            tags = tags.replace("भूतकाल (लङ्)", "लङ्")
        else:
            tags = tags.replace("भूतकाल (लङ्)", "लिट्")

    # Explicitly map the remaining base tenses
    tags = tags.replace("वर्तमान (लट्)", "लट्")
    tags = tags.replace("भविष्यत्काल (लृट्)", "लृट्")

    # RULE 7: Format Stripping (Strip out all English keys, keep Devanagari values)
    keys_to_strip = ["Tense=", "Mood=", "Formation=", "Number=", "Case=", "Gender=", "Person=", "Voice=", "VerbForm="]
    for key in keys_to_strip:
        tags = tags.replace(key, "")

    # Additional cleanup 
    tags = re.sub(r'प्रथामा', "प्रथमा", tags) # Fix API typo
    tags = re.sub(r'साधारण। रूप', "", tags)   # Clean up remnants with danda separator
    tags = re.sub(r'is', "", tags)           # Remove stray "is" text

    # VerbForm replacements 
    tags = re.sub(r'Gdv', "विध्यर्थक कृदन्त", tags)
    tags = re.sub(r'Conv', "पूर्वकालीन कृदन्त", tags)
    tags = re.sub(r'Inf', "हेत्वर्थक कृदन्त", tags)
    tags = re.sub(r'Part', "भूत/वर्तमान कृदन्त", tags)

    # Tokenize the remaining string (split on comma/pipe/semicolon only, NOT spaces)
    tokens = re.split(r'[,|;]+', tags)
    clean_tokens = [t.strip() for t in tokens if t.strip()]

    # RULE 1: Fix Missing "Voice" (Pada) via Suffix Heuristics
    if "Case=" not in ml_tags:
        atmanepada_suffixes = [
            "ते", "इते", "न्ते", "से", "ध्वे", "महे", "वहे",
            "ताम्", "थाः", "ध्वम्", "वहि", "महि", "हे", "ष्ट",
            "\u0947" # e-matra, catches words like चक्रे
        ]
        is_atmanepada = any(word_clean.endswith(s) for s in atmanepada_suffixes)
        
        # Conditionally check 'त' for singular forms like अकुरुत
        if word_clean.endswith("त") and "एकवचन" in ml_tags:
            is_atmanepada = True
            
        pada = "आत्मनेपद" if is_atmanepada else "परस्मैपद"
        clean_tokens.append(pada)

    # Compile the final string formatted with Devanagari Dandas
    final_output = " । ".join(clean_tokens) + " ।"
    
    # Hyphens to spaces
    final_output = final_output.replace("-", " ")
    
    return final_output


def main():
    st.set_page_config(page_title="सखा - UI for Dharmamitra Sanskrit Analyzer", page_icon="🕉️", layout="wide")

    st.title("सखा - UI for Dharmamitra")
    st.markdown("**Sanskrit Grammatical Analyzer**")
    st.caption("NOTE: Dharmamitra is AI/ML and can make mistakes. Please use this as a learning tool only.")

    raw_text = st.text_area("Enter Sanskrit text (e.g. वाग्देव्यै नमः or vāgdevyai namaḥ)", height=150)

    # Get available scripts directly from indic-transliteration
    schemes = list(sanscript.SCHEMES.keys())

    col1, col2 = st.columns(2)
    with col1:
        input_schemes = ["autodetect"] + schemes
        input_script_sel = st.selectbox("Input Transliteration", input_schemes, format_func=format_scheme, index=0)

    with col2:
        output_schemes = schemes
        # Default to devanagari if exists
        default_out_idx = output_schemes.index(sanscript.DEVANAGARI) if sanscript.DEVANAGARI in output_schemes else 0
        output_script_sel = st.selectbox("Output Transliteration", output_schemes, format_func=format_scheme, index=default_out_idx)

    if st.button("Analyze", type="primary"):
        if not raw_text.strip():
            st.error("Please enter some Sanskrit text.")
            return

        with st.spinner("Analyzing..."):
            try:
                # 1. Detect or set input script
                if input_script_sel == "autodetect":
                    detected = detect.detect(raw_text)
                    input_script = normalize_script(detected)
                    st.info(f"Detected Input Script: {format_scheme(input_script)}")
                else:
                    input_script = normalize_script(input_script_sel)
                
                # Protect against totally unsupported scripts gracefully
                if input_script not in schemes:
                    st.warning(f"Script '{input_script}' is not fully supported natively for input. Defaulting to IAST.")
                    input_script = sanscript.IAST

                # 2. Transliterate input to IAST for the API (API works best with IAST)
                iast_text = sanscript.transliterate(raw_text, input_script, sanscript.IAST)
                
                # 3. Preprocess and split
                preprocessed = preprocess(iast_text)
                texts = split_into_lines(preprocessed)
                
                if not texts:
                    st.error("No valid text to analyze.")
                    return
                
                # 4. Call API
                data = call_api(texts)
                
                # 5. Build results & detect warnings
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
                    st.error("No grammatical analysis returned. Try different input.")
                    return
                
                if warning:
                    st.warning("Some words may have been lost in segmentation. Results may require verification.")
                    
                # Helper formatters
                def to_output(text):
                    return sanscript.transliterate(text, sanscript.IAST, output_script_sel)
                    
                def to_devanagari(text):
                    return sanscript.transliterate(text, sanscript.IAST, sanscript.DEVANAGARI)
                
                st.subheader("Input")
                st.info(" ".join(to_output(t) for t in texts))
                
                st.subheader("Padaccheda (Segmentation)")
                st.info(" ".join(to_output(u) for u in all_unsandhied))
                
                st.subheader("Word Analysis")
                
                # Create HTML table mapping to match Dharmamitra aesthetic
                table_html = "<div style='overflow-x:auto;'><table style='width:100%; border-collapse: collapse;'>"
                table_html += "<tr><th style='text-align:left; border-bottom:1px solid #e5e5e5; padding:12px;'>#</th>"
                table_html += "<th style='text-align:left; border-bottom:1px solid #e5e5e5; padding:12px;'>Word</th>"
                table_html += "<th style='text-align:left; border-bottom:1px solid #e5e5e5; padding:12px;'>Lemma</th>"
                table_html += "<th style='text-align:left; border-bottom:1px solid #e5e5e5; padding:12px;'>Grammar</th></tr>"
                
                for i in range(len(all_unsandhied)):
                    uns_out = to_output(all_unsandhied[i])
                    lem_out = to_output(all_lemmas[i])
                    
                    uns_dev = to_devanagari(all_unsandhied[i])
                    lem_dev = to_devanagari(all_lemmas[i])
                    raw_tag = all_tags[i]
                    
                    tag_result = post_process_tags(uns_dev, raw_tag)
                    if output_script_sel != sanscript.DEVANAGARI:
                        tag_result = sanscript.transliterate(tag_result, sanscript.DEVANAGARI, output_script_sel)
                        
                    uns_dev_encoded = urllib.parse.quote(uns_dev)
                    lem_dev_encoded = urllib.parse.quote(lem_dev)
                    
                    is_verb = any(x in raw_tag for x in ["Tense=", "Mood=", "VerbForm"])
                    if is_verb:
                        word_html = f'<a href="https://ashtadhyayi.com/dhatu?search={uns_dev_encoded}" target="_blank" style="text-decoration:none; color:#1d4ed8;">{uns_out}</a>'
                    else:
                        word_html = uns_out
                        
                    lemma_html = f'<a href="https://kosha.app/word/sa/{lem_dev_encoded}" target="_blank" style="text-decoration:none; color:#1d4ed8;">{lem_out}</a>'
                    
                    table_html += f"<tr><td style='border-bottom:1px solid #e5e5e5; padding:12px;'>{i+1}</td>"
                    table_html += f"<td style='border-bottom:1px solid #e5e5e5; padding:12px;'>{word_html}</td>"
                    table_html += f"<td style='border-bottom:1px solid #e5e5e5; padding:12px;'>{lemma_html}</td>"
                    table_html += f"<td style='border-bottom:1px solid #e5e5e5; padding:12px;'>{tag_result}</td></tr>"
                    
                table_html += "</table></div>"
                
                st.markdown(table_html, unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"Analysis failed: {e}. Check your connection and try again.")
                
    st.markdown("---")
    st.markdown('''
        <div style="text-align: center; font-size: 0.8rem; color: #6b7280; margin-top: 2rem;">
            Powered by <a href="https://dharmamitra.org" target="_blank" rel="noopener" style="color: #6b7280;">Dharmamitra</a>
            &middot; Transliteration by <a href="https://github.com/indic-transliteration/indic_transliteration_py" target="_blank" rel="noopener" style="color: #6b7280;">indic_transliteration</a>
            &middot; Based on <a href="https://t.me/Dharmamitrabot" target="_blank" rel="noopener" style="color: #6b7280;">@dharmamitrabot</a>
        </div>
    ''', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
