import requests

from app.models.billing import TenantBillingAccount
from app.database import db_session


ASAAS_BASE_URL = "https://api-sandbox.asaas.com/v3"


class AsaasServiceError(Exception):
    pass


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