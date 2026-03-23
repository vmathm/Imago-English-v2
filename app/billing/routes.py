from flask import render_template, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.exceptions import Forbidden

from app.billing import bp

'''
How do I want Billing to look like: 

if user.teacher -> show billing info for their students + link to Asaas dashboard:
- check the current plan condition of each of their students, and if they are due for payment.
- see the payment history of each student, and if they are due for payment, show a link to the payment page.
- ASAAS settings. 

if user.admin -> show billing info for all teachers + link to Asaas dashboard (admin user has product to charge teachers)

if user.student -> show their billing info + if due, show link to payment page
'''
@bp.route("/")
@login_required
def index():
    if current_user.is_admin():
        return redirect(url_for("billing.admin_dashboard"))
    elif current_user.is_teacher():
        return redirect(url_for("billing.teacher_dashboard"))
    elif current_user.is_student():
        return redirect(url_for("billing.student_dashboard"))
    else:
        raise Forbidden()