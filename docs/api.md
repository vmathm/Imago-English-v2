# API Endpoints (so far)

## Auth


### `GET /auth/test`
- Returns: `"Auth route is working!"`
- Purpose: Test that the auth blueprint is registered and working properly

More routes will be added as blueprints are developed.


### `GET /dev_login`
- Simulates logging in as an existing user. Useful for testing features without going through the Google OAuth flow.

#### Requirements:
- Flask app must be running in **debug mode**  
- `ALLOW_DEV_LOGIN = True` in .env

#### Response:
- Redirects the user to the dashboard (`/dashboard`) after logging them in
- Returns `403` if disabled or not in debug mode
- Returns `404` if the user does not exist




## Dashboard

### `GET /index`
loads dashboard.html with form for flashcards.


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
`next_review` is on or before the current UTC time (or None).


