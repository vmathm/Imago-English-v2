
# Imago English v2  

A modular Flask-based language learning app designed to help students build vocabulary using flashcards, study streak tracking, text-to-speech, and an interactive audiobook feature. This is a rewrite of the original Imago English app, structured for clarity and maintainability.

---

## ✅ Features (Planned and Implemented)

- ✅ Modular Flask blueprint architecture
- ✅ User authentication module (auth blueprint)
- ✅ Initial route test (`/auth/test`)
- ✅ User model
  - Role-based access: `student`, `teacher`, `admin`
  - Self-referencing relationship for teacher assignment
  - Integrated with Flask-Login (via `UserMixin`)
  - Overrides `is_active` based on DB value
  - Documented in `docs/architecture.md`
- 🛠 Flashcard creation and study flow
- 🛠 Progress tracking
- 🛠 Google Translate integration
- 🛠 Audiobook reader (with text parsing and flashcard addition)
- 🛠 Google Calendar integration (for teacher availability)
- 🛠 Teacher dashboard

---


## Flask-Login Authentication & Session Flow
               ┌──────────────────────────────┐
               │   User submits login form    │
               └────────────┬─────────────────┘
                            │
                            ▼
           ┌──────────────────────────────────────┐
           │   Your view calls `login_user(user)` │
           └────────────┬─────────────────────────┘
                        │
                        ▼
        ┌────────────────────────────────────────────┐
        │ Flask stores user.id in session (securely) │
        └────────────────────┬───────────────────────┘
                             │
                             ▼
         Browser stores session in a signed cookie

 ┌────────────────────────────────────────────────────────┐
 │                    A new request comes in             │
 └────────────────────────────────────────────────────────┘
                             │
                             ▼
        Flask reads the signed cookie and loads session
                             │
                             ▼
        ┌────────────────────────────────────────────┐
        │ Flask-Login finds user_id in session       │
        └────────────┬───────────────────────────────┘
                     │
                     ▼
      Calls your `@login_manager.user_loader` function:
     ┌───────────────────────────────────────────────┐
     │  @login_manager.user_loader                   │
     │  def load_user(user_id):                      │
     │      return User.query.get(user_id)           │
     └───────────────────────────────────────────────┘
                     │
                     ▼
          Sets `current_user` to that user object

Now in any route:
    🔹 current_user is available
    🔹 protect views with `@login_required`



## Folder Structure
Refer to docs/architecture.md ## Project Structure


## Getting Started

### 1. Clone and set up the environment
```bash
git clone https://github.com/vmathm/imago-english-v2.git
cd imago-english-v2
python3 -m venv venv
source venv/bin/activate   
pip install -r requirements.txt
```

### 2. Create a `.env` file in the project root:

```env
FLASK_CONFIG=config.DevelopmentConfig*
SECRET_KEY=your-secret-key
ALLOW_DEV_LOGIN=True
```
*Check config.py for classes

Optional: 
add DATABASE_URL=sqlite:///app.db= your_database.db to .env

### 2. Run the app
```bash
export FLASK_APP=main.py
flask run
``` 


## Project Start Date

June 12, 2025

See docs/ for architecture, API design, and roadmap.


