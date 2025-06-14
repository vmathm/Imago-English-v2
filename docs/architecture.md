# Architecture Overview

This project uses the Flask **app factory pattern** and **blueprints** to keep the code modular and maintainable.

## Main Components

- `main.py`: Entry point that runs the app
- `app/__init__.py`: Creates the app instance and registers all blueprints
- `app/auth/`: Handles user-related routes and logic
- `app/services/`: Contains reusable service functions like Google Translate

## Blueprints

Each major feature has its own blueprint:
- `auth` for login/signup routes
- `flashcards` for vocabulary creation
- `audiobook` for text/audio display + text selection for translation



## Why this structure?

- Easy to test and maintain
- Scalable as new features are added
- Encourages clean separation of concerns



# Models and Schema

## Base Class Setup

All models inherit from a shared SQLAlchemy base class, defined in `models/base.py`:

```python
from sqlalchemy.orm import declarative_base
Base = declarative_base()
```

##  User Model

The `User` model represents all types of users in the system: students, teachers, and admins. We use a single-table role-based approach, where each user has a `role` field to define their access level and permissions.

### 🧱 Table: `users`

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
| role                 | String       | `'student'`, `'teacher'`, or `'admin'` |
| active               | Boolean      | Whether the account is active (used by Flask-Login) |
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

---

### 🔁 Relationships

- `assigned_teacher_id` is a self-referencing FK used for assigning a teacher to a student.
- `assigned_students` is a reverse relationship available to teacher users.
- `progress`: links user to their reading progress (one-to-many)
- `flashcards`: links user to their flashcards (one-to-many)

---

### 🧠 Role System

- `role = 'student'`: Limited to studying and viewing own data
- `role = 'teacher'`: Can manage students assigned to them
- `role = 'admin'`: Has full control (user management, assignment, etc.)

Use helper methods for checks:

```python
user.is_student()   # True if student
user.is_teacher()   # True if teacher or admin
user.is_admin()     # True if admin




