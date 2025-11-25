# API Endpoints

## Auth

### `GET /auth/test`
- Returns: `"Auth route is working!"`
- Purpose: Test that the auth blueprint is registered and working properly

More routes will be added as blueprints are developed.


### `GET /auth/demo-login/<user_id>`
- Simulates logging in as an existing user. Useful for testing features without going through the Google OAuth flow.
- Returns `404` if the user does not exist

#### Requirements:
- Flask app must be running in **debug mode**  
- `ALLOW_SEEDED_USERS = True` in .env

#### Response:
- Redirects the user to the dashboard (`/dashboard`) after logging them in
- Returns `403` if disabled or not in debug mode
- Returns `404` if the user does not exist

### `GET /auth/login/google`
- Starts the OAuth login process via Google.
- Redirects to Google’s OAuth 2.0 authorization screen.

### `GET /auth/login/google/complete`
- Callback endpoint after Google authorization completes.
- Fetches user profile info from Google
- Logs in the user if already registered
- Creates a new user if email is not found in the database

#### Response: 
- redirects to `/dashboard` if successful
- Returns `403` if the user cancels login or token is invalid.

### `GET /auth/logout`
- Logs out a user and redirects to `/`.


## Admin

### `POST /admin/assign_student`
- Assigns a student to a teacher (admin only).

### `POST /admin/unassign_student`
- Removes the teacher assignment from a student (admin only).

### `POST /admin/change_role`
- Updates a user's role (`student`, `teacher`, or `@dmin!`) (admin only).

### `POST /admin/delete_user`
- Hard deletes a user and their flashcards from the database.

### `POST /admin/toggle_active_status`
- Toggles `user.active` 

- Disables flashcard creation, editing, study and managing student cards for teachers. 

- Redirects the user to `inactive_user.html` on any flashcard-related route

- keeps Google OAuth login functional (user can still log in)

### `POST /admin/update_student_level`
- Updates `user.level` (A1 to C2)

### `POST /admin/update_phone`
- Updates `user.phone` 



## Dashboard

### `GET /index`
- Loads `dashboard.html` according to user type.
- The route builds a base context and merges role-specific data via two helpers:

| Key                        | Type                     | Provided by         | Purpose                                        |
|----------------------------|--------------------------|---------------------|------------------------------------------------|
| form                       | FlashcardForm            | base route          | Quick-add flashcard form                       |
| assigned_students          | list[User]               | get_teacher_data    | Teacher’s students                             |
| change_student_level_form  | ChangeStudentLevelForm   | get_teacher_data    | Teacher: change a student’s level              |
| unreviewed_counts          | dict[int,int]            | get_teacher_data    | `{user_id → unreviewed_flashcards}`            |
| assign_form                | AssignStudentForm        | get_admin_data      | Admin: assign students to teachers             |
| unassign_form              | UnassignStudentForm      | get_admin_data      | Admin: unassign students                       |
| change_role_form           | ChangeRoleForm           | get_admin_data      | Admin: change user roles                       |
| delete_user_form           | DeleteUserForm           | get_admin_data      | Admin: delete users                            |
| toggle_active_status_form  | ToggleActiveStatusForm   | get_admin_data      | Admin: activate/deactivate users               |
| all_users                  | list[User]               | get_admin_data      | Admin overview                                 |
| teachers                   | list[User]               | get_admin_data      | Admin: teacher options                         |
| unassigned_students        | list[User]               | get_admin_data      | Admin: students with no teacher                |
| assigned_students_admin    | list[User]               | get_admin_data      | Admin: students currently assigned             |

**Notes**
- Helpers are internal; not endpoints themselves.
- Templates decide what to show based on which keys exist.


### `POST /dashboard/set_username`
- Updates the logged-in user’s `user_name`.
- Requires authentication.

#### Request
Standard HTML form POST:

- `user_name` – new username to be displayed in the dashboard and used in the URLs for the calendar link.

Basic validation is applied (non-empty string, trimmed).  
If valid, `current_user.user_name` is updated and the user is redirected back to `/dashboard` with a flashed message.

#### Notes
- On first login, `user_name` is automatically set to the part of the email before `@`.  
  Example: `john@gmail.com` → `john`.
- This endpoint lets the user override that default with a more friendly or public-facing username.


## Flashcards
⚠ All flashcard routes require an [active user](architecture.md####user-account-status-(active))
If current_user.active == False, the request redirects to `/inactive_user.html`


### `POST /addcards`
adds a flashcard to the user's db and redirects to dashboard.index. 
Handles flashcards being added to current_user or to student by using a hidden input for student.id:
<input type="hidden" name="student_id" value="{{ student.id }}">

### `GET /edit_cards`
- Renders edit.html with users flashcards for editing. Uses querystrings (e.g.  <a href="{{ url_for('your_blueprint.edit_card') }}?student_id={{ student.id }}">) which can be retrieved with `request.args.get("student_id")` to handle teachers and admin managing students flashcards.

- Checks if student is assigned to teacher making the request. Admin has access to all flashcards. 

### `POST /edit_card/<int:card_id>` 
- Uses the card id and information on the form to update flashcard. Handles student, teacher and admin requests. 

### `GET /flashcards`
- Renders flashcards.html, with forms to add flashcards using Google Translate from Portuguese to English, to add both 'question' and 'answer' and icon to render flashcards in edit mode. 

###  `GET /study`
- Returns `flashcards/study.html` populated with flashcards where
`next_review` is on or before the current UTC time (or None). Checks for `student_id`, which signals the study route is being called from `manage_student_cards` by a teacher, and triggers different behavior from `study.js`

### `POST /review_flashcard`
- Endpoint triggered by `study.js` when a user rates a card.
- Expects JSON payload: `{"card_id": <id>, "rating": 1 | 2 | 3}`.
- Updates the flashcard’s level, ease, interval, and scheduling, awarding points to the appropriate user.
- Checks whether the reviewed card is the last one being studied for the day, triggering `update_study_streak()`
- Returns `{"status": "success"}` on success, or `404` if the card is not found.

### `GET /flashcard/manage/<int:student_id>`
- Renders `flashcards/manage_student_cards.html` so a teacher (or admin) can
  edit, delete, or add flashcards for a specific student.
- Teachers may only manage students assigned to them. Admins can manage any student.
- Returns `{"status": "success"}` or `403` if the user lacks permission or the student does not belong to that teacher.

## Audiobook

### `GET /audiobooks`
Serves `audiobook/audiobooks.html`, allowing the user to upload an audio file and a matching text transcript.

### `POST /translate`
Receives JSON `{"text": "<selected string>"}` 



## Calendar

### `GET /calendar/<user_name>`
- Looks up a teacher by `user_name` and renders a public page with the teacher’s available slots.
- Returns **404** if the teacher is not found.  
 

### `GET /calendar/settings` *(teachers only)*
- Shows the `CalendarSettingsForm` for the logged‑in teacher to adjust working hours, lesson duration and weekend availability.
- Requires authentication and `teacher` role.  
  
### `POST /calendar/settings` *(teachers only)*
- Save form changes to `CalendarSettings` in the database, flashes a success message, and redirects back to the settings page.  
 

## Services

### `google_calendar.get_teacher_availability(user_id, days=5)`
- Loads Google service‑account credentials (expects `GOOGLE_APPLICATION_CREDENTIALS` in the environment).
- Combines the teacher’s `CalendarSettings` with Google Calendar **free/busy** data.
- Generates half‑hour slots within the configured working window, skipping busy periods, and returns a dictionary keyed by date.  

### `translate.translate_text(text, target_language="pt")`
 Receives a text string when it's called from audiobook/translate, sends it to the Google Translate API and returns its Portuguese translation.

Notes:
- Uses the Google Cloud Translate v2 API.
- Authenticated via service account loaded from GOOGLE_APPLICATION_CREDENTIALS in .env.
- Default target language is pt (Portuguese).
- Input is safely parsed and sanitized via Google’s API; no user input is executed.





## Progress

### `GET /progress/leaderboard`
- Renders `progress/leaderboard.html`, showing leaderboard data for students and teachers.  
- Requires authentication (`@login_required`).  

#### Response Context:
| Key              | Type        | Description                                    |
|------------------|-------------|------------------------------------------------|
| `students`       | list[User]  | All users with role `"student"`                |
| `teachers`       | list[User]  | All users with role `"teacher"`                |
| `total_students` | int         | Total number of students                       |
| `total_teachers` | int         | Total number of teachers                       |
| `top_students`   | list[User]  | Top 3 students ordered by `max_points` (desc)  |



