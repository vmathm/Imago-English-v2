from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required
from app.services.translate import translate_text

bp = Blueprint('audiobook', __name__, url_prefix='/audiobook')

@bp.route('/audiobooks')
@login_required
def audiobooks():
    return render_template('/audiobooks.html')


@bp.route("/translate", methods=["POST"])
@login_required
def translate_route():
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "Missing 'text' in request"}), 400

    translation = translate_text(data["text"])
    return jsonify({"translation": translation})