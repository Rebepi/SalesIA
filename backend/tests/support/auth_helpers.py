import secrets
from datetime import timedelta
from decimal import Decimal
from uuid import UUID, uuid4
from sqlalchemy import select
from sqlalchemy.orm import Session
from salesia.shared.infrastructure.models import (
    CompanyModel,
    UserModel,
    BranchModel,
    WarehouseModel,
    CustomerModel,
    ProductModel
)
from salesia.modules.seguridad.infrastructure.models import AuthSession
from salesia.modules.seguridad.infrastructure.security import hash_password
from salesia.modules.seguridad.infrastructure.sessions import token_pair, fingerprint, utcnow
from salesia.shared.infrastructure.database import sync_session_factory


def create_durable_identity(
    db: Session = None,
    company_id: UUID = None,
    user_id: UUID = None,
    role: str = "company_admin",
    email: str = None,
    password: str = None
):
    if db is None:
        with sync_session_factory() as session_db:
            return create_durable_identity(
                db=session_db,
                company_id=company_id,
                user_id=user_id,
                role=role,
                email=email,
                password=password
            )
    if company_id is None:
        company_id = uuid4()
    company = db.get(CompanyModel, company_id)
    if not company:
        company = CompanyModel(
            id=company_id,
            tax_id=uuid4().hex[:11],
            legal_name="Empresa Fixture Test",
            trade_name="Fixture Corp",
            base_currency="USD",
            is_active=True
        )
        db.add(company)
        db.flush()

    pwd = password or "SuperSecretSecurePassword2026!"
    user = None
    if user_id:
        user = db.get(UserModel, user_id)
    if not user and email:
        user = db.scalar(select(UserModel).where(UserModel.email == email))

    if not user:
        user = UserModel(
            id=user_id or uuid4(),
            company_id=company.id,
            email=email or f"user_{uuid4().hex[:8]}@salesia.enterprise",
            hashed_password=hash_password(pwd),
            role=role,
            is_active=True
        )
        db.add(user)
        db.flush()
    else:
        user.role = role
        if email and user.email != email:
            existing = db.scalar(select(UserModel).where(UserModel.email == email, UserModel.id != user.id))
            if existing:
                user = existing
                user.role = role
            else:
                user.email = email
        user.company_id = company.id
        user.hashed_password = hash_password(pwd)
        user.is_active = True
        db.flush()

    now = utcnow()
    session = AuthSession(
        user_id=user.id,
        company_id=company.id,
        refresh_hash=fingerprint(secrets.token_urlsafe(48)),
        created_at=now,
        expires_at=now + timedelta(days=7),
        user_agent="pytest-runner",
        ip_address="127.0.0.1"
    )
    db.add(session)
    db.flush()

    pair = token_pair(db, user, session)
    session.refresh_hash = fingerprint(pair["refresh_token"])
    db.commit()

    return {
        "company_id": company.id,
        "user_id": user.id,
        "email": user.email,
        "password": pwd,
        "role": user.role,
        "access_token": pair["access_token"],
        "refresh_token": pair["refresh_token"],
        "session_id": session.id,
        "headers": {"Authorization": f"Bearer {pair['access_token']}"}
    }


def ensure_business_records(
    db: Session = None,
    company_id: UUID = None,
    branch_id: UUID = None,
    warehouse_id: UUID = None,
    customer_id: UUID = None
):
    if db is None:
        with sync_session_factory() as session_db:
            return ensure_business_records(
                db=session_db,
                company_id=company_id,
                branch_id=branch_id,
                warehouse_id=warehouse_id,
                customer_id=customer_id
            )
    b_id = branch_id or uuid4()
    branch = db.get(BranchModel, b_id)
    if not branch:
        branch = BranchModel(
            id=b_id,
            company_id=company_id,
            code=f"BR-{uuid4().hex[:4]}",
            name="Sucursal Principal Fixture",
            timezone="UTC",
            is_active=True
        )
        db.add(branch)
        db.flush()

    w_id = warehouse_id or uuid4()
    warehouse = db.get(WarehouseModel, w_id)
    if not warehouse:
        warehouse = WarehouseModel(
            id=w_id,
            company_id=company_id,
            branch_id=branch.id,
            code=f"WH-{uuid4().hex[:4]}",
            name="Almacen Central Fixture",
            is_active=True
        )
        db.add(warehouse)
        db.flush()

    c_id = customer_id or uuid4()
    customer = db.get(CustomerModel, c_id)
    if not customer:
        customer = CustomerModel(
            id=c_id,
            company_id=company_id,
            code=f"CLI-{uuid4().hex[:4]}",
            doc_type="RUC",
            doc_number=f"20{uuid4().int % 1000000000:09d}",
            legal_name="Cliente Fixture S.A.C.",
            credit_limit=Decimal("50000.00"),
            current_balance=Decimal("0.00")
        )
        db.add(customer)
        db.flush()

    db.commit()
    return {
        "branch_id": branch.id,
        "warehouse_id": warehouse.id,
        "customer_id": customer.id
    }
