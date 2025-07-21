from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required

bp = Blueprint('audiobook', __name__, url_prefix='/audiobook')

@bp.route('/audiobooks')
@login_required
def audiobooks():
    return render_template('/audiobooks.html')


@bp.route("/translate", methods=["POST"])
@login_required
def translate():
    print("Received request to /translate endpoint")
    """
    Placeholder endpoint for Google Translate.
    Returns a dummy translation for now.
    """
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "Missing 'text' in request"}), 400

    text = data["text"]
    print(f"Received text for translation: {text}")
    return jsonify({"translation": "api call"})