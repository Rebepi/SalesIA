import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from salesia.modules.clientes.application.contracts.clientes import CustomerCreateModel
from salesia.modules.clientes.application.validacion import validate_customer_document


@pytest.mark.parametrize("document_type,value", [("DNI", "123456789"), ("DNI", "1234567"), ("DNI", "1234567A"), ("RUC", "201234567890"), ("PASSPORT", "A" * 17)])
def test_invalid_document_lengths_are_rejected(document_type, value):
    with pytest.raises(HTTPException) as error:
        validate_customer_document(document_type, value)
    assert error.value.status_code == 422


@pytest.mark.parametrize("document_type,value", [("DNI", "00123456"), ("RUC", "20123456789"), ("PASSPORT", "ABC12345")])
def test_valid_documents_preserve_leading_zeros(document_type, value):
    validate_customer_document(document_type, value)


@pytest.mark.parametrize("extra", [{"phone": "9" * 33}, {"email": "a" * 250 + "@mail.pe"}, {"address": "a" * 256}, {"legal_name": "a" * 256}])
def test_customer_contract_enforces_field_limits(extra):
    data = {"doc_type": "DNI", "doc_number": "12345678", "legal_name": "Cliente de prueba", **extra}
    with pytest.raises(ValidationError):
        CustomerCreateModel.model_validate(data)
