import json
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from salesia.modules.clientes.application.contracts.duplicados import CustomerMergeModel
from salesia.modules.clientes.infrastructure.models import (
    CustomerActivityModel,
    CustomerAddressModel,
    CustomerContactModel,
    CustomerLoyaltyLedgerModel,
    CustomerModel,
    CustomerNoteModel,
    CustomerOpportunityModel,
)
from salesia.modules.clientes.infrastructure.perfiles import ensure_customer_profile
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.errors import DomainConflictException, DomainNotFoundException
from salesia.shared.infrastructure.models import AuditLogModel, OrderModel, OutboxEventModel, QuotationModel, SaleModel


def preview_customer_merge(req: CustomerMergeModel, current_user: AuthenticatedUser, db: Session):
    if req.primary_customer_id == req.duplicate_customer_id:
        raise DomainConflictException("No se puede fusionar un cliente consigo mismo.")

    primary = db.scalar(
        select(CustomerModel).where(
            CustomerModel.company_id == current_user.company_id, CustomerModel.id == req.primary_customer_id
        )
    )
    duplicate = db.scalar(
        select(CustomerModel).where(
            CustomerModel.company_id == current_user.company_id, CustomerModel.id == req.duplicate_customer_id
        )
    )
    if not primary or not duplicate:
        raise DomainNotFoundException("Uno o ambos clientes no existen en la empresa.")

    sales_count = db.scalar(
        select(func.count(SaleModel.id)).where(
            SaleModel.company_id == current_user.company_id, SaleModel.customer_id == duplicate.id
        )
    )
    quotes_count = db.scalar(
        select(func.count(QuotationModel.id)).where(
            QuotationModel.company_id == current_user.company_id, QuotationModel.customer_id == duplicate.id
        )
    )
    orders_count = db.scalar(
        select(func.count(OrderModel.id)).where(
            OrderModel.company_id == current_user.company_id, OrderModel.customer_id == duplicate.id
        )
    )
    contacts_count = db.scalar(
        select(func.count(CustomerContactModel.id)).where(
            CustomerContactModel.company_id == current_user.company_id, CustomerContactModel.customer_id == duplicate.id
        )
    )
    addresses_count = db.scalar(
        select(func.count(CustomerAddressModel.id)).where(
            CustomerAddressModel.company_id == current_user.company_id, CustomerAddressModel.customer_id == duplicate.id
        )
    )
    notes_count = db.scalar(
        select(func.count(CustomerNoteModel.id)).where(
            CustomerNoteModel.company_id == current_user.company_id, CustomerNoteModel.customer_id == duplicate.id
        )
    )
    opps_count = db.scalar(
        select(func.count(CustomerOpportunityModel.id)).where(
            CustomerOpportunityModel.company_id == current_user.company_id,
            CustomerOpportunityModel.customer_id == duplicate.id,
        )
    )
    acts_count = db.scalar(
        select(func.count(CustomerActivityModel.id)).where(
            CustomerActivityModel.company_id == current_user.company_id,
            CustomerActivityModel.customer_id == duplicate.id,
        )
    )

    return {
        "primary_customer": {
            "id": str(primary.id),
            "legal_name": primary.legal_name,
            "code": primary.code,
            "current_balance": str(primary.current_balance),
        },
        "duplicate_customer": {
            "id": str(duplicate.id),
            "legal_name": duplicate.legal_name,
            "code": duplicate.code,
            "current_balance": str(duplicate.current_balance),
        },
        "impact": {
            "sales_count": sales_count,
            "quotations_count": quotes_count,
            "orders_count": orders_count,
            "contacts_count": contacts_count,
            "addresses_count": addresses_count,
            "notes_count": notes_count,
            "opportunities_count": opps_count,
            "activities_count": acts_count,
            "balance_transfer": str(duplicate.current_balance),
        },
    }


def merge_customers(req: CustomerMergeModel, current_user: AuthenticatedUser, db: Session):
    if req.primary_customer_id == req.duplicate_customer_id:
        raise DomainConflictException("No se puede fusionar un cliente consigo mismo.")

    primary = db.execute(
        select(CustomerModel).where(
            CustomerModel.company_id == current_user.company_id, CustomerModel.id == req.primary_customer_id
        )
    ).scalar_one_or_none()
    duplicate = db.execute(
        select(CustomerModel).where(
            CustomerModel.company_id == current_user.company_id, CustomerModel.id == req.duplicate_customer_id
        )
    ).scalar_one_or_none()

    if not primary or not duplicate:
        raise DomainNotFoundException("Uno o ambos clientes no existen para fusionar.")

    dup_profile = ensure_customer_profile(db, duplicate)
    pri_profile = ensure_customer_profile(db, primary)

    if req.version is not None and req.version != pri_profile.version:
        raise DomainConflictException("Conflicto de concurrencia en la fusión de clientes.")

    sales_migrated = db.execute(
        update(SaleModel)
        .where(SaleModel.company_id == current_user.company_id, SaleModel.customer_id == duplicate.id)
        .values(customer_id=primary.id)
    ).rowcount

    db.execute(
        update(QuotationModel)
        .where(QuotationModel.company_id == current_user.company_id, QuotationModel.customer_id == duplicate.id)
        .values(customer_id=primary.id)
    )

    db.execute(
        update(OrderModel)
        .where(OrderModel.company_id == current_user.company_id, OrderModel.customer_id == duplicate.id)
        .values(customer_id=primary.id)
    )

    db.execute(
        update(CustomerContactModel)
        .where(
            CustomerContactModel.company_id == current_user.company_id, CustomerContactModel.customer_id == duplicate.id
        )
        .values(customer_id=primary.id)
    )

    db.execute(
        update(CustomerAddressModel)
        .where(
            CustomerAddressModel.company_id == current_user.company_id, CustomerAddressModel.customer_id == duplicate.id
        )
        .values(customer_id=primary.id)
    )

    db.execute(
        update(CustomerNoteModel)
        .where(CustomerNoteModel.company_id == current_user.company_id, CustomerNoteModel.customer_id == duplicate.id)
        .values(customer_id=primary.id)
    )

    db.execute(
        update(CustomerOpportunityModel)
        .where(
            CustomerOpportunityModel.company_id == current_user.company_id,
            CustomerOpportunityModel.customer_id == duplicate.id,
        )
        .values(customer_id=primary.id)
    )

    db.execute(
        update(CustomerActivityModel)
        .where(
            CustomerActivityModel.company_id == current_user.company_id,
            CustomerActivityModel.customer_id == duplicate.id,
        )
        .values(customer_id=primary.id)
    )

    db.execute(
        update(CustomerLoyaltyLedgerModel)
        .where(
            CustomerLoyaltyLedgerModel.company_id == current_user.company_id,
            CustomerLoyaltyLedgerModel.customer_id == duplicate.id,
        )
        .values(customer_id=primary.id)
    )

    transferred_balance = duplicate.current_balance
    primary.current_balance += transferred_balance
    duplicate.current_balance = Decimal("0.000000")
    duplicate.is_active = False
    dup_profile.status = "archived"
    dup_profile.version += 1
    pri_profile.version += 1

    outbox = OutboxEventModel(
        id=uuid4(),
        company_id=current_user.company_id,
        event_type="CUSTOMER_MERGED",
        aggregate_type="Customer",
        aggregate_id=primary.id,
        payload_json=json.dumps(
            {
                "primary_id": str(primary.id),
                "duplicate_id": str(duplicate.id),
                "transferred_balance": str(transferred_balance),
                "sales_count": sales_migrated,
            }
        ),
        status="PENDING",
    )
    db.add(outbox)

    audit = AuditLogModel(
        id=uuid4(),
        company_id=current_user.company_id,
        actor_id=current_user.user_id,
        actor_email=current_user.email,
        action="CUSTOMER_MERGED",
        entity_type="Customer",
        entity_id=primary.id,
        trace_id=str(uuid4()),
        payload_diff=json.dumps(
            {
                "absorbed_customer": str(duplicate.id),
                "transferred_balance": str(transferred_balance),
                "sales_migrated": sales_migrated,
            }
        ),
    )
    db.add(audit)
    db.commit()

    return {
        "primary_customer_id": str(primary.id),
        "merged_duplicate_id": str(duplicate.id),
        "company_id": str(current_user.company_id),
        "status": "completed",
        "primary_current_balance": str(primary.current_balance),
        "transferred_balance": str(transferred_balance),
        "sales_migrated": sales_migrated,
    }
