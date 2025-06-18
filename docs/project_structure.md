## 📁 Project Structure
├── app/ # Main Flask application package
│ ├── init.py # App factory + config loader + DB init
│ ├── database.py #sets up the SQLAlchemy database.
│ ├── auth/ #User-related routes and logic
│ ├── admin/#routes and logic
│ ├── audiobook/#routes and logic
│ ├── dashboard/#routes and logic
│ ├── models/ # All database models
│ │ ├── init.py # Aggregates all models for easy import
│ │ ├── base.py # SQLAlchemy declarative base
│ │ ├── user.py # User model (with roles)
│ │ └── flashcard.py # Flashcard model (TBD)
│ └── templates/ # HTML templates