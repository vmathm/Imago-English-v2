
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
- ✅ Admin dashboard
    ✅ Routes: Assign students, Unassign students, Change roles, Hard delete, Activate/Deactivate user
    ✅ Dashboard
- ✅ Teacher features
    - Dashboard with private information and assigned_students list
    ✅ manage_student_flashcards.html
    ✅ Test student flashcards management routes (edit / delete/ add) 
    ✅ adds form for adding card for student
    ✅ creates search button within manage_student_flashcards (added to edit_cards also)   
- ✅ Audiobook reader (with text parsing and flashcard addition)
- ✅ Progress tracking
    - ✅ Leaderboard table with ranking and top three ever.
    - ✅ Student level (A1 to C1), for later implementation of audiobooks and activities. 
- ✅ Google Calendar integration (for teacher availability)
- ✅ Google Translate integration
- 🛠 Google Login integration  


---





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

## Google Calendar Integration

Allows teachers to publish their availability through Google Calendar.  
- teachers manage their own time window.
- Students see a list of free slots. 
- 
### 1. Prerequisites
1. Enable the **Google Calendar API** in a Google Cloud project.
2. Create a **service account** and download its JSON credentials.
3. Set the environment variable in `.env`:

### 2. Model
The `CalendarSettings` model stores each teacher’s preferences for availability and lesson duration, outputing a personalized calendar based on their Google Calendar availability. 

### 3. Routes
Refer to the Calendar section of `documents/api.md`


### 4. How it works
`app/services/google_calendar.get_teacher_availability()`:
1. Uses the service-account credentials to query Google Calendar for busy blocks.
2. Applies the teacher’s `CalendarSettings.
3. Generates slots and removes any overlapping busy periods.
4. Returns a dictionary keyed by date, each containing a list of free time ranges.

### 5. Sharing
After saving settings, a copyable link is displayed on the settings page: /calendar 
<teacher_user_name>
Share this URL with students so they can select an available time.

### 6. Dependencies
The feature relies on the following packages (already listed in `requirements.txt`):
- `google-api-python-client`
- `google-auth`
- `google-auth-oauthlib`
- `python-dateutil`



## Google Translate API

This project integrates with the [Google Cloud Translate API](https://cloud.google.com/translate) to provide English-to-Portuguese translation.

- The prerequisites for this API are similar to Google Calendar. 

- The logic is implemented in [`services/translate.py`](./app/services/translate.py).

See [`docs/api.md`](./docs/api.md) for request/response details on the `/audiobook/translate` endpoint.