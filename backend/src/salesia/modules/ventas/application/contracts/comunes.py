from pydantic import BaseModel


class SaleResponse(BaseModel):
    sale_id: str

    company_id: str

    branch_id: str

    customer_id: str

    status: str

    currency: str

    total_amount: str

    items_count: int
