from google.cloud import translate_v2 as translate
from flask_login import current_user

_client = None


def _get_client() -> translate.Client:
    """
    Lazily create a single Translate client.
    """
    global _client
    if _client is None:
        _client = translate.Client()
    return _client


def _default_target_language() -> str:
    """
    Decide translation target based on the user's learning language.

    Assumptions (you can tweak if needed):
    - learning_language == "en"   → Brazilian user learning English.
      They are reading **English** and want meaning in **Portuguese** → target "pt".
    - learning_language starts with "pt" (e.g. "pt-BR") → user learning Brazilian Portuguese.
      They are reading **Portuguese** and want meaning in **English** → target "en".

    If there's no logged-in user or no learning_language, default to "pt"
    to match your old behavior.
    """
    try:
        lang = getattr(current_user, "learning_language", None)
    except Exception:
        lang = None

    if isinstance(lang, str):
        if lang.startswith("pt"):
            # user learning Portuguese → show meaning in English
            return "en"
        if lang.startswith("en"):
            # user learning English → show meaning in Portuguese
            return "pt"

    # Fallback: keep old default
    return "pt"


def translate_text(text: str, target_language: str | None = None) -> str:
    """
    Translate arbitrary text using Google Cloud Translate v2.

    - If target_language is provided, it is used as-is.
    - If target_language is None, we pick a default based on the
      current_user.learning_language (see _default_target_language).
    """
    if not text:
        return ""

    if target_language is None:
        target_language = _default_target_language()

    client = _get_client()
    result = client.translate(text, target_language=target_language)
    return result["translatedText"]
