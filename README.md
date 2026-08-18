# 🕉️ सखा (Sakhaa) — The Sanskrit NLP Parser & Reader Assistant

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://the-sanskrit-parser.streamlit.app)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Aksharamukha](https://img.shields.io/badge/Transliteration-Aksharamukha-orange)](https://github.com/virtualvinodh/aksharamukha)
[![Cloudflare Workers](https://img.shields.io/badge/API%20Proxy-Cloudflare%20Workers-F38020?logo=cloudflare&logoColor=white)](https://workers.cloudflare.com/)
[![Made in India](https://img.shields.io/badge/Made%20in-India-ff9933?style=flat&logoColor=white)](https://linktr.ee/samvadah)

**सखा (Sakhaa)** is an open-source Sanskrit Natural Language Processing (NLP) tool and digital reading assistant designed for philologists, students, and computational linguists. It brings together automated word segmentation (*Padaccheda*), morphological tagging, multi-lexicon cross-referencing, multi-script transliteration, and phonetic syllable breakdowns into a unified web interface and embeddable JavaScript plugin.

---

## 🎯 Key NLP Features

### 1. 🧩 Automated Word Segmentation (*Padaccheda*) & Sandhi Resolution
- **Dharmamitra Engine:** Performs syntactic segmentation and detailed grammatical tokenization, resolving complex euphonic combinations (*Sandhi*) and compound words (*Samāsa*).
- **Oliver Hellwig Model (2018 EMNLP):** Classical statistical and neural segmentation for compound-heavy sentences (accessed via `skrutable`).

### 2. 🔍 Morphological Analysis & Tag Disambiguation
- Disambiguates nominal inflection (*Vibhakti*), verbal conjugations (*Lakāra*), voice (*Parasmaipada / Ātmanepada*), gender (*Linga*), and number (*Vacana*).
- Formats morphological tags according to classical Paninian conventions.
- Automatically maps root verbs (*Dhātus*) to the **Ashtadhyayi Dhatupatha**.

### 3. 📚 Multi-Dictionary Lexicon Lookup
- Instant single-click lemma searches integrated across premier digital Sanskrit dictionaries:
  - **[Ambuda](https://ambuda.org)** (Apte, Vachaspatyam, Shabdartha Kaustubha)
  - **[Kosha.app](https://kosha.app)**
  - **[Sanskrit Kosha](https://sanskritkosha.com)**
  - **[Ashtadhyayi.com](https://ashtadhyayi.com/dhatu)** (Root Verb Index)

### 4. 🔤 Varna & Akshara Phonetic Analysis
- Powered by [`akshara`](https://github.com/samvadah/akshara) for granular phonological parsing:
  - Syllable segmentation (*Akshara*)
  - Character spelling decomposition (*Vinyaasa*)
  - Quantitative metrics for vowels (*Svaras*), consonants (*Vyanjanas*), and total character counts.

### 5. 🔄 Universal Multi-Script Transliteration
- Real-time conversion across 20+ Roman and Indic writing systems via [`aksharamukha`](https://github.com/virtualvinodh/aksharamukha):
  - *Scripts supported:* Devanagari, IAST, ITRANS, SLP1, Harvard-Kyoto, Velthuis, WX, Bengali, Telugu, Kannada, Malayalam, Grantha, Sharada, Brahmi, Siddham, and more.
  - Automatic input script detection.

### 6. 🇮🇳 Classical Sanskrit Interface Mode
- Full Sanskrit localization (*संस्कृतम्*) adhering to traditional orthography:
  - Devanagari numerals (`१, २, ३...`) in analysis tables
  - Traditional punctuation (pure Dandas `।` with no Western punctuation)
  - Classical terminology (*पदच्छेदः*, *प्रातिपदिकं धातुर्वा*, *निवेशलिपिः*, *निर्गमलिपिः*)

---

## 🌐 Embeddable Web Plugin (`sakhaa-plugin.js`)

Digital Sanskrit libraries, text archives, and blog administrators can integrate **सखा** directly into their websites to provide instant *Padaccheda* tooltips when readers select text.

### How to Embed:
Add this single `<script>` tag immediately before the closing `</body>` tag of your HTML:

```html
<script src="https://cdn.jsdelivr.net/gh/samvadah/The-Sanskrit-Parser@main/sakhaa-plugin.js"></script>
```

### Plugin Capabilities:
- **Mobile & Touchscreen Compatible:** Uses DOM Selection API with touch-delay handling for iOS and Android.
- **Powered by Cloudflare Workers:** API requests route through a globally distributed, low-latency Cloudflare Worker proxy (`https://sakhaa.samvadah.workers.dev/`) with CORS enabled.
- **Zero Dependencies:** Pure Vanilla JavaScript; does not interfere with existing site scripts or stylesheets.

---

## 🚀 Quickstart & Local Setup

### Prerequisites
- Python 3.10 or higher
- `pip` package manager

### Installation
```bash
# 1. Clone the repository
git clone https://github.com/samvadah/The-Sanskrit-Parser.git
cd The-Sanskrit-Parser

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch the application
streamlit run app.py
```

---

## 📦 Dependencies

| Package | Purpose |
| :--- | :--- |
| `streamlit` | Reactive UI framework |
| `aksharamukha` | Transliteration and script auto-detection engine |
| `akshara` | Phonetic character counting and syllable decomposition |
| `skrutable` | Python bridge for Oliver Hellwig's segmentation engine |
| `requests` | HTTP client for backend NLP service queries |

---

## 🏗️ Technical Architecture

```
[ User Input / Web Plugin ]
          │
          ▼
┌────────────────────────────────────────────────────────┐
│  Aksharamukha (Script Normalization -> IAST)          │
└──────────────────┬─────────────────────────────────────┘
                   │
         ┌─────────┴─────────┐
         ▼                   ▼
┌─────────────────┐ ┌────────────────────────────────────┐
│ Dharmamitra API │ │ Skrutable / Hellwig (2018) Engine  │
│ (Morphology)    │ │ (Sandhi & Compound Splitting)      │
└────────┬────────┘ └─────────────────┬──────────────────┘
         │                            │
         └─────────┬──────────────────┘
                   │
                   ▼
┌────────────────────────────────────────────────────────┐
│  Post-Processing: Paninian Tag Normalization & Dandas   │
└──────────────────┬─────────────────────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────────────────────┐
│  Streamlit UI / Cloudflare Worker Tooltip Response     │
└────────────────────────────────────────────────────────┘
```

---

## 🔗 Sanskrit Digital Ecosystem

Explore related Sanskrit computational tools developed by Sanskrit Samvadah:

- 🧮 [**Sankhya (सङ्ख्या)**](https://sankhya.streamlit.app) — Sanskrit Numeral Converter & Number-to-Word Generator
- 🧩 [**Sandhify (सन्धीराट्)**](https://sandhify.streamlit.app) — Rule-based Sanskrit Sandhi Conjugator
- 📰 [**Sanskrit News (संस्कृतवार्ताः)**](https://sanskritnews.streamlit.app) — Daily Sanskrit News Reader & Aggregator
- 📚 [**Annotated Directory of Sanskrit Websites**](https://anotepad.com/note/read/qx4598pk) — Curated collection of digital Sanskrit portals

---

## 🤝 Bug Reports & Contributions

If you encounter segmentation anomalies or grammatical tag discrepancies:
- Submit an issue on the [GitHub Issue Tracker](https://github.com/samvadah/The-Sanskrit-Parser/issues)
- Reach out via email: `samvadah@proton.me`

---

## 📜 License

Distributed under the [MIT License](LICENSE).

<div align="center">
  <sub>Made in India with devotion by <a href="https://linktr.ee/samvadah">Sanskrit Samvadah</a> • भारतदेशे श्रद्धया रचितं संस्कृतसंवादेन।</sub>
</div>
```
