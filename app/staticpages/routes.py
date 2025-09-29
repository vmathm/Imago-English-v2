from flask import Blueprint, render_template

bp = Blueprint("staticpages", __name__)

@bp.route("/terms")
def terms():
    return render_template("staticpages/terms.html")

@bp.route("/privacy")
def privacy():
    return render_template("staticpages/privacy.html")