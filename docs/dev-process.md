
# ✅ Standard Development Process for a Feature

## Step 1: Design + Plan
- Define what the feature will do.

- Decide what models (if any) are needed.

- Outline expected routes.

→ 📄 Write this in docs/roadmap.md or create a docs/feature-flashcards.md if needed

## Step 2: Database Setup

- Add a new model class in `models/<feature>.py`
- Define columns, relationships, and default values
- Create schema using SQLAlchemy (SQLite initially)

→ 📄 Document the schema in `docs/architecture.md` or with inline comments

---

## Step 3: Blueprint Routes

- Add relevant routes in `routes/<feature>.py`
- Examples:
  - `GET /<resource>` → list or fetch data
  - `POST /<resource>` → create new data
  - `PUT` or `PATCH` as needed for updates
- Use placeholder responses if needed

→ 📄 Add new endpoints to `docs/api.md`

---

## Step 4: Templates + Frontend

- Create relevant HTML templates in `templates/<feature>.html`
- Build forms or views to display or interact with data
- Add JavaScript as needed (e.g. text-to-speech, real-time updates, async behavior)

---

## Step 5: Test + Commit

- Test all routes and frontend behaviors locally
- Use meaningful commit messages:
  - `add model for <feature>`
  - `add routes for <feature>`
  - `create UI for <feature>`

---

## Step 6: Update Documentation

✅ Update `README.md` project checklist  
✅ Add route info to `docs/api.md`  
✅ Add model structure (brief) to `docs/architecture.md`  
✅ Add feature progress or plans to `docs/roadmap.md`