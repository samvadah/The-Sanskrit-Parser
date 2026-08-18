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

# Import the Skrutable Splitter
from skrutable.splitting import Splitter

# Cloudflare Proxy URL for Dharmamitra
API_URL = "https://dharmamitra-proxy.avinash-varna.workers.dev"

AKSHARAMUKHA_SCHEMES = [
    "IAST", "ISO", "Harvard-Kyoto", "SLP1", "ITRANS", "Velthuis", "WX",
    "Devanagari", "Bengali", "Gujarati", "Gurmukhi", "Kannada", "Malayalam", 
    "Oriya", "Tamil", "Telugu", "Brahmi", "Grantha", "Sharada", "Siddham"
]

@st.cache_resource
def get_skrutable_splitter():
    return Splitter()

def preprocess(text):
    text = text.replace("-\n", "")
    text = text.replace("\n", " ")
    text = text.replace("।", "\n")
    text = text.replace("॥", "\n")
    return text

def split_into_lines(text):
    return [s.strip() for s in text.split("\n") if s.strip()]

def call_dharmamitra_api(texts):
    resp = requests.post(
        API_URL,
        json={"texts": texts, "grammar_type": "indic"},
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    resp.raise_for_status()
    return resp.json()

def call_hellwig_skrutable(texts):
    splitter = get_skrutable_splitter()
    results = []
    for text in texts:
        try:
            res = splitter.split(
                text, 
                from_scheme='IAST', 
                to_scheme='IAST', 
                splitter_model='splitter_2018'
            )
            results.append({"segmentation": res.split()})
        except Exception as e:
            results.append({"error": str(e)})
    return results

def post_process_tags(word, ml_tags, lang="English"):
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

    if lang == "संस्कृतम्":
        final_output = "। ".join(clean_tokens) + "।"
    else:
        final_output = " । ".join(clean_tokens) + " ।"
        
    return final_output.replace("-", " ")

def get_dict_url(word_dev_encoded, choice):
    if choice == "Ambuda":
        return f"https://ambuda.org/tools/dictionaries/apte,vacaspatyam,apte-sh,shabdartha-kaustubha/{word_dev_encoded}"
    elif choice == "Sanskrit Kosha":
        return f"https://sanskritkosha.com/?search={word_dev_encoded}"
    else:
        return f"https://kosha.app/word/sa/{word_dev_encoded}"

def to_devanagari_numeral(n):
    mapping = str.maketrans('0123456789', '०१२३४५६७८९')
    return str(n).translate(mapping)

def main():
    st.set_page_config(page_title="सखा - The Sanskrit Parser", page_icon="🕉️", layout="wide")

    lang = st.sidebar.radio("Language / भाषा", ["English", "संस्कृतम्"])

    if lang == "संस्कृतम्":
        t_title = "सखा"
        t_subtitle = "**संस्कृतपदपरिचयकृत्**"
        t_caption = "सूचनम्। एषः यन्त्रनिर्मितः तन्त्रांशः अस्ति। कृपया पठनार्थमेव उपयुज्यताम्।"
        t_input_label = "संस्कृतवाक्यमत्र लिख्यताम्। उदाहरणं वाग्देव्यै नमः।"
        t_btn = "विश्लेषणं कुरु"
        t_translate_eng = "🇬🇧 आङ्ग्लभाषया अनुवादः"
        t_settings = "⚙️ विकल्पाः"
        t_model_label = "प्रारूपम्"
        t_dict_label = "कोशः"
        t_input_script = "निवेशलिपिः"
        t_output_script = "निर्गमलिपिः"
        t_akshara = "🔤 वर्णविश्लेषणम्"
        t_syllables = "अक्षराणि।"
        t_spelling = "विन्यासः।"
        t_svaras = "स्वराः"
        t_vyanjanas = "व्यञ्जनानि"
        t_varnas = "वर्णाः"
        t_total_chars = "आहत्य वर्णाः"
        t_padaccheda = "पदच्छेदः"
        t_word_analysis = "पदविश्लेषणम्"
        t_col_no = "क्रमः"
        t_col_word = "पदम्"
        t_col_lemma = "प्रातिपदिकं धातुर्वा"
        t_col_grammar = "व्याकरणम्"
        t_links_title = "🔗 अन्यानि तन्त्रांशाणि"
        t_links = """
        * 🧮 [**सङ्ख्या**](https://sankhya.streamlit.app) संस्कृतसङ्ख्यापरिवर्तकः
        * 🧩 [**सन्धीराट्**](https://sandhify.streamlit.app) सन्धियोजकः
        * 📰 [**संस्कृतवार्ताः**](https://sanskritnews.streamlit.app) संस्कृतवार्ताजनित्रम्
        * 📚 [**संस्कृतजालस्थानानां सूचिः**](https://anotepad.com/note/read/qx4598pk)
        """
        t_report_title = "दोषावलोकनम्"
        t_report_body = (
            "<strong>दोषावलोकनम्।</strong> यत्र कुत्रापि दोषाः दृश्यन्ते सद्य एव विद्युत्पत्रेण गिड्ढब्जालस्थले वा सूच्यताम्<br><br>"
            "<div style='text-align: center; margin-top: 15px;'>"
            "<a href='mailto:samvadah@proton.me' style='text-decoration: none; padding: 5px 10px; background-color: #f0f2f6; border-radius: 5px; color: black; margin-right: 10px;'>विद्युत्पत्रम्</a>"
            "<a href='https://github.com/samvadah/The-Sanskrit-Parser/issues' target='_blank' style='text-decoration: none; padding: 5px 10px; background-color: #f0f2f6; border-radius: 5px; color: black;'>गिड्ढब्जालस्थलम्</a>"
            "</div>"
        )
        t_footer = '<div style="text-align: center; font-size: 0.9rem; color: #6b7280; margin-top: 2.5rem;">भारतदेशे श्रद्धया रचितं <a href="https://linktr.ee/samvadah" target="_blank" rel="noopener" style="color: #6b7280; text-decoration: underline;">संस्कृतसंवादेन</a>।</div>'
        t_analyzing = "विश्लेषणं प्रचलति"
        t_error_empty = "रिक्तवाक्यं न दीयताम्"
        t_error_fail = "विश्लेषणं विफलम्"
        t_akshara_fail = "वर्णविश्लेषणं विफलम्"
        t_hellwig_error = "हेल्विग्-प्रारूपस्य सम्पर्कः विफलः।"
    else:
        t_title = "सखा - The Sanskrit Parser"
        t_subtitle = "**Sanskrit Grammatical Analyzer**"
        t_caption = "NOTE: AI/ML models can make mistakes. Please use this as a learning aid."
        t_input_label = "Enter Sanskrit text (e.g. वाग्देव्यै नमः)"
        t_btn = "Analyze"
        t_translate_eng = "🇬🇧 Translate to English (Google)"
        t_settings = "⚙️ Settings"
        t_model_label = "Model"
        t_dict_label = "Dictionary"
        t_input_script = "Input Script"
        t_output_script = "Output Script"
        t_akshara = "🔤 Varna & Akshara Analysis (Powered by Akshara)"
        t_syllables = "Syllables:"
        t_spelling = "Spelling Breakdown:"
        t_svaras = "Svaras (Vowels)"
        t_vyanjanas = "Vyanjanas (Consonants)"
        t_varnas = "Total Varnas"
        t_total_chars = "Total Characters"
        t_padaccheda = "Padaccheda (Segmentation)"
        t_word_analysis = "Word Analysis"
        t_col_no = "#"
        t_col_word = "Word"
        t_col_lemma = "Lemma"
        t_col_grammar = "Grammar"
        t_links_title = "🔗 Try these too"
        t_links = """
        * 🧮 [**Sankhya**](https://sankhya.streamlit.app) - Sanskrit Numerals Converter
        * 🧩 [**Sandhify**](https://sandhify.streamlit.app) - Sandhi Conjugator for Sanskrit texts
        * 📰 [**Sanskrit News**](https://sanskritnews.streamlit.app) - Sanskrit News Generator
        * 📚 [**Annotated List of Sanskrit Websites**](https://anotepad.com/note/read/qx4598pk)
        """
        t_report_title = "Report Mistakes"
        t_report_body = (
            "<strong>Mistakes / Errors:</strong> If you spot any incorrect segmentations or grammatical analyses, please report them immediately via email or GitHub.<br><br>"
            "<div style='text-align: center; margin-top: 15px;'>"
            "<a href='mailto:samvadah@proton.me' style='text-decoration: none; padding: 5px 10px; background-color: #f0f2f6; border-radius: 5px; color: black; margin-right: 10px;'>Report via Email</a>"
            "<a href='https://github.com/samvadah/The-Sanskrit-Parser/issues' target='_blank' style='text-decoration: none; padding: 5px 10px; background-color: #f0f2f6; border-radius: 5px; color: black;'>Open GitHub Issue</a>"
            "</div>"
        )
        t_footer = '<div style="text-align: center; font-size: 0.9rem; color: #6b7280; margin-top: 2.5rem;">Made in India with devotion by <a href="https://linktr.ee/samvadah" target="_blank" rel="noopener" style="color: #6b7280; text-decoration: underline;">Sanskrit Samvadah</a></div>'
        t_analyzing = "Analyzing..."
        t_error_empty = "Text cannot be empty."
        t_error_fail = "Analysis failed:"
        t_akshara_fail = "Akshara analysis could not process this string entirely."
        t_hellwig_error = "Failed to connect to the Hellwig API via Skrutable."

    def format_model(m):
        if lang == "संस्कृतम्":
            if "Dharmamitra" in m: return "धर्ममित्रप्रारूपम्"
            if "Hellwig" in m: return "हेल्विग्प्रारूपम्"
        return m
        
    def format_dict(d):
        if lang == "संस्कृतम्":
            if "Kosha" in d and "app" in d: return "कोशैप्"
            if "Ambuda" in d: return "अम्बुदः"
            if "Sanskrit Kosha" in d: return "संस्कृतकोशः"
        return d

    def format_script(s):
        if lang == "संस्कृतम्":
            if s == "Auto-Detect": return "स्वयम्"
            if s == "Devanagari": return "देवनागरी"
        return s

    st.sidebar.title(t_settings)
    model_choice = st.sidebar.selectbox(t_model_label, ["Dharmamitra", "Hellwig (Segmentation Only)"], format_func=format_model)
    dict_choice = st.sidebar.selectbox(t_dict_label, ["Kosha.app", "Ambuda", "Sanskrit Kosha"], format_func=format_dict)
    
    st.sidebar.markdown("---")
    input_options = ["Auto-Detect"] + AKSHARAMUKHA_SCHEMES
    input_script_sel = st.sidebar.selectbox(t_input_script, input_options, index=0, format_func=format_script)
    output_script_sel = st.sidebar.selectbox(t_output_script, AKSHARAMUKHA_SCHEMES, index=AKSHARAMUKHA_SCHEMES.index("Devanagari"), format_func=format_script)

    st.title(t_title)
    st.markdown(t_subtitle)
    st.caption(t_caption)

    raw_text = st.text_area(t_input_label, height=100)
    
    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        submit_btn = st.button(t_btn, type="primary")
    with col_btn2:
        if raw_text.strip():
            encoded_text = urllib.parse.quote(raw_text)
            st.link_button(t_translate_eng, f"https://translate.google.com/?sl=sa&tl=en&text={encoded_text}&op=translate")

    if submit_btn:
        if not raw_text.strip():
            st.error(t_error_empty)
        else:
            with st.spinner(t_analyzing):
                try:
                    if input_script_sel == "Auto-Detect":
                        detected_script = transliterate.auto_detect(raw_text)
                        input_script = detected_script if detected_script else "IAST"
                    else:
                        input_script = input_script_sel

                    iast_text = transliterate.process(input_script, "IAST", raw_text)
                    dev_text = transliterate.process(input_script, "Devanagari", raw_text)

                    with st.expander(t_akshara, expanded=False):
                        try:
                            vinyaasa = vk.get_vinyaasa(dev_text)
                            aksharas = vk.get_akshara(dev_text)
                            
                            aksharas_str = "। ".join(aksharas) if lang == "संस्कृतम्" else ", ".join(aksharas)
                            vinyaasa_str = "। ".join(vinyaasa) if lang == "संस्कृतम्" else ", ".join(vinyaasa)
                            
                            st.markdown(f"**{t_syllables}** `{aksharas_str}`")
                            st.markdown(f"**{t_spelling}** `{vinyaasa_str}`")
                            
                            c1, c2, c3, c4 = st.columns(4)
                            c1.metric(t_svaras, vk.count_svaras(dev_text))
                            c2.metric(t_vyanjanas, vk.count_vyanjanas(dev_text))
                            c3.metric(t_varnas, vk.count_varnas(dev_text))
                            c4.metric(t_total_chars, len(vinyaasa))
                        except Exception as e:
                            st.warning(f"{t_akshara_fail} {e}")

                    texts = split_into_lines(preprocess(iast_text))
                    if not texts:
                        pass
                    elif "Hellwig" in model_choice:
                        # --- HELLWIG ROUTE VIA SKRUTABLE ---
                        hellwig_data = call_hellwig_skrutable(texts)
                        st.subheader(t_padaccheda)
                        
                        if hellwig_data and "error" in hellwig_data[0]:
                            st.error(f"⚠️ {t_hellwig_error} : {hellwig_data[0]['error']}")
                        else:
                            def to_output(txt):
                                return transliterate.process("IAST", output_script_sel, txt)
                                
                            for entry in hellwig_data:
                                segs = entry.get("segmentation", [])
                                st.code(" ".join(to_output(s) for s in segs), language="text")
                    else:
                        # --- DHARMAMITRA ROUTE ---
                        data = call_dharmamitra_api(texts)
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
                        
                        st.subheader(t_padaccheda)
                        seg_output = " ".join(to_output(u) for u in all_unsandhied)
                        st.code(seg_output, language="text")
                        
                        st.subheader(t_word_analysis)
                        table_html = "<div style='overflow-x:auto;'><table style='width:100%; border-collapse: collapse;'>"
                        table_html += f"<tr><th style='text-align:left; border-bottom:1px solid #e5e5e5; padding:10px;'>{t_col_no}</th>"
                        table_html += f"<th style='text-align:left; border-bottom:1px solid #e5e5e5; padding:10px;'>{t_col_word}</th>"
                        table_html += f"<th style='text-align:left; border-bottom:1px solid #e5e5e5; padding:10px;'>{t_col_lemma}</th>"
                        table_html += f"<th style='text-align:left; border-bottom:1px solid #e5e5e5; padding:10px;'>{t_col_grammar}</th></tr>"
                        
                        for i in range(len(all_unsandhied)):
                            uns_out = to_output(all_unsandhied[i])
                            lem_out = to_output(all_lemmas[i])
                            uns_dev = to_dev(all_unsandhied[i])
                            lem_dev = to_dev(all_lemmas[i])
                            
                            tag_result = post_process_tags(uns_dev, all_tags[i], lang=lang)
                            if output_script_sel != "Devanagari":
                                tag_result = transliterate.process("Devanagari", output_script_sel, tag_result)
                                
                            uns_dev_encoded = urllib.parse.quote(uns_dev)
                            lem_dev_encoded = urllib.parse.quote(lem_dev)
                            
                            lemma_link = get_dict_url(lem_dev_encoded, dict_choice)
                            lemma_html = f'<a href="{lemma_link}" target="_blank" style="text-decoration:none; color:#1d4ed8;">{lem_out}</a>'
                            
                            is_verb = any(x in all_tags[i] for x in ["Tense=", "Mood=", "VerbForm"])
                            word_html = f'<a href="https://ashtadhyayi.com/dhatu?search={uns_dev_encoded}" target="_blank" style="text-decoration:none; color:#1d4ed8;">{uns_out}</a>' if is_verb else uns_out
                            
                            display_num = to_devanagari_numeral(i + 1) if lang == "संस्कृतम्" else str(i + 1)
                            
                            table_html += f"<tr><td style='border-bottom:1px solid #eee; padding:10px;'>{display_num}</td>"
                            table_html += f"<td style='border-bottom:1px solid #eee; padding:10px;'>{word_html}</td>"
                            table_html += f"<td style='border-bottom:1px solid #eee; padding:10px;'>{lemma_html}</td>"
                            table_html += f"<td style='border-bottom:1px solid #eee; padding:10px;'>{tag_result}</td></tr>"
                            
                        table_html += "</table></div>"
                        st.markdown(table_html, unsafe_allow_html=True)
                        
                except Exception as e:
                    st.error(f"{t_error_fail} {e}")

    # --- FOOTERS ---
    st.markdown("---")
    with st.expander(t_links_title, expanded=False):
        st.markdown(t_links)

    with st.expander(t_report_title, expanded=False):
        st.markdown(f"<div style='color: gray; font-size: 0.9em;'>{t_report_body}</div>", unsafe_allow_html=True)

    # Bottom Footer
    st.markdown(t_footer, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
