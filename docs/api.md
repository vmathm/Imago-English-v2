# API Endpoints (so far)

## Auth

### `GET /auth/test`
- Returns: `"Auth route is working!"`
- Purpose: Test that the auth blueprint is registered and working properly

More routes will be added as blueprints are developed.


### `GET /dev-login/<user_id>`
- Simulates logging in as an existing user. Useful for testing features without going through the Google OAuth flow.

#### Requirements:
- Flask app must be running in **debug mode**  
- `ALLOW_DEV_LOGIN = True` in .env

#### Response:
- Redirects the user to the dashboard (`/dashboard`) after logging them in
- Returns `403` if disabled or not in debug mode
- Returns `404` if the user does not exist