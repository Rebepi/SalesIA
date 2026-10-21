from decimal import Decimal
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from salesia.modules.auditoria.service import record_audit_event
from salesia.modules.clientes.application.acceso import user_can_read_sensitive
from salesia.modules.clientes.application.contracts.clientes import CustomerCreateModel
from salesia.modules.clientes.application.validacion import (
    validate_customer_document,
    validate_customer_email,
    validate_customer_phone,
)
from salesia.modules.clientes.domain.texto import sanitize_text
from salesia.modules.clientes.infrastructure.models import CustomerAddressModel, CustomerModel, CustomerProfileModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.errors import DomainConflictException, DomainForbiddenException
from salesia.shared.infrastructure.models import AuditLogModel, CompanyModel


def create_customer(req: CustomerCreateModel, current_user: AuthenticatedUser, db: Session):
    validate_customer_document(req.doc_type, req.doc_number)
    validate_customer_email(req.email)
    validate_customer_phone(req.phone)

    clean_legal_name = sanitize_text(req.legal_name)
    if not clean_legal_name:
        raise HTTPException(422, {"field": "legal_name", "rule": "Razón social o nombre no puede ser vacío"})

    existing = db.execute(
        select(CustomerModel).where(
            CustomerModel.company_id == current_user.company_id,
            CustomerModel.doc_type == req.doc_type.upper().strip(),
            CustomerModel.doc_number == req.doc_number.strip(),
        )
    ).scalar_one_or_none()
    if existing:
        raise DomainConflictException(f"Ya existe un cliente registrado con documento {req.doc_type} {req.doc_number}.")

    customer_id = uuid4()
    customer_code = req.code.strip() if req.code else f"CLI-{customer_id.hex[:10].upper()}"
    customer = CustomerModel(
        id=customer_id,
        company_id=current_user.company_id,
        code=customer_code,
        doc_type=req.doc_type.upper().strip(),
        doc_number=req.doc_number.strip(),
        legal_name=clean_legal_name,
        email=req.email.lower().strip() if req.email else None,
        phone=req.phone.strip() if req.phone else None,
        credit_limit=req.credit_limit,
        current_balance=Decimal("0.000000"),
        is_active=(req.status != "archived"),
    )
    db.add(customer)
    db.flush()

    profile = CustomerProfileModel(
        id=uuid4(),
        company_id=current_user.company_id,
        customer_id=customer_id,
        status=req.status or "active",
        version=1,
        assigned_sales_rep_id=req.assigned_sales_rep_id,
        sales_team=req.sales_team,
        payment_terms_days=req.payment_terms_days or 30,
        preferred_currency=req.preferred_currency or "USD",
        is_credit_blocked=False,
        tags_json="[]",
        assignment_history_json="[]",
    )
    db.add(profile)
    if req.address:
        db.add(CustomerAddressModel(id=uuid4(), company_id=current_user.company_id, customer_id=customer_id, address_type="fiscal" if customer.doc_type == "RUC" else "comercial", street=sanitize_text(req.address) or req.address, city="Lima", country="PE", is_primary=True, is_active=True, version=1))

    audit = AuditLogModel(
        id=uuid4(),
        company_id=current_user.company_id,
        actor_id=current_user.user_id,
        actor_email=current_user.email,
        action="CUSTOMER_CREATED",
        entity_type="Customer",
        entity_id=customer.id,
        trace_id=str(uuid4()),
        payload_diff=f'{{"code": "{customer.code}", "doc_number": "{customer.doc_number}"}}',
    )
    db.add(audit)
    db.commit()
    db.refresh(customer)

    can_sensitive = user_can_read_sensitive(current_user)
    return {
        "id": str(customer.id),
        "customer_id": str(customer.id),
        "company_id": str(customer.company_id),
        "code": customer.code,
        "doc_type": customer.doc_type,
        "doc_number": customer.doc_number,
        "legal_name": customer.legal_name,
        "email": customer.email,
        "phone": customer.phone,
        "credit_limit": str(customer.credit_limit) if can_sensitive else None,
        "current_balance": str(customer.current_balance) if can_sensitive else None,
        "is_active": customer.is_active,
        "address": req.address,
        "status": profile.status,
        "version": profile.version,
        "created_at": customer.created_at.isoformat(),
    }


def ensure_walk_in_customer(current_user: AuthenticatedUser, db: Session):
    if (
        "sales:write" not in current_user.permissions
        and "customers:write" not in current_user.permissions
        and current_user.role not in ("company_admin", "platform_admin")
    ):
        raise DomainForbiddenException("No tiene permiso para preparar el consumidor final.")
    customer = db.scalar(
        select(CustomerModel).where(
            CustomerModel.company_id == current_user.company_id,
            CustomerModel.doc_type == "SIN_DOCUMENTO",
            CustomerModel.doc_number == "SIN_DOCUMENTO",
        )
    )
    if not customer:
        customer = CustomerModel(
            id=uuid4(),
            company_id=current_user.company_id,
            code="CONSUMIDOR_FINAL",
            doc_type="SIN_DOCUMENTO",
            doc_number="SIN_DOCUMENTO",
            legal_name="Consumidor final",
            email=None,
            phone=None,
            credit_limit=Decimal("0.000000"),
            current_balance=Decimal("0.000000"),
            is_active=True,
        )
        db.add(customer)
        db.flush()
        company = db.get(CompanyModel, current_user.company_id)
        profile = CustomerProfileModel(
            id=uuid4(),
            company_id=current_user.company_id,
            customer_id=customer.id,
            status="active",
            version=1,
            payment_terms_days=0,
            preferred_currency=company.base_currency if company else "USD",
            is_credit_blocked=True,
            tags_json='["walk_in"]',
            assignment_history_json="[]",
        )
        db.add(profile)
        record_audit_event(
            db=db,
            company_id=current_user.company_id,
            actor_id=current_user.user_id,
            actor_email=current_user.email,
            action="WALK_IN_CUSTOMER_CREATED",
            entity_type="Customer",
            entity_id=customer.id,
            diff={"code": "CONSUMIDOR_FINAL"},
        )
        try:
            db.commit()
            db.refresh(customer)
        except IntegrityError:
            db.rollback()
            customer = db.scalar(
                select(CustomerModel).where(
                    CustomerModel.company_id == current_user.company_id,
                    CustomerModel.doc_type == "SIN_DOCUMENTO",
                    CustomerModel.doc_number == "SIN_DOCUMENTO",
                )
            )
            if not customer:
                customer = db.scalar(
                    select(CustomerModel).where(
                        CustomerModel.company_id == current_user.company_id, CustomerModel.code == "CONSUMIDOR_FINAL"
                    )
                )
    return {
        "id": str(customer.id),
        "customer_id": str(customer.id),
        "code": customer.code,
        "doc_type": customer.doc_type,
        "doc_number": customer.doc_number,
        "legal_name": customer.legal_name,
        "email": customer.email,
        "phone": customer.phone,
        "credit_limit": str(customer.credit_limit),
        "current_balance": str(customer.current_balance),
        "is_active": customer.is_active,
        "is_walk_in": True,
    }
