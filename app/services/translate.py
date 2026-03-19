from html import unescape
from google.cloud import translate_v2 as translate
from flask_login import current_user

_client = None


def _get_client() -> translate.Client:
    global _client
    if _client is None:
        _client = translate.Client()
    return _client


def _default_target_language() -> str:
    try:
        lang = getattr(current_user, "learning_language", None)
    except Exception:
        lang = None

    if isinstance(lang, str):
        if lang.startswith("pt"):
            return "en"
        if lang.startswith("en"):
            return "pt"

    return "pt"


def translate_text(text: str, target_language: str | None = None) -> str:
    if not text:
        return ""

    if target_language is None:
        target_language = _default_target_language()

    client = _get_client()
    result = client.translate(
        text,
        target_language=target_language,
        format_="text",
    )
    return unescape(result["translatedText"])