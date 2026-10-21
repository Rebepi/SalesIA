from uuid import uuid4
from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa

revision = "0035"
down_revision = "0034"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("product_variants", sa.Column("operational_product_id", sa.Uuid(), nullable=True))
    with op.batch_alter_table("product_variants") as batch:
        batch.create_foreign_key("fk_variant_operational_product", "products", ["operational_product_id"], ["id"])
        batch.create_unique_constraint("uq_variant_operational_product", ["operational_product_id"])
    connection = op.get_bind()
    metadata = sa.MetaData()
    products = sa.Table("products", metadata, autoload_with=connection)
    variants = sa.Table("product_variants", metadata, autoload_with=connection)
    profiles = sa.Table("product_profiles", metadata, autoload_with=connection)
    barcodes = sa.Table("product_barcodes", metadata, autoload_with=connection)
    for variant in connection.execute(sa.select(variants)).mappings().all():
        parent = connection.execute(sa.select(products).where(products.c.id == variant["product_id"], products.c.company_id == variant["company_id"])).mappings().first()
        if parent is None:
            raise RuntimeError("Una variante no tiene producto principal. Corrige sus referencias antes de migrar.")
        duplicate = connection.execute(sa.select(products.c.id).where(products.c.company_id == variant["company_id"], products.c.sku == variant["sku"])).scalar_one_or_none()
        if duplicate is not None:
            raise RuntimeError(f"El SKU de variante {variant['sku']} ya existe como producto. Resuelve la duplicidad antes de migrar.")
        identifier = uuid4().hex if connection.dialect.name == "sqlite" else uuid4()
        current = datetime.now(timezone.utc)
        values = dict(parent)
        values.update(id=identifier, sku=variant["sku"], name=(parent["name"] + " · " + variant["sku"])[:255], unit_price=parent["unit_price"] + variant["price_delta"], is_active=variant["is_active"], created_at=current, updated_at=current)
        if values["unit_price"] < 0:
            raise RuntimeError("Una variante tiene precio negativo. Corrígelo antes de migrar.")
        connection.execute(products.insert().values(**values))
        profile = connection.execute(sa.select(profiles).where(profiles.c.product_id == parent["id"], profiles.c.company_id == parent["company_id"])).mappings().first()
        if profile:
            profile_values = dict(profile)
            profile_values.update(id=uuid4().hex if connection.dialect.name == "sqlite" else uuid4(), product_id=identifier, barcode=None, is_kit=False, created_at=current, updated_at=current)
            connection.execute(profiles.insert().values(**profile_values))
        connection.execute(variants.update().where(variants.c.id == variant["id"]).values(operational_product_id=identifier))
        connection.execute(barcodes.update().where(barcodes.c.company_id == variant["company_id"], barcodes.c.variant_id == variant["id"]).values(product_id=identifier))


def downgrade():
    raise RuntimeError("Los SKU operativos de las variantes y sus movimientos deben conservarse.")
