from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.clientes.application.contracts.duplicados import DuplicateCheckRequest, FiscalValidationRequest
from salesia.modules.clientes.application.validacion import validate_customer_document
from salesia.modules.clientes.domain.duplicados import calculate_name_similarity
from salesia.modules.clientes.infrastructure.models import CustomerModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser


def detect_duplicates(current_user: AuthenticatedUser, db: Session):
    customers = (
        db.execute(select(CustomerModel).where(CustomerModel.company_id == current_user.company_id)).scalars().all()
    )

    seen_docs: dict[str, list[CustomerModel]] = {}
    seen_emails: dict[str, list[CustomerModel]] = {}
    for c in customers:
        key = f"{c.doc_type.upper()}:{c.doc_number.strip()}"
        seen_docs.setdefault(key, []).append(c)
        if c.email:
            seen_emails.setdefault(c.email.lower().strip(), []).append(c)

    duplicates = []
    for key, group in seen_docs.items():
        if len(group) > 1:
            duplicates.append(
                {
                    "group_type": "exact_doc",
                    "group_key": key,
                    "count": len(group),
                    "customers": [{"id": str(x.id), "legal_name": x.legal_name, "code": x.code} for x in group],
                }
            )

    for email, group in seen_emails.items():
        if len(group) > 1:
            duplicates.append(
                {
                    "group_type": "matching_email",
                    "group_key": email,
                    "count": len(group),
                    "customers": [{"id": str(x.id), "legal_name": x.legal_name, "code": x.code} for x in group],
                }
            )

    return {"duplicate_groups": duplicates, "count": len(duplicates)}


def check_duplicate_candidate(req: DuplicateCheckRequest, current_user: AuthenticatedUser, db: Session):
    exact_doc = db.scalars(
        select(CustomerModel).where(
            CustomerModel.company_id == current_user.company_id,
            CustomerModel.doc_type == req.doc_type.upper().strip(),
            CustomerModel.doc_number == req.doc_number.strip(),
        )
    ).all()

    potential = []
    if req.email:
        email_matches = db.scalars(
            select(CustomerModel).where(
                CustomerModel.company_id == current_user.company_id, CustomerModel.email == req.email.lower().strip()
            )
        ).all()
        for m in email_matches:
            if m not in exact_doc:
                potential.append(
                    {
                        "id": str(m.id),
                        "legal_name": m.legal_name,
                        "code": m.code,
                        "matched_by": "email",
                        "similarity": 1.0,
                    }
                )

    if req.phone:
        phone_matches = db.scalars(
            select(CustomerModel).where(
                CustomerModel.company_id == current_user.company_id, CustomerModel.phone == req.phone.strip()
            )
        ).all()
        for m in phone_matches:
            if m not in exact_doc and not any(p["id"] == str(m.id) for p in potential):
                potential.append(
                    {
                        "id": str(m.id),
                        "legal_name": m.legal_name,
                        "code": m.code,
                        "matched_by": "phone",
                        "similarity": 1.0,
                    }
                )

    if req.legal_name:
        all_custs = db.scalars(select(CustomerModel).where(CustomerModel.company_id == current_user.company_id)).all()
        for c in all_custs:
            if c in exact_doc or any(p["id"] == str(c.id) for p in potential):
                continue
            sim = calculate_name_similarity(req.legal_name, c.legal_name)
            if sim >= 0.70:
                potential.append(
                    {
                        "id": str(c.id),
                        "legal_name": c.legal_name,
                        "code": c.code,
                        "matched_by": "name_similarity",
                        "similarity": round(sim, 2),
                    }
                )

    return {
        "exact_matches": [
            {"id": str(x.id), "legal_name": x.legal_name, "code": x.code, "doc_number": x.doc_number} for x in exact_doc
        ],
        "potential_matches": potential,
        "is_exact_duplicate": len(exact_doc) > 0,
    }


def validate_fiscal_identity(req: FiscalValidationRequest, current_user: AuthenticatedUser):
    validate_customer_document(req.doc_type, req.doc_number)
    doc_type = req.doc_type.upper().strip()
    doc_number = req.doc_number.strip()
    checksum_valid = True
    if doc_type == "RUC":
        weights = (5, 4, 3, 2, 7, 6, 5, 4, 3, 2)
        remainder = 11 - sum(int(digit) * weight for digit, weight in zip(doc_number[:10], weights)) % 11
        expected = 0 if remainder == 11 else 1 if remainder == 10 else remainder
        checksum_valid = expected == int(doc_number[-1])
        if not checksum_valid:
            raise HTTPException(422, {"field": "doc_number", "rule": "El dígito verificador del RUC no es válido"})
    provider = "SUNAT" if doc_type == "RUC" else "RENIEC" if doc_type == "DNI" else "REGISTRO_LOCAL"
    return {
        "valid": True,
        "doc_type": doc_type,
        "doc_number": doc_number,
        "checksum_valid": checksum_valid,
        "provider": provider,
        "external_lookup_ready": doc_type in ("RUC", "DNI"),
        "company_id": str(current_user.company_id),
    }
