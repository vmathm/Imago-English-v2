
# Imago English v2  

A modular Flask-based language learning app designed to help students build vocabulary using flashcards, study streak tracking, text-to-speech, and an interactive audiobook feature. This is a rewrite of the original Imago English app, structured for clarity and maintainability.

---

## ✅ Features (Planned and Implemented)

- ✅ Modular Flask blueprint architecture
- ✅ User authentication module (auth blueprint)
- ✅ Initial route test (`/auth/test`)
- ✅ User model
  ✅ Role-based access: `student`, `teacher`, `@dmin!`
  ✅ Self-referencing relationship for teacher assignment
  ✅ Integrated with Flask-Login (via `UserMixin`)
  ✅ Overrides `is_active` based on DB value
  ✅ Documented in `docs/architecture.md`
- ✅ Flashcard creation and study flow
- 🛠 Admin dashboard
    ✅ Routes: Assign students, Unassign students, Change roles
    ✅ Dashboard
    
- 🛠 Teacher features
    - Dashboard with private information and assigned_students list
    ✅ manage_student_flashcards.html
    ✅ Test student flashcards management routes (edit / delete/ add) 
    ✅ adds form for adding card for student
    ✅ creates search button within manage_student_flashcards (added to edit_cards also)
    


- 🛠 Audiobook reader (with text parsing and flashcard addition)
- 🛠 Progress tracking
- 🛠 Google Translate integration
- 🛠 Google Calendar integration (for teacher availability)


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


## FlashcardForm: Flask-WTF Form Structure
This app uses Flask-WTF for secure and structured form handling.

FlashcardForm is used to let students and teachers create flashcards.

Location: app/flashcard/form.py

Inherits from: FlaskForm
This enables:

- automatic CSRF protection

- built-in form validation

- integration with Jinja templates

Main fields:

front: Required text field (question/prompt)

back: Required text area (answer/explanation)

submit: Button to submit the form

Template Usage Example:
<form method="post" action="{{ url_for('flashcards.add_card') }}">
    {{ form.hidden_tag() }}
    {{ form.front.label }} {{ form.front() }}
    {{ form.back.label }} {{ form.back() }}
    {{ form.submit() }}
</form>
form.hidden_tag() ensures CSRF tokens are submitted properly.

## Folder Structure
Refer to docs/architecture.md ## Project Structure


## How to run the app

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

SECRET_KEY=your-secret-key
ALLOW_DEV_LOGIN=True
```
Optional: 
add DATABASE_URL=sqlite:///app.db= your_database.db to .env


#### Seed users
Run scripts/seed_users.py to create a user for each role for testing purposes. Production only allows users to login via Google API. 


### 3. Run the app
```bash
export FLASK_APP=main.py
flask run
``` 




## Project Start Date

June 12, 2025

See docs/ for architecture, API design, and roadmap.


