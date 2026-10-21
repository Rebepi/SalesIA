class DomainException(Exception):
    def __init__(self, message: str, code: str = "DOMAIN_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class InvariantViolationException(DomainException):
    def __init__(self, message: str):
        super().__init__(message, code="INVARIANT_VIOLATION")


class CurrencyMismatchException(DomainException):
    def __init__(self, expected: str, actual: str):
        super().__init__(f"No se pueden operar monedas distintas: {expected} vs {actual}", code="CURRENCY_MISMATCH")


class NegativeAmountException(DomainException):
    def __init__(self, amount: str):
        super().__init__(f"El importe monetario no puede ser negativo: {amount}", code="NEGATIVE_AMOUNT")


class InsufficientStockException(DomainException):
    def __init__(self, sku: str, requested: int, available: int):
        super().__init__(
            f"Stock insuficiente para SKU {sku}: solicitado {requested}, disponible {available}",
            code="INSUFFICIENT_STOCK"
        )


class ZeroEvidenceException(DomainException):
    def __init__(self, message: str = "La probabilidad de la evidencia P(B) no puede ser cero en el Teorema de Bayes"):
        super().__init__(message, code="ZERO_EVIDENCE")


class EmptySampleException(DomainException):
    def __init__(self, message: str = "No se puede calcular estadística descriptiva sobre una muestra vacía"):
        super().__init__(message, code="EMPTY_SAMPLE")


class UnauthorizedTenantAccessException(DomainException):
    def __init__(self, company_id: str):
        super().__init__(f"Acceso no autorizado al tenant {company_id}", code="UNAUTHORIZED_TENANT_ACCESS")


class IncompatibleVariableScaleException(DomainException):
    def __init__(self, message: str = "La escala de la variable no admite la operación solicitada"):
        super().__init__(message, code="INCOMPATIBLE_VARIABLE_SCALE")


class StockInsufficientException(DomainException):
    def __init__(self, sku: str, requested: int = 0, available: int = 0):
        super().__init__(
            f"Stock insuficiente para SKU {sku}: solicitado {requested}, disponible {available}",
            code="STOCK_INSUFFICIENT"
        )


class VersionConflictException(DomainException):
    def __init__(self, message: str = "Conflicto de concurrencia optimista en el recurso"):
        super().__init__(message, code="VERSION_CONFLICT")


class CreditLimitExceededException(DomainException):
    def __init__(self, message: str = "Límite de crédito excedido para el cliente"):
        super().__init__(message, code="CREDIT_LIMIT_EXCEEDED")


class PaymentPendingException(DomainException):
    def __init__(self, message: str = "El pago se encuentra pendiente de confirmación"):
        super().__init__(message, code="PAYMENT_PENDING")


class DatasetEmptyException(DomainException):
    def __init__(self, message: str = "El dataset seleccionado no contiene registros para analizar"):
        super().__init__(message, code="DATASET_EMPTY")
