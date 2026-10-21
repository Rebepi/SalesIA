import json
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Literal

from fastapi import HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select

from salesia.modules.auditoria.service import record_audit_event
from salesia.modules.operaciones.application.recursos import definition, entity
from salesia.modules.operaciones.infrastructure.models.campos import BusinessFieldDefinitionModel, BusinessFieldValuesModel
from salesia.shared.infrastructure.models import CompanyModel
from salesia.shared.infrastructure.transactions import claim_request, complete_request


class FieldDefinitionRequest(BaseModel):
    key: str = Field(pattern=r"^[a-z][a-z0-9_]{0,63}$")
    label: str = Field(min_length=2, max_length=128)
    field_type: Literal["text", "decimal", "date", "boolean", "choice"]
    options: list[str] = Field(default_factory=list, max_length=100)
    required_states: list[str] = Field(default_factory=list, max_length=50)
    is_active: bool = True
    version: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def validate_choices(self):
        if self.field_type == "choice" and not self.options:
            raise ValueError("Un campo de lista requiere opciones.")
        if len(set(self.options)) != len(self.options) or any(not value.strip() or len(value) > 255 for value in self.options):
            raise ValueError("Las opciones deben ser únicas, no vacías y de hasta 255 caracteres.")
        if any(not value.strip() or len(value) > 64 for value in self.required_states):
            raise ValueError("Indica estados de hasta 64 caracteres.")
        return self


class FieldValuesRequest(BaseModel):
    version: int = Field(ge=0)
    values: dict[str, str | bool | None] = Field(max_length=100)


def list_definitions(db, user, kind):
    definition(kind, user)
    rows = db.scalars(select(BusinessFieldDefinitionModel).where(BusinessFieldDefinitionModel.company_id == user.company_id, BusinessFieldDefinitionModel.resource_type == kind).order_by(BusinessFieldDefinitionModel.label)).all()
    return [{"id": str(row.id), "key": row.key, "label": row.label, "field_type": row.field_type, "options": json.loads(row.options_json), "required_states": json.loads(row.required_states_json), "is_active": row.is_active, "version": row.version} for row in rows]


def save_definition(db, user, kind, payload, key):
    definition(kind, user)
    if "organization:manage" not in user.permissions:
        raise HTTPException(403, "Solo un administrador de la organización configura campos.")
    record, cached = claim_request(db, user.company_id, f"fields.define:{kind}", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    db.scalar(select(CompanyModel).where(CompanyModel.id == user.company_id).with_for_update())
    row = db.scalar(select(BusinessFieldDefinitionModel).where(BusinessFieldDefinitionModel.company_id == user.company_id, BusinessFieldDefinitionModel.resource_type == kind, BusinessFieldDefinitionModel.key == payload.key).with_for_update())
    if (row.version if row else 0) != payload.version:
        raise HTTPException(409, "La definición del campo cambió.")
    if row and row.field_type != payload.field_type:
        raise HTTPException(409, "Conserva el tipo del campo existente. Crea otra clave para cambiar de tipo.")
    if row is None:
        row = BusinessFieldDefinitionModel(company_id=user.company_id, resource_type=kind, key=payload.key, field_type=payload.field_type, version=0)
        db.add(row)
    row.label, row.options_json, row.required_states_json, row.is_active, row.version = payload.label, json.dumps(payload.options), json.dumps(payload.required_states), payload.is_active, row.version + 1
    db.flush()
    result = {"id": str(row.id), "version": row.version}
    record_audit_event(db, company_id=user.company_id, actor_id=user.user_id, actor_email=user.email, action="DEFINE_BUSINESS_FIELD", entity_type="BusinessFieldDefinition", entity_id=row.id, diff=payload.model_dump(mode="json"))
    complete_request(record, result)
    db.commit()
    return result


def get_values(db, user, kind, identifier):
    row = entity(db, user, kind, identifier)
    values = db.scalar(select(BusinessFieldValuesModel).where(BusinessFieldValuesModel.company_id == user.company_id, BusinessFieldValuesModel.resource_type == kind, BusinessFieldValuesModel.resource_id == identifier))
    return {"version": values.version if values else 0, "values": json.loads(values.values_json) if values else {}, "state": getattr(row, "status", "active"), "definitions": list_definitions(db, user, kind)}


def validate_value(field, value):
    if value is None or value == "":
        return None
    if field.field_type == "boolean":
        if not isinstance(value, bool):
            raise HTTPException(422, f"{field.label}: se requiere verdadero o falso.")
        return value
    if not isinstance(value, str):
        raise HTTPException(422, f"{field.label}: formato de valor incorrecto.")
    if len(value) > 4000:
        raise HTTPException(422, f"{field.label}: el texto supera 4000 caracteres.")
    if field.field_type == "decimal":
        try:
            numeric = Decimal(value)
            if not numeric.is_finite() or abs(numeric) > Decimal("99999999999999.999999") or numeric.as_tuple().exponent < -6:
                raise ValueError()
            return str(numeric)
        except (InvalidOperation, ValueError):
            raise HTTPException(422, f"{field.label}: número inválido, máximo seis decimales.")
    if field.field_type == "date":
        try:
            return date.fromisoformat(value).isoformat()
        except ValueError:
            raise HTTPException(422, f"{field.label}: fecha inválida.")
    if field.field_type == "choice" and value not in json.loads(field.options_json):
        raise HTTPException(422, f"{field.label}: el valor no está entre las opciones permitidas.")
    return value.strip()


def validate_required_fields(db, company_id, kind, identifier, target_state):
    fields = db.scalars(select(BusinessFieldDefinitionModel).where(BusinessFieldDefinitionModel.company_id == company_id, BusinessFieldDefinitionModel.resource_type == kind, BusinessFieldDefinitionModel.is_active.is_(True))).all()
    record = db.scalar(select(BusinessFieldValuesModel).where(BusinessFieldValuesModel.company_id == company_id, BusinessFieldValuesModel.resource_type == kind, BusinessFieldValuesModel.resource_id == identifier))
    values = json.loads(record.values_json) if record else {}
    errors = []
    for field in fields:
        if target_state in json.loads(field.required_states_json) or "*" in json.loads(field.required_states_json):
            if field.key not in values or values[field.key] is None or values[field.key] == "":
                errors.append(field.label)
    if errors:
        raise HTTPException(422, "Completa los campos obligatorios antes de continuar: " + ", ".join(errors))


def save_values(db, user, kind, identifier, payload, key):
    record, cached = claim_request(db, user.company_id, f"fields.values:{kind}:{identifier}", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    entity(db, user, kind, identifier, write=True, lock=True)
    definitions = db.scalars(select(BusinessFieldDefinitionModel).where(BusinessFieldDefinitionModel.company_id == user.company_id, BusinessFieldDefinitionModel.resource_type == kind, BusinessFieldDefinitionModel.is_active.is_(True))).all()
    by_key = {field.key: field for field in definitions}
    if set(payload.values) - set(by_key):
        raise HTTPException(422, "El formulario contiene campos desconocidos o desactivados. Recarga sus definiciones.")
    row = db.scalar(select(BusinessFieldValuesModel).where(BusinessFieldValuesModel.company_id == user.company_id, BusinessFieldValuesModel.resource_type == kind, BusinessFieldValuesModel.resource_id == identifier).with_for_update())
    if (row.version if row else 0) != payload.version:
        raise HTTPException(409, "Los valores cambiaron; recarga antes de guardarlos.")
    before = json.loads(row.values_json) if row else {}
    values = {**before, **{field_key: validate_value(by_key[field_key], value) for field_key, value in payload.values.items()}}
    if row is None:
        row = BusinessFieldValuesModel(company_id=user.company_id, resource_type=kind, resource_id=identifier, version=0)
        db.add(row)
    row.values_json, row.version = json.dumps(values), row.version + 1
    db.flush()
    result = {"version": row.version, "values": values}
    record_audit_event(db, company_id=user.company_id, actor_id=user.user_id, actor_email=user.email, action="UPDATE_BUSINESS_FIELDS", entity_type=kind, entity_id=identifier, diff={"before": before, "after": values})
    complete_request(record, result)
    db.commit()
    return result
