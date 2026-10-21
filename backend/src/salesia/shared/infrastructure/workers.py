import hashlib
import hmac
import ipaddress
import json
import random
import re
import socket
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Any, Callable, Optional
from urllib.parse import urlsplit
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from salesia.shared.infrastructure.models import (
    JobModel,
    DeadLetterJobModel,
    ScheduleExecutionModel,
    ExternalNotificationIntentModel,
    WebhookSubscriptionModel,
    WebhookDeliveryModel,
    ExternalEntityMappingModel,
    ExternalSyncCursorModel
)

PERMITTED_TASK_NAMES = {
    "sale.created",
    "sale.confirmed",
    "sale.cancelled",
    "payment.received",
    "payment.confirmed",
    "payment.reversed",
    "refund.confirmed",
    "stock.reserved",
    "stock.released",
    "stock.moved",
    "report.generate",
    "import.process",
    "backup.execute",
    "webhook.outgoing",
    "export:massive"
}

SUPPORTED_INTEGRATION_PORTS = {
    "payments": {"stripe", "mercadopago", "custom"},
    "email": {"smtp", "sendgrid", "resend"},
    "invoicing": {"sunat_pe", "dian_co", "sat_mx"},
    "accounting": {"quickbooks", "concar"},
    "ecommerce": {"shopify", "woocommerce"},
    "shipping": {"dhl", "fedex", "custom"},
    "bi": {"powerbi", "snowflake"}
}


def compute_jitter_backoff(retry_count: int, base_delay_sec: float = 1.0, max_delay_sec: float = 60.0) -> float:
    factor = 2 ** retry_count
    delay = min(max_delay_sec, base_delay_sec * factor)
    jitter = random.uniform(0.0, 0.2) * delay
    return delay + jitter


def sign_webhook_payload(payload_bytes: bytes, secret: str) -> str:
    signature = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
    return f"sha256={signature}"


def verify_webhook_signature(payload_bytes: bytes, secret: str, expected_signature: str) -> bool:
    computed = sign_webhook_payload(payload_bytes, secret)
    return hmac.compare_digest(computed, expected_signature)


class DomainEventPayloadSchema(BaseModel):
    model_config = ConfigDict(extra="allow")

    event_id: Optional[str] = None
    event_type: Optional[str] = None
    company_id: Optional[str] = None
    occurred_at: Optional[str] = None


def validate_event_schema(task_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    if task_name not in PERMITTED_TASK_NAMES:
        raise ValueError(f"Nombre de tarea no permitido: {task_name}")

    payload_json = json.dumps(payload, default=str)
    if len(payload_json.encode("utf-8")) > 256 * 1024:
        raise ValueError("El tamaño del payload excede el límite permitido de 256KB")

    parsed = DomainEventPayloadSchema.model_validate(payload)
    return parsed.model_dump(mode="json")


def is_transient_error(exc: Exception) -> bool:
    if isinstance(exc, (ConnectionError, TimeoutError, OSError)):
        return True
    exc_type_name = type(exc).__name__
    if "OperationalError" in exc_type_name or "Deadlock" in exc_type_name:
        return True
    return False


def sanitize_error_message(text: str) -> str:
    cleaned = re.sub(r"://[^@]+@", "://[REDACTED]@", text)
    cleaned = re.sub(r"(bearer\s+)[A-Za-z0-9_\-\.]+", r"\1[REDACTED]", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"(password|secret|token|auth)=['\"][^'\"]+['\"]", r"\1=[REDACTED]", cleaned, flags=re.IGNORECASE)
    return cleaned[:1000]


def sanitize_dict_payload(data: dict[str, Any]) -> dict[str, Any]:
    safe = {}
    for k, v in data.items():
        if any(secret_term in k.lower() for secret_term in ("secret", "token", "password", "auth", "key")):
            safe[k] = "[REDACTED]"
        elif isinstance(v, dict):
            safe[k] = sanitize_dict_payload(v)
        else:
            safe[k] = v
    return safe


def record_dead_letter_job(
    session: Session,
    company_id: UUID,
    job_id: UUID,
    job_type: str,
    error: Exception,
    attempts: int,
    payload: dict[str, Any],
    source: str = "worker",
    recovery_action: str = "manual_retry"
) -> DeadLetterJobModel:
    safe_reason = sanitize_error_message(str(error))
    safe_payload = sanitize_dict_payload(payload)
    dl = DeadLetterJobModel(
        id=uuid4(),
        company_id=company_id,
        job_id=job_id,
        job_type=job_type,
        error_reason=safe_reason,
        attempts=attempts,
        source_origin=source,
        recovery_action=recovery_action,
        payload_json=json.dumps(safe_payload, default=str),
        created_at=datetime.now(timezone.utc)
    )
    session.add(dl)
    session.flush()
    return dl


class TenantFairnessLimiter:
    def __init__(self, max_concurrent_per_tenant: int = 2):
        self.max_concurrent_per_tenant = max_concurrent_per_tenant

    def can_schedule_job(self, session: Session, company_id: UUID) -> bool:
        stmt = select(func.count()).select_from(JobModel).where(
            JobModel.company_id == company_id,
            JobModel.status.in_(["running", "in_progress"])
        )
        active_count = session.scalar(stmt) or 0
        return active_count < self.max_concurrent_per_tenant

    def get_tenant_active_count(self, session: Session, company_id: UUID) -> int:
        stmt = select(func.count()).select_from(JobModel).where(
            JobModel.company_id == company_id,
            JobModel.status.in_(["running", "in_progress"])
        )
        return session.scalar(stmt) or 0


class DurableScheduler:
    def claim_window(
        self,
        session: Session,
        schedule_key: str,
        execution_window: str,
        leader_id: str,
        timezone_iana: str = "UTC"
    ) -> bool:
        existing = session.scalar(
            select(ScheduleExecutionModel.id).where(
                ScheduleExecutionModel.schedule_key == schedule_key,
                ScheduleExecutionModel.execution_window == execution_window
            )
        )
        if existing:
            return False

        exec_model = ScheduleExecutionModel(
            id=uuid4(),
            schedule_key=schedule_key,
            execution_window=execution_window,
            leader_id=leader_id,
            status="running",
            timezone_iana=timezone_iana,
            executed_at=datetime.now(timezone.utc)
        )
        session.add(exec_model)
        session.flush()
        return True


def validate_webhook_url(url: str) -> None:
    parsed = urlsplit(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("El esquema debe ser HTTP o HTTPS")

    host = parsed.hostname or ""
    if not host:
        raise ValueError("Host inválido")

    if host.lower() in ("localhost", "127.0.0.1", "0.0.0.0", "::1") or host.lower().endswith((".local", ".internal", ".lan")):
        raise ValueError("Destino a red privada o local prohibida")

    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        resolved_infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        if not resolved_infos:
            raise ValueError("El host no pudo resolverse por DNS")
        for info in resolved_infos:
            ip_str = info[4][0]
            ip_obj = ipaddress.ip_address(ip_str)
            if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_multicast or ip_obj.is_reserved or not ip_obj.is_global:
                raise ValueError("Destino a red privada prohibida")
    except socket.gaierror:
        raise ValueError("El host no pudo resolverse por DNS")
    except ValueError as exc:
        if "Destino a red privada" in str(exc) or "resolverse por DNS" in str(exc):
            raise exc


class OutgoingWebhookService:
    def record_delivery(
        self,
        session: Session,
        subscription_id: UUID,
        event_id: UUID,
        payload: dict[str, Any]
    ) -> WebhookDeliveryModel:
        sub = session.get(WebhookSubscriptionModel, subscription_id)
        if not sub or not sub.is_active:
            raise ValueError("Suscripción de webhook inactiva o no encontrada")

        payload_bytes = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        signature = sign_webhook_payload(payload_bytes, sub.secret)

        delivery = WebhookDeliveryModel(
            id=uuid4(),
            subscription_id=subscription_id,
            event_id=event_id,
            payload_json=payload_bytes.decode("utf-8"),
            signature=signature,
            status="delivered",
            attempts=1,
            delivered_at=datetime.now(timezone.utc)
        )
        session.add(delivery)
        session.flush()
        return delivery


class ExternalSyncManager:
    def record_mapping(
        self,
        session: Session,
        company_id: UUID,
        entity_type: str,
        local_id: UUID,
        external_id: str,
        origin_system: str,
        sync_hash: str
    ) -> ExternalEntityMappingModel:
        existing = session.scalar(
            select(ExternalEntityMappingModel).where(
                ExternalEntityMappingModel.company_id == company_id,
                ExternalEntityMappingModel.entity_type == entity_type,
                ExternalEntityMappingModel.external_id == external_id
            )
        )
        if existing:
            existing.origin_system = origin_system
            existing.sync_hash = sync_hash
            session.flush()
            return existing

        mapping = ExternalEntityMappingModel(
            id=uuid4(),
            company_id=company_id,
            entity_type=entity_type,
            local_id=local_id,
            external_id=external_id,
            origin_system=origin_system,
            sync_hash=sync_hash
        )
        session.add(mapping)
        session.flush()
        return mapping

    def should_skip_echo(
        self,
        session: Session,
        company_id: UUID,
        entity_type: str,
        external_id: str,
        incoming_hash: str
    ) -> bool:
        mapping = session.scalar(
            select(ExternalEntityMappingModel).where(
                ExternalEntityMappingModel.company_id == company_id,
                ExternalEntityMappingModel.entity_type == entity_type,
                ExternalEntityMappingModel.external_id == external_id
            )
        )
        if mapping and mapping.origin_system == "salesia" and mapping.sync_hash == incoming_hash:
            return True
        return False


class ExternalNotificationManager:
    def send_idempotent_notification(
        self,
        session: Session,
        company_id: UUID,
        channel: str,
        recipient: str,
        idempotency_key: str,
        send_fn: Callable[[], str]
    ) -> ExternalNotificationIntentModel:
        existing = session.scalar(
            select(ExternalNotificationIntentModel).where(
                ExternalNotificationIntentModel.company_id == company_id,
                ExternalNotificationIntentModel.idempotency_key == idempotency_key
            )
        )
        if existing:
            return existing

        provider_msg_id = send_fn()
        intent = ExternalNotificationIntentModel(
            id=uuid4(),
            company_id=company_id,
            channel=channel,
            recipient=recipient,
            idempotency_key=idempotency_key,
            provider_message_id=provider_msg_id,
            status="delivered",
            created_at=datetime.now(timezone.utc)
        )
        session.add(intent)
        session.flush()
        return intent


class IntegrationConnector:
    def __init__(self, port: str, provider: str, sandbox: bool = False):
        self.port = port
        self.provider = provider
        self.sandbox = sandbox

    def charge(self, amount: Decimal, currency: str, token: str) -> dict[str, Any]:
        if self.port != "payments":
            raise ValueError("El conector seleccionado no admite cobros.")
        if not self.sandbox:
            raise RuntimeError(f"El proveedor {self.provider} requiere credenciales y un adaptador activo para procesar cobros reales.")
        return {
            "status": "approved",
            "transaction_id": f"sandbox_{uuid4().hex[:12]}",
            "sandbox": True,
            "live_call_made": False,
            "amount": str(amount),
            "currency": currency
        }


class IntegrationPortRegistry:
    def list_available_ports(self) -> list[str]:
        return list(SUPPORTED_INTEGRATION_PORTS.keys())

    def get_connector(self, port: str, provider: str, sandbox: bool = False) -> IntegrationConnector:
        if port not in SUPPORTED_INTEGRATION_PORTS:
            raise ValueError(f"Puerto de integración no soportado: {port}")
        if provider not in SUPPORTED_INTEGRATION_PORTS[port]:
            raise ValueError(f"Proveedor no soportado para puerto {port}: {provider}")
        return IntegrationConnector(port=port, provider=provider, sandbox=sandbox)


def disconnect_integration_account(session: Session, company_id: UUID, connection_id: UUID) -> None:
    sub = session.get(WebhookSubscriptionModel, connection_id)
    if sub and sub.company_id == company_id:
        sub.is_active = False
        sub.secret = ""
        session.flush()
