from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.ventas.domain.entities import Sale, SaleLine, SaleStatus
from salesia.modules.ventas.domain.ports import ISaleRepository
from salesia.shared.domain.money import Money
from salesia.shared.infrastructure.models import SaleLineModel, SaleModel


class SqlSaleRepository(ISaleRepository):
    def __init__(self, session: Session):
        self.session = session

    def save(self, sale: Sale) -> None:
        model = self.session.scalar(select(SaleModel).where(SaleModel.id == sale.sale_id))
        was_confirmed = model is not None and model.status in ("confirmed", "paid")
        total = sale.calculate_total()
        subtotal = sum((line.calculate_subtotal().amount for line in sale.lines), Decimal("0.00"))
        tax = sum((line.calculate_tax().amount for line in sale.lines), Decimal("0.00"))

        if model is None:
            model = SaleModel(
                id=sale.sale_id,
                company_id=sale.company_id,
                branch_id=sale.branch_id,
                customer_id=sale.customer_id,
                version=1,
                status=sale.status.value,
                currency=sale.currency,
                subtotal_amount=subtotal,
                tax_amount=tax,
                total_amount=total.amount,
                paid_amount=Decimal("0.00"),
            )
            self.session.add(model)
            self.session.flush()

            for idx, line in enumerate(sale.lines, 1):
                line_model = SaleLineModel(
                    id=line.line_id,
                    company_id=sale.company_id,
                    sale_id=sale.sale_id,
                    product_id=line.product_id,
                    line_number=idx,
                    sku_snapshot=line.sku,
                    name_snapshot=line.product_name,
                    unit_of_measure_snapshot="NIU",
                    quantity=Decimal(line.quantity),
                    unit_price_snapshot=line.unit_price.amount,
                    unit_cost_snapshot=line.cost_snapshot.amount,
                    discount_amount=line.discount.amount,
                    tax_rate_snapshot=line.tax_rate,
                    subtotal_amount=line.calculate_subtotal().amount,
                    tax_amount=line.calculate_tax().amount,
                    total_amount=line.calculate_total().amount,
                )
                self.session.add(line_model)
        else:
            model.status = sale.status.value
            model.currency = sale.currency
            model.subtotal_amount = subtotal
            model.tax_amount = tax
            model.total_amount = total.amount
            model.version = model.version + 1
            if sale.status == SaleStatus.CONFIRMED and not model.confirmed_at:
                model.confirmed_at = datetime.now(timezone.utc)

        self.session.flush()
        if sale.status == SaleStatus.CONFIRMED and not was_confirmed:
            from salesia.modules.organizacion.application.perfil_operativo import require_sale_areas
            require_sale_areas(self.session, model)
            model.confirmed_at = model.confirmed_at or datetime.now(timezone.utc)
            from salesia.modules.finanzas.application.politicas_devolucion import freeze_sale_policies
            freeze_sale_policies(self.session, model)
            from salesia.modules.ventas.application.participacion_comercial import freeze_commission
            freeze_commission(self.session, model)
            from salesia.modules.ventas.application.auxiliares.payment_terms import set_sale_due_date
            set_sale_due_date(model, model.confirmed_at, self.session)

    def get_by_id(self, sale_id: UUID, company_id: Optional[UUID] = None) -> Optional[Sale]:
        query = select(SaleModel).where(SaleModel.id == sale_id)
        if company_id is not None:
            query = query.where(SaleModel.company_id == company_id)
        model = self.session.scalar(query)
        if model is None:
            return None

        lines: list[SaleLine] = []
        for line_model in model.lines:
            lines.append(
                SaleLine(
                    line_id=line_model.id,
                    product_id=line_model.product_id,
                    sku=line_model.sku_snapshot,
                    product_name=line_model.name_snapshot,
                    quantity=int(line_model.quantity),
                    unit_price=Money.create(line_model.unit_price_snapshot, model.currency),
                    tax_rate=line_model.tax_rate_snapshot,
                    discount=Money.create(line_model.discount_amount, model.currency),
                    cost_snapshot=Money.create(line_model.unit_cost_snapshot, model.currency),
                )
            )

        sale = Sale(
            sale_id=model.id,
            company_id=model.company_id,
            branch_id=model.branch_id,
            customer_id=model.customer_id,
            currency=model.currency,
            status=SaleStatus(model.status),
            lines=lines,
        )
        return sale
