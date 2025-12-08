# Architecture Overview

This project uses the Flask **app factory pattern** and **blueprints** to keep the code modular and maintainable.

## Main Components

- `main.py`: Entry point that runs the app
- `app/__init__.py`: Creates the app instance and registers all blueprints
- `app/auth/`: Handles user-related routes and logic
- `app/database.py`: Sets up SQLAlchemy database. Creates an engine and a scoped_session called db_session
- `app/services/`: Contains reusable service functions like Google Translate and Google Calendar

## Project Structure

```text
├── app/ # Main Flask application package
│ ├── init.py # App factory + config loader + DB init
│ ├── database.py #sets up the SQLAlchemy database.
│ ├── admin/#routes and logic
│ ├── audiobook/#routes and logic
│   │   ├── routes.py       # /audiobook/view, /audiobook/assign/<user_id>
│   │   └── forms.py        # UserAudiobookForm
│ ├── auth/ #User-related routes and logic
│ │ ├── user_loader.py #Defines @login_manager.user_loader decorator to load User objects from session on request
│ ├── admin/#routes and logic
| ├── calendar/#routes and logic
│ ├── dashboard/#routes and logic
│ ├── flashcard/#routes and logic
| ├── home/  # root endpoint (landing page)
│ ├── models/ # All database models
│ │ ├── init.py # Aggregates all models for easy import
│ │ ├── base.py # SQLAlchemy declarative base
│ │ ├── user.py # User model (with roles)
│ │ └── flashcard.py # Flashcard model (TBD)
| ├── progress/# routes and logic
│ ├── services/# routes and logic
│ ├── static/# Static files
│ ├── staticpages/# terms and privacy (future FAQ etc.)
│ ├── templates/ # HTML templates
│   └── partials/ # JINJA logic such as in navlinks being included in HTML via `{% include 'partials/navlinks.html' %}`
├── docs/ #project documentation
├── scripts/
│ └── seed_users.py # Adds test users for dev login
│
├── config.py # App configuration classes (dev, prod)
├── .env # Local environment settings
├── .flaskenv # Defines environment variables specifically for the Flask command-line interface (CLI) -  $ flask run
├── main.py # App launcher
├── extensions.py # Defines LoginManager()
├── requirements.txt # Python dependencies
└── README.md # Project overview and setup instructions
```



## Blueprints

Each major feature has its own blueprint:
- `admin` for users management
- `audiobook` for text/audio display + text selection for translation
- `auth` for login/signup routes
- `calendar` for teacher's to share their availability
- `dashboard` for student, teachers and admin dashboards. 
- `flashcard` for vocabulary build up and spaced repetition studying.
- `home` handles the root endpoint
- `progress` for students and teachers points and study sequence, which define the leaderboards. 
- `services` contains reusable integrations and background logic used across blueprints.
  
## Audiobook Feature

The audiobook feature is implemented as its own blueprint and model, and it reuses the existing flashcard/translation flow.

### Components

- `app/audiobook/routes.py`
  - `GET /audiobook/view`  
    Student-facing view. Loads the `UserAudiobook` row for the logged-in user, fetches the `.txt` from Google Cloud Storage using `requests`, and renders it into `audiobooks.html`.
  - `POST /audiobook/assign_audiobook/<user_id>`  
    Teacher/admin-only endpoint. Called from a modal in the teacher dashboard. Handles upload of text and/or audio, deletes any previously assigned files for that user, and updates the `UserAudiobook` row.

- `app/audiobook/forms.py`
  - `UserAudiobookForm`
    - Two optional fields:
      - `text_file` – `.txt` only (validated with `FileAllowed`)
      - `audio_file` – `.mp3` only
   

- `app/models/user_audiobook.py`
  - `UserAudiobook` model
    - `user_id` → `User.id` (one row per user)
    - `text_url` (nullable) – public GCS URL for `.txt`
    - `audio_url` (nullable) – public GCS URL for `.mp3`
    - `title` – human-readable title derived from the original uploaded filename
    - `created_at`, `updated_at` timestamps
  - Imported in `app/models/__init__.py` so it is registered with SQLAlchemy and created by `Base.metadata.create_all`.

- `app/gcs_utils.py`
  - `upload_file_to_gcs(file_obj, prefix, content_type) -> str`
    - Uploads the Werkzeug file object to the bucket defined in `Config.GCS_AUDIOBOOK_BUCKET`.
    - Uses a UUID suffix in the blob name to avoid collisions.
    - Returns a public URL using the `https://storage.googleapis.com/<bucket>/<blob_name>` pattern.
  - `delete_file_from_gcs_by_url(url: str) -> None`
    - Parses the blob name out of a GCS URL for the configured bucket and deletes the object.
    

### Configuration

- `config.py`
  - `GCS_AUDIOBOOK_BUCKET = os.getenv("GCS_AUDIOBOOK_BUCKET")`

The bucket is configured with **uniform bucket-level access** and an IAM binding:

- Principal: `allUsers`
- Role: `Storage Object Viewer`

This makes all objects in the audiobook bucket publicly readable, which is required for the `<audio>` player and text loading in the browser.

### Behaviour

- Upload:
  - When a teacher uploads new text or audio:
    - Existing files for that user (if any) are deleted from GCS via `delete_file_from_gcs_by_url`.
    - New files are uploaded and the URLs are stored in `UserAudiobook`.
    - If neither text nor audio is present after processing, the `UserAudiobook` row is deleted to keep the data model consistent and allow the user to load their own text or audio temporarily. 
- View:
  - The student audiobook page:
    - Shows the title if present.
    - Shows the audio player only if `audio_url` is set.
    - Loads the text via `requests.get(text_url)` and injects it into `<pre id="text-content">` so the existing selection → translate → flashcard flow works without changes to `audiobook.js`.


## Configuration System

The app uses a centralized `config.py` module to manage settings based on .env variables

| Profile      |  Key Behaviors |
|--------------|----------------|
| `DevConfig`  |  Relaxed cookies (no HTTPS required), `ALLOW_SEEDED_USERS=True` to enable demo/seeded logins   
| `ProdConfig` |  Strict cookies (`Secure`, `HttpOnly`), `ALLOW_SEEDED_USERS=False` (hard-disabled), assumes HTTPS termination. |


Secrets and third-party credentials (SECRET_KEY, GOOGLE_OAUTH_CLIENT_ID/SECRET, DATABASE_URL) always come from the environment—never hard-coded in config classes.

### Configuration Fields in .env

| Field                     | Purpose |
|---------------------------|---------|
| `SECRET_KEY`              | Flask session encryption and CSRF protection |
| `SQLALCHEMY_DATABASE_URI` | Database connection string (SQLite) |
| `SQLALCHEMY_TRACK_MODIFICATIONS` | Performance optimization (set to G`False`) |
| `APP_ENV`     |Sets Development or Production config at config.py |
for Google login:
| `GOOGLE_OAUTH_CLIENT_ID`  | your-client-id.apps.googleusercontent.com |
| `GOOGLE_OAUTH_CLIENT_SECRET`| your-secret |
| `OAUTHLIB_INSECURE_TRANSPORT`| dev mode / http -> allow OAuth over http for Flask-Dance |
for Google Cloud Storage (Enables teacher to upload audiobook to students)
| `GCS_AUDIOBOOK_BUCKET`    | Your Google Cloud bucket |


### Switching Environments

Use .flaskenv to set the variable FLASK_DEBUG=1 to enable Debug Mode/Dev mode and to 0 otherwise.  



## Models and Schema

### Base Class Setup

All models inherit from a shared SQLAlchemy base class, defined in `models/base.py`:

```python
from sqlalchemy.orm import declarative_base
Base = declarative_base()
```

### User Model

The `User` model represents all types of users in the system: students, teachers, and admins. Each user has a `role` field to define their access level and permissions.

#### Table: `users`

| Column               | Type         | Description |
|----------------------|--------------|-------------|
| id                   | String (PK)  | Unique user ID (from Google OAuth) |
| name                 | String       | User's display name |
| user_name            | String       | Defined by default using the user's email as in the example: john@gmail.com → user_name: john |
| email                | String       | User email address |
| google_access_token  | String       | Stored access token for Google APIs |
| profilepic           | String       | Profile image URL |
| phone                | String       | Optional phone number |
| level                | String       | English level (e.g., A1, B2) |
| role                 | String       | `'student'`, `'teacher'`, or `'@dmin!'` |
| learning_language    | String       | `'pt-BR'`or `'en'` - default: `'en'`
| active               | Boolean      | Grants access to flashcard features  |
| delete_date          | Date         | Soft-delete timestamp |
| user_stripe_id       | String       | Stripe ID for payment tracking |
| join_date            | Date         | First registration date |
| last_payment_date    | Date         | Most recent successful payment |
| study_streak         | Integer      | How many days in a row the user has studied |
| max_study_streak     | Integer      | The biggest sequence of days in a row the user has studied |
| streak_last_date     | Date         | Date of last study session |
| points               | Integer      | Total user points |
| max_points           | Integer      | The highest number of points ever achieved (points * max_study_streak) |
| flashcards_studied   | Integer      | Total flashcards reviewed |
| rate_three_count     | Integer      | Number of "3" ratings received for flashcards |
| assigned_teacher_id  | FK → users.id | Reference to the user’s assigned teacher |

#### `learning_language`:

  Language the user is currently **learning**. This setting controls:

  - The default **target language** for translation (Google Cloud Translate).
  - The **text-to-speech voice** language in study mode and audiobook text selection.



#### Relationships

- `assigned_teacher_id` is a self-referencing FK used for assigning a teacher to a student.
- `assigned_students` is a reverse relationship available to teacher users.
- `flashcards` links user to their flashcards (one-to-many)
- `user_audiobook`links user to current audiobook uploaded by the teacher. 

---

#### Role System

- `role = 'student'`: Limited to studying and viewing own data
- `role = 'teacher'`: Can manage students assigned to them
- `role = '@dmin!'`: Has full control (user management, assignment, etc.)

Use helper methods for checks:

```python
user.is_student()   # True if student
user.is_teacher()   # True if teacher or admin
user.is_admin()     # True if admin
```

#### User Account Status (active)

The active column controls whether the user has access to all learning features. 

Admins may toggle this status via `/admin/toggle_active_status`. Assigning a student to a teacher sets `active` to True and Unassigning sets it to False. 

When active = True → full access to:

- creating flashcards

- editing flashcards

- studying flashcards (spaced repetition)

- teacher flashcard management

Views are protected with a decorator `@active_required` that check the status of 'active'.

#### Inactive User Flow

When active = False →
user is blocked from all flashcard features and automatically redirected to `inactive_user.html` where they are prompted to book a free lesson.

Current behavior:

- `inactive_user.html` uses the admin hardcoded email user_name to call `calendar/user_name`. More about calendar at [README.md](../README.md#google-calendar-integration).

NEXT: - evolve into a general “teacher marketplace” where students can pick a teacher with open slots, allowing  inactive status to serve as:
- a payment gate

- an onboarding funnel

- a teacher acquisition mechanism


### Flashcard Model

The Flashcard model represents a language learning flashcard created by a user or teacher. It supports spaced repetition for personalized review and includes metadata for visibility, source, and linguistic tagging.

| Column             | Type         |  Description   |
| ------------------ | ------------ |--------------- |
| id                 | Integer (PK) | Unique         |
| question           | String       | The front side of the|
| answer             | String       | The back side of the                                                                  |
| identify_language | Integer    | Language orientation: `0` = answer in English, `1` = question in English, `2` = bothEnglish |
| part_of_speech   | String(20)   | Grammatical category (e.g., `'noun'`, `'verb'`,etc.) |
| level              | Integer      | Number of successful reviews|
| ease               | Integer      | Ease factor used in spaced  |
| interval           | Integer      | Days until the next review  |
| last_review       | DateTime     | Timestamp of the most recent review|
|next_review	    | DateTime	   |   When the flashcard should be shown again |
|show_answer	    | Boolean	   | Whether the answer is currently shown (controlled by frontend)|
|reviewed_by_tc	    | Boolean	   | Indicates if the flashcard was reviewed by a teacher|
|add_by_tc	        | Boolean	   | Indicates if the flashcard was created by a teacher |
|add_by_user	    | Boolean	   | Indicates if the flashcard was created by a student |
|user_id	        | FK → users.id| Foreign key linking to the flashcard owner |

#### Relationships
user_id is a foreign key that links each flashcard to its owner in the users table.

user: the SQLAlchemy relationship back to the User model, allowing access to user.flashcards.

#### Spaced Repetition Support
The fields level, ease, interval, last_review, and next_review enable the app to implement a lightweight spaced repetition algorithm (spaced_repetition.md).

#### Data Exposure
Use to_dict() when exposing flashcard data to the frontend or API. This method ensures show_answer is returned as False by default for study sessions:

```python
def to_dict(self):
    return {
        "id": self.id,
        "question": self.question,
        "answer": self.answer,
        "level": self.level,
        "ease": self.ease,
        "interval": self.interval,
        "last_review": self.last_review,
        "next_review": self.next_review,
        "user_id": self.user_id,
        "show_answer": False,
    }
``` 




## Spaced Repitition Algorithm
The flashcard review system blends spaced repetition with gamified rewards. While based on SuperMemo(SM*2), it has been customized to support:

* Real-time retry logic: cards rated 1 go back to the end of the queue. 
* Role-sensitive scoring: Teachers can review flashcards with students during class and rating will award the points to the student. 
* Simplified ease/interval management: Intervals are days and not hours, as the goal is a daily review of available cards.

### Study Streak Support

The flashcard review route (`/review_flashcard`) also manages daily streaks.  
When a user reviews their **last due flashcard of the day**, the helper function `update_study_streak(user)` is called.

Rules:
- If `streak_last_date == yesterday` → increment `study_streak` by 1  
- If `streak_last_date` is neither today nor yesterday → reset `study_streak` to 1  
- If `streak_last_date == today` or user didn't have a card to study on the day → no change  

## User Roles & Permissions

The system supports three main roles:

- **Student**
  - Can create, edit and study their own flashcards. 
  - Has a personal ranking score. 
  - Can use the audiobook section.

- **Teacher**
  - Inherits student permissions. 
  - Can create, edit, and review their students flashcards and level.
  - Manages lesson availability via `/calendar/settings`.
  

- **Admin**
  - Has access to `admin/` routes
  - Manages all users settings: assigning roles, assigning students to teachers, deleting users.
 

### Authentication
- Development mode: seeded test users (created via `scripts/seed_users.py`). 
- Production: only Google OAuth login is enabled


### Dashboard Context Flow

The dashboard route (`dashboard/index`) uses two helper functions to assemble role-specific context:

- `get_teacher_data()` → returns assigned students, level-change form, and counts of unreviewed flashcards per student (users with unreviewed flashcards are highlighted to the teacher).
- `get_admin_data()` → returns all admin forms and user lists, with WTForms choices pre-populated.

  

## PWA scope vs. Google OAuth (Android behavior)
The PWA manifest is intentionally scoped to the dashboard routes only:

```json
{
  "start_url": "/dashboard/",
  "scope": "/dashboard/",
  "display": "standalone",
  ...
}
```
#### Why this matters:

- All interactive app UI lives under /dashboard/….

- All authentication and OAuth endpoints live outside that scope:

    - /auth/...

    - /login/google/authorized (Flask-Dance callback)

- On Android, installed PWAs are packaged as WebAPKs. If the PWA scope includes / (the whole origin), Chrome may try to “hand off” OAuth callback URLs back into the PWA window, which breaks the Flask-Dance session/state on some devices and causes a Google login loop (account chooser repeating).

#### Resulting behavior

Google OAuth now runs entirely in normal Chrome:

1. User taps “Sign in with Google” (in browser or inside PWA).

2. Flow goes through /auth/login/google → Google → /login/google/authorized → /auth/login/google/complete.

3. All of this stays outside the PWA scope, in a single browser context with a consistent session.

- Once authenticated, the user is redirected to /dashboard/, which is inside the PWA scope and opens in standalone mode when installed.


** Restricting the PWA scope to /dashboard/ is a deliberate choice to avoid Android WebAPK / Chrome handoff issues during OAuth. ** 



