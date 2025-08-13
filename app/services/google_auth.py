from flask_dance.contrib.google import google

def get_google_user_info():
    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        raise Exception("Failed to fetch Google user info")
    return resp.json()
