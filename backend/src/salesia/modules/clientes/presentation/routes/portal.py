from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from salesia.modules.clientes.application import portal as service
from salesia.modules.clientes.infrastructure.models import CustomerModel
from salesia.modules.clientes.presentation.dependencies import get_portal_customer
from salesia.shared.infrastructure.database import get_db

customer_portal_router = APIRouter(prefix="/customer-portal")


@customer_portal_router.get("/me")
def portal_get_my_profile(customer: CustomerModel = Depends(get_portal_customer)):
    return service.portal_get_my_profile(customer=customer)


@customer_portal_router.get("/invoices")
def portal_get_my_invoices(customer: CustomerModel = Depends(get_portal_customer), db: Session = Depends(get_db)):
    return service.portal_get_my_invoices(customer=customer, db=db)


@customer_portal_router.get("/orders")
def portal_get_my_orders(customer: CustomerModel = Depends(get_portal_customer), db: Session = Depends(get_db)):
    return service.portal_get_my_orders(customer=customer, db=db)


@customer_portal_router.get("/statement")
def portal_get_my_statement(customer: CustomerModel = Depends(get_portal_customer), db: Session = Depends(get_db)):
    return service.portal_get_my_statement(customer=customer, db=db)
