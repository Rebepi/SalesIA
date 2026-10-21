import json

from fastapi import HTTPException
from sqlalchemy import select, update

from salesia.modules.auditoria.service import record_audit_event
from salesia.modules.clientes.application.validacion import validate_customer_email, validate_customer_phone
from salesia.modules.clientes.domain.texto import sanitize_text
from salesia.modules.clientes.infrastructure.models import CustomerAddressModel, CustomerContactModel, CustomerModel
from salesia.shared.infrastructure.transactions import claim_request, complete_request


def contact_data(row):
    return {"id": str(row.id), "name": row.name, "role": row.role, "email": row.email, "phone": row.phone, "is_primary": row.is_primary, "preferences": json.loads(row.preferences_json or "{}"), "purpose": row.purpose, "can_purchase": row.can_purchase, "can_receive": row.can_receive, "valid_from": row.valid_from.isoformat() if row.valid_from else None, "valid_until": row.valid_until.isoformat() if row.valid_until else None, "is_active": row.is_active, "version": row.version}


def address_data(row):
    return {"id": str(row.id), "address_type": row.address_type, "street": row.street, "city": row.city, "state": row.state, "country": row.country, "postal_code": row.postal_code, "is_primary": row.is_primary, "valid_from": row.valid_from.isoformat() if row.valid_from else None, "valid_until": row.valid_until.isoformat() if row.valid_until else None, "is_active": row.is_active, "version": row.version}


def edit_customer_detail(db, user, customer_id, identifier, payload, kind, key):
    record, cached = claim_request(db, user.company_id, f"customers.{kind}.edit:{identifier}", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    customer = db.scalar(select(CustomerModel).where(CustomerModel.company_id == user.company_id, CustomerModel.id == customer_id).with_for_update())
    if customer is None:
        raise HTTPException(404, "Cliente no encontrado.")
    model = CustomerContactModel if kind == "contact" else CustomerAddressModel
    row = db.scalar(select(model).where(model.company_id == user.company_id, model.customer_id == customer_id, model.id == identifier).with_for_update())
    if row is None:
        raise HTTPException(404, "Contacto o dirección no encontrados.")
    if row.version != payload.version:
        raise HTTPException(409, "El registro cambió; recarga antes de guardarlo.")
    serializer = contact_data if kind == "contact" else address_data
    before = serializer(row)
    values = payload.model_dump(exclude={"version", "preferences"})
    if kind == "contact":
        validate_customer_email(payload.email)
        validate_customer_phone(payload.phone)
        values["name"], values["role"] = sanitize_text(payload.name), sanitize_text(payload.role)
        values["email"] = payload.email.strip().lower() if payload.email else None
        values["phone"] = payload.phone.strip() if payload.phone else None
        row.preferences_json = json.dumps(payload.preferences or {})
    else:
        values["street"], values["city"] = sanitize_text(payload.street), sanitize_text(payload.city)
        values["country"] = payload.country.strip().upper()
    if payload.is_primary and payload.is_active:
        statement = update(model).where(model.company_id == user.company_id, model.customer_id == customer_id, model.id != identifier)
        statement = statement.where(model.purpose == payload.purpose) if kind == "contact" else statement.where(model.address_type == payload.address_type)
        db.execute(statement.values(is_primary=False, version=model.version + 1))
    if not payload.is_active:
        values["is_primary"] = False
    for field, value in values.items():
        setattr(row, field, value)
    row.version += 1
    result = serializer(row)
    record_audit_event(db, company_id=user.company_id, actor_id=user.user_id, actor_email=user.email, action="UPDATE_CUSTOMER_CONTACT" if kind == "contact" else "UPDATE_CUSTOMER_ADDRESS", entity_type="Customer", entity_id=customer_id, diff={"detail_id": str(row.id), "before": before, "after": result})
    complete_request(record, result)
    db.commit()
    return result
