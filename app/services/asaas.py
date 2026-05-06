from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from logging import config
import re
from urllib import response
from zoneinfo import ZoneInfo

from flask import jsonify
import requests

from app.database import db_session
from app.models.billing import Payment, TenantBillingAccount
from app.models.user import User


class AsaasServiceError(Exception):
    pass


def _normalize_cpf_cnpj(value: str) -> str:
    digits = re.sub(r"\D", "", value or "")
    return digits


def _raise_for_asaas_error(response: requests.Response, action: str) -> None:
    if response.ok:
        return

    try:
        payload = response.json()
    except Exception:
        payload = response.text

    raise AsaasServiceError(
        f"Asaas {action} failed: {response.status_code} - {payload}"
    )


def get_active_billing_account_for_tenant(tenant_id: int) -> TenantBillingAccount:
    account = (
        db_session.query(TenantBillingAccount)
        .filter_by(
            tenant_id=tenant_id,
            provider="asaas",
            active=True,
        )
        .first()
    )

    if account is None:
        raise AsaasServiceError("No active Asaas billing account found for this tenant.")

    return account


def get_asaas_base_url(is_sandbox: bool) -> str:
    if is_sandbox:
        return "https://api-sandbox.asaas.com/v3"
    return "https://api.asaas.com/v3"


def build_asaas_headers(api_key: str) -> dict:
    return {
        "accept": "application/json",
        "content-type": "application/json",
        "access_token": api_key,
    }


def get_account_config_for_tenant(tenant_id: int) -> dict:
    account = get_active_billing_account_for_tenant(tenant_id)

    return {
        "account": account,
        "base_url": get_asaas_base_url(account.is_sandbox),
        "headers": build_asaas_headers(account.api_key),
    }


def create_customer(
    *,
    tenant_id: int,
    user: User,
    cpf_cnpj: str,
) -> dict:
    """
    Create an Asaas customer and persist user.asaas_customer_id.

    We do NOT store cpf/cnpj in our DB. It is only sent to Asaas here.
    """
    if user.asaas_customer_id:
        raise AsaasServiceError("User already has an Asaas customer id.")

    if not user.name or not user.name.strip():
        raise AsaasServiceError("User must have a name before creating an Asaas customer.")

    normalized_cpf_cnpj = _normalize_cpf_cnpj(cpf_cnpj)
    if len(normalized_cpf_cnpj) not in {11, 14}:
        raise AsaasServiceError("CPF/CNPJ inválido.")

    email = (user.email or "").strip()
    if not email or email == "none":
        email = None

    phone = (user.phone or "").strip() or None

    config = get_account_config_for_tenant(tenant_id)

    payload = {
        "name": user.name.strip(),
        "cpfCnpj": normalized_cpf_cnpj,
    }

    if email:
        payload["email"] = email

    if phone:
        payload["mobilePhone"] = phone

    response = requests.post(
        f"{config['base_url']}/customers",
        json=payload,
        headers=config["headers"],
        timeout=20,
    )

    _raise_for_asaas_error(response, "customer creation")

    data = response.json()
    customer_id = data.get("id")

    if not customer_id:
        raise AsaasServiceError("Asaas customer creation succeeded but returned no customer id.")

    user.asaas_customer_id = customer_id
    db_session.commit()

    return data


def ensure_customer_for_user(
    *,
    tenant_id: int,
    user: User,
    cpf_cnpj: str | None = None,
) -> str:
    """
    Return existing Asaas customer id, or create the customer if needed.

    If the user has no customer id yet, cpf_cnpj is required.
    """
    if user.asaas_customer_id:
        return user.asaas_customer_id

    if not cpf_cnpj:
        raise AsaasServiceError("CPF/CNPJ is required to create the Asaas customer.")

    customer_data = create_customer(
        tenant_id=tenant_id,
        user=user,
        cpf_cnpj=cpf_cnpj,
    )
    return customer_data["id"]


def create_subscription(
    *,
    tenant_id: int,
    customer_id: str,
    amount_cents: int,
    description: str,
    cycle: str = "MONTHLY",
    billing_type: str = "PIX",
    next_due_date: date | None = None,
) -> dict:
    """
    Create an Asaas subscription.

    Asaas expects cycle values like MONTHLY and a first due date.
    """
    if not customer_id:
        raise AsaasServiceError("Missing Asaas customer id.")

    if amount_cents <= 0:
        raise AsaasServiceError("Subscription amount must be greater than zero.")

    if next_due_date is None:
        next_due_date = date.today() + timedelta(days=1)

    config = get_account_config_for_tenant(tenant_id)



    payload = {
        "customer": customer_id,
        "billingType": billing_type,
        "value": amount_cents / 100,
        "nextDueDate": next_due_date.isoformat(),
        "cycle": cycle,
        "description": description,
    }
    print("=== ASAAS SUBSCRIPTION DEBUG ===")
    print("URL:", f"{config['base_url']}/subscriptions")
    safe_headers = {
    "accept": config["headers"].get("accept"),
    "content-type": config["headers"].get("content-type"),
    "access_token": "***masked***",
    }
    print("HEADERS:", safe_headers)
    print("PAYLOAD:", payload)
    print("================================")

    response = requests.post(
        f"{config['base_url']}/subscriptions",
        json=payload,
        headers=config["headers"],
        timeout=20,
    )
    print("ASAAS STATUS:", response.status_code)
    print("ASAAS BODY:", response.text)

    _raise_for_asaas_error(response, "subscription creation")

    data = response.json()
    subscription_id = data.get("id")

    if not subscription_id:
        raise AsaasServiceError("Asaas subscription creation succeeded but returned no subscription id.")

    return data


def create_pix_payment(
    *,
    tenant_id: int,
    customer_id: str,
    amount_cents: int,
    description: str,
    due_date: date | None = None,
) -> dict:
    if not customer_id:
        raise AsaasServiceError("Missing Asaas customer id.")

    if amount_cents <= 0:
        raise AsaasServiceError("Payment amount must be greater than zero.")

    config = get_account_config_for_tenant(tenant_id)

    if due_date is None:
        due_date = date.today() + timedelta(days=1)

    payload = {
        "customer": customer_id,
        "billingType": "PIX",
        "value": amount_cents / 100,
        "dueDate": due_date.isoformat(),
        "description": description,
    }

    response = requests.post(
        f"{config['base_url']}/payments",
        json=payload,
        headers=config["headers"],
        timeout=20,
    )

    _raise_for_asaas_error(response, "PIX payment creation")

    data = response.json()
    payment_id = data.get("id")

    if not payment_id:
        raise AsaasServiceError("Asaas PIX payment creation succeeded but returned no payment id.")

    return data


def get_subscription_payments(
    *,
    tenant_id: int,
    subscription_id: str,
) -> dict:
    if not subscription_id:
        raise AsaasServiceError("Missing Asaas subscription id.")

    config = get_account_config_for_tenant(tenant_id)

    response = requests.get(
        f"{config['base_url']}/subscriptions/{subscription_id}/payments",
        headers=config["headers"],
        timeout=20,
    )

    _raise_for_asaas_error(response, "subscription payments lookup")
    return response.json()


def get_pix_qr_code(
    *,
    tenant_id: int,
    payment_id: str,
) -> dict:
    if not payment_id:
        raise AsaasServiceError("Missing Asaas payment id.")

    config = get_account_config_for_tenant(tenant_id)

    response = requests.get(
        f"{config['base_url']}/payments/{payment_id}/pixQrCode",
        headers=config["headers"],
        timeout=20,
    )

    _raise_for_asaas_error(response, "PIX QR code lookup")
    return response.json()

import requests

def asaas_request(tenant_id: int, method: str, path: str, json=None):
    config = get_account_config_for_tenant(tenant_id)

    url = f"{config['base_url']}{path}"

    response = requests.request(
        method,
        url,
        headers=config["headers"],
        json=json,
        timeout=20,
    )

    _raise_for_asaas_error(response, f"{method} {path}")

    return response.json()


def get_subscription(
    *,
    tenant_id: int,
    subscription_id: str,
) -> dict:
    if not subscription_id:
        raise AsaasServiceError("Missing Asaas subscription id.")

    config = get_account_config_for_tenant(tenant_id)

    response = requests.get(
        f"{config['base_url']}/subscriptions/{subscription_id}",
        headers=config["headers"],
        timeout=20,
    )

    _raise_for_asaas_error(response, "subscription lookup")
    return response.json()


def parse_asaas_date(value: str | None):
    if not value:
        return None

    try:
        # Asaas nextDueDate usually comes as YYYY-MM-DD
        dt = datetime.strptime(value, "%Y-%m-%d")
        return dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    
def normalize_asaas_status(status: str | None) -> str:
    return (status or "").strip().lower()


SP_TZ = ZoneInfo("America/Sao_Paulo")
UTC_TZ = timezone.utc

def parse_asaas_due_date_as_sp_end_of_day(value: str | None):
    if not value:
        return None

    try:
        # Asaas date format: YYYY-MM-DD
        due_date = datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None

    sp_end = datetime.combine(
        due_date,
        time(23, 59, 59, 999999),
        tzinfo=SP_TZ,
    )

    return sp_end.astimezone(UTC_TZ)

