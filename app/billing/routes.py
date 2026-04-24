'''
How do I want Billing to look like: 

if user.teacher -> show billing info for their students + link to Asaas dashboard:
- check the current plan condition of each of their students, and if they are due for payment.
- see the payment history of each student, and if they are due for payment, show a link to the payment page.
- ASAAS settings. 

if user.admin -> show billing info for all teachers + link to Asaas dashboard (admin user has product to charge teachers)

if user.student -> show their billing info + if due, show link to payment page
'''



from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from flask import abort, jsonify, render_template, redirect, request, url_for, flash
from flask_login import current_user, login_required
from werkzeug.exceptions import Forbidden

from app.billing import bp
from app.billing.forms import AsaasSettingsForm, PlanForm, StudentBillingForm, SubscriptionForm
from app.database import db_session
from app.models.billing import Payment, Subscription, Tenant, TenantBillingAccount, Plan
from app.models.user import User
from app.services.asaas import SP_TZ, AsaasServiceError, ensure_customer_for_user, create_subscription as asaas_create_subscription, get_subscription_payments, get_pix_qr_code, get_subscription, normalize_asaas_status, parse_asaas_date, parse_asaas_due_date_as_sp_end_of_day
from sqlalchemy import or_
from app.extensions import csrf


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

    assigned_students = (
    db_session.query(User)
    .filter_by(role="student", assigned_teacher_id=current_user.id)
    .order_by(User.name.asc())
    .all()
)

    plan_form.eligible_student_ids.choices = [
    (
        student.id,
        f"{student.name} ({student.email})" if student.email else student.name
    )
    for student in assigned_students
]
    

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
        assigned_students=assigned_students,
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

    assigned_students = (
        db_session.query(User)
        .filter_by(role="student", assigned_teacher_id=current_user.id)
        .order_by(User.name.asc())
        .all()
    )

    plan_form.eligible_student_ids.choices = [
        (
            student.id,
            f"{student.name} ({student.email})" if student.email else student.name
        )
        for student in assigned_students
    ]

    if not plan_form.validate_on_submit():
        flash("Please correct the plan form errors.", "danger")
        return redirect(url_for("billing.index"))

    if (
        not plan_form.available_to_all_students.data
        and not plan_form.eligible_student_ids.data
    ):
        flash("Select at least one student or mark the plan as available to all students.", "danger")
        return redirect(url_for("billing.index"))

    allowed_student_ids = {student.id for student in assigned_students}
    submitted_student_ids = set(plan_form.eligible_student_ids.data or [])

    if not submitted_student_ids.issubset(allowed_student_ids):
        flash("One or more selected students are invalid.", "danger")
        return redirect(url_for("billing.index"))

    plan = Plan(
        tenant_id=tenant.id,
        name=plan_form.name.data.strip(),
        amount_cents=int(plan_form.amount_reais.data) * 100,
        currency=plan_form.currency.data,
        interval=plan_form.interval.data,
        active=plan_form.active.data,
        available_to_all_students=plan_form.available_to_all_students.data,
    )

    db_session.add(plan)
    db_session.flush()

    if not plan_form.available_to_all_students.data:
        selected_students = (
            db_session.query(User)
            .filter(User.id.in_(plan_form.eligible_student_ids.data))
            .all()
        )
        plan.eligible_students = selected_students

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





@bp.route("/subscription", methods=["GET"])
@login_required
def student_subscription():
    if current_user.is_admin() or current_user.is_teacher():
        return redirect(url_for("billing.index"))

    subscription = (
        db_session.query(Subscription)
        .filter_by(user_id=current_user.id)
        .order_by(Subscription.created_at.desc())
        .first()
    )

    available_plans = []

    if current_user.assigned_teacher_id:
        tenant = (
            db_session.query(Tenant)
            .filter_by(owner_user_id=current_user.assigned_teacher_id)
            .first()
        )

        if tenant:
            available_plans = (
                db_session.query(Plan)
                .filter(
                    Plan.tenant_id == tenant.id,
                    Plan.active.is_(True),
                    or_(
                        Plan.available_to_all_students.is_(True),
                        Plan.eligible_students.any(User.id == current_user.id),
                    ),
                )
                .order_by(Plan.amount_cents.asc(), Plan.created_at.desc())
                .all()
            )

    latest_payment = (
    db_session.query(Payment)
    .filter_by(user_id=current_user.id)
    .order_by(Payment.id.desc())
    .first()
)
    
    payment_date_sp = None
    expiring_date_sp = None
    days_left = None

    if latest_payment and latest_payment.paid_at:
        payment_date_sp = latest_payment.paid_at.astimezone(SP_TZ)

    if subscription and subscription.current_period_end:
        expiring_date_sp = subscription.current_period_end.astimezone(SP_TZ)

        now_sp = datetime.now(timezone.utc).astimezone(SP_TZ)
        days_left = max((expiring_date_sp.date() - now_sp.date()).days, 0)


    billing_form = StudentBillingForm()

    is_pix_valid = (
    latest_payment
    and latest_payment.status in ["pending", "awaiting_payment"]
    and latest_payment.pix_expires_at
    and latest_payment.pix_expires_at > datetime.now(timezone.utc)
)
    sp_tz = ZoneInfo("America/Sao_Paulo")
    
    return render_template(
        "billing/student_billing.html",
        subscription=subscription,
        billing_form=billing_form,
        available_plans=available_plans,
        latest_payment=latest_payment,
        payment_date_sp=payment_date_sp,
        expiring_date_sp=expiring_date_sp,
        days_left=days_left,
        is_pix_valid=is_pix_valid,
        sp_tz=sp_tz
    )


@bp.route("/subscription", methods=["POST"])
@login_required
def create_student_subscription():
    if current_user.is_admin() or current_user.is_teacher():
        return redirect(url_for("billing.index"))

    form = StudentBillingForm()

    if not form.validate_on_submit():
        print("DEBUG subscription form.errors:", form.errors)
        print("DEBUG subscription form.data:", form.data)
        flash(f"Dados de cobrança inválidos: {form.errors}", "danger")
        return redirect(url_for("billing.student_subscription"))

    if not current_user.assigned_teacher_id:
        flash("Nenhum plano está disponível para sua conta.", "warning")
        return redirect(url_for("billing.student_subscription"))

    tenant = (
        db_session.query(Tenant)
        .filter_by(owner_user_id=current_user.assigned_teacher_id)
        .first()
    )

    if tenant is None:
        flash("Nenhum plano está disponível para sua conta.", "warning")
        return redirect(url_for("billing.student_subscription"))

    try:
        plan_id = int(form.plan_id.data)
    except (TypeError, ValueError):
        flash("Plano inválido.", "danger")
        return redirect(url_for("billing.student_subscription"))

    plan = (
        db_session.query(Plan)
        .filter(
            Plan.id == plan_id,
            Plan.tenant_id == tenant.id,
            Plan.active.is_(True),
            or_(
                Plan.available_to_all_students.is_(True),
                Plan.eligible_students.any(User.id == current_user.id),
            ),
        )
        .first()
    )

    if plan is None:
        flash("Plano inválido ou indisponível para sua conta.", "danger")
        return redirect(url_for("billing.student_subscription"))

    # Block a new signup flow if there is already a subscription in progress.
    # This does NOT mean the user has paid access yet.
    existing_subscription = (
        db_session.query(Subscription)
        .filter(
            Subscription.user_id == current_user.id,
            Subscription.status.in_(["active", "inactive"]),
        )
        .order_by(Subscription.created_at.desc())
        .first()
    )

    if existing_subscription:
        latest_existing_payment = (
            db_session.query(Payment)
            .filter(Payment.subscription_id == existing_subscription.id)
            .order_by(Payment.created_at.desc())
            .first()
        )

        if latest_existing_payment and latest_existing_payment.status in [
            "pending",
            "awaiting_payment",
            "received",
            "confirmed",
        ]:
            flash(
                "Você já possui uma cobrança/assinatura em andamento. "
                "Use o pagamento atual ou aguarde a atualização.",
                "warning",
            )
            return redirect(url_for("billing.student_subscription"))

    ASAAS_CYCLE_MAP = {
        "monthly": "MONTHLY",
        "month": "MONTHLY",
        "weekly": "WEEKLY",
        "yearly": "YEARLY",
    }

    try:
        customer_id = ensure_customer_for_user(
            tenant_id=plan.tenant_id,
            user=current_user,
            cpf_cnpj=form.cpf_cnpj.data,
        )

        asaas_subscription = asaas_create_subscription(
            tenant_id=plan.tenant_id,
            customer_id=customer_id,
            amount_cents=plan.amount_cents,
            description=f"Assinatura {plan.name}",
            cycle=ASAAS_CYCLE_MAP.get(plan.interval, "MONTHLY"),
            billing_type="PIX",
        )


        subscription = Subscription(
            tenant_id=plan.tenant_id,
            user_id=current_user.id,
            plan_id=plan.id,
            status=(asaas_subscription.get("status") or "inactive").lower(),
            provider="asaas",
            provider_subscription_id=asaas_subscription.get("id"),
        )

        db_session.add(subscription)
        db_session.flush()

        payments_data = get_subscription_payments(
            tenant_id=plan.tenant_id,
            subscription_id=asaas_subscription["id"],
        )

        payments_list = payments_data.get("data", [])
        first_payment = payments_list[0] if payments_list else None

        if not first_payment:
            raise AsaasServiceError(
                "Subscription created, but no generated payment was returned by Asaas."
            )

        payment = Payment(
            tenant_id=plan.tenant_id,
            user_id=current_user.id,
            subscription_id=subscription.id,
            provider="asaas",
            provider_payment_id=first_payment["id"],
            status=(first_payment.get("status") or "pending").lower(),
            amount_cents=plan.amount_cents,
            currency=plan.currency,
            billing_type=first_payment.get("billingType", "PIX"),
        )
        db_session.add(payment)

        pix_data = get_pix_qr_code(
            tenant_id=plan.tenant_id,
            payment_id=first_payment["id"],
        )

        expires_str = pix_data.get("expirationDate")
        expires_at = None

        if expires_str:
            try:
                expires_at = datetime.fromisoformat(expires_str)
                if expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)
            except ValueError:
                expires_at = None

        payment.pix_qr_code = pix_data.get("encodedImage")
        payment.pix_copy_paste = pix_data.get("payload")
        payment.pix_expires_at = expires_at

    
        db_session.commit()

    except AsaasServiceError as exc:
        db_session.rollback()
        flash(str(exc), "danger")
        return redirect(url_for("billing.student_subscription"))
    except Exception as exc:
        db_session.rollback()
        print("DEBUG create_student_subscription unexpected error:", exc)
        flash("Não foi possível gerar a cobrança no momento.", "danger")
        return redirect(url_for("billing.student_subscription"))

    flash(
        "Cobrança gerada com sucesso. Faça o pagamento para ativar sua assinatura.",
        "success",
    )
    return redirect(url_for("billing.student_subscription"))




PAID_PAYMENT_STATUSES = {"received", "confirmed", "paid"}
OPEN_PAYMENT_STATUSES = {"pending", "awaiting_payment"}
PROBLEM_PAYMENT_STATUSES = {"overdue", "failed", "canceled", "cancelled"}

@bp.route("/webhook/asaas", methods=["POST"])
@csrf.exempt
def asaas_webhook():
    data = request.get_json(silent=True) or {}

    event = data.get("event", "")
    payment_data = data.get("payment") or {}
    subscription_data = data.get("subscription") or {}

    if event == "PAYMENT_CREATED":
    # optional: update local payment status to pending
        return jsonify({"ok": True}), 200

    provider_payment_id = payment_data.get("id")
    provider_subscription_id = (
        payment_data.get("subscription")
        or subscription_data.get("id")
    )

    payment_status = normalize_asaas_status(payment_data.get("status"))

    print("=== ASAAS WEBHOOK DEBUG ===")
    print("event:", event)
    print("provider_payment_id:", provider_payment_id)
    print("provider_subscription_id:", provider_subscription_id)
    print("payment_status:", payment_status)

    try:
        payment = None

        if provider_payment_id:
            payment = (
                db_session.query(Payment)
                .filter_by(provider_payment_id=provider_payment_id)
                .first()
            )

        if payment is None and provider_subscription_id:
            payment = (
                db_session.query(Payment)
                .join(Subscription, Payment.subscription_id == Subscription.id)
                .filter(Subscription.provider_subscription_id == provider_subscription_id)
                .order_by(Payment.created_at.desc())
                .first()
            )

        if payment is None:
            print("Webhook received, but no local payment matched.")
            return jsonify({"ok": True, "message": "payment not found locally"}), 200

        if payment_status:
            payment.status = payment_status

        subscription = (
            db_session.query(Subscription)
            .filter_by(id=payment.subscription_id)
            .first()
        )

        user = db_session.query(User).filter_by(id=payment.user_id).first()

        if user is None:
            db_session.commit()
            return jsonify({"ok": True, "message": "user not found"}), 200


        if payment_status in PAID_PAYMENT_STATUSES:
            if payment.paid_at is None:
                payment.paid_at = datetime.now(timezone.utc)

            user.active = True

            if subscription is not None:
                subscription.status = "active"
                subscription.current_period_start = payment.paid_at

                if subscription.provider_subscription_id:
                    try:
                        asaas_subscription = get_subscription(
                            tenant_id=subscription.tenant_id,
                            subscription_id=subscription.provider_subscription_id,
                        )
                        next_due_date = parse_asaas_due_date_as_sp_end_of_day(
                            asaas_subscription.get("nextDueDate")
                        )
                        if next_due_date is not None:
                            subscription.current_period_end = next_due_date

                    except AsaasServiceError as exc:
                        print("Could not refresh Asaas subscription after payment:", exc)


        elif payment_status in OPEN_PAYMENT_STATUSES:
            if subscription is not None and not subscription.status:
                subscription.status = "pending"

        elif payment_status in PROBLEM_PAYMENT_STATUSES:
            # conservative first version:
            # do not deactivate automatically unless you are sure that is the rule you want
            if subscription is not None:
                subscription.status = payment_status

        db_session.commit()
        return jsonify({"ok": True}), 200

    except Exception as exc:
        db_session.rollback()
        print("ASAAS WEBHOOK ERROR:", exc)
        return jsonify({"ok": False}), 500