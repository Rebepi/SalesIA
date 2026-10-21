from decimal import Decimal
import pytest
from salesia.shared.domain.money import Money
from salesia.shared.domain.exceptions import CurrencyMismatchException, NegativeAmountException


def test_money_creation_and_attributes():
    m = Money.create("150.75", "USD")
    assert m.amount == Decimal("150.75")
    assert m.currency == "USD"
    assert str(m) == "150.75 USD"


def test_money_addition():
    m1 = Money.create("100.25", "USD")
    m2 = Money.create("50.75", "USD")
    res = m1 + m2
    assert res == Money.create("151.00", "USD")


def test_money_subtraction():
    m1 = Money.create("200.00", "PEN")
    m2 = Money.create("75.50", "PEN")
    res = m1 - m2
    assert res == Money.create("124.50", "PEN")


def test_money_currency_mismatch():
    m1 = Money.create("100.00", "USD")
    m2 = Money.create("100.00", "PEN")
    with pytest.raises(CurrencyMismatchException):
        _ = m1 + m2


def test_money_multiplication():
    m = Money.create("25.50", "USD")
    res = m * 3
    assert res == Money.create("76.50", "USD")


def test_money_division():
    m = Money.create("100.00", "USD")
    res = m.divide(4)
    assert res == Money.create("25.00", "USD")


def test_money_division_by_zero():
    m = Money.create("100.00", "USD")
    with pytest.raises(ZeroDivisionError):
        m.divide(0)


def test_money_rounding_bankers():
    m1 = Money.create("12.345", "USD")
    m2 = Money.create("12.355", "USD")
    assert m1.round_to(2).amount == Decimal("12.34")
    assert m2.round_to(2).amount == Decimal("12.36")


def test_money_negative_guard():
    m_pos = Money.create("10.00", "USD")
    m_pos.ensure_non_negative()

    m_neg = Money.create("-5.00", "USD")
    with pytest.raises(NegativeAmountException):
        m_neg.ensure_non_negative()


def test_money_comparisons():
    m1 = Money.create("10.00", "EUR")
    m2 = Money.create("20.00", "EUR")
    assert m1 < m2
    assert m2 > m1
    assert m1 <= m2
    assert m2 >= m1
    assert m1 != m2
