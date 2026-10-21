from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from salesia.modules.clientes.application.contracts.contactos import CustomerAddressCreateModel
from salesia.modules.clientes.application.contactos_edicion import address_data
from salesia.modules.clientes.domain.texto import sanitize_text
from salesia.modules.clientes.infrastructure.models import CustomerAddressModel, CustomerModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.errors import DomainNotFoundException


def list_customer_addresses(customer_id: UUID, current_user: AuthenticatedUser, db: Session):
    addresses = db.scalars(
        select(CustomerAddressModel)
        .where(
            CustomerAddressModel.company_id == current_user.company_id, CustomerAddressModel.customer_id == customer_id
        )
        .order_by(CustomerAddressModel.is_primary.desc(), CustomerAddressModel.address_type.asc())
    ).all()
    return [address_data(address) for address in addresses]


def create_customer_address(
    customer_id: UUID, req: CustomerAddressCreateModel, current_user: AuthenticatedUser, db: Session
):
    cust = db.scalar(
        select(CustomerModel).where(
            CustomerModel.company_id == current_user.company_id, CustomerModel.id == customer_id
        ).with_for_update()
    )
    if not cust:
        raise DomainNotFoundException("Cliente no encontrado.")

    if req.is_primary and req.is_active:
        db.execute(
            update(CustomerAddressModel)
            .where(
                CustomerAddressModel.company_id == current_user.company_id,
                CustomerAddressModel.customer_id == customer_id,
                CustomerAddressModel.address_type == req.address_type,
            )
            .values(is_primary=False, version=CustomerAddressModel.version + 1)
        )

    addr = CustomerAddressModel(
        id=uuid4(),
        company_id=current_user.company_id,
        customer_id=customer_id,
        address_type=req.address_type,
        street=sanitize_text(req.street) or req.street,
        city=sanitize_text(req.city) or "Lima",
        state=sanitize_text(req.state),
        country=req.country.upper().strip(),
        postal_code=req.postal_code.strip() if req.postal_code else None,
        is_primary=req.is_primary and req.is_active,
        valid_from=req.valid_from, valid_until=req.valid_until, is_active=req.is_active, version=1,
    )
    db.add(addr)
    db.commit()
    db.refresh(addr)

    return address_data(addr)


def delete_customer_address(customer_id: UUID, address_id: UUID, current_user: AuthenticatedUser, db: Session):
    customer = db.scalar(select(CustomerModel).where(CustomerModel.company_id == current_user.company_id, CustomerModel.id == customer_id).with_for_update())
    if customer is None:
        raise DomainNotFoundException("Cliente no encontrado.")

    addr = db.scalar(
        select(CustomerAddressModel).where(
            CustomerAddressModel.company_id == current_user.company_id,
            CustomerAddressModel.customer_id == customer_id,
            CustomerAddressModel.id == address_id,
        )
    )
    if not addr:
        raise DomainNotFoundException("Dirección no encontrada.")

    if addr.is_active:
        addr.is_active, addr.is_primary, addr.version = False, False, addr.version + 1
    db.commit()
    return {"status": "archived", "address_id": str(address_id)}
