# Architecture Overview

This project uses the Flask **app factory pattern** and **blueprints** to keep the code modular and maintainable.

## Main Components

- `main.py`: Entry point that runs the app
- `app/__init__.py`: Creates the app instance and registers all blueprints
- `app/auth/`: Handles user-related routes and logic
- `app/database.py`: Sets up SQLAlchemy database. Creates an engine and a scoped_session called db_session
- `app/services/`: Contains reusable service functions like Google Translate and Google Calendar

## Project Structure
├── app/ # Main Flask application package
│ ├── init.py # App factory + config loader + DB init
│ ├── database.py #sets up the SQLAlchemy database.
│ ├── admin/#routes and logic
│ ├── audiobook/#routes and logic
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

| Folder   / File      | Purpose |
|----------------------|---------|
| `app/__init__.py`    | Initializes Flask app, loads config, connects DB |
| `models/user.py`     | Defin
| `config.py`          | Defines settings based on .env variables |
| `scripts/seed_users.py` | Adds sample users to the DB for testing |


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


## Configuration System

The app uses a centralized `config.py` module to manage settings based on .env variables


### Configuration Fields in .env

| Field                     | Purpose |
|---------------------------|---------|
| `SECRET_KEY`              | Flask session encryption and CSRF protection |
| `SQLALCHEMY_DATABASE_URI` | Database connection string (SQLite) |
| `SQLALCHEMY_TRACK_MODIFICATIONS` | Performance optimization (set to `False`) |
| `ALLOW_SEEDED_USERS`         | Custom flag that enables `/auth/demo-login/<user_id>` |


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
| user_name            | String       | Optional custom username |
| email                | String       | User email address |
| google_access_token  | String       | Stored access token for Google APIs |
| profilepic           | String       | Profile image URL |
| phone                | String       | Optional phone number |
| level                | String       | English level (e.g., A1, B2) |
| role                 | String       | `'student'`, `'teacher'`, or `'@dmin!'` |
| active *               | Boolean      | Whether the account is active (used by Flask-Login)  |
| delete_date          | Date         | Soft-delete timestamp |
| user_stripe_id       | String       | Stripe ID for payment tracking |
| join_date            | Date         | First registration date |
| last_payment_date    | Date         | Most recent successful payment |
| study_streak         | Integer      | How many days in a row the user has studied |
| study_max_streak     | Integer      | The biggest sequence of days in a row the user has studied |
| streak_last_date     | Date         | Date of last study session |
| points               | Integer      | Total user points |
| max_points           | Integer      | The highest number of points ever achieved |
| flashcards_studied   | Integer      | Total flashcards reviewed |
| flashcards_studied_today | Integer  | Flashcards reviewed today |
| rate_three_count     | Integer      | Number of "3" ratings received for flashcards |
| assigned_teacher_id  | FK → users.id | Reference to the user’s assigned teacher |

* `active` overrides he default behavior of Flask-Login's `is_active` property so it's based on DB value. (default is always True)

---

#### Relationships

- `assigned_teacher_id` is a self-referencing FK used for assigning a teacher to a student.
- `assigned_students` is a reverse relationship available to teacher users.
- `flashcards`: links user to their flashcards (one-to-many)

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



### Flashcard Model

The Flashcard model represents a language learning flashcard created by a user or teacher. It supports spaced repetition for personalized review and includes metadata for visibility, source, and linguistic tagging.

| Column             | Type         |  Description   |
| ------------------ | ------------ |--------------- |
| id                 | Integer (PK) | Unique         |
| question           | String       | The front side of the|
| answer             | String       | The back side of the                                                                  |
| identify_language | Integer    | Language orientation: `0` = answer in English, `1` = question in English, `2` = bothEnglish |
| part_of_speech   | String(20)   | Grammatcal category (e.g., `'noun'`, `'verb'`,etc.) |
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

  
