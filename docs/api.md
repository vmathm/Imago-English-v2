# API Endpoints (so far)

## Auth


### `GET /auth/test`
- Returns: `"Auth route is working!"`
- Purpose: Test that the auth blueprint is registered and working properly

More routes will be added as blueprints are developed.


### `GET /auth/dev-login/<user_id>`
- Simulates logging in as an existing user. Useful for testing features without going through the Google OAuth flow.
- Returns `404` if the user does not exist

#### Requirements:
- Flask app must be running in **debug mode**  
- `ALLOW_DEV_LOGIN = True` in .env

#### Response:
- Redirects the user to the dashboard (`/dashboard`) after logging them in
- Returns `403` if disabled or not in debug mode
- Returns `404` if the user does not exist



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
- Toggles `user.active` (also affects is_active since it returns self.active)

### `POST /admin/update_student_level`
- Updates `user.level` (A1 to C2)


## Dashboard

### `GET /index`
- Loads `dashboard.html` according to user type, rendering necessary forms and partials. 


## Flashcards
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
- Returns `{"status": "success"}` on success, or `404` if the card is not found.

### `GET /flashcard/manage/<int:student_id>`
- Renders `flashcards/manage_student_cards.html` so a teacher (or admin) can
  edit, delete, or add flashcards for a specific student.
- Teachers may only manage students assigned to them. Admins can manage any student.
- Returns `{"status": "success"}` or `403` if the user lacks permission or the student does not belong to that teacher.

## Audiobook

### `GET /load`
Serves `audiobook/audiobooks.html`, allowing the user to upload an audio file and a matching text transcript.

### `POST /translate`
Receives JSON `{"text": "<selected string>"}` and currently returns `{"translation": "api call"}`.  
Later this will integrate with Google Translate to return a real translation.