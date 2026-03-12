# The Sanskrit Parser

A unified web interface for Sanskrit NLP tasks. This tool allows users to input Sanskrit text in any script, parse it using world-class models, and instantly look up words in major Sanskrit dictionaries.

## ✨ Features
- **Multi-Script Support:** Input in Devanagari, Telugu, Kannada, or IAST (via Aksharamukha).
- **Dual Parsing Models:**
  - **Dharmamitra:** Provides detailed morphological tagging (Prātipadikam, Vibhakti, etc.).
  - **Hellwig (2018):** character-level neural network model for advanced word segmentation.
- **Instant Dictionary Integration:** One-click lookups on **Kosha.app**, **Ambuda**, and **SanskritKosha**.

## 🛠️ Technology Stack
- **Frontend:** [Streamlit](https://streamlit.io)
- **NLP Models:** [Dharmamitra API](https://dharmamitra.org) & [Skrutable](https://github.com/tylergneill/skrutable) (Hellwig 2018 Wrapper)
- **Transliteration:** [Aksharamukha API](https://aksharamukha.appspot.com)

## 🚀 Deployment
This app is designed to be deployed on **Streamlit Community Cloud**. 
1. Push `app.py` and `requirements.txt` to GitHub.
2. Connect your repository to Streamlit Cloud.
