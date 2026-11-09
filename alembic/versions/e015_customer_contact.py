"""Contacto del cliente en las reservas.

Revision ID: e015contact
Revises: d013whatsapp
"""
import sqlalchemy as sa
from alembic import op

revision = "e015contact"
down_revision = "d013whatsapp"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("appointments") as batch:
        batch.add_column(sa.Column("customer_contact", sa.String(length=254), nullable=True))


def downgrade():
    with op.batch_alter_table("appointments") as batch:
        batch.drop_column("customer_contact")
