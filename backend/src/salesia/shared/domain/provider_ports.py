import time
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol, Optional
from uuid import UUID


@dataclass(frozen=True)
class GatewayChargeResult:
    success: bool
    transaction_id: str
    status: str
    amount: Decimal
    currency: str
    raw_response: dict


@dataclass(frozen=True)
class FiscalInvoiceResult:
    success: bool
    document_series: str
    document_number: int
    fiscal_hash: str
    status: str


class CircuitBreakerOpenException(Exception):
    def __init__(self, service_name: str):
        super().__init__(f"Circuit breaker abierto para el servicio {service_name}; peticiones degradadas temporalmente")


class CircuitBreaker:
    def __init__(self, service_name: str, failure_threshold: int = 3, reset_timeout_sec: float = 30.0):
        self.service_name = service_name
        self.failure_threshold = failure_threshold
        self.reset_timeout_sec = reset_timeout_sec
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "CLOSED"

    def record_success(self) -> None:
        self.failure_count = 0
        self.state = "CLOSED"
        self.last_failure_time = None

    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"

    def can_execute(self) -> bool:
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN":
            if self.last_failure_time and (time.time() - self.last_failure_time) > self.reset_timeout_sec:
                self.state = "HALF_OPEN"
                return True
            return False
        return True


class IEmailProviderPort(Protocol):
    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        metadata: Optional[dict] = None
    ) -> bool:
        ...


class IStorageProviderPort(Protocol):
    def upload_file(self, path: str, content: bytes, content_type: str) -> str:
        ...

    def download_file(self, path: str) -> bytes:
        ...


class IPaymentGatewayPort(Protocol):
    def charge(
        self,
        company_id: UUID,
        amount: Decimal,
        currency: str,
        idempotency_key: str,
        payment_token: str
    ) -> GatewayChargeResult:
        ...


class IFiscalProviderPort(Protocol):
    def emit_electronic_document(
        self,
        company_id: UUID,
        document_type: str,
        series: str,
        number: int,
        payload: dict
    ) -> FiscalInvoiceResult:
        ...


class ResilientEmailNotifier:
    def __init__(self, primary_provider: Optional[IEmailProviderPort] = None):
        self.primary_provider = primary_provider
        self.circuit_breaker = CircuitBreaker("email_service", failure_threshold=2, reset_timeout_sec=10.0)
        self.pending_notifications: list[dict] = []

    def notify_sale_confirmed(self, customer_email: str, sale_id: UUID, total_amount: str) -> bool:
        notification_data = {
            "customer_email": customer_email,
            "sale_id": str(sale_id),
            "total_amount": total_amount,
            "timestamp": time.time(),
            "status": "pending"
        }

        if not self.circuit_breaker.can_execute():
            notification_data["status"] = "degraded_circuit_open"
            self.pending_notifications.append(notification_data)
            return False

        try:
            if self.primary_provider is not None:
                success = self.primary_provider.send_email(
                    to_email=customer_email,
                    subject=f"Confirmación de Venta #{sale_id}",
                    body=f"Su venta por importe {total_amount} ha sido confirmada."
                )
                if success:
                    self.circuit_breaker.record_success()
                    return True
                else:
                    self.circuit_breaker.record_failure()
            else:
                self.circuit_breaker.record_failure()
        except Exception:
            self.circuit_breaker.record_failure()

        notification_data["status"] = "queued_due_to_failure"
        self.pending_notifications.append(notification_data)
        return False
