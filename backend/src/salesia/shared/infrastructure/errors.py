from uuid import uuid4
from sqlalchemy.exc import IntegrityError, OperationalError, TimeoutError as DatabasePoolTimeout
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from salesia.shared.domain.exceptions import DomainException


class DomainUnauthorizedException(DomainException):
    def __init__(self, message: str = "Credenciales inválidas o token expirado"):
        super().__init__(message, code="UNAUTHORIZED")


class DomainForbiddenException(DomainException):
    def __init__(self, message: str = "Acceso denegado: permisos insuficientes"):
        super().__init__(message, code="FORBIDDEN")


class DomainNotFoundException(DomainException):
    def __init__(self, message: str = "Recurso no encontrado"):
        super().__init__(message, code="NOT_FOUND")


class DomainConflictException(DomainException):
    def __init__(self, message: str = "Conflicto con el estado actual del recurso"):
        super().__init__(message, code="CONFLICT")


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DatabasePoolTimeout)
    async def database_pool_timeout_handler(request: Request, exc: DatabasePoolTimeout):
        return JSONResponse(status_code=503, headers={"Retry-After": "2"}, content={"type": "about:blank", "title": "Base de datos ocupada", "status": 503, "code": "DATABASE_BUSY", "detail": "No hay una conexión disponible dentro del tiempo permitido. Comprueba el estado de la operación antes de repetirla.", "instance": request.url.path})

    @app.exception_handler(IntegrityError)
    async def integrity_handler(request: Request, exc: IntegrityError):
        return JSONResponse(status_code=409, content={"type": "about:blank", "title": "Conflicto de datos", "status": 409, "detail": "La operación viola una restricción de integridad. Verifique referencias y duplicados.", "instance": request.url.path})

    @app.exception_handler(OperationalError)
    async def database_handler(request: Request, exc: OperationalError):
        return JSONResponse(status_code=503, headers={"Retry-After": "2"}, content={"type": "about:blank", "title": "Operación temporalmente no disponible", "status": 503, "detail": "No se pudo completar la transacción. Reintente con la misma clave de idempotencia.", "instance": request.url.path})

    @app.exception_handler(DomainUnauthorizedException)
    async def unauthorized_handler(request: Request, exc: DomainUnauthorizedException):
        trace_id = str(uuid4())
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "type": "https://api.salesia.enterprise/errors/unauthorized",
                "title": "No Autorizado",
                "status": status.HTTP_401_UNAUTHORIZED,
                "code": exc.code,
                "detail": exc.message,
                "instance": request.url.path,
                "trace_id": trace_id
            }
        )

    @app.exception_handler(DomainForbiddenException)
    async def forbidden_handler(request: Request, exc: DomainForbiddenException):
        trace_id = str(uuid4())
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "type": "https://api.salesia.enterprise/errors/forbidden",
                "title": "Prohibido",
                "status": status.HTTP_403_FORBIDDEN,
                "code": exc.code,
                "detail": exc.message,
                "instance": request.url.path,
                "trace_id": trace_id
            }
        )

    @app.exception_handler(DomainNotFoundException)
    async def not_found_handler(request: Request, exc: DomainNotFoundException):
        trace_id = str(uuid4())
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "type": "https://api.salesia.enterprise/errors/not-found",
                "title": "Recurso No Encontrado",
                "status": status.HTTP_404_NOT_FOUND,
                "code": exc.code,
                "detail": exc.message,
                "instance": request.url.path,
                "trace_id": trace_id
            }
        )

    @app.exception_handler(DomainConflictException)
    async def conflict_handler(request: Request, exc: DomainConflictException):
        trace_id = str(uuid4())
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "type": "https://api.salesia.enterprise/errors/conflict",
                "title": "Conflicto",
                "status": status.HTTP_409_CONFLICT,
                "code": exc.code,
                "detail": exc.message,
                "instance": request.url.path,
                "trace_id": trace_id
            }
        )

    @app.exception_handler(DomainException)
    async def domain_exception_handler(request: Request, exc: DomainException):
        trace_id = str(uuid4())
        status_code = status.HTTP_400_BAD_REQUEST
        if exc.code in ("VERSION_CONFLICT", "STOCK_INSUFFICIENT", "PAYMENT_PENDING", "CONFLICT"):
            status_code = status.HTTP_409_CONFLICT
        elif exc.code in ("DATASET_EMPTY",):
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY

        return JSONResponse(
            status_code=status_code,
            content={
                "type": f"https://api.salesia.enterprise/errors/{exc.code.lower().replace('_', '-')}",
                "title": exc.code.replace("_", " ").title(),
                "status": status_code,
                "code": exc.code,
                "detail": exc.message,
                "instance": request.url.path,
                "trace_id": trace_id
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        trace_id = str(uuid4())
        formatted_errors = []
        for err in exc.errors():
            loc = ".".join(str(x) for x in err.get("loc", []))
            formatted_errors.append({
                "field": loc,
                "message": err.get("msg", "Entrada inválida")
            })

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "type": "https://api.salesia.enterprise/errors/validation-error",
                "title": "Error de Validación de Entrada",
                "status": status.HTTP_422_UNPROCESSABLE_ENTITY,
                "code": "VALIDATION_ERROR",
                "detail": "Uno o más campos de la solicitud no cumplen el contrato público.",
                "instance": request.url.path,
                "errors": formatted_errors,
                "trace_id": trace_id
            }
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        trace_id = str(uuid4())
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "type": "https://api.salesia.enterprise/errors/internal-server-error",
                "title": "Error Interno del Servidor",
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "code": "INTERNAL_SERVER_ERROR",
                "detail": "Ha ocurrido un error inesperado. Consulte a soporte con el trace_id provisto.",
                "instance": request.url.path,
                "trace_id": trace_id
            }
        )
