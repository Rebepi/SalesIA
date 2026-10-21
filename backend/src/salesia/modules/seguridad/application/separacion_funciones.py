import json
from datetime import datetime, timezone

from fastapi import HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from salesia.modules.analitica.infrastructure.models.artefactos import AnalyticsArtifact
from salesia.modules.auditoria.service import record_audit_event
from salesia.shared.infrastructure.models import CompanyModel
from salesia.shared.infrastructure.transactions import claim_request, complete_request

PROCESSES = {
    "purchase_order": {"label": "Aprobar una orden de compra propia", "mandatory": False, "enabled": True},
    "purchase_requisition": {"label": "Aprobar una requisición propia", "mandatory": False, "enabled": True},
    "return_acceptance": {"label": "Aceptar una devolución solicitada por la misma persona", "mandatory": False, "enabled": True},
    "supplier_claim": {"label": "Registrar el acuerdo de un reclamo propio a proveedor", "mandatory": False, "enabled": True},
    "expense": {"label": "Resolver la aprobación de un gasto propio", "mandatory": True, "enabled": True},
    "stock_count": {"label": "Aprobar el conteo creado por la misma persona", "mandatory": True, "enabled": True},
    "cash_difference": {"label": "Autorizar una diferencia contada por la misma persona", "mandatory": True, "enabled": True},
    "commission": {"label": "Aprobar la comisión propia o un cálculo propio", "mandatory": True, "enabled": True},
    "commission_correction": {"label": "Resolver un ajuste de comisión propio", "mandatory": True, "enabled": True},
    "credit_conversion": {"label": "Revisar una conversión de saldo solicitada por la misma persona", "mandatory": True, "enabled": True},
    "petty_cash": {"label": "Resolver la rendición del propio anticipo", "mandatory": True, "enabled": True},
    "workflow": {"label": "Resolver la aprobación del documento propio o de la propia solicitud", "mandatory": True, "enabled": True},
}


class SeparationSave(BaseModel):
    expected_version: int = Field(ge=0)
    enabled: dict[str, bool]
    reason: str = Field(min_length=5, max_length=2000)


def current(db, company_id):
    row = db.scalar(select(AnalyticsArtifact).where(AnalyticsArtifact.company_id == company_id, AnalyticsArtifact.kind == "function_separation", AnalyticsArtifact.artifact_key == "company").order_by(AnalyticsArtifact.version.desc()).limit(1))
    data = json.loads(row.data_json) if row else {}
    enabled = {key: value["enabled"] for key, value in PROCESSES.items()}
    enabled.update(data.get("enabled", {}))
    return {"version": row.version if row else 0, "enabled": enabled, "processes": PROCESSES, "reason": data.get("reason"), "actor": data.get("actor"), "at": data.get("at"), "definition": "Una regla activa exige un revisor distinto de todos los autores identificados de la operación. Las protecciones obligatorias existentes se conservan. Cambiar una regla afecta decisiones futuras y queda registrado con motivo; no modifica decisiones anteriores."}


def save(db, user, payload, key):
    db.scalar(select(CompanyModel).where(CompanyModel.id == user.company_id).with_for_update())
    record, cached = claim_request(db, user.company_id, "function_separation.save", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    previous = current(db, user.company_id)
    if previous["version"] != payload.expected_version:
        raise HTTPException(409, "Las reglas de separación cambiaron. Consulte su versión vigente.")
    if set(payload.enabled) != set(PROCESSES):
        raise HTTPException(422, "Declare una decisión para cada proceso de separación de funciones.")
    if any(not payload.enabled[key] for key, value in PROCESSES.items() if value["mandatory"]):
        raise HTTPException(422, "Las reglas obligatorias no se pueden desactivar.")
    data = {"enabled": payload.enabled, "reason": payload.reason, "actor": user.email, "at": datetime.now(timezone.utc).isoformat()}
    row = AnalyticsArtifact(company_id=user.company_id, kind="function_separation", artifact_key="company", version=previous["version"] + 1, status="active", data_json=json.dumps(data), created_by=user.user_id)
    db.add(row)
    db.flush()
    record_audit_event(db, company_id=user.company_id, actor_id=user.user_id, actor_email=user.email, action="SAVE_FUNCTION_SEPARATION", entity_type="AnalyticsArtifact", entity_id=row.id, diff={"version": row.version, "previous": previous["enabled"], **data})
    result = current(db, user.company_id)
    complete_request(record, result)
    db.commit()
    return result


def enforce(db, user, process, authors, entity_type, identifier):
    db.scalar(select(CompanyModel).where(CompanyModel.id == user.company_id).with_for_update())
    policy = current(db, user.company_id)
    if process not in PROCESSES:
        raise HTTPException(422, "Proceso de separación de funciones desconocido.")
    enabled = policy["enabled"][process]
    known = {str(value) for value in authors if value is not None}
    if enabled and not known:
        raise HTTPException(409, "El documento no conserva un autor identificado para comprobar la revisión independiente. Reconcilie su origen antes de resolverlo o revise la regla opcional con un motivo documentado.")
    if enabled and str(user.user_id) in known:
        raise HTTPException(403, f"La regla de separación de funciones impide {PROCESSES[process]['label'].lower()}. La decisión debe registrarla otra persona autorizada.")
    record_audit_event(db, company_id=user.company_id, actor_id=user.user_id, actor_email=user.email, action="FUNCTION_SEPARATION_APPLIED", entity_type=entity_type, entity_id=identifier, diff={"process": process, "policy_version": policy["version"], "independent_review_required": enabled, "identified_authors": sorted(known)})
