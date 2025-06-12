
# Imago English v2

A modular Flask-based language learning app designed to help students build vocabulary using flashcards, study streak tracking, text-to-speech, and an interactive audiobook feature. This is a rewrite of the original Imago English app, structured for clarity and maintainability.

---

## ✅ Features (Planned and Implemented)

- ✅ Modular Flask blueprint architecture
- ✅ User authentication module (auth blueprint)
- ✅ Initial route test (`/auth/test`)
- 🛠 Flashcard creation and study flow
- 🛠 Progress tracking
- 🛠 Google Translate integration
- 🛠 Audiobook reader (with text parsing and flashcard addition)
- 🛠 Google Calendar integration (for teacher availability)
- 🛠 Teacher dashboard

---

##  Getting Started

### 1. Clone and set up the environment
```bash
git clone https://github.com/vmathm/imago-english-v2.git
cd imago-english-v2
python3 -m venv venv
source venv/bin/activate   
pip install -r requirements.txt
```
### 2. Run the app
```bash
export FLASK_APP=main.py
flask run
``` 

