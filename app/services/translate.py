from html import unescape

from flask_login import current_user
from google.cloud import translate_v2 as translate


MAX_TRANSLATION_CHARS = 2000

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

    text = text.strip()

    if len(text) > MAX_TRANSLATION_CHARS:
        raise ValueError(
            f"Translation text exceeds the {MAX_TRANSLATION_CHARS}-character limit."
        )

    if target_language is None:
        target_language = _default_target_language()

    client = _get_client()
    result = client.translate(
        text,
        target_language=target_language,
        format_="text",
    )

    return unescape(result["translatedText"])