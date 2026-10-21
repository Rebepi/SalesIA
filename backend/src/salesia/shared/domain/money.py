from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Union
from salesia.shared.domain.exceptions import CurrencyMismatchException, NegativeAmountException


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str

    def __post_init__(self):
        normalized_currency = self.currency.strip().upper()
        if len(normalized_currency) != 3:
            raise ValueError(f"Código de divisa inválido: {self.currency}")
        object.__setattr__(self, "currency", normalized_currency)

        if not isinstance(self.amount, Decimal):
            normalized_amount = Decimal(str(self.amount))
            object.__setattr__(self, "amount", normalized_amount)

    @classmethod
    def zero(cls, currency: str = "USD") -> "Money":
        return cls(amount=Decimal("0.00"), currency=currency)

    @classmethod
    def create(cls, amount: Union[str, int, float, Decimal], currency: str = "USD") -> "Money":
        dec_amount = Decimal(str(amount))
        return cls(amount=dec_amount, currency=currency)

    def round_to(self, decimals: int = 2) -> "Money":
        quantizer = Decimal("10") ** -decimals
        rounded = self.amount.quantize(quantizer, rounding=ROUND_HALF_EVEN)
        return Money(amount=rounded, currency=self.currency)

    def ensure_non_negative(self) -> "Money":
        if self.amount < Decimal("0"):
            raise NegativeAmountException(str(self.amount))
        return self

    def add(self, other: "Money") -> "Money":
        self._check_same_currency(other)
        return Money(amount=self.amount + other.amount, currency=self.currency)

    def subtract(self, other: "Money") -> "Money":
        self._check_same_currency(other)
        return Money(amount=self.amount - other.amount, currency=self.currency)

    def multiply(self, factor: Union[int, Decimal, str]) -> "Money":
        factor_dec = Decimal(str(factor))
        return Money(amount=self.amount * factor_dec, currency=self.currency)

    def divide(self, divisor: Union[int, Decimal, str]) -> "Money":
        divisor_dec = Decimal(str(divisor))
        if divisor_dec == Decimal("0"):
            raise ZeroDivisionError("No se puede dividir dinero entre cero")
        return Money(amount=self.amount / divisor_dec, currency=self.currency)

    def is_zero(self) -> bool:
        return self.amount == Decimal("0")

    def is_positive(self) -> bool:
        return self.amount > Decimal("0")

    def is_negative(self) -> bool:
        return self.amount < Decimal("0")

    def _check_same_currency(self, other: "Money") -> None:
        if self.currency != other.currency:
            raise CurrencyMismatchException(expected=self.currency, actual=other.currency)

    def __add__(self, other: "Money") -> "Money":
        return self.add(other)

    def __sub__(self, other: "Money") -> "Money":
        return self.subtract(other)

    def __mul__(self, other: Union[int, Decimal, str]) -> "Money":
        return self.multiply(other)

    def __truediv__(self, other: Union[int, Decimal, str]) -> "Money":
        return self.divide(other)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return False
        return self.currency == other.currency and self.amount == other.amount

    def __lt__(self, other: "Money") -> bool:
        self._check_same_currency(other)
        return self.amount < other.amount

    def __le__(self, other: "Money") -> bool:
        self._check_same_currency(other)
        return self.amount <= other.amount

    def __gt__(self, other: "Money") -> bool:
        self._check_same_currency(other)
        return self.amount > other.amount

    def __ge__(self, other: "Money") -> bool:
        self._check_same_currency(other)
        return self.amount >= other.amount

    def __str__(self) -> str:
        return f"{self.amount:.2f} {self.currency}"

    def to_dict(self) -> dict:
        return {
            "amount": str(self.amount),
            "currency": self.currency
        }
