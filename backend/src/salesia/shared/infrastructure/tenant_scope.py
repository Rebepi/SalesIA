from contextvars import ContextVar
from sqlalchemy import event, text
from sqlalchemy.orm import Session

current_company = ContextVar("salesia_current_company", default=None)


def bind_company(db, company_id):
    value = str(company_id)
    current_company.set(value)
    db.info["company_id"] = value
    if db.bind.dialect.name == "postgresql":
        db.execute(text("SELECT set_config('app.current_company_id', :company, true)"), {"company": value})


@event.listens_for(Session, "after_begin")
def apply_company_context(session, transaction, connection):
    company = session.info.get("company_id") or current_company.get()
    if connection.dialect.name == "postgresql" and company:
        connection.execute(text("SELECT set_config('app.current_company_id', :company, true)"), {"company": company})
