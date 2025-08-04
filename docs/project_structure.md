## 📁 Project Structure
├── app/                    # Main Flask application
│   ├── __init__.py         # App factory
│   ├── extensions.py       # LoginManager, CSRF setup
│   ├── database.py         # SQLAlchemy engine/session
│   ├── admin/              # Admin routes and forms
│   ├── auth/               # Authentication routes
│   ├── audiobook/          # Audiobook feature
│   ├── dashboard/          # Dashboard views
│   ├── flashcard/          # Flashcard routes and forms
│   ├── home/               # Landing page
│   ├── progress/           # Leaderboard routes
│   ├── models/             # Database models
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── user.py
│   │   └── flashcard.py
│   ├── services/           # External integrations
│   ├── static/             # JS and CSS
│   │   └── js/
│   └── templates/          # HTML/Jinja templates
│       ├── flashcards/
│       ├── partials/
│       └── progress/
├── scripts/                # Utility scripts
├── config.py               # Config class
├── main.py                 # App entry point
└── requirements.txt        # Dependencies
