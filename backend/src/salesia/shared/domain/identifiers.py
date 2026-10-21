from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass(frozen=True)
class EntityId:
    value: UUID

    @classmethod
    def generate(cls):
        return cls(value=uuid4())

    @classmethod
    def from_str(cls, raw: str):
        return cls(value=UUID(raw))

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class CompanyId(EntityId):
    pass


@dataclass(frozen=True)
class BranchId(EntityId):
    pass


@dataclass(frozen=True)
class UserId(EntityId):
    pass


@dataclass(frozen=True)
class CustomerId(EntityId):
    pass


@dataclass(frozen=True)
class ProductId(EntityId):
    pass


@dataclass(frozen=True)
class SaleId(EntityId):
    pass


@dataclass(frozen=True)
class PaymentId(EntityId):
    pass
