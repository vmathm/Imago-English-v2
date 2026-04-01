'''
How do I want Billing to look like: 

if user.teacher -> show billing info for their students + link to Asaas dashboard:
- check the current plan condition of each of their students, and if they are due for payment.
- see the payment history of each student, and if they are due for payment, show a link to the payment page.
- ASAAS settings. 

if user.admin -> show billing info for all teachers + link to Asaas dashboard (admin user has product to charge teachers)

if user.student -> show their billing info + if due, show link to payment page
'''

from flask import abort, render_template, redirect, url_for, flash
from flask_login import current_user, login_required
from werkzeug.exceptions import Forbidden, abort

from app.billing import bp
from app.billing.forms import AsaasSettingsForm, PlanForm, SubscriptionForm
from app.database import db_session
from app.models.billing import Subscription, Tenant, TenantBillingAccount, Plan
from app.models.user import User


def generate_slug(name: str) -> str:
    slug = name.lower().strip().replace(" ", "-")
    slug = "".join(ch for ch in slug if ch.isalnum() or ch == "-")
    slug = "-".join(part for part in slug.split("-") if part)
    return slug or "tenant"


@bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    if current_user.is_admin():
        return render_template("billing/index.html", view_type="admin")

    if not current_user.is_teacher():
        raise Forbidden("You are not allowed to access billing settings.")

    tenant = (
        db_session.query(Tenant)
        .filter_by(owner_user_id=current_user.id)
        .first()
    )

    if tenant is None:
        base_slug = generate_slug(current_user.name or "tenant")
        slug = base_slug
        counter = 2

        while db_session.query(Tenant).filter_by(slug=slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1

        tenant = Tenant(
            owner_user_id=current_user.id,
            name=(current_user.name or "Tenant").strip(),
            slug=slug,
        )
        db_session.add(tenant)
        db_session.commit()

    billing_account = (
        db_session.query(TenantBillingAccount)
        .filter_by(tenant_id=tenant.id)
        .first()
    )

    settings_form = AsaasSettingsForm()

    if settings_form.validate_on_submit():
        api_key_input = (settings_form.api_key.data or "").strip()
        webhook_token_input = (settings_form.webhook_auth_token.data or "").strip()

        if billing_account is None:
            if not api_key_input or not webhook_token_input:
                flash("API key and webhook auth token are required.", "danger")
            else:
                billing_account = TenantBillingAccount(
                    tenant_id=tenant.id,
                    provider=settings_form.provider.data or "asaas",
                    is_sandbox=settings_form.is_sandbox.data,
                    active=settings_form.active.data,
                    api_key=api_key_input,
                    webhook_auth_token=webhook_token_input,
                )
                db_session.add(billing_account)
                db_session.commit()
                flash("Billing settings saved successfully.", "success")
                return redirect(url_for("billing.index"))
        else:
            billing_account.provider = settings_form.provider.data or "asaas"
            billing_account.is_sandbox = settings_form.is_sandbox.data
            billing_account.active = settings_form.active.data

            if api_key_input:
                billing_account.api_key = api_key_input

            if webhook_token_input:
                billing_account.webhook_auth_token = webhook_token_input

            db_session.commit()
            flash("Billing settings saved successfully.", "success")
            return redirect(url_for("billing.index"))

    if billing_account and not settings_form.is_submitted():
        settings_form.provider.data = billing_account.provider
        settings_form.is_sandbox.data = billing_account.is_sandbox
        settings_form.active.data = billing_account.active

    students = (
        db_session.query(User)
        .filter_by(role="student", assigned_teacher_id=current_user.id)
        .order_by(User.name.asc())
        .all()
    )

    plan_form = PlanForm()

    plans = (
    db_session.query(Plan)
    .filter_by(tenant_id=tenant.id)
    .order_by(Plan.active.desc(), Plan.created_at.desc())
    .all()
    )
    

    subscription_form = SubscriptionForm()
    subscription_form.student_id.choices = [
    (student.id, f"{student.name} ({student.email})")
    for student in students
    ]

    subscription_form.plan_id.choices = [
    (plan.id, f"{plan.name} — R$ {plan.amount_cents / 100:.2f}")
    for plan in plans
    if plan.active
    ]


    subscriptions = (
    db_session.query(Subscription)
    .filter_by(tenant_id=tenant.id)
    .order_by(Subscription.created_at.desc())
    .all()
)

    return render_template(
        "billing/index.html",
        view_type="teacher",
        tenant=tenant,
        billing_account=billing_account,
        students=students,
        settings_form=settings_form,
        plan_form=plan_form,
        plans=plans,
        subscription_form=subscription_form,
        subscriptions=subscriptions,
    )




@bp.route("/plans/create", methods=["POST"])
@login_required
def create_plan():
    if current_user.is_admin():
        return redirect(url_for("billing.index"))

    if not current_user.is_teacher():
        raise Forbidden("You are not allowed to manage billing plans.")

    tenant = (
        db_session.query(Tenant)
        .filter_by(owner_user_id=current_user.id)
        .first()
    )

    if tenant is None:
        base_slug = generate_slug(current_user.name or "tenant")
        slug = base_slug
        counter = 2

        while db_session.query(Tenant).filter_by(slug=slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1

        tenant = Tenant(
            owner_user_id=current_user.id,
            name=(current_user.name or "Tenant").strip(),
            slug=slug,
        )
        db_session.add(tenant)
        db_session.commit()

    plan_form = PlanForm()

    if not plan_form.validate_on_submit():
        flash("Please correct the plan form errors.", "danger")
        return redirect(url_for("billing.index"))

    plan = Plan(
        tenant_id=tenant.id,
        name=plan_form.name.data.strip(),
        amount_cents=int(plan_form.amount_reais.data) * 100,
        currency=plan_form.currency.data,
        interval=plan_form.interval.data,
        active=plan_form.active.data,
    )

    db_session.add(plan)
    db_session.commit()

    flash("Plan created successfully.", "success")
    return redirect(url_for("billing.index"))



@bp.route("/plans/<int:plan_id>/toggle", methods=["POST"])
@login_required
def toggle_plan(plan_id):
    if current_user.is_admin():
        return redirect(url_for("billing.index"))

    if not current_user.is_teacher():
        raise Forbidden("You are not allowed to manage billing plans.")

    tenant = (
        db_session.query(Tenant)
        .filter_by(owner_user_id=current_user.id)
        .first()
    )
    if tenant is None:
        abort(404)

    plan = (
        db_session.query(Plan)
        .filter_by(id=plan_id, tenant_id=tenant.id)
        .first()
    )
    if plan is None:
        abort(404)

    plan.active = not plan.active
    db_session.commit()

    flash(
        f'Plan "{plan.name}" {"activated" if plan.active else "deactivated"}.',
        "success",
    )
    return redirect(url_for("billing.index"))




@bp.route("/subscriptions/create", methods=["POST"])
@login_required
def create_subscription():
    if current_user.is_admin():
        return redirect(url_for("billing.index"))

    if not current_user.is_teacher():
        raise Forbidden("You are not allowed to manage subscriptions.")

    tenant = (
        db_session.query(Tenant)
        .filter_by(owner_user_id=current_user.id)
        .first()
    )
    if tenant is None:
        abort(404)

    students = (
        db_session.query(User)
        .filter_by(role="student", assigned_teacher_id=current_user.id)
        .order_by(User.name.asc())
        .all()
    )

    plans = (
        db_session.query(Plan)
        .filter_by(tenant_id=tenant.id)
        .order_by(Plan.active.desc(), Plan.created_at.desc())
        .all()
    )

    subscription_form = SubscriptionForm()
    subscription_form.student_id.choices = [
        (student.id, f"{student.name} ({student.email})")
        for student in students
    ]
    subscription_form.plan_id.choices = [
        (plan.id, f"{plan.name} — R$ {plan.amount_cents / 100:.2f}")
        for plan in plans
        if plan.active
    ]

    if not subscription_form.validate_on_submit():
        flash("Please correct the subscription form errors.", "danger")
        return redirect(url_for("billing.index"))

    student = (
        db_session.query(User)
        .filter_by(
            id=subscription_form.student_id.data,
            role="student",
            assigned_teacher_id=current_user.id,
        )
        .first()
    )
    if student is None:
        abort(404)

    plan = (
        db_session.query(Plan)
        .filter_by(
            id=subscription_form.plan_id.data,
            tenant_id=tenant.id,
            active=True,
        )
        .first()
    )
    if plan is None:
        abort(404)

    existing_subscription = (
        db_session.query(Subscription)
        .filter(
            Subscription.tenant_id == tenant.id,
            Subscription.user_id == student.id,
            Subscription.plan_id == plan.id,
            Subscription.status.in_(["active", "incomplete", "past_due"]),
        )
        .first()
    )

    if existing_subscription:
        flash("This student already has an active subscription for this plan.", "warning")
        return redirect(url_for("billing.index"))

    subscription = Subscription(
        tenant_id=tenant.id,
        user_id=student.id,
        plan_id=plan.id,
        status="incomplete",
        provider="asaas",
    )
    print(subscription)
    db_session.add(subscription)
    db_session.commit()

    flash("Subscription created locally.", "success")
    return redirect(url_for("billing.index"))



@bp.route("/subscriptions/<int:subscription_id>/cancel", methods=["POST"])
@login_required
def cancel_subscription(subscription_id):
    if current_user.is_admin():
        return redirect(url_for("billing.index"))

    if not current_user.is_teacher():
        raise Forbidden("You are not allowed to manage subscriptions.")

    tenant = (
        db_session.query(Tenant)
        .filter_by(owner_user_id=current_user.id)
        .first()
    )
    if tenant is None:
        abort(404)

    subscription = (
        db_session.query(Subscription)
        .filter_by(id=subscription_id, tenant_id=tenant.id)
        .first()
    )
    if subscription is None:
        abort(404)

    if subscription.status == "canceled":
        flash("Subscription is already canceled.", "warning")
        return redirect(url_for("billing.index"))

    subscription.status = "canceled"
    db_session.commit()

    flash("Subscription canceled locally.", "success")
    return redirect(url_for("billing.index"))