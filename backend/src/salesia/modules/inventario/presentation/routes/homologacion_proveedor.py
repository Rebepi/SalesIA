from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.inventario.application import homologacion_proveedor as service
from salesia.modules.inventario.infrastructure_models import Supplier
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(tags=["Homologación de proveedores"])


@router.get("/suppliers/{supplier_id}/qualification")
def supplier_qualification(supplier_id: UUID, user: AuthenticatedUser = Depends(require_permission("purchases:read")), db: Session = Depends(get_db)):
    row = db.scalar(select(Supplier).where(Supplier.company_id == user.company_id, Supplier.id == supplier_id))
    if row is None:
        raise HTTPException(404, "Proveedor no encontrado.")
    return service.qualification_data(db, user, row)


@router.post("/suppliers/{supplier_id}/qualification")
def supplier_qualification_action(supplier_id: UUID, payload: service.QualificationRequest, user: AuthenticatedUser = Depends(require_permission("purchases:write")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.qualification_action(db, user, supplier_id, payload, key)


from salesia.modules.inventario.application.desempeno_proveedor import SupplierCorrectiveRequest, create_corrective


@router.post("/suppliers/{supplier_id}/corrective-tasks", status_code=201)
def supplier_corrective_task(supplier_id: UUID, payload: SupplierCorrectiveRequest, user: AuthenticatedUser = Depends(require_permission("purchases:write")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return create_corrective(db, user, supplier_id, payload, key)
