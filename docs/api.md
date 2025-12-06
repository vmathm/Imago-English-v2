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
- Sets flashcard.interval=1, flashcard.ease=1.3 and flashcard.next_review=current_date

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


### `POST /flashcard/flag_card`
- Mark a flashcard as problematic during study mode by using the “😵 Preciso de ajuda com esse flashcard.” button and selecting one of the help options.

- Request:  
```json
{
  "card_id": 123,
  "reason": "dont_understand" | "talk_next_class" | "has_mistake"
}

```

- Append a note to the flashcard question indicating the problem. 
- Push next_review 7 days ahead, making time for teacher to review. 
- Remove it from the current study session (handled on the frontend).
- Mark reviewed_by_tc = False, so it re-enters the teacher’s review queue.
- Does not affect streak or points.


## Audiobook

### `GET /audiobooks`
Serves `audiobook/audiobooks.html`, allowing the user to upload an audio file and a matching text transcript.

### `POST /translate`
Receives JSON `{"text": "<selected string>"}` 

### `GET /audiobook/view`
- **Auth**: `login_required` (student or teacher)
- **Purpose**: Show the audiobook page for the logged-in user.
- **Behaviour**:
  - Looks up the `UserAudiobook` row by `current_user.id`.
  - If a `text_url` exists, fetches the `.txt` from GCS and passes the text into the template as `text_content`.
  - Renders `audiobooks.html`:
    - Shows an audio player if `audio_url` is set.
    - Shows the text in the reader area if `text_content` is available.
    - Integrates with `static/js/audiobook.js` so users can select text, translate, and create flashcards.

### `POST /audiobook/assign_audiobook/<user_id>`
- **Auth**: `login_required`, and `current_user.is_teacher()` or `current_user.is_admin()` must be true.
- **Called from**: Teacher dashboard modal in `partials/teacher_dashboard.html`.
- **Form**: `UserAudiobookForm`
  - `text_file` – optional `.txt` file
  - `audio_file` – optional `.mp3` file
- **Behaviour**:
  - Loads or creates a `UserAudiobook` row for the target user.
  - Derives the `title` from the uploaded filename (prefers the text file name, falls back to audio).
  - For each file type:
    - If a new file was provided:
      - Deletes any existing GCS object for that field.
      - Uploads the new file and updates the corresponding URL.
    - If no new file was provided:
      - Deletes any existing GCS object for that field and clears the URL.
  - If both `text_url` and `audio_url` end up empty:
    - Deletes the `UserAudiobook` row.
    - Flashes a message indicating the buttons for manually uploading text and audio is now available for the student.
  - Redirects back to `/dashboard`.



## Calendar

### `GET /calendar/<user_name>`
- Looks up a teacher by `user_name` and renders a public page with the teacher’s available slots.
- Returns **404** if the teacher is not found.  
 
* Seeded teachers have a valid email address to enable demo view.   

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
 Receives a text string when it's called from audiobook/translate, sends it to the Google Translate API and returns its translation according to `user.learning_language` (if it's `en`, target language is `pt-BR` and the opposite otherwise).

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



